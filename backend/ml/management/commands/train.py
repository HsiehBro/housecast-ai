"""Train XGBoost model for house price prediction.

Usage:
    uv run python manage.py train
    uv run python manage.py train --tune
    uv run python manage.py train --sample-size 1000
"""

import os
import logging
import random

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from xgboost import XGBRegressor
from django.conf import settings
from django.core.management.base import BaseCommand
from houses.models import House

logger = logging.getLogger(__name__)

NUMERIC_FEATURES = ["area", "rooms", "floor", "house_age"]
CATEGORICAL_FEATURES = ["district"]


def build_dataset(sample_size=None):
    """Load house data from DB and build feature DataFrame."""
    rows = list(House.objects.values(
        "area", "rooms", "floor", "year", "district", "price"
    ))

    if not rows:
        return None, None, None

    if sample_size and sample_size < len(rows):
        rows = random.sample(rows, sample_size)

    df = pd.DataFrame(rows)

    # Drop rows with missing essential fields
    df = df.dropna(subset=["area", "rooms", "floor", "year", "district", "price"])
    df = df[df["area"] > 0]

    # Convert Decimal fields to float
    df["price"] = df["price"].astype(float)

    # Compute house_age
    current_year = pd.Timestamp.now().year
    df["house_age"] = current_year - df["year"]

    # Target
    y = df["price"]

    # Features
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()

    return X, y, df


def build_preprocessor():
    """Build the preprocessing pipeline."""
    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore"))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERIC_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES)
        ])

    return preprocessor


class Command(BaseCommand):
    help = "Train XGBoost model for house price prediction"

    def add_arguments(self, parser):
        parser.add_argument(
            "--tune",
            action="store_true",
            help="Perform hyperparameter tuning with GridSearchCV",
        )
        parser.add_argument(
            "--sample-size",
            type=int,
            default=None,
            help="Limit training data to N random records",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default=None,
            help="Directory to save model (default: settings.ML_MODEL_DIR)",
        )

    def handle(self, *args, **options):
        output_dir = options["output_dir"] or str(settings.ML_MODEL_DIR)
        os.makedirs(output_dir, exist_ok=True)

        self.stdout.write("Loading house data from database...")
        X, y, df = build_dataset(sample_size=options["sample_size"])

        if X is None or len(X) == 0:
            self.stderr.write(self.style.ERROR(
                "No house data found. Run 'manage.py import_houses --generate-sample' first."
            ))
            return

        self.stdout.write(f"Dataset: {len(X)} records, {X['district'].nunique()} districts")

        # Build and fit preprocessor
        preprocessor = build_preprocessor()
        X_processed = preprocessor.fit_transform(X)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_processed, y, test_size=0.2, random_state=42
        )

        self.stdout.write(f"Train: {len(y_train)}, Test: {len(y_test)}")

        # Train model
        if options["tune"]:
            self.stdout.write("Performing hyperparameter tuning...")
            xgb = XGBRegressor(
                objective="reg:squarederror",
                random_state=42,
                n_jobs=-1,
                tree_method="hist"
            )
            param_grid = {
                "n_estimators": [100, 200, 300],
                "max_depth": [3, 5, 7],
                "learning_rate": [0.01, 0.1, 0.3],
                "subsample": [0.8, 1.0],
                "colsample_bytree": [0.8, 1.0],
            }
            grid = GridSearchCV(
                estimator=xgb, param_grid=param_grid,
                cv=5, scoring="neg_mean_squared_error", n_jobs=-1, verbose=1
            )
            grid.fit(X_train, y_train)
            model = grid.best_estimator_
            self.stdout.write(f"Best params: {grid.best_params_}")
        else:
            self.stdout.write("Training XGBoost model...")
            model = XGBRegressor(
                objective="reg:squarederror",
                n_estimators=200,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                tree_method="hist"
            )
            model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        self.stdout.write(f"RMSE: {rmse:,.2f}")
        self.stdout.write(f"MAE:  {mae:,.2f}")
        self.stdout.write(f"R2:   {r2:.4f}")

        # Save model and preprocessor
        model_path = os.path.join(output_dir, "house_price_model.pkl")
        preprocessor_path = os.path.join(output_dir, "preprocessor.pkl")

        joblib.dump(model, model_path)
        joblib.dump(preprocessor, preprocessor_path)

        self.stdout.write(self.style.SUCCESS(f"Model saved to {model_path}"))
        self.stdout.write(self.style.SUCCESS(f"Preprocessor saved to {preprocessor_path}"))

        # Reload model service
        try:
            from prediction.service import model_service
            model_service.load_model()
            self.stdout.write(self.style.SUCCESS("Model service reloaded."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f"Could not reload model service (restart server): {e}"
            ))
