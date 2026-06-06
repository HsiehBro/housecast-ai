from django.urls import path
from .views import predict_price, model_info, explain_prediction, model_versions, current_version, rollback_version, trend_prediction

urlpatterns = [
    path("predict/", predict_price, name="predict-price"),
    path("model-info/", model_info, name="model-info"),
    path("explain/", explain_prediction, name="explain-prediction"),
    path("trend/", trend_prediction, name="trend-prediction"),
    path("versions/", model_versions, name="model-versions"),
    path("versions/current/", current_version, name="current-version"),
    path("versions/rollback/", rollback_version, name="rollback-version"),
]