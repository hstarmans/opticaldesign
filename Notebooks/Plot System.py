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
from system import PrismScanner
p = PrismScanner()

p.plot()

p.plot()

# It is not possible to load cylindrical lenses directly from Edmund optics library.
# Cylinder lenses are implemented without side surface.

# System with ray
S.ray_add(Ray(pos=[0,0,0], dir=[0,1,0], wavelength=405))
S.propagate()
Plot3D(S,center=(0,0,150),size=(250,100),scale=3,rot=[(0,0,0)])

# +
import numpy as np
hit_angle = []
failed = []
for angle in range(-90,90):
    S.complist['C1'][-1][-1] = np.radians(angle)
    S.reset()
    S.ray_add(Ray(pos=[0,0,0], dir=[0,1,0], wavelength=405))
    S.propagate()
    if angle == 20:
        Plot3D(S,center=(0,0,150),size=(250,100),scale=3,rot=[(0,0,0)])
    if len(M1.hit_list): 
        hit_angle.append(angle)
    else:
        failed.append(angle)
print(hit_angle)
# what do you want to know at minimum

# at which angle does the ray hit the mirror?
#  if len(M1.hitlst): --> hit
# if there is a hit --> you have have an intersection, you can collect it from hit list
# where is the start and the end of the scanline, show in FreeCad

# -

S.complist['C1'][-1][-1] = np.radians(-16)
S.reset()
S.ray_add(Ray(pos=[0,0,0], dir=[0,1,0], wavelength=405))
S.propagate()
Plot3D(S,center=(0,0,150),size=(250,100),scale=3,rot=[(0,0,0)])

dir()

S.complist

S.values()

S.update()



# # Limitations model
#
# G2 lens specs can be found online....  
#   6.33mm diameter, 5.3mm front surface, 4.0mm focal length  
# Working Distance: ~2.4mm from laser diode  
# Several issues  
#     - requires you to know aspheric coefficients AND divergence / sice point  
#     - mitigated by assuming parallel bundle  
#
# # Limitations Pyoptools
#  - It the prism exactly hits an edge corner, it does not know what to do and does not throw an error.
#  - cylindrical lenses, do not have side surfaces in pyoptools
#  - it is not possible to load cylindrical lenses directly from Edmund library

# execute update
S.update()
Plot3D(S,center=(0,0,150),size=(250,100),scale=3,rot=[(0,0,0)])


