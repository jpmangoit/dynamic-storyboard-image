import random
import json
import math
import os

# ==============================================================================
# 1. FIXED LAYOUTS (Legacy JSON)
# ==============================================================================
import glob

# ==============================================================================
# 1. FIXED LAYOUTS (Legacy JSON + External)
# ==============================================================================
def load_legacy_layouts(templates_dir="templates"):
    """Loads fixed layouts from JSON files in the templates directory."""
    presets = {}
    
    # Load External Templates (templates/*.json)
    ext_files = glob.glob(os.path.join(templates_dir, "*.json"))
    for ext in ext_files:
        try:
            with open(ext, 'r') as f:
                data = json.load(f)
                
                # Check for "presets" key (collection) or "containers" key (single layout)
                if "presets" in data:
                    presets.update(data["presets"])
                elif "containers" in data:
                    # Use filename as layout name if not a collection
                    name = os.path.basename(ext).replace(".json", "")
                    presets[name] = data
                    
        except Exception as e:
            print(f"[WARN] Failed to load external template {ext}: {e}")
            
    return presets

# ==============================================================================
# 2. FLEXIBLE ARCHETYPES (The "Digitized" Mockups)
# ==============================================================================
# Each function takes (safe_area, heroes, supports, accessories, item_aspects) 

def make_container(id, x, y, w, h):
    return {"id": id, "x": int(x), "y": int(y), "w": int(w), "h": int(h)}

def layout_hero_left_grid_right(safe, heroes, supports, accessories, item_aspects={}):
    """Archetype: Big Hero Left, Sized Grid Right"""
    if len(heroes) != 1: return None
    
    containers = []
    
    # Hero: 45% Width
    hero_w = int(safe['w'] * 0.45)
    gap = int(safe['w'] * 0.05)
    
    containers.append(make_container(heroes[0], safe['x'], safe['y'], hero_w, safe['h']))
    
    # Right Sized Grid
    # Logic: 
    # - Supports (Large/Medium) get 1 full cell.
    # - Accessories (Small/Tiny) share a cell (2 per cell).
    
    rx = safe['x'] + hero_w + gap
    rw = safe['w'] - hero_w - gap
    
    # Calculate slots needed
    # Each Support needs 1 slot.
    # Accessories need 0.5 slots (ceil(count/2)).
    slots_needed = len(supports) + math.ceil(len(accessories) / 2)
    
    if slots_needed == 0: return containers
    
    cols = 2
    rows = math.ceil(slots_needed / cols)
    
    cell_w = (rw - gap) / cols
    cell_h = (safe['h'] - (gap * (rows-1))) / rows
    
    # Populate Grid Cells
    grid_cells = []
    for r in range(rows):
        for c in range(cols):
            cx = rx + (c * (cell_w + gap))
            cy = safe['y'] + (r * (cell_h + gap))
            grid_cells.append((cx, cy, cell_w, cell_h))
            
    # Fill cells
    current_cell_idx = 0
    
    # 1. Place Supports (Full Cell)
    for item in supports:
        if current_cell_idx >= len(grid_cells): break
        cx, cy, cw, ch = grid_cells[current_cell_idx]
        containers.append(make_container(item, cx, cy, cw, ch))
        current_cell_idx += 1
        
    # 2. Place Accessories (Split Cell)
    acc_idx = 0
    while acc_idx < len(accessories):
        if current_cell_idx >= len(grid_cells): break
        
        # Take the cell
        cx, cy, cw, ch = grid_cells[current_cell_idx]
        
        # Determine how many items to put here (1 or 2)
        remaining_acc = len(accessories) - acc_idx
        
        if remaining_acc >= 2:
            # Split Vertically (Top/Bottom)
            sh = (ch - 20) / 2
            containers.append(make_container(accessories[acc_idx], cx, cy, cw, sh))
            containers.append(make_container(accessories[acc_idx+1], cx, cy + sh + 20, cw, sh))
            acc_idx += 2
        else:
            # Just one left, put it in center
            containers.append(make_container(accessories[acc_idx], cx, cy, cw, ch))
            acc_idx += 1
            
        current_cell_idx += 1
            
    return containers

def layout_hero_right_grid_left(safe, heroes, supports, accessories, item_aspects={}):
    """Archetype: Big Hero Right, Sized Grid Left"""
    if len(heroes) != 1: return None
    
    containers = []
    hero_w = int(safe['w'] * 0.45)
    gap = int(safe['w'] * 0.05)
    
    # Hero Right
    hx = safe['x'] + safe['w'] - hero_w
    containers.append(make_container(heroes[0], hx, safe['y'], hero_w, safe['h']))
    
    # Left Sized Grid
    lw = safe['w'] - hero_w - gap
    
    slots_needed = len(supports) + math.ceil(len(accessories) / 2)
    if slots_needed == 0: return containers
    
    cols = 2
    rows = math.ceil(slots_needed / cols)
    cell_w = (lw - gap) / cols
    cell_h = (safe['h'] - (gap * (rows-1))) / rows
    
    grid_cells = []
    for r in range(rows):
        for c in range(cols):
            cx = safe['x'] + (c * (cell_w + gap))
            cy = safe['y'] + (r * (cell_h + gap))
            grid_cells.append((cx, cy, cell_w, cell_h))
            
    current_cell_idx = 0
    
    # 1. Place Supports (Full Cell)
    for item in supports:
        if current_cell_idx >= len(grid_cells): break
        cx, cy, cw, ch = grid_cells[current_cell_idx]
        containers.append(make_container(item, cx, cy, cw, ch))
        current_cell_idx += 1
        
    # 2. Place Accessories (Split Cell)
    acc_idx = 0
    while acc_idx < len(accessories):
        if current_cell_idx >= len(grid_cells): break
        
        cx, cy, cw, ch = grid_cells[current_cell_idx]
        remaining_acc = len(accessories) - acc_idx
        
        if remaining_acc >= 2:
            sh = (ch - 20) / 2
            containers.append(make_container(accessories[acc_idx], cx, cy, cw, sh))
            containers.append(make_container(accessories[acc_idx+1], cx, cy + sh + 20, cw, sh))
            acc_idx += 2
        else:
            containers.append(make_container(accessories[acc_idx], cx, cy, cw, ch))
            acc_idx += 1
            
        current_cell_idx += 1

    return containers

def layout_hero_top_band_bottom(safe, heroes, supports, accessories, item_aspects={}):
    """Archetype: Hero Top (Landscape), Band of items Bottom (Row 2 Style 1)"""
    # CONSTRAINT: STRICT 1 HERO
    if len(heroes) != 1: return None

    # CONSTRAINT: HERO MUST BE LANDSCAPE-ISH (> 1.0)
    # This layout forces the hero into a wide, short box (Full Width, 60% Height).
    # If the hero is Portrait (like a Tote Bag), it will shrink massively to fit the height, leaving huge side gaps.
    # Therefore, we reject Portrait items for this specific layout.
    hero_id = heroes[0]
    aspect = item_aspects.get(hero_id, 1.0) 
    if aspect < 1.0: 
        # Reject Portrait items
        return None
    
    containers = []
    
    # Hero Top 60% Height
    hero_h = int(safe['h'] * 0.60)
    gap = int(safe['h'] * 0.05)
    
    containers.append(make_container(heroes[0], safe['x'], safe['y'], safe['w'], hero_h))
    
    # Bottom Band
    remaining = supports + accessories
    if not remaining: return containers
    
    by = safe['y'] + hero_h + gap
    bh = safe['h'] - hero_h - gap
    
    cols = len(remaining)
    cell_w = (safe['w'] - (gap * (cols-1))) / cols
    
    for i, item in enumerate(remaining):
        cx = safe['x'] + (i * (cell_w + gap))
        containers.append(make_container(item, cx, by, cell_w, bh))
        
    return containers

def layout_three_column_balanced(safe, heroes, supports, accessories, item_aspects={}):
    """Archetype: Hero Left, Hero Right, Stack Middle (Row 2 Style 2)"""
    # CONSTRAINT: AT LEAST 2 HEROES (Ideal for 2, works for 3 if we handle 3rd well)
    # If 3 heroes, 3rd acts as support in middle (ok, but risky for 'towel')
    # Let's be strict: EXACTLY 2 HEROES for this balanced look
    if len(heroes) != 2: return None
    
    containers = []
    col_w = (safe['w'] - (80*2)) / 3
    
    # Left
    containers.append(make_container(heroes[0], safe['x'], safe['y'], col_w, safe['h']))
    # Right
    containers.append(make_container(heroes[1], safe['x'] + (col_w+80)*2, safe['y'], col_w, safe['h']))
    
    # Middle
    remaining = supports + accessories + heroes[2:]
    if not remaining: return containers
    
    mx = safe['x'] + col_w + 80
    
    rows = len(remaining)
    cell_h = (safe['h'] - (80 * (rows-1))) / rows
    
    for i, item in enumerate(remaining):
        cy = safe['y'] + (i * (cell_h + 80))
        containers.append(make_container(item, mx, cy, col_w, cell_h))
        
    return containers

def layout_quadrant_split(safe, heroes, supports, accessories, item_aspects={}):
    """Archetype: 4 Equal Quadrants (Row 3 Style 1)"""
    # Strategy: Good for 2-4 Large items (Heroes/Supports)
    # If we have 2 Heroes, we put them in Q1 and Q2 (Top) to give them prominence
    
    large_items = heroes + supports
    if len(large_items) < 2: return None # Need at least 2 big things to justify quadrants
    # CONSTRAINT: NO MORE THAN 3 LARGE ITEMS
    # If we have 4+ large items (heroes+supports), one will be forced into the 'Cluster Grid' (Q4).
    # This demotes a "Large/Medium" item to "Tiny/Accessory" size, which violates the user's intent.
    # We should reject this layout and let the 'Grid Layouts' handle 4+ large items properly.
    if len(large_items) > 3: return None
    
    containers = []
    all_items = heroes + supports + accessories
    
    qw = (safe['w'] - 80) / 2
    qh = (safe['h'] - 80) / 2
    
    # Top Left (Hero 1 priority)
    containers.append(make_container(all_items[0], safe['x'], safe['y'], qw, qh))
    
    # Top Right (Hero 2 priority)
    containers.append(make_container(all_items[1], safe['x']+qw+80, safe['y'], qw, qh))
    
    # Bottom Left
    if len(all_items) > 2:
        containers.append(make_container(all_items[2], safe['x'], safe['y']+qh+80, qw, qh))
        
    # Bottom Right
    # Use remaining items clustered in last quadrant if > 4
    extras = all_items[3:]
    
    if len(extras) == 1:
        containers.append(make_container(extras[0], safe['x']+qw+80, safe['y']+qh+80, qw, qh))
    elif len(extras) > 1:
        # Cluster the rest in Q4
        rows = math.ceil(len(extras)/2)
        cw = (qw - 40) / 2
        ch = (qh - (40 * (rows-1))) / rows
        
        start_x = safe['x'] + qw + 80
        start_y = safe['y'] + qh + 80
        
        for i, item in enumerate(extras):
            r = i // 2
            c = i % 2
            containers.append(make_container(item, start_x + c*(cw+40), start_y + r*(ch+40), cw, ch))

    return containers

# List of all flexible generators
GENERATORS = [
    layout_hero_left_grid_right,
    layout_hero_right_grid_left,
    layout_hero_top_band_bottom,
    layout_three_column_balanced,
    layout_quadrant_split
]

# ==============================================================================
# 3. SELECTION LOGIC
# ==============================================================================
def normalize_container(c):
    # Ensure container keys map to what our renderer expects
    # Legacy JSON has 'canvas_x', 'canvas_y', 'width_px'...
    # Our new ones have 'x', 'y', 'w', 'h'
    # We should standardize to new format
    new_c = c.copy()
    if 'canvas_x' in c: new_c['x'] = c['canvas_x']
    if 'canvas_y' in c: new_c['y'] = c['canvas_y']
    if 'width_px' in c: new_c['w'] = c['width_px']
    if 'height_px' in c: new_c['h'] = c['height_px']
    
    # Copy other useful properties
    if 'rotation_deg' in c: new_c['rotation_deg'] = c['rotation_deg']
    if 'size_class' in c: new_c['size_class'] = c['size_class']
    
    # Also need internal 'id' to map to product role
    # Legacy JSON has fixed IDs like "hero_left". We need to map our inventory (e.g. "hero_left") to these.
    # This is tricky: Legacy templates expect SPECIFIC roles.
    # Our inventory has DYNAMIC roles.
    return new_c

def map_inventory_to_legacy(inventory, legacy_containers, item_aspects={}):
    """
    Maps dynamic inventory items to fixed legacy slots using a Best-Fit strategy.
    Prioritizes:
    1. Exact ID Match
    2. Role Match
    3. Aspect Ratio Match (minimizing cropping)
    """
    
    # 1. Check constraints: Hero count
    template_hero_slots = [c for c in legacy_containers if c.get('role') == 'hero']
    inventory_heroes = [k for k in inventory.keys() if 'hero' in k]
    
    if len(template_hero_slots) != len(inventory_heroes):
        return None
        
    mapped = []
    available_items = list(inventory.keys())
    
    # Sort slots to fill: 
    # 1. Heroes first
    # 2. Then by area (Largest slots get first pick of best-aspect items)
    def sort_prio(c):
        is_hero = 0 if c.get('role') == 'hero' else 1
        area = c.get('width_px', 0) * c.get('height_px', 0)
        return (is_hero, -area) # Descending area
        
    sorted_slots = sorted(legacy_containers, key=sort_prio)
    
    for slot in sorted_slots:
        slot_role = slot.get('role', 'support')
        slot_id = slot.get('id', 'unknown')
        
        # Calculate Slot Aspect Ratio
        s_w = slot.get('width_px', 100)
        s_h = slot.get('height_px', 100)
        slot_aspect = s_w / s_h
        
        best_item = None
        best_score = -float('inf')
        
        for item_key in available_items:
            # 1. Strict Role Filter
            # The item key MUST contain the slot role (e.g. 'hero' in 'hero_2')
            if slot_role not in item_key:
                continue
                
            # Calculate Score
            score = 0
            
            # A. Exact ID Match (Overrides everything)
            if item_key == slot_id:
                score += 1000
                
            # B. Aspect Ratio Match
            # We use log difference so 0.5 (1:2) and 2.0 (2:1) are equally "far" from 1.0
            if item_key in item_aspects:
                item_aspect = item_aspects[item_key]
                # Smaller difference is better. 
                # We subtract the difference from score.
                # Weighted factor 50 means a significant aspect deviation matters more than minor role variations
                diff = abs(math.log(slot_aspect / item_aspect))
                score -= (diff * 50)
            
            if score > best_score:
                best_score = score
                best_item = item_key
            
        if best_item:
            # Create a new container instance for this item
            c = normalize_container(slot)
            c['id'] = best_item # The inventory key
            mapped.append(c)
            available_items.remove(best_item)
            
    # If we have items left over, this template might not be ideal, but we return what we mapped.
    # For heroes, we already checked strict count, so heroes are safe.
    return mapped

def get_valid_templates(config, inventory, item_aspects={}):
    """
    Returns a list of all valid layout configurations (list of containers) for this inventory.
    """
    valid_options = []
    
    heroes = [k for k in inventory.keys() if 'hero' in k]
    accessories = [k for k in inventory.keys() if 'accessory' in k]
    supports = [k for k in inventory.keys() if 'hero' not in k and 'accessory' not in k]
    
    safe = {"x": 177, "y": 380, "w": 4607, "h": 2920} # Hardcoded safe area based on A3
    # ideally pass from config, but for now this is fine for templates
    
    # A. Check Flexible Generators
    for gen in GENERATORS:
        res = gen(safe, heroes, supports, accessories, item_aspects)
        if res:
            valid_options.append({
                "name": f"Dynamic_{gen.__name__}",
                "type": "dynamic",
                "containers": res
            })
            
    # B. Check Legacy JSON
    legacy_presets = load_legacy_layouts()
    for name, preset in legacy_presets.items():
        mapped = map_inventory_to_legacy(inventory, preset.get("containers", []), item_aspects)
        if mapped:
            valid_options.append({
                "name": f"Legacy_{name}",
                "type": "fixed",
                "containers": mapped
            })
            
    return valid_options
