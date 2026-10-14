MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_BYTES = 72  # bcrypt only reads the first 72 bytes


def validate_password_strength(password: str) -> str:
    # Used by every request that sets a new password.
    # Raises ValueError with a clear message when a rule is broken.

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
        )

    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError(
            "Password is too long (maximum 72 characters)"
        )

    if not any(char.isalpha() for char in password):
        raise ValueError("Password must contain at least one letter")

    if not any(char.isdigit() for char in password):
        raise ValueError("Password must contain at least one number")

    return password