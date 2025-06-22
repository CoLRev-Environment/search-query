class CustomParser(QueryStringParser):
    PARENTHESIS_REGEX = r"[\(\)]"
    LOGIC_OPERATOR_REGEX = r"\b(AND|OR|NOT)\b"
    FIELD_REGEX = r"\b\w{2}="
    TERM_REGEX = r"\"[^\"]+\"|\S+"

    pattern = "|".join(
        [PARENTHESIS_REGEX, LOGIC_OPERATOR_REGEX, FIELD_REGEX, TERM_REGEX]
    )

    def __init__(self, query_str, *, field_general=""):
        super().__init__(query_str, field_general=field_general)
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
