from .views import all_coin_memos_view, stream_memos, terms_of_use_view, privacy_policy_view, post_view
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

app_name = "hello_world"


# URL routing patterns for the project
urlpatterns = [
    # Main application views
    path("", all_coin_memos_view, name='all_coin_memos_view'),  # Home page
    path("stream-memos/", stream_memos, name="stream-memos"),  # Stream endpoint for real-time memos

    # Terms pages
    path("terms-of-use/", terms_of_use_view, name="terms_of_use"),  # Terms of use page
    path("post/", post_view, name="post"), # How to post page
    path("privacy-policy/", privacy_policy_view, name="privacy_policy"), # Privacy policy page

    # Admin site
    path("admin/", admin.site.urls),

    # Developer tools (browser reload)
    path("__reload__/", include("django_browser_reload.urls")),
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)