import json
import logging
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache import cache


logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 6 * 60 * 60
CACHE_KEY = "github_latest_release"
FAILURE_CACHE_SECONDS = 15 * 60
REQUEST_TIMEOUT_SECONDS = 3
VERSION_PATTERN = re.compile(r"^v?(\d+(?:\.\d+)*)(?:[-+][0-9A-Za-z.-]+)?$")


def get_update_info():
    release = _get_latest_release()
    if release is None:
        return {"update_available": False}

    installed_version = _version_key(settings.APP_VERSION)
    latest_version = _version_key(release["tag_name"])
    if installed_version is None or latest_version is None:
        return {"update_available": False}

    return {
        "update_available": _is_newer(latest_version, installed_version),
        "latest_version": release["tag_name"].removeprefix("v").removeprefix("V"),
        "release_url": release["html_url"],
    }


def _get_latest_release():
    cached_release = cache.get(CACHE_KEY)
    if cached_release is not None:
        return cached_release or None

    repository = settings.DEVELOPER_URL.rstrip("/")
    if not repository.startswith("https://github.com/"):
        return None

    api_url = repository.replace(
        "https://github.com/",
        "https://api.github.com/repos/",
        1,
    ) + "/releases/latest"
    request = Request(
        api_url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"MS-Contable/{settings.APP_VERSION}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
        release = _validated_release(payload, repository)
    except (OSError, ValueError, TypeError) as error:
        logger.info("No se pudo consultar la última versión de GitHub: %s", error)
        cache.set(CACHE_KEY, {}, FAILURE_CACHE_SECONDS)
        return None

    if release is None:
        cache.set(CACHE_KEY, {}, FAILURE_CACHE_SECONDS)
        return None

    cache.set(CACHE_KEY, release, CHECK_INTERVAL_SECONDS)
    return release


def _validated_release(payload, repository):
    if not isinstance(payload, dict):
        return None

    tag_name = payload.get("tag_name")
    html_url = payload.get("html_url")
    if not isinstance(html_url, str):
        return None
    parsed_url = urlparse(html_url)
    expected_path = urlparse(repository).path.rstrip("/") + "/releases/tag/"
    if (
        not isinstance(tag_name, str)
        or _version_key(tag_name) is None
        or parsed_url.scheme != "https"
        or parsed_url.netloc != "github.com"
        or not parsed_url.path.startswith(expected_path)
    ):
        return None

    return {"tag_name": tag_name, "html_url": html_url}


def _version_key(version):
    match = VERSION_PATTERN.fullmatch(version.strip())
    if match is None:
        return None
    return tuple(int(part) for part in match.group(1).split("."))


def _is_newer(latest_version, installed_version):
    length = max(len(latest_version), len(installed_version))
    latest = latest_version + (0,) * (length - len(latest_version))
    installed = installed_version + (0,) * (length - len(installed_version))
    return latest > installed
