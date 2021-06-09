from math import pi

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
                       'mirror': 'C3'}
        # default properties chief ray
        self.ray_prop = {'pos': [0, 0, 0],
                         'dir': [0, 1, 0],
                         'wavelength': self.wavelength}
        # default view settings for py3js renders
        self.view_set = {'center': (0, 0, 0),
                         'size': (150, 150),
                         'scale': 3,
                         'rot': [(np.radians(40), 0, 0)]}

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
        M1 = RectMirror(size=(10, 10, 2.0),
                        reflectivity=1)

        # Optical system
        shift = 10
        complist = [(CL_lens1, (0, shift, 0), (0.5*pi, 0, pi)),
                    (prism, (0, 10+15+shift, 0), (0, 0, 0)),
                    (CL_lens2, (0, 50+shift, 0), (0.5*pi, 0.5*pi, pi)),
                    (M1, (-10, 60+shift, 0), (0.5*pi, 0.5*pi, -0.25*pi))]
        S = System(complist=complist, n=1)
        return S

    def set_orientation(self, comp, position=None, rotation=None, reset=True):
        '''place comp at position and rotation

           comp     -- name of component; CL1, prism, CL2, mirror
           position -- [x, y, z] position of component
           rotation -- [rx, ry, rz] rotation of component
        '''
        naming = self.naming
        if position is not None:
            self.S.complist[naming[comp]][-2][:] = position
        if rotation is not None:
            self.S.complist[naming[comp]][-1][:] = rotation
        if reset:
            self.S.reset()
        self.S.ray_add(Ray(**self.ray_prop))
        self.S.propagate()

    def plot(self, angle=0):
        ''' plot the system with a ray

            angle -- rotation angle in degrees of prism
        '''
        self.set_orientation('prism', rotation=(0, 0, np.radians(angle)))
        self.S.ray_add(Ray(**self.ray_prop))
        self.S.propagate()
        return Plot3D(self.S,
                      **self.view_set)

    def show_five_rays(self):
        mirror_angles = self.find_mirror()
        max_scan_angle = np.degrees(self.p.max_recommended_angle())
        scan_angles = [-max_scan_angle, max_scan_angle, 0]
        self.S.reset()
        lst = mirror_angles + scan_angles
        for angle in lst:
            self.set_orientation('prism',
                                 rotation=(0, 0, np.radians(angle)),
                                 reset=False)
        return Plot3D(self.S,
                      **self.view_set)

    def find_mirror(self):
        ''' determines angle upon which mirror is hit
        '''
        hit_angle = []
        mirror = self.S.complist[self.naming['mirror']][0]
        max_angle = int(round(np.degrees(self.p.max_angle_incidence())))
        # course search
        for angle in range(-max_angle, max_angle, 1):
            self.set_orientation('prism', rotation=(0, 0, np.radians(angle)))
            if len(mirror.hit_list):
                hit_angle.append(angle)
        # optimize
        low = min(hit_angle)
        high = max(hit_angle)
        new = True
        while new:
            self.set_orientation('prism', rotation=(0, 0, np.radians(low-0.1)))
            if len(mirror.hit_list):
                low = low-0.1
            else:
                new = False
            self.set_orientation('prism',
                                 rotation=(0, 0, np.radians(high+0.1)))
            if len(mirror.hit_list):
                high = high+0.1
                new = True
            else:
                new = False
        return [low, high]
