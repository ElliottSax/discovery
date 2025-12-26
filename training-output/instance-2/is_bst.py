class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def is_bst(root: TreeNode) -> bool:
    """
    Validates if a binary tree is a valid Binary Search Tree (BST).

    A valid BST is defined as:
    - The left subtree of a node contains only nodes with keys less than the node's key.
    - The right subtree of a node contains only nodes with keys greater than the node's key.
    - Both left and right subtrees must also be valid BSTs.
    """
    def validate(node, min_val, max_val):
        if node is None:
            return True

        if node.val <= min_val or node.val >= max_val:
            return False

        return (validate(node.left, min_val, node.val) and
                validate(node.right, node.val, max_val))

    return validate(root, float('-inf'), float('inf'))
