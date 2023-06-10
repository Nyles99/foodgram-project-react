from django.contrib import admin
from django.contrib.admin import register

from . import models


admin.site.register(models.Follow)


@register(models.User)
class UserAdmin(admin.ModelAdmin):
    fields = ("username", "first_name", "last_name", "email")
    search_fields = ("username",)
