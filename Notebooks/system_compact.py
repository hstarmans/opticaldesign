import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Hexastorm Compact Prism Scanner & Reflection Analysis
    Analyze the compact optical layout (operating without cylindrical lenses),
    compute Snell's law refraction and Fresnel reflection coefficients at optical boundaries,
    and assess alignment sensitivity.
    """)


@app.cell
def _():
    import logging

    import marimo as mo
    import numpy as np
    from sympy.physics.optics import critical_angle, fresnel_coefficients

    from prisms.system import PrismScanner

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    return (
        PrismScanner,
        critical_angle,
        fresnel_coefficients,
        mo,
        np,
    )


@app.cell
def _(critical_angle, fresnel_coefficients, mo, np):
    # Snell's Law & Critical Angle for N-BK7 (n = 1.50) to Air (n = 1.00)
    n_glass = 1.50
    n_air = 1.00

    def snell(theta_inc, n1, n2):
        val = (n1 / n2) * np.sin(theta_inc)
        return np.arcsin(np.clip(val, -1.0, 1.0))

    test_theta_deg = 42.0
    theta_refr_deg = np.degrees(snell(np.radians(test_theta_deg), n_air, n_glass))
    crit_angle_deg = np.degrees(float(critical_angle(n_glass, n_air)))

    # Fresnel average reflectance at 0.46 rad (~26.35°)
    theta_fresnel_rad = 0.46
    fresnel_coeffs = fresnel_coefficients(theta_fresnel_rad, n_glass, n_air)[:2]
    refl_power = sum([abs(float(x)) ** 2 for x in fresnel_coeffs]) / 2.0

    mo.md(
        f"""
        ### Optical Physics & Interface Analysis
        | Property | Value | Formula / Details |
        | :--- | :--- | :--- |
        | **Glass Material** | `N-BK7 (n = {n_glass})` | Schott optical crown glass |
        | **Ambient Medium** | `Air (n = {n_air})` | Standard optical ambient |
        | **Critical Angle** | `{crit_angle_deg:.2f}°` | `θ_c = arcsin(n2 / n1)` |
        | **Refraction (Air → Glass)** | `{test_theta_deg:.1f}° → {theta_refr_deg:.2f}°` | `n1 × sin(θ1) = n2 × sin(θ2)` |
        | **Average Fresnel Reflectance** | `{refl_power * 100:.2f} %` | `R_avg = 0.5 × (|r_s|² + |r_p|²)` at `{np.degrees(theta_fresnel_rad):.1f}°` |
        """
    )


@app.cell
def _(mo):
    angle_input = mo.ui.slider(
        start=-45,
        stop=45,
        step=1,
        value=38,
        label="Prism Rotation Angle",
        include_input=True,
    ).form(submit_button_label="Calculate", bordered=False)

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
    return angle_input, camera_view, key_rays_toggle


@app.cell
def _(
    PrismScanner,
    angle_input,
    camera_view,
    key_rays_toggle,
    mo,
):
    scanner = PrismScanner(compact=True)
    hit_range = scanner.find_object("diode")

    angle_val = angle_input.value if angle_input.value is not None else 38
    is_hit = len(hit_range) == 2 and (hit_range[0] <= angle_val <= hit_range[1])
    hit_badge = "🟢 Diode illuminated" if is_hit else "⚪ Diode not hit"

    controls = mo.hstack(
        [angle_input, key_rays_toggle, camera_view],
        justify="start",
        align="center",
        gap=2,
    )

    status_md = mo.md(
        f"""
        * **Prism Angle:** `{angle_val}°` &nbsp;|&nbsp;
        * **Photodiode Status:** {hit_badge} &nbsp;|&nbsp;
        * **Photodiode Hit Window:** `{hit_range}` &nbsp;|&nbsp;
        * **Layout:** `Compact (No Cylinder Lenses)`
        """
    )

    if key_rays_toggle.value:
        fig = scanner.show_key_rays(backend="plotly", camera_eye=camera_view.value)
    else:
        fig = scanner.plot(
            angle=angle_val,
            backend="plotly",
            camera_eye=camera_view.value,
        )

    mo.vstack(
        [
            mo.md("### Interactive 3D Compact System View"),
            controls,
            status_md,
            mo.ui.plotly(fig),
        ]
    )
    return (scanner,)


@app.cell
def _(mo, np, scanner):
    # Sensitivity analysis: ±0.02 mm offset in X, Y, Z for compact layout
    initial_pos = np.array([0.0, 0.0, 0.0])
    delta_val = -0.02

    scanner.set_orientation("prism", position=initial_pos.tolist())
    nominal = scanner.focal_point(
        cyllens1=True, angle=43, simple=False, diode=True, plot=False
    )

    scanner.set_orientation(
        "prism", position=(initial_pos + np.array([delta_val, 0, 0])).tolist()
    )
    shift_x = scanner.focal_point(
        cyllens1=True, angle=43, simple=False, diode=True, plot=False
    )

    scanner.set_orientation(
        "prism", position=(initial_pos + np.array([0, delta_val, 0])).tolist()
    )
    shift_y = scanner.focal_point(
        cyllens1=True, angle=43, simple=False, diode=True, plot=False
    )

    scanner.set_orientation(
        "prism", position=(initial_pos + np.array([0, 0, delta_val])).tolist()
    )
    shift_z = scanner.focal_point(
        cyllens1=True, angle=43, simple=False, diode=True, plot=False
    )

    # Reset prism position
    scanner.set_orientation("prism", position=initial_pos.tolist())

    diff_x = np.array(nominal) - np.array(shift_x)
    diff_y = np.array(nominal) - np.array(shift_y)
    diff_z = np.array(nominal) - np.array(shift_z)

    norm_x = np.linalg.norm(diff_x)
    norm_y = np.linalg.norm(diff_y)
    norm_z = np.linalg.norm(diff_z)

    mo.md(
        f"""
        ### Alignment Sensitivity Analysis (Δ = {delta_val:+.2f} mm)
        Impact of prism mechanical alignment errors on photodiode focal hit position at `43°`:
        * **Nominal Focal Coordinates:** `[{nominal[0]:.3f}, {nominal[1]:.3f}, {nominal[2]:.3f}] mm`
        * **X-offset spot displacement:** `{norm_x * 1000:.3f} µm` (vector: `[{diff_x[0]:.2e}, {diff_x[1]:.2e}, {diff_x[2]:.2e}]`)
        * **Y-offset spot displacement:** `{norm_y * 1000:.3f} µm` (vector: `[{diff_y[0]:.2e}, {diff_y[1]:.2e}, {diff_y[2]:.2e}]`)
        * **Z-offset spot displacement:** `{norm_z * 1000:.3f} µm` (vector: `[{diff_z[0]:.2e}, {diff_z[1]:.2e}, {diff_z[2]:.2e}]`)
        """
    )


if __name__ == "__main__":
    app.run()
