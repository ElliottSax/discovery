class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def tree_depth(root):
    """
    Find the maximum depth of a binary tree.

    The maximum depth is the number of nodes along the longest path
    from the root node down to the farthest leaf node.

    Args:
        root: The root node of the binary tree (TreeNode or None)

    Returns:
        int: The maximum depth of the tree (0 if empty)
    """
    if root is None:
        return 0

    left_depth = tree_depth(root.left)
    right_depth = tree_depth(root.right)

    return max(left_depth, right_depth) + 1


def invert_tree(root):
    """
    Invert a binary tree recursively.

    Inverts the tree by swapping the left and right children
    of every node in the tree.

    Args:
        root: The root node of the binary tree (TreeNode or None)

    Returns:
        TreeNode: The root of the inverted tree (or None if empty)
    """
    if root is None:
        return None

    root.left, root.right = root.right, root.left

    invert_tree(root.left)
    invert_tree(root.right)

    return root


def is_balanced(root):
    """
    Check if a binary tree is height-balanced.

    A height-balanced binary tree is defined as a binary tree in which
    the depth of the two subtrees of every node never differs by more than 1.

    Args:
        root: The root node of the binary tree (TreeNode or None)

    Returns:
        bool: True if the tree is balanced, False otherwise
    """
    def check_height(node):
        if node is None:
            return 0

        left_height = check_height(node.left)
        if left_height == -1:
            return -1

        right_height = check_height(node.right)
        if right_height == -1:
            return -1

        if abs(left_height - right_height) > 1:
            return -1

        return max(left_height, right_height) + 1

    return check_height(root) != -1
