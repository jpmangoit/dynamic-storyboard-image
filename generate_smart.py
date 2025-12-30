import os
import sys
import json
from datetime import datetime
import importlib.util

# Utilities to load modules without modifying them
from engine import smart_classify
from engine import layout_generator

# Import rendering logic from generate_from_json using spec to avoid executing main() if it wasn't guarded (it is guarded, but direct import is cleaner)
from generate_from_json import load_config
from engine.smart_renderer import render_smart_storyboard

import argparse

def main():
    print("=" * 60)
    print("AI-Driven Smart Layout Generator")
    print("=" * 60)
    
    parser = argparse.ArgumentParser(description="Generate AI Storyboards")
    parser.add_argument("customer_name", nargs="?", default="Generative Client", help="Name of the client/project")
    parser.add_argument("--template", help="Force a specific layout template (e.g. layout_A_classic)")
    parser.add_argument("--flexible", action="store_true", help="Allow flexible/random placement of products within their category (e.g. swap heroes)")
    parser.add_argument("--ai-layout", action="store_true", help="Use Generative AI (Gemini) to design the layout structure dynamically")
    
    args = parser.parse_args()
    
    customer_name = args.customer_name
    preferred_template = args.template
    flexible_mode = args.flexible
    use_ai_layout = args.ai_layout
    
    # 1. Configuration
    print("\n[1] Loading Configuration...")
    config = load_config()
    
    # Calculate Content Area if not defined (Safe area between Header and Footer)
    if "content_area" not in config:
        canvas_w = config["canvas"]["width_px"]
        canvas_h = config["canvas"]["height_px"]
        margin = config["canvas"].get("safe_margin_px", 177)
        
        # Header bottom
        h_cfg = config.get("header", {})
        h_bottom = h_cfg.get("area", {}).get("y", 0) + h_cfg.get("area", {}).get("h", 0)
        
        # Footer top
        f_cfg = config.get("footer", {})
        f_top = f_cfg.get("area", {}).get("y", canvas_h)
        
        # Define Safe Content Area
        config["content_area"] = {
            "x": margin,
            "y": h_bottom + 50, # 50px padding
            "w": canvas_w - (margin * 2),
            "h": f_top - h_bottom - 100 # 50px padding top/bottom
        }
        print(f"   > Calculated Content Area: {config['content_area']}")
    
    # 2. Smart Inventory Scan
    print("\n[2] AI Inventory Scan (products/)...")
    if not smart_classify.AI_AVAILABLE:
        print("   [ERROR] AI modules not available. Cannot proceed with smart generation.")
        return

    model, processor = smart_classify.load_ai()
    # If using AI Layout, we definitely want flexible/generalized roles
    inventory = smart_classify.scan_directory("products", model, processor, flexible=(flexible_mode or use_ai_layout))
    
    if not inventory:
        print("   [ERROR] No products found.")
        return
        
    print(f"   > Found {len(inventory)} items.")

    # 3. Layout Generation (Composition)
    print("\n[3] Generating Composition...")
    
    if use_ai_layout:
        print("[AI] Using Generative Layout Brain (Gemini)...")
        from engine.layout_brain import LayoutBrain
        from engine.layout_solver import LayoutSolver
        
        # 1. Ask the Brain
        brain = LayoutBrain(config)
        layout_tree = brain.generate_layout_strategy(inventory)
        print(f"[AI] Strategy Generated: {json.dumps(layout_tree, indent=2)}")
        
        # 2. Solve the Layout
        solver = LayoutSolver(width=config["content_area"]["w"], height=config["content_area"]["h"], margin=0) # Margin handled by content_area offset
        containers = solver.solve(layout_tree, inventory)
        
        # Offset to content area
        for c in containers:
            c["x"] += config["content_area"]["x"]
            c["y"] += config["content_area"]["y"]
            
        # Save this generated layout as a template for inspection
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        template_name = f"layout_ai_gen_{timestamp}"
        template_path = os.path.join("templates", f"{template_name}.json")
        
        try:
            os.makedirs("templates", exist_ok=True)
            with open(template_path, "w") as f:
                json.dump(containers, f, indent=2)
            print(f"[AI] Saved generated layout to: {template_path}")
        except Exception as e:
            print(f"[WARN] Failed to save layout template: {e}")
            
    else:
        # inventory keys are the roles (e.g. hero_left, accessory_small)
        containers = layout_generator.generate_dynamic_layout(config, inventory, preferred_template)
    
    # 4. Rendering
    print("\n[4] Rendering Storyboard...")
    
    # Inject temporary preset into config for the renderer to use
    preset_name = "smart_generated"
    config["presets"][preset_name] = sorted(containers, key=lambda c: c['id'])
    
    # Product mapping is just the inventory (role -> path)
    # The container IDs match the inventory keys
    # Product mapping is just the inventory (role -> path)
    # The container IDs match the inventory keys
    try:
        canvas = render_smart_storyboard(config, preset_name, inventory, customer_name)
        
        # Save
        os.makedirs("output", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"output/storyboard_smart_{timestamp}.png"
        canvas.save(output_path, dpi=(300, 300))
        
        print(f"\n[SUCCESS] Saved to: {output_path}")
        
    except Exception as e:
        print(f"\n[ERROR] Rendering failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
