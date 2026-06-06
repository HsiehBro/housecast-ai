from django_filters import rest_framework as django_filters

from .models import House


class HouseFilterSet(django_filters.FilterSet):
    """Custom filterset with range filters for price, area, and year."""

    min_price = django_filters.NumberFilter(
        field_name="price", lookup_expr="gte", label="最低价格"
    )
    max_price = django_filters.NumberFilter(
        field_name="price", lookup_expr="lte", label="最高价格"
    )
    min_area = django_filters.NumberFilter(
        field_name="area", lookup_expr="gte", label="最小面积"
    )
    max_area = django_filters.NumberFilter(
        field_name="area", lookup_expr="lte", label="最大面积"
    )
    year_min = django_filters.NumberFilter(
        field_name="year", lookup_expr="gte", label="最早年份"
    )
    year_max = django_filters.NumberFilter(
        field_name="year", lookup_expr="lte", label="最晚年份"
    )

    class Meta:
        model = House
        fields = [
            "district",
            "rooms",
            "status",
            "property_type",
            "orientation",
            "decoration",
        ]
