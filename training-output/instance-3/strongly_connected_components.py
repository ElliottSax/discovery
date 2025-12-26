from collections import defaultdict


def strongly_connected_components(graph: dict[int, list[int]]) -> list[list[int]]:
    """
    Find all strongly connected components in a directed graph using Kosaraju's algorithm.

    Args:
        graph: Adjacency list representation of a directed graph.
                Keys are node ids, values are lists of adjacent nodes.

    Returns:
        A list of strongly connected components, where each component is a list of nodes.

    Example:
        >>> graph = {0: [1], 1: [2], 2: [0, 3], 3: [4], 4: [5], 5: [3]}
        >>> strongly_connected_components(graph)
        [[3, 5, 4], [0, 2, 1]]
    """
    # Get all nodes from graph (including nodes that only appear as destinations)
    all_nodes = set(graph.keys())
    for neighbors in graph.values():
        all_nodes.update(neighbors)

    # Step 1: Perform DFS and fill stack with finish order
    visited = set()
    finish_order = []

    def dfs_first_pass(node: int) -> None:
        visited.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs_first_pass(neighbor)
        finish_order.append(node)

    for node in all_nodes:
        if node not in visited:
            dfs_first_pass(node)

    # Step 2: Build the transposed (reversed) graph
    transposed = defaultdict(list)
    for node, neighbors in graph.items():
        for neighbor in neighbors:
            transposed[neighbor].append(node)

    # Step 3: Process nodes in reverse finish order on the transposed graph
    visited.clear()
    sccs = []

    def dfs_second_pass(node: int, component: list[int]) -> None:
        visited.add(node)
        component.append(node)
        for neighbor in transposed.get(node, []):
            if neighbor not in visited:
                dfs_second_pass(neighbor, component)

    for node in reversed(finish_order):
        if node not in visited:
            component = []
            dfs_second_pass(node, component)
            sccs.append(component)

    return sccs


if __name__ == "__main__":
    # Example usage
    graph = {
        0: [1],
        1: [2],
        2: [0, 3],
        3: [4],
        4: [5],
        5: [3]
    }

    result = strongly_connected_components(graph)
    print("Strongly Connected Components:")
    for i, scc in enumerate(result):
        print(f"  Component {i + 1}: {scc}")
