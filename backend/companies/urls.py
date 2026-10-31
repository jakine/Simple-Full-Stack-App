from django.urls import path

from companies.views import CompanyListCreateView, MemberListCreateView, SwitchCompanyView

urlpatterns = [
    path("", CompanyListCreateView.as_view(), name="company-list"),
    path("switch/", SwitchCompanyView.as_view(), name="company-switch"),
    path("members/", MemberListCreateView.as_view(), name="company-members"),
]
