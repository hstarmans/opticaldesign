import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        # Optical Design & Simulation of Prism Scanner

        This notebook simulates the optical layout of the Hexastorm polygon prism scanner.
        It computes chief rays, photodiode hit angles, cylinder lens focal points,
        and sensitivity to alignment offsets.
        """
    )


@app.cell
def _():
    import logging
    import os

    import marimo as mo
    import numpy as np

    from prisms.system import PrismScanner

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)
    return PrismScanner, logger, mo, np, os


@app.cell
def _(PrismScanner):
    # Instantiate scanner system with cylindrical lenses
    p = PrismScanner(withcylinder=True)
    return (p,)


@app.cell
def _(logger, p):
    # Plot the system for a prism rotation angle of -38 degrees
    logger.info("Generating 3D plot widget at -38 degrees")
    return p.plot(-38)


@app.cell
def _(logger, p):
    # Find the angle range at which the photodiode is illuminated
    hit_angles = p.find_object("diode")
    logger.info("Photodiode hit angle range: %s degrees", hit_angles)
    return (hit_angles,)


@app.cell
def _(logger, p):
    # Trace key rays:
    # - Rays hitting photodiode edges
    # - Rays defining scanline limits
    # - Center reference ray
    logger.info("Rendering key rays")
    return p.show_key_rays()


@app.cell
def _(logger, p):
    # Distance between focal points of both cylindrical lenses
    dist = p.distance_between_cylinders()
    logger.info("Distance between focal points of cylinder lenses: %.2f mm", dist)
    return (dist,)


@app.cell
def _(logger, p):
    # Determine the optimal position of the photodiode
    p.focal_point(cyllens1=True, angle=-43, diode=True, plot=False)
    logger.info("Calculated photodiode position: %s", p.position_diode)


@app.cell
def _(logger, np, p):
    # Sensitivity analysis:
    # Test displacement of prism rotation axis and its effect on spot position
    initial_position = np.array([-35.0, 0.0, 0.0])
    delta = 0.2
    p.set_orientation("prism", position=initial_position.tolist())

    start = p.focal_point(
        cyllens1=True, angle=-42, simple=False, diode=True, plot=False
    )

    # X-translation
    p.set_orientation(
        "prism", position=(initial_position + np.array([delta, 0, 0])).tolist()
    )
    delta_x = p.focal_point(
        cyllens1=True, angle=-42, simple=False, diode=True, plot=False
    )

    # Y-translation
    p.set_orientation(
        "prism", position=(initial_position + np.array([0, delta, 0])).tolist()
    )
    delta_y = p.focal_point(
        cyllens1=True, angle=-42, simple=False, diode=True, plot=False
    )

    # Z-translation
    p.set_orientation(
        "prism", position=(initial_position + np.array([0, 0, delta])).tolist()
    )
    delta_z = p.focal_point(
        cyllens1=True, angle=-42, simple=False, diode=True, plot=False
    )

    logger.info("Shift from X-offset (0.2 mm): %s", start - delta_x)
    logger.info("Shift from Y-offset (0.2 mm): %s", start - delta_y)
    logger.info("Shift from Z-offset (0.2 mm): %s", start - delta_z)
    return delta_x, delta_y, delta_z, initial_position, start


@app.cell
def _(logger, os, p):
    # Load cached FreeCAD positions if available
    cache_file = "temp.pkl"
    if os.path.exists(cache_file):
        p.load_system(cache_file)
        logger.info("Loaded system positions from %s", cache_file)
    else:
        logger.info(
            "No %s cache file found; using default analytical positions", cache_file
        )
    return (cache_file,)


if __name__ == "__main__":
    app.run()
