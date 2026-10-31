from django.contrib import admin

from inventory.models import Location, StockItem, StockLot, StockMovement, StockType

admin.site.register(StockType)
admin.site.register(Location)
admin.site.register(StockItem)
admin.site.register(StockLot)
admin.site.register(StockMovement)
