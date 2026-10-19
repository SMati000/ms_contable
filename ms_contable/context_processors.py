from django.conf import settings
from core.services.version_checker import CHECK_INTERVAL_SECONDS


def app_info(request):
    app_version_tag = settings.APP_VERSION
    if not app_version_tag.lower().startswith("v"):
        app_version_tag = f"v{app_version_tag}"

    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "app_version_tag": app_version_tag,
        "developer": settings.DEVELOPER,
        "developer_url": settings.DEVELOPER_URL,
        "version_check_interval_ms": CHECK_INTERVAL_SECONDS * 1000,
    }
