def matrix_multiply(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    """
    Multiply two matrices a and b.

    Args:
        a: First matrix (m x n)
        b: Second matrix (n x p)

    Returns:
        Result matrix (m x p)

    Raises:
        ValueError: If matrices cannot be multiplied (incompatible dimensions)
    """
    if not a or not b or not a[0] or not b[0]:
        raise ValueError("Matrices cannot be empty")

    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])

    if cols_a != rows_b:
        raise ValueError(f"Cannot multiply: matrix A has {cols_a} columns, matrix B has {rows_b} rows")

    result = [[0.0 for _ in range(cols_b)] for _ in range(rows_a)]

    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += a[i][k] * b[k][j]

    return result
