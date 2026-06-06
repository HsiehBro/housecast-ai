from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import House

User = get_user_model()


class HouseModelTests(TestCase):
    """Test the House model and its auto-calculation logic."""

    def setUp(self):
        self.house_data = {
            "name": "测试小区",
            "address": "测试路1号",
            "district": "浦东新区",
            "property_type": "住宅",
            "area": 100.0,
            "rooms": 3,
            "halls": 2,
            "bathrooms": 1,
            "floor": 5,
            "total_floors": 20,
            "year": 2020,
            "orientation": "南",
            "decoration": "精装",
            "price": Decimal("5000000.00"),
        }

    def test_auto_calculate_price_per_sqm(self):
        house = House.objects.create(**self.house_data)
        self.assertEqual(house.price_per_sqm, Decimal("50000.00"))

    def test_auto_calculate_price_per_sqm_rounding(self):
        data = {**self.house_data, "area": 70.0, "price": Decimal("4900000.00")}
        house = House.objects.create(**data)
        self.assertEqual(house.price_per_sqm, Decimal("70000.00"))

    def test_str_representation(self):
        house = House.objects.create(**self.house_data)
        self.assertIn("测试小区", str(house))
        self.assertIn("100", str(house))


class HouseSerializerTests(TestCase):
    """Test serializer validation rules."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.valid_data = {
            "name": "测试小区",
            "address": "测试路1号",
            "district": "浦东新区",
            "property_type": "住宅",
            "area": 100.0,
            "rooms": 3,
            "halls": 2,
            "bathrooms": 1,
            "floor": 5,
            "total_floors": 20,
            "year": 2020,
            "orientation": "南",
            "decoration": "精装",
            "price": "5000000.00",
        }

    def test_create_house_with_valid_data(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/houses/", self.valid_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["price_per_sqm"], "50000.00")

    def test_area_must_be_positive(self):
        self.client.force_authenticate(user=self.user)
        data = {**self.valid_data, "area": -10}
        response = self.client.post("/api/houses/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("area", response.data)

    def test_area_zero_invalid(self):
        self.client.force_authenticate(user=self.user)
        data = {**self.valid_data, "area": 0}
        response = self.client.post("/api/houses/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rooms_must_be_at_least_one(self):
        self.client.force_authenticate(user=self.user)
        data = {**self.valid_data, "rooms": 0}
        response = self.client.post("/api/houses/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("rooms", response.data)

    def test_price_must_be_positive(self):
        self.client.force_authenticate(user=self.user)
        data = {**self.valid_data, "price": "-100"}
        response = self.client.post("/api/houses/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", response.data)

    def test_year_range_validation(self):
        self.client.force_authenticate(user=self.user)
        data = {**self.valid_data, "year": 1800}
        response = self.client.post("/api/houses/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("year", response.data)

    def test_year_upper_bound_validation(self):
        self.client.force_authenticate(user=self.user)
        data = {**self.valid_data, "year": 2100}
        response = self.client.post("/api/houses/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_floor_exceeds_total_floors(self):
        self.client.force_authenticate(user=self.user)
        data = {**self.valid_data, "floor": 25, "total_floors": 20}
        response = self.client.post("/api/houses/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_floor_must_be_positive(self):
        self.client.force_authenticate(user=self.user)
        data = {**self.valid_data, "floor": 0}
        response = self.client.post("/api/houses/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_total_floors_must_be_positive(self):
        self.client.force_authenticate(user=self.user)
        data = {**self.valid_data, "total_floors": 0}
        response = self.client.post("/api/houses/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_read_only_fields_not_settable(self):
        self.client.force_authenticate(user=self.user)
        data = {**self.valid_data, "price_per_sqm": "99999.00"}
        response = self.client.post("/api/houses/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # price_per_sqm should be auto-calculated, not the injected value
        self.assertEqual(response.data["price_per_sqm"], "50000.00")


class HouseCRUDAPITests(TestCase):
    """Test full CRUD operations on the House API."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.house = House.objects.create(
            name="阳光花园",
            address="浦东路1号",
            district="浦东新区",
            property_type="住宅",
            area=120.0,
            rooms=3,
            halls=2,
            bathrooms=1,
            floor=10,
            total_floors=20,
            year=2018,
            orientation="南",
            decoration="精装",
            price=Decimal("6000000.00"),
        )
        self.detail_url = f"/api/houses/{self.house.id}/"

    # --- LIST ---
    def test_list_houses_unauthenticated(self):
        response = self.client.get("/api/houses/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_houses_returns_paginated_results(self):
        response = self.client.get("/api/houses/")
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)

    def test_list_uses_list_serializer(self):
        response = self.client.get("/api/houses/")
        if response.data["results"]:
            item = response.data["results"][0]
            # List serializer should NOT include lat/lng/address
            self.assertNotIn("lat", item)
            self.assertNotIn("lng", item)
            self.assertNotIn("address", item)

    # --- CREATE ---
    def test_create_house_unauthenticated(self):
        data = {
            "district": "黄浦区",
            "area": 80.0,
            "rooms": 2,
            "floor": 5,
            "total_floors": 10,
            "year": 2015,
            "price": "3000000.00",
        }
        response = self.client.post("/api/houses/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_house_authenticated(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "district": "黄浦区",
            "area": 80.0,
            "rooms": 2,
            "floor": 5,
            "total_floors": 10,
            "year": 2015,
            "price": "3000000.00",
        }
        response = self.client.post("/api/houses/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["district"], "黄浦区")

    # --- RETRIEVE ---
    def test_retrieve_house(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "阳光花园")
        # Detail serializer should include all fields
        self.assertIn("address", response.data)
        self.assertIn("lat", response.data)
        self.assertIn("lng", response.data)

    def test_retrieve_nonexistent_house(self):
        response = self.client.get("/api/houses/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- UPDATE ---
    def test_update_house_unauthenticated(self):
        data = {"name": "新名字", "district": "浦东新区", "area": 120.0,
                "rooms": 3, "floor": 10, "total_floors": 20,
                "year": 2018, "price": "6500000.00"}
        response = self.client.put(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_house_authenticated(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "name": "更新后名称",
            "district": "浦东新区",
            "area": 120.0,
            "rooms": 3,
            "floor": 10,
            "total_floors": 20,
            "year": 2018,
            "price": "6500000.00",
        }
        response = self.client.put(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "更新后名称")
        self.assertEqual(response.data["price"], "6500000.00")

    def test_partial_update_house(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            self.detail_url, {"name": "部分更新"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "部分更新")

    # --- DELETE ---
    def test_delete_house_unauthenticated(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_house_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(House.objects.filter(id=self.house.id).exists())

    def test_delete_nonexistent_house(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete("/api/houses/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class HouseFilterTests(TestCase):
    """Test filtering, ordering, and search functionality."""

    def setUp(self):
        self.client = APIClient()
        House.objects.create(
            name="低价房", district="浦东新区", property_type="住宅",
            area=50.0, rooms=1, floor=3, total_floors=10,
            year=2000, orientation="南", decoration="简装",
            price=Decimal("2000000.00"),
        )
        House.objects.create(
            name="高价房", district="黄浦区", property_type="别墅",
            area=200.0, rooms=4, floor=1, total_floors=3,
            year=2022, orientation="东南", decoration="豪装",
            price=Decimal("15000000.00"),
        )
        House.objects.create(
            name="中等房", district="浦东新区", property_type="公寓",
            area=80.0, rooms=2, floor=8, total_floors=20,
            year=2010, orientation="南", decoration="精装",
            price=Decimal("5000000.00"),
        )

    def test_filter_by_district(self):
        response = self.client.get("/api/houses/", {"district": "浦东新区"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_filter_by_rooms(self):
        response = self.client.get("/api/houses/", {"rooms": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "低价房")

    def test_filter_by_property_type(self):
        response = self.client.get("/api/houses/", {"property_type": "别墅"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_orientation(self):
        response = self.client.get("/api/houses/", {"orientation": "东南"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_decoration(self):
        response = self.client.get("/api/houses/", {"decoration": "豪装"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_min_price(self):
        response = self.client.get("/api/houses/", {"min_price": 6000000})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "高价房")

    def test_filter_by_max_price(self):
        response = self.client.get("/api/houses/", {"max_price": 3000000})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "低价房")

    def test_filter_by_price_range(self):
        response = self.client.get(
            "/api/houses/", {"min_price": 3000000, "max_price": 8000000}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "中等房")

    def test_filter_by_min_area(self):
        response = self.client.get("/api/houses/", {"min_area": 100})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_max_area(self):
        response = self.client.get("/api/houses/", {"max_area": 60})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_year_range(self):
        response = self.client.get(
            "/api/houses/", {"year_min": 2015, "year_max": 2025}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "高价房")

    def test_ordering_by_price(self):
        response = self.client.get("/api/houses/", {"ordering": "price"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prices = [Decimal(r["price"]) for r in response.data["results"]]
        self.assertEqual(prices, sorted(prices))

    def test_ordering_by_area_descending(self):
        response = self.client.get("/api/houses/", {"ordering": "-area"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        areas = [r["area"] for r in response.data["results"]]
        self.assertEqual(areas, sorted(areas, reverse=True))

    def test_combined_filter_and_ordering(self):
        response = self.client.get(
            "/api/houses/",
            {"district": "浦东新区", "ordering": "-price"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)


class HousePaginationTests(TestCase):
    """Test pagination behavior."""

    def setUp(self):
        self.client = APIClient()
        # Create 25 houses to exceed default page size of 20
        for i in range(25):
            House.objects.create(
                name=f"小区{i}",
                district="浦东新区",
                area=80.0,
                rooms=2,
                floor=5,
                total_floors=10,
                year=2015,
                price=Decimal("3000000.00"),
            )

    def test_default_page_size(self):
        response = self.client.get("/api/houses/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 20)
        self.assertEqual(response.data["count"], 25)

    def test_second_page(self):
        response = self.client.get("/api/houses/", {"page": 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)

    def test_custom_page_size(self):
        response = self.client.get("/api/houses/", {"page_size": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)
