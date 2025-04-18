#!/usr/bin/env python3
"""Web-of-Science query parser unit tests."""
import typing

import pytest

from search_query.constants import Fields
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.exception import FatalLintingException
from search_query.parser_wos import WOSListParser
from search_query.parser_wos import WOSParser
from search_query.query import Query
from search_query.query import SearchField

# ruff: noqa: E501
# pylint: disable=too-many-lines
# flake8: noqa: E501


@pytest.mark.parametrize(
    "query_str, expected_tokens",
    [
        (
            "TI=example AND AU=John Doe",
            [
                Token(value="TI=", type=TokenTypes.FIELD, position=(0, 3)),
                Token(value="example", type=TokenTypes.SEARCH_TERM, position=(3, 10)),
                Token(value="AND", type=TokenTypes.LOGIC_OPERATOR, position=(11, 14)),
                Token(value="AU=", type=TokenTypes.FIELD, position=(15, 18)),
                Token(value="John Doe", type=TokenTypes.SEARCH_TERM, position=(18, 26)),
            ],
        ),
        (
            "TI=example example2 AND AU=John Doe",
            [
                Token(value="TI=", type=TokenTypes.FIELD, position=(0, 3)),
                Token(
                    value="example example2",
                    type=TokenTypes.SEARCH_TERM,
                    position=(3, 19),
                ),
                Token(value="AND", type=TokenTypes.LOGIC_OPERATOR, position=(20, 23)),
                Token(value="AU=", type=TokenTypes.FIELD, position=(24, 27)),
                Token(value="John Doe", type=TokenTypes.SEARCH_TERM, position=(27, 35)),
            ],
        ),
        (
            "TI=example example2 example3 AND AU=John Doe",
            [
                Token(value="TI=", type=TokenTypes.FIELD, position=(0, 3)),
                Token(
                    value="example example2 example3",
                    type=TokenTypes.SEARCH_TERM,
                    position=(3, 28),
                ),
                Token(value="AND", type=TokenTypes.LOGIC_OPERATOR, position=(29, 32)),
                Token(value="AU=", type=TokenTypes.FIELD, position=(33, 36)),
                Token(value="John Doe", type=TokenTypes.SEARCH_TERM, position=(36, 44)),
            ],
        ),
        (
            "TI=ex$mple* AND AU=John?Doe",
            [
                Token(value="TI=", type=TokenTypes.FIELD, position=(0, 3)),
                Token(value="ex$mple*", type=TokenTypes.SEARCH_TERM, position=(3, 11)),
                Token(value="AND", type=TokenTypes.LOGIC_OPERATOR, position=(12, 15)),
                Token(value="AU=", type=TokenTypes.FIELD, position=(16, 19)),
                Token(value="John?Doe", type=TokenTypes.SEARCH_TERM, position=(19, 27)),
            ],
        ),
    ],
)
def test_tokenization(query_str: str, expected_tokens: list) -> None:
    parser = WOSParser(query_str=query_str, search_field_general="", mode="")
    parser.tokenize()
    assert parser.tokens == expected_tokens, print(parser.tokens)


def test_handle_closing_parenthesis_single_child() -> None:
    """
    Test the `handle_closing_parenthesis` method with a single child.

    This test verifies that the `handle_closing_parenthesis` method correctly returns
    the single child when there is only one child in the list.
    """
    children = [Query(value="example", operator=False)]
    parser = WOSParser(query_str="", search_field_general="", mode="")
    result = parser.handle_closing_parenthesis(children, current_operator="")

    assert result == children[0]


def test_handle_closing_parenthesis_with_operator() -> None:
    """
    Test the `handle_closing_parenthesis` method with an operator.

    This test verifies that the `handle_closing_parenthesis` method correctly returns
    a Query object with the given operator and children when there is an operator.
    """
    children = [
        Query(value="example1", operator=False),
        Query(value="example2", operator=False),
    ]
    current_operator = "AND"
    parser = WOSParser(query_str="", search_field_general="", mode="")
    result = parser.handle_closing_parenthesis(children, current_operator)

    expected_result = Query(
        value=current_operator, operator=True, children=list(children)
    )

    assert result.value == expected_result.value
    assert result.operator == expected_result.operator
    assert result.children == expected_result.children


def test_handle_operator_uppercase() -> None:
    """
    Test the `handle_operator` method with an uppercase operator.

    This test verifies that the `handle_operator` method correctly handles
    an uppercase operator and returns the expected values.
    """
    token = Token(value="AND", type=TokenTypes.LOGIC_OPERATOR, position=(0, 3))
    current_operator = ""
    current_negation = False

    parser = WOSParser(query_str="", search_field_general="", mode="")
    result_operator, result_negation = parser.handle_operator(
        token, current_operator, current_negation
    )

    assert result_operator == "AND"
    assert result_negation is False


def test_handle_operator_near_with_distance() -> None:
    """
    Test the `handle_operator` method with a NEAR operator with distance.

    This test verifies that the `handle_operator` method correctly handles
    a NEAR operator with a given distance and returns the expected values.
    """
    token = Token(value="NEAR/2", type=TokenTypes.PROXIMITY_OPERATOR, position=(0, 6))
    current_operator = ""
    current_negation = False

    parser = WOSParser(query_str="", search_field_general="", mode="")
    result_operator, result_negation = parser.handle_operator(
        token, current_operator, current_negation
    )

    assert result_operator == "NEAR/2"
    assert result_negation is False


def test_handle_operator_not() -> None:
    """
    Test the `handle_operator` method with the NOT operator.

    This test verifies that the `handle_operator` method correctly handles
    the NOT operator, sets the negation flag, and changes the operator to AND.
    """
    token = Token(value="NOT", type=TokenTypes.LOGIC_OPERATOR, position=(0, 3))
    current_operator = ""
    current_negation = False

    parser = WOSParser(query_str="", search_field_general="", mode="")
    result_operator, result_negation = parser.handle_operator(
        token, current_operator, current_negation
    )

    assert result_operator == "AND"
    assert result_negation is True


def test_combine_subsequent_terms_single_term() -> None:
    """
    Test the `combine_subsequent_terms` method with a single term.

    This test verifies that the `combine_subsequent_terms` method correctly handles
    a list of tokens with a single term and does not combine it with anything.
    """
    parser = WOSParser(query_str="", search_field_general="", mode="")
    parser.tokens = [
        Token(value="example", type=TokenTypes.SEARCH_TERM, position=(0, 7))
    ]
    parser.combine_subsequent_terms()

    expected_tokens = [
        Token(value="example", type=TokenTypes.SEARCH_TERM, position=(0, 7))
    ]

    assert parser.tokens == expected_tokens


def test_combine_subsequent_terms_multiple_terms() -> None:
    """
    Test the `combine_subsequent_terms` method with multiple terms.

    This test verifies that the `combine_subsequent_terms` method correctly combines
    subsequent terms into a single token.
    """
    parser = WOSParser(query_str="", search_field_general="", mode="")
    parser.tokens = [
        Token(value="example", type=TokenTypes.SEARCH_TERM, position=(0, 7)),
        Token(value="example2", type=TokenTypes.SEARCH_TERM, position=(8, 16)),
    ]
    parser.combine_subsequent_terms()

    expected_tokens = [
        Token(value="example example2", type=TokenTypes.SEARCH_TERM, position=(0, 16))
    ]

    assert parser.tokens == expected_tokens


def test_combine_subsequent_terms_with_operators() -> None:
    """
    Test the `combine_subsequent_terms` method with terms and operators.

    This test verifies that the `combine_subsequent_terms` method correctly combines
    subsequent terms into a single token and does not combine terms with operators.
    """
    parser = WOSParser(query_str="", search_field_general="", mode="")
    parser.tokens = [
        Token(value="example", type=TokenTypes.SEARCH_TERM, position=(0, 7)),
        Token(value="AND", type=TokenTypes.LOGIC_OPERATOR, position=(8, 11)),
        Token(value="example2", type=TokenTypes.SEARCH_TERM, position=(12, 20)),
    ]
    parser.combine_subsequent_terms()

    expected_tokens = [
        Token(value="example", type=TokenTypes.SEARCH_TERM, position=(0, 7)),
        Token(value="AND", type=TokenTypes.LOGIC_OPERATOR, position=(8, 11)),
        Token(value="example2", type=TokenTypes.SEARCH_TERM, position=(12, 20)),
    ]

    assert parser.tokens == expected_tokens


def test_combine_subsequent_terms_with_special_characters() -> None:
    """
    Test the `combine_subsequent_terms` method with terms containing special characters.

    This test verifies that the `combine_subsequent_terms` method correctly combines
    subsequent terms containing special characters into a single token.
    """
    parser = WOSParser(query_str="", search_field_general="", mode="")
    parser.tokens = [
        Token(value="ex$mple", type=TokenTypes.SEARCH_TERM, position=(0, 7)),
        Token(value="example2", type=TokenTypes.SEARCH_TERM, position=(8, 16)),
    ]
    parser.combine_subsequent_terms()

    expected_tokens = [
        Token(value="ex$mple example2", type=TokenTypes.SEARCH_TERM, position=(0, 16))
    ]

    assert parser.tokens == expected_tokens


def test_combine_subsequent_terms_with_mixed_case() -> None:
    """
    Test the `combine_subsequent_terms` method with terms in mixed case.

    This test verifies that the `combine_subsequent_terms` method correctly combines
    subsequent terms in mixed case into a single token.
    """
    parser = WOSParser(query_str="", search_field_general="", mode="")
    parser.tokens = [
        Token(value="Example", type=TokenTypes.SEARCH_TERM, position=(0, 7)),
        Token(value="example2", type=TokenTypes.SEARCH_TERM, position=(8, 16)),
    ]
    parser.combine_subsequent_terms()

    expected_tokens = [
        Token(value="Example example2", type=TokenTypes.SEARCH_TERM, position=(0, 16))
    ]

    assert parser.tokens == expected_tokens


def test_append_children_with_same_operator() -> None:
    """
    Test the `append_children` method with the same operator.

    This test verifies that the `append_children` method correctly appends
    the children of the sub expression to the last child when the current operator
    is the same as the last child and the sub expression value.
    """
    children = [
        Query(
            value="AND",
            operator=True,
            children=[Query(value="example1", operator=False)],
        )
    ]
    sub_expr = Query(
        value="AND",
        operator=True,
        children=[Query(value="example2", operator=False)],
    )
    current_operator = "AND"

    parser = WOSParser(query_str="", search_field_general="", mode="")
    result = parser.append_children(children, sub_expr, current_operator)

    expected_result = [
        Query(
            value="AND",
            operator=True,
            children=[
                Query(value="example1", operator=False),
                Query(value="example2", operator=False),
            ],
        )
    ]

    assert result[0].value == expected_result[0].value
    assert result[0].operator == expected_result[0].operator
    assert result[0].children[0].value == expected_result[0].children[0].value
    assert result[0].children[0].operator == expected_result[0].children[0].operator
    assert result[0].children[1].value == expected_result[0].children[1].value
    assert result[0].children[1].operator == expected_result[0].children[1].operator


def test_append_children_with_operator_and_term() -> None:
    """
    Test the `append_children` method with an operator and a term.

    This test verifies that the `append_children` method correctly appends
    the sub expression to the last child when the last child is an operator
    and the sub expression is a term.
    """
    children = [
        Query(
            value="AND",
            operator=True,
            children=[Query(value="example1", operator=False)],
        )
    ]
    sub_expr = Query(value="example2", operator=False)
    current_operator = "AND"

    parser = WOSParser(query_str="", search_field_general="", mode="")
    result = parser.append_children(children, sub_expr, current_operator)

    expected_result = [
        Query(
            value="AND",
            operator=True,
            children=[
                Query(value="example1", operator=False),
                Query(value="example2", operator=False),
            ],
        )
    ]

    assert result[0].value == expected_result[0].value
    assert result[0].operator == expected_result[0].operator
    assert result[0].children[0].value == expected_result[0].children[0].value
    assert result[0].children[0].operator == expected_result[0].children[0].operator
    assert result[0].children[1].value == expected_result[0].children[1].value
    assert result[0].children[1].operator == expected_result[0].children[1].operator


def test_append_children_with_different_operator() -> None:
    """
    Test the `append_children` method with a different operator.

    This test verifies that the `append_children` method correctly appends
    the sub expression to the list of children when the current operator
    is different from the last child.
    """
    children = [
        Query(
            value="AND",
            operator=True,
            children=[Query(value="example1", operator=False)],
        )
    ]
    sub_expr = Query(
        value="OR",
        operator=True,
        children=[Query(value="example2", operator=False)],
    )
    current_operator = "OR"

    parser = WOSParser(query_str="", search_field_general="", mode="")
    result = parser.append_children(children, sub_expr, current_operator)

    expected_result = [
        Query(
            value="AND",
            operator=True,
            children=[Query(value="example1", operator=False)],
        ),
        Query(value="example2", operator=False),
    ]

    assert result[0].value == expected_result[0].value
    assert result[0].operator == expected_result[0].operator
    assert result[0].children[0].value == expected_result[0].children[0].value
    assert result[0].children[0].operator == expected_result[0].children[0].operator
    assert result[1].value == expected_result[1].value
    assert result[1].operator == expected_result[1].operator


def test_append_children_with_empty_children() -> None:
    """
    Test the `append_children` method with empty children.

    This test verifies that the `append_children` method correctly appends
    the sub expression to the list of children when the children list is empty.
    """
    children: typing.List[Query] = []
    sub_expr = Query(value="example1", operator=False)
    current_operator = "AND"

    parser = WOSParser(query_str="", search_field_general="", mode="")
    result = parser.append_children(children, sub_expr, current_operator)

    expected_result = [Query(value="example1", operator=False)]

    assert result[0].value == expected_result[0].value
    assert result[0].operator == expected_result[0].operator


def test_append_children_with_operator_and_sub_expr_operator() -> None:
    """
    Test the `append_children` method with an operator and a sub expression operator.

    This test verifies that the `append_children` method correctly appends
    the sub expression to the last child when the last child is an operator
    and the sub expression is also an operator.
    """
    children = [
        Query(
            value="AND",
            operator=True,
            children=[Query(value="example1", operator=False)],
        )
    ]
    sub_expr = Query(
        value="AND",
        operator=True,
        children=[Query(value="example2", operator=False)],
    )
    current_operator = "AND"

    parser = WOSParser(query_str="", search_field_general="", mode="")
    result = parser.append_children(children, sub_expr, current_operator)

    expected_result = [
        Query(
            value="AND",
            operator=True,
            children=[
                Query(value="example1", operator=False),
                Query(value="example2", operator=False),
            ],
        )
    ]

    assert result[0].value == expected_result[0].value
    assert result[0].operator == expected_result[0].operator
    assert result[0].children[0].value == expected_result[0].children[0].value
    assert result[0].children[0].operator == expected_result[0].children[0].operator
    assert result[0].children[1].value == expected_result[0].children[1].value
    assert result[0].children[1].operator == expected_result[0].children[1].operator


def test_handle_year_search_valid_year_span() -> None:
    """
    Test the `handle_year_search` method with a valid year span.

    This test verifies that the `handle_year_search` method correctly handles
    a valid year span and adds the year search field to the list of children.
    """
    token = Token(value="2015-2019", type=TokenTypes.SEARCH_TERM, position=(0, 9))
    children: typing.List[Query] = []
    current_operator = "AND"

    parser = WOSParser(query_str="", search_field_general="", mode="")
    result = parser.handle_year_search(token, children, current_operator)

    expected_result = [
        Query(
            value="AND",
            operator=True,
            children=[
                Query(
                    value=token.value,
                    operator=False,
                    search_field=SearchField(
                        value=Fields.YEAR, position=token.position
                    ),
                    position=token.position,
                )
            ],
        )
    ]

    assert result[0].value == expected_result[0].value
    assert result[0].operator == expected_result[0].operator
    assert (
        result[0].children[0].search_field.value  # type: ignore
        == expected_result[0].children[0].search_field.value  # type: ignore
    )
    assert result[0].children[0].position == expected_result[0].children[0].position


def test_handle_year_search_single_year() -> None:
    """
    Test the `handle_year_search` method with a single year.

    This test verifies that the `handle_year_search` method correctly handles
    a single year and adds the year search field to the list of children.
    """
    token = Token(value="2015", type=TokenTypes.SEARCH_TERM, position=(0, 4))
    children: typing.List[Query] = []
    current_operator = "AND"

    parser = WOSParser(query_str="", search_field_general="", mode="")
    result = parser.handle_year_search(token, children, current_operator)

    expected_result = [
        Query(
            value="AND",
            operator=True,
            children=[
                Query(
                    value=token.value,
                    operator=False,
                    search_field=SearchField(
                        value=Fields.YEAR, position=token.position
                    ),
                    position=token.position,
                )
            ],
        )
    ]

    assert result[0].children[0].value == expected_result[0].children[0].value
    assert result[0].children[0].operator == expected_result[0].children[0].operator
    assert (
        result[0].children[0].search_field.value  # type: ignore
        == expected_result[0].children[0].search_field.value  # type: ignore
    )
    assert result[0].children[0].position == expected_result[0].children[0].position


def test_add_term_node_without_current_operator() -> None:
    """
    Test the `add_term_node` method without a current operator.

    This test verifies that the `add_term_node` method correctly adds
    a term node to the list of children when there is no current operator.
    """
    tokens = [Token(value="example", type=TokenTypes.SEARCH_TERM, position=(0, 7))]
    parser = WOSParser(query_str="", search_field_general="", mode="")
    parser.tokens = tokens
    index = 0
    value = "example"
    operator = False
    search_field = SearchField(value="TI=", position=(0, 3))
    position = (0, 7)
    current_operator = ""
    children: typing.List[Query] = []

    result = parser.add_term_node(
        index=index,
        value=value,
        operator=operator,
        search_field=search_field,
        position=position,
        current_operator=current_operator,
        children=children,
    )
    expected_result = [
        Query(
            value=value,
            operator=operator,
            search_field=search_field,
            position=position,
        )
    ]
    assert result[0].value == expected_result[0].value
    assert result[0].operator == expected_result[0].operator
    assert result[0].search_field.value == expected_result[0].search_field.value  # type: ignore
    assert result[0].position == expected_result[0].position


def test_add_term_node_with_current_operator() -> None:
    """
    Test the `add_term_node` method with a current operator.

    This test verifies that the `add_term_node` method correctly adds
    a term node to the list of children when there is a current operator.
    """
    tokens = [Token(value="example", type=TokenTypes.SEARCH_TERM, position=(0, 7))]
    parser = WOSParser(query_str="", search_field_general="", mode="")
    parser.tokens = tokens
    index = 0
    value = "example"
    operator = False
    search_field = SearchField(value="TI=", position=(0, 3))
    position = (0, 7)
    current_operator = "AND"
    children: typing.List[Query] = []

    result = parser.add_term_node(
        index=index,
        value=value,
        operator=operator,
        search_field=search_field,
        position=position,
        current_operator=current_operator,
        children=children,
    )
    expected_result = [
        Query(
            value=current_operator,
            operator=True,
            children=[
                Query(
                    value=value,
                    operator=operator,
                    search_field=search_field,
                    position=position,
                )
            ],
        )
    ]
    assert result[0].value == expected_result[0].value
    assert result[0].operator == expected_result[0].operator
    assert result[0].children[0].value == expected_result[0].children[0].value
    assert result[0].children[0].operator == expected_result[0].children[0].operator
    assert (
        result[0].children[0].search_field.value  # type: ignore
        == expected_result[0].children[0].search_field.value  # type: ignore
    )
    assert result[0].children[0].position == expected_result[0].children[0].position


def test_add_term_node_with_near_operator() -> None:
    """
    Test the `add_term_node` method with a NEAR operator.

    This test verifies that the `add_term_node` method correctly adds
    a term node to the list of children when there is a NEAR operator.
    """
    tokens = [
        Token(value="example", type=TokenTypes.SEARCH_TERM, position=(0, 7)),
        Token(value="example2", type=TokenTypes.SEARCH_TERM, position=(8, 16)),
        Token(value="example3", type=TokenTypes.SEARCH_TERM, position=(17, 25)),
    ]
    parser = WOSParser(query_str="", search_field_general="", mode="")
    parser.tokens = tokens
    index = 1
    value = "example2"
    operator = False
    search_field = SearchField(value="TI=", position=(0, 3))
    position = (8, 16)
    current_operator = "NEAR/5"
    children = [
        Query(
            value="NEAR",
            operator=True,
            children=[
                Query(
                    value="example",
                    operator=False,
                    search_field=search_field,
                    position=(0, 7),
                ),
                Query(
                    value="example2",
                    operator=False,
                    search_field=search_field,
                    position=(8, 16),
                ),
            ],
            distance=5,
        )
    ]

    result = parser.add_term_node(
        index=index,
        value=value,
        operator=operator,
        search_field=search_field,
        position=position,
        current_operator=current_operator,
        children=children,
    )
    expected_result = [
        Query(
            value="AND",
            operator=True,
            children=[
                Query(
                    value="NEAR",
                    operator=True,
                    children=[
                        Query(
                            value="example",
                            operator=False,
                            search_field=search_field,
                            position=(0, 7),
                        ),
                        Query(
                            value="example2",
                            operator=False,
                            search_field=search_field,
                            position=(8, 16),
                        ),
                    ],
                    distance=5,
                ),
                Query(
                    value="example2",
                    operator=False,
                    search_field=search_field,
                    position=(8, 16),
                ),
                Query(
                    value="example3",
                    operator=False,
                    search_field=search_field,
                    position=(17, 25),
                ),
            ],
        )
    ]
    assert result[0].value == expected_result[0].value
    assert result[0].operator == expected_result[0].operator
    assert result[0].children[0].value == expected_result[0].children[0].value
    assert result[0].children[0].operator == expected_result[0].children[0].operator
    assert (
        result[0].children[0].children[0].value
        == expected_result[0].children[0].children[0].value
    )
    assert (
        result[0].children[0].children[0].operator
        == expected_result[0].children[0].children[0].operator
    )
    assert (
        result[0].children[0].children[1].value
        == expected_result[0].children[0].children[1].value
    )
    assert (
        result[0].children[0].children[1].operator
        == expected_result[0].children[0].children[1].operator
    )


def test_add_term_node_with_existing_children() -> None:
    """
    Test the `add_term_node` method with existing children.

    This test verifies that the `add_term_node` method correctly adds
    a term node to the existing list of children.
    """
    tokens = [Token(value="example", type=TokenTypes.SEARCH_TERM, position=(0, 7))]
    parser = WOSParser(query_str="", search_field_general="", mode="")
    parser.tokens = tokens
    index = 0
    value = "example"
    operator = False
    search_field = SearchField(value="TI=", position=(0, 3))
    position = (0, 7)
    current_operator = ""
    children = [
        Query(
            value="existing",
            operator=False,
            search_field=search_field,
            position=(0, 8),
        )
    ]

    result = parser.add_term_node(
        index=index,
        value=value,
        operator=operator,
        search_field=search_field,
        position=position,
        current_operator=current_operator,
        children=children,
    )
    expected_result = [
        Query(
            value="existing",
            operator=False,
            search_field=search_field,
            position=(0, 8),
        ),
        Query(
            value=value,
            operator=operator,
            search_field=search_field,
            position=position,
        ),
    ]
    assert result[0].value == expected_result[0].value
    assert result[0].operator == expected_result[0].operator
    assert result[0].search_field.value == expected_result[0].search_field.value  # type: ignore
    assert result[0].position == expected_result[0].position
    assert result[1].value == expected_result[1].value
    assert result[1].operator == expected_result[1].operator
    assert result[1].search_field.value == expected_result[1].search_field.value  # type: ignore
    assert result[1].position == expected_result[1].position


def test_add_term_node_with_current_negation() -> None:
    """
    Test the `add_term_node` method with current negation.

    This test verifies that the `add_term_node` method correctly adds
    a term node to the list of children when there is a current negation.
    """
    tokens = [Token(value="example", type=TokenTypes.SEARCH_TERM, position=(0, 7))]
    parser = WOSParser(query_str="", search_field_general="", mode="")
    parser.tokens = tokens
    index = 0
    value = "example"
    operator = False
    search_field = SearchField(value="TI=", position=(0, 3))
    position = (0, 7)
    current_operator = "AND"
    children: typing.List[Query] = []
    current_negation = True

    result = parser.add_term_node(
        index=index,
        value=value,
        operator=operator,
        search_field=search_field,
        position=position,
        current_operator=current_operator,
        children=children,
        current_negation=current_negation,
    )
    expected_result = [
        Query(
            value=current_operator,
            operator=True,
            children=[
                Query(
                    value=value,
                    operator=operator,
                    search_field=search_field,
                    position=position,
                )
            ],
        )
    ]
    assert result[0].value == expected_result[0].value
    assert result[0].operator == expected_result[0].operator
    assert result[0].children[0].value == expected_result[0].children[0].value
    assert result[0].children[0].operator == expected_result[0].children[0].operator
    assert (
        result[0].children[0].search_field.value  # type: ignore
        == expected_result[0].children[0].search_field.value  # type: ignore
    )
    assert result[0].children[0].position == expected_result[0].children[0].position


def test_check_search_fields_title() -> None:
    """
    Test the `check_search_fields` method with title search fields.

    This test verifies that the `check_search_fields` method correctly translates
    title search fields into the base search field "TI=".
    """
    title_fields = ["TI=", "Title", "ti=", "title=", "ti", "title", "TI", "TITLE"]
    parser = WOSParser(query_str="", search_field_general="", mode="")

    for field in title_fields:
        result = parser._map_default_field(field)
        assert result == "ti"


def test_check_search_fields_abstract() -> None:
    """
    Test the `check_search_fields` method with abstract search fields.

    This test verifies that the `check_search_fields` method correctly translates
    abstract search fields into the base search field "AB=".
    """
    abstract_fields = [
        "AB=",
        "ab=",
        "abstract=",
        # "Abstract", "ab", "abstract", "AB", "ABSTRACT"
    ]
    parser = WOSParser(query_str="", search_field_general="", mode="")

    for field in abstract_fields:
        result = parser._map_default_field(field)
        assert result == "ab"


def test_check_search_fields_author() -> None:
    """
    Test the `check_search_fields` method with author search fields.

    This test verifies that the `check_search_fields` method correctly translates
    author search fields into the base search field "AU=".
    """
    author_fields = [
        "AU=",
        "Author",
        "au=",
        "author=",
        # "au", "author", "AU", "AUTHOR"
    ]
    parser = WOSParser(query_str="", search_field_general="", mode="")

    for field in author_fields:
        result = parser._map_default_field(field)
        assert result == "au"


def test_check_search_fields_topic() -> None:
    """
    Test the `check_search_fields` method with topic search fields.

    This test verifies that the `check_search_fields` method correctly translates
    topic search fields into the base search field "TS=".
    """
    topic_fields = [
        "TS=",
        "ts=",
        "topic=",
        # "Topic", "ts", "topic", "TS", "TOPIC", "Topic Search", "Topic TS"
    ]
    parser = WOSParser(query_str="", search_field_general="", mode="")

    for field in topic_fields:
        result = parser._map_default_field(field)
        assert result == "ts"


def test_check_search_fields_language() -> None:
    """
    Test the `check_search_fields` method with language search fields.

    This test verifies that the `check_search_fields` method correctly translates
    language search fields into the base search field "LA=".
    """
    language_fields = [
        "LA=",
        "la=",
        "language=",
        # "Languages", "la", "language", "LA", "LANGUAGE"
    ]
    parser = WOSParser(query_str="", search_field_general="", mode="")

    for field in language_fields:
        result = parser._map_default_field(field)
        assert result == "la"


def test_check_search_fields_year() -> None:
    """
    Test the `check_search_fields` method with year search fields.

    This test verifies that the `check_search_fields` method correctly translates
    year search fields into the base search field "PY=".
    """
    year_fields = [
        "PY=",
        "py=",
        "py",
        # "Publication Year",
        # "publication year",
        # "PY",
        # "PUBLICATION YEAR",
    ]
    parser = WOSParser(query_str="", search_field_general="", mode="")

    for field in year_fields:
        result = parser._map_default_field(field)
        assert result == "py"


def test_check_search_fields_misc() -> None:
    """
    Test the `check_search_fields` method with unknown search fields.
    """
    misc_fields = ["INVALID", "123", "random", "field"]
    parser = WOSParser(query_str="", search_field_general="", mode="")

    for field in misc_fields:
        result = parser._map_default_field(field)
        assert result == field


def test_query_parsing_1() -> None:
    parser = WOSParser(
        query_str="TI=example AND AU=John Doe", search_field_general="", mode=""
    )
    query = parser.parse()

    # Assertions using standard assert statement
    assert query.value == "AND"
    assert query.operator is True
    assert len(query.children) == 2
    assert query.children[0].value == "example"
    assert query.children[0].operator is False
    assert query.children[1].value == "John Doe"
    assert query.children[1].search_field.value == "au"  # type: ignore
    assert query.children[1].operator is False


def test_query_parsing_2() -> None:
    parser = WOSParser(
        query_str="TI=example AND (AU=John Doe OR AU=John Wayne)",
        search_field_general="",
        mode="",
    )
    query = parser.parse()

    # Assertions using standard assert statement
    assert query.value == "AND"
    assert query.operator is True
    assert len(query.children) == 2
    assert query.children[0].value == "example"
    assert query.children[0].operator is False
    assert query.children[1].value == "OR"
    assert query.children[1].children[1].value == "John Wayne"
    assert query.children[1].children[1].search_field.value == "au"  # type: ignore


def test_query_parsing_basic_vs_advanced() -> None:
    # Basic search
    parser = WOSParser(
        query_str="digital AND online", search_field_general="ALL=", mode=""
    )
    parser.parse()
    assert len(parser.linter_messages) == 0

    # Search field could be nested
    parser = WOSParser(
        query_str="(TI=digital AND AB=online)", search_field_general="ALL=", mode=""
    )
    parser.parse()
    assert len(parser.linter_messages) == 0

    # Advanced search
    parser = WOSParser(
        query_str="ALL=(digital AND online)", search_field_general="", mode=""
    )
    parser.parse()
    assert len(parser.linter_messages) == 0

    parser = WOSParser(
        query_str="(ALL=digital AND ALL=online)", search_field_general="", mode=""
    )
    parser.parse()
    assert len(parser.linter_messages) == 0

    # ERROR: Basic search without search_field_general
    parser = WOSParser(query_str="digital AND online", search_field_general="", mode="")
    parser.parse()
    assert len(parser.linter_messages) == 1

    # ERROR: Advanced search with search_field_general
    parser = WOSParser(
        query_str="ALL=(digital AND online)", search_field_general="ALL=", mode=""
    )
    parser.parse()
    assert len(parser.linter_messages) == 1

    # ERROR: Advanced search with search_field_general
    parser = WOSParser(
        query_str="TI=(digital AND online)", search_field_general="ALL=", mode=""
    )
    parser.parse()
    assert len(parser.linter_messages) == 1
    assert parser.linter_messages[0] == {
        "code": "E0002",
        "label": "search-field-contradiction",
        "message": "Contradictory search fields specified",
        "is_fatal": False,
        "details": "",
        "position": (0, 3),
    }


def test_query_in_quotes() -> None:
    parser = WOSParser(
        query_str='"TI=(digital AND online)"', search_field_general="", mode=""
    )
    parser.parse()

    # Assertions using standard assert statement
    assert len(parser.linter_messages) == 1
    assert parser.tokens[0].value == "TI="


def test_artificial_parentheses() -> None:
    parser = WOSParser(
        query_str="remote OR online AND work", search_field_general="ALL=", mode=""
    )
    query = parser.parse()

    # Assertions using standard assert statement
    assert query.value == "OR"
    assert query.children[0].value == "remote"
    assert query.children[1].value == "AND"
    assert query.children[1].children[0].value == "online"
    assert query.children[1].children[1].value == "work"

    # Check if linter messages contain one entry
    assert len(parser.linter_messages) == 1
    assert parser.linter_messages[0] == {
        "code": "W0007",
        "label": "implicit-precedence",
        "message": "Operator changed at the same level (currently relying on implicit operator precedence, explicit parentheses are recommended)",
        "position": (7, 9),
        "is_fatal": False,
        "details": "",
    }


# Test case 1
def test_list_parser_case_1() -> None:
    query_list = '1. TS=("Peer leader*" OR "Shared leader*" OR "Distributed leader*" OR \u201cDistributive leader*\u201d OR \u201cCollaborate leader*\u201d OR "Collaborative leader*" OR "Team leader*" OR "Peer-led" OR "Athlete leader*" OR "Team captain*" OR "Peer mentor*" OR "Peer Coach")\n2. TS=("acrobatics" OR "acrobat" OR "acrobats" OR "acrobatic" OR "aikido" OR "aikidoists" OR "anetso" OR "archer" OR "archers" OR "archery" OR "airsoft" OR "angling" OR "aquatics" OR "aerobics" OR "athlete" OR "athletes" OR "athletic" OR "athletics" OR "ball game*" OR "ballooning" OR "basque pelota" OR "behcup" OR "bicycling" OR "BMX" OR "bodyboarding" OR "boule lyonnaise" OR "bridge" OR "badminton" OR "balle au tamis" OR "baseball" OR "basketball" OR "battle ball" OR "battleball" OR "biathlon" OR "billiards" OR "boating" OR "bobsledding" OR "bobsled" OR "bobsledder" OR "bobsledders" OR "bobsleigh" OR "boccia" OR "bocce" OR "buzkashi" OR "bodybuilding" OR "bodybuilder" OR "bodybuilders" OR "bowling" OR "bowler" OR "bowlers" OR "bowls" OR "boxing" OR "boxer" OR "boxers" OR "bandy" OR "breaking" OR "breakdanc*" OR "broomball" OR "budo" OR "bullfighting" OR "bullfights" OR "bullfight" OR "bullfighter" OR "bullfighters" OR "mountain biking" OR "mountain bike" OR "carom billiards" OR "camogie" OR "canoe slalom" OR "canoeing" OR "canoeist" OR "canoeists" OR "canoe" OR "climbing" OR "coasting" OR "cricket" OR "croquet" OR "crossfit" OR "curling" OR "curlers" OR "curler" OR "cyclist" OR "cyclists" OR "combat*" OR "casting" OR "cheerleading" OR "cheer" OR "cheerleader*" OR "chess" OR "charrerias" OR "cycling" OR "dancesport" OR "darts" OR "decathlon" OR "draughts" OR "dancing" OR "dance" OR "dancers" OR "dancer" OR "diving" OR "dodgeball" OR "e-sport" OR "dressage" OR "endurance" OR "equestrian" OR "eventing" OR "eskrima" OR "escrima" OR "fencer" OR "fencing" OR "fencers" OR "fishing" OR "finswimming" OR "fistball" OR "floorball" OR "flying disc" OR "foosball" OR "futsal" OR "flickerball" OR "football" OR "frisbee" OR "gliding" OR "go" OR "gongfu" OR "gong fu" OR "goalball" OR "golf" OR "golfer" OR "golfers" OR "gymnast" OR "gymnasts" OR "gymnastics" OR "gymnastic" OR "gymkhanas" OR "half rubber" OR "highland games" OR "hap ki do" OR "halfrubber" OR "handball" OR "handballers" OR "handballer" OR "hapkido" OR "hiking" OR "hockey" OR "hsing-I" OR "hurling" OR "Hwa rang do" OR "hwarangdo" OR "horsemanship" OR "horseshoes" OR "orienteer" OR "orienteers" OR "orienteering" OR "iaido" OR "iceboating" OR "icestock" OR "intercrosse" OR "jousting" OR "jai alai" OR "jeet kune do" OR "jianzi" OR "jiu-jitsu" OR "jujutsu" OR "ju-jitsu" OR "kung fu" OR "kungfu" OR "kenpo" OR "judo" OR "judoka" OR "judoists" OR "judoist" OR "jump" OR "jumping" OR "jumper" OR "jian zi" OR "kabaddi" OR "kajukenbo" OR "karate" OR "karateists" OR "karateist" OR "karateka" OR "kayaking" OR "kendo" OR "kenjutsu" OR "kickball" OR "kickbox*" OR "kneeboarding" OR "krav maga" OR "kuk sool won" OR "kun-tao" OR "kuntao" OR "kyudo" OR "korfball" OR "lacrosse" OR "life saving" OR "lapta" OR "lawn tempest" OR "bowling" OR "bowls" OR "logrolling" OR "luge" OR "marathon" OR "marathons" OR "marathoning" OR "martial art" OR "martial arts" OR "martial artist" OR "martial artists" OR "motorsports" OR "mountainboarding" OR "mountain boarding" OR "mountaineer" OR "mountaineering" OR "mountaineers" OR "muay thai" OR "mallakhamb" OR "motorcross" OR "modern arnis" OR "naginata do" OR "netball" OR "ninepins" OR "nine-pins" OR "nordic combined" OR "nunchaku" OR "olympic*" OR "pes\u00e4pallo" OR "pitch and putt" OR "pool" OR "pato" OR "paddleball" OR "paddleboarding" OR "pankration" OR "pancratium" OR "parachuting" OR "paragliding" OR "paramotoring" OR "paraski" OR "paraskiing" OR "paraskier" OR "paraskier" OR "parakour" OR "pelota" OR "pencak silat" OR "pentathlon" OR "p\u00e9tanque" OR "petanque" OR "pickleball" OR "pilota" OR "pole bending" OR "pole vault" OR "polo" OR "polocrosse" OR "powerlifting" OR "player*" OR "powerboating" OR "pegging" OR "parathletic" OR "parathletics" OR "parasport*" OR "paraathletes" OR "paraathlete" OR "pushball" OR "push ball" OR "quidditch" OR "races" OR "race" OR "racing" OR "racewalking" OR "racewalker" OR "racewalkers" OR "rackets" OR "racketlon" OR "racquetball" OR "racquet" OR "racquets" OR "rafting" OR "regattas" OR "riding" OR "ringette" OR "rock-it-ball" OR "rogaining" OR "rock climbing" OR "roll ball" OR "roller derby" OR "roping" OR "rodeos" OR "rodeo" OR "riding" OR "rider" OR "riders" OR "rounders" OR "rowing" OR "rower" OR "rowers" OR "rug ball" OR "running" OR "runner" OR "runners" OR "rugby" OR "sailing" OR "san shou" OR "sepaktakraw" OR "sepak takraw" OR "san-jitsu" OR "savate" OR "shinty" OR "shishimai" OR "shooting" OR "singlestick" OR "single stick" OR "skateboarding" OR "skateboarder" OR "skateboarders" OR "skater" OR "skaters" OR "skating" OR "skipping" OR "racket game*" OR "rollerskating" OR "skelton" OR "skibobbing" OR "ski" OR "skiing" OR "skier" OR "skiers" OR "skydive" OR "skydiving" OR "skydivers" OR "skydiver" OR "skysurfing" OR "sledding" OR "sledging" OR "sled dog" OR "sleddog" OR "snooker" OR "sleighing" OR "snowboarder" OR "snowboarding" OR "snowboarders" OR "snowshoeing" OR "soccer" OR "softball" OR "spear fighting" OR "speed-a-way" OR "speedball" OR "sprint" OR "sprinting" OR "sprints" OR "squash" OR "stick fighting" OR "stickball" OR "stoolball" OR "stunt flying" OR "sumo" OR "surfing" OR "surfer" OR "surfers" OR "swimnastics" OR "swimming" OR "snowmobiling" OR "swim" OR "swimmer" OR "swimmers" OR "shot-put" OR "shot-putters" OR "shot-putter" OR "sport" OR "sports" OR "tae kwon do" OR "taekwondo" OR "taekgyeon" OR "taekkyeon" OR "taekkyon" OR "taekyun" OR "tang soo do" OR "tchoukball" OR "tennis" OR "tetherball" OR "throwing" OR "thrower" OR "throwers" OR "tai ji" OR "tai chi" OR "taiji" OR "t ai chi" OR "throwball" OR "tug of war" OR "tobogganing" OR "track and field" OR "track & field" OR "trampoline" OR "trampolining" OR "trampolinists" OR "trampolinist" OR "trapball" OR "trapshooting" OR "triathlon" OR "triathlete" OR "triathletes" OR "tubing" OR "tumbling" OR "vaulting" OR "volleyball" OR "wakeboarding" OR "wallyball" OR "weightlifting" OR "weightlifter" OR "weightlifters" OR "wiffle ball" OR "windsurfing" OR "windsurfer" OR "windsurfers" OR "walking" OR "wingwalking" OR "woodchopping" OR "wood chopping" OR "woodball" OR "wushu" OR "weight lifter" OR "weight lift" OR "weight lifters" OR "wrestling" OR "wrestler" OR "wrestlers" OR "vovinam" OR "vx" OR "yoga")\n3. #1 AND #2\n'

    list_parser = WOSListParser(query_list=query_list, search_field_general="", mode="")
    list_parser.parse()


# Test case 2
def test_list_parser_case_2() -> None:
    query_list = '1. TS=("Peer leader*" OR "Shared leader*")\n2. TS=("acrobatics" OR "acrobat" OR "acrobats")'

    list_parser = WOSListParser(query_list=query_list, search_field_general="", mode="")
    try:
        list_parser.parse()
    except FatalLintingException:
        pass
    assert list_parser.linter_messages[WOSListParser.GENERAL_ERROR_POSITION][0] == {
        "code": "F3001",
        "is_fatal": True,
        "label": "missing-root-node",
        "message": "List format query without root node (typically containing operators)",
        "position": (-1, -1),
        "details": "",
    }


# Test case 3
def test_list_parser_case_3() -> None:
    query_list = '1. TS=("Peer leader*" OR "Shared leader*")\n2. TS=("acrobatics" OR "acrobat" OR "acrobats")\n3. #1 AND not_a_ref_to_term_node\n'

    list_parser = WOSListParser(query_list=query_list, search_field_general="", mode="")
    try:
        list_parser.parse()
    except FatalLintingException:
        pass
    assert list_parser.linter_messages[WOSListParser.GENERAL_ERROR_POSITION][0] == {
        "code": "F1004",
        "is_fatal": True,
        "label": "invalid-token-sequence",
        "message": "The sequence of tokens is invalid.",
        "position": (3, 6),
        "details": "Last token of query item 3 must be a list item.",
    }


# Test case 4
def test_list_parser_case_4() -> None:
    query_list = '1. TS=("Peer leader*" OR "Shared leader*")\n2. TS=("acrobatics" OR "acrobat" OR "acrobats")\n3. #1 AND #5\n'

    list_parser = WOSListParser(query_list=query_list, search_field_general="", mode="")
    try:
        list_parser.parse()
    except FatalLintingException:
        pass
    assert list_parser.linter_messages[2][0] == {
        "code": "F3003",
        "is_fatal": True,
        "label": "invalid-list-reference",
        "message": "Invalid list reference in list query (not found)",
        "position": (7, 9),
        "details": "List reference #5 not found.",
    }
