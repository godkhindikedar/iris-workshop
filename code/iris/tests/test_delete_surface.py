import json

from scripts.delete_surface import (
    Ownership,
    clear_surface_env,
    confirmed,
    forget_surface,
    read_ledger,
    record_surface,
    surface_ids_from_index_names,
)

A = "a104e294-c7db-44c5-a735-336eec563910"
B = "54a15083-a2da-468c-a03e-33514f8b82a7"
OTHER = "b82b9236-1111-2222-3333-444444444444"


def test_surface_ids_come_from_surface_index_names_only():
    names = [
        f"idx:{A}:ee3a4f79:order",
        f"idx:{A.upper()}:12ce2ab4:customer",
        f"idx:{B}:4f35adec:orderitem",
        "reddash-guardrails",
        "langcache:7fe47040d5514a11b8504a35af300a60",
        "idx:northfield_bankdocument",
        "memory:874ef2ec259c45b3ad3fa81ac76f9666:ltm",
    ]
    assert surface_ids_from_index_names(names) == {A, B}


def test_only_surfaces_tied_to_this_demo_count_as_owned():
    own = Ownership(current_id=A, ledger_ids=frozenset({B}), index_ids=frozenset({"c" * 8 + "-0000-0000-0000-000000000000"}))
    assert own.reason(A) == "current (.env)"
    assert own.reason(B) == "created by this checkout"
    assert own.reason("c" * 8 + "-0000-0000-0000-000000000000") == "owns indexes in this Redis"
    assert own.reason(OTHER) is None  # a colleague's surface on the shared admin key


def test_matching_ignores_case_and_an_empty_current_id_matches_nothing():
    own = Ownership(current_id="", ledger_ids=frozenset(), index_ids=frozenset({A}))
    assert own.reason(A.upper()) == "owns indexes in this Redis"
    assert own.reason("") is None


def test_clear_surface_env_blanks_only_the_surface_keys():
    text = "GOOGLE_CLOUD_PROJECT=proj\nCTX_SURFACE_ID=abc\nMCP_AGENT_KEY=secret\nMEMORY_STORE_ID=keep\n"
    assert clear_surface_env(text) == "GOOGLE_CLOUD_PROJECT=proj\nCTX_SURFACE_ID=\nMCP_AGENT_KEY=\nMEMORY_STORE_ID=keep\n"


def test_confirmation_rules():
    assert confirmed(2, yes=True, interactive=False)
    assert not confirmed(2, yes=False, interactive=False)  # never delete silently without --yes
    assert confirmed(2, yes=False, interactive=True, ask=lambda _: "y")
    assert not confirmed(2, yes=False, interactive=True, ask=lambda _: "")


def test_ledger_round_trip(tmp_path):
    path = tmp_path / "ledger.json"
    assert read_ledger(path) == []
    record_surface(A, "Reddash Delivery Surface", path)
    record_surface(B, "Reddash Delivery Surface", path)
    record_surface(A, "Reddash Delivery Surface", path)  # re-recording does not duplicate
    assert [e["id"] for e in read_ledger(path)] == [B, A]
    forget_surface(B, path)
    assert [e["id"] for e in read_ledger(path)] == [A]
    path.write_text("not json")
    assert read_ledger(path) == []
