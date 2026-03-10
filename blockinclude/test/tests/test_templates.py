import re

from typing import Any

import bs4
import django.shortcuts
import django.test


class TestTemplates(django.test.SimpleTestCase):
    """
    These test rely on some of the setup being done in the template. When writing of
    reviewing these tests, be sure to also take a look at rendered templates.

    A lot of these test rely on features of the template language and try to test its
    behavior. It would have been too cumbersome to try make all of that work with all
    the setup in and assertion in Python.
    """

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
    def get_included_box(soup: bs4.Tag) -> bs4.Tag:
        the_box = soup.find(attrs={"data-test": "the-box"})
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
        # The content is not found in the output container in the parent template.
        output = soup.find(id="content-output-in-parent")
        assert isinstance(output, bs4.Tag)
        output_content = output.find(string=re.compile("Lorem"))
        self.assertIsNone(output_content)

    def test_takes_kwargs(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-05-blockinclude-takes-kwargs.html",
        )

        the_box = self.get_included_box(soup=soup)
        box_content_text = the_box.find(string=re.compile("Lorem"))
        self.assertIsNotNone(box_content_text)
        assert isinstance(the_box.header, bs4.Tag)
        box_header_text = the_box.header.find(string=re.compile("Adipisci"))
        self.assertIsNotNone(box_header_text)

    def test_block_content_overrides_kwarg(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-06-blockinclude-block-content-overrides-kwarg.html",
        )

        the_box = self.get_included_box(soup=soup)
        unexpected_box_content_text = the_box.find(string=re.compile("Adipisci"))
        self.assertIsNone(unexpected_box_content_text)
        expected_box_content_text = the_box.find(string=re.compile("Lorem"))
        self.assertIsNotNone(expected_box_content_text)

    def test_recursion(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-07-blockinclude-recursion.html",
        )

        outer_box = self.get_included_box(soup=soup)
        self.assertTrue(outer_box.text.strip().startswith("Lorem"))
        inner_box = self.get_included_box(soup=outer_box)
        self.assertTrue(inner_box.text.strip().startswith("Phasellus"))
