import numpy as np

from pyoptools.raytrace.component import Component
from pyoptools.raytrace.surface import Plane
from pyoptools.raytrace.shape import Rectangular, Triangular


class Polygon(Component):
    '''defines regular polygon prism

    Defines component containing a polygon shape
    The center of mass of the polygon is at the origin

    sides        -- number of sides
    height       -- height of polygon
    inner radius -- inner radius of polygon
    reflection   -- ray is reflected when it exist the prism
                    this is used to simulate
    '''
    def __init__(self, sides=3, height=3, inner_radius=10, reflection=False, **traits):
        if sides < 3:
            raise Exception("Polygon should have at least 3 sides.")
        if sides % 2 == 1:
            print("Polygon needs even number of sides for scanning.")
        side_length = 2*inner_radius*np.tan(np.pi/sides)
        Component.__init__(self, **traits)
        # create a side base shape
        side = Plane(shape=Rectangular(size=(side_length, height)))
        for i in range(sides):
            angle = 2*np.pi/sides*i
            center = inner_radius*np.array([np.cos(angle), np.sin(angle)])
            if (i == 1) and reflection: # laser does not hit at side 0 but side 3
                side = Plane(shape=Rectangular(size=(side_length, height)),
                             reflectivity=1)
            else:
                side = Plane(shape=Rectangular(size=(side_length, height)))
            self.surflist[f"S{i}"] = (side, (center[0], center[1], 0),
                                      (np.pi/2, 0, angle+np.pi/2))
            
        # create a top/bottom base shape
        triangle = Plane(shape=Triangular(((0, 0),
                         (-inner_radius, -side_length/2),
                         (-inner_radius, side_length/2))))
        for i in ['bottom', 'height']:
            surface = len(self.surflist)
            if i == 'bottom':
                offset = -height/2
            else:
                offset = height/2
            for i in range(sides):
                angle = 2*np.pi/sides*i
                if sides % 2:
                    offset = 2*np.pi/(sides*2)
                else:
                    offset = 0
                self.surflist[f"S{i+surface}"] = (triangle,
                                                  (0, 0, offset),
                                                  (0, 0, angle+offset))
