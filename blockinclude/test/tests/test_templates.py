import re

from typing import Any

import bs4
import django.shortcuts
import django.test


class TestTemplates(django.test.SimpleTestCase):
    @staticmethod
    def get_soup_for_template(
        template_name: str, context: dict[Any, Any] | None = None
    ) -> bs4.BeautifulSoup:
        response = django.shortcuts.render(
            request=None,
            template_name=template_name,
            context={},
        )

        soup = bs4.BeautifulSoup(response.content, "html.parser")
        return soup

    def test_simple_text_content(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-01-blockinclude-with-simple-text-content.html",
        )

        # Find container defined in the include.
        the_box = soup.find(id="the-box")
        assert isinstance(the_box, bs4.Tag)  # type narrowing
        # Find the content, defined in the parent template, in the container.
        result = the_box.find(string=re.compile("Lorem"))
        self.assertIsNotNone(result)

    def test_content_with_markup(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-02-blockinclude-content-with-markup.html",
        )

        the_box = soup.find(id="the-box")
        assert isinstance(the_box, bs4.Tag)  # type narrowing
        bolded = the_box.find("b", string="Lorem")
        self.assertIsNotNone(bolded)

    def test_content_with_template_logic(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-03-blockinclude-content-with-template-logic.html",
            context={
                "items": [
                    "Lorem",
                    "Ipsum",
                ],
            },
        )

        the_box = soup.find(id="the-box")
        assert isinstance(the_box, bs4.Tag)  # type narrowing
        # The loop to render the list is in the parent.
        ul = the_box.find("ul")
        assert isinstance(ul, bs4.Tag)  # type narrowing
        item_0 = ul.contents[0]
        assert isinstance(item_0, bs4.Tag)  # type narrowing
        self.assertEqual(item_0.string, "Lorem")
        item_1 = ul.contents[1]
        assert isinstance(item_1, bs4.Tag)  # type narrowing
        self.assertEqual(item_1.string, "Ipsum")
