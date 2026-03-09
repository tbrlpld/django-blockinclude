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
        # Find content from parent in container.
        # the_box = soup.find(id="the-box")
        # result = the_box.find(string=re.match("Lorem"))
        result = soup.find(string=re.compile("Lorem"))
        self.assertIsNotNone(result)
