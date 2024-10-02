import re


def parse(text: str, version=2) -> str:
    return text

    """
    Escapes special characters for Telegram MarkdownV2 formatting,
    preserving the original Markdown syntax.

    Args:
        text (str): The markdown text to be escaped.

    Returns:
        str: The escaped markdown text suitable for Telegram.
    """
    # List of special characters as per Telegram's MarkdownV2
    special_chars = r"_*\[\]()~`>#+-=|{}.!"

    # Function to escape special characters
    def escape(match):
        char = match.group(0)
        return "\\" + char

    # Escape backslashes first
    text = re.sub(r"\\", r"\\\\", text)

    # Handle code and pre-formatted text blocks separately
    # Regex pattern to find code blocks and inline code
    pattern = re.compile(
        r"""
        (```.*?```) |    # Code blocks with triple backticks
        (`.*?`)          # Inline code with single backticks
    """,
        re.DOTALL | re.VERBOSE,
    )

    # Split the text into code and non-code parts
    parts = pattern.split(text)

    # Process each part
    for i, part in enumerate(parts):
        if part is None:
            continue
        if pattern.match(part):
            # Inside code blocks or inline code, escape only backslashes and backticks
            part = re.sub(r"\\", r"\\\\", part)
            part = re.sub(r"`", r"\`", part)
            parts[i] = part
        else:
            # Outside code blocks, escape all special characters
            part = re.sub(r"([{}])".format(re.escape(special_chars)), escape, part)
            parts[i] = part

    # Reconstruct the text
    escaped_text = "".join(parts)

    return escaped_text
