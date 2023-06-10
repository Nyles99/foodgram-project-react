from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from rest_framework.views import APIView

from . import models, serializers


class TagView(viewsets.ModelViewSet):
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer
    permissions = [AllowAny, ]
    pagination_class = None


class IngredientsView(viewsets.ModelViewSet):
    queryset = models.Ingredient.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, ]
    serializer_class = serializers.IngredientSerializer
    filter_backends = [DjangoFilterBackend, ]
    search_fields = ["name", ]
    pagination_class = None


class RecipeView(viewsets.ModelViewSet):
    queryset = models.Recipe.objects.all()
    permissions = [IsAuthenticatedOrReadOnly, ]
    filter_backends = [DjangoFilterBackend, ]
    pagination_class = PageNumberPagination

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
