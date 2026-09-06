from .cart import Cart
from .models import Category
from django.db import OperationalError, ProgrammingError

def cart_context(request):
    try:
        categories = list(Category.objects.all())
    except (OperationalError, ProgrammingError, Exception):
        categories = []

    try:
        cart = Cart(request)
    except Exception:
        cart = []

    return {
        'cart': cart,
        'nav_categories': categories,
    }
