import random
import string

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, DetailView, View
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
import json
import time
import copy

from .forms import (
    CheckoutForm,
    CouponForm,
    RefundForm,
    PaymentForm,
    NewUserForm,
    LoginForm,
)
from .models import (
    Item,
    OrderItem,
    Order,
    Address,
    Payment,
    Coupon,
    Refund,
    Review,
    UserProfile,
    # Review,
)

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_ref_code():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=20))


def products(request):
    context = {"items": Item.objects.all()}
    return render(request, "products.html", context)


def is_valid_form(values):
    valid = True
    for field in values:
        if field == "":
            valid = False
    return valid


class SignUpView(View):
    def get(self, *args, **kwargs):
        form = NewUserForm
        return render(self.request, "account/signup.html", context={"form": form})

    def post(self, *args, **kwargs):
        form = NewUserForm(self.request.POST or None)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password1")
            email = form.cleaned_data.get("email")
            user = User.objects.create_user(username=username, email=email, password=password)
            messages.success(self.request, "Successfully signed up!")
            return redirect("/")
        messages.error(self.request, "Could not sign up")
        return redirect("/")


class LoginView(View):
    def get(self, *args, **kwargs):
        form = LoginForm
        return render(self.request, "account/login.html", context={"form": form})

    def post(self, *args, **kwargs):
        form = LoginForm(self.request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = User.objects.get(username=username)
            if user:
                messages.success(self.request, "Successfully logged in")
                return redirect("/", u_id=user.id)

        # form is not valid or user is not authenticated
        messages.error(self.request, f"Invalid username or password")
        return redirect("/")


def del_user(request):
    try:
        u = User.objects.get(email=request.POST.get("email"))
        u.delete()
        messages.success(request, "The user is deleted")
        return redirect("/")
    except User.DoesNotExist:
        messages.error(request, "User does not exist")
        return redirect("/")



class HomeView(ListView):
    model = Item
    paginate_by = 10
    template_name = "home.html"


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {"object": order}
            return render(self.request, "order_summary.html", context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/")


class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"


class AddReview(View):
    def post(self, *args, **kwargs):
        #request = copy.copy(self.request.POST)
        slug = self.request.POST.get("slug")
        title = self.request.POST.get("title")
        body = self.request.POST.get("body")
        user = User.objects.get(username=self.request.POST.get("username"))
        if user:
            item = get_object_or_404(Item, slug=slug)
            order_item = OrderItem.objects.filter(item_id=item.id, user_id=user.id).first()
            review = Review(title=title, body=body, item_id=order_item.item_id)
            review.save()
            messages.info(self.request, "Successfully reviewed")
            return redirect("/")
        else:
            messages.error(self.request, f"Invalid username or password")
            return redirect("/")

class AddOrderView(View):
    def post(self, *args, **kwargs):
        slug = self.request.POST.get("slug")
        user = User.objects.get(username=self.request.POST.get("username"))
        #print("1")
        if user:
            item = get_object_or_404(Item, slug=int(slug))
            ordered_date = timezone.now()
            order_item = OrderItem.objects.create(
                item_id=item.id, user_id=user.id, ordered=True, ordered_date=ordered_date
            )
            messages.info(self.request, "This item was added to your cart.")
            #print("2")
            return redirect("/")
        else:
            #print("invalid")
            # form is not valid or user is not authenticated
            messages.error(self.request, f"Invalid username or password")
            return redirect("/")

@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item, user=request.user, ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "This item was removed from your cart.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item, user=request.user, ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("core:checkout")


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get("code")
                order = Order.objects.get(user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("core:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("core:checkout")


class RequestRefundView(View):
    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get("ref_code")
            message = form.cleaned_data.get("message")
            email = form.cleaned_data.get("email")
            # edit the order
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                # store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, "Your request was received.")
                return redirect("core:request-refund")

            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist.")
                return redirect("core:request-refund")

    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {"form": form}
        return render(self.request, "request_refund.html", context)
