import re

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "password", "password_confirm", "email", "phone")

    def validate_phone(self, value):
        if value and not re.match(r"^1[3-9]\d{9}$", value):
            raise serializers.ValidationError("请输入有效的手机号")
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("该邮箱已被注册")
        return value

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError("两次密码不一致")
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, max_length=128)
    new_password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    new_password_confirm = serializers.CharField(write_only=True, max_length=128)

    def validate_old_password(self, value):
        request = self.context.get("request")
        if not request or not request.user:
            raise serializers.ValidationError("缺少请求上下文")
        if not request.user.check_password(value):
            raise serializers.ValidationError("当前密码不正确")
        return value

    def validate_new_password(self, value):
        request = self.context.get("request")
        if request and request.user:
            from django.core.exceptions import ValidationError as DjangoValidationError
            try:
                validate_password(value, user=request.user)
            except DjangoValidationError as e:
                raise serializers.ValidationError(e.messages)
        return value

    def validate(self, data):
        if data["new_password"] == data["old_password"]:
            raise serializers.ValidationError({"new_password": "新密码不能与当前密码相同"})
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "两次密码不一致"})
        return data

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "phone", "avatar", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")
