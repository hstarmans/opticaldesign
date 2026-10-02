import logging
import pickle
from copy import deepcopy
from math import pi

import numpy as np
from pyoptools.all import (
    CCD,
    CylindricalLens,
    IdealLens,
    Plot3D,
    Ray,
    RectMirror,
    System,
    material,
    nearest_points,
)
from pyoptools.raytrace.shape.rectangular import Rectangular

from prisms.analytical import PrismProperties
from prisms.library import Polygon

logger = logging.getLogger(__name__)


def _target_is_hit(target):
    """Check whether a component or any of its constituent surfaces was hit by a ray."""
    if hasattr(target, "hit_list") and len(target.hit_list) > 0:
        return True
    if hasattr(target, "surflist"):
        for surf_tuple in target.surflist.values():
            surf = surf_tuple[0]
            if hasattr(surf, "hit_list") and len(surf.hit_list) > 0:
                return True
    return False


class PrismScanner:
    """Defines optical system for a prism scanner."""

    def __init__(self, wavelength=0.405, withcylinder=True, **kwargs):
        """Defines optical system.

        Laser propagates in the y-direction with specified wavelength [microns].
        The system can be constructed with or without cylinder lenses.
        The prism is centered at (x, y, z) = (0, 0, laser_height).

        Parameters:
            wavelength   -- wavelength of laser [microns] (default: 0.405)
            withcylinder -- whether the system uses cylinder lenses
            compact      -- legacy alias: if True, sets withcylinder=False
        """
        if "compact" in kwargs:
            withcylinder = not kwargs.pop("compact")
        self.withcylinder = withcylinder
        self.position_diode = (60, 38, 0)
        self.wavelength = wavelength
        self.p = PrismProperties()

        # Component naming map to indices
        if self.withcylinder:
            self.naming = {
                "CL1": "C0",
                "prism": "C1",
                "CL2": "C2",
                "ccd": "C3",
                "mirror": "C4",
                "diode": "C5",
            }
        else:
            self.naming = {
                "lens": "C0",
                "prism": "C1",
                "mirror": "C2",
                "diode": "C3",
            }

        # Default chief ray properties
        self.ray_prop = {
            "pos": [0, -40, 0],
            "dir": [0, 1, 0],
            "wavelength": self.wavelength,
        }

        # Default 3D view settings for Plot3D rendering
        self.view_set = {
            "center": (0, 0, 0),
            "size": (150, 150),
            "scale": 3,
            "rot": [(0, 0, 0)],
        }

        self.S = self.system()

    def _make_ray(self, origin=None, direction=None, wavelength=None):
        """Create a Ray instance compatible across pyoptools versions."""
        pos = list(origin) if origin is not None else list(self.ray_prop["pos"])
        dir_vec = (
            list(direction) if direction is not None else list(self.ray_prop["dir"])
        )
        wl = wavelength if wavelength is not None else self.ray_prop["wavelength"]
        try:
            return Ray(origin=pos, direction=dir_vec, wavelength=wl)
        except TypeError:
            return Ray(pos=pos, dir=dir_vec, wavelength=wl)

    def system(self):
        """Defines the optical system using pyoptools.

        System is ordered by distance from optical source (closest first).
        """
        # Cylinder Lens 1 (Edmund Optics 68-048)
        cl_lens1 = CylindricalLens(
            size=(12.5, 25),
            thickness=2,
            curvature_s1=1.0 / 38.76,
            curvature_s2=0,
            material=material.schott["N-BK7"],
        )

        ideal_lens = IdealLens(shape=Rectangular(size=(5, 5)), f=60)

        # Polygon Prism Scanner
        prism = Polygon(
            sides=4,
            height=2,
            inner_radius=15,
            material=material.schott["N-BK7"],
        )

        # Cylinder Lens 2 (Edmund Optics 68-046)
        cl_lens2 = CylindricalLens(
            size=(12.5, 25),
            thickness=3,
            curvature_s1=1.0 / 12.92,
            curvature_s2=0,
            material=material.schott["N-BK7"],
        )

        # Mirror (Rectangular, 10x10x2 mm, coated on one side)
        m1 = RectMirror(size=(10, 10, 2), reflectivity=1)

        # Photodiode BPW34
        pd = RectMirror(size=(5.4, 4, 0.01), reflectivity=0)

        # CCD camera for focal plane visualization
        ccd = CCD()

        if self.withcylinder:
            self.position_diode = (35, 25, 0)
            complist = [
                (cl_lens1, (0, -29, 0), (-0.5 * pi, 0, 0)),
                (prism, (0, 0, 0), (0, 0, 0)),
                (cl_lens2, (6, 31, 0), (0, -0.5 * pi, -0.5 * pi)),
                (ccd, (0, 50, 0), (0.5 * pi, 0.5 * pi, 0)),
                (m1, (-11, 25, 0), (0.5 * pi, 0.5 * pi, 0.25 * pi + pi)),
                (pd, self.position_diode, (0.5 * pi, 0.5 * pi, 0.5 * pi)),
            ]
        else:
            self.position_diode = (60, 38, 0)
            complist = [
                (ideal_lens, (0, -26, 0), (0.5 * pi, 0, 0)),
                (prism, (0, 0, 0), (0, 0, 0)),
                (m1, (-11, 38, 0), (0.5 * pi, 0.5 * pi, 0.25 * pi + pi)),
                (pd, self.position_diode, (0.5 * pi, 0.5 * pi, 0.5 * pi)),
            ]

        sys_obj = System(complist=complist, n=1)
        return sys_obj

    def set_orientation(self, comp, position=None, rotation=None, reset=True):
        """Place optical component at position and rotation.

        Parameters:
            comp     -- name of component ('CL1', 'prism', 'CL2', 'mirror', 'diode')
            position -- [x, y, z] position coordinates
            rotation -- [rx, ry, rz] rotation angles in radians
            reset    -- whether to reset system rays before propagating
        """
        target = self.S.complist[self.naming[comp]]
        comp_obj = target[0]
        old_pos = target[1]
        old_rot = target[2]

        new_pos = tuple(position) if position is not None else old_pos
        new_rot = tuple(rotation) if rotation is not None else old_rot

        self.S.complist[self.naming[comp]] = (comp_obj, new_pos, new_rot)

        # If cylinder 2 is moved, update CCD position to new focal point
        if comp == "CL2" and position is not None and "ccd" in self.naming:
            f_vec = self.focal_point(cyllens1=False, simple=False)
            ccd_target = self.S.complist[self.naming["ccd"]]
            if self.withcylinder:
                new_ccd_pos = (0.0, float(f_vec[1]), 0.0)
            else:
                new_ccd_pos = (float(f_vec[0]), 0.0, 0.0)
            self.S.complist[self.naming["ccd"]] = (
                ccd_target[0],
                new_ccd_pos,
                ccd_target[2],
            )
        if comp == "CL2" and rotation is not None:
            raise ValueError("Rotation of CL2 is not supported")

        if reset:
            self.S.reset()
        self.S.ray_add(self._make_ray())
        self.S.propagate()

    def distance_between_cylinders(self):
        """Returns distance between the focal points of both cylinder lenses in mm."""
        return self.focal_point(cyllens1=True) - self.focal_point(cyllens1=False)

    def focal_point(self, cyllens1=True, angle=0, simple=True, diode=False, plot=False):
        """Returns focal point of cylinder lens and optionally positions photodiode.

        Parameters:
            cyllens1 -- True for cylinder lens 1, False for cylinder lens 2
            angle    -- prism rotation angle in degrees
            simple   -- True to return only x-coordinate, False for (x, y, z)
            diode    -- whether to update diode position to focal point
            plot     -- True to return Plot3D visualization
        """
        dct1 = deepcopy(self.ray_prop)
        dct2 = deepcopy(self.ray_prop)

        # Cylinder 1 focuses parallel to prism (x-direction)
        # Cylinder 2 focuses orthogonal to cylinder (z-direction)
        if cyllens1:
            dct1["pos"][0] += 0.5
            dct2["pos"][0] -= 0.5
        else:
            dct1["pos"][2] += 0.5
            dct2["pos"][2] -= 0.5

        def trace_pair():
            self.S.reset()
            self.set_orientation("prism", rotation=(0, 0, np.radians(angle)))
            ray1 = self._make_ray(
                origin=dct1["pos"], direction=dct1["dir"], wavelength=dct1["wavelength"]
            )
            ray2 = self._make_ray(
                origin=dct2["pos"], direction=dct2["dir"], wavelength=dct2["wavelength"]
            )
            self.S.ray_add(ray1)
            self.S.ray_add(ray2)
            self.S.propagate()
            return ray1, ray2

        # Temporarily isolate CCD so it never intercepts rays during focal point determination
        old_ccd = None
        if "ccd" in self.naming and self.naming["ccd"] in self.S.complist:
            old_ccd = self.S.complist[self.naming["ccd"]]
            del self.S.complist[self.naming["ccd"]]

        try:
            ray1, ray2 = trace_pair()

            final_rays_1 = ray1.get_final_rays()
            final_rays_2 = ray2.get_final_rays()
            if not final_rays_1 or not final_rays_2:
                raise RuntimeError("Rays did not reach final optical interface")

            focal_coords = nearest_points(final_rays_1[0], final_rays_2[0])[0]

            if diode:
                self.position_diode = focal_coords
                self.set_orientation("diode", position=self.position_diode)
                ray1, ray2 = trace_pair()

            dist = focal_coords[0] if simple else focal_coords

            if plot:
                return Plot3D(self.S, **self.view_set)
            return dist
        finally:
            if old_ccd is not None:
                self.S.complist[self.naming["ccd"]] = old_ccd

    def save_system(self, fname):
        """Save the optical system and chief ray properties to disk."""
        with open(fname, "wb") as file:
            pickle.dump([self.ray_prop, self.S], file)

    def load_system(self, fname):
        """Load an optical system from disk."""
        with open(fname, "rb") as file:
            self.ray_prop, self.S = pickle.load(file)

    def plot(self, angle=0, backend="plotly", **kwargs):
        """Plot the system with a traced ray at given prism rotation angle.

        Parameters:
            angle: Prism rotation angle in degrees.
            backend: 'plotly' (default, modern interactive WebGL) or 'auto'.
        """
        self.S.reset()
        self.S.ray_add(self._make_ray())
        self.S.propagate(100)
        self.set_orientation("prism", rotation=(0, 0, np.radians(angle)))
        if backend == "plotly":
            from prisms.viewer import plot_system_plotly

            title = kwargs.pop("title", f"Hexastorm Prism Scanner (Angle: {angle}°)")
            return plot_system_plotly(self.S, title=title, **kwargs)
        return Plot3D(self.S, **self.view_set)

    def plot_plotly(self, angle=0, **kwargs):
        """Convenience method to explicitly generate a Plotly 3D visualization."""
        return self.plot(angle=angle, backend="plotly", **kwargs)

    def draw_key_rays(self, diode=True, scanline=True):
        """Trace chief rays for scanline edges and photodiode hits."""
        angles = []
        if diode:
            diode_angles = self.find_object("diode")
            if not diode_angles:
                logger.warning("Cannot hit diode with laser at current orientation.")
            angles.extend(diode_angles)

        if scanline:
            max_scan_angle = np.degrees(self.p.max_recommended_angle())
            angles.extend([-max_scan_angle, max_scan_angle, 0.0])

        self.S.reset()
        logger.info("Drawing key rays for prism angles: %s", angles)
        for ang in angles:
            self.set_orientation("prism", rotation=(0, 0, np.radians(ang)), reset=False)

    def show_key_rays(self, diode=True, scanline=True, backend="plotly", **kwargs):
        """Draw key rays and return 3D plot widget (Plotly)."""
        self.draw_key_rays(diode, scanline)
        if backend == "plotly":
            from prisms.viewer import plot_system_plotly

            title = kwargs.pop("title", "Hexastorm Prism Scanner - Key Rays")
            return plot_system_plotly(self.S, title=title, **kwargs)
        return Plot3D(self.S, **self.view_set)

    def show_key_rays_plotly(self, diode=True, scanline=True, **kwargs):
        """Convenience method to explicitly generate a Plotly 3D visualization of key rays."""
        return self.show_key_rays(
            diode=diode, scanline=scanline, backend="plotly", **kwargs
        )

    def find_object(self, name):
        """Determines minimum and maximum scan angle where target object is hit.

        Returns [low_angle, high_angle] in degrees, or [] if not hit.
        """
        low_angle = None if self.withcylinder else 0
        hit_angles = []
        target = self.S.complist[self.naming[name]][0]
        max_angle = round(float(np.degrees(self.p.max_angle_incidence())))

        if low_angle is None:
            low_angle = -max_angle
        else:
            logger.info("Low search angle fixed at %d degrees", low_angle)

        # Coarse sweep
        for angle in range(low_angle, max_angle, 1):
            self.set_orientation("prism", rotation=(0, 0, np.radians(angle)))
            if _target_is_hit(target):
                hit_angles.append(angle)

        if not hit_angles:
            return hit_angles

        # Fine boundary refinement
        low = float(min(hit_angles))
        high = float(max(hit_angles))

        refining_low = True
        while refining_low and low > -90.0:
            self.set_orientation("prism", rotation=(0, 0, np.radians(low - 0.1)))
            if _target_is_hit(target):
                low -= 0.1
            else:
                refining_low = False

        refining_high = True
        while refining_high and high < 90.0:
            self.set_orientation("prism", rotation=(0, 0, np.radians(high + 0.1)))
            if _target_is_hit(target):
                high += 0.1
            else:
                refining_high = False

        return [round(low, 2), round(high, 2)]
