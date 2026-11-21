from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from order.models import Order
from product.models import Product


class OrderViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="pedro", password="senha-teste-123")
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.product_1 = Product.objects.create(title="Django", price=100)
        self.product_2 = Product.objects.create(title="Python", price=50)
        self.order = Order.objects.create(user=self.user)
        self.order.product.set([self.product_1])

        self.list_url = reverse("order-list", kwargs={"version": "v1"})
        self.detail_url = reverse("order-detail", kwargs={"version": "v1", "pk": self.order.id})

    # --- com token: CRUD do próprio pedido ---

    def test_list_orders(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["product"][0]["title"], "Django")
        self.assertEqual(response.data["results"][0]["total"], 100)

    def test_retrieve_order(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"], self.user.id)

    def test_create_order(self):
        data = {"user": self.user.id, "products_id": [self.product_1.id, self.product_2.id]}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 2)
        self.assertEqual(response.data["total"], 150)

    def test_create_order_without_products(self):
        data = {"user": self.user.id, "products_id": []}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("products_id", response.data)

    def test_delete_order(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Order.objects.exists())

    def test_retrieve_nonexistent_order(self):
        url = reverse("order-detail", kwargs={"version": "v1", "pk": 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- sem token ou token errado ---

    def test_list_orders_without_token_returns_401(self):
        self.client.credentials()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_order_without_token_returns_401(self):
        self.client.credentials()
        data = {"user": self.user.id, "products_id": [self.product_1.id]}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Order.objects.count(), 1)

    def test_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token token-invalido")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- cada usuário só enxerga os próprios pedidos ---

    def test_user_does_not_see_other_users_orders(self):
        other = User.objects.create_user(username="maria", password="senha-teste-456")
        other_order = Order.objects.create(user=other)
        other_order.product.set([self.product_2])

        response = self.client.get(self.list_url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.order.id)

        url = reverse("order-detail", kwargs={"version": "v1", "pk": other_order.id})
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_order_is_created_for_authenticated_user(self):
        other = User.objects.create_user(username="maria", password="senha-teste-456")
        data = {"user": other.id, "products_id": [self.product_1.id]}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"], self.user.id)
        self.assertFalse(Order.objects.filter(user=other).exists())

    def test_basic_authentication_also_works(self):
        self.client.credentials()
        self.client.login(username="pedro", password="senha-teste-123")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
