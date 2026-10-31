from rest_framework.permissions import BasePermission

from companies.models import Membership
from companies.services import COMPANY_SESSION_KEY


class IsCompanyMember(BasePermission):
    message = "Choose a company first."

    def has_permission(self, request, view):
        company_id = request.session.get(COMPANY_SESSION_KEY)
        if not company_id:
            return False
        membership = (
            Membership.objects.filter(user=request.user, company_id=company_id)
            .select_related("company")
            .first()
        )
        if membership is None:
            return False
        request.company = membership.company
        request.membership = membership
        return True


class IsCompanyOwner(IsCompanyMember):
    message = "Only an owner can invite managers."

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.membership.role == Membership.Role.OWNER
