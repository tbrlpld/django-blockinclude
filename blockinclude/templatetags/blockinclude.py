from typing import TYPE_CHECKING, Any

import django.template
import django.template.loader_tags


if TYPE_CHECKING:
    import django.utils.safestring


register = django.template.library.Library()


class BlockInclude(django.template.loader_tags.IncludeNode):

    def __init__(
        self,
        template: django.template.base.FilterExpression,
        *args: tuple[Any, ...],
        content_nodelist: django.template.NodeList,
        extra_context: dict[Any, Any] | None = None,
        isolated_context: bool = False,
        **kwargs: dict[Any, Any],
    ) -> None:
        # Store the content nodelist. The rest of the initialization is handled by the
        # IncludeNode.
        self.content_nodelist = content_nodelist
        super().__init__(
            template,
            *args,
            extra_context=extra_context,
            isolated_context=isolated_context,
            **kwargs,
        )

    def render(
        self, context: django.template.context.Context
    ) -> "django.utils.safestring.SafeString":
        """
        Render the template with block content as an extra context variable.

        The values in extra context need to be of the variable type.
        To pass an exact string, it needs to be surrounded by quotes.
        Usually extra context is passed with `variable=value` bits of the include
        tag. To pass a string you would quote it (`variable="The string"`).
        That is basically what we are reproducing here.

        We are passing the content as `extra_context` so that it is always available,
        even when the `only` keyword is used. With the `only` keyword, the include
        tag limits the context to the `extra_context`, which includes only the
        variables passed as keyword arguments.
        """
        # Render content "in place" with context of parent.
        rendered_content = self.content_nodelist.render(context)
        # Add the `content` variable to the extra context that is passed to the included
        # template.
        # Need to ignore the type here, because somehow the assumed type for
        # `extra_context` dict values is only `FilterExpression` and I am having
        # a hard time constructing that here.
        self.extra_context["content"] = django.template.base.Variable(
            var=f'"{rendered_content}"',
        )  # type: ignore[assignment]
        return super().render(context)


@register.tag(name="blockinclude")
def do_block_include(
    parser: django.template.base.Parser,
    token: django.template.base.Token,
) -> BlockInclude:
    # Grab the content
    content_nodelist = parser.parse(("endblockinclude",))
    # "Consume" the closing tag. Whatever that means. Including this based on the docs.
    # https://docs.djangoproject.com/en/6.0/howto/custom-template-tags/#parsing-until-another-block-tag
    parser.delete_first_token()

    # With the rest of the tag, let the default include tag do its thing.
    include_node: django.template.loader_tags.IncludeNode = (
        django.template.loader_tags.do_include(parser, token)
    )

    # Construct our own node with the properties of the IncludeNode. Our node is based
    # on the IncludeNode and lets it handle the default include functionality.
    return BlockInclude(
        template=include_node.template,
        content_nodelist=content_nodelist,
        extra_context=include_node.extra_context,
        isolated_context=include_node.isolated_context,
    )
