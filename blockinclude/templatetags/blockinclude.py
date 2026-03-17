from typing import TYPE_CHECKING, Any, cast

import django.template
import django.template.loader_tags
from django.template.loader_tags import construct_relative_path


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
        Render the template with block and slot contents as extra context variables.

        We pass the content as context variables so they are always available, even
        when the ``only`` keyword is used. With ``only``, the include tag limits the
        context to the ``extra_context`` which includes only the variables passed as
        keyword arguments to the tag.

        .. admonition:: Template node reuse and thread safety

            Django compiles each template once and caches the resulting node tree for
            all subsequent renders. The cached loader (``django.template.loaders.cached
            .Loader``) stores these compiled templates keyed by template name, so the
            exact same ``Node`` *instances* are reused across every request.

            See the Django docs for details:

            * Thread-safety considerations for custom template tags —
              https://docs.djangoproject.com/en/stable/howto/custom-template-tags/#thread-safety-considerations
            * ``django.template.loaders.cached.Loader`` —
              https://docs.djangoproject.com/en/stable/ref/templates/api/#django.template.loaders.cached.Loader
            * Django source — ``django/template/loaders/cached.py`` and
              ``django/template/base.py``

            Because node instances are shared, **mutating instance attributes inside
            ``render()`` is not safe**: changes would persist across requests and could
            drop nodes permanently or cause cross-request data leakage under
            concurrency.

            To avoid this, we:

            1. Work on a *copy* of ``self.content_nodelist`` so that removing slot
               nodes does not permanently alter the shared node tree.
            2. Build a *per-render* ``values`` dict rather than writing into the
               shared ``self.extra_context`` dict.
            3. Re-implement the template-resolution and rendering logic from
               ``IncludeNode.render()`` so that we can inject the per-render values
               without touching any instance attributes.  The template object itself
               is still cached safely through ``context.render_context``, exactly as
               Django's own ``IncludeNode`` does.
        """
        # Work on a copy of the nodelist to avoid permanently removing slot nodes
        # from the shared, cached instance-level nodelist.
        content_nodelist = django.template.base.NodeList(self.content_nodelist)

        # Resolve the included template, caching the template object in
        # context.render_context (a per-render dict) to avoid reparsing on every
        # call (e.g., when the tag is inside a for-loop).  This mirrors the caching
        # strategy used by Django's own IncludeNode.render().
        template = self.template.resolve(context)
        if not callable(getattr(template, "render", None)):
            template_name = template or ()
            if isinstance(template_name, str):
                template_name = (
                    construct_relative_path(
                        self.origin.template_name,
                        template_name,
                    ),
                )
            else:
                template_name = tuple(template_name)
            cache = context.render_context.dicts[0].setdefault(self, {})
            template = cache.get(template_name)
            if template is None:
                template = context.template.engine.select_template(template_name)
                cache[template_name] = template
        elif hasattr(template, "template"):
            # Use the base Template of a backends.django.Template.
            template = template.template

        # Build a per-render values dict, starting by resolving the keyword arguments
        # that were passed to the tag at parse time (stored in self.extra_context).
        # Reading self.extra_context here is safe because we only *read* it.
        values = {
            name: var.resolve(context) for name, var in self.extra_context.items()
        }

        # Extract and render slot nodes, removing them from the working copy so they
        # are not also rendered as part of the main content block.
        slots = cast(list[SlotNode], content_nodelist.get_nodes_by_type(SlotNode))
        for slot in slots:
            content_nodelist.remove(slot)
            # Render each slot's content in the parent context and store it under the
            # variable name defined on the slot node.
            values[slot.target_variable_name] = slot.render(context)

        # Render the remaining (non-slot) content in the parent context and expose it
        # as the ``content`` variable inside the included template.
        values["content"] = content_nodelist.render(context)

        if self.isolated_context:
            return template.render(context.new(values))
        with context.push(**values):
            return template.render(context)


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
