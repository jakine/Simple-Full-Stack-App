from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from companies.exceptions import Conflict
from companies.models import Company, Membership

COMPANY_SESSION_KEY = "company_id"

User = get_user_model()


def memberships_for_user(user):
    return Membership.objects.filter(user=user).select_related("company")


def create_company(user, name):
    with transaction.atomic():
        company = Company.objects.create(name=name)
        Membership.objects.create(
            user=user,
            company=company,
            role=Membership.Role.OWNER,
        )
    return company


def switch_company(request, company_id):
    membership = (
        Membership.objects.filter(user=request.user, company_id=company_id)
        .select_related("company")
        .first()
    )
    if membership is None:
        return None
    request.session[COMPANY_SESSION_KEY] = membership.company_id
    return membership


def invite_manager(company, email, password):
    email = email.strip().lower()
    user = User.objects.filter(username__iexact=email).first()
    if user is None:
        if not password:
            raise ValidationError({"password": "Password is required for a new manager."})
        try:
            validate_password(password)
        except DjangoValidationError as exc:
            raise ValidationError({"password": list(exc.messages)}) from exc
        user = User.objects.create_user(username=email, email=email, password=password)
    try:
        with transaction.atomic():
            return Membership.objects.create(
                user=user,
                company=company,
                role=Membership.Role.MANAGER,
            )
    except IntegrityError as exc:
        raise Conflict("That person is already a member of this company.") from exc
