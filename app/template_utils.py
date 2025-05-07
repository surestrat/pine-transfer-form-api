import os
from pathlib import Path
import logging

logger = logging.getLogger("pine-api")


def get_template_path(template_name):
    """
    Get the absolute path to a template file

    Args:
        template_name: The name of the template file

    Returns:
        Path object representing the template's absolute path
    """
    app_dir = Path(__file__).parent
    template_dir = app_dir / "templates"
    return template_dir / template_name


def load_template(template_name):
    """
    Load a template file from the templates directory

    Args:
        template_name: The name of the template file

    Returns:
        String containing the template content or None if not found
    """
    template_path = get_template_path(template_name)

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading template '{template_name}': {str(e)}")
        return None


def format_template(template_str, **kwargs):
    """
    Format a template string using the provided keyword arguments

    Args:
        template_str: Template string with placeholders
        **kwargs: Keyword arguments to substitute in the template

    Returns:
        Formatted template string
    """
    if not template_str:
        return ""

    try:
        return template_str.format(**kwargs)
    except KeyError as e:
        logger.error(f"Missing template variable: {str(e)}")
        return template_str
    except Exception as e:
        logger.error(f"Error formatting template: {str(e)}")
        return template_str
