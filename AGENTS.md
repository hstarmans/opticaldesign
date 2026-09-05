# Agent Guidelines for OpticalDesign

## Script Execution Pattern
- Whenever running ad-hoc Python scripts, environment inspections, or multi-step execution commands, ALWAYS write them into `script.py` at the repository root and execute via:
  ```bash
  python3 script.py
  ```
- This ensures the user only needs to authorize permission once in the IDE.
- `script.py` is ignored in `.gitignore`.

## Math & Formula Formatting
- Do not output math formulas in LaTeX (`$$`, `\frac`, `\text`).
- Format all equations using clean plain text, Unicode characters (e.g., ×, ÷, ±, x̄, Δ), or inside Markdown code blocks.
