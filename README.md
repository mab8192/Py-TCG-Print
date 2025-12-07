# pytcgprint

**pytcgprint** is a lightweight Command Line Interface (CLI) tool designed for board game designers and "Print and Play" enthusiasts. It takes a folder of card images and automatically arranges them into high-resolution, evenly spaced PDF grids ready for printing.

It handles the math for you - automatically calculating gaps, centering grids, and scaling cards to ensure they fit perfectly on standard letter paper (or any custom size).

## Features

* **Smart Layout:** Automatically calculates the maximum number of rows and columns that fit on your paper.
* **Auto-Centering:** Mathematically centers the grid horizontally and vertically.
* **Even Spacing:** Calculates the horizontal gap between cards and applies that exact same gap vertically for a uniform look.
* **Smart Scaling:** Defaults to 98% scale to provide "breathing room" for cutting and sleeves, preventing cards from running off the page edges.
* **PDF Output:** Generates a high-quality (300 DPI) multi-page PDF.
* **Customizable:** Precise control over page size, card size, margins, and scaling via CLI arguments.

## Installation

### Prerequisites
* Python 3.6 or higher
* `pip` (Python package installer)

### Install from Source
1.  Download or clone this repository.
2.  Open your terminal/command prompt and navigate to the project folder (where `setup.py` is located).
3.  Run the following command:

```bash
pip install .
```

*For developers: You can use `pip install -e .` to install in editable mode.*

## Usage

### Quick Start
1.  Create a folder named `cards` in your current directory.
2.  Place your image files (PNG, JPG, etc.) inside it.
3.  Run:

```bash
pytcgprint
```

This will generate `output_deck.pdf` with a 3x3 grid (assuming standard poker cards on Letter paper) at 98% scale with 0.5" side margins.

### Custom Input/Output

```bash
pytcgprint --input "my_prototype_v1" --output "prototype_print.pdf"
```

### Adjusting Dimensions
If you are using A4 paper or different sized cards (e.g., Mini Euro):

```bash
# Example for A4 Paper (8.27 x 11.69 inches)
pytcgprint --page-width 8.27 --page-height 11.69

# Example for Mini Euro Cards (1.73 x 2.67 inches)
pytcgprint --card-width 1.73 --card-height 2.67
```

### Manual Layout
If you want to force a specific grid (e.g., 2x2) or exact 100% scale:

```bash
pytcgprint --rows 2 --cols 2 --scale 1.0
```

## CLI Arguments Reference

| Argument | Flag | Default | Description |
| :--- | :--- | :--- | :--- |
| **Input** | `-i`, `--input` | `cards` | Folder containing your image files. |
| **Output** | `-o`, `--output` | `output_deck.pdf` | The filename of the generated PDF. |
| **Margin** | `-m`, `--margin` | `0.5` | Minimum horizontal margin (inches). |
| **Scale** | `-s`, `--scale` | `0.98` | Card scale factor (0.98 = 98%). |
| **Rows** | `--rows` | `0` (Auto) | Force specific number of rows. |
| **Cols** | `--cols` | `0` (Auto) | Force specific number of columns. |
| **Page W** | `--page-width` | `8.5` | Page width in inches (Letter). |
| **Page H** | `--page-height` | `11.0` | Page height in inches (Letter). |
| **Card W** | `--card-width` | `2.5` | Card width in inches (Poker). |
| **Card H** | `--card-height` | `3.5` | Card height in inches (Poker). |
| **DPI** | `--dpi` | `300` | Resolution for the output PDF. |

## Printing Tips

When printing the resulting PDF, **do not** select "Fit to Page" or "Shrink to Fit" in your printer dialog.

1.  Select **"Actual Size"** or **"Scale: 100%"**.
2.  Because the tool defaults to 98% scale, the cards will print slightly smaller than standard TCG cards (approx 2.45" wide).
3.  If you need exact sized cards (e.g., for precise sleeving), run the tool with `--scale 1.0`.