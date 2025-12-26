import heapq
from typing import Optional


def dijkstra(
    graph: dict[str, list[tuple[str, int | float]]],
    start: str,
    end: str
) -> tuple[Optional[list[str]], int | float]:
    """
    Find the shortest path in a weighted graph using Dijkstra's algorithm.

    Args:
        graph: Adjacency list where keys are nodes and values are lists of
               (neighbor, weight) tuples.
        start: Starting node.
        end: Target node.

    Returns:
        A tuple of (path, distance) where path is a list of nodes from start
        to end, and distance is the total weight. Returns (None, inf) if no
        path exists.
    """
    if start not in graph:
        return None, float('inf')

    # Priority queue: (distance, node)
    heap = [(0, start)]
    # Track shortest distance to each node
    distances = {start: 0}
    # Track the path (previous node for each node)
    previous = {}
    # Track visited nodes
    visited = set()

    while heap:
        current_dist, current = heapq.heappop(heap)

        if current in visited:
            continue
        visited.add(current)

        if current == end:
            # Reconstruct path
            path = []
            node = end
            while node is not None:
                path.append(node)
                node = previous.get(node)
            return path[::-1], current_dist

        for neighbor, weight in graph.get(current, []):
            if neighbor in visited:
                continue

            new_dist = current_dist + weight
            if new_dist < distances.get(neighbor, float('inf')):
                distances[neighbor] = new_dist
                previous[neighbor] = current
                heapq.heappush(heap, (new_dist, neighbor))

    return None, float('inf')


if __name__ == "__main__":
    # Example usage
    graph = {
        'A': [('B', 1), ('C', 4)],
        'B': [('A', 1), ('C', 2), ('D', 5)],
        'C': [('A', 4), ('B', 2), ('D', 1)],
        'D': [('B', 5), ('C', 1)],
    }

    path, distance = dijkstra(graph, 'A', 'D')
    print(f"Path: {path}")       # Path: ['A', 'B', 'C', 'D']
    print(f"Distance: {distance}")  # Distance: 4
