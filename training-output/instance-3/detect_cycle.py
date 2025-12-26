def detect_cycle(graph: dict[int, list[int]]) -> bool:
    """
    Detect if a directed graph contains a cycle using DFS.

    Args:
        graph: Adjacency list representation where keys are nodes
               and values are lists of neighboring nodes.

    Returns:
        True if the graph contains a cycle, False otherwise.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}

    def dfs(node: int) -> bool:
        color[node] = GRAY

        for neighbor in graph.get(node, []):
            if color.get(neighbor, WHITE) == GRAY:
                # Found a back edge - cycle detected
                return True
            if color.get(neighbor, WHITE) == WHITE and dfs(neighbor):
                return True

        color[node] = BLACK
        return False

    for node in graph:
        if color[node] == WHITE:
            if dfs(node):
                return True

    return False
