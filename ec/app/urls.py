from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .forms import LoginFrom, MyPasswordResetFrom 
from django.contrib.auth import views as auth_view  

urlpatterns = [
    path("", views.home),
    path('about/', views.about, name="about"),
    path('contact/', views.contact, name="contact"),
    path("category/<slug:val>", views.categoryView.as_view(), name="category"),
    path("category-title/<val>", views.categoryTitle.as_view(), name="category-title"),
    path("product/<int:pk>", views.ProductDetail.as_view(), name="productdetail"),
    path("profile/", views.ProfileView.as_view(),name= "profile"),
    path("address/", views.address,name= "address"),
    path('updateAddress/<int:pk>', views.updateAddress.as_view(), name='updateAddress'),
    
    
    path('registration', views.CustomerRegistrationView.as_view(), name='customerregistrationview'),
    path('accounts/login/', auth_view.LoginView.as_view(
        template_name='app/login.html',
        authentication_form=LoginFrom
    ), name='login'),

    path('password-reset/', auth_view.PasswordResetView.as_view(
        template_name='app/password_reset.html',
        form_class=MyPasswordResetFrom
    ), name='password_reset'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
