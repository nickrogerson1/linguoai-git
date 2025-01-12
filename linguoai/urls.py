from django.contrib import admin
from django.urls import path, include, re_path
from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from django.conf import settings
from django.views.static import serve

from django.contrib.sitemaps import GenericSitemap
from django.contrib.sitemaps.views import sitemap
from blog.models import BlogPage

info_dict = {
    "queryset": BlogPage.objects.all(),
    "date_field": "last_published_at",
}

urlpatterns = [
    path('cms/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),
    path('blog/', include(wagtail_urls)),

    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": {"blog": GenericSitemap(info_dict, priority=0.6)}},
        name="django.contrib.sitemaps.views.sitemap",
    ),

    path('tz_detect/', include('tz_detect.urls')),
    path('admin/', admin.site.urls),

    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),

    path('', include('home.urls')),
    
    path('', include('landing_pages.urls')),
    path('', include('members.urls')),

]
