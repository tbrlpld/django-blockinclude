from django.urls import path

from blockinclude.test.example.views import kitchen_sink


urlpatterns = [
    path("", kitchen_sink),
]
