"""
HTML and text sanitization utilities for security
Prevents XSS attacks by cleaning user-provided content
"""
import bleach
from typing import Optional, List


# Allowed HTML tags for rich text (minimal set for security)
ALLOWED_TAGS = [
    'b', 'i', 'u', 'em', 'strong',  # Text formatting
    'p', 'br',  # Paragraphs and line breaks
    'ul', 'ol', 'li',  # Lists
]

# Allowed HTML attributes
ALLOWED_ATTRIBUTES = {
    '*': ['class'],  # Allow class on all elements for styling
}

# Protocols allowed in links (none by default for incident descriptions)
ALLOWED_PROTOCOLS = []


def sanitize_html(text: str, strip: bool = True) -> str:
    """
    Sanitize HTML content to prevent XSS attacks

    Args:
        text: Raw text that may contain HTML
        strip: If True, strip all HTML tags. If False, allow safe tags

    Returns:
        Sanitized text safe for storage and display

    Examples:
        >>> sanitize_html("<script>alert('XSS')</script>Hello")
        "Hello"

        >>> sanitize_html("<b>Bold text</b>", strip=False)
        "<b>Bold text</b>"
    """
    if not text:
        return text

    if strip:
        # Strip all HTML tags for incident descriptions
        return bleach.clean(
            text,
            tags=[],  # No tags allowed
            strip=True  # Remove tags, keep content
        )
    else:
        # Allow minimal safe HTML tags
        return bleach.clean(
            text,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True
        )


def sanitize_text_field(text: str) -> str:
    """
    Sanitize plain text fields (descriptions, location names, etc.)
    Removes all HTML tags and potentially dangerous content

    Args:
        text: Raw text input

    Returns:
        Clean text with all HTML removed
    """
    if not text:
        return text

    # Strip all HTML
    cleaned = bleach.clean(text, tags=[], strip=True)

    # Remove NULL bytes
    cleaned = cleaned.replace('\x00', '')

    # Normalize whitespace
    cleaned = ' '.join(cleaned.split())

    return cleaned


def sanitize_url(url: str) -> Optional[str]:
    """
    Sanitize and validate URL

    Args:
        url: Raw URL string

    Returns:
        Sanitized URL or None if invalid
    """
    if not url:
        return url

    # Linkify will sanitize URLs
    cleaned = bleach.linkify(
        url,
        parse_email=False,
        callbacks=[],
        skip_tags=['pre', 'code']
    )

    # Only allow http and https protocols
    if not (cleaned.startswith('http://') or cleaned.startswith('https://')):
        return None

    return cleaned


def sanitize_list_field(items: List[str]) -> List[str]:
    """
    Sanitize a list of strings (tags, media URLs, etc.)

    Args:
        items: List of strings

    Returns:
        List of sanitized strings
    """
    if not items:
        return items

    return [sanitize_text_field(item) for item in items if item]


def validate_no_null_bytes(value: str) -> str:
    """
    Validate that a string doesn't contain NULL bytes

    Args:
        value: String to validate

    Returns:
        Original value if valid

    Raises:
        ValueError: If NULL bytes found
    """
    if '\x00' in value:
        raise ValueError("NULL bytes are not allowed in text fields")
    return value
