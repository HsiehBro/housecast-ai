import os
import logging
import threading
import time
from datetime import datetime

import numpy as np
import pandas as pd
import joblib
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Avg

from .versioning import version_manager

logger = logging.getLogger(__name__)

FEATURE_ORDER = ["area", "rooms", "floor", "house_age", "district"]


class ModelService:
    _instance = None
    _lock = threading.Lock()
    _model = None
    _preprocessor = None
    _last_loaded = None
    _model_version = None

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ModelService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    self.load_model()

    def load_model(self):
        """Load the trained model and preprocessor"""
        try:
            model_path = os.path.join(settings.ML_MODEL_DIR, "house_price_model.pkl")
            preprocessor_path = os.path.join(settings.ML_MODEL_DIR, "preprocessor.pkl")

            if not os.path.exists(model_path) or not os.path.exists(preprocessor_path):
                logger.warning("Model files not found. Using heuristic fallback for predictions.")
                self._model = None
                self._preprocessor = None
                return

            if os.path.getsize(model_path) == 0:
                logger.warning("Model file is empty (0 bytes). Using heuristic fallback.")
                self._model = None
                self._preprocessor = None
                return

            self._model = joblib.load(model_path)
            self._preprocessor = joblib.load(preprocessor_path)
            self._last_loaded = time.time()
            self._model_version = int(os.path.getmtime(model_path))

            self._log_model_info()

        except Exception as e:
            logger.error("Failed to load model: %s", e)
            self._model = None
            self._preprocessor = None

    def _log_model_info(self):
        """Log model information"""
        model_path = os.path.join(settings.ML_MODEL_DIR, "house_price_model.pkl")
        model_info = {
            "model_type": str(type(self._model)),
            "model_version": self._model_version,
            "features": self.get_feature_names(),
            "model_size_mb": os.path.getsize(model_path) / (1024 * 1024),
            "version_info": version_manager.get_model_info()
        }
        logger.info("Model loaded: %s", model_info)

    def get_feature_names(self):
        """Get feature names from preprocessor"""
        if self._preprocessor is None:
            return []

        numeric_features = ["area", "rooms", "floor", "house_age"]
        categorical_features = ["district"]

        numeric_transformer = self._preprocessor.named_transformers_["num"]
        categorical_transformer = self._preprocessor.named_transformers_["cat"]

        numeric_feature_names = numeric_features
        cat_encoder = categorical_transformer.named_steps["onehot"]
        cat_feature_names = cat_encoder.get_feature_names_out(categorical_features)

        return list(np.concatenate([numeric_feature_names, cat_feature_names]))

    def _get_district_avg_price_per_sqm(self, district):
        """Get average price_per_sqm for a district from the database."""
        from houses.models import House

        cache_key = f"district_avg_pps_{district}"
        avg_pps = cache.get(cache_key)

        if avg_pps is not None:
            return avg_pps

        result = House.objects.filter(district=district).aggregate(
            avg_pps=Avg("price_per_sqm")
        )
        avg_pps = float(result["avg_pps"]) if result["avg_pps"] else 6000.0

        if result["avg_pps"] is None:
            logger.warning("No price data for district=%s, using fallback", district)

        cache.set(cache_key, avg_pps, timeout=300)
        return avg_pps

    def _prepare_features(self, data):
        """Transform raw prediction input into the feature format the preprocessor expects."""
        current_year = datetime.now().year
        house_age = current_year - data["year"]

        feature_dict = {
            "area": [float(data["area"])],
            "rooms": [int(data["rooms"])],
            "floor": [int(data.get("floor", 1))],
            "house_age": [house_age],
            "district": [data["district"]],
        }

        return pd.DataFrame(feature_dict)[FEATURE_ORDER]

    def _heuristic_predict(self, data):
        """Fallback prediction using district average price_per_sqm x area."""
        price_per_sqm = self._get_district_avg_price_per_sqm(data["district"])
        area = float(data["area"])

        # Adjust for room count and age
        room_factor = 1.0 + (int(data["rooms"]) - 3) * 0.05
        current_year = datetime.now().year
        house_age = current_year - int(data["year"])
        age_factor = max(0.7, 1.0 - house_age * 0.005)

        return price_per_sqm * area * room_factor * age_factor

    def predict(self, data):
        """Make prediction using the loaded model, or heuristic fallback."""
        if self._model is None or self._preprocessor is None:
            return self._heuristic_predict(data)

        try:
            df = self._prepare_features(data)
            X_processed = self._preprocessor.transform(df)
            prediction = self._model.predict(X_processed)[0]
            return float(prediction)

        except Exception as e:
            logger.warning("Model prediction failed, using heuristic: %s", e)
            return self._heuristic_predict(data)

    def predict_batch(self, data_list):
        """Batch prediction: process multiple inputs in a single model call.

        Args:
            data_list: list of dicts, each with keys: area, rooms, floor, year, district

        Returns:
            list of float predictions, same order as input
        """
        if not data_list:
            return []

        if self._model is None or self._preprocessor is None:
            return [self._heuristic_predict(d) for d in data_list]

        try:
            frames = [self._prepare_features(d) for d in data_list]
            df = pd.concat(frames, ignore_index=True)
            X_processed = self._preprocessor.transform(df)
            predictions = self._model.predict(X_processed)
            return [float(p) for p in predictions]

        except Exception as e:
            logger.warning("Batch prediction failed, falling back to individual: %s", e)
            return [self._heuristic_predict(d) for d in data_list]

    def health_check(self):
        """Check if model is healthy and ready for predictions"""
        if self._model is None:
            return False

        model_path = os.path.join(settings.ML_MODEL_DIR, "house_price_model.pkl")
        if not os.path.exists(model_path):
            return False

        return True

    def get_model_info(self):
        """Get model information"""
        return {
            "model_type": str(type(self._model)),
            "model_version": self._model_version,
            "last_loaded": self._last_loaded,
            "features": self.get_feature_names(),
            "healthy": self.health_check()
        }


# Global instance
model_service = ModelService()
