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

    def assertIsTag(self, obj: Any) -> bs4.Tag:
        """
        Assert that the given object is a Tag and return it.

        This method combines the type assertion with type narrowing by returning the
        checked object. This ensures that a type failure would create a sensible test
        failure too, while also avoiding duplication of the assertion.

        We need to return the asserted object, because mypy otherwise won't notice that
        we asserted the type.
        """
        try:
            assert isinstance(obj, bs4.Tag)
        except AssertionError:
            self.fail("Object %s is unexpectedly not a tag" % obj)
        else:
            return obj

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
        bolded = the_box.find(name="b")
        bolded = self.assertIsTag(bolded)
        self.assertStringInTag(string="Lorem", tag=bolded)

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
        ul = self.assertIsTag(ul)
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
        output = self.assertIsTag(output)
        self.assertStringNotInTag(string="Lorem", tag=output)

    def test_takes_kwargs(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-05-blockinclude-takes-kwargs.html",
        )

        the_box = self.get_included_box(soup=soup)
        self.assertStringInTag(string="Lorem", tag=the_box)
        header = self.assertIsTag(the_box.header)
        self.assertStringInTag(string="Adipisci", tag=header)

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
        div = self.assertIsTag(the_box.div)
        self.assertStringInTag(string="Lorem", tag=div)
        header = self.assertIsTag(the_box.header)
        bolded = self.assertIsTag(header.b)
        self.assertStringInTag(string="Phasellus", tag=bolded)

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
        div = self.assertIsTag(the_box.div)
        self.assertStringInTag(string="Lorem", tag=div)
        assert isinstance(the_box.header, bs4.Tag)
        header = self.assertIsTag(the_box.header)
        list_ = self.assertIsTag(header.ul)
        items = list_.find_all("li")
        self.assertEqual(items[0].string, "Etiam")
        self.assertEqual(items[1].string, "Donec")

    def test_multiple_slots(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-10-multiple-slots.html",
        )

        the_box = self.get_included_box(soup=soup)
        div = self.assertIsTag(the_box.div)
        self.assertStringInTag(string="Lorem", tag=div)
        header = self.assertIsTag(the_box.header)
        self.assertStringInTag(string="Phasellus", tag=header)
        footer = self.assertIsTag(the_box.footer)
        self.assertStringInTag(string="Minima", tag=footer)

    def test_slot_order_does_not_matter(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-11-slot-order-does-not-matter.html",
        )

        the_box = self.get_included_box(soup=soup)
        div = self.assertIsTag(the_box.div)
        self.assertStringInTag(string="Lorem", tag=div)
        header = self.assertIsTag(the_box.header)
        self.assertStringInTag(string="Phasellus", tag=header)
        footer = self.assertIsTag(the_box.footer)
        self.assertStringInTag(string="Minima", tag=footer)

    def test_slot_surrounded_by_blockinclude_content(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-12-slot-surrounded-by-blockinclude-content.html",
        )

        the_box = self.get_included_box(soup=soup)
        div = self.assertIsTag(the_box.div)
        self.assertStringInTag(string="Lorem", tag=div)
        self.assertStringInTag(string="Minima", tag=div)
        header = self.assertIsTag(the_box.header)
        self.assertStringInTag(string="Phasellus", tag=header)

    def test_slot_overrides_kwarg(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-13-slot-overrides-kwarg.html",
        )

        the_box = self.get_included_box(soup=soup)
        div = self.assertIsTag(the_box.div)
        self.assertStringInTag(string="Lorem", tag=div)
        header = self.assertIsTag(the_box.header)
        self.assertStringNotInTag(string="Adipisci", tag=header)
        self.assertStringInTag(string="Phasellus", tag=header)

    def test_slot_named_content_is_overridden(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-14-slot-named-content-is-overridden.html",
        )

        the_box = self.get_included_box(soup=soup)
        the_box = self.assertIsTag(the_box)
        self.assertStringNotInTag(string="Adipisci", tag=the_box)
        self.assertStringInTag(string="Lorem", tag=the_box)

    def test_only_does_not_remove_content_or_slots(self) -> None:
        soup = self.get_soup_for_template(
            template_name="tests/test-15-only-does-not-remove-content-or-slot.html",
        )

        the_box = self.get_included_box(soup=soup)
        div = self.assertIsTag(the_box.div)
        self.assertStringInTag(string="Lorem", tag=div)
        header = self.assertIsTag(the_box.header)
        self.assertStringInTag(string="Phasellus", tag=header)
        self.assertIsNone(the_box.footer)

    def test_repeated_renders_produce_consistent_output(self) -> None:
        """
        Rendering the same template multiple times must produce identical output.

        Django caches the compiled template node tree and reuses the same Node
        instances across renders (see the ``django.template.loaders.cached.Loader``
        docs and the thread-safety section for custom template tags).  If
        ``BlockInclude.render()`` mutated instance attributes (e.g. by removing slot
        nodes from ``self.content_nodelist`` or writing into ``self.extra_context``),
        a second render of the same template would see a corrupted node tree and
        produce wrong output.  This test guards against that regression.
        """
        template_name = "tests/test-16-repeated-render.html"
        first_soup = self.get_soup_for_template(template_name=template_name)
        second_soup = self.get_soup_for_template(template_name=template_name)

        # Both renders must contain the slot content.
        first_box = self.get_included_box(soup=first_soup)
        second_box = self.get_included_box(soup=second_soup)

        for box in (first_box, second_box):
            self.assertStringInTag(string="Lorem", tag=box)
            header = self.assertIsTag(box.header)
            self.assertStringInTag(string="Phasellus", tag=header)
