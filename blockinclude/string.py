def has_quotes(string: str) -> bool:
    """
    Returns if the given text has quotes or not.

    Based on code fond in Django's `construct_relative_path`.
    """
    return string.startswith(('"', "'")) and string[0] == string[-1]
