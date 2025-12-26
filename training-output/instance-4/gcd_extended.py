def gcd_extended(a: int, b: int) -> tuple[int, int, int]:
    """
    Compute the GCD of a and b using the Extended Euclidean Algorithm.

    Returns a tuple (gcd, x, y) where:
    - gcd is the greatest common divisor of a and b
    - x and y are the Bezout coefficients such that: a*x + b*y = gcd
    """
    if b == 0:
        return a, 1, 0

    gcd, x1, y1 = gcd_extended(b, a % b)
    x = y1
    y = x1 - (a // b) * y1

    return gcd, x, y
