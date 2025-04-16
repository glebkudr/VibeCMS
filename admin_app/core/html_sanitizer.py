"""
admin_app/core/html_sanitizer.py

Constants for HTML sanitization with bleach.
Use these in all places where user HTML is sanitized (admin, API, generator).
"""

ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 's', 'code', 'pre',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'dl', 'dt', 'dd',
    'blockquote', 'hr',
    'a', 'img',
    'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td',
    'div', 'span', 'input',
]
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'input': ['type', 'checked', 'disabled'],
    'code': ['class'],
    'pre': ['class'],
    'th': ['colspan', 'rowspan'],
    'td': ['colspan', 'rowspan'],
}

# Simple function to allow any URL (use with caution if source is untrusted)
def passthrough_url(url):
    """Returns the URL unchanged."""
    return url

# ALLOWED_STYLES is not used by html-sanitizer
# ALLOWED_STYLES = [
#     'color', 'background-color', 'font-family', 'text-align',
# ] 