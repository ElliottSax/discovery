from collections import defaultdict, deque
from typing import TypeVar

T = TypeVar('T')


def topological_sort(graph: dict[T, list[T]]) -> list[T]:
    """
    Perform topological sort on a directed acyclic graph (DAG).

    Args:
        graph: A dictionary where keys are nodes and values are lists of
               nodes that the key node has edges pointing to.
               Example: {'a': ['b', 'c']} means 'a' -> 'b' and 'a' -> 'c'

    Returns:
        A list of nodes in topologically sorted order.

    Raises:
        ValueError: If the graph contains a cycle.

    Example:
        >>> graph = {'a': ['b', 'c'], 'b': ['d'], 'c': ['d'], 'd': []}
        >>> topological_sort(graph)
        ['a', 'c', 'b', 'd']  # or another valid ordering
    """
    # Calculate in-degree for each node
    in_degree: dict[T, int] = defaultdict(int)
    all_nodes: set[T] = set()

    # Collect all nodes and initialize in-degrees
    for node in graph:
        all_nodes.add(node)
        for neighbor in graph[node]:
            all_nodes.add(neighbor)
            in_degree[neighbor] += 1

    # Ensure all nodes have an in-degree entry
    for node in all_nodes:
        if node not in in_degree:
            in_degree[node] = 0

    # Queue of nodes with no incoming edges
    queue: deque[T] = deque([node for node in all_nodes if in_degree[node] == 0])

    result: list[T] = []

    while queue:
        node = queue.popleft()
        result.append(node)

        # Reduce in-degree for neighbors
        for neighbor in graph.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Check for cycle
    if len(result) != len(all_nodes):
        raise ValueError("Graph contains a cycle - topological sort not possible")

    return result


if __name__ == "__main__":
    # Example usage
    dag = {
        'a': ['b', 'c'],
        'b': ['d'],
        'c': ['d'],
        'd': ['e'],
        'e': []
    }

    print("Graph:", dag)
    print("Topological order:", topological_sort(dag))

    # Example with integers
    int_dag = {
        5: [2, 0],
        4: [0, 1],
        2: [3],
        3: [1],
        0: [],
        1: []
    }

    print("\nGraph:", int_dag)
    print("Topological order:", topological_sort(int_dag))
