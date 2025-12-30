"""
Layout Validator - Validates AI-generated layout trees for quality and compliance
"""

class LayoutValidator:
    def __init__(self, canvas_width=4961, canvas_height=3508):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        
        # Define size constraints based on config size_classes
        self.size_constraints = {
            "hero": {"min_width_pct": 30, "min_width_px": 1400},
            "support_large": {"min_width_pct": 15, "min_width_px": 700},
            "support_medium": {"min_width_pct": 10, "min_width_px": 500},
            "accessory": {"min_width_pct": 5, "min_width_px": 250},
            "default": {"min_width_pct": 8, "min_width_px": 400}
        }
        
        self.min_slot_size = 400  # Minimum pixel size for any slot
        
    def validate_layout_tree(self, layout_tree, inventory):
        """
        Validates a layout tree structure before execution.
        Returns (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        # 1. Check all products are included
        all_slots = self._extract_all_slots(layout_tree)
        missing_products = set(inventory.keys()) - set(all_slots)
        extra_products = set(all_slots) - set(inventory.keys())
        
        if missing_products:
            errors.append(f"Missing products in layout: {missing_products}")
        
        if extra_products:
            errors.append(f"Unknown products in layout: {extra_products}")
            
        # 2. Validate slot counts
        if len(all_slots) != len(inventory):
            errors.append(f"Product count mismatch: layout has {len(all_slots)} slots, inventory has {len(inventory)} items")
        
        # 3. Calculate actual slot percentages through nested splits
        slot_percentages = self._calculate_slot_percentages(layout_tree, 1.0, 1.0)
        
        # 4. Validate each hero product gets minimum 30% width
        for item_id in inventory.keys():
            if "hero" in item_id.lower() and item_id in slot_percentages:
                width_pct = slot_percentages[item_id]["width_pct"] * 100
                if width_pct < 30:
                    errors.append(
                        f"Hero product '{item_id}' only gets {width_pct:.1f}% canvas width (minimum 30% required). "
                        f"Nested splits are reducing hero size too much!"
                    )
        
        # 3. Validate hero products are in dedicated slots (not grids)
        hero_violations = self._check_hero_slots(layout_tree, inventory)
        if hero_violations:
            errors.extend(hero_violations)
        
        is_valid = len(errors) == 0
        return is_valid, errors, warnings
    
    def validate_containers(self, containers, inventory):
        """
        Validates rendered container sizes after layout solving.
        Returns (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        # Create mapping of container sizes
        for container in containers:
            item_id = container["id"]
            width = container["w"]
            height = container["h"]
            
            # Determine size constraint based on role
            constraint = self._get_size_constraint(item_id)
            min_width_px = constraint["min_width_px"]
            
            # Check minimum size
            if width < self.min_slot_size or height < self.min_slot_size:
                warnings.append(f"Product '{item_id}' is very small: {width}x{height}px (min recommended: {self.min_slot_size}px)")
            
            # Check role-specific constraints
            if width < min_width_px:
                role = item_id.split('_')[0] if '_' in item_id else "product"
                errors.append(f"Product '{item_id}' ({role}) width {width}px is below minimum {min_width_px}px")
        
        # Check for missing products
        container_ids = {c["id"] for c in containers}
        missing = set(inventory.keys()) - container_ids
        if missing:
            errors.append(f"Missing products in containers: {missing}")
        
        is_valid = len(errors) == 0
        return is_valid, errors, warnings
    
    def _extract_all_slots(self, node):
        """Recursively extract all slot item_ids from layout tree"""
        if not node:
            return []
            
        node_type = node.get("type", "slot")
        
        if node_type == "slot":
            return [node.get("item_id")]
        elif node_type == "split":
            first_slots = self._extract_all_slots(node.get("first"))
            second_slots = self._extract_all_slots(node.get("second"))
            return first_slots + second_slots
        elif node_type == "grid":
            return node.get("items", [])
        elif node_type == "empty":
            return []
        
        return []
    
    def _check_hero_slots(self, node, inventory):
        """Check that hero products are in dedicated slots, not grids"""
        errors = []
        
        # Find all hero products
        hero_items = [k for k in inventory.keys() if "hero" in k.lower()]
        
        if not hero_items:
            return errors
        
        # Check if any hero is in a grid
        grids = self._extract_all_grids(node)
        for grid_items in grids:
            for hero in hero_items:
                if hero in grid_items:
                    errors.append(f"Hero product '{hero}' is in a grid! Heroes must have dedicated 'slot' nodes.")
        
        return errors
    
    def _extract_all_grids(self, node):
        """Recursively extract all grid item lists"""
        if not node:
            return []
            
        node_type = node.get("type", "slot")
        grids = []
        
        if node_type == "grid":
            grids.append(node.get("items", []))
        elif node_type == "split":
            grids.extend(self._extract_all_grids(node.get("first")))
            grids.extend(self._extract_all_grids(node.get("second")))
        
        return grids
    
    def _calculate_slot_percentages(self, node, width_pct, height_pct):
        """
        Recursively calculate what percentage of canvas each slot actually receives.
        Returns dict: {item_id: {"width_pct": float, "height_pct": float}}
        """
        if not node:
            return {}
        
        node_type = node.get("type", "slot")
        percentages = {}
        
        if node_type == "slot":
            item_id = node.get("item_id")
            if item_id:
                percentages[item_id] = {
                    "width_pct": width_pct,
                    "height_pct": height_pct
                }
        
        elif node_type == "split":
            direction = node.get("direction", "horizontal")
            ratio = node.get("ratio", 0.5)
            gap_pct = node.get("gap", 50) / self.canvas_width  # Approximate gap as percentage
            
            if direction == "horizontal":
                # Split reduces width for each child
                first_width = width_pct * ratio - (gap_pct / 2)
                second_width = width_pct * (1 - ratio) - (gap_pct / 2)
                
                first_percentages = self._calculate_slot_percentages(
                    node.get("first"), first_width, height_pct
                )
                second_percentages = self._calculate_slot_percentages(
                    node.get("second"), second_width, height_pct
                )
            else:  # vertical
                # Split reduces height for each child
                first_height = height_pct * ratio - (gap_pct / 2)
                second_height = height_pct * (1 - ratio) - (gap_pct / 2)
                
                first_percentages = self._calculate_slot_percentages(
                    node.get("first"), width_pct, first_height
                )
                second_percentages = self._calculate_slot_percentages(
                    node.get("second"), width_pct, second_height
                )
            
            percentages.update(first_percentages)
            percentages.update(second_percentages)
        
        elif node_type == "grid":
            items = node.get("items", [])
            columns = node.get("columns", 2)
            if items:
                rows = (len(items) + columns - 1) // columns
                cell_width = width_pct / columns
                cell_height = height_pct / rows
                
                for item_id in items:
                    percentages[item_id] = {
                        "width_pct": cell_width,
                        "height_pct": cell_height
                    }
        
        return percentages
    
    def _get_size_constraint(self, item_id):
        """Get size constraint based on item role"""
        item_lower = item_id.lower()
        
        if "hero" in item_lower:
            return self.size_constraints["hero"]
        elif "support" in item_lower:
            if "large" in item_lower:
                return self.size_constraints["support_large"]
            else:
                return self.size_constraints["support_medium"]
        elif "accessory" in item_lower:
            return self.size_constraints["accessory"]
        else:
            return self.size_constraints["default"]
