import logging
from datetime import datetime

from django.db.models import Avg, Count
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .service import model_service
from .explainability import explainability_service
from .versioning import version_manager
from houses.models import House

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def predict_price(request):
    """Predict house price based on input features"""
    try:
        # Validate input data
        data = request.data
        required_fields = ["area", "rooms", "year", "district"]

        for field in required_fields:
            if field not in data:
                return Response(
                    {"error": f"Missing required field: {field}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Prepare data for prediction
        prediction_data = {
            "area": float(data["area"]),
            "rooms": int(data["rooms"]),
            "floor": int(data.get("floor", 1)),  # Default to 1st floor if not provided
            "year": int(data["year"]),
            "district": data["district"],
            "lat": float(data.get("lat", 0.0)),
            "lng": float(data.get("lng", 0.0)),
        }

        # Validate district
        valid_districts = list(
            House.objects.values_list("district", flat=True).distinct()
        )
        if valid_districts and prediction_data["district"] not in valid_districts:
            return Response(
                {"error": f"Invalid district. Valid districts: {', '.join(valid_districts)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Make prediction
        predicted_price = model_service.predict(prediction_data)

        # Get feature importance (simplified - in real implementation would need model's feature_importances_)
        feature_importance = {
            "area": 0.35,
            "rooms": 0.25,
            "district": 0.20,
            "year": 0.10,
            "floor": 0.05,
            "location": 0.05
        }

        # Calculate confidence (simplified - in real implementation would use model's prediction intervals)
        confidence = 0.85

        response_data = {
            "predicted_price": round(predicted_price, 2),
            "confidence": confidence,
            "feature_importance": feature_importance,
            "input_data": prediction_data
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except ValueError as e:
        return Response(
            {"error": f"Invalid input data: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {"error": f"Prediction failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def model_info(request):
    """Get model information and health status"""
    try:
        model_info = model_service.get_model_info()
        return Response(model_info, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def explain_prediction(request):
    """Explain a prediction using SHAP values"""
    try:
        # Validate input data
        data = request.data
        required_fields = ["area", "rooms", "year", "district"]

        for field in required_fields:
            if field not in data:
                return Response(
                    {"error": f"Missing required field: {field}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Prepare data for explanation
        features = {
            "area": float(data["area"]),
            "rooms": int(data["rooms"]),
            "floor": int(data.get("floor", 1)),
            "year": int(data["year"]),
            "district": data["district"],
            "lat": float(data.get("lat", 0.0)),
            "lng": float(data.get("lng", 0.0)),
        }

        # Get explanation
        explanation = explainability_service.explain_prediction(features)

        return Response(explanation, status=status.HTTP_200_OK)

    except ValueError as e:
        return Response(
            {"error": f"Invalid input data: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {"error": f"Explanation failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def model_versions(request):
    """Get all model versions"""
    try:
        versions = version_manager.list_versions()
        return Response({"versions": versions}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def trend_prediction(request):
    """Return historical and predicted avg price_per_sqm by year"""
    try:
        years_ahead = int(request.query_params.get("years", 3))
        years_ahead = min(max(years_ahead, 1), 10)
    except (TypeError, ValueError):
        years_ahead = 3

    historical_qs = (
        House.objects.values("year")
        .annotate(avg_price=Avg("price_per_sqm"), cnt=Count("id"))
        .order_by("year")
    )
    historical = [
        {"year": row["year"], "avg_price": round(float(row["avg_price"]), 2)}
        for row in historical_qs
        if row["avg_price"] is not None
    ]

    if not historical:
        return Response({"historical": [], "predicted": [], "method": "none"})

    current_year = datetime.now().year
    last_hist_price = historical[-1]["avg_price"]
    last_hist_year = historical[-1]["year"]
    future_years = list(range(current_year + 1, current_year + 1 + years_ahead))

    predicted = []
    method = "cagr"
    try:
        if model_service.health_check():
            districts = list(
                House.objects.values_list("district", flat=True).distinct()
            )
            latest_houses = House.objects.filter(year=last_hist_year)
            if not latest_houses.exists():
                latest_houses = House.objects.all().order_by("-created_at")[:50]

            area_values = list(
                latest_houses.exclude(area__isnull=True)
                .order_by("area").values_list("area", flat=True)
            )
            median_area = float(area_values[len(area_values) // 2]) if area_values else 100.0

            room_values = list(
                latest_houses.exclude(rooms__isnull=True)
                .order_by("rooms").values_list("rooms", flat=True)
            )
            median_rooms = int(room_values[len(room_values) // 2]) if room_values else 3

            floor_values = list(
                latest_houses.exclude(floor__isnull=True)
                .order_by("floor").values_list("floor", flat=True)
            )
            median_floor = int(floor_values[len(floor_values) // 2]) if floor_values else 6

            # Build all prediction inputs at once for batch processing
            batch_inputs = []
            for yr in future_years:
                for district in districts:
                    batch_inputs.append({
                        "area": median_area,
                        "rooms": median_rooms,
                        "floor": median_floor,
                        "year": yr,
                        "district": district,
                        "lat": 0.0,
                        "lng": 0.0,
                    })

            batch_results = model_service.predict_batch(batch_inputs)

            # Reshape results: results are ordered by year then district
            idx = 0
            for yr in future_years:
                district_prices = []
                for _ in districts:
                    if idx < len(batch_results):
                        pred = batch_results[idx]
                        per_sqm = pred / median_area if median_area else pred
                        district_prices.append(per_sqm)
                    idx += 1
                if district_prices:
                    avg_price = sum(district_prices) / len(district_prices)
                    predicted.append({"year": yr, "avg_price": round(avg_price, 2)})
                else:
                    predicted.append({"year": yr, "avg_price": round(last_hist_price, 2)})
            method = "model"
        else:
            raise Exception("Model not loaded")
    except Exception as exc:
        logger.warning("Model-based trend prediction failed, using CAGR: %s", exc)
        if len(historical) >= 2:
            first_price = historical[0]["avg_price"]
            first_year = historical[0]["year"]
            n_years = last_hist_year - first_year
            cagr = (
                (last_hist_price / first_price) ** (1 / n_years) - 1
                if n_years > 0 and first_price > 0
                else 0.02
            )
        else:
            cagr = 0.02

        for yr in future_years:
            years_diff = yr - last_hist_year
            price = last_hist_price * ((1 + cagr) ** years_diff)
            predicted.append({"year": yr, "avg_price": round(price, 2)})

    return Response({
        "historical": historical,
        "predicted": predicted,
        "method": method,
    })


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def current_version(request):
    """Get current model version info"""
    try:
        version_info = version_manager.get_current_version()
        if not version_info:
            return Response(
                {"error": "No model version found"},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(version_info, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def rollback_version(request):
    """Rollback to specific version"""
    try:
        version = int(request.data.get("version"))
        if not version:
            return Response(
                {"error": "Version number is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        success = version_manager.rollback_to_version(version)
        if success:
            return Response(
                {"message": f"Successfully rolled back to version {version}"},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": f"Version {version} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    except ValueError:
        return Response(
            {"error": "Invalid version number"},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )