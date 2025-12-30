import os
import sys
import json
from PIL import Image

try:
    from transformers import CLIPProcessor, CLIPModel
    import torch
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("[WARN] transformers/torch not found. Run in venv.")

# Configuration
LABELS = [
    "tea towel", 
    "tote bag", 
    "mug", 
    "keyring", 
    "magnet", 
    "notebook", 
    "frame",
    "greeting card"
]

AMBIGUOUS_LABELS = ["tea towel", "magnet", "greeting card", "frame"]

def load_ai():
    print("[AI] Loading CLIP model...", file=sys.stderr)
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    return model, processor

def classify_image(image_path, model, processor):
    """
    Classify an image using CLIP + Aspect Ratio Heuristics.
    Returns: (role, confidence_score, explanation)
    """
    try:
        image = Image.open(image_path)
        
        # 0. Filename Hinting (Zero-Config Manifest)
        # Check if filename contains keywords from labels to guide the AI
        filename_base = os.path.basename(image_path).lower()
        filename_hint_idx = -1
        
        for idx, label in enumerate(LABELS):
            label_words = label.split()
            for word in label_words:
                if len(word) > 2 and word in filename_base:
                    filename_hint_idx = idx
                    break
            if filename_hint_idx != -1:
                break
        
        # HARD OVERRIDE: If Filename matches a label, trust it implicitly
        if filename_hint_idx != -1:
            forced_label = LABELS[filename_hint_idx]
            role = None
            
            # Canonical Mapping for Hints
            if forced_label == "tea towel": role = "hero_left"
            elif forced_label == "tote bag": role = "hero_right" 
            elif forced_label == "frame": role = "support_large"
            elif forced_label == "greeting card": role = "support_medium_large" # Targeted Fix!
            elif forced_label == "notebook": role = "support_medium"
            elif forced_label == "mug": role = "cluster_bottom"
            elif forced_label == "magnet": role = "accessory_small"
            elif forced_label == "keyring": role = "accessory_tiny"
            
            if role:
                 return role, 1.0, f"Filename says '{forced_label}'"

        # 1. AI Classification
        inputs = processor(text=LABELS, images=image, return_tensors="pt", padding=True)
        outputs = model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1)
        
        # Get top prediction
        pred_idx = probs.argmax().item()
        ai_label = LABELS[pred_idx]
        conf = probs[0][pred_idx].item()
        
        # 2. Heuristics (Aspect Ratio)
        w, h = image.size
        aspect = w / h
        
        role = None
        reason = f"AI says '{ai_label}' ({conf:.1%})"
        
        # Logic adapted from generate_collage.py
        if ai_label in AMBIGUOUS_LABELS:
            # Aspect ratio is king for flat rectangular objects
            if aspect < 0.6:
                role = "hero_left"      # Very tall -> Towel
                reason += " + Tall (< 0.6)"
            elif 0.6 <= aspect < 0.85:
                 role = "hero_left"      # Tall-ish -> Towel or Print
                 reason += " + Portrait (< 0.85)"
            elif 0.9 <= aspect <= 1.1:
                role = "accessory_small" # Square -> Magnet/Coaster
                reason += " + Square (~1.0)"
            elif 0.85 <= aspect < 0.9:
                role = "support_medium_large" # Greeting Card typically 
                reason += " + Card Aspect"
            elif aspect > 1.2:
                role = "support_large"   # Wide -> Frame/Print
                reason += " + Landscape (> 1.2)"
            else:
                # Fallback to AI label if aspect is inconclusive
                if ai_label == "tea towel": role = "hero_left"
                elif ai_label == "frame": role = "support_large"
                elif ai_label == "greeting card": role = "support_medium_large"
                elif ai_label == "magnet": role = "accessory_small"
        
        # Distinct Group (Shape usually defines these well)
        if role is None:
            if ai_label == "tote bag":
                role = "hero_right"
            elif ai_label == "mug":
                role = "cluster_bottom"
            elif ai_label == "keyring":
                role = "accessory_tiny"
            elif ai_label == "notebook":
                role = "support_medium"
                
        # Final Fallback
        if role is None:
            role = "support_medium" # Generic fallback
            reason += " -> Fallback"
            
        return role, conf, reason
        
    except Exception as e:
        return None, 0.0, f"Error: {e}"

# Role Mapping for Manual Overrides
MANUAL_ROLE_MAP = {
    "hero": "hero_left",
    "large": "support_large",
    "medium": "support_medium_large", # slightly larger than medium
    "small": "accessory_small",
    "tiny": "accessory_tiny",
    "support": "support_medium",
    "cluster": "cluster_bottom"
}

def get_manual_role(filename, manifest):
    """
    Checks for manual overrides in Manifest or Filename.
    Returns: (role, reason) or (None, None)
    """
    # 1. Manifest Check
    if filename in manifest:
        user_role = manifest[filename].lower()
        mapped = MANUAL_ROLE_MAP.get(user_role, user_role) # Use distinct if not in map (e.g. 'hero_right')
        return mapped, f"Manifest says '{user_role}'"
        
    # 2. Filename Tag Check
    # e.g. "towel_hero.png" -> "hero_left"
    base = filename.lower()
    for key, mapped_role in MANUAL_ROLE_MAP.items():
        if f"_{key}" in base or f"-{key}" in base:
             return mapped_role, f"Filename tag '{key}'"
             
    # Specific edge case: "hero" in filename could mean left or right
    if "_hero" in base:
        return "hero_left", "Filename tag 'hero'"

    return None, None

import random

def scan_directory(directory, model, processor, flexible=False):
    """Scan a directory and build an inventory."""
    inventory = {}
    
    print(f"[AI] Scanning '{directory}'...", file=sys.stderr)
    
    if not os.path.exists(directory):
        print(f"[ERROR] Directory not found: {directory}", file=sys.stderr)
        return {}

    # Load Manifest if exists
    manifest = {}
    manifest_path = os.path.join(directory, "manifest.json")
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            print(f"[AI] Loaded manifest with {len(manifest)} overrides.", file=sys.stderr)
        except Exception as e:
            print(f"[WARN] Failed to load manifest: {e}", file=sys.stderr)

    # Get file list
    files = os.listdir(directory)
    
    # Randomize order if flexible mode is on to allow varied placement
    if flexible:
        random.shuffle(files)
        print("[AI] Flexible mode: Randomizing processing order.", file=sys.stderr)
    else:
        files.sort() # Deterministic order for default mode

    for filename in files:
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            path = os.path.join(directory, filename)
            
            # Check Manual Override FIRST
            role, reason = get_manual_role(filename, manifest)
            
            # If no manual override, use AI
            if not role:
                 role, conf, reason = classify_image(path, model, processor)
            
            if role:
                # Flexible Mode: Generalize roles to allow random placement
                # But PRESERVE size suffixes for accessories/supports so Gemini respects sizing
                if flexible:
                    if "hero" in role:
                        role = "hero"  # Generalize all heroes to allow flexible placement
                    elif "cluster" in role:
                        role = "cluster"  # Generalize clusters
                    # For supports and accessories, keep the FULL role including size suffix
                    # This allows Gemini to differentiate accessory_small from accessory_tiny
                
                # Handle duplicate roles (prevent overwrite)
                final_role = role
                counter = 2
                while final_role in inventory:
                    final_role = f"{role}_{counter}"
                    counter += 1
                
                print(f"  > {filename} -> {final_role} [Base: {role}, {reason}]", file=sys.stderr)
                inventory[final_role] = path
            else:
                print(f"  [SKIP] {filename} - No role determined.", file=sys.stderr)
        else:
            print(f"  [IGNORE] {filename}", file=sys.stderr)
            
    return inventory

def main():
    if len(sys.argv) < 2:
        target_dir = "products" # Default
    else:
        target_dir = sys.argv[1]

    if not AI_AVAILABLE:
        print(json.dumps({"error": "AI modules missing"}))
        return

    model, processor = load_ai()
    inventory = scan_directory(target_dir, model, processor)
    
    # OUTPUT JSON to stdout
    print(json.dumps(inventory, indent=2))

if __name__ == "__main__":
    main()
