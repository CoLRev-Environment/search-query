class Node:
    
    value="work"
    operator=True
    children=[]
    
    def __init__(self, value, operator):
        self.value=value
        self.operator=operator

    
    def printNode(self):
        print("value: "+self.value+" operator: "+str(self.operator)+" children: "+str(len(self.children)))
        return
    
    



