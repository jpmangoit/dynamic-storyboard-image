#!/usr/bin/env python3
"""
JSON-Based Storyboard Generator with Image Header/Footer Support
Usage: python generate_from_json.py [layout_name] [customer_name]
Example: python generate_from_json.py layout_A "ACME Corp"
"""

import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

import glob

def load_config(config_path="a3_storyboard_master.json"):
    """Load JSON configuration file and templates."""
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    # Ensure presets key exists
    if "presets" not in config:
        config["presets"] = {}
        
    # Load templates from templates/ directory
    template_files = glob.glob(os.path.join("templates", "*.json"))
    for t_file in template_files:
        try:
            with open(t_file, 'r') as f:
                t_data = json.load(f)
                if "presets" in t_data:
                    config["presets"].update(t_data["presets"])
                elif "containers" in t_data:
                    name = os.path.basename(t_file).replace(".json", "")
                    config["presets"][name] = t_data
        except Exception as e:
            print(f"[WARN] Failed to load template {t_file}: {e}")
            
    return config

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_brush_stroke_header(width, height, bg_color="#4A90C8"):
    """
    Create header with brush stroke effect programmatically.
    No image files needed!
    """
    import random
    
    # Create base image
    header = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(header)
    
    # Brush stroke starts at ~70% width
    brush_x = int(width * 0.7)
    
    # Create jagged edge points for brush effect
    points = []
    num_points = 15
    
    # Top edge with irregular pattern
    for i in range(num_points):
        x = brush_x + (width - brush_x) * (i / num_points)
        y = 0 + random.randint(-20, 30) * (1 if i % 2 == 0 else -1)
        points.append((int(x), int(max(0, y))))
    
    # Right edge
    points.append((width, 0))
    points.append((width, height))
    
    # Bottom edge with irregular pattern
    for i in range(num_points, 0, -1):
        x = brush_x + (width - brush_x) * (i / num_points)
        y = height + random.randint(-30, 20) * (1 if i % 2 == 0 else -1)
        points.append((int(x), int(min(height, y))))
    
    # Close polygon
    points.append((brush_x, height))
    points.append((brush_x, 0))
    
    # Draw white brush stroke
    draw.polygon(points, fill='white')
    
    return header

def render_header(canvas, config, customer_name="CUSTOMER NAME"):
    """Render header section - supports both image and programmatic generation."""
    if "header" not in config:
        return
    
    header_cfg = config["header"]
    header_area = header_cfg["area"]
    
    # Draw background color first if specified
    if "background" in header_cfg:
        draw = ImageDraw.Draw(canvas)
        bg_color = hex_to_rgb(header_cfg["background"])
        draw.rectangle([
            (header_area["x"], header_area["y"]),
            (header_area["x"] + header_area["w"], header_area["y"] + header_area["h"])
        ], fill=bg_color)
    
    if header_cfg.get("type") == "programmatic" or (header_cfg.get("type") == "image" and not os.path.exists(header_cfg.get("src", ""))):
        # Generate brush stroke header programmatically
        bg_color = header_cfg.get("background", "#4A90C8")
        header_img = create_brush_stroke_header(header_area["w"], header_area["h"], bg_color)
        canvas.paste(header_img, (header_area["x"], header_area["y"]))
        
    elif header_cfg.get("type") == "image":
        # Load header image
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
                
                print(f"[OK] Header image loaded: {target_width}x{target_height} at ({img_x}, {img_y})")
                
            except Exception as e:
                print(f"[ERROR] Failed to load header image: {e}")
                import traceback
                traceback.print_exc()
                
            except Exception as e:
                print(f"[ERROR] Failed to load header image: {e}")
                import traceback
                traceback.print_exc()
    else:
        # Legacy drawn header
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([
            (header_area["x"], header_area["y"]),
            (header_area["x"] + header_area["w"], header_area["y"] + header_area["h"])
        ], fill=hex_to_rgb(header_cfg.get("background", "#1E73BE")))
        
        for element in header_cfg.get("elements", []):
            if element["type"] == "text":
                try:
                    font = ImageFont.truetype("arial.ttf", element["size"])
                except:
                    font = ImageFont.load_default()
                
                text = element["text"].replace("{{CUSTOMER_NAME}}", customer_name)
                draw.text((element["x"], element["y"]), text, 
                         fill=hex_to_rgb(element["color"]), font=font)
    
    # Render text overlays (for both programmatic and image headers)
    draw = ImageDraw.Draw(canvas)
    for overlay in header_cfg.get("text_overlays", []):
        try:
            font = ImageFont.truetype("arial.ttf", overlay["size"])
        except:
            font = ImageFont.load_default()
        
        text = overlay["text"].replace("{{CUSTOMER_NAME}}", customer_name)
        draw.text((overlay["x"], overlay["y"]), text, 
                 fill=hex_to_rgb(overlay["color"]), font=font)
    
    return canvas

def render_footer(canvas, config):
    """Render footer section - supports both image and drawn types."""
    if "footer" not in config:
        return
    
    footer_cfg = config["footer"]
    
    if footer_cfg.get("type") == "image":
        # Image-based footer
        footer_area = footer_cfg["area"]
        footer_src = footer_cfg.get("src")
        
        if footer_src and os.path.exists(footer_src):
            try:
                footer_img = Image.open(footer_src).convert("RGBA")
                footer_img = footer_img.resize((footer_area["w"], footer_area["h"]), Image.Resampling.LANCZOS)
                
                # Convert to RGB for pasting
                bg = Image.new("RGB", footer_img.size, (255, 255, 255))
                bg.paste(footer_img, mask=footer_img.split()[3] if footer_img.mode == 'RGBA' else None)
                canvas.paste(bg, (footer_area["x"], footer_area["y"]))
            except Exception as e:
                print(f"[WARN] Failed to load footer image: {e}")
    
    # Render footer elements (logo and text)
    draw = ImageDraw.Draw(canvas)
    for element in footer_cfg.get("elements", []):
        if element["type"] == "image":
            # Logo image
            logo_src = element.get("src")
            if logo_src and os.path.exists(logo_src):
                try:
                    logo_img = Image.open(logo_src).convert("RGBA")
                    logo_img = logo_img.resize((element["w"], element["h"]), Image.Resampling.LANCZOS)
                    
                    bg = Image.new("RGB", logo_img.size, (255, 255, 255))
                    bg.paste(logo_img, mask=logo_img.split()[3] if logo_img.mode == 'RGBA' else None)
                    canvas.paste(bg, (element["x"], element["y"]))
                except Exception as e:
                    print(f"[WARN] Failed to load logo: {e}")
        elif element["type"] == "text":
            try:
                font = ImageFont.truetype("arial.ttf", element["size"])
            except:
                font = ImageFont.load_default()
            
            draw.text((element["x"], element["y"]), element["text"],
                     fill=hex_to_rgb(element["color"]), font=font)

def load_product_mapping(products_dir="products"):
    """
    Load product-to-zone mapping.
    Auto-maps based on filename patterns.
    """
    mapping = {}
    
    # Auto-mapping rules (map to zone IDs)
    auto_map = {
        "towel": "tea_towel",
        "mug": "mug_set",
        "magnet": "magnet",
        "keyring": "keyring",
        "bag": "bag",
        "frame": "mounted_print",
        "notebook": "book",
        "greeting": "greeting_card"
    }
    
    # Scan products directory
    if os.path.exists(products_dir):
        for filename in os.listdir(products_dir):
            if filename.lower().endswith('.png'):
                # Try to match filename to zone
                for pattern, zone_id in auto_map.items():
                    if pattern in filename.lower():
                        mapping[zone_id] = os.path.join(products_dir, filename)
                        break
    
    return mapping

def fit_image_to_zone(img, zone_w, zone_h):
    """
    Fit image to zone using 'contain' mode.
    Returns resized image and offset for centering.
    """
    img_w, img_h = img.size
    aspect = img_w / img_h
    zone_aspect = zone_w / zone_h
    
    if aspect > zone_aspect:
        # Image is wider - fit to width
        new_w = zone_w
        new_h = int(zone_w / aspect)
    else:
        # Image is taller - fit to height
        new_h = zone_h
        new_w = int(zone_h * aspect)
    
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Calculate centering offset
    x_offset = (zone_w - new_w) // 2
    y_offset = (zone_h - new_h) // 2
    
    return resized, x_offset, y_offset

def render_storyboard(config, layout_name, product_mapping, customer_name="CUSTOMER NAME"):
    """Generate storyboard from JSON config with specified layout."""
    
    # Get layout zones
    if layout_name not in config["presets"]:
        available = ", ".join(config["presets"].keys())
        raise ValueError(f"Layout '{layout_name}' not found. Available: {available}")
    
    zones = config["presets"][layout_name]
    
    # Create canvas
    canvas_cfg = config["canvas"]
    bg_color = hex_to_rgb(canvas_cfg.get("background", "#FFFFFF"))
    canvas = Image.new("RGB", 
                      (canvas_cfg["width_px"], canvas_cfg["height_px"]),
                      bg_color)
    
    # Render header
    render_header(canvas, config, customer_name)
    
    # Render product zones
    placed_count = 0
    for zone in zones:
        zone_id = zone["id"]
        
        if zone_id in product_mapping:
            product_path = product_mapping[zone_id]
            
            try:
                # Load product image
                product_img = Image.open(product_path).convert("RGBA")
                
                # Fit to zone
                fitted_img, x_off, y_off = fit_image_to_zone(
                    product_img, zone["w"], zone["h"]
                )
                
                # Paste onto canvas
                final_x = zone["x"] + x_off
                final_y = zone["y"] + y_off
                
                # Preserve transparency by using alpha_composite
                if fitted_img.mode == 'RGBA':
                    # Create a temporary canvas section to composite onto
                    temp_canvas = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
                    temp_canvas.paste(fitted_img, (final_x, final_y))
                    
                    # Convert main canvas to RGBA temporarily for compositing
                    canvas_rgba = canvas.convert("RGBA")
                    canvas_rgba = Image.alpha_composite(canvas_rgba, temp_canvas)
                    canvas = canvas_rgba.convert("RGB")
                else:
                    canvas.paste(fitted_img, (final_x, final_y))
                
                placed_count += 1
                print(f"[OK] Placed {zone_id} at ({final_x}, {final_y})")
                
            except Exception as e:
                print(f"[ERROR] Failed to place {zone_id}: {e}")
        else:
            print(f"[WARN] No product mapped to zone: {zone_id}")
    
    # Render footer
    render_footer(canvas, config)
    
    print(f"\nPlaced {placed_count}/{len(zones)} products")
    return canvas

def main():
    """Main execution."""
    # Parse command line arguments
    layout_name = sys.argv[1] if len(sys.argv) > 1 else "layout_A"
    customer_name = sys.argv[2] if len(sys.argv) > 2 else "CUSTOMER NAME"
    
    print("=" * 60)
    print("JSON-Based Storyboard Generator")
    print("=" * 60)
    
    # Load configuration
    # Parse command line arguments
    layout_name = sys.argv[1] if len(sys.argv) > 1 else "layout_A"
    customer_name = sys.argv[2] if len(sys.argv) > 2 else "CUSTOMER NAME"
    
    print("=" * 60)
    print("JSON-Based Storyboard Generator")
    print("=" * 60)
    
    # Load configuration
    print("\n1. Loading configuration...")
    config = load_config()
    print(f"   Canvas: {config['canvas']['width_px']}x{config['canvas']['height_px']} @ {config['canvas']['dpi']} DPI")
    print(f"   Available layouts: {', '.join(config['presets'].keys())}")
    print(f"   Selected layout: {layout_name}")
    print(f"   Customer: {customer_name}")
    
    # Load product mapping
    print("\n2. Mapping products to zones...")
    product_mapping = load_product_mapping()
    for zone_id, path in product_mapping.items():
        print(f"   {zone_id} -> {os.path.basename(path)}")
    
    if layout_name not in config["presets"]:
         print(f"[ERROR] Layout '{layout_name}' not found.")
         return

    # Generate storyboard
    print(f"\n3. Generating storyboard with '{layout_name}'...")
    try:
        canvas = render_storyboard(config, layout_name, product_mapping, customer_name)
    except ValueError as e:
        print(f"\n[ERROR] {e}")
        return
    
    # Save output
    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"output/storyboard_{layout_name}_{timestamp}.png"
    canvas.save(output_path, dpi=(300, 300))
    
    print(f"\n[SUCCESS] Complete! Saved to: {output_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
