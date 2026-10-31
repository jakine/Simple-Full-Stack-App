from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from inventory.models import Location, StockLot, StockMovement


def _lock_lot(lot_id):
    return (
        StockLot.objects.select_for_update()
        .select_related("item__stock_type", "location")
        .get(pk=lot_id)
    )


def _destination_lot(source, location, happened_on):
    existing = (
        StockLot.objects.select_for_update()
        .filter(item=source.item, location=location, expires_on=source.expires_on)
        .first()
    )
    if existing is not None:
        return existing
    try:
        with transaction.atomic():
            return StockLot.objects.create(
                item=source.item,
                location=location,
                quantity=Decimal("0.00"),
                expires_on=source.expires_on,
                received_on=happened_on,
            )
    except IntegrityError:
        return (
            StockLot.objects.select_for_update()
            .get(item=source.item, location=location, expires_on=source.expires_on)
        )


def receive_stock(*, company, item, location, quantity, expires_on, received_on, note, user):
    if item.company_id != company.id or location.company_id != company.id:
        raise ValidationError("Stock must stay inside the active company.")
    if location.kind != Location.Kind.DEPOT:
        raise ValidationError({"location": "Stock is received into a depot."})
    if item.stock_type.company_id != company.id:
        raise ValidationError({"stock_type": "Stock type must belong to this company."})
    if quantity <= 0:
        raise ValidationError({"quantity": "Quantity must be greater than zero."})
    if item.stock_type.requires_expiration and expires_on is None:
        raise ValidationError({"expires_on": "This stock type requires an expiration date."})
    received_on = received_on or timezone.localdate()

    with transaction.atomic():
        lot = (
            StockLot.objects.select_for_update()
            .filter(item=item, location=location, expires_on=expires_on)
            .first()
        )
        if lot is None:
            try:
                with transaction.atomic():
                    lot = StockLot.objects.create(
                        item=item,
                        location=location,
                        quantity=Decimal("0.00"),
                        expires_on=expires_on,
                        received_on=received_on,
                    )
            except IntegrityError:
                lot = (
                    StockLot.objects.select_for_update()
                    .get(item=item, location=location, expires_on=expires_on)
                )
        lot.quantity += quantity
        lot.save(update_fields=["quantity"])
        movement = StockMovement.objects.create(
            company=company,
            lot=lot,
            kind=StockMovement.Kind.RECEIVE,
            quantity=quantity,
            to_location=location,
            happened_on=received_on,
            note=note or "",
            recorded_by=user,
        )
    return lot, movement


def apply_movement(
    *,
    company,
    lot,
    kind,
    quantity,
    to_location,
    workplace,
    happened_on,
    note,
    user,
):
    if quantity == 0:
        raise ValidationError({"quantity": "Quantity cannot be zero."})
    if kind != StockMovement.Kind.ADJUST and quantity < 0:
        raise ValidationError({"quantity": "Quantity must be greater than zero."})
    if kind == StockMovement.Kind.ADJUST and not (note or "").strip():
        raise ValidationError({"note": "A note is required for an adjustment."})
    happened_on = happened_on or timezone.localdate()

    with transaction.atomic():
        lot = _lock_lot(lot.pk)
        if lot.item.company_id != company.id:
            raise ValidationError({"lot": "Lot must belong to this company."})
        if to_location is not None and to_location.company_id != company.id:
            raise ValidationError({"to_location": "Location must belong to this company."})
        if workplace is not None and workplace.company_id != company.id:
            raise ValidationError({"workplace": "Workplace must belong to this company."})

        destination_lot = None
        from_location = None
        stored_to_location = None

        if kind == StockMovement.Kind.RECEIVE:
            if quantity <= 0:
                raise ValidationError({"quantity": "Quantity must be greater than zero."})
            lot.quantity += quantity
            stored_to_location = lot.location
        elif kind == StockMovement.Kind.CONSUME:
            if lot.quantity < quantity:
                raise ValidationError({"quantity": "Not enough stock in this lot."})
            if workplace is None:
                raise ValidationError({"workplace": "Choose the workplace that used this stock."})
            lot.quantity -= quantity
            from_location = lot.location
        elif kind == StockMovement.Kind.TRANSFER:
            if to_location is None:
                raise ValidationError({"to_location": "Choose a destination location."})
            if to_location.id == lot.location_id:
                raise ValidationError({"to_location": "Choose a different location."})
            if lot.quantity < quantity:
                raise ValidationError({"quantity": "Not enough stock in this lot."})
            lot.quantity -= quantity
            destination_lot = _destination_lot(lot, to_location, happened_on)
            destination_lot.quantity += quantity
            destination_lot.save(update_fields=["quantity"])
            from_location = lot.location
            stored_to_location = to_location
            if workplace is None and to_location.workplace_id:
                workplace = to_location.workplace
        elif kind == StockMovement.Kind.ADJUST:
            updated = lot.quantity + quantity
            if updated < 0:
                raise ValidationError({"quantity": "Adjustment would make the quantity negative."})
            lot.quantity = updated
            from_location = lot.location
        else:
            raise ValidationError({"kind": "Unknown movement."})

        lot.save(update_fields=["quantity"])
        movement = StockMovement.objects.create(
            company=company,
            lot=lot,
            destination_lot=destination_lot,
            kind=kind,
            quantity=quantity,
            from_location=from_location,
            to_location=stored_to_location,
            workplace=workplace,
            happened_on=happened_on,
            note=note or "",
            recorded_by=user,
        )
    return movement
