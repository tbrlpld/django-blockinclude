import dataclasses
import os
import pathlib

from typing import TYPE_CHECKING

import django.http
import django.shortcuts
import django.urls
import django.utils.html


if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse


@dataclasses.dataclass
class Link:
    href: str
    text: str


def index(request: "HttpRequest") -> "HttpResponse":
    """Render a page with all examples."""

    test_template_filenames = get_test_template_filenames()

    links = [
        Link(
            href=django.urls.reverse("render_test_template", kwargs={"filename": ttf}),
            text=get_title_from_filename(ttf),
        )
        for ttf in sorted(test_template_filenames)
        if not ttf.startswith("_")
    ]

    return django.shortcuts.render(
        request,
        template_name="pages/index.html",
        context={"links": links},
    )


class HttpResponseTemplateNotFound(django.http.HttpResponseNotFound):
    def __init__(self, *, filename: str) -> None:
        filename = django.utils.html.escape(filename)
        super().__init__(content=f"Requested test template not found: {filename}")


def render_test_template(request: "HttpRequest", filename: str) -> "HttpResponse":
    """Render the requested test template."""

    allowed_filenames = get_test_template_filenames()
    if filename not in allowed_filenames:
        return HttpResponseTemplateNotFound(filename=filename)

    title = get_title_from_filename(filename)

    return django.shortcuts.render(
        request,
        template_name=f"tests/{filename}",
        context={
            "title": title,
            "items": [
                "Lorem",
                "Ipsum",
            ],
        },
    )


def get_title_from_filename(filename: str) -> str:
    title = filename[8:-5].replace("-", " ").title()
    return title


def get_test_template_filenames() -> tuple[str, ...]:
    views_filepath = pathlib.Path(__file__)
    test_template_dir = views_filepath.parent / "templates/tests"
    test_template_filenames = os.listdir(test_template_dir)
    return tuple(test_template_filenames)
