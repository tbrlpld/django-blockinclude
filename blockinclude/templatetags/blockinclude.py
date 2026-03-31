import typing

from typing import TYPE_CHECKING

import django.template.base
import django.template.loader_tags

import blockinclude.string


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
            include_context_data[slot.target_variable_name] = slot.render_content(
                context
            )

        # Create a new layer of context with the new data in it. We use a context
        # manager so that after the end of the function, our custom context data is
        # removed from the context again. This avoids "polluting" the parent context.
        with context.update(include_context_data):
            return super().render(context)


@register.tag(name=BLOCKINCLUDE_START_TAG)
def do_block_include(
    parser: django.template.base.Parser,
    token: django.template.base.Token,
) -> BlockInclude:
    '''
    Render block content and pass it as `content` variable to the included template.

    This is an extension of Django's default `include` tag and supports all of its
    features. Additionally, it allows you to pass a block of rendered markup to the
    included template.

    ```django
    {% blockinclude "my-box.html" %}
        The body content of the box.
    {% endblockinclude %}
    ```

    In the above example, the `my-box.html` template will have a `content` variable
    with the value `"The body content of the box."` in the context.

    The content can include any sort of HTML markup you like.

    If you use template logic between the `blockinclude`/`endblockinclude` tags, then
    the that logic is evaluated in the context of the parent and then passed to the
    included template.

    ```django
    {% blockinclude "my-box.html" %}
        <ul>
            {% for item in items %}
                <li>{{ item }}</li>
            {% endfor %}
        </ul>
    {% endblockinclude %}
    ```

    If the parent is rendered with `items = ["Apple", "Banana"]` in the context,
    then the included template will receive the `content` variable` with the value:

    ```python
    """
    <ul>
        <li>Apple</li>
        <li>Banana</li>
    </ul>
    """
    ```

    If you wish to pass more than one block of markup with different names to the
    included template, you can add `slot` tags inside the `blockinclude`.

    ```django
    {% blockinclude "my-slotted-box.html" %}
        {% slot "header" %}
            Header of the box
        {% endslot %}

        The body content of the box.
    {% endblockinclude %}
    ```

    In the above example, the `my-slotted-box.html` template will receive the variables
    `content="The body content of the box."` and `header="Header of the box"`.

    You can use as many `slot` tags inside a `blockinclude` as you like. The `slot`
    does have to be a direct child of the `blockinclude` and can not be nested in other
    template block tags (`if` or `for`) inside the `blockinclude`. The `blockinclude`
    itself can be nested inside of other template tag blocks just fine.
    '''

    # Grab the content
    content_nodelist = parser.parse((BLOCKINCLUDE_END_TAG,))
    # "Consume" the closing tag. Whatever that means. Including this based on the docs.
    # https://docs.djangoproject.com/en/6.0/howto/custom-template-tags/#parsing-until-another-block-tag
    parser.delete_first_token()

    # With the rest of the tag, let the default include tag do its thing.
    include_node: django.template.loader_tags.IncludeNode = (
        django.template.loader_tags.do_include(parser, token)
    )

    # We update the extra context (the stuff passed as keyword arguments) so that it
    # expects a `content` variable in the context in which the include node is
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
    # We are only interested in the direct children of the `blockinclude`. This is to
    # avoid removing slots that may be nested inside a if block.
    slot_nodes = [n for n in content_nodelist if isinstance(n, SlotNode)]
    for slot_node in slot_nodes:
        # Remove the slot nodes from the content nodelist so they are not rendered
        # as part of the main content. Slot nodes don't render themselves. But, we
        # don't need to call them twice for no reason.
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
    Slot node to be consumed by the `BlockIncludeNode`.

    This node does not render or manipulate the context directly. It's basically a no-op
    node. The point of the node is to make the template variable and content nodelist
    available for consumption by a `BlockIncludeNode`.
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
    ) -> typing.Literal[""]:
        """
        No-op rendering.

        We don't want rendering of the slot to accidentally be output or to pollute the
        parent context. Thus, we always returns an empty string and perform no context
        side effects.

        To access the rendered contents of the node, use the `render_content` method.
        """
        return ""

    def render_content(
        self,
        context: django.template.context.Context,
    ) -> "django.utils.safestring.SafeString":
        """
        Alternative method to render the contents of the slot.

        We don't want rendering of the slot to accidentally be output or to pollute the
        parent context. Thus, the default `render` method always returns an empty
        string and has no context side effects. If we really want the rendered contents,
        then this method should be used instead.
        """
        return self.content_nodelist.render(context)


@register.tag(name=SLOT_START_TAG)
def do_slot(
    parser: django.template.base.Parser,
    token: django.template.base.Token,
) -> SlotNode:
    """
    Define variable name for a markup block to the parent `blockinclude`.

    Use this tag to define a block of markup and pass it as a context variable to the
    template included by the surrounding `blockinclude`. The name of the variable is
    defined as the first, and only, argument to this tag.

    Note: The slot name  needs to be quoted and a valid Python variable name.

    This tag needs to be used as a direct child of the `blockinclude`. Nesting it inside
    other block tags (like `if`, `for` etc.) does not work.

    Usage:
    ```django
    {% blockinclude "my-box.html" %}
        {% slot "header" %}
            Header of the box
        {% endslot %}

        The body content of the box.
    {% endblockinclude %}
    ```
    """
    content_nodelist = parser.parse((SLOT_END_TAG,))
    parser.delete_first_token()

    bits = token.split_contents()
    if len(bits) != 2:
        raise django.template.exceptions.TemplateSyntaxError(
            "%r tag takes exactly one argument: the name of the variable "
            "as which the content should be passed to the included template."
            % SLOT_START_TAG
        )

    slotname = unquote_or_raise(bits[1])

    if not slotname.isidentifier():
        raise django.template.exceptions.TemplateSyntaxError(
            "The first argument to %r needs to be a valid Python variable name."
            % (SLOT_START_TAG)
        )

    if slotname == BLOCKINCLUDE_CONTENT_VAR_NAME:
        raise django.template.exceptions.TemplateSyntaxError(
            "%r is a protected variable used for the main block content of %r. "
            "It can not be used as an argument to %r."
            % (BLOCKINCLUDE_CONTENT_VAR_NAME, BLOCKINCLUDE_START_TAG, SLOT_START_TAG)
        )

    return SlotNode(
        content_nodelist=content_nodelist,
        target_variable_name=slotname,
    )


def unquote_or_raise(slotname: str) -> str:
    """
    Remove surrounding quotes from the slotname.

    Raises `django.template.exceptions.TemplateSyntaxError` if the slotname was
    not quoted.
    """
    potential_slotname = slotname
    unquoted_slotname = blockinclude.string.without_quotes(potential_slotname)
    had_quotes = potential_slotname != unquoted_slotname
    if not had_quotes:
        raise django.template.exceptions.TemplateSyntaxError(
            "The first argument to %r has to be quoted. "
            "Please use '%s %s \"%s\" %s'."
            % (
                SLOT_START_TAG,
                django.template.base.BLOCK_TAG_START,
                SLOT_START_TAG,
                potential_slotname,
                django.template.base.BLOCK_TAG_END,
            ),
        )
    return unquoted_slotname
