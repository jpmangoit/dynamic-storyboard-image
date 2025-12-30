import math

class LayoutSolver:
    def __init__(self, width=4961, height=3508, margin=177):
        self.width = width
        self.height = height
        self.margin = margin
        self.safe_area = {
            "x": margin,
            "y": margin,
            "w": width - (margin * 2),
            "h": height - (margin * 2)
        }

    def solve(self, layout_tree, inventory):
        """
        Executes the layout tree to generate container coordinates.
        Returns a list of container dicts ready for the renderer.
        """
        containers = []
        self._process_node(layout_tree, self.safe_area, inventory, containers)
        return containers

    def _process_node(self, node, area, inventory, containers):
        node_type = node.get("type", "slot")
        
        if node_type == "split":
            self._process_split(node, area, inventory, containers)
        elif node_type == "grid":
            self._process_grid(node, area, inventory, containers)
        elif node_type == "slot":
            self._process_slot(node, area, inventory, containers)
        elif node_type == "empty":
            pass # Explicit empty space

    def _process_split(self, node, area, inventory, containers):
        direction = node.get("direction", "horizontal")
        ratio = node.get("ratio", 0.5)
        gap = node.get("gap", 50)
        
        if direction == "horizontal":
            # Split width
            w1 = int((area["w"] - gap) * ratio)
            w2 = area["w"] - w1 - gap
            
            area1 = {"x": area["x"], "y": area["y"], "w": w1, "h": area["h"]}
            area2 = {"x": area["x"] + w1 + gap, "y": area["y"], "w": w2, "h": area["h"]}
        else:
            # Split height
            h1 = int((area["h"] - gap) * ratio)
            h2 = area["h"] - h1 - gap
            
            area1 = {"x": area["x"], "y": area["y"], "w": area["w"], "h": h1}
            area2 = {"x": area["x"], "y": area["y"] + h1 + gap, "w": area["w"], "h": h2}
            
        self._process_node(node.get("first"), area1, inventory, containers)
        self._process_node(node.get("second"), area2, inventory, containers)

    def _process_grid(self, node, area, inventory, containers):
        item_ids = node.get("items", [])
        if not item_ids: return

        cols = node.get("columns", 2)
        gap = node.get("gap", 50)
        rows = math.ceil(len(item_ids) / cols)
        
        cell_w = (area["w"] - (gap * (cols - 1))) / cols
        cell_h = (area["h"] - (gap * (rows - 1))) / rows
        
        for i, item_id in enumerate(item_ids):
            r = i // cols
            c = i % cols
            
            cx = area["x"] + c * (cell_w + gap)
            cy = area["y"] + r * (cell_h + gap)
            
            # Create a slot node for each grid item
            slot_node = {"type": "slot", "item_id": item_id}
            cell_area = {"x": int(cx), "y": int(cy), "w": int(cell_w), "h": int(cell_h)}
            
            self._process_slot(slot_node, cell_area, inventory, containers)

    def _process_slot(self, node, area, inventory, containers):
        item_id = node.get("item_id")
        
        # Basic validation
        if not item_id: return
        
        # Size validation and warnings
        min_recommended_size = 400
        if area["w"] < min_recommended_size or area["h"] < min_recommended_size:
            print(f"[!] [LAYOUT WARNING] Slot '{item_id}' is very small: {area['w']}x{area['h']}px (recommended min: {min_recommended_size}px)")
        
        # Check for hero products that are too small
        if "hero" in item_id.lower():
            min_hero_width = 1400  # ~30% of 4607px content area width
            if area["w"] < min_hero_width:
                print(f"[!] [CRITICAL] Hero product '{item_id}' width {area['w']}px is below minimum {min_hero_width}px (should be 30-40% of canvas)")
        
        # Create container
        container = {
            "id": item_id,
            "x": int(area["x"]),
            "y": int(area["y"]),
            "w": int(area["w"]),
            "h": int(area["h"]),
            "rotation_deg": node.get("rotation", 0)
        }
        containers.append(container)
