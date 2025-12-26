def floyd_warshall(graph):
    """
    Find all pairs shortest paths using the Floyd-Warshall algorithm.

    Args:
        graph: A 2D list (adjacency matrix) where graph[i][j] represents
               the weight of the edge from vertex i to vertex j.
               Use float('inf') for no direct edge between vertices.

    Returns:
        A 2D list containing the shortest distances between all pairs of vertices.
        Returns None if a negative cycle is detected.
    """
    n = len(graph)

    # Create a copy of the graph to store distances
    dist = [[graph[i][j] for j in range(n)] for i in range(n)]

    # Floyd-Warshall algorithm
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] != float('inf') and dist[k][j] != float('inf'):
                    if dist[i][k] + dist[k][j] < dist[i][j]:
                        dist[i][j] = dist[i][k] + dist[k][j]

    # Check for negative cycles (diagonal should be 0 or positive)
    for i in range(n):
        if dist[i][i] < 0:
            return None  # Negative cycle detected

    return dist


if __name__ == "__main__":
    # Example usage
    INF = float('inf')

    # Example graph as adjacency matrix
    graph = [
        [0, 3, INF, 5],
        [2, 0, INF, 4],
        [INF, 1, 0, INF],
        [INF, INF, 2, 0]
    ]

    result = floyd_warshall(graph)

    if result is None:
        print("Negative cycle detected!")
    else:
        print("Shortest distances between all pairs:")
        for row in result:
            print([x if x != INF else "INF" for x in row])
