from math import pi
import pickle

import numpy as np
from pyoptools.all import (CylindricalLens, Ray, RectMirror,
                           material, System, Plot3D)

from prisms.library import Polygon
from prisms.analytical import Prism_properties


class PrismScanner():
    '''defines a prism scanner'''
    def __init__(self, wavelength=0.405):
        '''instantiate optical system

        wavelength -- wavelength of the laser in microns
        '''
        self.S = self.system()
        self.wavelength = wavelength
        self.p = Prism_properties()
        # converts name to position
        # CL is cylinder lens
        self.naming = {'CL1': 'C0',
                       'prism': 'C1',
                       'CL2': 'C2',
                       'mirror': 'C3',
                       'diode': 'C4'}
        # default properties chief ray
        self.ray_prop = {'pos': [10, 0, 0],
                         'dir': [-1, 0, 0],
                         'wavelength': self.wavelength}
        # default view settings for py3js renders
        self.view_set = {'center': (0, 0, 0),
                         'size': (150, 150),
                         'scale': 3,
                         # rotation is broken, doesn't work well
                         'rot': [(0, 0, 0)]}

    def system(self):
        '''defines optical system using pyoptools

        System is ordered upon distance from optical source.
        Closest component comes first.
        '''
        # Cylinder LENS 1 Edmund optics 68-048
        # BFL + CT = 73.68 + 2 = 75.68
        CL_lens1 = CylindricalLens(size=(12.5, 25),
                                   thickness=2,
                                   curvature_s1=1./75.68,
                                   curvature_s2=0,
                                   material=material.schott["N-BK7"])

        # Prism
        prism = Polygon(sides=4,
                        height=2,
                        inner_radius=15,
                        material=material.schott["N-BK7"])

        # Cylinder LENS 2 Edmund optics 68-046
        # BFL + CT = 23.02 + 3
        CL_lens2 = CylindricalLens(size=(12.5, 25),
                                   thickness=3,
                                   curvature_s1=1./26.02,
                                   curvature_s2=0,
                                   material=material.schott["N-BK7"])

        # Mirror
        # Mirror is actually 2 mm thick, but want to prevent
        # hitting side is counted as hit
        M1 = RectMirror(size=(10, 10, 0.01),
                        reflectivity=1)

        # Photodiode BPW34
        # Photiodiode is actually 3.2 mm thick, but want to prevent
        # hitting side is counted as hit
        PD = RectMirror(size=(5.4, 4, 0.01),
                        reflectivity=1)

        # Optical system
        # This rotation as this simplifies interaction with FreeCAD
        # Here the laser points in the -x direction
        # I am not able to rotate ThreeJS view in Z, so it is not optimal
        complist = [(CL_lens1, (0, 0, 0), (0.5*pi, 0, -0.5*pi)),
                    (prism, (-10-15, 0, 0), (0, 0, 0)),
                    (CL_lens2, (-50, 0, 0), (0.5*pi, 0.5*pi, -0.5*pi)),
                    (M1, (-60, -10, 0), (0.5*pi, 0.5*pi, 0.25*pi)),
                    (PD, (-60, -20, 0), (0.5*pi, 0.5*pi, 0))]
        S = System(complist=complist, n=1)
        return S

    def set_orientation(self, comp, position=None, rotation=None, reset=True):
        '''place comp at position and rotation

           comp     -- name of component; CL1, prism, CL2, mirror
           position -- [x, y, z] position of component
           rotation -- [rx, ry, rz] rotation of component
        '''
        target = self.S.complist[self.naming[comp]]
        if position is not None:
            target[-2][:] = position
        if rotation is not None:
            target[-1][:] = rotation
        if reset:
            self.S.reset()
        self.S.ray_add(Ray(**self.ray_prop))
        self.S.propagate()

    def save_system(self, fname):
        '''save the system

           It is hard to save threejs plot objects as
           image, as a result this is used.

           fname -- filename to save system to
        '''
        with open(fname, 'wb') as file:
            pickle.dump(self.S, file)

    def load_system(self, fname):
        '''plot the system with a ray

           fname -- filename to load system from
        '''
        with open(fname, 'rb') as file:
            self.S = pickle.load(file)

    def plot(self, angle=0, save=False):
        '''plot the system with a ray

           angle -- rotation angle in degrees of prism
        '''
        self.set_orientation('prism', rotation=(0, 0, np.radians(angle)))
        self.S.ray_add(Ray(**self.ray_prop))
        self.S.propagate()
        return Plot3D(self.S,
                      **self.view_set)

    def draw_key_rays(self):
        '''draws six chief rays

           chief rays which hit sides mirror
           chief rays which hit side scanline
           chief rays which hit side photodiode
           chief rays which are unperturbered
        '''
        mirror_angles = self.find_object('mirror')
        if mirror_angles:
            diode_angles = self.find_object('diode')
            if not diode_angles:
                print("Can't hit diode with laser")
            else:
                mirror_angles += diode_angles
        else:
            print("Can't hit mirror with laser")

        max_scan_angle = np.degrees(self.p.max_recommended_angle())
        scan_angles = [-max_scan_angle, max_scan_angle, 0]
        self.S.reset()
        lst = mirror_angles + scan_angles
        for angle in lst:
            self.set_orientation('prism',
                                 rotation=(0, 0, np.radians(angle)),
                                 reset=False)

    def show_key_rays(self):
        '''draws five chief rays and returns plot'''
        self.draw_key_rays()
        return Plot3D(self.S,
                      **self.view_set)

    def find_object(self, name):
        '''determines min and max scanangle upon which target
           is hit

           name -- target to find

           return minimum and maximum hit angle
        '''
        hit_angle = []
        target = self.S.complist[self.naming[name]][0]
        max_angle = int(round(np.degrees(self.p.max_angle_incidence())))
        # course search
        for angle in range(-max_angle, max_angle, 1):
            self.set_orientation('prism', rotation=(0, 0, np.radians(angle)))
            if len(target.hit_list):
                hit_angle.append(angle)

        if not len(hit_angle):
            return hit_angle
        # optimize
        low = min(hit_angle)
        high = max(hit_angle)
        new = True
        while new:
            self.set_orientation('prism', rotation=(0, 0, np.radians(low-0.1)))
            if len(target.hit_list):
                low = low-0.1
            else:
                new = False
            self.set_orientation('prism',
                                 rotation=(0, 0, np.radians(high+0.1)))
            if len(target.hit_list):
                high = high+0.1
                new = True
            else:
                new = False
        return [low, high]
