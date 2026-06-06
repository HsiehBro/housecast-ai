from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import HouseViewSet, map_houses

router = DefaultRouter()
router.register(r"", HouseViewSet, basename="house")

urlpatterns = [
    path("map/", map_houses, name="map-houses"),
    path("", include(router.urls)),
]
