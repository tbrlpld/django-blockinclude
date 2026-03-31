def has_quotes(string: str) -> bool:
    """
    Returns if the given text has quotes or not.

    Based on code fond in Django's `construct_relative_path`.
    """
    return string.startswith(('"', "'")) and string[0] == string[-1]


def without_quotes(string: str) -> str:
    """
    Returns the given text without surrounding quotes.

    Returns the string unchanged if no surrounding quotes are found.
    """
    if not has_quotes(string):
        return string
    return string[1:-1]
