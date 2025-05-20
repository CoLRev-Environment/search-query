#!/usr/bin/env python3
"""Web-of-Science unit tests for internals of query parser."""
import typing

from search_query.constants import Fields
from search_query.constants import PLATFORM
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.query import Query
from search_query.query import SearchField
from search_query.wos.constants import syntax_str_to_generic_search_field_set
from search_query.wos.parser import WOSParser

# ruff: noqa: E501
# pylint: disable=too-many-lines
# flake8: noqa: E501


def test_handle_closing_parenthesis_single_child() -> None:
    """
    Test the `handle_closing_parenthesis` method with a single child.

    This test verifies that the `handle_closing_parenthesis` method correctly returns
    the single child when there is only one child in the list.
    """
    children = [Query(value="example", operator=False, platform=PLATFORM.WOS.value)]
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
        Query(value="example1", operator=False, platform=PLATFORM.WOS.value),
        Query(value="example2", operator=False, platform=PLATFORM.WOS.value),
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
            platform=PLATFORM.WOS.value,
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
                    platform=PLATFORM.WOS.value,
                )
            ],
            platform=PLATFORM.WOS.value,
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
                    platform=PLATFORM.WOS.value,
                ),
                Query(
                    value="example2",
                    operator=False,
                    search_field=search_field,
                    position=(8, 16),
                    platform=PLATFORM.WOS.value,
                ),
            ],
            distance=5,
            platform=PLATFORM.WOS.value,
        )
    ]

    result = parser.add_term_node(
        index=index,
        value=value,
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
                            platform=PLATFORM.WOS.value,
                        ),
                        Query(
                            value="example2",
                            operator=False,
                            search_field=search_field,
                            position=(8, 16),
                            platform=PLATFORM.WOS.value,
                        ),
                    ],
                    distance=5,
                    platform=PLATFORM.WOS.value,
                ),
                Query(
                    value="example2",
                    operator=False,
                    search_field=search_field,
                    position=(8, 16),
                    platform=PLATFORM.WOS.value,
                ),
                Query(
                    value="example3",
                    operator=False,
                    search_field=search_field,
                    position=(17, 25),
                    platform=PLATFORM.WOS.value,
                ),
            ],
            platform=PLATFORM.WOS.value,
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
            platform=PLATFORM.WOS.value,
        )
    ]

    result = parser.add_term_node(
        index=index,
        value=value,
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
            platform=PLATFORM.WOS.value,
        ),
        Query(
            value=value,
            operator=operator,
            search_field=search_field,
            position=position,
            platform=PLATFORM.WOS.value,
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
                    platform=PLATFORM.WOS.value,
                )
            ],
            platform=PLATFORM.WOS.value,
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
    title_fields = ["TI=", "ti=", "title="]

    for field in title_fields:
        result = syntax_str_to_generic_search_field_set(field)
        assert result == {Fields.TITLE}


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
    ]

    for field in abstract_fields:
        result = syntax_str_to_generic_search_field_set(field)
        assert result == {Fields.ABSTRACT}


def test_check_search_fields_author() -> None:
    """
    Test the `check_search_fields` method with author search fields.

    This test verifies that the `check_search_fields` method correctly translates
    author search fields into the base search field "AU=".
    """
    author_fields = [
        "AU=",
        "au=",
        "author=",
    ]

    for field in author_fields:
        result = syntax_str_to_generic_search_field_set(field)
        assert result == {Fields.AUTHOR}


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
    ]

    for field in topic_fields:
        result = syntax_str_to_generic_search_field_set(field)
        assert result == {Fields.TOPIC}


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
    ]

    for field in language_fields:
        result = syntax_str_to_generic_search_field_set(field)
        assert result == {Fields.LANGUAGE}


def test_check_search_fields_year() -> None:
    """
    Test the `check_search_fields` method with year search fields.

    This test verifies that the `check_search_fields` method correctly translates
    year search fields into the base search field "PY=".
    """
    year_fields = [
        "PY=",
        "py=",
    ]

    for field in year_fields:
        result = syntax_str_to_generic_search_field_set(field)
        assert result == {Fields.YEAR}


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
    assert query.children[1].search_field.value == "AU="  # type: ignore
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
    assert query.children[1].children[1].search_field.value == "AU="  # type: ignore
