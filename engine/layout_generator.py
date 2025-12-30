import math
import random
from PIL import Image
from engine import templates
import os

def get_safe_area(config):
    """Extract safe area from config."""
    canvas = config["canvas"]
    margin = canvas.get("safe_margin_px", 150)
    w = canvas["width_px"]
    h = canvas["height_px"]
    
    # Account for Header/Footer if they exist
    header_h = config.get("header", {}).get("area", {}).get("h", 0)
    footer_h = config.get("footer", {}).get("area", {}).get("h", 0)
    
    return {
        "x": margin,
        "y": margin + header_h,
        "w": w - (margin * 2),
        "h": h - (margin * 2) - header_h - footer_h,
        "full_w": w,
        "full_h": h
    }

def analyze_aspect_ratios(inventory):
    """Returns a dict of {id: aspect_ratio} for all items."""
    aspects = {}
    for role, path in inventory.items():
        if os.path.exists(path):
            try:
                with Image.open(path) as img:
                    width, height = img.size
                    aspects[role] = width / height
            except:
                aspects[role] = 1.0 # default square
    return aspects

def generate_dynamic_layout(config, inventory, preferred_template=None):
    """
    Generates a layout configuration based on the product inventory using the Template Engine.
    """
    print(f"[GEN] Inventory: {len(inventory)} items.")
    
    # Analyze Image Shapes (Aspect Ratios)
    item_aspects = analyze_aspect_ratios(inventory)
    
    # 1. Get all valid options from the Template Engine
    options = templates.get_valid_templates(config, inventory, item_aspects)
    
    if not options:
        print("[GEN] No valid templates found!")
        return []

    print(f"[GEN] Found {len(options)} valid layout strategies:")
    
    # Check Preferred Template
    if preferred_template:
        print(f"[GEN] User requested template: '{preferred_template}'")
        # Try to find exact match
        matches = [opt for opt in options if preferred_template in opt['name']]
        if matches:
            selected = matches[0]
            print(f"[GEN] Success! Using preferred: {selected['name']}")
            return selected['containers']
        else:
            print(f"[WARN] Preferred template '{preferred_template}' not found or invalid for this inventory. Falling back to Auto-Select.")

    for opt in options:
        print(f"  - {opt['name']} ({len(opt['containers'])} slots)")
        
    # 2. Pick One Randomly
    selected = random.choice(options)
    print(f"[GEN] Selected Strategy: {selected['name']}")
    
    return selected['containers']


def make_container(id, x, y, w, h):
    """Helper to create standard container dict."""
    return {"id": id, "x": int(x), "y": int(y), "w": int(w), "h": int(h)}

def layout_single_hero_asymmetric(safe, heroes, supports, accessories):
    """
    Layout:
    | HERO (60%) |  Grid (40%) |
    """
    containers = []
    
    # Golden Ratio-ish split (60/40)
    split_x = int(safe['w'] * 0.58) 
    gap = int(safe['w'] * 0.04)
    
    # 1. Place Hero (Left, Large)
    hero_w = split_x
    containers.append(make_container(heroes[0], safe['x'], safe['y'], hero_w, safe['h']))
    
    # 2. Right Column (Supports + Accessories)
    rx = safe['x'] + hero_w + gap
    rw = safe['w'] - hero_w - gap
    
    # Combine remaining items
    remaining = supports + accessories
    count = len(remaining)
    
    if count == 0: return containers
    
    # Create a layout for the right column
    # If we have many small items, cluster them at the bottom
    
    # Simple logic: Stack them, but group accessories
    current_y = safe['y']
    
    # If mixed accessories and supports, give supports more height
    # Heuristics: Support = 2 units, Accessory = 1 unit
    total_units = (len(supports) * 2) + len(accessories)
    unit_h = safe['h'] / total_units
    
    # Place Supports first
    for item in supports:
        h = unit_h * 2
        containers.append(make_container(item, rx, current_y, rw, h))
        current_y += h
        
    # Place Accessories (clustered in pairs if possible)
    acc_count = len(accessories)
    if acc_count > 0:
        # Make a grid for accessories within the remaining space
        acc_h = safe['h'] - (current_y - safe['y'])
        
        # Grid logic for accessories
        cols = 2 if acc_count >= 2 else 1
        rows = math.ceil(acc_count / cols)
        
        cell_w = rw / cols
        cell_h = acc_h / rows
        
        for i, item in enumerate(accessories):
            r = i // cols
            c = i % cols
            cx = rx + (c * cell_w)
            cy = current_y + (r * cell_h)
            
            # Add padding to accessories so they float
            pad = 20
            containers.append(make_container(item, cx+pad, cy+pad, cell_w-(pad*2), cell_h-(pad*2)))

    return containers

def layout_split_wings(safe, heroes, supports, accessories):
    """
    Layout:
    | HERO 1 |   CENTER STACK   | HERO 2 |
    """
    containers = []
    
    # 25% - 50% - 25% Split (Wide Center) or 30-40-30
    w_hero = int(safe['w'] * 0.28)
    gap = int(safe['w'] * 0.03)
    w_center = safe['w'] - (w_hero * 2) - (gap * 2)
    
    # Left Hero
    containers.append(make_container(heroes[0], safe['x'], safe['y'], w_hero, safe['h']))
    
    # Right Hero
    containers.append(make_container(heroes[1], safe['x'] + safe['w'] - w_hero, safe['y'], w_hero, safe['h']))
    
    # Center Column
    cx = safe['x'] + w_hero + gap
    
    # Mix items
    center_items = supports + accessories
    if not center_items: return containers
    
    # Layout Center: "Scatter Cluster"
    # We define a few "slots" in the center and fill them
    # Supports get main slots, accessories get shared slots
    
    valid_supports = [i for i in center_items if i in supports]
    valid_accs = [i for i in center_items if i in accessories]
    
    # Define slots
    slots_count = len(valid_supports) + (1 if valid_accs else 0)
    slot_h = safe['h'] / slots_count
    
    current_y = safe['y']
    
    # Place Supports
    for item in valid_supports:
        # Alternating alignment for interest
        # offset = random.choice([-20, 0, 20])
        containers.append(make_container(item, cx, current_y, w_center, slot_h))
        current_y += slot_h
        
    # Place Accessories in the last slot as a group
    if valid_accs:
        # 2x2 grid for accessories?
        acc_rows = math.ceil(len(valid_accs) / 2)
        acc_h = slot_h / acc_rows
        acc_w = w_center / 2
        
        for i, item in enumerate(valid_accs):
            r = i // 2
            c = i % 2
            ax = cx + (c * acc_w)
            ay = current_y + (r * acc_h)
            
            # shrink them a bit to look like scattered items
            containers.append(make_container(item, ax + 20, ay + 20, acc_w - 40, acc_h - 40))

    return containers

def layout_mosaic(safe, items):
    """Masonry for when there are no dominant heroes."""
    containers = []
    n = len(items)
    if n == 0: return []
    
    cols = 3
    rows = math.ceil(n / cols)
    
    w_cell = safe['w'] / cols
    h_cell = safe['h'] / rows
    
    for i, item in enumerate(items):
        r = i // cols
        c = i % cols
        containers.append(make_container(item, safe['x'] + c*w_cell, safe['y'] + r*h_cell, w_cell, h_cell))
        
    return containers

