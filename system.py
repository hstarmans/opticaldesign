import numpy as np

from math import pi

from pyoptools.raytrace.component import Component 
from pyoptools.all import CylindricalLens, Ray, RectMirror, material, System, Plot3D
from library import Polygon


class PrismScanner():
    '''defines a prism scanner
    '''  
    def __init__(self, wavelength=405):
        '''instantiate optical system
        
        wavelength -- wavelength of the laser
        '''
        self.S = self.system()
        self.wavelength = wavelength
    
    def system(self, angle = 0):
        '''defines optical system using pyoptools
        
        System is ordered upon distance from optical source.
        Closest component comes first.
        
        angle -- angle in degrees of prism
        '''
        # Cylinder LENS 1 Edmund optics 68-048 
        # BFL + CT = 73.68 + 2 = 75.68
        CL_lens1=CylindricalLens(size=(12.5, 25), thickness=2,
                                 curvature_s1=1./75.68, curvature_s2=0,
                                 material=material.schott["N-BK7"])

        # Prism
        prism = Polygon(sides=4,
                        height=2,
                        inner_radius=15,
                        material=material.schott["N-BK7"])

        # Cylinder LENS 2 Edmund optics 68-046
        # BFL + CT = 23.02 + 3
        CL_lens2=CylindricalLens(size=(12.5, 25),
                                 thickness=3,
                                 curvature_s1=1./26.02,
                                 curvature_s2=0,
                                 material=material.schott["N-BK7"])

        # Mirror
        M1=RectMirror(size=(10, 10, 2.0),
                      reflectivity=1,
                      material=material.schott["N-BK7"] )

        # Optical system
        S=System(complist=[(CL_lens1,(0,0,0),(0.5*pi,0,0)),
                           (prism,(0,10+15,0),(0,0,-np.radians(angle))),
                           (CL_lens2,(0,50,0),(0.5*pi,0.5*pi,0)),
                           (M1, (-10, 60, 0), (0.5*pi,0.5*pi, -0.25*pi))],n=1)
        return S
    
    def set_angle(self, angle = 0):
        ''' sets the angle of the prism to a given angle
        
            angle -- rotation angle in degrees of prism
        ''' 
        self.S.complist['C1'][-1][-1] = np.radians(angle)
        self.S.reset()
        self.S.ray_add(Ray(pos=[0,0,0],
                       dir=[0,1,0], 
                       wavelength=self.wavelength))
        self.S.propagate()
    
    def plot(self, angle = 0):
        ''' plot the system with a ray
        
            angle -- rotation angle in degrees of prism
        ''' 
        self.set_angle(angle)
        return Plot3D(self.S,
                      center=(0,0,0),
                      size=(250,100),
                      scale=3,
                      rot=[(np.radians(40), 0,0)])
                
    def find_mirror(self):
        ''' determines angle upon which mirror is hit
        ''' 
        hit_angle = []
        failed = []
        mirror = self.S.complist['C3'][0]
        for angle in range(-90, 90):
            self.set_angle(angle)
            if len(mirror.hit_list): 
                hit_angle.append(angle)
            else:
                failed.append(angle)
        return hit_angle
