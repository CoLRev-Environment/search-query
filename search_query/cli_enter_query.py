import os

from search_query import AndQuery
from search_query import OrQuery
from search_query.node import Node
from search_query.query import Query

# # Typical building-blocks approach
# digital_synonyms = OrQuery(["digital", "virtual", "online"], search_field="Abstract")
# work_synonyms = OrQuery(["work", "labor", "service"], search_field="Abstract")
# query = AndQuery([digital_synonyms, work_synonyms], search_field="Author Keywords")

# print(query.to_string(syntax="ieee"))
# print(query.to_string(syntax="pubmed"))
# print(query.to_string(syntax="wos"))

PLACEHOLDER = " ( ? ) "
INSTRUCTION = (
    'Enter "AND" or "OR" to add a new query, or "q" to complete the current level.'
)


def create_query(query_to_edit: Query = None, query_to_print: Query = None) -> Query:
    if not query_to_edit:
        print(INSTRUCTION)
        print(f"\nCurrent query: \n {PLACEHOLDER}\n")
        # print(PLACEHOLDER)
        q_input = input("QUERY: ")
        if q_input == "AND":
            query_to_edit = AndQuery([], search_field="Author Keywords")
            query_to_edit.children = [PLACEHOLDER]
        if q_input == "OR":
            query_to_edit = OrQuery([], search_field="Author Keywords")
            query_to_edit.children = [PLACEHOLDER]
        query_to_print = query_to_edit

    while True:
        os.system("clear")
        print(INSTRUCTION)
        print()
        if query_to_print:
            print("Current query: \n ")
            print(query_to_print.to_string(syntax="pre_notation"))
            print()

        item_input = input("QUERY: ")
        if item_input in ["AND", "OR"]:
            if item_input == "AND":
                new_query = AndQuery([], search_field="Author Keywords")
                new_query.children = [PLACEHOLDER]
            if item_input == "OR":
                new_query = OrQuery([], search_field="Author Keywords")
                new_query.children = [PLACEHOLDER]

            query_to_edit.children[-1] = new_query
            create_query(new_query, query_to_print)
            query_to_edit.children.append(PLACEHOLDER)
            continue
        if item_input == "q":
            if PLACEHOLDER in query_to_edit.children:
                query_to_edit.children.remove(PLACEHOLDER)
            break

        query_to_edit.children[-1] = Node(
            item_input, operator=False, search_field="Author Keywords"
        )
        query_to_edit.children.append(PLACEHOLDER)

    return query_to_edit


if __name__ == "__main__":
    # query = AndQuery([PLACEHOLDER], search_field="Author Keywords")
    # or_query = OrQuery(["online", "digital"], search_field="Author Keywords")

    # query.children.append(or_query)
    # # If we try to print the query, we get an error:
    # print(query.to_string(syntax="pre_notation"))

    # if we call the constructor again, there is no error:
    # query = AndQuery([PLACEHOLDER, or_query], search_field="Author Keywords")
    # print(query.to_string(syntax="pre_notation"))

    print("TODO: simple one-term queries")
    print("TODO: undo last entry?")

    q = create_query()
    os.system("clear")
    print("Final query:")
    # print('To show the current state, we need to call the top-level constructor and replace placeholders')
    print(q.to_string(syntax="pre_notation"))
