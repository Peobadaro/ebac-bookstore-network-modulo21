from rest_framework.authentication import (
    BasicAuthentication,
    SessionAuthentication,
    TokenAuthentication,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from order.models import Order
from order.serializers import OrderSerializer


class OrderViewSet(ModelViewSet):
    """Pedidos exigem login: só o dono do pedido consegue ver e mexer nele."""

    serializer_class = OrderSerializer
    # TokenAuthentication primeiro: sem login a API responde 401 com "WWW-Authenticate: Token".
    authentication_classes = [TokenAuthentication, BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .select_related("user")
            .prefetch_related("product__category")
            .order_by("id")
        )

    def perform_create(self, serializer):
        # O pedido sempre fica no nome de quem está autenticado.
        serializer.save(user=self.request.user)
