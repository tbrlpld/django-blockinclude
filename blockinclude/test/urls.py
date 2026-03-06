from django.urls import path

from blockinclude.test.example.views import index


urlpatterns = [
    path("", index),
]
