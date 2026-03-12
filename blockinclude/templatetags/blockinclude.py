from typing import TYPE_CHECKING, Any, cast

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
        self,
        context: django.template.context.Context,
    ) -> "django.utils.safestring.SafeString":
        """
        Render the template with block and slot contents as an extra context variables.

        We are passing the content as `extra_context` so that it is always available,
        even when the `only` keyword is used. With the `only` keyword, the include
        tag limits the context to the `extra_context`, which includes only the
        variables passed as keyword arguments.
        """
        slots = cast(list[SlotNode], self.content_nodelist.get_nodes_by_type(SlotNode))
        for slot in slots:
            # Remove the slot nodes from the content nodelist so they are not rendered
            # as part of the main content.
            self.content_nodelist.remove(slot)
            # Render each slots content "in place" with context of the parent.
            rendered_slot_content = slot.render(context)
            # Store slot content as extra context in the variable defined on the slot
            # node.
            self.add_content_to_extra_context(
                key=slot.target_variable_name,
                content=rendered_slot_content,
            )

        # Render content "in place" with context of parent.
        rendered_content = self.content_nodelist.render(context)
        # Add the `content` variable to the extra context that is passed to the included
        # template.
        self.add_content_to_extra_context(key="content", content=rendered_content)
        return super().render(context)

    def add_content_to_extra_context(self, key: str, content: str) -> None:
        """
        Add the given content string as key to the extra context.

        The extra context will be provided to the included template even if the context
        is isolated via the `only` keyword.

        The values in extra context need to be a template `Variable` type. To pass an
        exact string, it needs to be surrounded by quotes. Usually extra context is
        passed with `variable=value` bits of the include tag. To pass a string you would
        quote it (`variable="The string"`). That is basically what we are reproducing
        here (`content="..."`).
        """
        # Need to ignore the type here, because somehow the assumed type for
        # `extra_context` dict values is only `FilterExpression` and I am having
        # a hard time constructing that here.
        self.extra_context[key] = django.template.base.Variable(
            var=f'"{content}"',
        )  # type: ignore[assignment]


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


class SlotNode(django.template.base.Node):
    """
    Renders the content_node list in the current context.

    Also carries a `target_variable_name` prop. That is the name of the variable that
    the `BlockIncludeNode` should use to pass the rendered output to the included
    template.
    """

    def __init__(
        self,
        content_nodelist: django.template.base.NodeList,
        target_variable_name: str,
    ) -> None:
        self.content_nodelist = content_nodelist
        self.target_variable_name = target_variable_name

    def render(
        self,
        context: django.template.context.Context,
    ) -> "django.utils.safestring.SafeString":
        return self.content_nodelist.render(context)


@register.tag(name="slot")
def do_store_content(
    parser: django.template.base.Parser,
    token: django.template.base.Token,
) -> SlotNode:
    content_nodelist = parser.parse(("endslot",))
    parser.delete_first_token()

    bits = token.split_contents()
    if len(bits) != 2:
        raise django.template.exceptions.TemplateSyntaxError(
            "%r tag takes exactly one argument: the name of the variable "
            "as which the content should be passed to the included template." % bits[0]
        )

    return SlotNode(
        content_nodelist=content_nodelist,
        target_variable_name=bits[1],
    )
