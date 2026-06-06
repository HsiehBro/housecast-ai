import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer


def preprocess_data(df):
    """Preprocess raw house data for machine learning"""
    # Make a copy to avoid modifying original
    X = df.copy()

    # 1. Handle missing values
    # Numeric features: fill with median
    numeric_features = ["area", "rooms", "floor", "year"]
    for feature in numeric_features:
        X[feature] = X[feature].fillna(X[feature].median())

    # 2. Calculate house age (current year - year built)
    current_year = pd.Timestamp.now().year
    X["house_age"] = current_year - X["year"]

    # 3. Feature engineering
    # Create price per square meter
    X["price_per_sqm"] = X["price"] / X["area"]

    # 4. Select features for model
    features = [
        "area", "rooms", "floor", "house_age", "price_per_sqm", "district"
    ]

    X = X[features]

    # 5. Prepare target variable
    y = X["price"]
    X = X.drop("price", axis=1)

    # 6. Create preprocessing pipeline
    numeric_features = ["area", "rooms", "floor", "house_age", "price_per_sqm"]
    categorical_features = ["district"]

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
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features)
        ])

    # 7. Apply preprocessing
    X_processed = preprocessor.fit_transform(X)

    return X_processed, y, preprocessor


def get_feature_names(preprocessor):
    """Get feature names after preprocessing"""
    numeric_features = ["area", "rooms", "floor", "house_age", "price_per_sqm"]
    categorical_features = ["district"]

    numeric_transformer = preprocessor.named_transformers_["num"]
    categorical_transformer = preprocessor.named_transformers_["cat"]

    # Get numeric feature names (scaled features keep original names)
    numeric_feature_names = numeric_features

    # Get categorical feature names (one-hot encoded)
    cat_encoder = categorical_transformer.named_steps["onehot"]
    cat_feature_names = cat_encoder.get_feature_names_out(categorical_features)

    return np.concatenate([numeric_feature_names, cat_feature_names])