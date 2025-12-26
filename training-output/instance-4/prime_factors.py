def prime_factors(n: int) -> list[int]:
    """
    Return the prime factorization of n as a list of prime factors.

    Factors are returned in ascending order with repetition for multiplicity.
    For example: prime_factors(12) returns [2, 2, 3] since 12 = 2^2 * 3.

    Args:
        n: A positive integer greater than 1.

    Returns:
        A list of prime factors in ascending order.

    Raises:
        ValueError: If n is less than 2.
    """
    if n < 2:
        raise ValueError("n must be greater than or equal to 2")

    factors = []

    # Handle factor of 2
    while n % 2 == 0:
        factors.append(2)
        n //= 2

    # Check odd factors from 3 to sqrt(n)
    i = 3
    while i * i <= n:
        while n % i == 0:
            factors.append(i)
            n //= i
        i += 2

    # If n is still greater than 1, it's a prime factor
    if n > 1:
        factors.append(n)

    return factors
