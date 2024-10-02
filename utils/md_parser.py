import re


def parse(text: str, version=2) -> str:
    """
    Escapes special characters for Telegram MarkdownV2 formatting.

    Args:
        text (str): The markdown text to be escaped.
        version (int, optional): The Markdown version (1 or 2). Defaults to 2.

    Returns:
        str: The escaped markdown text.
    """
    if version == 1:
        escape_chars = r"_*\`["
    elif version == 2:
        escape_chars = r"_*\[\]()~`>#+-=|{}.!"
    else:
        raise ValueError("Markdown version must be either 1 or 2")

    # Function to escape special characters
    def replace(match):
        char = match.group(0)
        return "\\" + char

    # Escape special characters
    pattern = re.compile(f"([{re.escape(escape_chars)}])")
    text = pattern.sub(replace, text)

    # Handle code and pre-formatted text blocks
    text = re.sub(
        r"(?P<delim>`+)(?P<code>.*?)\1",
        lambda m: m.group("delim")
        + m.group("code").replace("\\", "\\\\").replace("`", "\\`")
        + m.group("delim"),
        text,
        flags=re.DOTALL,
    )

    text = re.sub(
        r"(?P<delim>```)(?P<code>.*?)(?P=delim)",
        lambda m: m.group("delim")
        + m.group("code").replace("\\", "\\\\").replace("`", "\\`")
        + m.group("delim"),
        text,
        flags=re.DOTALL,
    )

    return text
