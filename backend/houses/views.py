from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response

from .filters import HouseFilterSet
from .models import House
from .pagination import HousePagination
from .serializers import HouseListSerializer, HouseDetailSerializer, HouseMapSerializer


class HouseViewSet(viewsets.ModelViewSet):
    queryset = House.objects.all()
    serializer_class = HouseDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = HouseFilterSet
    ordering_fields = ["price", "area", "year", "created_at"]
    ordering = ["-created_at"]
    pagination_class = HousePagination

    def get_serializer_class(self):
        if self.action == "list":
            return HouseListSerializer
        return HouseDetailSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def map_houses(request):
    """Return all houses (no pagination) with map-relevant fields only.

    Supports same filter params as the list endpoint:
    district, rooms, min_price, max_price, min_area, max_area.
    """
    queryset = House.objects.exclude(lat__isnull=True).exclude(lng__isnull=True)

    filterset = HouseFilterSet(request.query_params, queryset=queryset)
    if filterset.is_valid():
        queryset = filterset.qs

    serializer = HouseMapSerializer(queryset, many=True)
    return Response(serializer.data)
