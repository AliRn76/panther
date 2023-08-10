from app.views import hello_world
from django.urls import path

urlpatterns = [
    path('', hello_world),
]
