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

    def test_second_render_with_content_changed_to_empty(
        self,
    ) -> None:
        """
        When the same template node is reused for another render call, stale
        blockinclude content from a previous render must not bleed through.
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

    def test_second_render_with_content_changed_to_different_value(
        self,
    ) -> None:
        """
        When the same template node is reused for another render call, stale
        blockinclude content from a previous render must not bleed through.
        """
        template = django.template.Template(self.TEMPLATE_WITH_VARIABLE_IN_BLOCK)

        # First render populates the content with a "title" variable.
        first_output = template.render(
            django.template.Context({"title": "First title"})
        )
        # Second render populates the content with a different value for the "title"
        # variable.
        second_output = template.render(
            django.template.Context({"title": "Second title"})
        )

        self.assertIn("First title", first_output)
        self.assertNotIn("First title", second_output)
        self.assertIn("Second title", second_output)

    def test_second_render_with_slot_content_changed_to_empty(
        self,
    ) -> None:
        """
        When the same template node is reused for another render call, stale
        slot content from a previous render must not bleed through.
        """
        template = django.template.Template(self.TEMPLATE_WITH_HEADER_SLOT)

        # First render populates the content with a "title" variable.
        first_output = template.render(
            django.template.Context({"title": "Title value"})
        )
        # Second render uses a context without "title".
        second_output = template.render(django.template.Context({}))

        self.assertIn("Title value", first_output)
        # When no "title" variable is in the context, the slot content is empty. We
        # should not find the previously used content anymore.
        self.assertNotIn("Title value", second_output)

    def test_second_render_with_slot_content_changed_to_different_value(
        self,
    ) -> None:
        """
        When the same template node is reused for another render call, stale
        slot content from a previous render must not bleed through.
        """
        template = django.template.Template(self.TEMPLATE_WITH_HEADER_SLOT)

        # First render populates the content with a "title" variable.
        first_output = template.render(
            django.template.Context({"title": "First title"})
        )
        # Second render populates the content with a different value for the "title"
        # variable.
        second_output = template.render(
            django.template.Context({"title": "Second title"})
        )

        self.assertIn("First title", first_output)
        self.assertNotIn("First title", second_output)
        self.assertIn("Second title", second_output)
