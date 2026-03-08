import django.shortcuts
import django.test


class TestTemplates(django.test.SimpleTestCase):
    def test_blockinclude_passes_content_from_parent(self) -> None:
        result = django.shortcuts.render(
            request=None,
            template_name="tests/test-blockinclude-passes-content-from-parent.html",
            context={},
        )

        # Make soup.
        # Find content from parent in container.
        self.fail(result)
