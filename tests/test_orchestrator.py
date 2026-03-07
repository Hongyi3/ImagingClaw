from clawimaging.orchestrator import route_query
from clawimaging.registry import list_skills


def test_route_query_ct() -> None:
    skill = route_query("please run a low-dose ct reconstruction from a sinogram", list_skills())
    assert skill is not None
    assert skill["name"] == "ct-recon"
