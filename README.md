# Prisms

Package contains optical similations and calculations for prisms.
There are two representions;
 - Analytical:  properties of prisms based upon pure math and physics
 - pyOpTools: description of the optical system in [pyOpTools](https://github.com/cihologramas/pyoptools)

In the old folder, there is a numerical verification for the Strehl ratio formula;
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
 - there is no proper bridge for object from FreeCad to pyoptools
 - first side of mirror is at origin
 - I have problems rotating the in z-direction in the PyThreejs viewer
 - If light hits the prism at an edge corner, it does not know what to do and does not throw an error.
 - cylindrical lenses, do not have side surfaces in pyoptools
 - it is not possible to load cylindrical lenses directly from Edmund's library

## Links
[Official site](https://www.hexastorm.com/)  
[Hackaday page](https://hackaday.io/project/21933-open-hardware-transparent-polygon-scanner)  
[Reprap article](https://reprap.org/wiki/Transparent_Polygon_Scanning)  
