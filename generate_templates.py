import sys
import os

# Ensure we can import from engine
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.layout_designer import LayoutDesigner

def main():
    print("=" * 60)
    print("AI Layout Template Generator")
    print("=" * 60)
    
    # Initialize Designer
    designer = LayoutDesigner(config_file="a3_storyboard_master.json", templates_dir="templates")
    
    # Generate Templates
    print("\n[1] Generative Process Started...")
    designer.generate_remixes(output_dir="templates")
    
    print("\n[SUCCESS] Generation Complete.")
    print("You can now use these templates with generate_smart.py")
    print("Example: python generate_smart.py --template Remix_Mix_A_X_B")

if __name__ == "__main__":
    main()
