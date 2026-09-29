from unittest.mock import patch

from pyoptools.all import Ray

from prisms.cad_verifier import CadOpticsVerifier, extract_ray_segments


def test_extract_ray_segments():
    ray = Ray(origin=(0, 0, 0), direction=(0, 1, 0), wavelength=0.405)
    segments = extract_ray_segments(ray, z_offset=10.0)
    assert len(segments) == 1
    p1, p2 = segments[0]
    assert p1 == [0.0, 0.0, 10.0]
    assert p2[1] == 15.0
    assert p2[2] == 10.0


def test_verifier_mocked_alignment():
    mock_positions = {
        "prism": [0.0, 0.0, -8.42],
        "clens1": [0.0, -29.0, 12.0],
        "clens2": [6.0, 31.0, 11.0],
        "mirror": [-8.75, 25.0, 11.3],
        "laser": [0.0, -1.0, 9.0],
        "diode": [0.0, 0.0, 0.0],
    }

    verifier = CadOpticsVerifier()
    with (
        patch.object(verifier, "extract_cad_positions", return_value=mock_positions),
        patch.object(verifier, "_push_rays_to_freecad"),
    ):
        results = verifier.verify_and_report(update_cad_rays=True)
        assert results["alignment"]["laser_pass"] is True
        assert results["alignment"]["cl1_pass"] is True
        assert "cl1_focal_x" in results["focal"]
