"""
Smart Storyboard Renderer with Enhanced Visual Effects.

This module provides advanced rendering with shadows, rotations, and proper
product sizing. Fixes the sizing bug by using shared utilities.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

from engine.image_utils import fit_image_to_box, get_centering_offset


def hex_to_rgb(hex_color):
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def add_drop_shadow(image, offset=(15, 15), shadow_color=(0, 0, 0, 100), blur_radius=20):
    """
    Adds a soft drop shadow to an RGBA image.
    Returns (shadow_image, offset_x, offset_y) for proper positioning.
    """
    total_width = image.width + abs(offset[0]) + 2 * blur_radius
    total_height = image.height + abs(offset[1]) + 2 * blur_radius
    
    # Create shadow layer
    shadow = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
    shadow_left = blur_radius + max(offset[0], 0)
    shadow_top = blur_radius + max(offset[1], 0)
    
    # Paste the image's alpha channel as the shadow source
    shadow.paste(shadow_color, (shadow_left, shadow_top), mask=image)
    
    # Blur the shadow
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))
    
    # Composite Image ON TOP of Shadow
    img_left = blur_radius - min(offset[0], 0)
    img_top = blur_radius - min(offset[1], 0)
    
    shadow.paste(image, (img_left, img_top), mask=image)
    
    return shadow, img_left, img_top


def render_smart_storyboard(config, preset_name, product_mapping, customer_name="Generative Client"):
    """
    Enhanced renderer with shadows, rotations, and CORRECT product sizing.
    
    KEY FIX: Products are now properly fitted to container bounds using shared
    fit_image_to_box() utility, matching generate_collage.py behavior.
    """
    # Canvas
    canvas_cfg = config["canvas"]
    bg_color = hex_to_rgb(canvas_cfg.get("background", "#FFFFFF"))
    canvas = Image.new("RGB", (canvas_cfg["width_px"], canvas_cfg["height_px"]), bg_color)
    
    # 1. Header
    if "header" in config:
        h_cfg = config["header"]
        h_area = h_cfg["area"]
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([(h_area["x"], h_area["y"]), (h_area["x"]+h_area["w"], h_area["y"]+h_area["h"])], fill="#87CEEB")
        
        if h_cfg.get("type") == "image" and os.path.exists(h_cfg.get("src", "")):
            try:
                h_img = Image.open(h_cfg["src"]).convert("RGBA")
                h_img = h_img.resize((h_area["w"], h_area["h"]), Image.Resampling.LANCZOS)
                canvas.paste(h_img, (h_area["x"], h_area["y"]), mask=h_img)
            except: pass
            
        try:
             font = ImageFont.truetype("arial.ttf", 80)
        except:
             font = ImageFont.load_default()
        draw.text((h_area["x"] + 50, h_area["y"] + 100), customer_name, fill="white", font=font)

    # 2. Render Products
    containers = config["presets"][preset_name]
    
    # Sort: Heroes first (back), then Supports, then Accessories (front)
    def z_sort(c):
        cid = c["id"]
        if "hero" in cid: return 0
        if "support" in cid: return 1
        return 2
        
    sorted_containers = sorted(containers, key=z_sort)
    
    for container in sorted_containers:
        cid = container["id"]
        img_path = product_mapping.get(cid)
        
        if not img_path or not os.path.exists(img_path):
            continue
            
        try:
            # Load product image
            img = Image.open(img_path).convert("RGBA")
            
            # FIX: Use shared fit_image_to_box utility (same as generate_collage.py)
            target_w, target_h = container["w"], container["h"]
            fitted_img = fit_image_to_box(img, target_w, target_h, maintain_aspect=True)
            
            # Rotation
            angle = container.get("rotation_deg", 0)
            if angle != 0:
                fitted_img = fitted_img.rotate(-angle, resample=Image.Resampling.BICUBIC, expand=True)
            
            # Add Drop Shadow
            img_with_shadow, shadow_offset_x, shadow_offset_y = add_drop_shadow(fitted_img)
            
            # FIX: Center using fitted image size, not shadow-expanded size
            x_offset, y_offset = get_centering_offset(fitted_img.size, (target_w, target_h))
            
            # Final position accounts for container, centering, and shadow offsets
            final_x = container["x"] + x_offset - shadow_offset_x
            final_y = container["y"] + y_offset - shadow_offset_y
            
            # Paste
            canvas.paste(img_with_shadow, (final_x, final_y), mask=img_with_shadow)
            
            print(f"   [RENDER] Placed {cid} (fitted: {fitted_img.size})")
            
        except Exception as e:
            print(f"   [ERROR] Failed to render {cid}: {e}")

    # 3. Footer
    if "footer" in config:
        f_cfg = config["footer"]
        f_area = f_cfg["area"]
        if f_cfg.get("type") == "image" and os.path.exists(f_cfg.get("src", "")):
            try:
                f_img = Image.open(f_cfg["src"]).convert("RGBA")
                f_img = f_img.resize((f_area["w"], f_area["h"]), Image.Resampling.LANCZOS)
                canvas.paste(f_img, (f_area["x"], f_area["y"]), mask=f_img)
            except: pass

    return canvas
