import os
from math import ceil
from PIL import Image

# --- CONFIGURATION ---
INPUT_FOLDER = 'cards'          # Folder containing your card images
OUTPUT_FILENAME = 'output_deck.pdf'
DPI = 300

# Physical dimensions (inches)
PAGE_WIDTH_IN = 8.5
PAGE_HEIGHT_IN = 11.0
CARD_WIDTH_IN = 2.5
CARD_HEIGHT_IN = 3.5

# Requested Margins
MARGIN_X_IN = 0.5
# Note: 3 cards * 3.5" = 10.5". Page is 11". Remaining space is 0.5".
# We set vertical margin to 0.25" to center the grid vertically.
MARGIN_Y_IN = 0.25 

# Grid Layout
COLS = 3
ROWS = 3
CARDS_PER_PAGE = COLS * ROWS

# --- CALCULATIONS ---
# Convert inches to pixels
def in_to_px(inches):
    return int(inches * DPI)

PAGE_SIZE = (in_to_px(PAGE_WIDTH_IN), in_to_px(PAGE_HEIGHT_IN))
CARD_SIZE = (in_to_px(CARD_WIDTH_IN), in_to_px(CARD_HEIGHT_IN))
MARGIN_X = in_to_px(MARGIN_X_IN)
MARGIN_Y = in_to_px(MARGIN_Y_IN)

def create_card_sheet(image_files):
    """
    Creates a single page image with a grid of cards.
    """
    # Create a blank white page (RGB)
    page = Image.new('RGB', PAGE_SIZE, 'white')
    
    # Calculate spacing (gap between cards)
    # Available space for gaps = Page Width - (2 * Margin) - (Cols * Card Width)
    total_card_width = COLS * CARD_SIZE[0]
    available_width_space = PAGE_SIZE[0] - (2 * MARGIN_X) - total_card_width
    
    # Determine horizontal gap size (distribute remaining space evenly between cols)
    if COLS > 1:
        gap_x = available_width_space // (COLS - 1)
    else:
        gap_x = 0
        
    # Standard calculations result in 0 gap for 2.5" cards on 8.5" paper with 0.5" margins
    # Force gap to 0 if it calculates to negative due to rounding
    gap_x = max(0, gap_x) 
    gap_y = 0 # Vertical fit is tight (0.25" margins), so 0 gap is enforced.

    for index, img_path in enumerate(image_files):
        try:
            # Load and Resize Image
            img = Image.open(img_path)
            
            # optional: handle RGBA to RGB conversion if using PNGs with transparency
            if img.mode == 'RGBA':
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            
            # High-quality resize to target card dimension
            img = img.resize(CARD_SIZE, Image.Resampling.LANCZOS)
            
            # Calculate Position (Row/Col)
            col = index % COLS
            row = index // COLS
            
            x_pos = MARGIN_X + (col * (CARD_SIZE[0] + gap_x))
            y_pos = MARGIN_Y + (row * (CARD_SIZE[1] + gap_y))
            
            page.paste(img, (x_pos, y_pos))
            
        except Exception as e:
            print(f"Error processing {img_path}: {e}")

    return page

def main():
    # 1. Get all images from folder
    valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
    files = [os.path.join(INPUT_FOLDER, f) for f in os.listdir(INPUT_FOLDER) 
             if f.lower().endswith(valid_extensions)]
    
    files.sort() # Ensure consistent order
    
    if not files:
        print(f"No images found in folder '{INPUT_FOLDER}'")
        return

    print(f"Found {len(files)} images. Generating PDF...")

    # 2. Chunk images into groups of 9 (CARDS_PER_PAGE)
    pages = []
    total_pages = ceil(len(files) / CARDS_PER_PAGE)

    for i in range(total_pages):
        start_idx = i * CARDS_PER_PAGE
        end_idx = start_idx + CARDS_PER_PAGE
        batch = files[start_idx:end_idx]
        
        print(f"Creating page {i+1}/{total_pages}...")
        sheet_image = create_card_sheet(batch)
        pages.append(sheet_image)

    # 3. Save to PDF
    # The first image is saved, and the rest are appended
    if pages:
        pages[0].save(
            OUTPUT_FILENAME, 
            "PDF", 
            resolution=DPI, 
            save_all=True, 
            append_images=pages[1:]
        )
        print(f"Success! Saved to {OUTPUT_FILENAME}")

if __name__ == "__main__":
    # Create the folder if it doesn't exist for testing
    if not os.path.exists(INPUT_FOLDER):
        os.makedirs(INPUT_FOLDER)
        print(f"Created folder '{INPUT_FOLDER}'. Please put your images there and run again.")
    else:
        main()
