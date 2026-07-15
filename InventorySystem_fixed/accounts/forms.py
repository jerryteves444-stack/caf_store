from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm, AuthenticationForm
from .models import User

class StyledFormMixin:
    """Adds Bootstrap classes to every widget without needing crispy tags
    everywhere (crispy is still used on templates for layout/columns).

    Note: this mixin deliberately does NOT touch a 'request' kwarg. Plain
    forms.Form/ModelForm subclasses never receive one, and StyledLoginForm
    (which mixes this in with AuthenticationForm) needs 'request' to pass
    through untouched so AuthenticationForm can store/use it itself.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            if isinstance(field.widget, (forms.CheckboxInput,)):
                field.widget.attrs["class"] = (css + " form-check-input").strip()
            else:
                field.widget.attrs["class"] = (css + " form-control").strip()


class StyledLoginForm(StyledFormMixin, AuthenticationForm):
    """AuthenticationForm already handles field validation, get_user(),
    and confirm_login_allowed() -- we only need the Bootstrap styling."""
    pass


class UserCreateForm(StyledFormMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "first_name", "last_name", "email", "role", "phone_number"]

class UserUpdateForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "role", "phone_number", "avatar", "is_active_employee"]


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone_number", "avatar"]


class StyledPasswordChangeForm(StyledFormMixin, PasswordChangeForm):
    pass