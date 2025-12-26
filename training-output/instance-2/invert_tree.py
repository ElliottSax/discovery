from binary_search_tree import Node


def invert_tree(node):
    """
    Recursively invert a binary tree by swapping left and right children.

    Args:
        node: The root node of the tree (or subtree) to invert.

    Returns:
        The root node of the inverted tree.
    """
    if node is None:
        return None

    # Swap the left and right children
    node.left, node.right = node.right, node.left

    # Recursively invert the subtrees
    invert_tree(node.left)
    invert_tree(node.right)

    return node


if __name__ == "__main__":
    # Build a sample tree:
    #        4
    #       / \
    #      2   7
    #     / \ / \
    #    1  3 6  9
    root = Node(4)
    root.left = Node(2)
    root.right = Node(7)
    root.left.left = Node(1)
    root.left.right = Node(3)
    root.right.left = Node(6)
    root.right.right = Node(9)

    def print_tree(node, level=0, prefix="Root: "):
        if node is not None:
            print(" " * (level * 4) + prefix + str(node.value))
            if node.left or node.right:
                print_tree(node.left, level + 1, "L--- ")
                print_tree(node.right, level + 1, "R--- ")

    print("Original tree:")
    print_tree(root)

    invert_tree(root)

    print("\nInverted tree:")
    print_tree(root)
