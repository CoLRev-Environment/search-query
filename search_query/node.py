class Node:
    def __init__(self, value, operator):
        self.value = value
        self.operator = operator
        self.children = []

    def printNode(self):
        print(
            "value: "
            + self.value
            + " operator: "
            + str(self.operator)
            + " children: "
            + str(len(self.children))
        )
        return
