from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from lessons.admin import admin_site
from lessons import views as lesson_views 



urlpatterns = [
    path("", home, name="home"),  # root URL
    path("admin/", admin_site.urls), 
    path("lessons/", include("lessons.urls")),
    path('', lesson_views.home, name='home'),

    # Authentication URLs
    path("accounts/login/", auth_views.LoginView.as_view(template_name="lessons/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
]

# Serve media files in DEBUG mode (local dev)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
