class Node:
    def __init__(self, value, operator, searchField):
        self.value = value
        self.operator = operator
        self.children = []
        self.marked = False
        self.searchField=searchField
        if operator:
            self.searchField=""

    def printNode(self):
        
        return f"value: {self.value} operator: {str(self.operator)} search field: {self.searchField}"
        
        