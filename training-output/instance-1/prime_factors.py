def prime_factors(n):
    """Return all prime factors of a number.

    Args:
        n: A positive integer greater than 1

    Returns:
        A list of prime factors in ascending order (with duplicates)
    """
    if n < 2:
        return []

    factors = []
    divisor = 2

    while divisor * divisor <= n:
        while n % divisor == 0:
            factors.append(divisor)
            n //= divisor
        divisor += 1

    if n > 1:
        factors.append(n)

    return factors
