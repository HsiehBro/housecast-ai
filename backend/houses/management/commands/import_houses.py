"""
Django management command for importing house data from CSV files.

Usage:
    uv run python manage.py import_houses <csv_path>
    uv run python manage.py import_houses --generate-sample
    uv run python manage.py import_houses --generate-sample --count 2000

Features:
    - CSV file reading with pandas
    - Data cleaning and validation (required fields, value ranges, district choices)
    - Bulk insert via Django ORM (bulk_create, batch size 500)
    - Progress display (every 100 records)
    - Duplicate handling (skip records with same name + address + area)
    - Anomaly logging to file
    - Sample data generation for Shanghai districts
"""

import csv
import logging
import os
import random
from datetime import datetime
from decimal import Decimal

import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from houses.models import House

logger = logging.getLogger(__name__)

VALID_STATUSES = [choice[0] for choice in House.STATUS_CHOICES]
VALID_ORIENTATIONS = [choice[0] for choice in House.ORIENTATION_CHOICES]
VALID_DECORATIONS = [choice[0] for choice in House.DECORATION_CHOICES]
VALID_PROPERTY_TYPES = [choice[0] for choice in House.PROPERTY_TYPE_CHOICES]

# Required fields that must not be null/empty
REQUIRED_FIELDS = ["area", "rooms", "year", "district", "price"]

# District price tiers for sample data generation (Xi'an Gaoling District)
# Key: community name, Value: (price_per_sqm_min, price_per_sqm_max) in yuan/sqm
COMMUNITY_PRICE_TIERS = {
    "泾渭上城": (5500, 7500),
    "泾渭佳苑": (4500, 6500),
    "高陵天下": (6000, 8500),
    "鹿苑小区": (4000, 6000),
    "崇皇花园": (5000, 7000),
    "泾渭新城": (4800, 6800),
    "渭水茗居": (5200, 7200),
    "高陵碧桂园": (6500, 9000),
    "鹿苑华庭": (5800, 8000),
    "泾渭春天": (4200, 6200),
    "崇皇新城": (4500, 6500),
    "渭水家园": (3800, 5800),
    "高陵恒大": (6000, 8500),
    "泾渭明珠": (5000, 7000),
    "鹿苑新城": (4600, 6600),
}

COMMUNITY_WEIGHTS = {
    "泾渭上城": 12,
    "泾渭佳苑": 10,
    "高陵天下": 8,
    "鹿苑小区": 10,
    "崇皇花园": 8,
    "泾渭新城": 9,
    "渭水茗居": 7,
    "高陵碧桂园": 6,
    "鹿苑华庭": 7,
    "泾渭春天": 8,
    "崇皇新城": 6,
    "渭水家园": 5,
    "高陵恒大": 5,
    "泾渭明珠": 6,
    "鹿苑新城": 5,
}

COMMUNITY_COORDS = {
    "泾渭上城": (34.531, 109.089),
    "泾渭佳苑": (34.528, 109.085),
    "高陵天下": (34.535, 109.092),
    "鹿苑小区": (34.533, 109.080),
    "崇皇花园": (34.540, 109.095),
    "泾渭新城": (34.526, 109.088),
    "渭水茗居": (34.538, 109.083),
    "高陵碧桂园": (34.532, 109.098),
    "鹿苑华庭": (34.529, 109.078),
    "泾渭春天": (34.525, 109.091),
    "崇皇新城": (34.542, 109.087),
    "渭水家园": (34.536, 109.076),
    "高陵恒大": (34.530, 109.100),
    "泾渭明珠": (34.527, 109.082),
    "鹿苑新城": (34.534, 109.074),
}

# Sub-district mapping for Gaoling District, Xi'an
COMMUNITY_DISTRICTS = {
    "泾渭上城": "泾渭街道",
    "泾渭佳苑": "泾渭街道",
    "泾渭新城": "泾渭街道",
    "泾渭春天": "泾渭街道",
    "泾渭明珠": "泾渭街道",
    "高陵天下": "鹿苑街道",
    "鹿苑小区": "鹿苑街道",
    "鹿苑华庭": "鹿苑街道",
    "鹿苑新城": "鹿苑街道",
    "崇皇花园": "崇皇街道",
    "崇皇新城": "崇皇街道",
    "渭水茗居": "渭水片区",
    "渭水家园": "渭水片区",
    "高陵碧桂园": "通远街道",
    "高陵恒大": "耿镇街道",
}


class Command(BaseCommand):
    help = "Import house data from CSV file or generate sample data"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=str,
            nargs="?",
            help="Path to the CSV file containing house data",
        )
        parser.add_argument(
            "--generate-sample",
            action="store_true",
            help="Generate sample data instead of importing from CSV",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=1500,
            help="Number of sample records to generate (default: 1500)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Batch size for bulk_create (default: 500)",
        )
        parser.add_argument(
            "--skip-duplicates",
            action="store_true",
            default=True,
            help="Skip records that already exist (default: True)",
        )
        parser.add_argument(
            "--log-errors",
            type=str,
            default="import_errors.log",
            help="File path for error logging (default: import_errors.log)",
        )

    def handle(self, *args, **options):
        self.batch_size = options["batch_size"]
        self.skip_duplicates = options["skip_duplicates"]
        self.error_log_path = options["log_errors"]
        self.error_records = []

        if options["generate_sample"]:
            self.stdout.write(
                self.style.WARNING(
                    f"Generating {options['count']} sample records..."
                )
            )
            df = self.generate_sample_data(options["count"])
        elif options["csv_file"]:
            csv_file = options["csv_file"]
            if not os.path.exists(csv_file):
                raise CommandError(f"File not found: {csv_file}")
            df = self.read_csv(csv_file)
        else:
            raise CommandError(
                "Either provide a CSV file path or use --generate-sample"
            )

        if df.empty:
            self.stderr.write(self.style.ERROR("No data to import."))
            return

        # Clean and validate
        df = self.clean_data(df)

        if df.empty:
            self.stderr.write(self.style.ERROR(
                "No valid records remaining after cleaning."
            ))
            self.write_error_log()
            return

        # Import to database
        self.import_to_database(df)

        # Write error log if there were anomalies
        self.write_error_log()

    def read_csv(self, csv_file):
        """Read CSV file with proper encoding handling."""
        self.stdout.write(f"Reading CSV file: {csv_file}")

        # Try common encodings
        for encoding in ("utf-8", "utf-8-sig", "gbk", "gb2312", "latin-1"):
            try:
                df = pd.read_csv(csv_file, encoding=encoding)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully read {len(df)} records "
                        f"(encoding: {encoding})"
                    )
                )
                return df
            except (UnicodeDecodeError, UnicodeError):
                continue

        raise CommandError(
            f"Could not read CSV file with any supported encoding: {csv_file}"
        )

    def clean_data(self, df):
        """Clean and validate the data."""
        self.stdout.write("Cleaning and validating data...")
        initial_count = len(df)

        # Normalize column names: strip whitespace, lowercase
        df.columns = df.columns.str.strip().str.lower()

        # Column name mapping: support common CSV header variants
        column_mapping = {
            "区域": "district",
            "区": "district",
            "面积": "area",
            "房间": "rooms",
            "卧室": "rooms",
            "室": "rooms",
            "楼层": "floor",
            "总楼层": "total_floors",
            "年份": "year",
            "建造年份": "year",
            "价格": "price",
            "总价": "price",
            "厅": "halls",
            "卫生间": "bathrooms",
            "纬度": "lat",
            "经度": "lng",
            "状态": "status",
            "小区": "name",
            "小区名称": "name",
            "地址": "address",
            "类型": "property_type",
            "房源类型": "property_type",
            "朝向": "orientation",
            "装修": "decoration",
            "装修情况": "decoration",
            "单价": "price_per_sqm",
        }
        df = df.rename(columns=column_mapping)

        # Track rows before each filter step
        def log_step(step_name, before, after):
            removed = before - after
            if removed > 0:
                self.stdout.write(f"  {step_name}: removed {removed} records")

        # Step 1: Check required fields exist
        missing_fields = [
            f for f in REQUIRED_FIELDS if f not in df.columns
        ]
        if missing_fields:
            raise CommandError(
                f"Missing required columns in CSV: {missing_fields}"
            )

        # Step 2: Drop rows with missing required fields
        before = len(df)
        df = df.dropna(subset=REQUIRED_FIELDS)
        # Also treat empty strings as missing
        for field in REQUIRED_FIELDS:
            if df[field].dtype == object:
                df = df[df[field].astype(str).str.strip() != ""]
        log_step("Drop missing required fields", before, len(df))

        # Step 3: Convert numeric fields
        numeric_fields = [
            "area", "rooms", "floor", "year", "price",
            "halls", "bathrooms", "total_floors", "lat", "lng",
        ]
        for field in numeric_fields:
            if field in df.columns:
                df[field] = pd.to_numeric(df[field], errors="coerce")

        # Drop rows where essential numeric fields became NaN
        essential_numeric = ["area", "rooms", "year", "price"]
        before = len(df)
        df = df.dropna(subset=essential_numeric)
        log_step("Drop invalid numeric values", before, len(df))

        # Step 4: Value range validation
        before = len(df)
        invalid_mask = (
            (df["area"] <= 0) |
            (df["area"] > 2000) |
            (df["rooms"] < 1) |
            (df["rooms"] > 20) |
            (df["year"] < 1900) |
            (df["year"] > 2030) |
            (df["price"] <= 0)
        )
        # Log invalid records
        invalid_df = df[invalid_mask]
        for _, row in invalid_df.iterrows():
            reasons = []
            if row["area"] <= 0 or row["area"] > 2000:
                reasons.append(f"area={row['area']}")
            if row["rooms"] < 1 or row["rooms"] > 20:
                reasons.append(f"rooms={row['rooms']}")
            if row["year"] < 1900 or row["year"] > 2030:
                reasons.append(f"year={row['year']}")
            if row["price"] <= 0:
                reasons.append(f"price={row['price']}")
            self.error_records.append({
                "type": "value_range",
                "data": row.to_dict(),
                "reason": ", ".join(reasons),
            })

        df = df[~invalid_mask]
        log_step("Value range validation", before, len(df))

        # Step 5: Validate district is not empty
        before = len(df)
        invalid_district_mask = (
            df["district"].isna() |
            (df["district"].astype(str).str.strip() == "")
        )
        for _, row in df[invalid_district_mask].iterrows():
            self.error_records.append({
                "type": "invalid_district",
                "data": row.to_dict(),
                "reason": "district is empty",
            })
        df = df[~invalid_district_mask]
        log_step("Empty district filter", before, len(df))

        # Step 6: Validate optional choice fields
        if "status" in df.columns:
            invalid_status = ~df["status"].isin(VALID_STATUSES) & \
                             df["status"].notna()
            df.loc[invalid_status, "status"] = "available"

        if "orientation" in df.columns:
            invalid_ori = ~df["orientation"].isin(VALID_ORIENTATIONS) & \
                          df["orientation"].notna()
            df.loc[invalid_ori, "orientation"] = "南"

        if "decoration" in df.columns:
            invalid_dec = ~df["decoration"].isin(VALID_DECORATIONS) & \
                          df["decoration"].notna()
            df.loc[invalid_dec, "decoration"] = "精装"

        if "property_type" in df.columns:
            invalid_pt = ~df["property_type"].isin(VALID_PROPERTY_TYPES) & \
                         df["property_type"].notna()
            df.loc[invalid_pt, "property_type"] = "住宅"

        # Step 7: Set defaults for optional fields
        default_values = {
            "name": "",
            "address": "",
            "halls": 1,
            "bathrooms": 1,
            "floor": 1,
            "total_floors": 6,
            "property_type": "住宅",
            "orientation": "南",
            "decoration": "精装",
            "status": "available",
            "lat": np.nan,
            "lng": np.nan,
            "price_per_sqm": 0,
        }
        for col, default in default_values.items():
            if col not in df.columns:
                df[col] = default

        # Ensure floor is at least 1
        df["floor"] = df["floor"].fillna(1).clip(lower=1).astype(int)
        df["total_floors"] = df["total_floors"].fillna(6).clip(lower=1)
        df["total_floors"] = df["total_floors"].astype(int)
        df["rooms"] = df["rooms"].astype(int)
        df["halls"] = df["halls"].fillna(1).astype(int)
        df["bathrooms"] = df["bathrooms"].fillna(1).astype(int)
        df["year"] = df["year"].astype(int)

        # Ensure floor does not exceed total_floors
        df["floor"] = df[["floor", "total_floors"]].min(axis=1)

        self.stdout.write(
            self.style.SUCCESS(
                f"Cleaning complete: {len(df)}/{initial_count} "
                f"records valid ({initial_count - len(df)} removed)"
            )
        )
        return df.reset_index(drop=True)

    def import_to_database(self, df):
        """Import cleaned data to database using bulk_create."""
        self.stdout.write("Importing to database...")
        total = len(df)
        success_count = 0
        duplicate_count = 0
        error_count = 0

        # Build set of existing records for duplicate detection
        existing_keys = set()
        if self.skip_duplicates:
            existing_records = House.objects.all().values_list(
                "name", "address", "area"
            )
            existing_keys = {
                (r[0], r[1], round(r[2], 2)) for r in existing_records
            }
            self.stdout.write(
                f"Found {len(existing_keys)} existing records for "
                f"deduplication check"
            )

        # Process in batches
        for start in range(0, total, self.batch_size):
            end = min(start + self.batch_size, total)
            batch_df = df.iloc[start:end]
            houses_to_create = []

            for _, row in batch_df.iterrows():
                # Duplicate check
                if self.skip_duplicates:
                    key = (
                        str(row.get("name", "")),
                        str(row.get("address", "")),
                        round(float(row["area"]), 2),
                    )
                    if key in existing_keys:
                        duplicate_count += 1
                        continue
                    existing_keys.add(key)

                try:
                    house = House(
                        name=str(row.get("name", ""))[:200],
                        address=str(row.get("address", ""))[:300],
                        district=row["district"],
                        property_type=str(
                            row.get("property_type", "住宅")
                        ),
                        area=float(row["area"]),
                        rooms=int(row["rooms"]),
                        halls=int(row.get("halls", 1)),
                        bathrooms=int(row.get("bathrooms", 1)),
                        floor=int(row["floor"]),
                        total_floors=int(row.get("total_floors", 6)),
                        year=int(row["year"]),
                        orientation=str(row.get("orientation", "南")),
                        decoration=str(row.get("decoration", "精装")),
                        price=Decimal(str(round(float(row["price"]), 2))),
                        lat=float(row["lat"]) if pd.notna(row.get("lat"))
                        else None,
                        lng=float(row["lng"]) if pd.notna(row.get("lng"))
                        else None,
                        status=str(row.get("status", "available")),
                    )
                    houses_to_create.append(house)
                except (ValueError, TypeError) as exc:
                    error_count += 1
                    self.error_records.append({
                        "type": "create_error",
                        "data": row.to_dict(),
                        "reason": str(exc),
                    })

            if houses_to_create:
                try:
                    with transaction.atomic():
                        # Pre-calculate price_per_sqm since bulk_create skips save()
                        for h in houses_to_create:
                            if h.area and h.area > 0 and h.price:
                                h.price_per_sqm = Decimal(str(h.price)) / Decimal(str(h.area))
                                h.price_per_sqm = h.price_per_sqm.quantize(Decimal("0.01"))
                        created = House.objects.bulk_create(
                            houses_to_create,
                            batch_size=self.batch_size,
                        )
                        success_count += len(created)
                except Exception as exc:
                    error_count += len(houses_to_create)
                    self.stderr.write(
                        self.style.ERROR(
                            f"Batch insert failed (rows {start}-{end}): "
                            f"{exc}"
                        )
                    )
                    self.error_records.append({
                        "type": "batch_error",
                        "data": {"start": start, "end": end},
                        "reason": str(exc),
                    })

            # Progress display every 100 records or at end of batch
            processed = min(end, total)
            if processed % 100 < self.batch_size or end == total:
                progress = processed / total * 100
                self.stdout.write(
                    f"Progress: {progress:.1f}% "
                    f"({processed}/{total}) - "
                    f"imported: {success_count}, "
                    f"duplicates skipped: {duplicate_count}"
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete: {success_count} records imported, "
                f"{duplicate_count} duplicates skipped, "
                f"{error_count} errors"
            )
        )

        # Verify import
        db_count = House.objects.count()
        self.stdout.write(f"Total records in database: {db_count}")

    def generate_sample_data(self, count):
        """Generate realistic sample house data for Xi'an Gaoling District."""
        self.stdout.write(f"Generating {count} sample records...")

        communities = list(COMMUNITY_WEIGHTS.keys())
        weights = list(COMMUNITY_WEIGHTS.values())

        # Area ranges by room count (70-180㎡)
        AREA_BY_ROOMS = {
            1: (70, 85),
            2: (80, 110),
            3: (100, 140),
            4: (130, 180),
        }

        records = []
        for i in range(count):
            community = random.choices(communities, weights=weights, k=1)[0]
            price_tier = COMMUNITY_PRICE_TIERS[community]
            coords = COMMUNITY_COORDS[community]
            sub_district = COMMUNITY_DISTRICTS[community]

            # Rooms first, then area based on rooms
            rooms = random.choices([1, 2, 3, 4], weights=[5, 30, 45, 20], k=1)[0]
            area_min, area_max = AREA_BY_ROOMS[rooms]
            area = round(random.uniform(area_min, area_max), 1)

            halls = max(1, rooms - 1) if rooms > 1 else 1
            bathrooms = 1 if rooms <= 2 else random.choices(
                [1, 2], weights=[40, 60], k=1
            )[0]

            # Floors capped at 30
            total_floors = random.choices(
                [6, 11, 18, 25, 30], weights=[15, 25, 30, 20, 10], k=1
            )[0]
            floor = random.randint(1, total_floors)

            # Year only 2025 or 2026
            year = random.choice([2025, 2026])

            # Price = area × price_per_sqm
            base_pps = random.uniform(price_tier[0], price_tier[1])
            pps = base_pps * random.uniform(0.9, 1.1)
            pps = round(pps, 2)
            total_price = round(area * pps, 2)

            if rooms == 1:
                property_type = random.choices(
                    ["公寓", "住宅"], weights=[50, 50], k=1
                )[0]
            elif rooms == 4 and area > 150:
                property_type = random.choices(
                    ["住宅", "别墅"], weights=[80, 20], k=1
                )[0]
            else:
                property_type = random.choices(
                    ["住宅", "公寓"], weights=[85, 15], k=1
                )[0]

            orientation = random.choices(
                VALID_ORIENTATIONS,
                weights=[10, 50, 5, 2, 15, 8, 5, 5],
                k=1,
            )[0]

            decoration = random.choices(
                VALID_DECORATIONS,
                weights=[10, 25, 50, 15],
                k=1,
            )[0]

            lat = round(coords[0] + random.uniform(-0.01, 0.01), 6)
            lng = round(coords[1] + random.uniform(-0.01, 0.01), 6)

            building_num = random.randint(1, 20)
            unit_num = random.randint(1, 6)
            name = community
            address = f"西安市高陵区{sub_district}{community}{building_num}栋{unit_num}单元"

            status = random.choices(
                VALID_STATUSES, weights=[85, 10, 5], k=1
            )[0]

            records.append({
                "name": name,
                "address": address,
                "district": sub_district,
                "property_type": property_type,
                "area": area,
                "rooms": rooms,
                "halls": halls,
                "bathrooms": bathrooms,
                "floor": floor,
                "total_floors": total_floors,
                "year": year,
                "orientation": orientation,
                "decoration": decoration,
                "price": total_price,
                "price_per_sqm": pps,
                "lat": lat,
                "lng": lng,
                "status": status,
            })

        df = pd.DataFrame(records)
        self.stdout.write(
            self.style.SUCCESS(
                f"Generated {len(df)} sample records across "
                f"{df['district'].nunique()} sub-districts"
            )
        )
        return df

    def write_error_log(self):
        """Write error records to a log file."""
        if not self.error_records:
            return

        log_path = self.error_log_path
        self.stdout.write(
            self.style.WARNING(
                f"Writing {len(self.error_records)} error records "
                f"to {log_path}"
            )
        )

        try:
            with open(log_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "error_type", "reason",
                    "district", "area", "rooms", "year", "price"
                ])
                for record in self.error_records:
                    data = record.get("data", {})
                    if isinstance(data, dict):
                        writer.writerow([
                            datetime.now().isoformat(),
                            record.get("type", ""),
                            record.get("reason", ""),
                            data.get("district", ""),
                            data.get("area", ""),
                            data.get("rooms", ""),
                            data.get("year", ""),
                            data.get("price", ""),
                        ])
                    else:
                        writer.writerow([
                            datetime.now().isoformat(),
                            record.get("type", ""),
                            record.get("reason", ""),
                            "", "", "", "", str(data),
                        ])
        except OSError as exc:
            self.stderr.write(
                self.style.ERROR(f"Failed to write error log: {exc}")
            )
