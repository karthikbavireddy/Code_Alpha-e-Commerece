from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db import transaction
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme

import secrets
from .models import Category, Product, Order, OrderItem, ReturnRequest
from .cart import Cart
from .forms import UserRegistrationForm, CheckoutForm, AddToCartForm, ReturnRequestForm


def product_list(request):
    category_slug = request.GET.get('category')
    search_query = request.GET.get('q', '').strip()

    products = Product.objects.all()
    selected_category = None

    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)

    if search_query:
        products = products.filter(name__icontains=search_query) | products.filter(description__icontains=search_query)

    categories = Category.objects.all()

    context = {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
        'search_query': search_query,
    }
    return render(request, 'store/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    form = AddToCartForm()
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]

    context = {
        'product': product,
        'form': form,
        'related_products': related_products,
    }
    return render(request, 'store/product_detail.html', context)


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    if not product.is_in_stock:
        messages.error(request, f"Sorry, '{product.name}' is currently out of stock.")
        return redirect('store:product_detail', slug=product.slug)

    form = AddToCartForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        quantity = cd['quantity']
        if quantity > product.stock:
            quantity = product.stock
            messages.warning(request, f"Quantity adjusted to available stock limit ({product.stock}).")

        cart.add(product=product, quantity=quantity)
        messages.success(request, f"Added {quantity}x '{product.name}' to your cart!")

    return redirect('store:cart_detail')


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.info(request, f"Removed '{product.name}' from your cart.")
    return redirect('store:cart_detail')


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity <= 0:
            cart.remove(product)
            messages.info(request, f"Removed '{product.name}' from your cart.")
        elif quantity > product.stock:
            cart.update_quantity(product.id, product.stock)
            messages.warning(request, f"Max available stock for '{product.name}' is {product.stock}.")
        else:
            cart.update_quantity(product.id, quantity)
            messages.success(request, f"Updated quantity for '{product.name}'.")
    except ValueError:
        messages.error(request, "Invalid quantity specified.")

    return redirect('store:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'store/cart.html', {'cart': cart})


def user_register(request):
    if request.user.is_authenticated:
        return redirect('store:product_list')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to CodeAlpha Store, {user.username}! Your account has been created.")
            next_url = request.POST.get('next') or request.GET.get('next')
            if not next_url or not url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}):
                next_url = 'store:product_list'
            return redirect(next_url)
    else:
        form = UserRegistrationForm()

    return render(request, 'store/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('store:product_list')

    next_url = request.GET.get('next', '')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_staff:
                messages.info(
                    request,
                    f"Staff account detected ({user.username}). You can access the dedicated Admin Portal anytime."
                )
            else:
                messages.success(request, f"Welcome back, {user.username}!")

            redirect_to = request.POST.get('next') or request.GET.get('next')
            if not redirect_to or not url_has_allowed_host_and_scheme(url=redirect_to, allowed_hosts={request.get_host()}):
                redirect_to = 'store:product_list'
            return redirect(redirect_to)
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()

    return render(request, 'store/login.html', {'form': form, 'next': next_url})


def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('store:product_list')


@login_required
def checkout(request):
    cart = Cart(request)

    if cart.is_empty:
        messages.warning(request, "Your cart is empty. Add some products before checkout.")
        return redirect('store:product_list')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Lock product records for update to eliminate concurrency race conditions
                locked_products = {}
                for item in cart:
                    prod = Product.objects.select_for_update().get(id=item['product'].id)
                    if prod.stock < item['quantity']:
                        messages.error(
                            request,
                            f"Sorry, only {prod.stock} units of '{prod.name}' are remaining in stock."
                        )
                        return redirect('store:cart_detail')
                    locked_products[item['product'].id] = prod

                order = form.save(commit=False)
                order.user = request.user
                # Generate tracking code
                from django.utils import timezone
                now_prefix = timezone.now().strftime('%Y%m')
                order.tracking_number = f"TRK-{now_prefix}-{secrets.token_hex(4).upper()}"
                order.save()

                for item in cart:
                    prod = locked_products[item['product'].id]
                    OrderItem.objects.create(
                        order=order,
                        product=prod,
                        product_name=prod.name,
                        price=prod.price,
                        quantity=item['quantity']
                    )
                    # Decrement product stock safely
                    prod.stock -= item['quantity']
                    prod.save(update_fields=['stock'])

                # Clear cart
                cart.clear()

            messages.success(
                request,
                f"Order {order.order_id} placed successfully! Tracking #: {order.tracking_number}. Thank you for your purchase."
            )
            return redirect('store:order_confirmation', order_id=order.id)
    else:
        initial_data = {
            'full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
        }
        form = CheckoutForm(initial=initial_data)

    context = {
        'cart': cart,
        'form': form,
    }
    return render(request, 'store/checkout.html', context)


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_confirmation.html', {'order': order})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items', 'returns').order_by('-created_at')
    return render(request, 'store/order_history.html', {'orders': orders})


@login_required
def request_return(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if not order.can_request_return:
        messages.error(
            request,
            f"Order {order.order_id} is currently '{order.get_status_display()}' and is not eligible for a new return request."
        )
        return redirect('store:order_history')

    if request.method == 'POST':
        form = ReturnRequestForm(request.POST, order=order)
        if form.is_valid():
            with transaction.atomic():
                return_request = form.save(commit=False)
                return_request.order = order
                return_request.user = request.user
                return_request.status = 'requested'
                return_request.save()

                # Update order status to reflect active return request
                order.status = 'return_requested'
                order.save(update_fields=['status'])

            messages.success(
                request,
                f"Return request #{return_request.return_id} submitted for {order.order_id}. Our team will review it shortly."
            )
            return redirect('store:returns_list')
    else:
        form = ReturnRequestForm(order=order)

    context = {
        'order': order,
        'form': form,
    }
    return render(request, 'store/return_request.html', context)


@login_required
def returns_list(request):
    returns = ReturnRequest.objects.filter(user=request.user).select_related('order', 'item').order_by('-created_at')
    return render(request, 'store/returns_list.html', {'returns': returns})

