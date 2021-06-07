import numpy as np
from scipy.integrate import dblquad
from sympy import symbols, diff, cos, sin, sqrt


class Prism_properties:
    '''Key analytical properties in prism scanning
     
       Source:
          Wyant: Basic Abberations and Optical testing
          http://rohr.aiax.de/BasicAberrationsandOpticalTesting.pdf
    '''
    def __init__(self, params=None):
        '''Instanstiates prism properties with dictionary
        '''
        self.set_params(params)
        
    def set_params(self, params):
        '''set parameters with properties of scanner
        
           In the dictionary several keys need to be defined
              n  -- refractive index
              facets -- number of polygon facets, should be even
              wavelength -- wavelength [nm]
              T -- thickness optical plate [mm]
              f_length -- focal length first cylindrical lens [mm]
              d_bundle -- diameter laser bundle [mm]
              rot_hz -- rotations per second of prism [Hz]
              apex_angle -- maximum deviation angle of adjacent sides
                            in degrees
        '''
        if not params:
            params = {'n': 1.53,
                     'facets': 4,
                      'wavelength':405,
                      'T': 30,
                      'f_length': 75,
                      'd_bundle': 1.2,
                      'rot_hz': 350,
                      # apex angle is 1 arc_minute
                      'apex_angle': 1/60 
            }
        # f_number of the first cylindrical lens
        params['f_numb'] = params['f_length'] / params['d_bundle']
        self.params = params         
                 
    def spot_size(self, f_numb=None):
        '''returns the focused spot size of a Gaussian beam in microns

           For details on the calculation see;
             https://www.newport.com/n/gaussian-beam-optics
           On default, the f_number, of the first cylindrical lens
           is used.
        '''
        if not f_numb:
            f_numb=self.params['f_numb']
        # Spot size
        waist=2*self.params['wavelength']/np.pi*f_numb
        waist/=1E3
        return waist
        
    def rayleigh_length(self, f_numb=None):
        '''returns the rayleigh length in mm

           The laser is only in focus for a certain distance.
           Outside of this discance the laser is larger than sqrt(2)
           minimum spot size.
           This assumes a Gaussian beam and is not the case for
           other beams like Bessel beams.
           On default, the f-number of the first
           cylindrical lens is used.
        '''
        waist=self.spot_size(f_numb)
        rayleigh_length=np.pi*waist**2/self.params['wavelength']
        return rayleigh_length
            
    def max_angle_incidence(self):
        '''returns maximum angle of incidence in radians

           If the prism is rotated further than this angle
           the next facet is hit.
        '''
        utiltmax=np.radians(90-(180-360/self.params['facets'])/2) 
        return utiltmax
    
    def max_recommended_angle(self, strehl_ratio=0.71):
        '''returns the maximum recommended angle of incidence
        
           strehl ratio -- minimum required strehl ratio
        '''
        utilt_max=self.max_angle_incidence()
        iterations=1000
        for i in range(0, iterations):
            angle=utilt_max/iterations*i
            ratio=self.strehl_ratio(angle)
            if ratio < strehl_ratio:
                return utilt_max/iterations*(i-1)
        
    def longitudinal_shift(self):
        '''return longitudinal shift in mm of focus bundle

           The focal point of a focussed bundle, 
           with its focal point outside of the prism,
           is displaced.
           The prism in effect increases the focal length of the lens.
           This effect is mostly independent of the rotation angle.
        '''
        # Wyant page 41 equation 68
        params = self.params
        slong=(params['n']-1)/params['n']*params['T']
        return slong
               
    def transversal_shift(self, angle):
        '''transversal shift for a given angle of incidence

           The transversal shift does not require a focussed bundle.

           angle -- rotation angle of prism in radians
        '''
        # symbol needed for differentation
        x=symbols('x') 
        params = self.params
        T = params['T']
        n = params['n']
        x = angle
        # Wyant page 41 equation 70
        expr=T*sin(x)*(1-sqrt((1-sin(x)**2)/(n**2-sin(x)**2)))
        disp=expr.evalf(subs={x:angle})
        return disp
    
    def cross_scan_error(self, focal_distance=35):
        '''error orthogonal to scanline 
            
           the sides of the prism are not perfectly parallel
           this result in a cross-scan error, i.e.
           error orthogonal to the scanline.
           There is also an error
           parallel to the scanline, this can be resolved 
           with interpolation as it only changes the size 
           and speed along the the scanline.
            
           focal distance  -- distance between focal point 
                              and edge prism
        '''
        # https://en.wikipedia.org/wiki/Prism
        # assumes incidence angle and apex angle are both small
        #  the apex angle is small as adjacent side are almost parallel
        #  the angle of incidicence small in the orthogonal case 
        #  but not the parallel case
        #  furthermore both sides will have this
        params = self.params
        d_angle = (params['n']-1)*np.radians(params['apex_angle'])
        cross_error = np.tan(d_angle)*focal_distance
        cross_error *= 2
        return cross_error

    def print_properties(self):
        '''gives a print out of defining properties 
           of the optical system
        '''
        T = self.params['T']
        n = self.params['n']
        utiltmax = self.max_angle_incidence()
        utilt = self.max_recommended_angle()
        dispmax = self.transversal_shift(utiltmax)
        print(f"The maximum transversal focus shift is {dispmax:.2f} mm.")
        dispused = self.transversal_shift(utilt)
        print(f"The line length is {dispused:.2f} mm.")
        # the transversal focus shift is dependent on the position plane
        # we use it too calculate the maximum displacement (chain rule)
        #  y=f(x) dx/dt=c   x=ct
        #    here y is the position of the spot in one dimension measured in mm
        #         x is the angle as a position of the time
        #         c is the angular rotation speed of the prism (assumed constant)
        #  --> dy/dt=dy/dx(x(t))*c 
        x=symbols('x') 
        # Wyant page 41 equation 70
        expr=T*sin(x)*(1-sqrt((1-sin(x)**2)/(n**2-sin(x)**2)))
        sdisp=diff(expr, x)
        # fractional speed
        fraction=sdisp.evalf(subs={x:0})/sdisp.evalf(subs={x:utilt})
        print(f"The speed at the center is {round(fraction*100,2)}" +
                " % of the speed at the edges.")
        ang_speed = np.pi*2*self.params['rot_hz']
        print(f"The speed at the edges is " +
              f"{sdisp.evalf(subs={x:utilt})/1000*ang_speed:.2f} m/s.")
        print(f"The spot radius of the first cylindical lens is {self.spot_size():.2f}"
                + " micrometers.")
        print(f"The Rayleigh range is {self.rayleigh_length():.3f} mm.")
        print(f"The Strehl ratio is {self.strehl_ratio(utilt, verbose=True):.2f}")
        print(f"The cross scan error is {self.cross_scan_error()*1000:.2f} microns")
      
    def strehl_ratio(self, utilt, verbose=False):
        '''returns the strehl ratio of the optical system
        
           These calculation only account for the distortions caused by the 
           the prism.
           The optical performance of the system can be expressed with the Strehl ratio. 
           If the Strehl ratio gets below a threshold,
           the aberrations will become dominant and the system will not image properly.
           As a result, it must be ensured via calculation that the Strehl ratio is larger
           than some acceptable limit, e.g. the Rayleigh limit of 0.71.
           Literature provides us with the Seidel coefficients of the main aberrations. 
           These are used to determine the Strehl ratio for a given rotation angle.
           In some literature, the Strehl ratio is referred to as the strehl radius
        
           utilt -- tilt angle in radians
           verbose -- prints lambda opd rms if True
        ''' 
        params = self.params
        wavelength = params['wavelength']
        fnumber = params['f_numb']
        n = params['n']
        T = params['T']
        # 3rd order Seidel aberrations in [mm]
        #  Wyant page 42 equation 72; spherical aberration
        sabr=-T/pow(fnumber,4)*((pow(n,2)-1)/(128*pow(n,3)))
        #   Wyant page 44 equation 75; coma
        #   Note: cosine has been omitted, will be added back when function f is defined
        coma=-T*utilt/pow(fnumber,3)*((pow(n,2)-1)/(16*pow(n,3)))
        #   Wyant page 45 equation 77 ; astigmatism
        #   Note: cosine has been omitted, will be added back when function f is defined
        astig=-T*pow(utilt,2)/pow(fnumber,2)*((pow(n,2)-1)/(8*pow(n,3)))
        # To calculate the combined RMS we add back the functional forms to the coefficients
        # They have been obtained from Wyant, page 17, table 2
        # The function f defines the wavefront aberration denoted by Wyant as w
        def f(theta,rho):
            return sabr*(rho**4)+astig*(rho**2)*(np.cos(theta)**2)+coma*(rho**3)*np.cos(theta)
        # We now try to evaluate equation 62, page 37, Wyant
        # First we define two auxiliary functions
        def ws(theta,rho):
            return f(theta,rho)**2*rho
        def w(theta,rho):
            return f(theta,rho)*rho
        # Hereafter we evaluate the integral, i.e. equation 62
        var=1/np.pi*dblquad(ws,0,1,lambda rho: 0, lambda rho: 2*np.pi)[0]\
        -1/(np.pi**2)*(dblquad(w,0,1,lambda rho: 0, lambda rho: 2*np.pi)[0]**2)
        # the RMS value is obtained by the root
        rms=np.sqrt(var)
        # The lambda RMS is expressed in [mm] 
        # and will be converted to wavelength units
        lambdarms=rms/(wavelength*1E-6)
        if verbose:
            print(f"The lambda OPD RMS is {lambdarms:6f}")
        # The Strehl radius is calculated with the first 
        # three terms of its Taylor series
        # Wyant page 39 equation 67
        rstrehl=1-(2*np.pi*lambdarms)**2+(2*np.pi*lambdarms)**4/2
        return rstrehl

    
if __name__ == "__main__":
    p = Prism_properties()
    p.print_properties()
    