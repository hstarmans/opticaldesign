import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        # Compact Prism Scanner & Reflection Analysis

        Analyzes the compact layout of the Hexastorm scanner and optical reflections
        at the secondary prism surface using Snell's Law and Fresnel equations.
        """
    )


@app.cell
def _():
    import logging
    import os

    import marimo as mo
    import numpy as np
    from sympy.physics.optics import critical_angle, fresnel_coefficients

    from prisms.system import PrismScanner

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)
    return PrismScanner, critical_angle, fresnel_coefficients, logger, mo, np, os


@app.cell
def _(PrismScanner):
    # Instantiate compact scanner (without cylindrical lenses)
    p = PrismScanner(compact=True)
    return (p,)


@app.cell
def _(logger, p):
    # Plot at -35 degrees
    logger.info("Plotted compact system at -35 degrees")
    return p.plot(-35)


@app.cell
def _(logger, p):
    # Calculate optimal photodiode position
    focal_coords = p.focal_point(
        cyllens1=True, angle=43, simple=False, diode=True, plot=False
    )
    logger.info("Optimal photodiode position: %s", p.position_diode)
    return (focal_coords,)


@app.cell
def _(logger, p):
    # Trace key rays hitting photodiode
    logger.info("Rendering key rays for photodiode")
    return p.show_key_rays(scanline=False)


@app.cell
def _(logger, np):
    # Snell's Law calculation for refracted beam
    def snell(theta_inc, n1, n2):
        """Compute the refraction angle using Snell's Law.

        sin(theta_refr) = (n1 / n2) * sin(theta_inc)
        """
        return np.arcsin((n1 / n2) * np.sin(theta_inc))

    angle_inc = np.radians(42)
    angle_refr = snell(angle_inc, 1.0, 1.5)
    logger.info(
        "Incident angle: %.2f deg -> Refracted angle: %.2f deg",
        np.degrees(angle_inc),
        np.degrees(angle_refr),
    )
    return angle_inc, angle_refr, snell


@app.cell
def _(critical_angle, fresnel_coefficients, logger, np):
    # Fresnel reflectance calculation
    coeffs = fresnel_coefficients(0.46, 1.5, 1.0)[:2]
    refl_power = sum([abs(float(x)) ** 2 for x in coeffs]) / 2.0
    logger.info("Fresnel average reflectance at 0.46 rad: %.4f", refl_power)

    crit_ang = critical_angle(1.5, 1.0)
    logger.info(
        "Critical angle (N-BK7 to air): %.2f degrees", np.degrees(float(crit_ang))
    )
    return coeffs, crit_ang, refl_power


@app.cell
def _(logger, np, p):
    # Alignment sensitivity analysis
    initial_position = np.array([0.0, 0.0, 0.0])
    delta = -0.02
    p.set_orientation("prism", position=initial_position.tolist())
    start = p.focal_point(cyllens1=True, angle=43, simple=False, diode=True, plot=False)

    # Test axis shifts
    p.set_orientation(
        "prism", position=(initial_position + np.array([delta, 0, 0])).tolist()
    )
    delta_x = p.focal_point(
        cyllens1=True, angle=43, simple=False, diode=True, plot=False
    )

    p.set_orientation(
        "prism", position=(initial_position + np.array([0, delta, 0])).tolist()
    )
    delta_y = p.focal_point(
        cyllens1=True, angle=43, simple=False, diode=True, plot=False
    )

    p.set_orientation(
        "prism", position=(initial_position + np.array([0, 0, delta])).tolist()
    )
    delta_z = p.focal_point(
        cyllens1=True, angle=43, simple=False, diode=True, plot=False
    )

    logger.info("X-offset delta: %s", start - delta_x)
    logger.info("Y-offset delta: %s", start - delta_y)
    logger.info("Z-offset delta: %s", start - delta_z)
    return delta, delta_x, delta_y, delta_z, initial_position, start


@app.cell
def _(logger, os, p):
    # Load cached FreeCAD positions if available
    cache_file = "temp.pkl"
    if os.path.exists(cache_file):
        p.load_system(cache_file)
        logger.info("Loaded system positions from %s", cache_file)
    return (cache_file,)


if __name__ == "__main__":
    app.run()
