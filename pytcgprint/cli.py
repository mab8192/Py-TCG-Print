import argparse

from pytcgprint.core import pytcgprint, Settings

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Arrange card images into a printable PDF grid.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # File I/O
    parser.add_argument("-i", "--input", type=str, default="cards",
                        help="Input folder containing image files")
    parser.add_argument("-o", "--output", type=str, default="output_deck.pdf",
                        help="Output PDF filename")

    # Dimensions (Inches)
    parser.add_argument("--page-width", type=float, default=8.5, help="Page width in inches")
    parser.add_argument("--page-height", type=float, default=11.0, help="Page height in inches")
    parser.add_argument("--card-width", type=float, default=2.5, help="Actual card width in inches")
    parser.add_argument("--card-height", type=float, default=3.5, help="Actual card height in inches")
    
    # Layout & Scaling
    parser.add_argument("-m", "--margin", type=float, default=0.5, 
                        help="Minimum horizontal margin (left/right) in inches")
    parser.add_argument("-s", "--scale", type=float, default=0.98, 
                        help="Scale factor (0.98 = 98%% size)")
    
    # Grid (0 or None means "Auto-calculate")
    parser.add_argument("--rows", type=int, default=0, help="Grid rows (0 = auto-calculate)")
    parser.add_argument("--cols", type=int, default=0, help="Grid columns (0 = auto-calculate)")
    
    parser.add_argument("--dpi", type=int, default=300, help="Output resolution (DPI)")

    return parser.parse_args()

def main():
    args = parse_arguments()
    
    settings = Settings(
        input_dir=args.input,
        output_file=args.output,
        page_width=args.page_width,
        page_height=args.page_height,
        card_width=args.card_width,
        card_height=args.card_height,
        margin=args.margin,
        scale=args.scale,
        rows=args.rows,
        cols=args.cols,
        dpi=args.dpi
    )
    
    pytcgprint(settings)

if __name__ == "__main__":
    main()