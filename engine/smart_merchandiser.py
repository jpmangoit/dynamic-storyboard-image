# engine/smart_merchandiser.py
def smart_merchandize(pvil_data):
    """
    Intelligent, deterministic merchandising that mimics professional POD proposals.
    Always produces clean: big hero left, grid on right.
    """
    # Sort by our improved layout_priority + area
    sorted_products = sorted(pvil_data, key=lambda x: (x["layout_priority"], -x["area"]))

    placements = []
    roles = [
        ("hero", "xl"),
        ("right_anchor", "large"),      # Top right
        ("center_focus", "large"),      # Middle right
        ("flow", "medium"),             # Flow item
        ("flow", "medium"),
        ("filler", "small"),
        ("filler", "small"),
        ("accent", "xs")
    ]

    for i, product in enumerate(sorted_products):
        role, size = roles[i] if i < len(roles) else ("accent", "xs")
        reason = (
            "Top-ranked by visual impact score" if i == 0
            else f"Rank {i+1} in visual hierarchy: {product['aspect']} {product['size_category']} {product['complexity']}"
        )

        placements.append({
            "file": product["file"],
            "visual_role": role,
            "relative_size": size,
            "reason": reason
        })

    return {
        "overall_strategy": "Classic POD proposal: large hero on left, clean supporting grid on right. "
                           "Hero chosen by visual impact (size, aspect, simplicity). Smaller items as accents.",
        "hero_choice": f"{sorted_products[0]['file']} selected as hero: best balance of size, aspect, and clean composition.",
        "placements": placements
    }
