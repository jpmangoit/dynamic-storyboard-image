#!/usr/bin/env python3
"""
Header Generator - Creates brush stroke header effect programmatically
"""

from PIL import Image, ImageDraw, ImageFont
import random

def create_brush_stroke_header(width=4961, height=380, bg_color="#4A90C8"):
    """
    Create a header with brush stroke effect on the right side.
    
    Args:
        width: Header width in pixels
        height: Header height in pixels
        bg_color: Background color (hex)
    
    Returns:
        PIL Image object
    """
    # Create base image
    header = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(header)
    
    # Create brush stroke effect on right side
    # Use irregular polygon to simulate brush strokes
    brush_start_x = int(width * 0.75)  # Start at 75% of width
    
    # Create multiple brush stroke layers for organic look
    for layer in range(3):
        points = []
        
        # Top edge - wavy
        for x in range(brush_start_x, width, 20):
            y_offset = random.randint(-15, 15) + (layer * 10)
            points.append((x, y_offset))
        
        # Right edge
        points.append((width, 0))
        points.append((width, height))
        
        # Bottom edge - wavy
        for x in range(width, brush_start_x, -20):
            y_offset = random.randint(-15, 15) + (layer * 10)
            points.append((x, height + y_offset))
        
        # Close the polygon
        points.append((brush_start_x, height))
        points.append((brush_start_x, 0))
        
        # Draw with white color
        draw.polygon(points, fill='white')
    
    return header

def create_brush_header_v2(width=4961, height=380, bg_color="#4A90C8"):
    """
    Alternative brush stroke using bezier-like curves.
    More controlled and smoother appearance.
    """
    header = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(header)
    
    # Brush stroke starts at ~70% width
    brush_x = int(width * 0.7)
    
    # Create jagged edge points
    points = []
    
    # Top edge with irregular pattern
    num_points = 15
    for i in range(num_points):
        x = brush_x + (width - brush_x) * (i / num_points)
        # Create wave pattern
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

def add_text_to_header(header, customer_name="Customer Name", subtitle="Range Proposal"):
    """
    Add text overlays to header image.
    """
    draw = ImageDraw.Draw(header)
    
    # Try to load fonts
    try:
        font_large = ImageFont.truetype("arial.ttf", 86)
        font_small = ImageFont.truetype("arial.ttf", 44)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw customer name
    draw.text((260, 170), customer_name, fill='white', font=font_large)
    
    # Draw subtitle
    draw.text((260, 285), subtitle, fill='white', font=font_small)
    
    return header

# Test the function
if __name__ == "__main__":
    # Create header
    header = create_brush_header_v2(4961, 380, "#4A90C8")
    header = add_text_to_header(header, "Durham University", "Range Proposal")
    
    # Save test output
    header.save("test_header.png")
    print("Header created: test_header.png")
