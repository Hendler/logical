import shutil

import pytest

from logical.prolog import run_swipl_query, validate_with_swipl


pytestmark = pytest.mark.skipif(
    shutil.which("swipl") is None,
    reason="SWI-Prolog is not installed; on macOS run `brew install swi-prolog`.",
)


def test_swipl_validates_and_queries_world_file(tmp_path):
    world_path = tmp_path / "world.pl"
    world_path.write_text("triple(sky,color,red).\n", encoding="utf-8")

    result = validate_with_swipl(world_path)

    assert result.ok, result.message
    assert run_swipl_query(world_path, "triple(sky,color,red)") is True
    assert run_swipl_query(world_path, "triple(sky,color,blue)") is False


from logical.prolog import project_world, query_for_intent
from logical.reasoning import infer
from logical.schema import ClaimRecord, QueryIntent


def test_prolog_and_python_agree_on_taxonomy_cycles_and_universal_negation(tmp_path):
    claims = [
        ClaimRecord(
            "ada",
            "instance_of",
            "person",
            "fixture",
            s_kind="object",
            o_kind="category",
        ),
        ClaimRecord(
            "person",
            "subclass_of",
            "human",
            "fixture",
            s_kind="category",
            o_kind="category",
        ),
        ClaimRecord(
            "human",
            "subclass_of",
            "person",
            "fixture",
            s_kind="category",
            o_kind="category",
        ),
        ClaimRecord(
            "human",
            "subclass_of",
            "mammal",
            "fixture",
            s_kind="category",
            o_kind="category",
        ),
        ClaimRecord(
            "mammal",
            "breathes",
            "true",
            "fixture",
            s_kind="category",
            o_kind="value",
            scope="all",
        ),
        ClaimRecord(
            "mammal",
            "made_of_metal",
            "true",
            "fixture",
            s_kind="category",
            o_kind="value",
            scope="all",
            polarity=False,
        ),
    ]
    world = tmp_path / "world.pl"
    world.write_text(project_world(claims, []))
    assert validate_with_swipl(world).ok
    proofs = infer(claims).proofs
    for s, p, o, polarity in proofs:
        assert run_swipl_query(world, query_for_intent(QueryIntent(s, p, o, polarity)))
    for s, p, o in [
        ("ada", "flies", "true"),
        ("mammal", "breathes", "true"),
        ("unknown_person", "instance_of", "person"),
    ]:
        assert not run_swipl_query(world, query_for_intent(QueryIntent(s, p, o)))
        assert (s, p, o, True) not in proofs


def test_prolog_check_detects_semantic_contradiction_not_just_syntax(tmp_path):
    claims = [
        ClaimRecord("ada", "breathes", "true", "fixture"),
        ClaimRecord("ada", "breathes", "true", "fixture", polarity=False),
    ]
    path = tmp_path / "world.pl"
    path.write_text(project_world(claims, []))
    assert not validate_with_swipl(path).ok


def test_prolog_syntax_error_is_not_reported_as_success(tmp_path):
    path = tmp_path / "world.pl"
    path.write_text("triple(ada, color, .\n")
    assert not validate_with_swipl(path).ok


def test_empty_world_has_callable_predicates_and_unknown_answers(tmp_path):
    path = tmp_path / "world.pl"
    path.write_text(project_world([], []))
    assert validate_with_swipl(path).ok
    assert not run_swipl_query(path, "triple(ada,color,red)")
