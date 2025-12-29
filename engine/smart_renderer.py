from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import os
import random

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def add_drop_shadow(image, offset=(15, 15), background_color=(255, 255, 255), shadow_color=(0, 0, 0, 100), blur_radius=20):
    """
    Adds a soft drop shadow to an RGBA image.
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
    
    # Create background layer
    # For storyboards, we usually just return the shadow + image composite
    # But since we paste onto a canvas later, we just need the composite of Shadow + Image
    
    # Composite Image ON TOP of Shadow
    img_left = blur_radius - min(offset[0], 0)
    img_top = blur_radius - min(offset[1], 0)
    
    shadow.paste(image, (img_left, img_top), mask=image)
    
    # Return the composite and the offset needed to place it correctly
    # The new image is larger than the original.
    # Original X/Y was for the top-left of the image.
    # New X should be X - img_left
    return shadow, img_left, img_top

def render_smart_storyboard(config, preset_name, product_mapping, customer_name="Generative Client"):
    """
    Enhanced renderer with Shadows, Rotations, and Overlaps.
    """
    # Canvas
    canvas_cfg = config["canvas"]
    bg_color = hex_to_rgb(canvas_cfg.get("background", "#FFFFFF"))
    canvas = Image.new("RGB", (canvas_cfg["width_px"], canvas_cfg["height_px"]), bg_color)
    
    # 1. Header (Reusing logic would be ideal, but for isolation we reimplement basic header)
    # We can import helpers if we really want, but let's keep it self-contained for safety
    if "header" in config:
        h_cfg = config["header"]
        h_area = h_cfg["area"]
        # Draw placeholder header if image missing
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([(h_area["x"], h_area["y"]), (h_area["x"]+h_area["w"], h_area["y"]+h_area["h"])], fill="#87CEEB")
        # Try loading image
        if h_cfg.get("type") == "image" and os.path.exists(h_cfg.get("src", "")):
            try:
                h_img = Image.open(h_cfg["src"]).convert("RGBA")
                h_img = h_img.resize((h_area["w"], h_area["h"]), Image.Resampling.LANCZOS)
                canvas.paste(h_img, (h_area["x"], h_area["y"]), mask=h_img)
            except: pass
            
        # Draw Customer Name
        try:
             font = ImageFont.truetype("arial.ttf", 80)
        except:
             font = ImageFont.load_default()
        draw.text((h_area["x"] + 50, h_area["y"] + 100), customer_name, fill="white", font=font)

    # 2. Render Products
    # Sort containers by area size? Larger items usually in back? 
    # Or strict z-index? 
    # For now, we trust the list order, but let's reverse it so first items (Hero) are at back?
    # Actually, Layout Generator usually puts Hero first.
    # If we want overlap, smaller items ( Accessories) should be ON TOP of Heroes.
    # So we should draw Heroes first, Accessories last.
    
    containers = config["presets"][preset_name]
    
    # Sort: Heroes first (back), then Supports, then Accessories (front)
    # We can guess by ID name
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
            # Load
            img = Image.open(img_path).convert("RGBA")
            
            # Smart Resize (Fit Inside Box)
            # Calculate aspect ratios to fit 'contain' style
            target_w, target_h = container["w"], container["h"]
            img_ratio = img.width / img.height
            box_ratio = target_w / target_h
            
            if img_ratio > box_ratio:
                # Width constrained
                new_w = target_w
                new_h = int(target_w / img_ratio)
            else:
                # Height constrained
                new_h = target_h
                new_w = int(target_h * img_ratio)
                
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # Rotation
            angle = container.get("rotation_deg", 0)
            if angle != 0:
                # Note: generate_collage uses negative rotation for PIL compatibility
                img = img.rotate(-angle, resample=Image.Resampling.BICUBIC, expand=True)
            
            # Add Drop Shadow
            img_with_shadow, offset_x, offset_y = add_drop_shadow(img)
            
            # Position Calculation
            # Center based on the FINAL image size (after rotation)
            # container["x"] is the top-left of the bounding box
            center_x = container["x"] + (container["w"] - img.width) // 2
            center_y = container["y"] + (container["h"] - img.height) // 2
            
            # The paste coordinate needs to account for the shadow expansion (offset_x/y)
            # If offset_x is positive (left padding), we move Left (subtract).
            final_x = center_x - offset_x
            final_y = center_y - offset_y
            
            # Paste
            canvas.paste(img_with_shadow, (final_x, final_y), mask=img_with_shadow)
            
            print(f"   [RENDER] Placed {cid} with shadow/rotation")
            
        except Exception as e:
            print(f"   [ERROR] Failed to render {cid}: {e}")

    # 3. Footer
    if "footer" in config:
        f_cfg = config["footer"]
        f_area = f_cfg["area"]
        draw = ImageDraw.Draw(canvas)
        # draw.rectangle([(f_area["x"], f_area["y"]), (f_area["x"]+f_area["w"], f_area["y"]+f_area["h"])], fill="#EEE")
        if f_cfg.get("type") == "image" and os.path.exists(f_cfg.get("src", "")):
            try:
                f_img = Image.open(f_cfg["src"]).convert("RGBA")
                f_img = f_img.resize((f_area["w"], f_area["h"]), Image.Resampling.LANCZOS)
                canvas.paste(f_img, (f_area["x"], f_area["y"]), mask=f_img)
            except: pass

    return canvas
