from typing import Any


class Node:
    value="work"
    operator=True
    leftChild=object
    rightChild=object
    


    def __init__(self, value, operator, leftChild, rightChild):
        self.value=value
        self.operator=operator
        self.leftChild=leftChild
        self.rightChild=rightChild
        
    
    def printNode(self):
        print("value:"+self.value+"operator:"+self.operator)
        return
    



