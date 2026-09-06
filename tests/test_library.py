import pytest

from prisms.library import Polygon


def test_polygon_init():
    """Verify polygon prism initialization with 4 sides."""
    poly = Polygon(sides=4, height=3, inner_radius=10)
    # 4 side facets + 1 bottom cap + 1 top cap = 6 surfaces
    assert len(poly.surflist) == 6
    # Ensure vertical sides exist
    for i in range(4):
        assert f"S{i}" in poly.surflist
    # Ensure caps exist
    assert "S4" in poly.surflist
    assert "S5" in poly.surflist


def test_polygon_reflection():
    """Verify reflection flag sets reflectivity on facet 1."""
    poly_no_refl = Polygon(sides=4, height=3, inner_radius=10, reflection=False)
    poly_refl = Polygon(sides=4, height=3, inner_radius=10, reflection=True)

    surf_no_refl = poly_no_refl.surflist["S1"][0]
    surf_refl = poly_refl.surflist["S1"][0]

    assert surf_refl.reflectivity == 1
    assert surf_no_refl.reflectivity != 1


def test_polygon_invalid_sides():
    """Verify error on polygon with fewer than 3 sides."""
    with pytest.raises(ValueError, match="at least 3 sides"):
        Polygon(sides=2)


def test_polygon_warning_odd_sides(caplog):
    """Verify warning logged for odd number of sides."""
    import logging

    with caplog.at_level(logging.WARNING):
        Polygon(sides=5)
    assert any("even number of sides" in record.message for record in caplog.records)
