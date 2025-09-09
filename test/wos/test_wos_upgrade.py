import pytest

from search_query.constants import PLATFORM
from search_query.upgrade import upgrade_query


def test_upgrade_wos_0_to_1_deprecated_fields() -> None:
    query = "DI=10.1000/xyz123 AND DE=robotics AND PU=Springer"
    with pytest.warns(UserWarning) as record:
        upgraded = upgrade_query(query, PLATFORM.WOS.value, "0", "1")
    assert upgraded == "DO=10.1000/xyz123 AND AK=robotics"
    assert any("PU=" in str(w.message) for w in record)
