import cv2, numpy as np, os
from PIL import Image

def analyze_products(folder):
    """
    Dynamic product analysis for any 8 products.
    Analyzes visual characteristics for layout decisions.
    """
    products = []
    
    for f in os.listdir(folder):
        if f.lower().endswith('.png'):
            img_path = os.path.join(folder, f)
            
            # Load image
            pil_img = Image.open(img_path).convert("RGBA")
            img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
            
            h, w = img.shape[:2]
            area = h * w
            
            # Basic aspect analysis
            aspect_ratio = w / h
            if aspect_ratio > 1.5:
                aspect = "horizontal"
            elif aspect_ratio < 0.67:
                aspect = "vertical"
            else:
                aspect = "square"
            
            # Size categorization based on realistic product image areas
            if area > 8000000:  # > 8MP pixels
                size_category = "large"
            elif area > 2000000:  # 2-8MP pixels  
                size_category = "medium"
            else:  # < 2MP pixels
                size_category = "small"
            
            # Basic complexity analysis with adjusted thresholds
            gray = cv2.cvtColor(img[:, :, :3], cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / area
            
            if edge_density > 0.04:
                complexity = "complex"
            elif edge_density > 0.02:
                complexity = "moderate"
            else:
                complexity = "simple"
            
            # Hero candidate detection
            is_hero_candidate = (
                size_category in ["large", "medium"] and 
                aspect in ["horizontal", "square"] and 
                complexity in ["simple", "moderate"]
            )
            
            # Layout priority scoring
            if is_hero_candidate and size_category == "large":
                layout_priority = 1  # Best hero candidates
            elif is_hero_candidate and size_category == "medium":
                layout_priority = 2  # Good hero candidates
            elif size_category == "large":
                layout_priority = 3  # Large supporting elements
            elif size_category == "medium":
                layout_priority = 4  # Medium elements
            else:
                layout_priority = 5  # Small accent elements
            
            products.append({
                "file": f,
                "path": img_path,
                "width": w,
                "height": h,
                "area": area,
                "aspect_ratio": aspect_ratio,
                "aspect": aspect,
                "size_category": size_category,
                "complexity": complexity,
                "edge_density": edge_density,
                "is_hero_candidate": is_hero_candidate,
                "layout_priority": layout_priority
            })
    
    # Sort by size (largest first) - helps with hero selection
    products.sort(key=lambda x: x["area"], reverse=True)
    return products
