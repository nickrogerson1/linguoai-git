from django.contrib import admin
from django.urls import path, include
from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('cms/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),
    path('blog/', include(wagtail_urls)),

    path('tz_detect/', include('tz_detect.urls')),
    path('admin/', admin.site.urls),

    path('', include('home.urls')),
    path('', include('members.urls')),

]
