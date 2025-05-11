class CustomParser(QueryStringParser):
    PARENTHESIS_REGEX = r"[\(\)]"
    LOGIC_OPERATOR_REGEX = r"\b(AND|OR|NOT)\b"
    SEARCH_FIELD_REGEX = r"\b\w{2}="
    SEARCH_TERM_REGEX = r"\"[^\"]+\"|\S+"

    pattern = "|".join(
        [PARENTHESIS_REGEX, LOGIC_OPERATOR_REGEX, SEARCH_FIELD_REGEX, SEARCH_TERM_REGEX]
    )

    def __init__(self, query_str, *, search_field_general="", mode=LinterMode.STRICT):
        super().__init__(
            query_str, search_field_general=search_field_general, mode=mode
        )
        self.linter = CustomLinter(self)

    def tokenize(self):
        for match in re.finditer(self.pattern, self.query_str):
            token = match.group().strip()
            start, end = match.span()
            # assign token_type as shown above
            self.tokens.append(
                Token(value=token, type=token_type, position=(start, end))
            )

        self.combine_subsequent_terms()

    def parse_query_tree(self, tokens: list) -> Query:
        # Build query tree here
        ...

    def parse(self) -> Query:
        self.tokenize()
        self.linter.validate_tokens()
        self.linter.check_status()
        query = self.parse_query_tree(self.tokens)
        self.linter.validate_query_tree(query)
        self.linter.check_status()
        return query
