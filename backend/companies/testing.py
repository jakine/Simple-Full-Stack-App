from rest_framework.test import APIClient

from companies.models import Company, Membership
from django.contrib.auth import get_user_model

User = get_user_model()


def make_user(email, password="Manager-pass-123"):
    return User.objects.create_user(username=email, email=email, password=password)


def make_membership(user, name="Acme", role=Membership.Role.OWNER):
    company = Company.objects.create(name=name)
    return Membership.objects.create(user=user, company=company, role=role)


def auth_client(user, company):
    client = APIClient()
    client.force_login(user)
    session = client.session
    session["company_id"] = company.id
    session.save()
    return client
