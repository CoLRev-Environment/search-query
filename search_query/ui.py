import sys
from query import Query

def main():
    print("***search-query***")
    run = True
    while run:
        data = input("Please choose option: \n *to enter a new search string, type: search"
         + "\n *to translate your search string to a different database syntax, type: translate"
         + "\n *to exit the python package, type: exit \n")
        
        #build search string
        if data=="search":
            data = input("Please state first which boolean operator you would like to use to connect your search terms, followed by your search terms in square brackets, separated by comma. \n"
                + "Example: OR [cucumber, tomato, pepper] \n"
                + "If you need to use nested structures please enter them in the following way: \n" 
                + "query1 = AND[dog, cat]; OR[query1, elephant]\n")
            query =Query()
            query.parseQuery(data)
            
            run=False

        #perform translating operation
        elif data=="translate":
            print("translate")
            run=False

        #leave package 
        elif data=="exit":
            run=False
        
        else:
            data = print("Sorry, that's not an option! Please try again!\n")



if __name__=="__main__":
    main()

