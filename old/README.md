# Analytical simulation

The [Strehl Ratio](https://en.wikipedia.org/wiki/Strehl_ratio) measures the quality of optical image formation.
The Strehl ratio has a value between 0 and 1.  
In the analytical model, it is assumed the Strehl ratio follows a relation
published by Wyant.  
The relationship is tested numerically using [Rayopt](https://github.com/quartiq/rayopt).  
Rayopt is not actively maintained and executing the simulation script gives errors but it should work.  
Dr. Jordens provided help with making the script, see [issue 16](https://github.com/quartiq/rayopt/issues/16).  
If you run both programs, analytical.py and simulation.py, you should see;

## Lambda RMS optical path difference:

|Tilt angle (degrees) |Rayopt (simulation.py)| Wyant (analytical.py)
|-----|--------|-------|
| 10 | 0.006 | 0.005 |
| 24 | 0.034 | 0.032 |
| 30 | 0.054 | 0.05 |
