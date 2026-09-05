import logging

import numpy as np
from scipy.integrate import dblquad
from sympy import diff, lambdify, sin, sqrt, symbols

logger = logging.getLogger(__name__)

# Precompute derivative function for transversal focus shift
_sym_x, _sym_T, _sym_n = symbols("x T n")
_sym_expr = (
    _sym_T
    * sin(_sym_x)
    * (1 - sqrt((1 - sin(_sym_x) ** 2) / (_sym_n**2 - sin(_sym_x) ** 2)))
)
_sym_dexpr = diff(_sym_expr, _sym_x)
_eval_dexpr = lambdify((_sym_x, _sym_T, _sym_n), _sym_dexpr, "numpy")


class PrismProperties:
    """Key analytical properties in prism scanning.

    Source:
        Wyant: Basic Aberrations and Optical Testing
        http://rohr.aiax.de/BasicAberrationsandOpticalTesting.pdf
    """

    def __init__(self, params=None):
        """Instantiates prism properties with dictionary."""
        self.params = {}
        self.set_params(params)

    def set_params(self, params):
        """Set parameters with properties of scanner.

        In the dictionary several keys need to be defined:
            n            -- refractive index
            facets       -- number of polygon facets, should be even
            wavelength   -- wavelength [nm]
            T            -- thickness optical plate [mm]
            f_length     -- focal length first cylindrical lens [mm]
            d_bundle     -- diameter laser bundle [mm]
            rot_hz       -- rotations per second of prism [Hz]
            apex_angle   -- maximum deviation angle of adjacent sides in degrees
        """
        if not params:
            params = {
                "n": 1.53,
                "facets": 4,
                "wavelength": 405,
                "T": 30,
                "f_length": 75,
                "d_bundle": 1.2,
                "rot_hz": 350,
                # apex angle is 1 arc_minute
                "apex_angle": 1 / 60,
            }
        # f_number of the first cylindrical lens: f_numb = f_length / d_bundle
        params["f_numb"] = params["f_length"] / params["d_bundle"]
        self.params = params

    def spot_size(self, f_numb=None):
        """Returns the focused spot size (waist radius) of a Gaussian beam in microns.

        Calculation reference:
            waist = (2 × wavelength / π) × f_numb
        """
        if not f_numb:
            f_numb = self.params["f_numb"]
        # Spot size in microns
        waist = 2 * self.params["wavelength"] / np.pi * f_numb
        waist /= 1e3
        return waist

    def duty_cycle(self):
        """Duty cycle is fraction of one period during which the system is active."""
        return self.max_recommended_angle() / self.max_angle_incidence()

    def rayleigh_length(self, f_numb=None):
        """Returns the Rayleigh length in mm.

        Rayleigh length = π × waist² / wavelength
        """
        waist = self.spot_size(f_numb)
        rayleigh_len = np.pi * waist**2 / self.params["wavelength"]
        return rayleigh_len

    def max_angle_incidence(self):
        """Returns maximum angle of incidence in radians.

        If the prism is rotated further than this angle the next facet is hit:
        max_angle = 90° - (180° - 360° / facets) / 2
        """
        utiltmax = np.radians(90 - (180 - 360 / self.params["facets"]) / 2)
        return utiltmax

    def max_recommended_angle(self, strehl_ratio=0.71, min_fraction=0.8, verbose=False):
        """Returns the maximum recommended angle of incidence in radians.

        Parameters:
            strehl_ratio -- minimum required Strehl ratio (default: 0.71)
            min_fraction -- minimum percentage power / speed ratio at edges (default: 0.8)
            verbose      -- log decisions via logger.info
        """
        utilt_max = self.max_angle_incidence()

        def bisection_find(func, threshold, low=0.0, high=utilt_max, tol=1e-4):
            # Check boundaries
            if func(low) < threshold:
                return low
            if func(high) >= threshold:
                return high
            # Monotonic decreasing function search
            for _ in range(30):
                mid = 0.5 * (low + high)
                if abs(high - low) < tol:
                    return mid
                if func(mid) >= threshold:
                    low = mid
                else:
                    high = mid
            return 0.5 * (low + high)

        utilt_strehl = bisection_find(self.strehl_ratio, strehl_ratio)
        utilt_fraction = bisection_find(self.speed_edges, min_fraction)

        if verbose:
            if utilt_fraction < utilt_strehl:
                logger.info("Exposure line length fixed by speed constraint.")
            else:
                logger.info("Exposure line length fixed by Strehl constraint.")
            logger.info(
                "Strehl limit gives maximum angle of %.2f radians", utilt_strehl
            )
            logger.info(
                "Speed limit gives maximum angle of %.2f radians", utilt_fraction
            )

        return min(utilt_fraction, utilt_strehl)

    def longitudinal_shift(self):
        """Return longitudinal shift in mm of focus bundle.

        Wyant page 41 equation 68:
            slong = ((n - 1) / n) × T
        """
        params = self.params
        slong = (params["n"] - 1) / params["n"] * params["T"]
        return slong

    def transversal_shift(self, angle):
        """Transversal shift in mm for a given angle of incidence.

        Wyant page 41 equation 70:
            disp = T × sin(x) × (1 - sqrt((1 - sin(x)²) / (n² - sin(x)²)))
        """
        params = self.params
        t = params["T"]
        n = params["n"]
        sin_a = np.sin(angle)
        cos_a = np.cos(angle)
        disp = t * sin_a * (1.0 - cos_a / np.sqrt(n**2 - sin_a**2))
        return float(disp)

    def cross_scan_error(self, focal_distance=35, verbose=False):
        """Error orthogonal to scanline in mm.

        The sides of the prism are not perfectly parallel, resulting in
        a cross-scan error.
        """
        params = self.params
        apex_rad = np.radians(params["apex_angle"])
        d_angle = (params["n"] - 1) * apex_rad
        cross_error_1 = np.tan(d_angle) * focal_distance
        cross_error_2 = self.transversal_shift(apex_rad)

        if verbose:
            logger.info("Cross error, single side: %.4f mm", cross_error_1)
            logger.info("Cross error, tilted: %.4f mm", cross_error_2)

        return max(cross_error_1, cross_error_2)

    def speed_edges(self, utilt, verbose=False):
        """Speed variation along the scanline.

        Computes ratio of speed at center to speed at edges:
            fraction = (dy/dx at 0) / (dy/dx at utilt)
        """
        t = self.params["T"]
        n = self.params["n"]

        sdisp_center = float(_eval_dexpr(0.0, t, n))
        sdisp_edge = float(_eval_dexpr(utilt, t, n))

        fraction = sdisp_center / sdisp_edge if sdisp_edge != 0 else 0.0

        if verbose:
            logger.info(
                "The speed at the center is %.2f %% of the speed at the edges.",
                fraction * 100,
            )
            ang_speed = np.pi * 2 * self.params["rot_hz"]
            logger.info(
                "The speed at the edges is %.2f m/s.",
                (sdisp_edge / 1000.0) * ang_speed,
            )

        return fraction

    def print_properties(self):
        """Log defining properties of the optical system."""
        utiltmax = self.max_angle_incidence()
        utilt = self.max_recommended_angle(verbose=True)
        dispmax = self.transversal_shift(utiltmax)
        logger.info("The duty cycle is %.2f", utilt / utiltmax)
        logger.info("The maximum line length is %.2f mm.", 2 * dispmax)
        dispused = self.transversal_shift(utilt)
        self.speed_edges(utilt, verbose=True)
        logger.info("The line length is %.2f mm.", 2 * dispused)
        logger.info(
            "The spot radius of the first cylindrical lens is %.2f micrometers.",
            self.spot_size(),
        )
        logger.info("The Rayleigh range is %.3f mm.", self.rayleigh_length())
        logger.info(
            "The Strehl ratio is %.2f",
            self.strehl_ratio(utilt, verbose=True),
        )
        logger.info(
            "The cross scan error is %.2f microns", self.cross_scan_error() * 1000
        )

    def strehl_ratio(self, utilt, verbose=False):
        """Returns the Strehl ratio of the optical system based on 3rd order Seidel aberrations.

        Aberrations from Wyant:
            Spherical aberration (Wyant p. 42 eq 72):
                sabr = -T / f_numb⁴ × ((n² - 1) / (128 × n³))
            Coma (Wyant p. 44 eq 75):
                coma = -T × utilt / f_numb³ × ((n² - 1) / (16 × n³))
            Astigmatism (Wyant p. 45 eq 77):
                astig = -T × utilt² / f_numb² × ((n² - 1) / (8 × n³))
        """
        params = self.params
        wavelength = params["wavelength"]
        fnumber = params["f_numb"]
        n = params["n"]
        t = params["T"]

        # 3rd order Seidel aberrations in [mm]
        sabr = -t / (fnumber**4) * ((n**2 - 1) / (128 * n**3))
        coma = -t * utilt / (fnumber**3) * ((n**2 - 1) / (16 * n**3))
        astig = -t * (utilt**2) / (fnumber**2) * ((n**2 - 1) / (8 * n**3))

        # Wavefront aberration function w(theta, rho)
        def f(theta, rho):
            return (
                sabr * (rho**4)
                + astig * (rho**2) * (np.cos(theta) ** 2)
                + coma * (rho**3) * np.cos(theta)
            )

        def ws(theta, rho):
            return (f(theta, rho) ** 2) * rho

        def w(theta, rho):
            return f(theta, rho) * rho

        # Evaluate equation 62, page 37, Wyant using double quadrature
        # Note: dblquad integrates over theta in [0, 2*pi] and rho in [0, 1]
        int_ws = dblquad(ws, 0, 1, lambda rho: 0, lambda rho: 2 * np.pi)[0]
        int_w = dblquad(w, 0, 1, lambda rho: 0, lambda rho: 2 * np.pi)[0]
        var = (1.0 / np.pi * int_ws) - (1.0 / (np.pi**2) * (int_w**2))

        # Root mean square aberration
        rms = np.sqrt(max(0.0, var))
        # Convert lambda RMS from [mm] to wavelength units
        lambdarms = rms / (wavelength * 1e-6)

        if verbose:
            logger.info("The lambda OPD RMS is %6f", lambdarms)

        # Strehl ratio via Taylor expansion (Wyant page 39 eq 67):
        # rstrehl = 1 - (2π × lambdarms)² + (2π × lambdarms)⁴ / 2
        phase = 2 * np.pi * lambdarms
        rstrehl = 1 - phase**2 + (phase**4) / 2.0
        return float(rstrehl)


# Backward compatibility alias
Prism_properties = PrismProperties

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    p = PrismProperties()
    p.print_properties()
