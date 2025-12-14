import sys
from math import ceil, floor
from pathlib import Path
from PIL import Image, UnidentifiedImageError

from dataclasses import dataclass

@dataclass
class Settings:
    input_dir: str
    output_file: str
    page_width: float
    page_height: float
    card_width: float
    card_height: float
    margin: float
    scale: float
    rows: int
    cols: int
    dpi: int

def px(inches, dpi):
    """Convert inches to pixels."""
    return int(inches * dpi)

def get_image_files(settings: Settings):
    """Scans directory for valid images."""
    input_path = Path(settings.input_dir)
    if not input_path.exists():
        print(f"Error: Input directory '{settings.input_dir}' does not exist.")
        return []

    valid_files = []
    # Sort files to ensure page order is consistent
    all_files = sorted([f for f in input_path.iterdir() if f.is_file()])
    
    print(f"Scanning '{settings.input_dir}' for images...")
    for f in all_files:
        try:
            with Image.open(f) as img:
                img.verify() 
                valid_files.append(f)
        except (UnidentifiedImageError, OSError):
            continue 
            
    if not valid_files:
        print("Error: No valid images found in input directory.")
        return []

    return valid_files

def calculate_layout(settings: Settings):
    """
    Calculates grid dimensions (if not provided) and pixel spacing.
    """
    page_w = px(settings.page_width, settings.dpi)
    page_h = px(settings.page_height, settings.dpi)
    
    # Scaled Card Size
    card_w = px(settings.card_width * settings.scale, settings.dpi)
    card_h = px(settings.card_height * settings.scale, settings.dpi)
    
    margin_x = px(settings.margin, settings.dpi)

    # --- AUTO-COMPUTE GRID IF NEEDED ---
    # Max width available for cards = Page - Margins
    # We essentially divide available space by card width. 
    # (Note: This is a "tight fit" calc; gaps are calculated after)
    
    avail_w = page_w - (2 * margin_x)
    
    cols = settings.cols
    if cols <= 0:
        cols = floor(avail_w / card_w)
        if cols < 1:
            raise ValueError("Page too narrow for even one card + margins!")

    rows = settings.rows
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
            buffer_y = px(0.25, settings.dpi) * 2
            
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
        raise ValueError(f"{rows} rows is too tall for this page height.")

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

def create_page(image_paths, layout):
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

def pytcgprint(settings: Settings):
    try:
        image_files = get_image_files(settings)
        total_images = len(image_files)
        
        layout = calculate_layout(settings)
        
        print(f"Found {total_images} images.")
        print(f"Auto-Computed Layout: {layout['cols']} Cols x {layout['rows']} Rows")
        print(f"Card Scale: {int(settings.scale*100)}% | Gap: {layout['gap']} px")
        
        pages = []
        cards_per_page = layout['cards_per_page']
        total_pages = ceil(total_images / cards_per_page)
        
        for i in range(total_pages):
            start = i * cards_per_page
            end = start + cards_per_page
            batch = image_files[start:end]
            
            print(f"Generating page {i+1}/{total_pages}...")
            page_img = create_page(batch, layout)
            
            pages.append(page_img)
            
        if pages:
            print(f"Saving output PDF to '{settings.output_file}'...")
            pages[0].save(
                settings.output_file,
                save_all=True,
                append_images=pages[1:],
                resolution=settings.dpi,
                quality=95
            )
            print("Done.")
        else:
            print("No pages were created.")

        return pages
    except ValueError as e:
        print(f"Error: {e}")
        return []
