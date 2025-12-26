def mod_exponentiation(base: int, exponent: int, modulus: int) -> int:
    """
    Compute (base ^ exponent) % modulus using fast modular exponentiation.

    Uses the binary exponentiation method (also known as exponentiation by squaring)
    which runs in O(log exponent) time.

    Args:
        base: The base number
        exponent: The exponent (must be non-negative)
        modulus: The modulus (must be positive)

    Returns:
        (base ^ exponent) % modulus

    Raises:
        ValueError: If exponent is negative or modulus is not positive
    """
    if modulus <= 0:
        raise ValueError("Modulus must be positive")
    if exponent < 0:
        raise ValueError("Exponent must be non-negative")

    if modulus == 1:
        return 0

    result = 1
    base = base % modulus

    while exponent > 0:
        # If exponent is odd, multiply result with base
        if exponent & 1:
            result = (result * base) % modulus

        # Square the base and halve the exponent
        exponent >>= 1
        base = (base * base) % modulus

    return result
