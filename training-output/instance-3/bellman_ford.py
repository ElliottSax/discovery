def bellman_ford(graph, source):
    """
    Find shortest paths from source to all vertices using Bellman-Ford algorithm.
    Handles negative edge weights and detects negative cycles.

    Args:
        graph: Dict of {vertex: [(neighbor, weight), ...]} representing adjacency list
        source: Starting vertex

    Returns:
        Tuple of (distances, predecessors) where:
            - distances: Dict mapping each vertex to its shortest distance from source
            - predecessors: Dict mapping each vertex to its predecessor in shortest path
        Returns (None, None) if a negative cycle is detected.
    """
    # Initialize distances and predecessors
    distances = {v: float('inf') for v in graph}
    predecessors = {v: None for v in graph}
    distances[source] = 0

    vertices = list(graph.keys())
    num_vertices = len(vertices)

    # Relax edges |V| - 1 times
    for _ in range(num_vertices - 1):
        for u in graph:
            for v, weight in graph[u]:
                if distances[u] != float('inf') and distances[u] + weight < distances[v]:
                    distances[v] = distances[u] + weight
                    predecessors[v] = u

    # Check for negative cycles
    for u in graph:
        for v, weight in graph[u]:
            if distances[u] != float('inf') and distances[u] + weight < distances[v]:
                return None, None  # Negative cycle detected

    return distances, predecessors


def get_path(predecessors, target):
    """Reconstruct path from source to target using predecessors dict."""
    path = []
    current = target
    while current is not None:
        path.append(current)
        current = predecessors[current]
    return path[::-1]


if __name__ == "__main__":
    # Example graph with negative weights
    graph = {
        'A': [('B', 4), ('C', 2)],
        'B': [('C', -3), ('D', 2)],
        'C': [('D', 3)],
        'D': [('E', 2)],
        'E': []
    }

    distances, predecessors = bellman_ford(graph, 'A')

    if distances is None:
        print("Negative cycle detected!")
    else:
        print("Shortest distances from A:")
        for vertex, dist in sorted(distances.items()):
            path = get_path(predecessors, vertex)
            print(f"  {vertex}: {dist} (path: {' -> '.join(path)})")
