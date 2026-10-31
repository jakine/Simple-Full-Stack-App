from django.db.models import ProtectedError
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from companies.permissions import IsCompanyMember


class CompanyScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsCompanyMember]
    company_lookup = "company"

    def get_queryset(self):
        return super().get_queryset().filter(**{self.company_lookup: self.request.company})

    def perform_create(self, serializer):
        if self.company_lookup == "company":
            serializer.save(company=self.request.company)
        else:
            serializer.save()

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "This record is used by other data and cannot be deleted."},
                status=400,
            )
