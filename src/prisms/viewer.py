"""Interactive 3D visualization for optical systems using Plotly.

Provides a modern, universal WebGL 3D viewer compatible with Marimo,
Jupyter, VS Code Interactive Window, and standalone web exports.
"""

import numpy as np
import plotly.graph_objects as go


def _rotation_matrix(psi: float, phi: float, theta: float) -> np.ndarray:
    """Compute 3D rotation matrix from Euler angles (psi, phi, theta) in radians."""
    Rz = np.array(
        [
            [np.cos(theta), -np.sin(theta), 0.0],
            [np.sin(theta), np.cos(theta), 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    Ry = np.array(
        [
            [np.cos(phi), 0.0, np.sin(phi)],
            [0.0, 1.0, 0.0],
            [-np.sin(phi), 0.0, np.cos(phi)],
        ]
    )
    Rx = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, np.cos(psi), -np.sin(psi)],
            [0.0, np.sin(psi), np.cos(psi)],
        ]
    )
    return Rz @ Ry @ Rx


def _extract_ray_segments(ray) -> list[tuple[np.ndarray, np.ndarray]]:
    """Recursively extracts line segments from a pyoptools ray and its children."""
    segments = []
    p1 = np.array(ray.origin, dtype=float)
    if len(ray.childs) > 0:
        p2 = np.array(ray.childs[0].origin, dtype=float)
    else:
        p2 = p1 + 15.0 * np.array(ray.direction, dtype=float)

    if getattr(ray, "intensity", 1.0) != 0:
        segments.append((p1, p2))

    for child in ray.childs:
        segments.extend(_extract_ray_segments(child))
    return segments


def plot_system_plotly(
    system,
    title: str = "Hexastorm Optical System (3D View)",
    dark_mode: bool = False,
    width: int = 900,
    height: int = 550,
) -> go.Figure:
    """Creates an interactive 3D WebGL visualization of an optical system using Plotly.

    Parameters:
        system: pyoptools System object containing components and rays.
        title: Title of the visualization plot.
        dark_mode: If True, uses dark background theme.
        width: Plot width in pixels.
        height: Plot height in pixels.

    Returns:
        plotly.graph_objects.Figure ready to display in Marimo or Jupyter.
    """
    traces = []

    # 1. Render Optical Components
    for comp in system.complist:
        component, position, rotation = comp
        rot_matrix = _rotation_matrix(*rotation)
        pos = np.array(position, dtype=float)
        comp_name = type(component).__name__

        # Assign material styling based on component type
        if "Mirror" in comp_name:
            color = "#ADB5BD"
            opacity = 0.85
        elif "CCD" in comp_name or "pd" in str(comp).lower():
            color = "#E76F51"
            opacity = 0.90
        elif "Cylindrical" in comp_name or "Lens" in comp_name:
            color = "#48CAE4"
            opacity = 0.45
        elif "Polygon" in comp_name:
            color = "#0077B6"
            opacity = 0.50
        else:
            color = "#90E0EF"
            opacity = 0.50

        if hasattr(component, "surflist"):
            for surf_name, surf_data in component.surflist.items():
                surf = (
                    surf_data[0] if isinstance(surf_data, (list, tuple)) else surf_data
                )
                if not hasattr(surf, "polylist"):
                    continue
                pts, polys = surf.polylist()
                pts = np.array(pts, dtype=float)
                polys = np.array(polys, dtype=int)
                if len(pts) == 0 or len(polys) == 0:
                    continue

                # Transform to global world coordinates
                world_pts = (rot_matrix @ pts.T).T + pos

                mesh = go.Mesh3d(
                    x=world_pts[:, 0],
                    y=world_pts[:, 1],
                    z=world_pts[:, 2],
                    i=polys[:, 0],
                    j=polys[:, 1],
                    k=polys[:, 2],
                    name=f"{comp_name} ({surf_name})",
                    color=color,
                    opacity=opacity,
                    flatshading=True,
                    lighting={
                        "ambient": 0.6,
                        "diffuse": 0.8,
                        "roughness": 0.5,
                        "specular": 0.4,
                    },
                    hoverinfo="name",
                    showlegend=False,
                )
                traces.append(mesh)

    # 2. Render Propagated Rays
    rx, ry, rz = [], [], []
    for ray in getattr(system, "prop_ray", []):
        for p1, p2 in _extract_ray_segments(ray):
            rx.extend([p1[0], p2[0], None])
            ry.extend([p1[1], p2[1], None])
            rz.extend([p1[2], p2[2], None])

    if rx:
        ray_trace = go.Scatter3d(
            x=rx,
            y=ry,
            z=rz,
            mode="lines",
            line={"color": "#B5179E", "width": 4},
            name="Laser Beam (405 nm)",
            hoverinfo="name",
            showlegend=True,
        )
        traces.append(ray_trace)

    # 3. Configure Camera & True 1:1:1 Scale
    template = "plotly_dark" if dark_mode else "plotly_white"
    fig = go.Figure(data=traces)
    fig.update_layout(
        title={"text": title, "x": 0.05, "y": 0.95},
        template=template,
        width=width,
        height=height,
        scene={
            "aspectmode": "data",  # Crucial for optics: guarantees true 1:1:1 geometric scale
            "xaxis": {
                "title": "X (mm)",
                "gridcolor": "#E0E0E0" if not dark_mode else "#333333",
            },
            "yaxis": {
                "title": "Y (mm)",
                "gridcolor": "#E0E0E0" if not dark_mode else "#333333",
            },
            "zaxis": {
                "title": "Z (mm)",
                "gridcolor": "#E0E0E0" if not dark_mode else "#333333",
            },
            "camera": {
                "eye": {"x": -1.5, "y": -1.5, "z": 1.2},
                "up": {"x": 0, "y": 0, "z": 1},
            },
        },
        margin={"l": 10, "r": 10, "b": 10, "t": 50},
        legend={"x": 0.02, "y": 0.98},
    )
    return fig
