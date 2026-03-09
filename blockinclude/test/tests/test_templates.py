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
            context=context or {},
        )

        soup = bs4.BeautifulSoup(response.content, "html.parser")
        return soup

    @staticmethod
    def get_included_box(soup: bs4.BeautifulSoup) -> bs4.Tag:
        the_box = soup.find(id="the-box")
        assert isinstance(the_box, bs4.Tag)  # type narrowing
        return the_box

    def test_simple_text_content(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-01-blockinclude-with-simple-text-content.html",
        )

        # Find container defined in the include.
        the_box = self.get_included_box(soup=soup)
        # Find the content, defined in the parent template, in the container.
        result = the_box.find(string=re.compile("Lorem"))
        self.assertIsNotNone(result)

    def test_content_with_markup(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-02-blockinclude-content-with-markup.html",
        )

        the_box = self.get_included_box(soup=soup)
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

        the_box = self.get_included_box(soup=soup)
        # The loop to render the list is in the parent.
        ul = the_box.find("ul")
        assert isinstance(ul, bs4.Tag)  # type narrowing
        items = ul.find_all("li")
        self.assertEqual(items[0].string, "Lorem")
        self.assertEqual(items[1].string, "Ipsum")

    def test_does_not_pollute_parent_context(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-04-blockinclude-does-not-pollute-parent-context.html",
        )

        the_box = self.get_included_box(soup=soup)
        # The content is found in the box.
        box_content = the_box.find(string=re.compile("Lorem"))
        self.assertIsNotNone(box_content)
        # The content is not found in the output in the parent template.
        output = soup.find(id="content-output-in-parent")
        assert isinstance(output, bs4.Tag)
        output_content = output.find(string=re.compile("Lorem"))
        self.assertIsNone(output_content)
