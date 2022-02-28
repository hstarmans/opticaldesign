from math import pi
import pickle
from copy import deepcopy

import numpy as np
from pyoptools.all import (CylindricalLens, Ray, RectMirror, CCD, IdealLens,
                           material, System, Plot3D, nearest_points, Shape)

from prisms.library import Polygon
from prisms.analytical import Prism_properties


class PrismScanner():
    '''defines a prism scanner'''
    def __init__(self, wavelength=0.405, compact=False):
        '''instantiate optical system

        wavelength -- wavelength of the laser in microns
        compact -- True renders with simple lens and prism
                   False renders with two cylinder lenses
                   mirror and prism
        '''
        self.compact = compact
        self.position_diode = (-70, 20, 0)
        self.S = self.system()
        self.wavelength = wavelength
        self.p = Prism_properties()
        # converts name to position
        # CL is cylinder lens
        if compact:
            self.naming = {'lens': 'C0',
                           'prism': 'C1',
                           'diode': 'C2'}
        else:
            self.naming = {'CL1': 'C0',
                           'prism': 'C1',
                           'CL2': 'C2',
                           'ccd': 'C3',
                           'mirror': 'C4',
                           'diode': 'C5'}
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

    def system(self, microscope=False, reflection=False):
        '''defines optical system using pyoptools

        System is ordered upon distance from optical source.
        Closest component comes first.

        microscope  -- make laser microscope
        '''
        # Mirror
        # 50-50 beamsplitter used by breaking taps
        BSM = RectMirror(size=(10, 10, 2),
                         reflectivity=0.5)


        # Cylinder LENS 1 Edmund optics 68-048
        # https://www.gophotonics.com/products/
        # optical-lenses/edmund-optics-inc/33-15-68-048
        CL_lens1 = CylindricalLens(size=(12.5, 25),
                                   thickness=2,
                                   curvature_s1=1./38.76,
                                   curvature_s2=0,
                                   material=material.schott["N-BK7"])
        Ideal_lens= IdealLens(f=75)

        # Prism
        prism = Polygon(sides=4,
                        height=2,
                        inner_radius=15,
                        reflection=reflection,
                        material=material.schott["N-BK7"])

        # Cylinder LENS 2 Edmund optics 68-046
        # https://www.gophotonics.com/products/
        # optical-lenses/edmund-optics-inc/33-15-68-046
        CL_lens2 = CylindricalLens(size=(12.5, 25),
                                   thickness=3,
                                   curvature_s1=1./12.92,
                                   curvature_s2=0,
                                   material=material.schott["N-BK7"])

        # Mirror
        # Mirror, is only coated on side; it is not symmetric!
        M1 = RectMirror(size=(10, 10, 2),
                        reflectivity=1)

        # Photodiode BPW34
        # Photiodiode is actually 3.2 mm thick, but want to prevent
        # hitting side is counted as hit
        PD = RectMirror(size=(5.4, 4, 0.01),
                        reflectivity=0)

        # CCD camera
        # CCD allows to image spot in focal plane
        # and increases the length of rays traced
        ccd = CCD()
        # Optical system
        # This rotation as this simplifies interaction with FreeCAD
        # Here the laser points in the -x direction
        # I am not able to rotate ThreeJS view in Z, so it is not optimal
        if self.compact:
            complist = [(Ideal_lens, (-1, 0, 0), (0.5*pi, 0, -0.5*pi)),
                        (prism, (-20-15, 0, 0), (0, 0, 0)),
                        (PD, self.position_diode, (0.5*pi, 0.5*pi, 0))]
                        #(ccd, (-20, 30, 0), (0.5*pi, 0.5*pi, 0))]
        else:
            complist = [(CL_lens1, (-1, 0, 0), (0.5*pi, 0, -0.5*pi)),
                        (prism, (-20-15, 0, 0), (0, 0, 0)),
                        (CL_lens2, (-61, 0, 0), (0.5*pi, 0.5*pi, -0.5*pi)),
                        (ccd, (-85, 0, 0), (0.5*pi, 0.5*pi, -0.5*pi)),
                        (M1, (-70, 10, 0), (0.5*pi, 0.5*pi, -0.25*pi)),
                        (PD, self.position_diode, (0.5*pi, 0.5*pi, 0))]
        if microscope:
            complist.append((BSM, (-60, 0, 0), (0, -0.25*pi, 0)))
        
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

        # if cylinder 2 is moved, move CCD to new approx focal point
        if comp == 'CL2' and position:
            position[0] = self.focal_point(cyllens1=False)
            self.S.complist[self.naming['ccd']][-2][:] = position
        if comp == 'CL2' and rotation:
            raise Exception("Not supported")

        if reset:
            self.S.reset()
        self.S.ray_add(Ray(**self.ray_prop))
        self.S.propagate()

    def focal_point(self, cyllens1, angle=0, simple=True, plot=False):
        '''returns focal point of cylinder lens

           cyllens1  -- True, focal point cyl lens 1
                        False, focal point cyl lens 2
           simple    -- Only get x-coordinate
        '''
        dct1 = deepcopy(self.ray_prop)
        dct2 = deepcopy(self.ray_prop)
        if cyllens1:
            dct1['pos'][1] += 0.5
            dct2['pos'][1] -= 0.5
        else:
            dct1['pos'][2] += 0.5
            dct2['pos'][2] -= 0.5
        self.S.reset()
        self.set_orientation('prism', rotation=(0, 0, np.radians(angle)))
        straal1 = Ray(**dct1)
        straal2 = Ray(**dct2)
        self.S.ray_add(straal1)
        self.S.ray_add(straal2)
        self.S.propagate()
        self.position_diode = nearest_points(straal1.get_final_rays()[0],
                                  straal2.get_final_rays()[0])[0]
        if simple:
            dist = nearest_points(straal1.get_final_rays()[0],
                                  straal2.get_final_rays()[0])[0][0]
        else:
            dist = nearest_points(straal1.get_final_rays()[0],
                                  straal2.get_final_rays()[0])[0]
        if plot:
            return Plot3D(self.S,
                          **self.view_set)
        return dist

    def save_system(self, fname):
        '''save the system

           It is hard to save threejs plot objects as
           image, as a result this is used.

           fname -- filename to save system to
        '''
        with open(fname, 'wb') as file:
            pickle.dump([self.ray_prop, self.S], file)

    def load_system(self, fname):
        '''plot the system with a ray

           fname -- filename to load system from
        '''
        with open(fname, 'rb') as file:
            [self.ray_prop, self.S] = pickle.load(file)

    def plot(self, angle=0, save=False, reflection=False):
        '''plot the system with a ray

           angle -- rotation angle in degrees of prism
           reflection -- plots reflected ray which is used to trigger diode
        '''
        self.S = self.system(reflection=reflection)
        self.S.ray_add(Ray(**self.ray_prop))
        self.S.propagate(100)
        self.set_orientation('prism', rotation=(0, 0, np.radians(angle)))
        return Plot3D(self.S,
                      **self.view_set)

    def draw_key_rays(self):
        '''draws six chief rays

           chief rays which hit side scanline
           chief rays which hit side photodiode
           chief rays which are unperturbered
        '''
        diode_angles = self.find_object('diode')
        if not diode_angles:
            print("Can't hit diode with laser")
        max_scan_angle = np.degrees(self.p.max_recommended_angle())
        scan_angles = [-max_scan_angle, max_scan_angle, 0]
        self.S.reset()
        lst = diode_angles + scan_angles
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
                # in case of mirror we only want specific side
                # you can get specific sides as follows
                # if target.hit_list[0][-1].orig_surf[-1] != 'S2':
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
