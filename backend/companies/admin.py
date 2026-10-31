from django.contrib import admin

from companies.models import Company, Membership


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "company", "role"]
    list_filter = ["role"]
