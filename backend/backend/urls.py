from django.contrib import admin
from django.conf.urls import include
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/docs/", TemplateView.as_view(template_name="redoc.html")),
    path("api/", include("users.urls")),
    path("api/", include("foodgram.urls")),
]
