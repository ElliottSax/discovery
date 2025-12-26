import heapq
from typing import List, Tuple


def prim(graph: dict[int, list[tuple[int, int]]]) -> list[tuple[int, int, int]]:
    """
    Find the Minimum Spanning Tree using Prim's algorithm.

    Args:
        graph: Adjacency list where graph[u] = [(v, weight), ...]
               representing edges from u to v with given weight.
               Graph should be undirected (edges in both directions).

    Returns:
        List of edges (u, v, weight) in the MST.
        Returns empty list if graph is empty.
    """
    if not graph:
        return []

    start = next(iter(graph))
    visited = {start}
    mst = []

    # Priority queue: (weight, from_node, to_node)
    edges = [(weight, start, neighbor) for neighbor, weight in graph[start]]
    heapq.heapify(edges)

    while edges and len(visited) < len(graph):
        weight, u, v = heapq.heappop(edges)

        if v in visited:
            continue

        visited.add(v)
        mst.append((u, v, weight))

        for neighbor, edge_weight in graph[v]:
            if neighbor not in visited:
                heapq.heappush(edges, (edge_weight, v, neighbor))

    return mst


if __name__ == "__main__":
    # Example usage
    graph = {
        0: [(1, 4), (7, 8)],
        1: [(0, 4), (2, 8), (7, 11)],
        2: [(1, 8), (3, 7), (5, 4), (8, 2)],
        3: [(2, 7), (4, 9), (5, 14)],
        4: [(3, 9), (5, 10)],
        5: [(2, 4), (3, 14), (4, 10), (6, 2)],
        6: [(5, 2), (7, 1), (8, 6)],
        7: [(0, 8), (1, 11), (6, 1), (8, 7)],
        8: [(2, 2), (6, 6), (7, 7)],
    }

    mst = prim(graph)
    print("Minimum Spanning Tree edges:")
    total_weight = 0
    for u, v, weight in mst:
        print(f"  {u} -- {v} (weight: {weight})")
        total_weight += weight
    print(f"Total MST weight: {total_weight}")
