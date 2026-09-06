"""Interactive 3D visualization for Hexastorm optical systems.

Delegates directly to pyoptools.gui.plotly_viewer for modern, universal
WebGL 3D visualization.
"""

from pyoptools.gui.plotly_viewer import (
    _extract_ray_segments,
    _generate_lens_side_mesh,
    _transformation_matrix,
    _wavelength_to_color,
    plot_system_plotly,
)

__all__ = [
    "_extract_ray_segments",
    "_generate_lens_side_mesh",
    "_transformation_matrix",
    "_wavelength_to_color",
    "plot_system_plotly",
]
