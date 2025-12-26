def prime_sieve(n: int) -> list[int]:
    """
    Implement the Sieve of Eratosthenes to find all primes up to n.

    Args:
        n: Upper limit (inclusive) for finding primes.

    Returns:
        List of all prime numbers from 2 to n.
    """
    if n < 2:
        return []

    # Initialize sieve: True means potentially prime
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False

    # Sieve: mark multiples of each prime as composite
    for i in range(2, int(n ** 0.5) + 1):
        if is_prime[i]:
            # Mark all multiples of i starting from i*i
            for j in range(i * i, n + 1, i):
                is_prime[j] = False

    # Collect all primes
    return [i for i, prime in enumerate(is_prime) if prime]


def prime_factors(n: int) -> list[int]:
    """
    Return the prime factorization of n as a list of prime factors.

    Args:
        n: A positive integer to factorize.

    Returns:
        List of prime factors in ascending order (with repetition).
        For example, prime_factors(12) returns [2, 2, 3].

    Raises:
        ValueError: If n is less than 2.
    """
    if n < 2:
        raise ValueError("n must be at least 2")

    factors = []

    # Extract all factors of 2
    while n % 2 == 0:
        factors.append(2)
        n //= 2

    # Check odd factors from 3 upward
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
