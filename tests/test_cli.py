from logical import cli
from logical.schema import ClaimRecord, ConstraintRecord, ExtractionResult, QueryIntent


class FakeExtractor:
    def __init__(self):
        self.extractions = {
            "the sky is red": ExtractionResult(
                claims=[
                    ClaimRecord(
                        id="red",
                        s="sky",
                        p="color",
                        o="red",
                        source_text="the sky is red",
                    )
                ]
            ),
            "a sky can only be one color": ExtractionResult(
                constraints=[
                    ConstraintRecord(
                        kind="functional_for_subject",
                        s="sky",
                        p="color",
                        source_claim_id="constraint",
                    )
                ]
            ),
            "the sky is blue": ExtractionResult(
                claims=[
                    ClaimRecord(
                        id="blue",
                        s="sky",
                        p="color",
                        o="blue",
                        source_text="the sky is blue",
                    )
                ]
            ),
        }

    def extract_knowledge(self, text):
        return self.extractions[text]

    def extract_query(self, text):
        assert text == "is the sky red?"
        return QueryIntent(s="sky", p="color", o="red")


def test_cli_add_quarantines_conflict_and_ask_returns_true(tmp_path, capsys):
    extractor = FakeExtractor()

    assert cli.main(["--store-dir", str(tmp_path), "add", "the sky is red"], extractor) == 0
    assert (
        cli.main(
            ["--store-dir", str(tmp_path), "add", "a sky can only be one color"],
            extractor,
        )
        == 0
    )
    assert cli.main(["--store-dir", str(tmp_path), "add", "the sky is blue"], extractor) == 2

    output = capsys.readouterr().out
    assert "quarantined" in output
    assert "sky color blue" in output

    assert cli.main(["--store-dir", str(tmp_path), "ask", "is the sky red?"], extractor) == 0
    output = capsys.readouterr().out
    assert "true" in output
    assert "red" in output


def test_cli_check_writes_world_file(tmp_path, capsys):
    extractor = FakeExtractor()
    cli.main(["--store-dir", str(tmp_path), "add", "the sky is red"], extractor)

    assert cli.main(["--store-dir", str(tmp_path), "check"], extractor) == 0

    assert (tmp_path / "world.pl").exists()
    assert "ok" in capsys.readouterr().out


def test_cli_export_prolog_prints_projection(tmp_path, capsys):
    extractor = FakeExtractor()
    cli.main(["--store-dir", str(tmp_path), "add", "the sky is red"], extractor)

    assert cli.main(["--store-dir", str(tmp_path), "export-prolog"], extractor) == 0

    assert "triple(sky,color,red)." in capsys.readouterr().out


def test_cli_interactive_conflict_can_replace_existing_claim(
    tmp_path, capsys, monkeypatch
):
    extractor = FakeExtractor()
    cli.main(["--store-dir", str(tmp_path), "add", "the sky is red"], extractor)
    cli.main(
        ["--store-dir", str(tmp_path), "add", "a sky can only be one color"],
        extractor,
    )
    monkeypatch.setattr("builtins.input", lambda _: "r")

    exit_code = cli.main(
        ["--store-dir", str(tmp_path), "add", "--interactive", "the sky is blue"],
        extractor,
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "accepted: sky color blue" in output

    cli.main(["--store-dir", str(tmp_path), "export-prolog"], extractor)
    output = capsys.readouterr().out
    assert "triple(sky,color,blue)." in output
    assert "triple(sky,color,red)." not in output
