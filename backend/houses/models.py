from decimal import Decimal

from django.db import models


class House(models.Model):
    STATUS_CHOICES = [
        ("available", "在售"),
        ("sold", "已售"),
        ("off", "下架"),
    ]

    ORIENTATION_CHOICES = [
        ("东", "东"),
        ("南", "南"),
        ("西", "西"),
        ("北", "北"),
        ("东南", "东南"),
        ("西南", "西南"),
        ("东北", "东北"),
        ("西北", "西北"),
    ]

    DECORATION_CHOICES = [
        ("毛坯", "毛坯"),
        ("简装", "简装"),
        ("精装", "精装"),
        ("豪装", "豪装"),
    ]

    PROPERTY_TYPE_CHOICES = [
        ("住宅", "住宅"),
        ("公寓", "公寓"),
        ("别墅", "别墅"),
        ("商住", "商住"),
        ("其他", "其他"),
    ]

    # 基本信息
    name = models.CharField("小区名称", max_length=200, default="")
    address = models.CharField("详细地址", max_length=300, default="")
    district = models.CharField("小区/区域", max_length=100)
    property_type = models.CharField(
        "房源类型", max_length=10,
        choices=PROPERTY_TYPE_CHOICES, default="住宅"
    )

    # 房屋属性
    area = models.FloatField("房屋面积(㎡)")
    rooms = models.IntegerField("房间数量")
    halls = models.IntegerField("厅数量", default=1)
    bathrooms = models.IntegerField("卫生间数量", default=1)
    floor = models.IntegerField("所在楼层")
    total_floors = models.IntegerField("总楼层", default=1)
    year = models.IntegerField("建造年份")
    orientation = models.CharField(
        "朝向", max_length=10,
        choices=ORIENTATION_CHOICES, default="南"
    )
    decoration = models.CharField(
        "装修情况", max_length=10,
        choices=DECORATION_CHOICES, default="精装"
    )

    # 价格信息
    price = models.DecimalField("总价(元)", max_digits=12, decimal_places=2)
    price_per_sqm = models.DecimalField(
        "单价(元/㎡)", max_digits=10, decimal_places=2, default=0
    )

    # 位置信息
    lat = models.FloatField("纬度", null=True, blank=True)
    lng = models.FloatField("经度", null=True, blank=True)

    # 状态信息
    status = models.CharField(
        "状态", max_length=10,
        choices=STATUS_CHOICES, default="available"
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "houses"
        verbose_name = "房源"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name or self.district} {self.area}㎡ {self.rooms}室"

    def save(self, *args, **kwargs):
        """Auto-calculate price_per_sqm from total price and area."""
        if self.area and self.area > 0 and self.price:
            self.price_per_sqm = Decimal(str(self.price)) / Decimal(str(self.area))
            self.price_per_sqm = self.price_per_sqm.quantize(Decimal("0.01"))
        super().save(*args, **kwargs)
