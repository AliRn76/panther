from django.contrib import admin
from django.urls import path

from app.views import hello_world

urlpatterns = [
    path('', hello_world),
]
