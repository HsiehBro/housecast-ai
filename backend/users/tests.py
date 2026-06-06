from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


# ============================================================
# Login endpoint tests
# ============================================================

class LoginAPITests(APITestCase):
    url = "/api/auth/login/"

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
        )

    def test_login_success(self):
        resp = self.client.post(
            self.url,
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)
        self.assertTrue(len(resp.data["access"]) > 0)
        self.assertTrue(len(resp.data["refresh"]) > 0)

    def test_login_wrong_password(self):
        resp = self.client.post(
            self.url,
            {"username": "testuser", "password": "wrongpass"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        resp = self.client.post(
            self.url,
            {"username": "nouser", "password": "whatever"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_username(self):
        resp = self.client.post(
            self.url,
            {"password": "testpass123"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_password(self):
        resp = self.client.post(
            self.url,
            {"username": "testuser"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_empty_body(self):
        resp = self.client.post(self.url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        resp = self.client.post(
            self.url,
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_tokens_are_distinct(self):
        resp = self.client.post(
            self.url,
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertNotEqual(resp.data["access"], resp.data["refresh"])

    def test_login_requires_post(self):
        resp = self.client.get(self.url)
        self.assertIn(
            resp.status_code,
            [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_400_BAD_REQUEST],
        )

    def test_login_success_with_email_user(self):
        User.objects.create_user(
            username="emailuser",
            password="emailpass123",
            email="email@test.com",
        )
        resp = self.client.post(
            self.url,
            {"username": "emailuser", "password": "emailpass123"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_login_blank_username(self):
        resp = self.client.post(
            self.url,
            {"username": "", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_blank_password(self):
        resp = self.client.post(
            self.url,
            {"username": "testuser", "password": ""},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_wrong_content_type(self):
        resp = self.client.post(
            self.url,
            "username=testuser&password=testpass123",
            content_type="text/plain",
        )
        self.assertIn(resp.status_code, [status.HTTP_400_BAD_REQUEST,
                                         status.HTTP_415_UNSUPPORTED_MEDIA_TYPE])


# ============================================================
# Register endpoint tests
# ============================================================

class RegisterAPITests(APITestCase):
    url = "/api/auth/register/"

    def test_register_success(self):
        resp = self.client.post(
            self.url,
            {
                "username": "newuser",
                "password": "newpass123",
                "password_confirm": "newpass123",
                "email": "new@example.com",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["username"], "newuser")
        self.assertEqual(resp.data["email"], "new@example.com")
        self.assertNotIn("password", resp.data)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_password_mismatch(self):
        resp = self.client.post(
            self.url,
            {
                "username": "newuser",
                "password": "newpass123",
                "password_confirm": "different",
                "email": "new@example.com",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username(self):
        User.objects.create_user(username="taken", password="pass1234", email="a@b.com")
        resp = self.client.post(
            self.url,
            {
                "username": "taken",
                "password": "newpass123",
                "password_confirm": "newpass123",
                "email": "c@d.com",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        User.objects.create_user(username="existing", password="pass1234", email="dup@b.com")
        resp = self.client.post(
            self.url,
            {
                "username": "another",
                "password": "newpass123",
                "password_confirm": "newpass123",
                "email": "dup@b.com",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_short_password(self):
        resp = self.client.post(
            self.url,
            {
                "username": "shortpw",
                "password": "123",
                "password_confirm": "123",
                "email": "short@example.com",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields(self):
        resp = self.client.post(self.url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_with_optional_phone(self):
        resp = self.client.post(
            self.url,
            {
                "username": "phoneuser",
                "password": "pass12345",
                "password_confirm": "pass12345",
                "email": "phone@example.com",
                "phone": "13800138000",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["phone"], "13800138000")

    def test_register_invalid_phone(self):
        resp = self.client.post(
            self.url,
            {
                "username": "badphone",
                "password": "pass12345",
                "password_confirm": "pass12345",
                "email": "bad@example.com",
                "phone": "123",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_not_returned(self):
        resp = self.client.post(
            self.url,
            {
                "username": "safeuser",
                "password": "pass12345",
                "password_confirm": "pass12345",
                "email": "safe@example.com",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", resp.data)


# ============================================================
# Logout endpoint tests
# ============================================================

class LogoutAPITests(APITestCase):
    url = "/api/auth/logout/"

    def setUp(self):
        self.user = User.objects.create_user(
            username="logoutuser",
            password="logoutpass123",
            email="logout@example.com",
        )
        self.client.force_authenticate(self.user)

    def _get_refresh_token(self):
        refresh = RefreshToken.for_user(self.user)
        return str(refresh)

    def test_logout_success(self):
        token = self._get_refresh_token()
        resp = self.client.post(
            self.url,
            {"refresh": token},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_logout_missing_refresh_token(self):
        resp = self.client.post(self.url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_invalid_refresh_token(self):
        resp = self.client.post(
            self.url,
            {"refresh": "invalid-token"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_unauthenticated(self):
        self.client.force_authenticate(user=None)
        resp = self.client.post(
            self.url,
            {"refresh": "sometoken"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ============================================================
# Token refresh endpoint tests
# ============================================================

class RefreshAPITests(APITestCase):
    url = "/api/auth/refresh/"

    def setUp(self):
        self.user = User.objects.create_user(
            username="refreshuser",
            password="refreshpass123",
            email="refresh@example.com",
        )

    def test_refresh_success(self):
        refresh = RefreshToken.for_user(self.user)
        resp = self.client.post(
            self.url,
            {"refresh": str(refresh)},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)

    def test_refresh_invalid_token(self):
        resp = self.client.post(
            self.url,
            {"refresh": "invalid-token"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_missing_token(self):
        resp = self.client.post(self.url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


# ============================================================
# Me endpoint tests
# ============================================================

class MeAPITests(APITestCase):
    url = "/api/auth/me/"

    def setUp(self):
        self.user = User.objects.create_user(
            username="meuser",
            password="mepass123",
            email="me@example.com",
            phone="13800138000",
        )

    def test_me_authenticated(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["username"], "meuser")
        self.assertEqual(resp.data["email"], "me@example.com")
        self.assertEqual(resp.data["phone"], "13800138000")
        self.assertIn("id", resp.data)

    def test_me_unauthenticated(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_fields_no_password(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(self.url)
        self.assertNotIn("password", resp.data)

    def test_me_update_username(self):
        self.client.force_authenticate(self.user)
        resp = self.client.put(
            self.url,
            {
                "username": "updateduser",
                "email": "me@example.com",
                "phone": "13800138000",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "updateduser")

    def test_me_update_unauthenticated(self):
        resp = self.client.put(
            self.url,
            {"username": "hacked"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ============================================================
# Full login flow integration tests
# ============================================================

class LoginFlowTests(APITestCase):
    """End-to-end login flow: login → use token → refresh → logout"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="flowuser",
            password="flowpass123",
            email="flow@example.com",
        )

    def test_full_login_flow(self):
        # 1. Login
        resp = self.client.post(
            "/api/auth/login/",
            {"username": "flowuser", "password": "flowpass123"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        access = resp.data["access"]
        refresh = resp.data["refresh"]

        # 2. Access protected endpoint with access token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        me_resp = self.client.get("/api/auth/me/")
        self.assertEqual(me_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(me_resp.data["username"], "flowuser")

        # 3. Refresh token
        self.client.credentials()
        refresh_resp = self.client.post(
            "/api/auth/refresh/",
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(refresh_resp.status_code, status.HTTP_200_OK)
        new_access = refresh_resp.data["access"]

        # 4. Use new access token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {new_access}")
        me_resp2 = self.client.get("/api/auth/me/")
        self.assertEqual(me_resp2.status_code, status.HTTP_200_OK)

        # 5. Logout (blacklist refresh token)
        new_refresh = refresh_resp.data.get("refresh", refresh)
        self.client.force_authenticate(self.user)
        logout_resp = self.client.post(
            "/api/auth/logout/",
            {"refresh": new_refresh},
            format="json",
        )
        self.assertEqual(logout_resp.status_code, status.HTTP_200_OK)

    def test_register_then_login(self):
        # 1. Register
        reg_resp = self.client.post(
            "/api/auth/register/",
            {
                "username": "regthenlogin",
                "password": "regpass123",
                "password_confirm": "regpass123",
                "email": "reglogin@example.com",
            },
            format="json",
        )
        self.assertEqual(reg_resp.status_code, status.HTTP_201_CREATED)

        # 2. Login with same credentials
        login_resp = self.client.post(
            "/api/auth/login/",
            {"username": "regthenlogin", "password": "regpass123"},
            format="json",
        )
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_resp.data)
