# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.13.7
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

from pyoptools.all import Plot3D
from math import pi
from prisms.system import PrismScanner
p = PrismScanner(compact=True, reflection=False)

# The code has been updated so it is possible to plot a reflection on the second prism surface.
# There are two domains; above 40 degrees (bundle will reflect back) or below 40 degrees (sideways).

#p.set_orientation('prism', position=[0, 0, 0.2])
p.plot(-35)

# You can also calculate the ideal position of the photodiode and place the diode there.  
# There are two ideal positions; one on the box side and the other at the same place as the laser diode.

p.focal_point(cyllens1=True, angle=43, simple=False, diode=True, plot=True)

# The diode must be positioned for this to work.
# Draw the rays which hit the edges of the photo-diode.

p.show_key_rays(scanline=False)

# The edges of the scanline cannot be drawn in the same image.

diode_pos = p.position_diode
p = PrismScanner(compact=True)
p.position_diode = diode_pos
p.S = p.system()
p.show_key_rays(diode=False)

# Let's calculate the amount of reflected light. The angle of incidence equals the rotation angle.
# The refracted angle can be calculated from Snell's law.

import numpy as np
def snell(theta_inc, n1, n2):
    """
    Compute the refraction angle using Snell's Law.

    See https://en.wikipedia.org/wiki/Snell%27s_law

    Parameters
    ----------
    theta_inc : float
        Incident angle in radians.
    n1, n2 : float
        The refractive index of medium of origin and destination medium.

    Returns
    -------
    theta : float
        refraction angle

    Examples
    --------
    A ray enters an air--water boundary at pi/4 radians (45 degrees).
    Compute exit angle.

    >>> snell(np.pi/4, 1.00, 1.33)
    0.5605584137424605
    """
    return np.arcsin(n1 / n2 * np.sin(theta_inc))


# For a rotation angle of 30 degrees, I get a refracted angle.

snell(np.radians(42), 1, 1.5)

# Reflected light on the second surface, is according to Fresnell. At a 30 degrees rotation angle.

from sympy.physics.optics import fresnel_coefficients, critical_angle
sum([abs(x)**2 for x in fresnel_coefficients(0.46, 1.5, 1)[:2]])/2

# All light can be reflected if you can go from a dense medium to a less dense medium. The transition from quartz to air.  
# The critical angle cannot be reached. The reflected angle is smaller than the incident angle.  
# The critical angle is 41 degrees. The maximum refracted angle is 28 degrees.

print(np.degrees(snell(np.radians(45), 1, 1.5)))
print(critical_angle(1.5, 1)/(2*np.pi)*360)

# In the new system, the rotation axis might not be fixed at the center.  
# Let's say the rotational axis is displaced from the center.  
# The systems is sensitive to delta translation in x and y, this leads to ghosting.

initial_position = np.array([0,0,0])
delta = -0.02
p.set_orientation('prism', position=initial_position.tolist())
p.plot(35)
start = p.focal_point(cyllens1=True, angle=43, simple=False, diode=True, plot=False)
# x translation shifts in y and x
p.set_orientation('prism', position=initial_position+np.array([delta, 0, 0]))
delta_x = p.focal_point(cyllens1=True, angle=43, simple=False, diode=True, plot=False)
# ray propagates in the y-direction, shift in the y direction, shifts in y
p.set_orientation('prism', position=initial_position+np.array([0, delta, 0]))
delta_y = p.focal_point(cyllens1=True, angle=43, simple=False, diode=True, plot=False)
# z translation should not matter
p.set_orientation('prism', position=initial_position+np.array([0, 0, delta]))
delta_z = p.focal_point(cyllens1=True, angle=43, simple=False, diode=True, plot=False)
# NOTE: it's too high in x and y, 4.0E-1 equals 400 micron
print(start-delta_x)
print(start-delta_y)
print(start-delta_z)

p.load_system('temp.pkl')

from pyoptools.all import (CylindricalLens, Ray, RectMirror, CCD, IdealLens,
                           material, System, Plot3D, nearest_points, Shape)

from pyoptools.raytrace.shape.rectangular import Rectangular

Rectangular(size=(5,5))

# !jupytext --to py system_compact.ipynb

# !jupytext --to notebook Plot\ System.py

p.set_orientation('prism', position=initial_position+np.array([0, 0, 0]))
p.focal_point(cyllens1=True, angle=43, simple=False, diode=True, plot=True)


