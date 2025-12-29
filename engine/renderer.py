# engine/renderer.py
from PIL import Image
import os
from datetime import datetime

def render(placements, folder):
    """
    Composites product images into final A3 storyboard.
    """
    A3_W, A3_H = 4961, 3508
    canvas = Image.new("RGBA", (A3_W, A3_H), (255, 255, 255, 255))

    # Sort placements for layering: XL/Large first (background), Small/XS last (foreground)
    # Actually, often you want the HERO (large) in front?
    # Standard composition: Background elements back, decorative small elements front. 
    # Current sort: Largest first -> Largest drawn first -> Largest is BEHIND.
    # This is usually correct for "clusters" where small items sit on top of big ones.
    

    # Sort placements by depth_layer (1=back, 10=front)
    sorted_placements = sorted(
        placements,
        key=lambda p: int(p.get("depth_layer", 5)),
        reverse=False
    )

    for i, placement in enumerate(sorted_placements):
        try:
            img_path = os.path.join(folder, placement["file"])
            if not os.path.exists(img_path): continue

            img = Image.open(img_path).convert("RGBA")
            target_w = int(placement["width"])
            target_h = int(placement["height"])
            img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            # Rotation
            rot = placement.get("rotation", 0)
            if rot != 0:
                img = img.rotate(rot, expand=True, resample=Image.Resampling.BICUBIC)
            
            x = int(placement["x"])
            y = int(placement["y"])

            # 1. APPLY SOFT DROP SHADOW (DISABLED)
            # draw_shadow(canvas, img, (x + 30, y + 30))

            # 2. PASTE PRODUCT
            # All products paste once only - no clustering
            canvas.alpha_composite(img, (x, y))

            # 3. DRAW PRODUCT LABEL
            label_text = placement.get("label", "")
            if label_text:
                draw_label(canvas, label_text, (x, y + target_h + 20), target_w)

        except Exception as e:
            print(f"Warning: Failed to place {placement.get('file', 'unknown')}: {e}")

    # 3. ADD BRANDING (Header/Footer)
    draw_branding(canvas, A3_W, A3_H)

    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"output/storyboard_A3_{timestamp}.png"

    canvas.save(output_path, dpi=(300, 300))
    print(f"Storyboard saved: {output_path}")
    return output_path

def draw_shadow(canvas, img, position):
    """Draws a soft drop shadow for an image."""
    from PIL import ImageFilter
    
    # Create a shadow mask from the image's alpha channel
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 100)) # Low opacity black
    shadow_mask = img.split()[-1] # Alpha channel
    
    # Blur the mask for softness
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(radius=20))
    
    # Paste into canvas
    canvas.paste(shadow, position, mask=shadow_mask)

def draw_label(img, text, position, width):
    """Draws small gray label text below product."""
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 35)
    except:
        font = ImageFont.load_default()
    
    # Center text horizontally relative to product width
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    center_x = position[0] + (width - text_w) // 2
    
    draw.text((center_x, position[1]), text, fill=(120, 120, 120, 255), font=font)

def draw_branding(img, width, height):
    """Surgical Branding: Torn Header + Airplane, Splash Logo + Disclaimer."""
    from PIL import ImageDraw, ImageFont, ImageFilter
    import random
    
    draw = ImageDraw.Draw(img)
    
    # 1. Header: Light Blue Banner
    header_h = 280
    blue_color = (135, 206, 250, 255) # Reference Light Blue
    draw.rectangle([(0, 0), (width, header_h)], fill=blue_color)
    
    # 2. Torn Paper Effect (Right side)
    torn_x = width - 450
    for i in range(0, header_h, 8):
        offset = random.randint(-25, 25)
        draw.ellipse([torn_x + offset, i - 20, width + 500, i + 20], fill=(255, 255, 255, 255))

    # 3. Header Text & Airplane Icon
    try:
        font_lg = ImageFont.truetype("arialbd.ttf", 90)
        font_sm = ImageFont.truetype("arial.ttf", 55)
    except:
        font_lg = ImageFont.load_default()
        font_sm = ImageFont.load_default()

    # "Customer Name"
    draw.text((150, 80), "CUSTOMER NAME", fill=(255, 255, 255, 255), font=font_lg)
    
    # Airplane Icon (approximate with unicode or shape)
    draw.text((880, 95), "✈", fill=(255, 255, 255, 255), font=font_lg) 
    
    # "Range Proposal"
    draw.text((1000, 110), "Range Proposal", fill=(255, 255, 255, 255), font=font_sm)
    
    # 4. Footer
    footer_y = height - 130
    
    # Splash Logo Placeholder
    logo_color = (0, 102, 204, 255)
    draw.ellipse([100, footer_y, 180, footer_y + 80], fill=logo_color)
    draw.text((200, footer_y + 10), "CORNFLOWER", fill=logo_color, font=font_sm)
    
    # Disclaimer Text
    disclaimer = "Design © Cornflower Ltd. All images on this board.\nPlease do not reproduce or distribute to third parties."
    try:
        font_disc = ImageFont.truetype("arial.ttf", 32)
    except:
        font_disc = ImageFont.load_default()
        
    draw.multiline_text((width - 950, footer_y), disclaimer, fill=(140, 140, 140, 255), font=font_disc, align="right")