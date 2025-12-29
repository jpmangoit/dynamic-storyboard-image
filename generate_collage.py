"""
Advanced Storyboard Generator with Anchored Layout System
Supports role-based containers, floating elements, and dynamic positioning
"""

import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# Optional AI imports
try:
    from transformers import CLIPProcessor, CLIPModel
    import torch
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_smart_role(img_path, model, processor):
    """
    Determine product role using AI + Heuristics (Aspect Ratio).
    Returns (role_id, confidence_msg)
    """
    try:
        image = Image.open(img_path)
        
        # 1. AI Classification
        labels = ["tea towel", "tote bag", "mug", "keyring", "magnet", "notebook", "frame", "greeting card"]
        inputs = processor(text=labels, images=image, return_tensors="pt", padding=True)
        outputs = model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1)
        pred_idx = probs.argmax().item()
        ai_label = labels[pred_idx]
        conf = probs[0][pred_idx].item()
        
        # 2. Heuristics (Aspect Ratio Check)
        w, h = image.size
        aspect = w / h
        
        # Ambiguous Group: Flat rectangular art items
        ambiguous_labels = ["tea towel", "magnet", "greeting card", "frame"]
        
        role = None
        reason = f"AI: {ai_label} ({conf:.1%})"
        
        if ai_label in ambiguous_labels:
            # Use Aspect Ratio to disambiguate
            if aspect < 0.8:
                role = "hero_left" # Towel (Tall)
                reason += " + Tall aspect (< 0.8)"
            elif 0.95 <= aspect <= 1.05:
                role = "accessory_small" # Magnet (Square)
                reason += " + Square aspect"
            elif 0.8 <= aspect < 0.95:
                role = "support_medium_large" # Greeting Card (Portrait)
                reason += " + Portrait aspect"
            elif aspect > 1.1:
                role = "support_large" # Frame (Landscape)
                reason += " + Landscape aspect"
        
        # Distinct Group
        if role is None:
            if ai_label == "tote bag":
                role = "hero_right"
            elif ai_label == "mug":
                role = "cluster_bottom"
            elif ai_label == "keyring":
                role = "accessory_tiny"
            elif ai_label == "notebook":
                role = "support_medium"
                
        return role, reason
        
    except Exception as e:
        print(f"[WARN] Smart analysis failed for {os.path.basename(img_path)}: {e}")
        return None, str(e)

def discover_products_smart(products_dir):
    """Scan directory and map products using AI."""
    if not AI_AVAILABLE:
        print("[WARN] AI libraries not installed. Falling back to filename match.")
        return discover_products_filenames(products_dir)
        
    print("\n[AI] Loading CLIP model for Smart Discovery...")
    try:
        model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    except Exception as e:
        print(f"[ERROR] Failed to load AI model: {e}")
        return {}

    mapping = {}
    print("[AI] Analyzing product images...")
    
    for filename in os.listdir(products_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            path = os.path.join(products_dir, filename)
            role, reason = get_smart_role(path, model, processor)
            
            if role:
                mapping[role] = filename
                print(f"  + {filename} -> {role} [{reason}]")
            else:
                print(f"  ? {filename} -> Unknown [{reason}]")
                
    return mapping

def discover_products_filenames(products_dir):
    """Legacy filename-based discovery."""
    mapping = {}
    auto_map = {
        "towel": "hero_left",
        "bag": "hero_right",
        "mug": "cluster_bottom",
        "magnet": "accessory_small",
        "keyring": "accessory_tiny",
        "frame": "support_large",
        "notebook": "support_medium",
        "greeting": "support_medium_large"
    }
    
    if os.path.exists(products_dir):
        for filename in os.listdir(products_dir):
            lower_name = filename.lower()
            if lower_name.endswith('.png'):
                for key, role in auto_map.items():
                    if key in lower_name:
                        mapping[role] = os.path.join(products_dir, filename)
    return mapping

def fit_image_to_box(img, max_width, max_height, maintain_aspect=True):
    """Resize image to fit within box while maintaining aspect ratio (scale up or down)."""
    if not maintain_aspect:
        return img.resize((max_width, max_height), Image.Resampling.LANCZOS)
    
    src_width, src_height = img.size
    src_aspect = src_width / src_height
    box_aspect = max_width / max_height
    
    if src_aspect > box_aspect:
        # Width constrained
        new_width = max_width
        new_height = int(max_width / src_aspect)
    else:
        # Height constrained
        new_height = max_height
        new_width = int(max_height * src_aspect)
    
    return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

def render_header(canvas, config, customer_name="CUSTOMER NAME"):
    """Render header with image and text overlays."""
    if "header" not in config:
        return canvas
    
    header_cfg = config["header"]
    header_area = header_cfg["area"]
    
    if header_cfg.get("type") == "image":
        header_src = header_cfg.get("src")
        if header_src and os.path.exists(header_src):
            try:
                header_img = Image.open(header_src)
                
                # Convert palette images to RGB (not RGBA) to preserve colors
                if header_img.mode == 'P':
                    header_img = header_img.convert('RGB')
                
                # Get width percentage (default 100%)
                width_percent = header_cfg.get("width_percent", 100)
                target_width = int(header_area["w"] * (width_percent / 100))
                target_height = header_area["h"]
                
                # Resize to fill the header area (stretch if needed)
                header_img = header_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                # Get position (default "left")
                position = header_cfg.get("position", "left")
                
                # Calculate position
                if position == "right":
                    img_x = header_area["x"] + header_area["w"] - target_width
                elif position == "center":
                    img_x = header_area["x"] + (header_area["w"] - target_width) // 2
                else:  # left
                    img_x = header_area["x"]
                
                img_y = header_area["y"]
                
                # Direct paste for header
                canvas.paste(header_img, (img_x, img_y))
                print(f"[OK] Header image loaded: {target_width}x{target_height}")
                
            except Exception as e:
                print(f"[WARN] Failed to load header image: {e}")
    
    # Render text overlays
    draw = ImageDraw.Draw(canvas)
    for overlay in header_cfg.get("text_overlays", []):
        try:
            font = ImageFont.truetype(overlay["font"], overlay["size"])
        except:
            font = ImageFont.load_default()
        
        text = overlay["text"].replace("{{CUSTOMER_NAME}}", customer_name)
        draw.text((overlay["x"], overlay["y"]), text, 
                 fill=hex_to_rgb(overlay["color"]), font=font)
    
    return canvas

def render_footer(canvas, config):
    """Render footer with image and elements."""
    if "footer" not in config:
        return canvas
    
    footer_cfg = config["footer"]
    
    # Render footer image if specified
    if footer_cfg.get("type") == "image":
        footer_src = footer_cfg.get("src")
        footer_area = footer_cfg["area"]
        
        if footer_src and os.path.exists(footer_src):
            try:
                footer_img = Image.open(footer_src)
                if footer_img.mode == 'P':
                    footer_img = footer_img.convert('RGB')
                
                footer_img = footer_img.resize((footer_area["w"], footer_area["h"]), Image.Resampling.LANCZOS)
                canvas.paste(footer_img, (footer_area["x"], footer_area["y"]))
                print(f"[OK] Footer image loaded")
            except Exception as e:
                print(f"[WARN] Failed to load footer image: {e}")
    
    # Render footer elements
    draw = ImageDraw.Draw(canvas)
    for element in footer_cfg.get("elements", []):
        if element["type"] == "image":
            try:
                elem_img = Image.open(element["src"])
                elem_img = elem_img.resize((element["w"], element["h"]), Image.Resampling.LANCZOS)
                canvas.paste(elem_img, (element["x"], element["y"]))
            except Exception as e:
                print(f"[WARN] Failed to load footer element: {e}")
        
        elif element["type"] == "text":
            try:
                font = ImageFont.truetype(element["font"], element["size"])
            except:
                font = ImageFont.load_default()
            
            draw.text((element["x"], element["y"]), element["text"],
                     fill=hex_to_rgb(element["color"]), font=font)
    
    return canvas

def calculate_container_bounds(container, content_area, size_classes, placed_containers):
    """Calculate the pixel bounds for a container based on its configuration."""
    content_x = content_area["x"]
    content_y = content_area["y"]
    content_w = content_area["w"]
    content_h = content_area["h"]
    
    size_class = size_classes.get(container.get("size_class", "medium"), {})
    
    # [NEW] Check for exact pixel overrides (highest priority)
    if "canvas_x" in container and "canvas_y" in container:
        x = container["canvas_x"]
        y = container["canvas_y"]
        
        # Determine width
        if "width_px" in container:
            w = container["width_px"]
        elif "fixed_width_px" in size_class:
            w = size_class["fixed_width_px"]
        else:
             max_width_pct = size_class.get("max_width_percent", 35)
             w = int(content_w * (max_width_pct / 100))
             
        # Determine height
        if "height_px" in container:
            h = container["height_px"]
        elif "fixed_height_px" in size_class:
            h = size_class["fixed_height_px"]
        else:
            max_height_pct = size_class.get("max_height_percent", 30)
            h = int(content_h * (max_height_pct / 100))
            
        return {"x": x, "y": y, "w": w, "h": h}

    # Handle anchored positioning
    if container.get("position") == "float" and container.get("anchor_to"):
        anchor_id = container["anchor_to"]
        if anchor_id not in placed_containers:
            print(f"[WARN] Anchor '{anchor_id}' not found for '{container['id']}'")
            return None
        
        anchor_bounds = placed_containers[anchor_id]
        anchor_side = container.get("anchor_side", "top_left")
        offset_x_pct = container.get("offset_x_percent", 0)
        offset_y_pct = container.get("offset_y_percent", 0)
        
        # Calculate anchor point
        if "top" in anchor_side:
            anchor_y = anchor_bounds["y"]
        elif "bottom" in anchor_side:
            anchor_y = anchor_bounds["y"] + anchor_bounds["h"]
        else:  # middle
            anchor_y = anchor_bounds["y"] + anchor_bounds["h"] // 2
        
        if "left" in anchor_side:
            anchor_x = anchor_bounds["x"]
        elif "right" in anchor_side:
            anchor_x = anchor_bounds["x"] + anchor_bounds["w"]
        else:  # center
            anchor_x = anchor_bounds["x"] + anchor_bounds["w"] // 2
        
        # Apply offsets
        offset_x = int(content_w * (offset_x_pct / 100))
        offset_y = int(content_h * (offset_y_pct / 100))
        
        x = anchor_x + offset_x
        y = anchor_y + offset_y
        
        # Get size from size_class
        if "fixed_width_px" in size_class:
            w = size_class["fixed_width_px"]
            h = size_class["fixed_height_px"]
        else:
            max_h_pct = size_class.get("max_height_percent", 30)
            h = int(content_h * (max_h_pct / 100))
            w = h  # Square by default
        
        return {"x": x, "y": y, "w": w, "h": h}
    
    # Get position for non-anchored items
    position = container.get("position", "left")
    
    # Handle absolute positioning (new system)
    if position == "absolute":
        margin_top_pct = container.get("margin_top_percent", 0)
        
        # Calculate Height based on size class limits
        max_height_pct = size_class.get("max_height_percent", 30)
        if "fixed_height_px" in size_class:
            h = size_class["fixed_height_px"]
        else:
            h = int(content_h * (max_height_pct / 100))
            
        # Calculate Y
        # Check if using bottom margin (optional future proofing)
        if "margin_bottom_percent" in container:
            margin_bottom_pct = container["margin_bottom_percent"]
            y = content_y + content_h - h - int(content_h * (margin_bottom_pct / 100))
        else:
            y = content_y + int(content_h * (margin_top_pct / 100))

        # Calculate Width based on size class limits
        max_width_pct = size_class.get("max_width_percent", 35)
        if "fixed_width_px" in size_class:
            w = size_class["fixed_width_px"]
        elif "fixed_height_px" in size_class:
             # If only fixed height is given (e.g. cluster), calculate width from max_width_percent
             w = int(content_w * (max_width_pct/100))
        else:
            w = int(content_w * (max_width_pct / 100))

        # Calculate X
        if "margin_right_percent" in container:
            # Right-aligned absolute
            margin_right_pct = container["margin_right_percent"]
            x = content_x + content_w - w - int(content_w * (margin_right_pct / 100))
        else:
            # Left-aligned absolute (default)
            margin_left_pct = container.get("margin_left_percent", 0)
            x = content_x + int(content_w * (margin_left_pct / 100))
            
        return {"x": x, "y": y, "w": w, "h": h}

    # Handle positioned containers (left, right, bottom_center, etc.)
    if position == "left":
        margin_left_pct = container.get("margin_left_percent", 0)
        margin_top_pct = container.get("margin_top_percent", 0)
        max_width_pct = container.get("max_width_percent", 35)
        max_height_pct = container.get("max_height_percent", 80)
        
        x = content_x + int(content_w * (margin_left_pct / 100))
        y = content_y + int(content_h * (margin_top_pct / 100))
        w = int(content_w * (max_width_pct / 100))
        h = int(content_h * (max_height_pct / 100))
        
    elif position == "right":
        margin_right_pct = container.get("margin_right_percent", 0)
        margin_top_pct = container.get("margin_top_percent", 0)
        max_width_pct = container.get("max_width_percent", 35)
        max_height_pct = container.get("max_height_percent", 80)
        
        w = int(content_w * (max_width_pct / 100))
        h = int(content_h * (max_height_pct / 100))
        x = content_x + content_w - w - int(content_w * (margin_right_pct / 100))
        y = content_y + int(content_h * (margin_top_pct / 100))
        
    elif position == "bottom_center":
        margin_bottom_pct = container.get("margin_bottom_percent", 0)
        max_width_pct = container.get("max_width_percent", 65)
        fixed_height_pct = container.get("fixed_height_percent", 15)
        
        w = int(content_w * (max_width_pct / 100))
        h = int(content_h * (fixed_height_pct / 100))
        x = content_x + (content_w - w) // 2
        y = content_y + content_h - h - int(content_h * (margin_bottom_pct / 100))
    
    else:
        # Default center
        w = int(content_w * 0.3)
        h = int(content_h * 0.3)
        x = content_x + (content_w - w) // 2
        y = content_y + (content_h - h) // 2
    
    return {"x": x, "y": y, "w": w, "h": h}

def map_products_to_containers(products_dir, containers):
    """Auto-map product files to containers based on role."""
    product_files = [f for f in os.listdir(products_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    mapping = {}
    used_products = set()
    
    # Priority mapping by role
    for container in containers:
        container_id = container["id"]
        role = container.get("role", "support")
        
        # Try to find a suitable product
        for product_file in product_files:
            if product_file in used_products:
                continue
            
            # Simple heuristic matching
            if role == "hero" and "towel" in product_file.lower():
                mapping[container_id] = product_file
                used_products.add(product_file)
                break
            elif role == "accessory" and ("magnet" in product_file.lower() or "keyring" in product_file.lower()):
                mapping[container_id] = product_file
                used_products.add(product_file)
                break
            elif role == "support":
                mapping[container_id] = product_file
                used_products.add(product_file)
                break
            elif role == "cluster" and "mug" in product_file.lower():
                mapping[container_id] = product_file
                used_products.add(product_file)
                break
    
    # Fill remaining containers with unused products
    for container in containers:
        container_id = container["id"]
        if container_id not in mapping and product_files:
            for product_file in product_files:
                if product_file not in used_products:
                    mapping[container_id] = product_file
                    used_products.add(product_file)
                    break
    
    return mapping

def render_storyboard(config, preset_name, customer_name, product_mapping=None, products_dir="products"):
    """Render the complete storyboard."""
    canvas_cfg = config["canvas"]
    canvas = Image.new("RGB", (canvas_cfg["width_px"], canvas_cfg["height_px"]), 
                      hex_to_rgb(canvas_cfg["background"]))
    
    # Render header
    canvas = render_header(canvas, config, customer_name)
    
    # Get preset and containers
    preset = config["presets"].get(preset_name)
    if not preset:
        print(f"[ERROR] Preset '{preset_name}' not found in layout config.")
        return None

    containers = preset["containers"]
    size_classes = config["size_classes"]
    content_area = config["content_area"]
    
    # Map products to containers
    if product_mapping is None:
        if AI_AVAILABLE:
            print("[INFO] Using AI Smart Discovery...")
            product_mapping = discover_products_smart(products_dir)
        
        # If AI not available or found nothing, fall back to legacy
        if not product_mapping:
            print("[INFO] Using Standard Filename Mapping...")
            product_mapping = map_products_to_containers(products_dir, containers)
    
    print(f"\n2. Product mapping:")
    for container_id, product_file in product_mapping.items():
        print(f"   {container_id} -> {product_file}")
    
    print(f"\n3. Placing products...")
    
    # Place products
    placed_containers = {}
    
    for container in containers:
        container_id = container["id"]
        
        # Calculate bounds
        bounds = calculate_container_bounds(container, content_area, size_classes, placed_containers)
        if not bounds:
            continue
        
        placed_containers[container_id] = bounds
        
        # Load and place product
        # Check both the specific assignment and fallbacks
        product_file = product_mapping.get(container_id)
        
        if product_file:
            product_path = os.path.join(products_dir, product_file)
            
            # Try to find the file if exact match doesn't exist (handle case sensitivity or missing extension)
            if not os.path.exists(product_path):
                # Try finding a match in the directory
                candidates = os.listdir(products_dir)
                for cand in candidates:
                    if cand.lower() == product_file.lower():
                        product_path = os.path.join(products_dir, cand)
                        break
            
            if os.path.exists(product_path):
                try:
                    product_img = Image.open(product_path)
                    
                    # Convert to RGBA for transparency
                    if product_img.mode != 'RGBA':
                        product_img = product_img.convert('RGBA')
                    
                    # Fit to bounds
                    product_img = fit_image_to_box(product_img, bounds["w"], bounds["h"])
                    
                    # Center within bounds
                    paste_x = bounds["x"] + (bounds["w"] - product_img.size[0]) // 2
                    paste_y = bounds["y"] + (bounds["h"] - product_img.size[1]) // 2
                    
                    # Handle rotation if specified
                    rotation = container.get("rotation_deg", 0)
                    if rotation != 0:
                        product_img = product_img.rotate(-rotation, expand=True, resample=Image.Resampling.BICUBIC)
                        # Re-center after rotation expansion
                        paste_x = bounds["x"] + (bounds["w"] - product_img.size[0]) // 2
                        paste_y = bounds["y"] + (bounds["h"] - product_img.size[1]) // 2

                    
                    # Paste with transparency
                    temp_canvas = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
                    temp_canvas.paste(product_img, (paste_x, paste_y))
                    canvas_rgba = canvas.convert("RGBA")
                    canvas_rgba = Image.alpha_composite(canvas_rgba, temp_canvas)
                    canvas = canvas_rgba.convert("RGB")
                    
                    print(f"[OK] Placed {container_id} ({product_file}) at ({paste_x}, {paste_y})")
                    
                except Exception as e:
                    print(f"[ERROR] Failed to place {container_id}: {e}")
            else:
                print(f"[WARN] Product file not found: {product_path}")
        else:
             print(f"[SKIP] No product assigned to {container_id}")

    
    # Render footer
    canvas = render_footer(canvas, config)
    
    return canvas

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_collage.py <mapping_file.json> OR <preset_name> [customer_name]")
        print("Example: python generate_collage.py classic_collage.json")
        sys.exit(1)
    
    arg1 = sys.argv[1]
    
    # Load layout configuration
    config_file = "a3_storyboard_layout.json"
    if not os.path.exists(config_file):
        print(f"[ERROR] Layout configuration file '{config_file}' not found.")
        sys.exit(1)

    with open(config_file, 'r') as f:
        config = json.load(f)

    # Determine mode
    if arg1 == "--generate":
        print("[INFO] Mode: GENERATIVE LAYOUT")
        customer_name = sys.argv[2] if len(sys.argv) > 2 else "Generative Customer"
        
        # 1. AI Scan
        print("[1] AI Inventory Scan...")
        # Force AI usage for generation
        if not AI_AVAILABLE:
            print("[ERROR] Generative mode requires AI libraries (transformers/torch).")
            sys.exit(1)
            
        inventory = discover_products_smart("products")
        if not inventory:
            print("[ERROR] No products found to generate layout.")
            sys.exit(1)
            
        # 2. Dynamic Layout Calculation
        print("[2] Procedural Layout Generation...")
        from layout_generator import generate_dynamic_layout
        
        # Use canvas config from layout file
        w = config['canvas']['width_px']
        h = config['canvas']['height_px']
        
        generated_containers = generate_dynamic_layout(w, h, inventory)
        
        # Create a synthetic preset
        preset = {
            "containers": generated_containers
        }
        
        # Update config with synthetic preset
        config["presets"]["generated"] = preset
        preset_name = "generated"
        product_mapping = inventory # Mapping is 1:1 with inventory keys
        
    elif arg1.endswith('.json'):
        mapping_file = arg1
        if not os.path.exists(mapping_file):
             print(f"[ERROR] Mapping file '{mapping_file}' not found.")
             sys.exit(1)
             
        print(f"Loading job from {mapping_file}...")
        with open(mapping_file, 'r') as f:
            job_data = json.load(f)
            
        preset_name = job_data.get("layout_preset")
        customer_name = job_data.get("customer_name", "Valued Customer")
        product_mapping = job_data.get("assignment", {})
        
    else:
        preset_name = arg1
        customer_name = sys.argv[2] if len(sys.argv) > 2 else "CUSTOMER NAME"
        product_mapping = None # Use auto-mapping

    print("=" * 60)
    print("Advanced Storyboard Generator")
    print("=" * 60)
    
    print(f"\n1. Configuration:")
    print(f"   Canvas: {config['canvas']['width_px']}x{config['canvas']['height_px']} @ {config['canvas']['dpi']} DPI")
    print(f"   Preset: {preset_name}")
    print(f"   Customer: {customer_name}")
    
    # Generate storyboard
    canvas = render_storyboard(config, preset_name, customer_name, product_mapping)
    
    if canvas:
        # Save output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        # Clean filenames for safety
        safe_customer = "".join([c for c in customer_name if c.isalpha() or c.isdigit() or c==' ']).strip().replace(' ', '_')
        output_path = os.path.join(output_dir, f"storyboard_{preset_name}_{safe_customer}_{timestamp}.png")
        canvas.save(output_path, "PNG", dpi=(config['canvas']['dpi'], config['canvas']['dpi']))
        
        print(f"\n[SUCCESS] Complete! Saved to: {output_path}")
    else:
        print("\n[FAILED] Could not generate storyboard.")
        
    print("=" * 60)

if __name__ == "__main__":
    main()
