from rest_framework import serializers

from .models import House


class HouseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    price_per_sqm = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = House
        fields = [
            "id", "name", "district", "area", "rooms", "halls", "bathrooms",
            "floor", "total_floors", "year",
            "price", "price_per_sqm", "orientation", "decoration",
            "lat", "lng", "status", "created_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at", "price_per_sqm")


class HouseDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail / create / update views."""

    price_per_sqm = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = House
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "price_per_sqm")


class HouseMapSerializer(serializers.ModelSerializer):
    """Lightweight serializer for map views — returns only map-relevant fields."""

    price_per_sqm = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = House
        fields = [
            "id", "name", "district", "area", "rooms",
            "floor", "year", "price", "price_per_sqm",
            "lat", "lng",
        ]

    def validate_area(self, value):
        if value <= 0:
            raise serializers.ValidationError("房屋面积必须大于0")
        return value

    def validate_rooms(self, value):
        if value < 1:
            raise serializers.ValidationError("房间数量至少为1")
        return value

    def validate_year(self, value):
        if value < 1900 or value > 2030:
            raise serializers.ValidationError("建造年份应在1900-2030之间")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("房价必须大于0")
        return value

    def validate_floor(self, value):
        if value < 1:
            raise serializers.ValidationError("楼层必须大于0")
        return value

    def validate_total_floors(self, value):
        if value < 1:
            raise serializers.ValidationError("总楼层必须大于0")
        return value

    def validate(self, attrs):
        floor = attrs.get("floor")
        total_floors = attrs.get("total_floors")
        if floor is not None and total_floors is not None:
            if floor > total_floors:
                raise serializers.ValidationError(
                    {"floor": "所在楼层不能超过总楼层"}
                )
        return attrs
