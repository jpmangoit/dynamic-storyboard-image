import os
import json
import math
from PIL import Image
from google import genai
from dotenv import load_dotenv

load_dotenv()

class LayoutBrain:
    def __init__(self, config=None):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.config = config
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[WARN] Failed to initialize Gemini client: {e}")

    def get_image_info(self, path):
        """Returns aspect ratio and orientation string."""
        try:
            with Image.open(path) as img:
                w, h = img.size
                aspect = w / h
                if aspect > 1.2: orientation = "Landscape"
                elif aspect < 0.8: orientation = "Portrait"
                else: orientation = "Square"
                return aspect, orientation, w, h
        except:
            return 1.0, "Square", 1000, 1000

    def generate_layout_strategy(self, inventory):
        """
        Analyzes inventory and returns a Layout Tree JSON.
        """
        if not self.client:
            print("[WARN] No Gemini API Key found. Using fallback logic.")
            return self._fallback_strategy(inventory)

        # 0. Get Canvas Info & Size Classes
        canvas_w = 4961
        canvas_h = 3508
        size_classes_desc = ""
        
        if self.config:
            if "content_area" in self.config:
                 canvas_w = self.config["content_area"]["w"]
                 canvas_h = self.config["content_area"]["h"]
            
            # Extract Size Classes for Context
            if "size_classes" in self.config:
                sc = self.config["size_classes"]
                desc_lines = []
                for k, v in sc.items():
                    dims = ""
                    if "fixed_width_px" in v: dims += f"W:{v['fixed_width_px']}px "
                    if "fixed_height_px" in v: dims += f"H:{v['fixed_height_px']}px "
                    if "max_width_percent" in v: dims += f"MaxW:{v['max_width_percent']}% "
                    if "max_height_percent" in v: dims += f"MaxH:{v['max_height_percent']}% "
                    desc_lines.append(f"   - {k}: {dims}")
                size_classes_desc = "\n".join(desc_lines)

        # 1. Prepare Inventory Description
        items_desc = []
        hero_items = []
        for role, path in inventory.items():
            aspect, orient, w, h = self.get_image_info(path)
            role_base = role.split('_')[0]
            items_desc.append(f"- ID: '{role}' | Role: {role_base} | Aspect: {aspect:.2f} ({orient}) | Size: {w}x{h}")
            
            if "hero" in role_base.lower():
                hero_items.append(role)
            
        inventory_text = "\n".join(items_desc)
        
        # 2. Strategy Injection
        strategy_hint = ""
        if len(hero_items) >= 2:
            strategy_hint = f"""
        *** DUAL HERO STRATEGY ACTIVE ***
        Detected {len(hero_items)} HERO items: {hero_items}.
        These items Combined require ~60-70% of the canvas width (based on 'xl' size class).
        
        RECOMMENDED STRUCTURES (Choose one):
        A) "Bookends": Split Horizontal (Ratio 0.35) -> First=Hero1, Second=Split Horizontal (Ratio 0.5) -> First=Accessories Grid, Second=Hero2.
        B) "Major Split": Split Horizontal (Ratio 0.55) -> First=Hero1, Second=Split Vertical -> First=Hero2, Second=Accessories.
        
        DO NOT stack two heroes vertically in a thin column. They need WIDTH.
        """
        elif len(hero_items) == 1:
             strategy_hint = f"""
        *** SINGLE HERO STRATEGY ACTIVE ***
        Detected 1 HERO item: {hero_items}.
        This item needs a dedicated 'xl' slot (approx 35-40% width).
        Place it on the Left or Right edge using a vertical split.
        """

        # 3. Construct Prompt
        item_count = len(inventory)
        item_ids_str = ", ".join([f"'{k}'" for k in inventory.keys()])
        
        prompt = f"""
        You are an expert Art Director for a high-end fashion/merchandise brand. 
        Your goal is to design a DYNAMIC, HIGH-DENSITY A3 storyboard layout.
        CANVAS CONTENT AREA: Width {canvas_w} px, Height {canvas_h} px.
        
        BRAND SIZE CLASSES (Reference for scaling):
        {size_classes_desc}
        
        INPUT INVENTORY ({item_count} ITEMS TOTAL):
        {inventory_text}
        
        STRATEGIC DIRECTIVE:
        {strategy_hint}
        
        TASK:
        Generate a 'Layout Tree' JSON structure to arrange ALL {item_count} items into a cohesive, magazine-quality composition.
        
        CRITICAL DESIGN RULES:
        1. **MUST USE ALL ITEMS**: You have {item_count} items: [{item_ids_str}]. The output JSON must contain exactly {item_count} 'slot' nodes. Double check this.
        2. **MAXIMIZE COVERAGE**: Do NOT leave large empty spaces. The items should fill the canvas visually.
        3. **HERO PROMINENCE**: 
           - **SINGLE HERO**: Must occupy 40-50% of canvas (ideally Left or Right half).
           - **DUAL HEROES**: You MUST split the main canvas (e.g. 50/50 or 60/40 Horizontal) to give BOTH heroes large, 'xl' equivalent slots. Do NOT put heroes in small grids.
        4. **TIGHT GRIDS**: Group 'accessory' and 'support' items into tight grids or clusters.
        5. **HOMOGENEOUS GRIDS**: Do NOT mix Portrait and Landscape items in the same 'grid'. The solver creates identical cells, so mixed shapes will cause whitespace. Use 'split' to separate different shapes.
        6. **ASPECT RATIO AWARENESS**: 
           - Match the container shape to the image aspect ratio.
           - Portrait images (Aspect < 0.8) -> Vertical splits.
           - Landscape images (Aspect > 1.2) -> Horizontal splits.
        7. **NO TINY SLIVERS**: Avoid split ratios less than 0.25 or greater than 0.75 unless it is for a sidebar.
        
        STRUCTURE DEFINITION:
        - "split": {{ "type": "split", "direction": "horizontal", "ratio": 0.5, "first": {{ ... }}, "second": {{ ... }} }}
        - "grid": {{ "type": "grid", "columns": 2, "items": ["id1", "id2"] }}
        - "slot": {{ "type": "slot", "item_id": "id1" }}
        
        OUTPUT FORMAT:
        Return ONLY the raw JSON object.
        
        EXAMPLE OUTPUT:
        {{
            "type": "split",
            "direction": "horizontal",
            "ratio": 0.6,
            "gap": 40,
            "first": {{ "type": "slot", "item_id": "hero_1" }},
            "second": {{
                "type": "grid",
                "columns": 1,
                "gap": 40,
                "items": ["support_1", "support_2"]
            }}
        }}
        """
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=[prompt]
            )
            
            text = response.text
            # Clean markdown if present
            text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
            
        except Exception as e:
            print(f"[ERROR] Gemini Generation Failed: {e}")
            return self._fallback_strategy(inventory)

    def _fallback_strategy(self, inventory):
        """Simple algorithmic fallback if AI fails."""
        # Simple Logic: Split Hero (Left) vs Rest (Right Grid)
        keys = list(inventory.keys())
        heroes = [k for k in keys if "hero" in k]
        others = [k for k in keys if "hero" not in k]
        
        if heroes:
            hero_id = heroes[0]
            others += heroes[1:] # Add extra heroes to others
            
            return {
                "type": "split",
                "direction": "horizontal",
                "ratio": 0.5,
                "gap": 60,
                "first": { "type": "slot", "item_id": hero_id },
                "second": {
                    "type": "grid",
                    "columns": 2,
                    "gap": 60,
                    "items": others
                }
            }
        else:
            # No hero, just big grid
            return {
                "type": "grid",
                "columns": 3,
                "gap": 60,
                "items": keys
            }
