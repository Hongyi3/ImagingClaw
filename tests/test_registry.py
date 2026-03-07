from clawimaging.registry import get_skill, list_skills


def test_list_skills_contains_ct() -> None:
    names = {skill["name"] for skill in list_skills()}
    assert "ct-recon" in names


def test_get_skill_by_alias() -> None:
    skill = get_skill("mri")
    assert skill is not None
    assert skill["name"] == "mri-recon"
