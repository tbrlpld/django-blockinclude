import django.template
import django.test


class TestBlockIncludeNodeReuse(django.test.SimpleTestCase):
    """
    Test repeat rendering of a given template using the blockinclude tag.

    Template rendering is split into two steps. Parsing of the template string into a
    node list, and rendering of that node list with a given context. For performance
    reasons, Django caches the result of the template parsing, the list of node
    instances. This means our nodes need to be safe to be reused and rendered with
    different contexts. The following tests check that our nodes are safe for repeated
    rendering with different contexts.
    """

    TEMPLATE_WITH_VARIABLE_IN_BLOCK = (
        "{% load blockinclude %}"
        "{% blockinclude 'includes/the-box.html' %}"
        "{{ title }}"
        "{% endblockinclude %}"
    )

    TEMPLATE_WITH_HEADER_SLOT = (
        "{% load blockinclude %}"
        "{% blockinclude 'includes/the-slotted-box.html' %}"
        "{% slot header %}{{ title }}{% endslot %}"
        "Content"
        "{% endblockinclude %}"
    )

    def test_second_render_with_changed_context(
        self,
    ) -> None:
        """
        When the same template node is reused for a different blockinclude
        call (without a slot), stale slot content from a previous render must
        not bleed through.
        """
        template = django.template.Template(self.TEMPLATE_WITH_VARIABLE_IN_BLOCK)

        # First render populates the content with a "title" variable.
        first_output = template.render(
            django.template.Context({"title": "Title value"})
        )
        # Second render uses a context without "title".
        second_output = template.render(django.template.Context({}))

        self.assertIn("Title value", first_output)
        # When no "title" variable is in the context, the blocks content is empty. We
        # should not find the previously used content anymore.
        self.assertNotIn("Title value", second_output)

    def test_render_template_twice_with_different_context(self) -> None:
        """
        Rendering the same template node twice with different contexts should
        reflect the context of each render.
        """
        template = django.template.Template(self.TEMPLATE_WITH_HEADER_SLOT)

        first_output = template.render(
            django.template.Context({"title": "First Title"})
        )
        second_output = template.render(
            django.template.Context({"title": "Second Title"})
        )

        self.assertIn("First Title", first_output)
        # Second render must reflect the second context, not the first.
        self.assertIn("Second Title", second_output)
        self.assertNotIn("First Title", second_output)

    def test_second_render_with_different_context_reflects_updated_slot_content(
        self,
    ) -> None:
        """
        Rendering the same template node twice with different contexts should
        reflect the context of each render.

        This test fails with the current implementation because:

        * On the first render, ``self.content_nodelist.remove(slot)``
          permanently removes the SlotNode.  On the second render there are no
          slot nodes left to process, so no new slot content is rendered.
        * ``self.extra_context`` persists between renders, so the header value
          rendered during the first render ("First Title") is still present
          during the second render and is returned instead of "Second Title".
        """
        template = django.template.Template(self.TEMPLATE_WITH_HEADER_SLOT)

        first_output = template.render(
            django.template.Context({"title": "First Title"})
        )
        second_output = template.render(
            django.template.Context({"title": "Second Title"})
        )

        self.assertIn("First Title", first_output)
        # Second render must reflect the second context, not the first.
        self.assertIn("Second Title", second_output)
        self.assertNotIn("First Title", second_output)
