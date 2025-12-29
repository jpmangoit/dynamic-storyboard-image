# engine/layout_physics.py
import os
from PIL import Image

A3_W, A3_H = 4961, 3508
MARGIN = 200

# ----- TEMPLATE DEFINITIONS -----
# Rectangles defined as (x, y, width, height) in pixels
# Or percentage tuples (x_pct, y_pct, w_pct, h_pct) for scalability

TEMPLATES = {
    "asymmetric_left": {
        "description": "Large Hero on Left, 2 Columns of Accesssories on Right",
        "slots": {
            "hero_slot":  (200, 200, 2000, 3108), # Left 40% tall
            "secondary_1": (2400, 200, 1100, 1400), # Top center
            "secondary_2": (3600, 200, 1100, 1400), # Top right
            "filler_1":   (2400, 1800, 700, 700),  # Mid grid
            "filler_2":   (3200, 1800, 700, 700),
            "filler_3":   (4000, 1800, 700, 700),
            "tiny_1":     (2400, 2600, 500, 500), # Bottom grid
            "tiny_2":     (3000, 2600, 500, 500),
            "tiny_3":     (3600, 2600, 500, 500)
        }
    },
    "waterfall_right": {
        "description": "Hero Full Height Right, Cascading Small Items Left",
        "slots": {
            "hero_slot":  (2761, 200, 2000, 3108), # Right side
            "secondary_1": (200, 200, 1000, 1000), # Top Left
            "secondary_2": (1300, 500, 1000, 1000), # Offset down
            "filler_1":   (200, 1300, 900, 900),
            "filler_2":   (1200, 1600, 900, 900),
            "tiny_1":     (200, 2400, 600, 600),
            "tiny_2":     (900, 2600, 600, 600),
            "tiny_3":     (1600, 2400, 600, 600)
        }
    },
    "editorial_grid": {
        "description": "Clean 3x2 Grid with Hero spanning 2 slots",
        "slots": {
            "hero_slot":  (200, 200, 2200, 1450),    # Top Left Quad
            "secondary_1": (2500, 200, 2200, 1450),  # Top Right
            "secondary_2": (200, 1850, 1000, 1450),  # Bottom Left 1
            "filler_1":   (1300, 1850, 1000, 1450), # Bottom Left 2
            "filler_2":   (2500, 1850, 1000, 1450), # Bottom Right 1
            "tiny_1":     (3600, 1850, 1100, 700),  # Split cell
            "tiny_2":     (3600, 2650, 1100, 650)
        }
    },
    "final_spec": {
        "description": "MASTER SPEC: 1:1 Parity, Hard Labels, Tilted Elements, Z-Depth",
        "slots": {
            # 1. Hero (Tea Towel) - Far Left, 40% height (3508 * 0.4 = 1403)
            # Centered vertically: (3508 - 1403) / 2 = 1052
            "hero_left":   {"rect": (150, 1052, 1600, 1403), "rotation": 0, "layer": 5, "label": "Tea Towel"},
            
            # 5. Anchor (Theale Bag) - Far Right (Shifted left for overlap/density)
            "anchor_right": {"rect": (2800, 400, 2000, 2800), "rotation": 5, "layer": 4, "label": "Theale Bag"},
            
            # 4. Mounted Print (Secondary) - Central Vertical Core
            "print_back": {"rect": (1900, 450, 1300, 1600), "rotation": 0, "layer": 2, "label": "Mounted Print"},
            
            # 2. Magnet (Accessory) - Upper Mid
            "magnet": {"rect": (1650, 500, 600, 600), "rotation": -10, "layer": 8, "label": "Fridge Magnet"},
            
            # 3. Keyring (Accessory) - Upper Mid
            "keyring": {"rect": (2250, 600, 400, 500), "rotation": 10, "layer": 9, "label": "Keyring"},
            
            # 6. Notebook (Support) - Lower Mid-Left
            "notebook": {"rect": (1500, 1900, 1200, 1100), "rotation": -5, "layer": 6, "label": "A5 Notebook Stitched"},
            
            # 7. Greetings Card (Support) - Lower Mid
            "card": {"rect": (2500, 2000, 900, 1200), "rotation": 0, "layer": 7, "label": "Greetings Card"},
            
            # 8. Mugs (Support) - Bottom Center Cluster
            "mugs_cluster": {"rect": (1800, 2600, 1700, 800), "rotation": 0, "layer": 10, "label": "Durham Mug"}
        }
    },
    "reference_1_match": {
        "description": "Reference-1 Layout: Matching reference-1.png positions and sizes",
        "slots": {
            # Tea Towel - Left side, large vertical
            "hero_left":   {"rect": (100, 700, 1700, 2000), "rotation": 0, "layer": 5, "label": ""},
            
            # Bag - Right side, moved down to align with towel
            "anchor_right": {"rect": (3300, 700, 1700, 2400), "rotation": 0, "layer": 4, "label": ""},
            
            # Frame - Upper right
            "print_back": {"rect": (3300, 300, 900, 1100), "rotation": 0, "layer": 2, "label": ""},
            
            # Magnet - Near towel on left side
            "magnet": {"rect": (1900, 800, 550, 550), "rotation": 0, "layer": 8, "label": ""},
            
            # Keyring - Near magnet
            "keyring": {"rect": (2500, 850, 380, 450), "rotation": 0, "layer": 9, "label": ""},
            
            # Notebook - Lower left (1200x1100 at y=1700)
            "notebook": {"rect": (1600, 1700, 1200, 1100), "rotation": 0, "layer": 6, "label": ""},
            
            # Card - RIGHT NEXT to notebook, centered vertically (notebook center: 1700+550=2250, card center: 2250-440=1810)
            "card": {"rect": (2820, 1810, 960, 880), "rotation": 0, "layer": 7, "label": ""},
            
            # Mug - DOUBLED size (1700x2000), moved up to align with towel
            "mugs_cluster": {"rect": (1850, 700, 1700, 2000), "rotation": 0, "layer": 10, "label": ""}
        }
    }
}

def get_image_aspect(filepath):
    try:
        with Image.open(filepath) as img:
            return img.width / img.height
    except Exception:
        return 1.0

def fit_image_to_slot(img_w, img_h, slot_w, slot_h):
    """
    Returns (w, h, x_offset, y_offset) to fit image INSIDE slot maintaining aspect ratio.
    Centered in the slot.
    """
    aspect = img_w / img_h
    slot_aspect = slot_w / slot_h
    
    if aspect > slot_aspect: 
        # Image is wider than slot -> Fit to Width
        w = int(slot_w * 1.15) # Inflate 15% for density
        h = int(w / aspect)
    else:
        # Image is taller than slot -> Fit to Height
        h = int(slot_h * 1.15) # Inflate 15%
        w = int(h * aspect)
        
    x_off = (slot_w - w) // 2
    y_off = (slot_h - h) // 2
    return w, h, x_off, y_off

def compute_layout(ai_layout):
    placements = []
    
    # 1. Get Template Choice
    template_key = ai_layout.get("template_name", "asymmetric_left")
    # Fuzzy match or default
    if template_key not in TEMPLATES:
        template_key = "asymmetric_left"
        
    template = TEMPLATES[template_key]
    slots = template["slots"]
    
    assignments = ai_layout.get("assignments", {})
    
    # 2. Fill Slots
    for slot_name, filename in assignments.items():
        if not filename: continue
        if slot_name not in slots: continue
        
        filepath = os.path.join("products", filename)
        if not os.path.exists(filepath): continue
        
        # Get Slot Data
        slot_data = slots[slot_name]
        
        # Handle Format: Tuple (Legacy) vs Dict (Spec V1)
        if isinstance(slot_data, tuple) or isinstance(slot_data, list):
            sx, sy, sw, sh = slot_data
            rot = 0
            layer = 5
            label = ""
        elif isinstance(slot_data, dict):
            sx, sy, sw, sh = slot_data["rect"]
            rot = slot_data.get("rotation", 0)
            layer = slot_data.get("layer", 5)
            label = slot_data.get("label", "")
        else:
            continue
        
        # Get Real Image Aspect
        try:
             with Image.open(filepath) as img:
                 orig_w, orig_h = img.size
        except:
             orig_w, orig_h = 1000, 1000 # Default if image cannot be opened
             
        # Fit logic (Allow 15% inflation for density)
        w, h, dx, dy = fit_image_to_slot(orig_w, orig_h, sw, sh)
        
        # Final Coords
        final_x = sx + dx
        final_y = sy + dy
        
        placements.append({
            "file": filename,
            "x": final_x,
            "y": final_y,
            "width": w,
            "height": h,
            "rotation": rot, 
            "depth_layer": layer,
            "slot_name": slot_name, # Added slot_name
            "label": label          # Added label
        })

    return placements