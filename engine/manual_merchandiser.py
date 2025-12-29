# engine/manual_merchandiser.py
"""
Manual merchandiser that bypasses Gemini AI.
Returns a hardcoded layout based on reference-1.png structure.
"""

def merchandize_manual(pvil_data):
    """
    Returns a hardcoded layout matching reference-1.png style.
    No AI calls - pure manual configuration.
    """
    
    # Create filename mapping from pvil_data
    products = {item['file']: item for item in pvil_data}
    
    # Hardcoded layout based on reference-1.png structure
    # This matches the dense, hierarchical layout style
    layout = {
        "strategy_name": "Manual Reference-1 Layout (Bypassing Gemini)",
        "template_name": "reference_1_match",
        "assignments": {}
    }
    
    # Map products to slots based on manifest roles
    # Priority order: hero -> large -> medium -> small -> tiny
    
    if "towel.png" in products:
        layout["assignments"]["hero_left"] = "towel.png"
    
    if "bag.png" in products:
        layout["assignments"]["anchor_right"] = "bag.png"
    
    if "frame.png" in products:
        layout["assignments"]["print_back"] = "frame.png"
    
    if "notebook.png" in products:
        layout["assignments"]["notebook"] = "notebook.png"
    
    if "greeting.png" in products:
        layout["assignments"]["card"] = "greeting.png"
    
    if "mug.png" in products:
        layout["assignments"]["mugs_cluster"] = "mug.png"
    
    if "magnet.png" in products:
        layout["assignments"]["magnet"] = "magnet.png"
    
    if "keyring.png" in products:
        layout["assignments"]["keyring"] = "keyring.png"
    
    print(f"Manual Layout: {len(layout['assignments'])} products assigned")
    return layout
