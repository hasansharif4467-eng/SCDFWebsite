
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("check-username/", views.check_username, name="check_username"),
    path("register/", views.register, name="register"),
    path("verify-email/<uuid:token>/", views.verify_email, name="verify_email"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="core/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path("comments/load/", views.load_comments, name="load_comments"),
    path("comments/add/", views.add_comment, name="add_comment"),
    path("reactions/", views.react_to_post, name="react_to_post"),
    path("reactions/load/", views.load_reactions, name="load_reactions"),
    path("comments/react/", views.react_to_comment, name="react_to_comment"),
]
