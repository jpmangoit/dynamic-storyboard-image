from engine.pvil_analyzer import analyze_products
from engine.manual_merchandiser import merchandize_manual  # Bypassing Gemini
from engine.layout_physics import compute_layout
from engine.renderer import render
import os

def main():
    """
    Fixed 8-product storyboard generation pipeline.
    """
    try:
        print("Analyzing product visual intelligence...")
        pvil_data = analyze_products("products")
        
        if len(pvil_data) == 0:
            print("No products found in the 'products' directory.")
            return
        
        print(f"Analyzed {len(pvil_data)} products")
        
        print("Using manual layout (Gemini bypassed)...")
        ai_layout = merchandize_manual(pvil_data)
        print(f"Strategy: {ai_layout.get('strategy_name', 'N/A')}")
        
        print("Computing pixel-perfect layout...")
        placements = compute_layout(ai_layout)
        print(f"Computed {len(placements)} placements")
        
        print("Rendering print-ready storyboard...")
        output_path = render(placements, "products")
        
        print(f"Complete! Storyboard saved to: {output_path}")
        
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        print("Please check that the 'products' directory exists and contains PNG files")
    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        print("Please check your API key and product files")

if __name__ == "__main__":
    main()
