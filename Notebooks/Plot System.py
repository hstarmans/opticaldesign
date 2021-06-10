# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.11.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

from pyoptools.all import Plot3D
from math import pi
from prisms.system import PrismScanner
p = PrismScanner()

# Let's plot the system for an angle of 10 degrees.

p.plot(10)

# Let's find the angle at which the mirror is hit

hit_angles = p.find_mirror()
print(hit_angles)

# Let's plot 5 critical rays:
#  - ray which hits left side of mirror
#  - ray which hits right side of mirror
#  - ray which forms left side of scanline
#  - ray which forms right side of scanline
#  - the center ray

p.show_five_rays()

# As FreeCAD modifies the system, its state can be stored from there
# and loaded here.

p.save_system('test.pkl')
p.load_system('test.pkl')

# In FreeCAD, the thickness of the cylindrical lens is required to
# send over the correct position.

p.S.complist[p.naming['CL1']][0].thickness
