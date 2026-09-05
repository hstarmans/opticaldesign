import plotly.graph_objects as go

from prisms.system import PrismScanner
from prisms.viewer import plot_system_plotly


def test_plot_system_plotly_structure():
    """Verify plot_system_plotly produces a valid Figure with meshes and ray lines."""
    p = PrismScanner(withcylinder=True)
    p.plot(-38)
    fig = plot_system_plotly(p.S, title="Test Optical System")

    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0

    # Ensure both Mesh3d (components) and Scatter3d (rays) are present
    types = {trace.type for trace in fig.data}
    assert "mesh3d" in types
    assert "scatter3d" in types

    # Check 1:1:1 scale configuration
    assert fig.layout.scene.aspectmode == "data"


def test_prism_scanner_plotly_methods():
    """Verify PrismScanner plot and show_key_rays methods with plotly backend."""
    p = PrismScanner(withcylinder=True)

    fig_single = p.plot(angle=-38, backend="plotly")
    assert isinstance(fig_single, go.Figure)

    fig_explicit = p.plot_plotly(angle=-35)
    assert isinstance(fig_explicit, go.Figure)

    fig_rays = p.show_key_rays(diode=True, scanline=True, backend="plotly")
    assert isinstance(fig_rays, go.Figure)

    fig_rays_explicit = p.show_key_rays_plotly()
    assert isinstance(fig_rays_explicit, go.Figure)
