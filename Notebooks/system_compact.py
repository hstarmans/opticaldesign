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

p.plot(30, reflection=True)

# You can also calculate the ideal position of the photodiode.
# The signal can also be into the direction of the laserdiode.

p.focal_point(cyllens1=True, angle=42, simple=False, plot=True)
