import django.template


register = django.template.library.Library()


class BlockInclude(django.template.Node):

    def render(self, context: django.template.context.Context) -> str:
        return ""


@register.tag(name="blockinclude")
def do_block_include(
    parser: django.template.base.Parser,
    token: django.template.base.Token,
) -> BlockInclude:
    # Grab the content
    _ = parser.parse(("endblockinclude",))
    parser.delete_first_token()

    return BlockInclude()
