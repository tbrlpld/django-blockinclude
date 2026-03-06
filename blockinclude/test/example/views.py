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
            text=ttf,
        )
        for ttf in test_template_filenames
    ]

    return render(
        request,
        template_name="pages/index.html",
        context={"links": links},
    )


def render_test_template(request: "HttpRequest", filename: str) -> "HttpResponse":
    """Render the requested test template."""
    try:
        return render(
            request,
            template_name=f"tests/{filename}",
        )
    except django.template.TemplateDoesNotExist:
        return django.http.HttpResponseNotFound(
            "Requested test template not found.",
            filename,
        )
