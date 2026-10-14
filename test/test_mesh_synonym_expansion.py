"""Offline tests for MeSH synonym expansion."""
from __future__ import annotations

import pytest

from search_query import synonym_expansion_mesh


class FakeResponse:
    """Minimal response object returned by the mocked NCBI calls."""

    def __init__(self, content: bytes) -> None:
        self.content = content


def test_expand_query_without_mesh_results(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, *, params: dict, timeout: int) -> FakeResponse:
        assert url.endswith("esearch.fcgi")
        assert params["term"] == "unlisted term"
        assert timeout == 60
        return FakeResponse(b"<eSearchResult><IdList /></eSearchResult>")

    monkeypatch.setattr(synonym_expansion_mesh.requests, "get", fake_get)

    assert synonym_expansion_mesh.expand_query_with_synonyms("unlisted term") == (
        "unlisted term"
    )


def test_expand_query_with_mesh_synonyms(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, *, params: dict, timeout: int) -> FakeResponse:
        if url.endswith("esearch.fcgi"):
            return FakeResponse(
                b"<eSearchResult><IdList><Id>42</Id></IdList></eSearchResult>"
            )
        assert url.endswith("esummary.fcgi")
        assert params["id"] == "42"
        return FakeResponse(
            b"<eSummaryResult><DocSum><Item Name='DS_MeshTerms'>"
            b"<Item>Asthma</Item><Item>Wheezing</Item>"
            b"</Item></DocSum></eSummaryResult>"
        )

    monkeypatch.setattr(synonym_expansion_mesh.requests, "get", fake_get)

    assert synonym_expansion_mesh.expand_query_with_synonyms("asthma") == (
        "(Asthma OR Wheezing)"
    )


def test_expand_each_and_term_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []

    def fake_get(url: str, *, params: dict, timeout: int) -> FakeResponse:
        if url.endswith("esearch.fcgi"):
            term = params["term"]
            calls.append(("search", term))
            if term == "asthma":
                return FakeResponse(
                    b"<eSearchResult><IdList><Id>42</Id></IdList></eSearchResult>"
                )
            return FakeResponse(b"<eSearchResult><IdList /></eSearchResult>")
        calls.append(("summary", params["id"]))
        return FakeResponse(
            b"<eSummaryResult><DocSum><Item Name='DS_MeshTerms'>"
            b"<Item>Asthma</Item><Item>Wheezing</Item>"
            b"</Item></DocSum></eSummaryResult>"
        )

    monkeypatch.setattr(synonym_expansion_mesh.requests, "get", fake_get)

    assert synonym_expansion_mesh.expand_query_with_synonyms(
        "asthma AND treatment"
    ) == ("(Asthma OR Wheezing) AND treatment")
    assert calls == [
        ("search", "asthma"),
        ("summary", "42"),
        ("search", "treatment"),
    ]
