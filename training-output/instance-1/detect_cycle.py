def detect_cycle(graph: dict[int, list[int]]) -> bool:
    """
    Detect if a directed graph has a cycle using DFS.

    Args:
        graph: Adjacency list representation where keys are nodes
               and values are lists of neighbor nodes.

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


if __name__ == "__main__":
    # Test cases
    cyclic_graph = {0: [1], 1: [2], 2: [0]}
    print(f"Cyclic graph: {detect_cycle(cyclic_graph)}")  # True

    acyclic_graph = {0: [1], 1: [2], 2: []}
    print(f"Acyclic graph: {detect_cycle(acyclic_graph)}")  # False

    self_loop = {0: [0]}
    print(f"Self-loop: {detect_cycle(self_loop)}")  # True

    empty_graph = {}
    print(f"Empty graph: {detect_cycle(empty_graph)}")  # False
