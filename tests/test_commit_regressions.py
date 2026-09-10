from copy import deepcopy
import json

import pytest

from logical import cli
from logical.schema import ClaimRecord, ExtractionResult, QueryIntent
from logical.service import add_knowledge, ask_query, check_knowledge
from logical.store import KnowledgeStore


class CityExtractor:
    model = "fixture"

    def __init__(self, city):
        self.city = city

    def extract_knowledge(self, text):
        return deepcopy(
            ExtractionResult(
                claims=[
                    ClaimRecord(
                        "ada",
                        "home_city",
                        self.city,
                        text,
                        s_kind="object",
                        o_kind="object",
                    )
                ]
            )
        )


@pytest.mark.parametrize("json_output", [False, True])
@pytest.mark.parametrize("replace", [False, True])
def test_committed_source_reports_success_and_recoverable_projection_warning(
    tmp_path, capsys, json_output, replace
):
    store = KnowledgeStore(tmp_path)
    old = add_knowledge(
        "Ada lives in London.", store, CityExtractor("london"), interactive=False
    )
    store.world_path.unlink()
    store.world_path.mkdir()
    args = ["--store-dir", str(tmp_path)]
    args += ["update", old.source_id] if replace else ["add"]
    args += ["Ada lives in Paris.", "--noninteractive"]
    if json_output:
        args.append("--json")

    code = cli.main(args, extractor=CityExtractor("paris"))
    captured = capsys.readouterr()
    sources = store.load_sources()
    committed = next(s for s in sources if s.text == "Ada lives in Paris.")
    assert code == 0
    assert committed.id in captured.out
    if json_output:
        result = json.loads(captured.out)
        assert result["source_id"] == committed.id
        assert "was committed" in result["warnings"][0]
    else:
        assert "was committed" in captured.err and "logical check" in captured.err
    assert ask_query(QueryIntent("ada", "home_city", "paris"), store).answer == "true"
    if replace:
        assert (
            next(s for s in sources if s.id == old.source_id).superseded_by
            == committed.id
        )
        assert (
            ask_query(QueryIntent("ada", "home_city", "london"), store).answer
            == "unknown"
        )

    # Repairing the derived file must not require replaying the committed update.
    assert not check_knowledge(store).ok
    store.world_path.rmdir()
    assert check_knowledge(store).ok
    assert "paris" in store.world_path.read_text()
