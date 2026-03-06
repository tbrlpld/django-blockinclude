from django.urls import path

import blockinclude.test.example.views


urlpatterns = [
    path(
        "<str:filename>",
        blockinclude.test.example.views.render_test_template,
        name="render_test_template",
    ),
    path("", blockinclude.test.example.views.index),
]
