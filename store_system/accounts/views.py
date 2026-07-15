from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import UpdateView, ListView, CreateView, DeleteView
from core.mixins import AdminOnlyMixin

from .forms import StyledLoginForm, ProfileForm, StyledPasswordChangeForm, UserCreateForm, UserUpdateForm
from .models import User


class StoreLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = StyledLoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().get_full_name() or form.get_user().username}!")
        return super().form_valid(form)


class StoreLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = "registration/profile.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully.")
        return super().form_valid(form)


class StorePasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "registration/change_password.html"
    form_class = StyledPasswordChangeForm
    success_url = reverse_lazy("dashboard:index")

    def form_valid(self, form):
        messages.success(self.request, "Password changed successfully.")
        user = form.save()
        user.must_change_password = False
        user.save(update_fields=["must_change_password"])
        return super().form_valid(form)


# ---- User management (Administrator only) ---------------------------------

class UserListView(AdminOnlyMixin, ListView):
    model = User
    template_name = "registration/user_list.html"
    context_object_name = "users"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")
        role = self.request.GET.get("role")
        if q:
            qs = qs.filter(username__icontains=q)
        if role:
            qs = qs.filter(role=role)
        return qs.order_by("username")


class UserCreateView(AdminOnlyMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = "registration/user_form.html"
    success_url = reverse_lazy("accounts:user_list")

    def form_valid(self, form):
        messages.success(self.request, "User account created.")
        return super().form_valid(form)


class UserUpdateView(AdminOnlyMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "registration/user_form.html"
    success_url = reverse_lazy("accounts:user_list")

    def form_valid(self, form):
        messages.success(self.request, "User account updated.")
        return super().form_valid(form)


class UserDeleteView(AdminOnlyMixin, DeleteView):
    model = User
    template_name = "registration/user_confirm_delete.html"
    success_url = reverse_lazy("accounts:user_list")

    def form_valid(self, form):
        messages.success(self.request, "User account deleted.")
        return super().form_valid(form)
