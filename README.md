# Prisms

Package contains optical similations and calculations for prisms.
There are two representions;
 - Analytical:  properties of prism based upon pure math and physics
 - pyOpTools: description of the optical system in [pyOpTools](https://github.com/cihologramas/pyoptools)

In the old folder, there is also a representation;
 - rayOpt: description of the optical system in [rayOpt](https://github.com/jordens/rayopt)

```console
python3 setup.py develop --user
```

## Remarks

### Limitations model
G2 lens specs can be found online....  
  6.33mm diameter, 5.3mm front surface, 4.0mm focal length  
Working Distance: ~2.4mm from laser diode  
Several issues  
    - requires you to know aspheric coefficients AND divergence / sice point  
    - mitigated by assuming parallel bundle  

### Limitations Pyoptools
 - If light hits the prism at an edge corner, it does not know what to do and does not throw an error.
 - cylindrical lenses, do not have side surfaces in pyoptools
 - it is not possible to load cylindrical lenses directly from Edmund's library

### Optical design
Numerical and analytical model used for building a Hexastorm.
The analytical model is contained in analytical.py
The numerical model is contained in simulation.py.
The article where the model and the technology for the Hexastorm is outlined is available [here](http://reprap.org/wiki/Transparent_polygon_scanner). 
A presentation on the technology is available [here](https://www.youtube.com/watch?v=bLrt0U69ZLI).
The Zemax lens is contained in zmax_49332ink.zmx. Installation info for Rayopt is available [here](https://github.com/jordens/rayopt).
Note that the glass and stock catalogs need to be grabbed from the Windows installation to parse the lens data. The program also works under Linux.

## Links
[Official site](https://www.hexastorm.com/)  
[Hackaday page](https://hackaday.io/project/21933-open-hardware-transparent-polygon-scanner)  
[Reprap article](https://reprap.org/wiki/Transparent_Polygon_Scanning)  
