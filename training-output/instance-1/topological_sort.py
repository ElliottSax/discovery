def topological_sort(graph: dict[str, list[str]]) -> list[str]:
    """
    Return a topological ordering of nodes in a directed acyclic graph (DAG).

    Args:
        graph: Adjacency list representation where keys are nodes and values
               are lists of nodes that the key node has edges to.

    Returns:
        A list of nodes in topological order.

    Raises:
        ValueError: If the graph contains a cycle.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}
    result = []

    def dfs(node: str) -> None:
        if color[node] == GRAY:
            raise ValueError("Graph contains a cycle")
        if color[node] == BLACK:
            return

        color[node] = GRAY
        for neighbor in graph.get(node, []):
            if neighbor not in color:
                color[neighbor] = WHITE
            dfs(neighbor)
        color[node] = BLACK
        result.append(node)

    for node in graph:
        if color[node] == WHITE:
            dfs(node)

    result.reverse()
    return result
