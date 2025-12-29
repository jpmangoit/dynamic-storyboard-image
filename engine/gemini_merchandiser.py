# engine/gemini_merchandiser.py
from google import genai
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()

def merchandize(pvil_data):
    """
    Uses Gemini (via google-genai) to create creative, dynamic A3 storyboard layouts.
    """
    # Relaxed constraint: Allow 1 to 8 products
    if not (1 <= len(pvil_data) <= 8):
        print(f"Warning: Optimal performance is with 4-8 products. Found {len(pvil_data)}.")
        if len(pvil_data) == 0:
             raise ValueError("No products found to merchandize.")

    # Load Manual Manifest
    manifest = {}
    manifest_path = os.path.join("products", "manifest.json")
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
            print("Loaded manual product manifest.")
        except Exception as e:
            print(f"Error loading manifest: {e}")

    # Rich product insights with Manual Overrides
    product_insights = []
    
    # Check if we have a Hero defined in manifest
    manual_hero = next((k for k,v in manifest.items() if v.lower() == "hero"), None)
    
    for i, item in enumerate(pvil_data):
        filename = item["file"]
        
        # Get Manual Role or Fallback
        manual_role = manifest.get(filename, "medium")
        
        # If manifest exists but this item isn't in it, default to medium
        # If no manifest, default to auto-logic (which we are replacing with this hybrid logic)
        
        insight = (
            f"{i+1}. {filename}: "
            f"ROLE: {manual_role.upper()} "
            f"(Original Data: aspect {item['aspect']}, {item['size_category']})"
        )
        product_insights.append(insight)

    prompt = f"""
You are an expert AI Visual Merchandiser Director.
Task: Select the best Layout Template for these products and assign them to slots.

AVAILABLE TEMPLATES:
1. "final_spec":
   - **MASTER SPEC**: High Density, Tilted items, Drop Shadows.
   - Slots: 
     - "hero_left" (Tea Towel)
     - "magnet" (Tilted Fridge Magnet), "keyring" (Tilted Keyring)
     - "print_back" (Mounted Print - behind bag)
     - "anchor_right" (Theale Bag - Tilted Right)
     - "notebook" (Angled Notebook), "card" (Straight Card)
     - "mugs_cluster" (3 Mugs Group)
2. "reference_1_match":
   - Legacy dense layout.
2. "asymmetric_left":
   - Use when you have a Tall/Vertical Hero.
   - Slots: "hero_slot" (Huge Left), "secondary_1", "secondary_2" (Top Right), "filler_1...3", "tiny_1...3".
2. "waterfall_right":
   - Use when the Hero looks best on the Right.
   - Slots: "hero_slot" (Huge Right), "secondary_1" (Top Left), "filler_1...2", "tiny_1...3".
3. "editorial_grid":
   - Use for a clean, squarely aligned look.
   - Slots: "hero_slot" (Top Left Quad), "secondary_1" (Top Right), "secondary_2", "filler_1...2", "tiny_1...2".

INPUTS:
Products (ordered by priority):
{chr(10).join(product_insights)}

CRITICAL INSTRUCTIONS:
- You MUST use one of the template keys above.
- You MUST assign the "HERO" product to the "hero_slot".
- Assign other products to slots that match their size (Secondary=Large, Filler=Medium, Tiny=Small).
- Return strictly JSON.

OUTPUT JSON:
{{
  "strategy_name": "Using Asymmetric Left for vertical impact",
  "template_name": "asymmetric_left",
  "assignments": {{
    "hero_slot": "bag_hero.png",
    "secondary_1": "notebook.png",
    "tiny_1": "keyring.png"
  }}
}}
"""

    try:
        # Initialize client with API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
            
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-flash-latest", 
            contents=[prompt]
        )
        
        text = response.text
        cleaned_text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(cleaned_text)
        return result

    except Exception as e:
        print(f"Gemini failed: {e}")
        # Return a fallback or re-raise depending on desired stability
        raise