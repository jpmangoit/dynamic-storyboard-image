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
        
        # 2. Create Size Mapping Dictionary
        size_mapping = {}
        for role in inventory.keys():
            role_base = role.split('_')[0].lower()
            if "hero" in role_base:
                size_mapping[role] = {
                    "min_width_pct": 30,
                    "max_width_pct": 40,
                    "size_class": "xl",
                    "description": f"{role} must occupy 30-40% of canvas width in a dedicated 'slot' node, NEVER in a grid"
                }
            elif "support" in role_base:
                if "large" in role.lower():
                    size_mapping[role] = {
                        "min_width_pct": 15,
                        "max_width_pct": 20,
                        "size_class": "large",
                        "description": f"{role} should occupy 15-20% of canvas width"
                    }
                else:
                    size_mapping[role] = {
                        "min_width_pct": 10,
                        "max_width_pct": 15,
                        "size_class": "medium",
                        "description": f"{role} should occupy 10-15% of canvas width"
                    }
            elif "cluster" in role_base:
                size_mapping[role] = {
                    "min_width_pct": 20,
                    "max_width_pct": 30,
                    "size_class": "large",
                    "description": f"{role} is a cluster group, needs 20-30% width"
                }
            else:  # accessories, small items
                size_mapping[role] = {
                    "min_width_pct": 8,
                    "max_width_pct": 12,
                    "size_class": "small",
                    "description": f"{role} is a small item, 8-12% width is acceptable"
                }
        
        # Format size mapping for prompt
        size_mapping_text = "\n".join([
            f"   • {role}: {info['description']} (size_class: {info['size_class']})"
            for role, info in size_mapping.items()
        ])
        
        # Generate strategic directive based on hero count
        strategy_hint = ""
        if len(hero_items) >= 2:
            strategy_hint = f"""
*** DUAL HERO STRATEGY ***
You have {len(hero_items)} HERO products: {hero_items}

[!] CRITICAL SIZE REQUIREMENT: EACH hero must INDEPENDENTLY occupy 30-40% of TOTAL canvas width.
    This means after ALL nested splits, calculate the final width percentage - it must be 30%+.

CALCULATING WIDTH PERCENTAGES:
- If hero_1 is in first of horizontal split (ratio 0.35), it gets 35% width ✓
- If hero_2 is nested: parent gets 65%, then vertical split 40%, then horizontal 50%
  → hero_2 gets 0.65 × 0.40 × 0.50 = 13% width ✗ TOO SMALL!

RECOMMENDED APPROACHES (ensures EACH hero gets 30%+ width):

A) "Bookends Layout" (PREFERRED for dual heroes):
   ```
   Split Horizontal (ratio: 0.35)
   ├─ First: Hero 1 (gets 35% width) ✓
   └─ Second (65% remaining)
       └─ Split Horizontal (ratio: 0.54)  
           ├─ First: Grid of accessories (gets 35% of total)
           └─ Second: Hero 2 (gets 30% width) ✓
   ```

B) "Side-by-Side Layout":
   ```
   Split Horizontal (ratio: 0.4)
   ├─ First: Hero 1 (gets 40% width) ✓
   └─ Second (60% remaining)
       └─ Split Horizontal (ratio: 0.5)
           ├─ First: Hero 2 (gets 30% width) ✓
           └─ Second: Accessories stack
   ```

[!] DO NOT nest heroes more than ONE level deep in splits, or they will become too small!
"""
        elif len(hero_items) == 1:
            strategy_hint = f"""
*** SINGLE HERO STRATEGY ***
You have 1 HERO product: {hero_items[0]}

This hero requires 35-40% of canvas width in a DEDICATED 'slot' node.

RECOMMENDED APPROACH:
- Split Horizontal (ratio: 0.35-0.4) -> First = Hero, Second = Grid/Stack of other products
- Place hero on LEFT or RIGHT edge for maximum impact
"""
        
        item_count = len(inventory)
        item_ids_str = ", ".join([f"'{k}'" for k in inventory.keys()])
        
        prompt = f"""
You are an expert Art Director for a PREMIUM EDITORIAL BRAND creating magazine-quality storyboards.

CANVAS CONTENT AREA: {canvas_w}px wide × {canvas_h}px tall

═══════════════════════════════════════════════════════════════════
CRITICAL REQUIREMENT: PRODUCT SIZE HIERARCHY
═══════════════════════════════════════════════════════════════════

You have {item_count} products to arrange: [{item_ids_str}]

**MANDATORY SIZE ALLOCATIONS** (based on role):
{size_mapping_text}

[!] **ABSOLUTE RULE**: Hero products MUST be in DEDICATED 'slot' nodes occupying 30-40% canvas width.
   NEVER put a hero product in a 'grid'! Grids create equal-sized cells which will make heroes too small.

BRAND SIZE CLASSES (from professional design system):
{size_classes_desc}

═══════════════════════════════════════════════════════════════════
STRATEGIC GUIDANCE
═══════════════════════════════════════════════════════════════════

{strategy_hint}

═══════════════════════════════════════════════════════════════════
LAYOUT STRUCTURE GRAMMAR
═══════════════════════════════════════════════════════════════════

**split**: Divides space into two regions (first/second)
  - direction: "horizontal" (left/right) or "vertical" (top/bottom)
  - ratio: 0.0-1.0 (percentage of FIRST region, e.g. 0.35 = first gets 35%)
  - gap: spacing in pixels between regions (default: 40-60px)

**grid**: Creates equal-sized cells for multiple items
  - columns: number of columns
  - items: array of item_ids
  - gap: spacing between cells
  [!] WARNING: Grids create EQUAL-SIZED cells. Only use for items of similar importance!

**slot**: Single product placement
  - item_id: the product identifier

═══════════════════════════════════════════════════════════════════
FEW-SHOT EXAMPLES OF EXCELLENT LAYOUTS
═══════════════════════════════════════════════════════════════════

**EXAMPLE 1: Dual Hero Balanced Layout**
// Scenario: 2 Heroes + 4 Medium/Small products
{{
    "type": "split",
    "direction": "horizontal",
    "ratio": 0.35,
    "gap": 50,
    "first": {{
        "type": "slot",
        "item_id": "hero_left"  // Gets 35% width - PROMINENT!
    }},
    "second": {{
        "type": "split",
        "direction": "horizontal",
        "ratio": 0.6,
        "gap": 50,
        "first": {{
            "type": "grid",
            "columns": 2,
            "gap": 40,
            "items": ["support_large", "support_medium", "accessory_small", "accessory_tiny"]
        }},
        "second": {{
            "type": "slot",
            "item_id": "hero_right"  // Gets ~30% width - PROMINENT!
        }}
    }}
}}

**EXAMPLE 2: Single Hero with Support Stack**
// Scenario: 1 Hero + 3 Support items of varying sizes
{{
    "type": "split",
    "direction": "horizontal",
    "ratio": 0.4,
    "gap": 60,
    "first": {{
        "type": "slot",
        "item_id": "hero_main"  // Gets 40% width - DOMINANT!
    }},
    "second": {{
        "type": "split",
        "direction": "vertical",
        "ratio": 0.5,
        "gap": 50,
        "first": {{
            "type": "slot",
            "item_id": "support_large"  // Top half of remaining space
        }},
        "second": {{
            "type": "grid",
            "columns": 2,
            "gap": 40,
            "items": ["support_medium", "accessory_small"]  // Bottom half split
        }}
    }}
}}

═══════════════════════════════════════════════════════════════════
YOUR TASK
═══════════════════════════════════════════════════════════════════

Generate a Layout Tree JSON for ALL {item_count} products: [{item_ids_str}]

**DESIGN PRINCIPLES:**
1. [+] **PREMIUM SPACING**: This is editorial design, not a catalog. Allow generous whitespace.
2. [+] **VISUAL HIERARCHY**: Hero products (30-40% width) should DOMINATE the composition.
3. [+] **INCLUDE EVERY PRODUCT**: The JSON must contain ALL {item_count} items. Missing products = CRITICAL FAILURE.
4. [+] **DEDICATED HERO SLOTS**: Heroes MUST be in 'slot' nodes with 30-40% width allocation via split ratios.
5. [+] **SMART GROUPING**: Only grid items of similar size/importance. Don't mix heroes with accessories!
6. [+] **ASPECT RATIO MATCHING**: 
   - Portrait items (aspect < 0.8) -> use vertical splits or vertical-oriented grids
   - Landscape items (aspect > 1.2) -> use horizontal splits
7. [+] **BALANCED SPLITS**: Avoid extreme ratios like 0.1 or 0.9 unless intentional (sidebar effect)

**ANTI-PATTERNS TO AVOID:**
[-] Putting hero products in grids
[-] Making all products the same size
[-] Extreme cramming to "fit everything"
[-] Skipping or omitting any products
[-] Using tiny slivers (ratio < 0.2 or > 0.8) without design reason

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════════════

Return ONLY the raw JSON object. No markdown, no explanations.

VALIDATION CHECKLIST (before returning):
[ ] Count all 'slot' nodes and 'grid' items = {item_count} total?
[ ] All hero products in dedicated 'slot' nodes (not grids)?
[ ] Hero slots allocated 30-40% width via parent split ratio?
[ ] No extreme split ratios (< 0.2 or > 0.8) without good reason?

BEGIN YOUR LAYOUT TREE JSON NOW:
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
