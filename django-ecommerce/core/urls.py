from django.urls import path
from .views import (
    ItemDetailView,
    HomeView,
    remove_from_cart,
    remove_single_item_from_cart,
    SignUpView,
    LoginView,
    del_user,
    AddOrderView,
    AddReview
)

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("product/<slug>/", ItemDetailView.as_view(), name="product"),
    path("order/", AddOrderView.as_view(), name="order"),
    path("remove-from-cart/<slug>/", remove_from_cart, name="remove-from-cart"),
    path(
        "remove-item-from-cart/<slug>/",
        remove_single_item_from_cart,
        name="remove-single-item-from-cart",
    ),
    path("review/", AddReview.as_view(), name="review"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("delete-user/", del_user, name="delete-user")
]
