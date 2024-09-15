from django.contrib import admin
from django.urls import path
# Import both views
from stylesync.views import analyze_skin_tone_view, home, remove_background_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('remove-background/', remove_background_view,
         name='remove_background'),
    path('analyze-skin-tone/', analyze_skin_tone_view, name='analyze_skin_tone'),
]
