import dataclasses
import os

from pathlib import Path
from typing import TYPE_CHECKING

import django.http
import django.template
import django.urls

from django.shortcuts import render


if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse


@dataclasses.dataclass
class Link:
    href: str
    text: str


def index(request: "HttpRequest") -> "HttpResponse":
    """Render a page with all examples."""

    views_filepath = Path(__file__)
    test_template_dir = views_filepath.parent / "templates/tests"
    test_template_filenames = os.listdir(test_template_dir)

    links = [
        Link(
            href=django.urls.reverse("render_test_template", kwargs={"filename": ttf}),
            text=get_title_from_filename(ttf),
        )
        for ttf in sorted(test_template_filenames)
        if not ttf.startswith("_")
    ]

    return render(
        request,
        template_name="pages/index.html",
        context={"links": links},
    )


def render_test_template(request: "HttpRequest", filename: str) -> "HttpResponse":
    """Render the requested test template."""
    if filename.startswith("_"):
        return django.http.HttpResponseNotFound(
            f"Requested test template not found: {filename}"
        )

    title = get_title_from_filename(filename)

    try:
        return render(
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
    except django.template.TemplateDoesNotExist:
        return django.http.HttpResponseNotFound(
            f"Requested test template not found: {filename}"
        )


def get_title_from_filename(filename: str) -> str:
    title = filename[8:-5].replace("-", " ").title()
    return title
