import logging

import numpy as np
from pyoptools.raytrace.component import Component
from pyoptools.raytrace.shape import Polygon as ShapePolygon, Rectangular
from pyoptools.raytrace.surface import Plane

logger = logging.getLogger(__name__)


class Polygon(Component):
    """Defines a regular polygon prism component.

    The center of mass of the polygon is positioned at the origin.

    Parameters:
        sides        -- number of sides (facets)
        height       -- height of polygon [mm]
        inner_radius -- inner radius (apothem) of polygon [mm]
        reflection   -- whether ray is reflected when it exits the prism
    """

    def __init__(self, sides=4, height=3, inner_radius=10, reflection=False, **traits):
        if sides < 3:
            raise ValueError("Polygon should have at least 3 sides.")
        if sides % 2 == 1:
            logger.warning("Polygon needs an even number of sides for scanning.")

        side_length = 2 * inner_radius * np.tan(np.pi / sides)
        super().__init__(**traits)

        # Create vertical facet surfaces
        for i in range(sides):
            angle = 2 * np.pi / sides * i
            center = inner_radius * np.array([np.cos(angle), np.sin(angle)])
            if (i == 1) and reflection:
                side = Plane(
                    shape=Rectangular(size=(side_length, height)),
                    reflectivity=1,
                )
            else:
                side = Plane(shape=Rectangular(size=(side_length, height)))

            self.surflist[f"S{i}"] = (
                side,
                (float(center[0]), float(center[1]), 0.0),
                (np.pi / 2, 0.0, angle + np.pi / 2),
            )

        # Compute counter-clockwise vertex coordinates for the regular polygon cross-section
        r_vertex = inner_radius / np.cos(np.pi / sides)
        poly_coords = []
        for i in range(sides):
            angle = 2 * np.pi / sides * i - np.pi / sides
            poly_coords.append((r_vertex * np.cos(angle), r_vertex * np.sin(angle)))
        poly_coords = tuple(poly_coords)

        # Create single watertight bottom and top cap surfaces
        bottom_cap = Plane(shape=ShapePolygon(coord=poly_coords))
        top_cap = Plane(shape=ShapePolygon(coord=poly_coords))

        self.surflist[f"S{sides}"] = (
            bottom_cap,
            (0.0, 0.0, -height / 2.0),
            (0.0, 0.0, 0.0),
        )
        self.surflist[f"S{sides + 1}"] = (
            top_cap,
            (0.0, 0.0, height / 2.0),
            (0.0, 0.0, 0.0),
        )
