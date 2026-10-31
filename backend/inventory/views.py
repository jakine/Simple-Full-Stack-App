from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from companies.permissions import HasCompanyRole
from companies.viewsets import CompanyScopedViewSet
from core.services import record_event
from inventory.models import Location, StockItem, StockLot, StockMovement, StockType
from inventory.serializers import (
    LocationSerializer,
    StockItemSerializer,
    StockLotCreateSerializer,
    StockLotSerializer,
    StockMovementSerializer,
    StockTypeSerializer,
)
from inventory.services import apply_movement, receive_stock


class StockTypeViewSet(CompanyScopedViewSet):
    serializer_class = StockTypeSerializer
    queryset = StockType.objects.all()


class LocationViewSet(CompanyScopedViewSet):
    serializer_class = LocationSerializer
    queryset = Location.objects.all()
    http_method_names = ["get", "post", "delete", "head", "options"]

    def perform_create(self, serializer):
        serializer.save(
            company=self.request.company,
            kind=Location.Kind.DEPOT,
            workplace=None,
        )


class StockItemViewSet(CompanyScopedViewSet):
    serializer_class = StockItemSerializer
    queryset = StockItem.objects.select_related("stock_type")


class StockLotViewSet(CompanyScopedViewSet):
    queryset = StockLot.objects.select_related("item__stock_type", "location")
    company_lookup = "item__company"
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return StockLotCreateSerializer
        return StockLotSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        expires_before = self.request.query_params.get("expires_before")
        if expires_before:
            queryset = queryset.filter(expires_on__isnull=False, expires_on__lte=expires_before)
        location_id = self.request.query_params.get("location")
        if location_id:
            queryset = queryset.filter(location_id=location_id)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        lot, _movement = receive_stock(
            company=request.company,
            item=data["item"],
            location=data["location"],
            quantity=data["quantity"],
            expires_on=data.get("expires_on"),
            received_on=data.get("received_on"),
            note=data.get("note", "") if "note" in data else "",
            user=request.user,
        )
        record_event(
            request,
            "stock.received",
            lot,
            project=lot.location.workplace,
            data={"item": lot.item.name, "quantity": str(data["quantity"]), "location": lot.location.name},
        )
        output = StockLotSerializer(lot, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class StockMovementViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated, HasCompanyRole]
    serializer_class = StockMovementSerializer
    queryset = StockMovement.objects.select_related(
        "lot__item",
        "from_location",
        "to_location",
        "workplace",
    )

    def get_queryset(self):
        queryset = super().get_queryset().filter(company=self.request.company)
        lot_id = self.request.query_params.get("lot")
        if lot_id:
            queryset = queryset.filter(lot_id=lot_id)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        lot = data["lot"]
        if lot.item.company_id != request.company.id:
            return Response({"lot": ["Lot must belong to this company."]}, status=status.HTTP_400_BAD_REQUEST)
        movement = apply_movement(
            company=request.company,
            lot=lot,
            kind=data["kind"],
            quantity=data["quantity"],
            to_location=data.get("to_location"),
            workplace=data.get("workplace"),
            happened_on=data.get("happened_on"),
            note=data.get("note", ""),
            user=request.user,
        )
        to_location = movement.to_location
        record_event(
            request,
            f"stock.{movement.kind}",
            movement,
            project=movement.workplace or (to_location.workplace if to_location else None),
            data={"item": lot.item.name, "quantity": str(movement.quantity)},
        )
        return Response(self.get_serializer(movement).data, status=status.HTTP_201_CREATED)
