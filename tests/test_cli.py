import json

from clawimaging.cli import run


def test_cli_list_text(capsys) -> None:
    exit_code = run(["list"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "- ct-recon (ct):" in captured.out


def test_cli_list_json(capsys) -> None:
    exit_code = run(["list", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert any(skill["name"] == "benchmark-run" for skill in payload)


def test_cli_show_skill(capsys) -> None:
    exit_code = run(["show-skill", "bench"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["name"] == "benchmark-run"


def test_cli_route(capsys) -> None:
    exit_code = run(["route", "please run a low-dose ct reconstruction from a sinogram"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["name"] == "ct-recon"


def test_cli_route_explain(capsys) -> None:
    exit_code = run(["route", "benchmark compare methods", "--explain"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["skill"]["name"] == "benchmark-run"
    assert payload["score"] == 2
    assert payload["matched_keywords"] == ["benchmark", "compare methods"]


def test_cli_route_unmatched(capsys) -> None:
    exit_code = run(["route", "morphological image segmentation"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "No matching skill found.\n"
