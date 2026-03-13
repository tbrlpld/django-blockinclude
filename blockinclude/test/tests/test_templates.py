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

    def assertStringInTag(self, string: str, tag: bs4.Tag) -> None:
        result = tag.find(string=re.compile(string))
        self.assertIsNotNone(
            obj=result, msg="String not found in tag: '%s' %s" % (string, tag)
        )

    def assertStringNotInTag(self, string: str, tag: bs4.Tag) -> None:
        result = tag.find(string=re.compile(string))
        self.assertIsNone(
            obj=result, msg="String unexpectedly found in tag: '%s' %s" % (string, tag)
        )

    def test_simple_text_content(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-01-blockinclude-with-simple-text-content.html",
        )

        # Find container defined in the include.
        the_box = self.get_included_box(soup=soup)
        # Find the content, defined in the parent template, in the container.
        self.assertStringInTag(string="Lorem", tag=the_box)

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
        self.assertStringNotInTag(string="Lorem", tag=output)

    def test_takes_kwargs(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-05-blockinclude-takes-kwargs.html",
        )

        the_box = self.get_included_box(soup=soup)
        self.assertStringInTag(string="Lorem", tag=the_box)
        assert isinstance(the_box.header, bs4.Tag)
        self.assertStringInTag(string="Adipisci", tag=the_box.header)

    def test_block_content_overrides_kwarg(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-06-blockinclude-block-content-overrides-kwarg.html",
        )

        the_box = self.get_included_box(soup=soup)
        self.assertStringNotInTag(string="Adipisci", tag=the_box)
        self.assertStringInTag(string="Lorem", tag=the_box)

    def test_recursion(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-07-blockinclude-recursion.html",
        )

        outer_box = self.get_included_box(soup=soup)
        self.assertStringInTag(string="Lorem", tag=outer_box)
        inner_box = self.get_included_box(soup=outer_box)
        self.assertStringInTag(string="Phasellus", tag=inner_box)

    def test_slot_content_with_markup(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-08-slot-content-with-markup.html",
            context={
                "items": [
                    "Etiam",
                    "Donec",
                ],
            },
        )

        the_box = self.get_included_box(soup=soup)
        assert isinstance(the_box.div, bs4.Tag)
        self.assertStringInTag(string="Lorem", tag=the_box.div)
        assert isinstance(the_box.header, bs4.Tag)
        assert isinstance(the_box.header.b, bs4.Tag)
        self.assertStringInTag(string="Phasellus", tag=the_box.header.b)

    def test_slot_content_with_template_logic(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-09-slot-content-with-template-logic.html",
            context={
                "items": [
                    "Etiam",
                    "Donec",
                ],
            },
        )

        the_box = self.get_included_box(soup=soup)
        assert isinstance(the_box.div, bs4.Tag)
        self.assertStringInTag(string="Lorem", tag=the_box.div)
        assert isinstance(the_box.header, bs4.Tag)
        assert isinstance(the_box.header.ul, bs4.Tag)
        items = the_box.header.ul.find_all("li")
        self.assertEqual(items[0].string, "Etiam")
        self.assertEqual(items[1].string, "Donec")

    def test_multiple_slots(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-10-multiple-slots.html",
        )

        the_box = self.get_included_box(soup=soup)
        assert isinstance(the_box.div, bs4.Tag)
        self.assertStringInTag(string="Lorem", tag=the_box.div)
        assert isinstance(the_box.header, bs4.Tag)
        self.assertStringInTag(string="Phasellus", tag=the_box.header)
        assert isinstance(the_box.footer, bs4.Tag)
        self.assertStringInTag(string="Minima", tag=the_box.footer)

    def test_slot_order_does_not_matter(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-11-slot-order-does-not-matter.html",
        )

        the_box = self.get_included_box(soup=soup)
        assert isinstance(the_box.div, bs4.Tag)
        self.assertStringInTag(string="Lorem", tag=the_box.div)
        assert isinstance(the_box.header, bs4.Tag)
        self.assertStringInTag(string="Phasellus", tag=the_box.header)
        assert isinstance(the_box.footer, bs4.Tag)
        self.assertStringInTag(string="Minima", tag=the_box.footer)

    def test_slot_surrounded_by_blockinclude_content(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-12-slot-surrounded-by-blockinclude-content.html",
        )

        the_box = self.get_included_box(soup=soup)
        assert isinstance(the_box.div, bs4.Tag)
        self.assertStringInTag(string="Lorem", tag=the_box.div)
        self.assertStringInTag(string="Minima", tag=the_box.div)
        assert isinstance(the_box.header, bs4.Tag)
        self.assertStringInTag(string="Phasellus", tag=the_box.header)

    def test_slot_overrides_kwarg(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-13-slot-overrides-kwarg.html",
        )

        the_box = self.get_included_box(soup=soup)
        assert isinstance(the_box.div, bs4.Tag)
        self.assertStringInTag(string="Lorem", tag=the_box.div)
        assert isinstance(the_box.header, bs4.Tag)
        self.assertStringNotInTag(string="Adipisci", tag=the_box.header)
        self.assertStringInTag(string="Phasellus", tag=the_box.header)

    def test_slot_named_content_is_overridden(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-14-slot-named-content-is-overridden.html",
        )

        the_box = self.get_included_box(soup=soup)
        assert isinstance(the_box, bs4.Tag)
        self.assertStringNotInTag(string="Adipisci", tag=the_box)
        self.assertStringInTag(string="Lorem", tag=the_box)
