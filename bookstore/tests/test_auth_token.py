from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class AuthTokenTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="pedro", password="senha-teste-123")
        self.url = reverse("api_token_auth")

    def test_obtain_token_with_valid_credentials(self):
        response = self.client.post(
            self.url, {"username": "pedro", "password": "senha-teste-123"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["token"], Token.objects.get(user=self.user).key)

    def test_obtain_token_with_wrong_password(self):
        response = self.client.post(
            self.url, {"username": "pedro", "password": "errada"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Token.objects.exists())

    def test_product_and_category_stay_open(self):
        for name in ("product", "category"):
            response = self.client.get(reverse(f"{name}-list", kwargs={"version": "v1"}))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
