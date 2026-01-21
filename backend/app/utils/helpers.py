"""
Helper Utilities
"""
import re
import unicodedata
from typing import Optional
import random
import string


def generate_slug(text: str, max_length: int = 100) -> str:
    """
    Generate a URL-friendly slug from text.
    
    Args:
        text: Input text
        max_length: Maximum length of slug
    
    Returns:
        URL-friendly slug
    """
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces and special characters with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    
    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length].rsplit('-', 1)[0]
    
    return text


def generate_unique_slug(text: str, existing_slugs: list) -> str:
    """
    Generate a unique slug by appending a number if needed.
    
    Args:
        text: Input text
        existing_slugs: List of existing slugs to check against
    
    Returns:
        Unique slug
    """
    base_slug = generate_slug(text)
    slug = base_slug
    counter = 1
    
    while slug in existing_slugs:
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug


def generate_room_id(length: int = 8) -> str:
    """Generate a random room ID for tournaments"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def generate_room_password(length: int = 6) -> str:
    """Generate a random room password"""
    return ''.join(random.choices(string.digits, k=length))


def format_currency_pkr(amount: float) -> str:
    """Format amount as PKR currency"""
    return f"Rs. {amount:,.0f}"


def format_currency_usd(amount: float) -> str:
    """Format amount as USD currency"""
    return f"${amount:,.2f}"


def mask_phone_number(phone: str) -> str:
    """
    Mask phone number for display.
    Example: +923001234567 -> +92300***4567
    """
    if len(phone) < 8:
        return phone
    
    return phone[:5] + '***' + phone[-4:]


def mask_email(email: str) -> str:
    """
    Mask email for display.
    Example: user@example.com -> u***@example.com
    """
    if '@' not in email:
        return email
    
    local, domain = email.split('@')
    if len(local) <= 2:
        masked_local = local[0] + '***'
    else:
        masked_local = local[0] + '***' + local[-1]
    
    return f"{masked_local}@{domain}"


def validate_pakistan_phone(phone: str) -> tuple[bool, Optional[str]]:
    """
    Validate and format Pakistan phone number.
    
    Accepts:
        - 03001234567
        - +923001234567
        - 923001234567
    
    Returns:
        (is_valid, formatted_number)
    """
    # Remove all non-numeric characters
    cleaned = ''.join(filter(str.isdigit, phone))
    
    # Handle different formats
    if cleaned.startswith('92'):
        cleaned = '0' + cleaned[2:]
    
    # Validate format (should be 11 digits starting with 03)
    if len(cleaned) != 11 or not cleaned.startswith('03'):
        return False, None
    
    # Format as international
    formatted = '+92' + cleaned[1:]
    
    return True, formatted


def calculate_prize_distribution(
    prize_pool: int,
    num_winners: int = 3
) -> dict:
    """
    Calculate prize distribution for tournaments.
    Default: 50% first, 30% second, 20% third
    
    Returns:
        {"first": amount, "second": amount, "third": amount}
    """
    if num_winners == 1:
        return {"first": prize_pool}
    elif num_winners == 2:
        return {
            "first": int(prize_pool * 0.65),
            "second": int(prize_pool * 0.35)
        }
    else:
        return {
            "first": int(prize_pool * 0.50),
            "second": int(prize_pool * 0.30),
            "third": int(prize_pool * 0.20)
        }
