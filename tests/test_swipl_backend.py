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
