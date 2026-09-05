"""Interactive 3D visualization for optical systems using Plotly.

Provides a modern, universal WebGL 3D viewer compatible with Marimo,
Jupyter, VS Code Interactive Window, and standalone web exports.
"""

import numpy as np
import plotly.graph_objects as go


def _transformation_matrix(
    translation: tuple[float, float, float], rotation: tuple[float, float, float]
) -> np.ndarray:
    """Creates a 4x4 homogeneous transformation matrix from translation and Euler rotations.

    Rotations are applied in the order: Rx(psi) -> Ry(phi) -> Rz(theta), followed by translation.
    Matches the exact coordinate transform convention in pyOpTools.
    """
    psi, phi, theta = rotation
    Rz = np.array(
        [
            [np.cos(theta), -np.sin(theta), 0.0, 0.0],
            [np.sin(theta), np.cos(theta), 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=float,
    )
    Ry = np.array(
        [
            [np.cos(phi), 0.0, np.sin(phi), 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [-np.sin(phi), 0.0, np.cos(phi), 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=float,
    )
    Rx = np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, np.cos(psi), -np.sin(psi), 0.0],
            [0.0, np.sin(psi), np.cos(psi), 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=float,
    )
    T = np.array(
        [
            [1.0, 0.0, 0.0, translation[0]],
            [0.0, 1.0, 0.0, translation[1]],
            [0.0, 0.0, 1.0, translation[2]],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=float,
    )
    return T @ Rz @ Ry @ Rx


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

    # 1. Render Optical Components with Hierarchical Transformations
    for comp in system.complist:
        component, comp_pos, comp_rot = comp
        T_comp = _transformation_matrix(comp_pos, comp_rot)
        comp_name = type(component).__name__

        # Material styling
        if "Polygon" in comp_name:
            # Elegant optical crown glass (N-BK7) with transparency
            color = "#00B4D8"
            opacity = 0.65
            flatshading = True
        elif "Cylindrical" in comp_name or "Lens" in comp_name:
            color = "#48CAE4"
            opacity = 0.55
            flatshading = False  # Smooth shading for cylindrical curves
        elif "Mirror" in comp_name:
            color = "#D3D3D3"
            opacity = 0.90
            flatshading = True
        elif "CCD" in comp_name or "pd" in str(comp).lower():
            color = "#E76F51"
            opacity = 0.85
            flatshading = True
        else:
            color = "#90E0EF"
            opacity = 0.60
            flatshading = True

        surflist = getattr(component, "surflist", [])
        for surf_idx, surf_item in enumerate(surflist):
            if isinstance(surf_item, (list, tuple)) and len(surf_item) == 3:
                surf_obj, surf_pos, surf_rot = surf_item
            else:
                surf_obj, surf_pos, surf_rot = (
                    surf_item,
                    (0.0, 0.0, 0.0),
                    (0.0, 0.0, 0.0),
                )

            if not hasattr(surf_obj, "polylist"):
                continue

            pts, polys = surf_obj.polylist()
            pts = np.array(pts, dtype=float)
            polys = np.array(polys, dtype=int)
            if len(pts) == 0 or len(polys) == 0:
                continue

            # Composite 4x4 matrix: World = T_comp @ T_surface
            T_surf = _transformation_matrix(surf_pos, surf_rot)
            T_total = T_comp @ T_surf

            pts_4d = np.hstack([pts, np.ones((len(pts), 1), dtype=float)])
            world_pts = (T_total @ pts_4d.T).T[:, :3]

            # Reflection facet highlight on polygon
            facet_color = (
                "#F77F00" if getattr(surf_obj, "reflectivity", 0) == 1 else color
            )

            mesh = go.Mesh3d(
                x=world_pts[:, 0],
                y=world_pts[:, 1],
                z=world_pts[:, 2],
                i=polys[:, 0],
                j=polys[:, 1],
                k=polys[:, 2],
                name=f"{comp_name} ({surf_idx})",
                color=facet_color,
                opacity=opacity,
                flatshading=flatshading,
                lighting={
                    "ambient": 0.7,
                    "diffuse": 0.9,
                    "roughness": 0.1,
                    "specular": 0.8,
                    "fresnel": 0.4,
                },
                lightposition={"x": 100, "y": 200, "z": 500},
                hoverinfo="name",
                showlegend=False,
            )
            traces.append(mesh)

    # 2. Render Propagated Rays with High-Visibility Neon Glow
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
            line={"color": "#FF007F", "width": 5},  # High-visibility neon beam
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
            "aspectmode": "data",  # Guaranteed true 1:1:1 optical scale
            "xaxis": {
                "title": "X (mm)",
                "gridcolor": "#E5E7EB" if not dark_mode else "#333333",
            },
            "yaxis": {
                "title": "Y (mm)",
                "gridcolor": "#E5E7EB" if not dark_mode else "#333333",
            },
            "zaxis": {
                "title": "Z (mm)",
                "gridcolor": "#E5E7EB" if not dark_mode else "#333333",
            },
            "camera": {
                "eye": {"x": -1.6, "y": -1.6, "z": 1.3},
                "up": {"x": 0, "y": 0, "z": 1},
            },
        },
        margin={"l": 10, "r": 10, "b": 10, "t": 50},
        legend={"x": 0.02, "y": 0.98},
    )
    return fig
