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
p = PrismScanner(compact=True)

# The code has been updated so it is possible to plot a reflection on the second prism surface.

p.plot(33, reflection=True)

# You can also calculate the ideal position of the photodiode.
# The signal can also be into the direction of the laserdiode.

p.focal_point(cyllens1=True, angle=42, simple=False, plot=True)

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

snell(np.radians(30), 1, 1.5)

# Reflected light on the second surface, is according to Fresnell. At a 30 degrees rotation angle.

from sympy.physics.optics import fresnel_coefficients, critical_angle
sum([abs(x)**2 for x in fresnel_coefficients(0.33, 1.5, 1)[:2]])/2

# All light can be reflected at second surface, the critical angle cannot be reached. The reflected angle is smaller than the incident angle.
# The critical angle is 41 degrees. The maximum refracted angle is 28 degrees.

print(np.degrees(snell(np.radians(45), 1, 1.5)))
print(critical_angle(1.5, 1)/(2*np.pi)*360)

