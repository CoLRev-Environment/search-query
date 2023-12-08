import sys

def main():
    print("***search-query***")
    run = True
    while run:
        data = input("Please choose option: \n *to enter a new search string, type: search-string"
         + "\n *to translate your search string to a different database syntax, type: translate"
         + "\n *to exit the python package, type: exit \n")
        
        #build search string
        if data=="search-string":
            print("search")
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

