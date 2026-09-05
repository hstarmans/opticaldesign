# %% [markdown]
# # Optical Design & Simulation of Prism Scanner
#
# This notebook simulates the optical layout of the Hexastorm polygon prism scanner.
# It computes chief rays, photodiode hit angles, cylinder lens focal points,
# and sensitivity to alignment offsets.

# %%
import logging
import os

import numpy as np

from prisms.system import PrismScanner

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# %%
# Instantiate scanner system with cylindrical lenses
p = PrismScanner(withcylinder=True)

# %%
# Plot the system for a prism rotation angle of -38 degrees
plot_38 = p.plot(-38)
logger.info("Generated 3D plot widget at -38 degrees")

# %%
# Find the angle range at which the photodiode is illuminated
hit_angles = p.find_object("diode")
logger.info("Photodiode hit angle range: %s degrees", hit_angles)

# %%
# Trace key rays:
# - Rays hitting photodiode edges
# - Rays defining scanline limits
# - Center reference ray
p.show_key_rays()

# %%
# Distance between focal points of both cylindrical lenses
dist = p.distance_between_cylinders()
logger.info("Distance between focal points of cylinder lenses: %.2f mm", dist)

# %%
# Determine the optimal position of the photodiode and plot
p.focal_point(cyllens1=True, angle=-43, diode=True, plot=False)
logger.info("Calculated photodiode position: %s", p.position_diode)

# %%
# Sensitivity analysis:
# Test displacement of prism rotation axis and its effect on spot position
initial_position = np.array([-35.0, 0.0, 0.0])
delta = 0.2
p.set_orientation("prism", position=initial_position.tolist())

start = p.focal_point(cyllens1=True, angle=-42, simple=False, diode=True, plot=False)

# X-translation
p.set_orientation(
    "prism", position=(initial_position + np.array([delta, 0, 0])).tolist()
)
delta_x = p.focal_point(cyllens1=True, angle=-42, simple=False, diode=True, plot=False)

# Y-translation
p.set_orientation(
    "prism", position=(initial_position + np.array([0, delta, 0])).tolist()
)
delta_y = p.focal_point(cyllens1=True, angle=-42, simple=False, diode=True, plot=False)

# Z-translation
p.set_orientation(
    "prism", position=(initial_position + np.array([0, 0, delta])).tolist()
)
delta_z = p.focal_point(cyllens1=True, angle=-42, simple=False, diode=True, plot=False)

logger.info("Shift from X-offset (0.2 mm): %s", start - delta_x)
logger.info("Shift from Y-offset (0.2 mm): %s", start - delta_y)
logger.info("Shift from Z-offset (0.2 mm): %s", start - delta_z)

# %%
# Load cached FreeCAD positions if available
cache_file = "temp.pkl"
if os.path.exists(cache_file):
    p.load_system(cache_file)
    logger.info("Loaded system positions from %s", cache_file)
else:
    logger.info(
        "No %s cache file found; using default analytical positions", cache_file
    )
