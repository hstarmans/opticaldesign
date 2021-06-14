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

hit_angles = p.find_object('diode')
print(hit_angles)

# Let's plot 5 critical rays:
#  - rays which form edges photodiode
#  - rays which form edges scanline
#  - the center ray

p.show_key_rays()

# Let's find the distance between the focal point of the two cylinder lenses.

dist = p.focal_point(cyllens1=True)-p.focal_point(cyllens1=False)
print(f'The distance between focal point cylinder lenses is {dist:.2f} mm')

# In FreeCAD, the coordinates of the optical components are collected.  
# They can be stored to disk and loaded here for debugging purposes.  
# It allows one to visualize, what positions are pushed throught.  

#p.save_system('a.pkl')
p.load_system('temp.pkl')


