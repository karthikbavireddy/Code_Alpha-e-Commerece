from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Order

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'name@example.com',
        'autocomplete': 'email'
    }))
    first_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last Name'
    }))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a unique username',
                'autocomplete': 'username'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'address', 'city', 'postal_code']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'John Doe',
                'required': True
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '123 Main Street, Apt 4B',
                'required': True
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'New York',
                'required': True
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '10001',
                'required': True
            }),
        }


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'quantity-input',
            'min': '1',
            'value': '1'
        })
    )


from .models import ReturnRequest, OrderItem

class ReturnRequestForm(forms.ModelForm):
    class Meta:
        model = ReturnRequest
        fields = ['item', 'reason', 'description']
        widgets = {
            'item': forms.Select(attrs={
                'class': 'form-control',
            }),
            'reason': forms.Select(attrs={
                'class': 'form-control',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please detail why you are returning this item and the condition of the package...'
            }),
        }

    def __init__(self, *args, order=None, **kwargs):
        super().__init__(*args, **kwargs)
        if order:
            self.fields['item'].queryset = OrderItem.objects.filter(order=order)
            self.fields['item'].empty_label = "Return entire order (All Items)"
            self.fields['item'].required = False

