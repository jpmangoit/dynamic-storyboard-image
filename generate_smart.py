import os
import sys
from datetime import datetime
import importlib.util

# Utilities to load modules without modifying them
import smart_classify
import layout_generator

import os
import sys
from datetime import datetime
import importlib.util

# Utilities to load modules without modifying them
import smart_classify
import layout_generator

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
    
    args = parser.parse_args()
    
    customer_name = args.customer_name
    preferred_template = args.template
    
    # 1. Configuration
    print("\n[1] Loading Configuration...")
    config = load_config()
    
    # 2. Smart Inventory Scan
    print("\n[2] AI Inventory Scan (products/)...")
    if not smart_classify.AI_AVAILABLE:
        print("   [ERROR] AI modules not available. Cannot proceed with smart generation.")
        return

    model, processor = smart_classify.load_ai()
    inventory = smart_classify.scan_directory("products", model, processor)
    
    if not inventory:
        print("   [ERROR] No products found.")
        return
        
    print(f"   > Found {len(inventory)} items.")

    # 3. Layout Generation (Composition)
    print("\n[3] Generating Composition...")
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
