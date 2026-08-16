from cybersec_api.models import Base


def test_initial_tables_are_registered() -> None:
    assert {"users", "sources", "items", "enrichments", "cyber_entities"}.issubset(
        Base.metadata.tables.keys()
    )
