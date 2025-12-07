import argparse
import sys
from math import floor, ceil
from pathlib import Path
from PIL import Image, UnidentifiedImageError

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

def px(inches, dpi):
    """Convert inches to pixels."""
    return int(inches * dpi)

def get_image_files(input_dir):
    """Scans directory for valid images."""
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        sys.exit(1)

    valid_files = []
    # Sort files to ensure page order is consistent
    all_files = sorted([f for f in input_path.iterdir() if f.is_file()])
    
    print(f"Scanning '{input_dir}' for images...")
    for f in all_files:
        try:
            with Image.open(f) as img:
                img.verify() 
                valid_files.append(f)
        except (UnidentifiedImageError, OSError):
            continue 
            
    if not valid_files:
        print("Error: No valid images found in input directory.")
        sys.exit(1)

    return valid_files

def calculate_layout(args):
    """
    Calculates grid dimensions (if not provided) and pixel spacing.
    """
    page_w = px(args.page_width, args.dpi)
    page_h = px(args.page_height, args.dpi)
    
    # Scaled Card Size
    card_w = px(args.card_width * args.scale, args.dpi)
    card_h = px(args.card_height * args.scale, args.dpi)
    
    margin_x = px(args.margin, args.dpi)

    # --- AUTO-COMPUTE GRID IF NEEDED ---
    # Max width available for cards = Page - Margins
    # We essentially divide available space by card width. 
    # (Note: This is a "tight fit" calc; gaps are calculated after)
    
    avail_w = page_w - (2 * margin_x)
    
    cols = args.cols
    if cols <= 0:
        cols = floor(avail_w / card_w)
        if cols < 1:
            print("Error: Page too narrow for even one card + margins!")
            sys.exit(1)

    rows = args.rows
    if rows <= 0:
        # We start with a safe estimate for vertical fit
        # We need to account for the fact that gaps add height
        # Simple iterative check to find max rows that fit
        test_rows = 1
        while True:
            # Theoretical height needed = (rows * card) + ((rows-1) * gap)
            # Since we don't know the gap yet (it depends on horizontal fit), 
            # we assume the vertical gap will eventually match the horizontal gap.
            
            # 1. Calc Horizontal gap for 'cols'
            total_card_w = cols * card_w
            rem_x = page_w - (2 * margin_x) - total_card_w
            gap = rem_x // (cols - 1) if cols > 1 else 0
            
            # 2. Check if next row fits vertically with that gap
            next_rows = test_rows + 1
            needed_h = (next_rows * card_h) + ((next_rows - 1) * gap)
            
            # Ensure we leave a tiny buffer (e.g. 0.25") for printer grip if possible
            buffer_y = px(0.25, args.dpi) * 2
            
            if needed_h > (page_h - buffer_y):
                rows = test_rows
                break
            test_rows += 1

    # --- FINAL GEOMETRY ---
    
    # Recalculate gap based on final COLS
    total_card_w = cols * card_w
    available_gap_space = page_w - (2 * margin_x) - total_card_w
    
    gap = 0
    if cols > 1:
        gap = available_gap_space // (cols - 1)
    
    # Calculate Total Grid Height
    total_grid_h = (rows * card_h) + ((rows - 1) * gap)
    
    # Verify vertical fit one last time
    if total_grid_h > page_h:
        print(f"Error: {rows} rows is too tall for this page height.")
        sys.exit(1)

    # Center Vertically
    margin_y = (page_h - total_grid_h) // 2
    
    return {
        "page_size": (page_w, page_h),
        "card_size": (card_w, card_h),
        "margin_x": margin_x,
        "margin_y": margin_y,
        "gap": gap,
        "cols": cols,
        "rows": rows,
        "cards_per_page": cols * rows
    }

def create_page(image_paths, layout, args):
    page = Image.new('RGB', layout['page_size'], 'white')
    
    cw, ch = layout['card_size']
    gap = layout['gap']
    cols = layout['cols']
    
    for idx, img_path in enumerate(image_paths):
        try:
            with Image.open(img_path) as img:
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    img = img.convert("RGBA")
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[3])
                    img = bg
                else:
                    img = img.convert("RGB")

                img = img.resize((cw, ch), Image.Resampling.LANCZOS)
                
                # Grid Position
                col = idx % cols
                row = idx // cols
                
                x = layout['margin_x'] + (col * (cw + gap))
                y = layout['margin_y'] + (row * (ch + gap))
                
                page.paste(img, (x, y))
        except Exception as e:
            print(f"Warning: Could not process {img_path.name}: {e}")

    return page

def main():
    args = parse_arguments()
    
    image_files = get_image_files(args.input)
    layout = calculate_layout(args)
    
    total_images = len(image_files)
    cpp = layout['cards_per_page']
    
    if cpp == 0:
        print("Error: Layout calculation resulted in 0 cards per page.")
        sys.exit(1)

    total_pages = ceil(total_images / cpp)
    
    print(f"Found {total_images} images.")
    print(f"Auto-Computed Layout: {layout['cols']} Cols x {layout['rows']} Rows")
    print(f"Card Scale: {int(args.scale*100)}% | Gap: {layout['gap']} px")
    
    pages = []
    
    for i in range(total_pages):
        start = i * cpp
        end = start + cpp
        batch = image_files[start:end]
        
        print(f"Generating page {i+1}/{total_pages}...")
        page_img = create_page(batch, layout, args)
        pages.append(page_img)
        
    if pages:
        output_path = Path(args.output)
        print(f"Saving to {output_path.absolute()}...")
        pages[0].save(
            output_path,
            "PDF",
            resolution=args.dpi,
            save_all=True,
            append_images=pages[1:]
        )
        print("Done.")

if __name__ == "__main__":
    main()