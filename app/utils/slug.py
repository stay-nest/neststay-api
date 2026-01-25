"""Slug generation utilities."""
import re
import secrets
import string
from typing import Callable


def slugify_name(name: str) -> str:
    """
    Convert name to slug format.

    Args:
        name: The name to slugify

    Returns:
        Slugified name (lowercase, spaces replaced with hyphens, special chars removed)
    """
    # Convert to lowercase
    slug = name.lower()

    # Replace spaces and underscores with hyphens
    slug = re.sub(r"[\s_]+", "-", slug)

    # Remove all non-alphanumeric characters except hyphens
    slug = re.sub(r"[^a-z0-9\-]", "", slug)

    # Replace multiple consecutive hyphens with a single hyphen
    slug = re.sub(r"-+", "-", slug)

    # Remove leading and trailing hyphens
    slug = slug.strip("-")

    return slug


def generate_random_string() -> str:
    """
    Generate a 6-character alphanumeric random string.

    Uses cryptographically secure random generation.

    Returns:
        6-character alphanumeric string (lowercase letters and digits)
    """
    # Use alphanumeric characters (lowercase letters and digits)
    alphanumeric_chars = string.ascii_lowercase + string.digits

    # Generate 6 random characters
    random_str = "".join(secrets.choice(alphanumeric_chars) for _ in range(6))

    return random_str


def generate_unique_slug(name: str, check_exists: Callable[[str], bool]) -> str:
    """
    Generate a unique slug from name with random suffix.

    Format: {slugified-name}-{random-string}
    If collision occurs, appends counter: {slugified-name}-{random-string}-{counter}

    Args:
        name: The hotel name
        check_exists: Function that checks if a slug exists (returns True if exists)

    Returns:
        Unique slug string
    """
    # Slugify the name
    base_slug = slugify_name(name)

    # Generate random string
    random_str = generate_random_string()

    # Create initial slug
    slug = f"{base_slug}-{random_str}"

    # Check for collisions and append counter if needed
    counter = 1
    while check_exists(slug):
        slug = f"{base_slug}-{random_str}-{counter}"
        counter += 1

    return slug
