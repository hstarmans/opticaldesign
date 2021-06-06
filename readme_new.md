# Limitations model

G2 lens specs can be found online....  
  6.33mm diameter, 5.3mm front surface, 4.0mm focal length  
Working Distance: ~2.4mm from laser diode  
Several issues  
    - requires you to know aspheric coefficients AND divergence / sice point  
    - mitigated by assuming parallel bundle  

# Limitations Pyoptools

 - If light hits the prism at an edge corner, it does not know what to do and does not throw an error.
 - cylindrical lenses, do not have side surfaces in pyoptools
 - it is not possible to load cylindrical lenses directly from Edmund's library