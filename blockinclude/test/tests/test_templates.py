import re

import bs4
import django.shortcuts
import django.test


class TestTemplates(django.test.SimpleTestCase):
    def test_blockinclude_passes_text_content_from_parent(self) -> None:
        response = django.shortcuts.render(
            request=None,
            template_name="tests/test-01-blockinclude-passes-text-content-from-parent.html",
            context={},
        )

        # Make soup.
        soup = bs4.BeautifulSoup(response.content, "html.parser")
        # Find container defined in the include.
        the_box = soup.find(id="the-box")
        assert isinstance(the_box, bs4.Tag)  # type narrowing
        # Find the content, defined in the parent template, in the container.
        result = the_box.find(string=re.compile("Lorem"))
        self.assertIsNotNone(result)

    def test_blockinclude_passes_markup_content_from_parent(self) -> None:
        response = django.shortcuts.render(
            request=None,
            template_name=(
                "tests/test-02-blockinclude-passes-markup-content-from-parent.html"
            ),
            context={},
        )

        # Make soup.
        soup = bs4.BeautifulSoup(response.content, "html.parser")
        the_box = soup.find(id="the-box")
        assert isinstance(the_box, bs4.Tag)  # type narrowing
        bolded = the_box.find("b", string="Lorem")
        self.assertIsNotNone(bolded)
