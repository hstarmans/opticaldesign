import marimo

__generated_with = "0.23.9"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Hexastorm Polygon Prism Scanner - Interactive Simulation
    Simulate and visualize the optical layout, ray tracing, photodiode hit angles,
    and alignment sensitivity of the Hexastorm prism scanner in real time.
    """)


@app.cell
def _():
    import logging

    import marimo as mo
    import numpy as np

    from prisms.analytical import PrismProperties
    from prisms.system import PrismScanner

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    return PrismProperties, PrismScanner, mo, np


@app.cell
def _(PrismProperties, mo, np):
    props = PrismProperties()
    deg_val = np.degrees(props.max_recommended_angle())
    mo.md(
        f"""
        ### Analytical Performance Metrics
        | Metric | Value |
        | :--- | :--- |
        | **Waist spot size** | `{props.spot_size():.2f} µm` |
        | **Rayleigh range** | `{props.rayleigh_length():.3f} mm` |
        | **Max recommended angle** | `{props.max_recommended_angle():.2f} rad` ({deg_val:.1f}°) |
        | **Duty cycle** | `{props.duty_cycle() * 100:.1f} %` |
        | **Strehl ratio at max angle** | `{props.strehl_ratio(props.max_recommended_angle()):.2f}` |
        | **Cross-scan error** | `{props.cross_scan_error() * 1000:.2f} µm` |
        """
    )


@app.cell
def _(mo):
    angle_slider = mo.ui.slider(
        start=-45,
        stop=45,
        step=1,
        value=-38,
        label="Prism Rotation Angle",
        show_value=True,
    )
    cylinder_toggle = mo.ui.checkbox(value=True, label="Include Cylinders")
    key_rays_toggle = mo.ui.checkbox(value=False, label="Key Boundary Rays")
    camera_view = mo.ui.dropdown(
        options={
            "Perspective 3D": {"x": -1.6, "y": -1.6, "z": 1.3},
            "Top View (XY)": {"x": 0.0, "y": 0.0, "z": 2.5},
            "Side View (YZ)": {"x": 2.5, "y": 0.0, "z": 0.0},
            "Front View (XZ)": {"x": 0.0, "y": -2.5, "z": 0.0},
        },
        value="Perspective 3D",
        label="Camera Angle",
    )
    return angle_slider, camera_view, cylinder_toggle, key_rays_toggle


@app.cell
def _(
    PrismScanner,
    angle_slider,
    camera_view,
    cylinder_toggle,
    key_rays_toggle,
    mo,
):
    scanner = PrismScanner(withcylinder=cylinder_toggle.value)
    hit_range = scanner.find_object("diode")
    focal_dist = scanner.distance_between_cylinders() if cylinder_toggle.value else 0.0

    is_hit = len(hit_range) == 2 and (
        hit_range[0] <= angle_slider.value <= hit_range[1]
    )
    hit_badge = "🟢 Diode illuminated" if is_hit else "⚪ Diode not hit"

    controls = mo.hstack(
        [angle_slider, cylinder_toggle, key_rays_toggle, camera_view],
        justify="start",
        align="center",
        gap=2,
    )

    status_md = mo.md(
        f"""
        * **Prism Angle:** `{angle_slider.value}°` &nbsp;|&nbsp;
        * **Photodiode Status:** {hit_badge} &nbsp;|&nbsp;
        * **Photodiode Hit Window:** `{hit_range}` &nbsp;|&nbsp;
        * **Cylinder Focal Distance:** `{focal_dist:.3f} mm`
        """
    )

    if key_rays_toggle.value:
        fig = scanner.show_key_rays(backend="plotly", camera_eye=camera_view.value)
    else:
        fig = scanner.plot(
            angle=angle_slider.value,
            backend="plotly",
            camera_eye=camera_view.value,
        )

    mo.vstack(
        [
            mo.md("### Interactive 3D System View"),
            controls,
            status_md,
            mo.ui.plotly(fig),
        ]
    )
    return (scanner,)


@app.cell
def _(mo, np, scanner):
    # Sensitivity analysis: 0.2 mm offset in X, Y, Z
    initial_pos = np.array([-35.0, 0.0, 0.0])
    delta_val = 0.2
    scanner.set_orientation("prism", position=initial_pos.tolist())
    nominal = scanner.focal_point(
        cyllens1=True, angle=-42, simple=False, diode=True, plot=False
    )

    scanner.set_orientation(
        "prism", position=(initial_pos + np.array([delta_val, 0, 0])).tolist()
    )
    shift_x = nominal - scanner.focal_point(
        cyllens1=True, angle=-42, simple=False, diode=True, plot=False
    )

    scanner.set_orientation(
        "prism", position=(initial_pos + np.array([0, delta_val, 0])).tolist()
    )
    shift_y = nominal - scanner.focal_point(
        cyllens1=True, angle=-42, simple=False, diode=True, plot=False
    )

    scanner.set_orientation(
        "prism", position=(initial_pos + np.array([0, 0, delta_val])).tolist()
    )
    shift_z = nominal - scanner.focal_point(
        cyllens1=True, angle=-42, simple=False, diode=True, plot=False
    )

    # Reset orientation
    scanner.set_orientation("prism", position=initial_pos.tolist())

    norm_x = np.linalg.norm(shift_x)
    norm_y = np.linalg.norm(shift_y)
    norm_z = np.linalg.norm(shift_z)

    mo.md(
        f"""
        ### Alignment Sensitivity (0.2 mm axis displacement)
        * **X-offset spot shift:** `{norm_x:.4e} mm` ({shift_x})
        * **Y-offset spot shift:** `{norm_y:.4e} mm` ({shift_y})
        * **Z-offset spot shift:** `{norm_z:.4e} mm` ({shift_z})
        """
    )


if __name__ == "__main__":
    app.run()
