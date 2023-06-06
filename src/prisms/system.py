from math import pi
import pickle
from copy import deepcopy

import numpy as np
from pyoptools.all import (CylindricalLens, Ray, RectMirror, CCD, IdealLens,
                           material, System, Plot3D, nearest_points)
from pyoptools.raytrace.shape.rectangular import Rectangular

from prisms.library import Polygon
from prisms.analytical import Prism_properties


class PrismScanner():
    '''defines a prism scanner'''

    def __init__(self, wavelength=0.405, withcylinder=True):
        '''defines optical system

           laser propagates in y-direction with wavelength [microns]
           system can be constructed with or without cylinder lenses.
           The prism is located at x,y,z = 0, 0, laser height

        wavelength   -- wavelength laser [microns]
        withcylinder -- wether the system uses cylinder lenses
        '''
        self.withcylinder = withcylinder
        self.position_diode = (60, 38, 0)
        self.wavelength = wavelength
        self.S = self.system()
        self.p = Prism_properties()
        # converts name to position
        # CL is cylinder lens
        if self.withcylinder:
            self.naming = {'CL1': 'C0',
                           'prism': 'C1',
                           'CL2': 'C2',
                           'ccd': 'C3',
                           'mirror': 'C4',
                           'diode': 'C5'}
        else:
            self.naming = {'lens': 'C0',
                           'prism': 'C1',
                           'mirror': 'C2',
                           'diode': 'C3'}

        # default properties chief ray
        self.ray_prop = {'pos': [0, -40, 0],
                         'dir': [0, 1, 0],
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
        # Mirror
        # A beamsplitter could possibly be used in laser microscope
        # see the video of laser microscopes on breaking taps
        # There is research in doing this on
        # chip via a photonic circuit which simplifies the design
        # BSM = RectMirror(size=(10, 10, 2),
        #                 reflectivity=0.5)

        # Cylinder LENS 1 Edmund optics 68-048
        # https://www.gophotonics.com/products/
        # optical-lenses/edmund-optics-inc/33-15-68-048
        CL_lens1 = CylindricalLens(size=(12.5, 25),
                                   thickness=2,
                                   curvature_s1=1./38.76,
                                   curvature_s2=0,
                                   material=material.schott["N-BK7"])
        Ideal_lens = IdealLens(shape=Rectangular(size=(5,5)),
                               f=60)

        # Prism
        prism = Polygon(sides=4,
                        height=2,
                        inner_radius=15,
                        # reflection
                        #   used to try out system
                        #   where light is reflected at the second prism
                        #   interface for the position of the photodiode
                        #   https://hackaday.io/project/21933-prism-laser-scanner/
                        #   log/204569-optical-weakenss-in-new-design
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
        # and increases the distance over which rays are traced
        # as these are drawn until CCD camera
        ccd = CCD()
        # Optical system
        # This rotation as this simplifies interaction with FreeCAD
        # Here the laser points in the -x direction
        # I am not able to rotate ThreeJS view in Z, so it is not optimal
        if self.withcylinder:
            self.position_diode = (35, 31, 0)
            complist = [(CL_lens1, (0, -29, 0), (-0.5*pi, 0, 0)),
                        (prism, (0, 0, 0), (0, 0, 0)),
                        (CL_lens2, (-6, 31, 0), (0, -0.5*pi, -0.5*pi)),
                        (ccd, (0, 50, 0), (0.5*pi, 0.5*pi, 0)),
                        (M1, (11, 31, 0), (0.5*pi, 0.5*pi, 0.25*pi+pi)),
                        (PD, self.position_diode, (0.5*pi, 0.5*pi, 0.5*pi))]
        else:
            self.position_diode = (60, 38, 0)
            complist = [(Ideal_lens, (0, -26, 0), (0.5*pi, 0, 0)),
                        (prism, (0, 0, 0), (0, 0, 0)),
                        (M1, (11, 38, 0), (0.5*pi, 0.5*pi, 0.25*pi+pi)),
                        (PD, self.position_diode, (0.5*pi, 0.5*pi, 0.5*pi))]
                        #(ccd, (-20, 30, 0), (0.5*pi, 0.5*pi, 0))]

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

    def distance_between_cylinders(self):
        '''returns distance between the focal points of both
           cylinder lenses
        '''

    def focal_point(self, cyllens1, angle=0, simple=True, diode=False, plot=False):
        '''returns focal point of cylinder lens, positions photodiode
           at correct position

           diode     -- position photodiode
           cyllens1  -- True, focal point cyl lens 1
                        False, focal point cyl lens 2
           simple    -- Only get x-coordinate
        '''
        # the idea is that two rays are created
        # light propagates in positive y-direction
        dct1 = deepcopy(self.ray_prop)
        dct2 = deepcopy(self.ray_prop)
        # the first cylinder focusses parallel to the
        # prism, i.e. the x-direction.
        # The rays are given an offset in this direction.
        # Now they should intersect at only one point,
        # known as the nearest point
        if cyllens1:
            dct1['pos'][0] += 0.5
            dct2['pos'][0] -= 0.5
        # the second cylinder focusses orthogonal to the
        # the cylinder, i.e. the z-direction
        else:
            dct1['pos'][2] += 0.5
            dct2['pos'][2] -= 0.5

        # we propagate the two rays
        def dotwice():
            self.S.reset()
            self.set_orientation('prism', rotation=(0, 0, np.radians(angle)))
            straal1 = Ray(**dct1)
            straal2 = Ray(**dct2)
            self.S.ray_add(straal1)
            self.S.ray_add(straal2)
            self.S.propagate()
            return straal1, straal2
        straal1, straal2 = dotwice()
        if diode:
            # updates position diode
            self.position_diode = nearest_points(straal1.get_final_rays()[0],
                                      straal2.get_final_rays()[0])[0]
            self.set_orientation('diode', self.position_diode)
            straal1, straal2 = dotwice()
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

    def plot(self, angle=0, save=False):
        '''plot the system with a ray

           angle -- rotation angle in degrees of prism
           reflection -- plots reflected ray which is used to trigger diode
        '''
        self.S.reset()
        self.S.ray_add(Ray(**self.ray_prop))
        self.S.propagate(100)
        self.set_orientation('prism', rotation=(0, 0, np.radians(angle)))
        return Plot3D(self.S,
                      **self.view_set)

    def draw_key_rays(self, diode=True, scanline=True):
        '''draws six chief rays

           chief rays which hit side scanline
           chief rays which hit side photodiode
           chief rays which are unperturbered
        '''
        lst = []
        if diode:
            diode_angles = self.find_object('diode')
            if not diode_angles:
                print("Can't hit diode with laser")
            lst += diode_angles
        if scanline:
            max_scan_angle = np.degrees(self.p.max_recommended_angle())
            scan_angles = [-max_scan_angle, max_scan_angle, 0]
            lst += scan_angles
        self.S.reset()
        print('drawing')
        print(lst)
        for angle in lst:
            self.set_orientation('prism',
                                 rotation=(0, 0, np.radians(angle)),
                                 reset=False)

    def show_key_rays(self, diode=True, scanline=True):
        '''draws five chief rays and returns plot'''
        self.draw_key_rays(diode, scanline)
        return Plot3D(self.S,
                      **self.view_set)

    def find_object(self, name):
        '''determines min and max scanangle upon which target
           is hit

           name -- target to find

           return minimum and maximum hit angle
        '''
        if self.withcylinder:
            low_angle = None
        else:
            low_angle = 0

        hit_angle = []
        target = self.S.complist[self.naming[name]][0]
        max_angle = int(round(np.degrees(self.p.max_angle_incidence())))
        # course search
        if not low_angle:
            low_angle = -max_angle
        else:
            print(f"Low search angle fixed at {low_angle} degrees")
        for angle in range(low_angle, max_angle, 1):
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
