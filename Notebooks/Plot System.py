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
p = PrismScanner(withcylinder=True)

# Let's plot the system for an angle of 10 degrees.

p.plot(-38)

# Let's find the angle at which the mirror is hit

# !pwd

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

# Determine the optimal position of the diode and plot the results

p.focal_point(cyllens1=True, angle=-43, diode=True, plot=True)

p.position_diode

# The goal of the code below was to look for alternative photodiode
# which relied on a reflection when light would normally exit the prism
# as outlined on hackaday, this was not stable enough.
import numpy as np
initial_position = np.array([-20-15,0,0])
delta = 0.2
p.set_orientation('prism', position=initial_position.tolist())
p.plot(35)
start = p.focal_point(cyllens1=True, angle=-42, simple=False, diode=True, plot=False)
# x translation shifts in y and x
p.set_orientation('prism', position=initial_position+np.array([delta, 0, 0]))
delta_x = p.focal_point(cyllens1=True, angle=-42, simple=False, diode=True, plot=False)
# ray propagates in the y-direction, shift in the y direction, shifts in y
p.set_orientation('prism', position=initial_position+np.array([0, delta, 0]))
delta_y = p.focal_point(cyllens1=True, angle=-42, simple=False, diode=True, plot=False)
# z translation should not matter
p.set_orientation('prism', position=initial_position+np.array([0, 0, delta]))
delta_z = p.focal_point(cyllens1=True, angle=-42, simple=False, diode=True, plot=False)
# NOTE: it's too high in x and y, 4.0E-1 equals 400 micron
print(start-delta_x)
print(start-delta_y)
print(start-delta_z)

p.set_orientation('prism', position=initial_position+np.array([0, 10, 0]))
p.focal_point(cyllens1=True, angle=-42, simple=False, diode=True, plot=True)

# In FreeCAD, the coordinates of the optical components are collected.  
# They can be stored to disk and loaded here for debugging purposes.  
# It allows one to visualize, what positions are pushed throught.  

#p.save_system('a.pkl')
p.load_system('temp.pkl')

p.S.complist[p.naming['CL2']]
