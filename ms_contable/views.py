from django.shortcuts import render
from django.urls import Resolver404, resolve


def page_not_found(request, exception):
    return render(
        request,
        "404.html",
        {"nearest_section_url": _nearest_section_url(request.path_info)},
        status=404,
    )


def _nearest_section_url(path):
    segments = [segment for segment in path.split("/") if segment]
    for depth in range(len(segments) - 1, 1, -1):
        candidate = f"/{'/'.join(segments[:depth])}/"
        try:
            match = resolve(candidate)
        except Resolver404:
            continue

        if match.url_name == "app_list" or (
            match.url_name and match.url_name.endswith("_changelist")
        ):
            return candidate

    return None
