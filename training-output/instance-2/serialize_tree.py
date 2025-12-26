class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def serialize_tree(root: TreeNode) -> str:
    """Serialize a binary tree to a string using level-order traversal."""
    if not root:
        return ""

    result = []
    queue = [root]

    while queue:
        node = queue.pop(0)
        if node:
            result.append(str(node.val))
            queue.append(node.left)
            queue.append(node.right)
        else:
            result.append("null")

    # Remove trailing nulls
    while result and result[-1] == "null":
        result.pop()

    return ",".join(result)


def deserialize_tree(data: str) -> TreeNode:
    """Deserialize a string back to a binary tree."""
    if not data:
        return None

    values = data.split(",")
    root = TreeNode(int(values[0]))
    queue = [root]
    i = 1

    while queue and i < len(values):
        node = queue.pop(0)

        if i < len(values) and values[i] != "null":
            node.left = TreeNode(int(values[i]))
            queue.append(node.left)
        i += 1

        if i < len(values) and values[i] != "null":
            node.right = TreeNode(int(values[i]))
            queue.append(node.right)
        i += 1

    return root
