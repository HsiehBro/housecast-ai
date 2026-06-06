import os
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from xgboost import XGBRegressor
from features import preprocess_data
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Train XGBoost model for house price prediction"

    def add_arguments(self, parser):
        parser.add_argument(
            "data_file",
            type=str,
            help="Path to the CSV file containing house data",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default=settings.ML_MODEL_DIR,
            help="Directory to save the trained model",
        )

    def handle(self, *args, **options):
        data_file = options["data_file"]
        output_dir = options["output_dir"]

        if not os.path.exists(data_file):
            self.stderr.write(self.style.ERROR(f"Data file not found: {data_file}"))
            return

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Load and preprocess data
        self.stdout.write("Loading and preprocessing data...")
        df = pd.read_csv(data_file)
        X, y, preprocessor = preprocess_data(df)

        # Split data into train and test sets
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.stdout.write(f"Training set: {len(X_train)} samples")
        self.stdout.write(f"Test set: {len(X_test)} samples")

        # Define XGBoost model
        xgb = XGBRegressor(
            objective="reg:squarederror",
            random_state=42,
            n_jobs=-1,
            tree_method="hist"
        )

        # Hyperparameter tuning with cross-validation
        self.stdout.write("Performing hyperparameter tuning...")
        param_grid = {
            "n_estimators": [100, 200, 300],
            "max_depth": [3, 5, 7],
            "learning_rate": [0.01, 0.1, 0.3],
            "subsample": [0.8, 1.0],
            "colsample_bytree": [0.8, 1.0],
        }

        grid_search = GridSearchCV(
            estimator=xgb,
            param_grid=param_grid,
            cv=5,
            scoring="neg_mean_squared_error",
            n_jobs=-1,
            verbose=1
        )

        grid_search.fit(X_train, y_train)

        # Get best model
        best_model = grid_search.best_estimator_
        self.stdout.write(f"Best parameters: {grid_search.best_params_}")

        # Evaluate model
        self.stdout.write("Evaluating model...")
        y_pred = best_model.predict(X_test)

        # Calculate metrics
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        self.stdout.write(f"RMSE: {rmse:.2f}")
        self.stdout.write(f"MAE: {mae:.2f}")
        self.stdout.write(f"R²: {r2:.4f}")

        # Save model and preprocessor
        model_path = os.path.join(output_dir, "house_price_model.pkl")
        preprocessor_path = os.path.join(output_dir, "preprocessor.pkl")

        joblib.dump(best_model, model_path)
        joblib.dump(preprocessor, preprocessor_path)

        self.stdout.write(self.style.SUCCESS(f"Model saved to {model_path}"))
        self.stdout.write(self.style.SUCCESS(f"Preprocessor saved to {preprocessor_path}"))

        # Save feature importance
        self.save_feature_importance(best_model, preprocessor, output_dir)

    def save_feature_importance(self, model, preprocessor, output_dir):
        """Save feature importance visualization"""
        feature_names = get_feature_names(preprocessor)
        importance = model.feature_importances_

        # Create DataFrame for visualization
        importance_df = pd.DataFrame({
            "feature": feature_names,
            "importance": importance
        }).sort_values("importance", ascending=False)

        # Plot feature importance
        plt.figure(figsize=(12, 8))
        plt.barh(importance_df["feature"], importance_df["importance"])
        plt.xlabel("Feature Importance")
        plt.title("XGBoost Feature Importance")
        plt.tight_layout()

        importance_plot_path = os.path.join(output_dir, "feature_importance.png")
        plt.savefig(importance_plot_path)
        plt.close()

        self.stdout.write(self.style.SUCCESS(f"Feature importance plot saved to {importance_plot_path}"))


def get_feature_names(preprocessor):
    """Get feature names after preprocessing"""
    numeric_features = ["area", "rooms", "floor", "house_age", "price_per_sqm"]
    categorical_features = ["district"]

    numeric_transformer = preprocessor.named_transformers_["num"]
    categorical_transformer = preprocessor.named_transformers_["cat"]

    numeric_feature_names = numeric_features
    cat_encoder = categorical_transformer.named_steps["onehot"]
    cat_feature_names = cat_encoder.get_feature_names_out(categorical_features)

    return np.concatenate([numeric_feature_names, cat_feature_names])