class Node:
    def __init__(self, value, operator, searchField):
        self.value = value
        self.validateValue()
        self.operator = operator
        self.children = []
        self.marked=False
        if operator== False:
            if(searchField!=""):
                self.searchField = searchField
            else:
                self.searchField = "keywords"
        
    # validate value input
    def validateValue(self):
        if (
            self.value.startswith("!")
            | self.value.startswith("&")
            | self.value.startswith("$")
            | self.value.startswith("%")
            | self.value.startswith("*")
        ):
            raise Exception(f"The value you entered: {self.value} is invalid. Search terms cannot start with: !, &, $, %, or, *")
        

    def printNode(self):
        print(f"value: {self.value} operator: {str(self.operator)} children: {str(len(self.children))} search field: {self.searchField}")
        return
