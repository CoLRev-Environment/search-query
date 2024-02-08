from query import Query


def main():
    print("***search-query***")
    query = Query()
    data = input(
        "Please choose option: \n *to enter a new search string, type: search"
        + "\n *to exit the python package, type: exit \n"
    )
    match data:
        # build search string
        case "search":
            searchUI(query)
            return
        # leave package
        case "exit":
            return
        case _:
            print("Error invalid option, please try again!\n")
            return


def searchUI(query):
    data = input(
        "Please state first which boolean operator you would like to use to connect your search terms, "
        + "followed by your search terms in square brackets, separated by comma. \n"
        + "Example: OR [cucumber, tomato, pepper] \n"
        + "If you need to use nested structures please enter them in the following way: \n"
        + "query1 = AND[dog, cat]; OR[query1, elephant]\n"
    )

    if query.validateQueryString(data):
        data.replace(" ", "")
        query.parseQuery(data)
        processedQueryUI(query)

    else:
        print(
            "The search string you entered is invalid. Please review the instructions and try again!"
        )
        searchUI(query)
        return
    return


def processedQueryUI(query):
    nextStep = input(
        "Please choose your next step:"
        + "\n *to translate your query enter: translate"
        + "\n *to print out your search query enter: print"
        + "\n *to exit the python package, type: exit \n"
    )
    if nextStep == "translate":
        chooseDatabaseUI(query)
        return
    elif nextStep == "print":
        printUI(query)
    elif nextStep == "exit":
        return
    else:
        print("Error invalid option, try again")
        processedQueryUI(query)


def chooseDatabaseUI(query):
    nextStep = input(
        "**choose database**"
        + "\n Please choose the database-syntax in which your query should be translated: "
        + "\n *for database1, enter: db1"
        + "\n *for database2, enter: db2"
        + "\n *to exit the python package, type: exit \n"
    )
    if nextStep == "db1":
        translateUI("db1", query)
    elif nextStep == "db2":
        translateUI("db2", query)
    elif nextStep == "exit":
        return
    else:
        print("Error invalid option, try again")
        chooseDatabaseUI(query)
    return


def printUI(query):
    print("print")
    processedQueryUI(query)
    return


def translateUI(db, query):
    if db == "db2":
        query.translateDB2()
        print("Your query was translated to db2!")
        processedQueryUI(query)
    if db == "db1":
        query.translateDB1()
        print("Your query was translated to db1!")
        processedQueryUI(query)
    return


if __name__ == "__main__":
    main()
