# Optical Design & Simulation (Prisms)

Optical design, analytical modeling, and 3D ray-tracing simulations for the transparent polygon prism laser scanner known as **Hexastorm**.

This package provides the optical calculations used by:
* **Hexastorm Design**: [github.com/hstarmans/hexastorm_design](https://github.com/hstarmans/hexastorm_design)
* **Hexastorm FreeCAD Workbench**: [github.com/hstarmans/freecad_hexastorm](https://github.com/hstarmans/freecad_hexastorm)
* **Hackaday Project**: [hackaday.io/project/21933-open-hardware-transparent-polygon-scanner](https://hackaday.io/project/21933-open-hardware-transparent-polygon-scanner)
* **Video Walkthrough**: [YouTube Explanation](https://youtu.be/kekMkjqzRjE)

---

## Features

1. **Analytical Model (`prisms.analytical`)**
   * Computes diffraction-limited Gaussian beam waist spot size and Rayleigh range.
   * Calculates longitudinal and transversal focus shift through rotating polygon facets.
   * Computes 3rd-order Seidel aberrations (spherical, coma, astigmatism) and Strehl ratio based on Wyant's optical testing formulations.
   * Analyzes scanline duty cycle, non-uniform sweep velocity, and cross-scan facet-to-datum errors.

2. **Ray-Tracing Simulation (`prisms.system` & `prisms.library`)**
   * Non-sequential 3D ray tracing using upstream [pyOpTools](https://github.com/cihologramas/pyoptools).
   * Models N-BK7 polygon prisms, Edmund Optics cylindrical lenses, fold mirrors, and photodiode detection targets.
   * Automatically determines synchronization photodiode hit angles (`find_object('diode')`) and focal plane positioning.

3. **Modern Interactive Notebooks (`Notebooks/`)**
   * **Marimo Reactive App**: Launch interactive simulations with live sliders via `uv run marimo edit Notebooks/marimo_plot_system.py`.
   * **Standard Python / Jupytext**: Compatible with JupyterLab, VS Code, or direct terminal execution.

---

## Installation & Setup

This repository uses [`uv`](https://docs.astral.sh/uv/) for fast, reproducible, and modern dependency management.

### 1. Prerequisites (Eigen3 Headers - Zero Sudo Required)

`pyoptools` compiles Cython/C++ extensions against the header-only C++ Eigen3 library (`<Eigen/Dense>`).

* **Zero-sudo (User Local - Recommended):**
  Eigen is header-only and can be placed in `~/.local/include/eigen3`:
  ```bash
  mkdir -p ~/.local/include/eigen3
  curl -sL https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.tar.gz | tar -xz -C ~/.local/include/eigen3 --strip-components=1
  export EIGEN3_INCLUDE_DIR="$HOME/.local/include/eigen3"
  ```
* **System Package (Alternative if you have sudo):**
  ```bash
  sudo apt install -y libeigen3-dev
  ```

### 2. Install Project Environment

Clone the repository and synchronize the environment:

```bash
# Sync core dependencies and dev/notebook groups
uv sync --all-groups
```

To install this package in editable mode in an external project (such as `hexastorm_design`):
```bash
uv add --editable /path/to/opticaldesign
```

---

## Running Tests

Run the complete automated test suite with `pytest`:

```bash
uv run pytest -v
```

Lint and format code using `ruff`:

```bash
uv run ruff check .
uv run ruff format .
```

---

## Interactive Notebooks

### 1. Reactive Notebook with Marimo (Recommended)

Launch the reactive Marimo application:

```bash
uv run marimo edit Notebooks/marimo_plot_system.py
```

Or run as a web app:

```bash
uv run marimo run Notebooks/marimo_plot_system.py
```

### 2. Standard Script / JupyterLab

You can run the notebook scripts directly via `uv`:

```bash
uv run python Notebooks/plot_system.py
uv run python Notebooks/system_compact.py
```

Or launch JupyterLab:

```bash
uv run jupyter lab
```

---

## Mathematical Summary

Key optical relationships implemented in `prisms.analytical`:

* **Gaussian Waist Radius**:
  `waist = (2 × wavelength / π) × f_numb`
* **Rayleigh Length**:
  `rayleigh_length = π × waist² / wavelength`
* **Longitudinal Focus Shift**:
  `slong = ((n - 1) / n) × T`
* **Transversal Focus Shift**:
  `disp = T × sin(x) × (1 - cos(x) / sqrt(n² - sin²(x)))`
* **Duty Cycle**:
  `duty_cycle = max_recommended_angle / max_angle_incidence`
* **Strehl Ratio**:
  Derived from wavefront aberration polynomial RMS optical path difference (OPD).

---

## Architecture

```
opticaldesign/
├── src/prisms/
│   ├── __init__.py       # Top-level exports (PrismProperties, PrismScanner, Polygon)
│   ├── analytical.py     # Closed-form physics formulas, aberrations, and Strehl calculations
│   ├── library.py        # Custom pyOpTools components (regular Polygon prism)
│   └── system.py         # Complete optical system layout and ray-tracing routines
├── Notebooks/
│   ├── marimo_plot_system.py  # Interactive reactive Marimo notebook
│   ├── plot_system.py         # Full scanner simulation (py:percent format)
│   └── system_compact.py      # Compact layout & Fresnel reflection analysis
├── tests/
│   ├── test_analytical.py     # Analytical formulas unit tests
│   ├── test_library.py        # Polygon geometry tests
│   └── test_system.py         # Ray propagation & diode hit detection tests
├── old/                       # Archived 2017 RayOpt comparison scripts
├── pyproject.toml             # Standard PEP 621 configuration managed by uv
└── uv.lock                    # Fully pinned, reproducible lockfile
```

---

## License

GPL-3.0-or-later.
