import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    import numpy as np

    from prisms.analytical import PrismProperties
    from prisms.system import PrismScanner

    return PrismProperties, PrismScanner, mo, np


@app.cell
def __(mo):
    mo.md(
        """
        # Hexastorm Prism Scanner - Interactive Simulation
        Explore the optical design and simulation of the Hexastorm polygon prism scanner in real time.
        """
    )


@app.cell
def __(PrismProperties, mo):
    props = PrismProperties()
    mo.md(
        f"""
        ### Analytical Performance Metrics
        * **Waist spot size:** {props.spot_size():.2f} µm
        * **Rayleigh range:** {props.rayleigh_length():.3f} mm
        * **Max recommended incidence angle:** {props.max_recommended_angle():.2f} rad
        * **Duty cycle:** {props.duty_cycle() * 100:.1f} %
        * **Strehl ratio at max angle:** {props.strehl_ratio(props.max_recommended_angle()):.2f}
        * **Cross-scan error:** {props.cross_scan_error() * 1000:.2f} µm
        """
    )
    return (props,)


@app.cell
def __(mo):
    angle_slider = mo.ui.slider(
        start=-45,
        stop=45,
        step=1,
        value=-38,
        label="Prism Rotation Angle (degrees)",
    )
    cylinder_toggle = mo.ui.checkbox(value=True, label="Include Cylindrical Lenses")
    mo.hstack([angle_slider, cylinder_toggle], justify="start")
    return angle_slider, cylinder_toggle


@app.cell
def __(PrismScanner, angle_slider, cylinder_toggle, mo):
    scanner = PrismScanner(withcylinder=cylinder_toggle.value)
    hit_range = scanner.find_object("diode")
    focal_dist = scanner.distance_between_cylinders() if cylinder_toggle.value else 0.0

    is_hit = len(hit_range) == 2 and (
        hit_range[0] <= angle_slider.value <= hit_range[1]
    )
    hit_badge = "🟢 Diode illuminated" if is_hit else "⚪ Diode not hit"

    status_text = f"""
    ### Simulation Status ({hit_badge})
    * **Current Angle:** `{angle_slider.value}°`
    * **Photodiode Hit Window:** `{hit_range}` degrees
    * **Cylinder Focal Distance Spacing:** `{focal_dist:.3f} mm`
    """
    mo.md(status_text)
    return focal_dist, hit_badge, hit_range, is_hit, scanner, status_text


if __name__ == "__main__":
    app.run()
