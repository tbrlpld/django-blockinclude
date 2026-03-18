import django.template
import django.test


class TestBlockIncludeNodeReuse(django.test.SimpleTestCase):
    """
    Tests that expose state mutation bugs in BlockInclude.render().

    Template nodes are reused across renders when the template is cached (e.g.
    via Django's cached template loader or when a Template object is rendered
    more than once). The current implementation mutates instance state during
    render(), which causes incorrect behavior on subsequent renders of the same
    template node:

    1. ``self.content_nodelist.remove(slot)`` permanently removes SlotNode
       objects from the nodelist, so slot content is missing on subsequent
       renders.
    2. ``self.extra_context`` is mutated in place and persists between renders,
       so stale rendered content from a previous render leaks into later ones.
    """

    TEMPLATE_WITH_HEADER_SLOT = (
        "{% load blockinclude %}"
        "{% blockinclude 'includes/the-slotted-box.html' %}"
        "{% slot header %}{{ title }}{% endslot %}"
        "Content"
        "{% endblockinclude %}"
    )

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

    def test_second_render_with_no_slot_content_does_not_show_previous_slot(
        self,
    ) -> None:
        """
        When the same template node is reused for a different blockinclude
        call (without a slot), stale slot content from a previous render must
        not bleed through.

        This demonstrates the ``self.extra_context`` mutation bug: after the
        first render the header key remains in ``extra_context``, so the second
        render unexpectedly displays a header even though no slot is defined.

        Note: this scenario requires two *different* Template objects whose
        BlockInclude nodes share the same ``extra_context`` dict — which is
        exactly what happens when the parser reuses cached node instances.
        Instead we simulate it by rendering the same Template twice, where the
        second context omits the variable used inside the slot.
        """
        template = django.template.Template(self.TEMPLATE_WITH_HEADER_SLOT)

        # First render populates the header slot.
        first_output = template.render(
            django.template.Context({"title": "Persistent Title"})
        )
        # Second render uses a context without "title".
        second_output = template.render(django.template.Context({}))

        self.assertIn("Persistent Title", first_output)
        # Without a title in context the slot renders an empty string; the
        # included template should therefore not render a header section.
        self.assertNotIn("Persistent Title", second_output)
