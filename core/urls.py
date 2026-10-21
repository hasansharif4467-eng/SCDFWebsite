from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("check-username/", views.check_username, name="check_username"),
    path("register/", views.register, name="register"),
]
