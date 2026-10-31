from rest_framework import serializers

from inventory.models import Location, StockItem, StockLot, StockMovement, StockType


class StockTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockType
        fields = ["id", "name", "requires_expiration"]


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "name", "kind", "workplace"]
        read_only_fields = ["kind", "workplace"]


class StockItemSerializer(serializers.ModelSerializer):
    stock_type_name = serializers.CharField(source="stock_type.name", read_only=True)
    requires_expiration = serializers.BooleanField(source="stock_type.requires_expiration", read_only=True)

    class Meta:
        model = StockItem
        fields = ["id", "stock_type", "stock_type_name", "requires_expiration", "name", "unit"]

    def validate_stock_type(self, stock_type):
        if stock_type.company_id != self.context["request"].company.id:
            raise serializers.ValidationError("Stock type must belong to this company.")
        return stock_type


class StockLotSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)
    unit = serializers.CharField(source="item.unit", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)
    requires_expiration = serializers.BooleanField(
        source="item.stock_type.requires_expiration",
        read_only=True,
    )

    class Meta:
        model = StockLot
        fields = [
            "id",
            "item",
            "item_name",
            "unit",
            "location",
            "location_name",
            "quantity",
            "expires_on",
            "received_on",
            "requires_expiration",
        ]
        read_only_fields = ["quantity"]

    def validate(self, attrs):
        item = attrs.get("item")
        location = attrs.get("location")
        company = self.context["request"].company
        if item is not None and item.company_id != company.id:
            raise serializers.ValidationError({"item": "Item must belong to this company."})
        if location is not None and location.company_id != company.id:
            raise serializers.ValidationError({"location": "Location must belong to this company."})
        if item is not None and item.stock_type.requires_expiration and not attrs.get("expires_on"):
            raise serializers.ValidationError({"expires_on": "This stock type requires an expiration date."})
        return attrs


class StockLotCreateSerializer(StockLotSerializer):
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2)

    class Meta(StockLotSerializer.Meta):
        read_only_fields = []


class StockMovementSerializer(serializers.ModelSerializer):
    lot_item_name = serializers.CharField(source="lot.item.name", read_only=True)
    from_location_name = serializers.CharField(source="from_location.name", read_only=True)
    to_location_name = serializers.CharField(source="to_location.name", read_only=True)
    workplace_name = serializers.CharField(source="workplace.name", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "lot",
            "lot_item_name",
            "destination_lot",
            "kind",
            "quantity",
            "from_location",
            "from_location_name",
            "to_location",
            "to_location_name",
            "workplace",
            "workplace_name",
            "happened_on",
            "note",
            "created_at",
        ]
        read_only_fields = ["destination_lot", "from_location", "created_at"]

    happened_on = serializers.DateField(required=False)
