from django.contrib import admin
from django.urls import path
from stylesync.views import home, remove_background_view  # Import both views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('remove-background/', remove_background_view,
         name='remove_background'),  # Add the new URL pattern
]
