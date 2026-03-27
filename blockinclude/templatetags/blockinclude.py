from typing import TYPE_CHECKING

import django.template.base
import django.template.loader_tags


if TYPE_CHECKING:
    import django.utils.safestring


BLOCKINCLUDE_START_TAG = "blockinclude"
BLOCKINCLUDE_END_TAG = "endblockinclude"
BLOCKINCLUDE_CONTENT_VAR_NAME = "content"
SLOT_START_TAG = "slot"
SLOT_END_TAG = "endslot"


register = django.template.library.Library()


class BlockInclude(django.template.loader_tags.IncludeNode):

    def __init__(
        self,
        template: django.template.base.FilterExpression,
        *args: object,
        content_nodelist: django.template.base.NodeList,
        slot_nodes: list["SlotNode"],
        extra_context: dict[str, django.template.base.FilterExpression] | None = None,
        isolated_context: bool = False,
        **kwargs: object,
    ) -> None:
        # Store the content nodelist. The rest of the initialization is handled by the
        # IncludeNode.
        self.content_nodelist = content_nodelist
        self.slot_nodes = slot_nodes
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

        include_context_data: dict[str, "django.utils.safestring.SafeString"] = {}

        # Render content "in place" with context of parent. Save as the `content`
        # variable to the context in which the include tag is rendered. We have set up
        # the extra context of the include tag as if it used
        # `{% include "..." with content=content %}. Now we are making sure that the
        # `content` variable can be resolved from the context.
        include_context_data[BLOCKINCLUDE_CONTENT_VAR_NAME] = (
            self.content_nodelist.render(context)
        )

        # Do the same for the slot nodes
        for slot in self.slot_nodes:
            if slot.target_variable_name == BLOCKINCLUDE_CONTENT_VAR_NAME:
                # Ignore slots named the same as the main content variable. Ideally this
                # does not get here, but ignoring those slots for good measure.
                continue
            include_context_data[slot.target_variable_name] = slot.render(context)

        # Create a new layer of context with the new data in it. We use a context
        # manager so that after the end of the function, our custom context data is
        # removed from the context again. This avoids "poisoning" the parent context.
        with context.update(include_context_data):
            return super().render(context)


@register.tag(name=BLOCKINCLUDE_START_TAG)
def do_block_include(
    parser: django.template.base.Parser,
    token: django.template.base.Token,
) -> BlockInclude:
    # Grab the content
    content_nodelist = parser.parse((BLOCKINCLUDE_END_TAG,))
    # "Consume" the closing tag. Whatever that means. Including this based on the docs.
    # https://docs.djangoproject.com/en/6.0/howto/custom-template-tags/#parsing-until-another-block-tag
    parser.delete_first_token()

    # With the rest of the tag, let the default include tag do its thing.
    include_node: django.template.loader_tags.IncludeNode = (
        django.template.loader_tags.do_include(parser, token)
    )

    # We update the extra context (the stuff passed as keyword arguments) so that is
    # it expects a `content` variable in the context in which the include node is
    # rendered. Basically as if `{% include "..." with content=content %}` was used.
    extra_context = include_node.extra_context
    extra_context[BLOCKINCLUDE_CONTENT_VAR_NAME] = (
        django.template.base.FilterExpression(
            BLOCKINCLUDE_CONTENT_VAR_NAME,
            parser,
        )
    )

    # We do the same for each slot. Using a list comprehension instead of
    # `content_nodelist.get_nodes_by_type(...)`, because the method works recursively.
    # We are only interested in the direct children of the `blockinclude`.
    slot_nodes = [n for n in content_nodelist if isinstance(n, SlotNode)]
    for slot_node in slot_nodes:
        # Remove the slot nodes from the content nodelist so they are not rendered
        # as part of the main content.
        content_nodelist.remove(slot_node)

        extra_context[slot_node.target_variable_name] = (
            django.template.base.FilterExpression(
                slot_node.target_variable_name,
                parser,
            )
        )

    # Construct our own node with the properties of the IncludeNode. Our node is based
    # on the IncludeNode and lets it handle the default include functionality.
    # The `template`, `extra_context`, and `isolated_context` attributes are the only
    # ones defined on `IncludeNode.__init__` (besides `*args`/`**kwargs` forwarded to
    # `Node`). See:
    # https://github.com/django/django/blob/f2169ef/django/template/loader_tags.py#L166-L172
    return BlockInclude(
        template=include_node.template,
        content_nodelist=content_nodelist,
        slot_nodes=slot_nodes,
        extra_context=extra_context,
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


@register.tag(name=SLOT_START_TAG)
def do_store_content(
    parser: django.template.base.Parser,
    token: django.template.base.Token,
) -> SlotNode:
    content_nodelist = parser.parse((SLOT_END_TAG,))
    parser.delete_first_token()

    bits = token.split_contents()
    if len(bits) != 2:
        raise django.template.exceptions.TemplateSyntaxError(
            "%r tag takes exactly one argument: the name of the variable "
            "as which the content should be passed to the included template."
            % SLOT_START_TAG
        )
    if bits[1] == BLOCKINCLUDE_CONTENT_VAR_NAME:
        raise django.template.exceptions.TemplateSyntaxError(
            "%r is a protected variable used for the main block content of %r. "
            "It can not be used as an argument to %r."
            % (BLOCKINCLUDE_CONTENT_VAR_NAME, BLOCKINCLUDE_START_TAG, SLOT_START_TAG)
        )

    return SlotNode(
        content_nodelist=content_nodelist,
        target_variable_name=bits[1],
    )
