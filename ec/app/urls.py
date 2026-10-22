from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import reverse_lazy
from .forms import LoginFrom, MyPasswordChangeForm, MyPasswordResetFrom, MySetPasswordForm
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", views.home, name="home"),
    path('about/', views.about, name="about"),
    path('contact/', views.contact, name="contact"),
    path('search/', views.search, name="search"),
    path("category/<slug:val>/", views.categoryView.as_view(), name="category"),
    path("category-title/<val>/", views.categoryTitle.as_view(), name="category-title"),
    path("product/<int:pk>/", views.ProductDetail.as_view(), name="productdetail"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("address/", views.address, name="address"),
    path('updateAddress/<int:pk>/', views.updateAddress.as_view(), name='updateAddress'),
    path('orders/', views.orders, name='orders'),
    path('orders/<int:pk>/', views.order_detail, name='order-detail'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/', views.add_to_wishlist, name='add-to-wishlist'),
    path('wishlist/remove/', views.remove_from_wishlist, name='remove-from-wishlist'),

    path('add-to-cart/', views.add_to_cart,name='add-to-cart'),
    path('cart/' , views.show_cart,name='showcart'),
    path('checkout/', views.checkout.as_view(), name='checkout'),
    path('pluscart/', views.plus_cart, name='pluscart'),
    path('minuscart/', views.minus_cart, name='minuscart'), 
    path('removecart/', views.remove_cart, name='removecart'),
    

    path('registration/', views.CustomerRegistrationView.as_view(), name='customerregistrationview'),

    # LOGIN & LOGOUT
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='app/login.html',
        authentication_form=LoginFrom
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # PASSWORD RESET FLOW
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='app/password_reset.html',
        form_class=MyPasswordResetFrom,
        email_template_name='app/password_reset_email.html',
        success_url=reverse_lazy('password_reset_done')
    ), name='password_reset'),

    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='app/password_reset_done.html'
    ), name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='app/password_reset_confirm.html',
        form_class=MySetPasswordForm,
        success_url=reverse_lazy('password_reset_complete')
    ), name='password_reset_confirm'),

    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='app/password_reset_complete.html'
    ), name='password_reset_complete'),

    # PASSWORD CHANGE
    path('passwordchange/', auth_views.PasswordChangeView.as_view(
        template_name='app/changepassword.html',
        form_class=MyPasswordChangeForm,
        success_url=reverse_lazy('passwordchangedone')
    ), name='passwordchange'),

    path('passwordchangedone/', auth_views.PasswordChangeDoneView.as_view(
        template_name='app/passwordchangedone.html'
    ), name='passwordchangedone'),
]

# MEDIA FILES
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
