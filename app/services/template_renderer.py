"""
Template rendering with Jinja2 support and backward compatibility.

Supports both:
- Legacy syntax: {document}
- Jinja2 syntax: {{ document }}
"""
from jinja2 import Template, TemplateSyntaxError
import logging

logger = logging.getLogger(__name__)


def render_template(template_string: str, document_text: str, **extra_vars) -> str:
    """
    Render a template with document text.

    Automatically detects template syntax:
    - If template contains {{ or {% (Jinja2 markers), use Jinja2
    - Otherwise, fall back to simple string replacement

    Args:
        template_string: The template to render
        document_text: The document text to inject
        **extra_vars: Additional variables for Jinja2 templates

    Returns:
        Rendered template string

    Examples:
        # Legacy syntax
        >>> render_template("Summarize: {document}", "Hello world")
        "Summarize: Hello world"

        # Jinja2 syntax
        >>> render_template("Summarize: {{ document }}", "Hello world")
        "Summarize: Hello world"

        # Jinja2 with filters
        >>> render_template("{{ document | upper }}", "hello")
        "HELLO"
    """
    # Detect if template uses Jinja2 syntax
    uses_jinja2 = "{{" in template_string or "{%" in template_string

    if uses_jinja2:
        # Use Jinja2 rendering
        try:
            logger.debug("Rendering template with Jinja2")
            template = Template(template_string)
            return template.render(document=document_text, **extra_vars)
        except TemplateSyntaxError as e:
            logger.error(f"Jinja2 template syntax error: {e}")
            raise ValueError(f"Invalid Jinja2 template: {e}")
    else:
        # Fall back to legacy simple replacement
        logger.debug("Rendering template with legacy string replacement")
        return template_string.replace("{document}", document_text)
