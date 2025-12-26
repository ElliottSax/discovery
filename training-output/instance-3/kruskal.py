def kruskal(vertices, edges):
    """
    Find the minimum spanning tree using Kruskal's algorithm.

    Args:
        vertices: A list of vertex identifiers
        edges: A list of tuples (u, v, weight) representing edges

    Returns:
        tuple: (mst_edges, total_weight)
            - mst_edges: List of edges in the MST as (u, v, weight) tuples
            - total_weight: Total weight of the MST
    """
    # Sort edges by weight
    sorted_edges = sorted(edges, key=lambda e: e[2])

    # Union-Find data structure
    parent = {v: v for v in vertices}
    rank = {v: 0 for v in vertices}

    def find(x):
        """Find the root of x with path compression."""
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        """Union by rank. Returns True if union was performed, False if already connected."""
        root_x = find(x)
        root_y = find(y)

        if root_x == root_y:
            return False

        # Union by rank
        if rank[root_x] < rank[root_y]:
            parent[root_x] = root_y
        elif rank[root_x] > rank[root_y]:
            parent[root_y] = root_x
        else:
            parent[root_y] = root_x
            rank[root_x] += 1

        return True

    mst_edges = []
    total_weight = 0

    for u, v, weight in sorted_edges:
        if union(u, v):
            mst_edges.append((u, v, weight))
            total_weight += weight
            # MST has exactly |V| - 1 edges
            if len(mst_edges) == len(vertices) - 1:
                break

    return mst_edges, total_weight


if __name__ == "__main__":
    # Example usage
    vertices = ['A', 'B', 'C', 'D', 'E', 'F']
    edges = [
        ('A', 'B', 4),
        ('A', 'F', 2),
        ('B', 'C', 6),
        ('B', 'F', 5),
        ('C', 'D', 3),
        ('C', 'F', 1),
        ('D', 'E', 2),
        ('E', 'F', 4),
    ]

    mst_edges, total_weight = kruskal(vertices, edges)

    print("Minimum Spanning Tree edges:")
    for u, v, weight in mst_edges:
        print(f"  {u} -- {v} (weight: {weight})")
    print(f"\nTotal MST weight: {total_weight}")
