import pytest

from prisms.system import PrismScanner


def test_system_init():
    """Verify PrismScanner builds with and without cylinder lenses."""
    p_cyl = PrismScanner(withcylinder=True)
    assert p_cyl.withcylinder is True
    assert "CL1" in p_cyl.naming
    assert "prism" in p_cyl.naming
    assert "CL2" in p_cyl.naming
    assert "diode" in p_cyl.naming

    p_nocyl = PrismScanner(withcylinder=False)
    assert p_nocyl.withcylinder is False
    assert "lens" in p_nocyl.naming
    assert "prism" in p_nocyl.naming
    assert "diode" in p_nocyl.naming


def test_find_object_diode():
    """Verify finding the photodiode hit angles."""
    p = PrismScanner(withcylinder=True)
    angles = p.find_object("diode")
    assert len(angles) == 2
    # The photodiode is positioned to be hit around 41.3 to 44.9 degrees
    assert angles[0] == pytest.approx(41.3, abs=0.5)
    assert angles[1] == pytest.approx(44.9, abs=0.5)


def test_distance_between_cylinders():
    """Verify distance between focal points of both cylinder lenses."""
    p = PrismScanner(withcylinder=True)
    dist = p.distance_between_cylinders()
    # In nominal alignment, focal points are aligned (near 0 mm)
    assert dist == pytest.approx(0.0, abs=0.1)


def test_focal_point_coordinates():
    """Verify focal point calculation in both simple and full vector modes."""
    p = PrismScanner(withcylinder=True)
    dist_x = p.focal_point(cyllens1=True, simple=True)
    assert isinstance(dist_x, (float, int))

    dist_full = p.focal_point(cyllens1=True, simple=False)
    assert len(dist_full) == 3


def test_draw_key_rays():
    """Verify draw_key_rays executes without exceptions."""
    p = PrismScanner(withcylinder=True)
    p.draw_key_rays(diode=True, scanline=True)
