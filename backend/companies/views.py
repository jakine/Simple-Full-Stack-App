from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from companies.models import Membership
from companies.permissions import IsCompanyMember, IsCompanyOwner
from companies.serializers import (
    CompanyCreateSerializer,
    InviteSerializer,
    MembershipSerializer,
    SwitchSerializer,
)
from companies.services import (
    COMPANY_SESSION_KEY,
    create_company,
    invite_manager,
    memberships_for_user,
    switch_company,
)


def _company_data(membership):
    return {
        "id": membership.company_id,
        "name": membership.company.name,
        "role": membership.role,
    }


class CompanyListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        memberships = memberships_for_user(request.user)
        return Response([_company_data(membership) for membership in memberships])

    def post(self, request):
        serializer = CompanyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = create_company(request.user, serializer.validated_data["name"].strip())
        request.session[COMPANY_SESSION_KEY] = company.id
        return Response(
            {"id": company.id, "name": company.name, "role": Membership.Role.OWNER},
            status=status.HTTP_201_CREATED,
        )


class SwitchCompanyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SwitchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = switch_company(request, serializer.validated_data["company_id"])
        if membership is None:
            return Response(
                {"detail": "You are not a member of that company."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(_company_data(membership))


class MemberListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsCompanyOwner()]
        return [IsAuthenticated(), IsCompanyMember()]

    def get(self, request):
        memberships = (
            Membership.objects.filter(company=request.company)
            .select_related("user")
            .order_by("user__email")
        )
        return Response(MembershipSerializer(memberships, many=True).data)

    def post(self, request):
        serializer = InviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = invite_manager(
            request.company,
            serializer.validated_data["email"],
            serializer.validated_data.get("password") or "",
        )
        return Response(MembershipSerializer(membership).data, status=status.HTTP_201_CREATED)
