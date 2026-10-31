from rest_framework.routers import DefaultRouter

from inventory.views import (
    LocationViewSet,
    StockItemViewSet,
    StockLotViewSet,
    StockMovementViewSet,
    StockTypeViewSet,
)

router = DefaultRouter()
router.register("stock-types", StockTypeViewSet, basename="stock-type")
router.register("locations", LocationViewSet, basename="location")
router.register("stock-items", StockItemViewSet, basename="stock-item")
router.register("stock-lots", StockLotViewSet, basename="stock-lot")
router.register("stock-movements", StockMovementViewSet, basename="stock-movement")

urlpatterns = router.urls
