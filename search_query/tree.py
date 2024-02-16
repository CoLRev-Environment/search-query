class Tree:
    def __init__(self, root):
        self.root = root
        
    def removeAllMarks(self):
        self.root.marked=False
        for c in self.root.children:
            c.marked=False
        return
