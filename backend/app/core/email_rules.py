from pydantic import EmailStr


MEDISTOCK_EMAIL_DOMAIN = "medistock.com"


def validate_medistock_email(value: EmailStr) -> EmailStr:
    """Require application user accounts to use the MediStock domain."""
    if str(value).rsplit("@", 1)[-1].lower() != MEDISTOCK_EMAIL_DOMAIN:
        raise ValueError("Email address must use the @medistock.com domain")
    return value
