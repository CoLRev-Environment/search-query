"""CLI tool for entering search queries"""
import os
import typing

from search_query import AndQuery
from search_query import OrQuery
from search_query.query import Query
from search_query.query import SearchField

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


def create_query(
    query_to_edit: typing.Optional[Query] = None,
    query_to_print: typing.Optional[Query] = None,
) -> Query:
    """Create-query function"""
    new_query: Query
    if not query_to_edit:
        print(INSTRUCTION)
        print(f"\nCurrent query: \n {PLACEHOLDER}\n")
        # print(PLACEHOLDER)
        q_input = input("QUERY: ")
        if q_input == "AND":
            query_to_edit = AndQuery([], search_field=SearchField("Author Keywords"))
            query_to_edit.children = [PLACEHOLDER]  # type: ignore
        elif q_input == "OR":
            query_to_edit = OrQuery([], search_field=SearchField("Author Keywords"))
            query_to_edit.children = [PLACEHOLDER]  # type: ignore
        else:
            raise ValueError("Invalid input")
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
                new_query = AndQuery([], search_field=SearchField("Author Keywords"))
                new_query.children = [PLACEHOLDER]  # type: ignore
            if item_input == "OR":
                new_query = OrQuery([], search_field=SearchField("Author Keywords"))
                new_query.children = [PLACEHOLDER]  # type: ignore

            query_to_edit.children[-1] = new_query
            create_query(new_query, query_to_print)
            query_to_edit.children.append(PLACEHOLDER)  # type: ignore
            continue
        if item_input == "q":
            if PLACEHOLDER in query_to_edit.children:
                query_to_edit.children.remove(PLACEHOLDER)  # type: ignore
            break

        query_to_edit.children[-1] = Query(
            value=item_input,
            operator=False,
            search_field=SearchField("Author Keywords"),
        )
        query_to_edit.children.append(PLACEHOLDER)  # type: ignore

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
    # print('To show the current state,
    # we need to call the top-level constructor and replace placeholders')
    print(q.to_string(syntax="pre_notation"))
