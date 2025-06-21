from search_query.constants_example import generic_field_set_to_syntax_set
from search_query.constants_example import map_field
from search_query.query import Query
from search_query.translator_base import QueryTranslator


class CustomTranslator(QueryTranslator):
    """Translator for Custom queries."""

    @classmethod
    def to_generic_syntax(cls, query: Query, *, field_general: str) -> Query:
        query = query.copy()
        cls.translate_fields_to_generic(query)
        return query

    @classmethod
    def to_specific_syntax(cls, query: Query) -> Query:
        query = query.copy()
        cls._translate_fields(query)
        return query

    @classmethod
    def translate_fields_to_generic(cls, query: Query) -> None:
        if query.field:
            fields = map_field(query.field.value)
            if len(fields) == 1:
                query.field.value = fields.pop()
            else:
                raise NotImplementedError
        for child in query.children:
            cls.translate_fields_to_generic(child)

    @classmethod
    def _translate_fields(cls, query: Query) -> None:
        if query.field:
            specific = generic_field_to_syntax_field(query.field.value)
            query.field.value = specific

        for child in query.children:
            cls._translate_fields(child)
