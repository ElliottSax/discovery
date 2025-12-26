from collections import deque
from typing import List, Optional


class TreeNode:
    def __init__(self, val: int = 0, left: 'TreeNode' = None, right: 'TreeNode' = None):
        self.val = val
        self.left = left
        self.right = right


def zigzag_traversal(root: Optional[TreeNode]) -> List[List[int]]:
    """
    Return the zigzag level order traversal of a binary tree.

    Zigzag traversal alternates direction at each level:
    - Level 0: left to right
    - Level 1: right to left
    - Level 2: left to right
    - And so on...

    Args:
        root: The root node of the binary tree

    Returns:
        A list of lists, where each inner list contains node values at that level
        in zigzag order
    """
    if not root:
        return []

    result = []
    queue = deque([root])
    left_to_right = True

    while queue:
        level_size = len(queue)
        level = deque()

        for _ in range(level_size):
            node = queue.popleft()

            if left_to_right:
                level.append(node.val)
            else:
                level.appendleft(node.val)

            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)

        result.append(list(level))
        left_to_right = not left_to_right

    return result


if __name__ == "__main__":
    #       3
    #      / \
    #     9  20
    #       /  \
    #      15   7
    root = TreeNode(3)
    root.left = TreeNode(9)
    root.right = TreeNode(20)
    root.right.left = TreeNode(15)
    root.right.right = TreeNode(7)

    print(zigzag_traversal(root))  # [[3], [20, 9], [15, 7]]
