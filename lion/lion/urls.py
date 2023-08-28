from django.contrib import admin
from django.urls import path

from sns.urls import urlpatterns as sns_urls


urlpatterns = [
    path("admin/", admin.site.urls),
]

urlpatterns += sns_urls
