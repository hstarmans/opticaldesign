import numpy as np
import pytest

from prisms.analytical import Prism_properties, PrismProperties


def test_alias_compatibility():
    """Verify that Prism_properties is an alias to PrismProperties."""
    assert Prism_properties is PrismProperties
    p = Prism_properties()
    assert isinstance(p, PrismProperties)


def test_default_parameters():
    """Verify default optical parameters."""
    p = PrismProperties()
    assert p.params["n"] == 1.53
    assert p.params["facets"] == 4
    assert p.params["wavelength"] == 405
    assert p.params["T"] == 30
    assert p.params["f_length"] == 75
    assert p.params["d_bundle"] == 1.2
    assert p.params["rot_hz"] == 350
    assert p.params["f_numb"] == pytest.approx(75 / 1.2)


def test_spot_size_and_rayleigh():
    """Verify Gaussian spot size and Rayleigh range calculations."""
    p = PrismProperties()
    spot = p.spot_size()
    # waist = (2 * 405 / pi) * 62.5 / 1000 ~= 16.11 microns
    assert spot == pytest.approx(16.11, rel=1e-2)

    rayleigh = p.rayleigh_length()
    # rayleigh = pi * spot^2 / 405 ~= 2.014 mm
    assert rayleigh == pytest.approx(2.014, rel=1e-2)


def test_max_angle_incidence():
    """Verify max angle of incidence for 4 facets is 45 degrees (pi/4 rad)."""
    p = PrismProperties()
    max_angle = p.max_angle_incidence()
    assert max_angle == pytest.approx(np.pi / 4, rel=1e-4)


def test_shifts():
    """Verify longitudinal and transversal focus shifts."""
    p = PrismProperties()
    slong = p.longitudinal_shift()
    # (1.53 - 1) / 1.53 * 30 ~= 10.39 mm
    assert slong == pytest.approx(10.392, rel=1e-3)

    # At 0 angle, transversal shift should be exactly 0
    assert p.transversal_shift(0.0) == pytest.approx(0.0, abs=1e-9)
    # At positive angle, transversal shift is positive
    shift_pos = p.transversal_shift(0.2)
    assert shift_pos > 0.0


def test_speed_edges():
    """Verify speed ratio calculation along scanline."""
    p = PrismProperties()
    # At 0 angle, speed at edge equals center (fraction = 1.0)
    frac_zero = p.speed_edges(0.0)
    assert frac_zero == pytest.approx(1.0, rel=1e-4)

    # At 0.46 rad, speed fraction should be ~0.80 (80%)
    frac_angle = p.speed_edges(0.46)
    assert frac_angle == pytest.approx(0.80, abs=0.02)


def test_strehl_ratio():
    """Verify Strehl ratio decreases from 1.0 at 0 angle."""
    p = PrismProperties()
    # At zero tilt, Strehl ratio is 1.0 (or very close depending on spherical aberration)
    strehl_zero = p.strehl_ratio(0.0)
    assert 0.99 <= strehl_zero <= 1.0

    # At recommended angle (~0.46 rad), Strehl ratio is above 0.8
    strehl_angle = p.strehl_ratio(0.46)
    assert strehl_angle > 0.8


def test_max_recommended_angle():
    """Verify max recommended angle converges fast and within bounds."""
    p = PrismProperties()
    rec_angle = p.max_recommended_angle(strehl_ratio=0.71, min_fraction=0.8)
    assert 0.40 < rec_angle < 0.50
    assert rec_angle < p.max_angle_incidence()


def test_cross_scan_error():
    """Verify cross scan error is within expected microns range."""
    p = PrismProperties()
    cross_err = p.cross_scan_error(focal_distance=35)
    # Cross scan error should be around 0.0054 mm (5.4 microns)
    assert cross_err == pytest.approx(0.0054, rel=1e-1)
