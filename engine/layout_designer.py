import json
import os
import copy
import random
import glob
from datetime import datetime

class LayoutDesigner:
    def __init__(self, config_file="a3_storyboard_master.json", templates_dir="templates"):
        self.config_file = config_file
        self.templates_dir = templates_dir
        self.canvas_width = 4961
        self.canvas_height = 3508
        self._load_config()
        self.base_layouts = self._load_layouts()

    def _load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                self.canvas_width = data.get("canvas", {}).get("width_px", 4961)
                self.canvas_height = data.get("canvas", {}).get("height_px", 3508)

    def _load_layouts(self):
        presets = {}
        if not os.path.exists(self.templates_dir):
            print(f"[WARN] Templates directory not found: {self.templates_dir}")
            return presets
        
        files = glob.glob(os.path.join(self.templates_dir, "*.json"))
        for file in files:
            # Skip remix files to avoid remixing-remixes (optional, but safer for base generation)
            if "Remix_" in os.path.basename(file):
                continue
                
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    if "presets" in data:
                        presets.update(data["presets"])
                    elif "containers" in data:
                        name = os.path.basename(file).replace(".json", "")
                        presets[name] = data
            except Exception as e:
                print(f"[WARN] Failed to load {file}: {e}")
                
        return presets

    def generate_remixes(self, output_dir="templates"):
        """Generates new layouts by remixing existing ones."""
        os.makedirs(output_dir, exist_ok=True)
        
        generated_count = 0
        layout_names = list(self.base_layouts.keys())
        print(f"[DESIGNER] Analyzed {len(layout_names)} base layouts.")

        for name in layout_names:
            preset = self.base_layouts[name]
            containers = preset.get("containers", [])
            
            # Strategy 1: Horizontal Flip (Mirror)
            mirrored = self._create_mirror_variant(containers)
            self._save_template(output_dir, f"Remix_Mirror_{name}", mirrored, f"Mirrored version of {name}")
            generated_count += 1
            
            # Strategy 2: Role Swapping (Shuffle)
            shuffled = self._create_shuffle_variant(containers)
            if shuffled:
                self._save_template(output_dir, f"Remix_Shuffle_{name}", shuffled, f"Shuffled role positions of {name}")
                generated_count += 1
        
        # Strategy 3: Zone Mixing (Left of A + Right of B)
        # We try to combine every pair of layouts
        for name_a in layout_names:
            for name_b in layout_names:
                if name_a == name_b: continue
                
                mixed = self._create_mix_variant(self.base_layouts[name_a]["containers"], 
                                               self.base_layouts[name_b]["containers"])
                
                if mixed:
                    mix_name = f"Remix_Mix_{name_a}_X_{name_b}"
                    # Shorten name if needed
                    mix_name = mix_name.replace("layout_", "").replace("_classic", "")
                    self._save_template(output_dir, mix_name, mixed, f"Hybrid of {name_a} (Left) and {name_b} (Right)")
                    generated_count += 1

        print(f"[DESIGNER] Generated {generated_count} new templates in '{output_dir}/'.")

    def _create_mix_variant(self, containers_a, containers_b):
        """Combines Left Half of A with Right Half of B."""
        center_x = self.canvas_width / 2
        
        # Extract Left items from A
        left_items = []
        for c in containers_a:
            cx = (c.get("canvas_x") or c.get("x")) + (c.get("width_px") or c.get("w")) / 2
            if cx < center_x:
                left_items.append(copy.deepcopy(c))
                
        # Extract Right items from B
        right_items = []
        for c in containers_b:
            cx = (c.get("canvas_x") or c.get("x")) + (c.get("width_px") or c.get("w")) / 2
            if cx >= center_x:
                right_items.append(copy.deepcopy(c))
                
        # Collision Detection
        # If any item from Left overlaps with any item from Right, reject this mix
        if self._check_collisions(left_items, right_items):
            return None
            
        # Heuristic: Minimum Density
        # If the result is too sparse (e.g. < 5 items), it probably lost too much content.
        total_items = len(left_items) + len(right_items)
        if total_items < 5:
            return None
            
        # Heuristic: Balance
        # Ensure neither side is completely empty if the total is high
        if len(left_items) == 0 or len(right_items) == 0:
            return None
            
        # Combine
        return left_items + right_items

    def _check_collisions(self, group_a, group_b):
        """Returns True if any item in A overlaps with any item in B."""
        margin = 50 # Minimum gap required
        
        for a in group_a:
            ax = a.get("canvas_x") or a.get("x")
            ay = a.get("canvas_y") or a.get("y")
            aw = a.get("width_px") or a.get("w")
            ah = a.get("height_px") or a.get("h")
            
            for b in group_b:
                bx = b.get("canvas_x") or b.get("x")
                by = b.get("canvas_y") or b.get("y")
                bw = b.get("width_px") or b.get("w")
                bh = b.get("height_px") or b.get("h")
                
                # AABB Collision Logic
                if (ax < bx + bw + margin and
                    ax + aw + margin > bx and
                    ay < by + bh + margin and
                    ay + ah + margin > by):
                    return True
                    
        return False

    def _create_mirror_variant(self, containers):
        new_containers = copy.deepcopy(containers)
        for c in new_containers:
            # Flip X coordinate
            # New X = Width - Old X - Width of Item
            # (Because X is top-left corner)
            old_x = c.get("canvas_x") or c.get("x")
            w = c.get("width_px") or c.get("w")
            
            new_x = self.canvas_width - old_x - w
            
            # Update keys (handle both legacy and new formats)
            if "canvas_x" in c: c["canvas_x"] = new_x
            if "x" in c: c["x"] = new_x
            
            # Flip Rotation if present
            rot = c.get("rotation_deg", 0)
            if rot != 0:
                c["rotation_deg"] = -rot
                
        return new_containers

    def _create_shuffle_variant(self, containers):
        """Swaps slots of the same role/size."""
        new_containers = copy.deepcopy(containers)
        
        # Group by role
        groups = {}
        for i, c in enumerate(new_containers):
            role = c.get("role", "unknown")
            if role not in groups: groups[role] = []
            groups[role].append(i)
            
        # Check if any swapping is possible
        swapped = False
        for role, indices in groups.items():
            if len(indices) > 1:
                # We have multiple items of this role (e.g. 2 Heroes, 2 Accessories)
                # Shuffle their POSITIONS (x, y, w, h, rotation) but keep their IDs?
                # No, we want to swap the physical slots.
                
                # Let's extract the spatial properties
                props = []
                for idx in indices:
                    c = new_containers[idx]
                    p = {
                        "x": c.get("canvas_x") or c.get("x"),
                        "y": c.get("canvas_y") or c.get("y"),
                        "w": c.get("width_px") or c.get("w"),
                        "h": c.get("height_px") or c.get("h"),
                        "rot": c.get("rotation_deg", 0)
                    }
                    props.append(p)
                
                # Shuffle the properties list
                random.shuffle(props)
                
                # Apply back to the containers
                for i, idx in enumerate(indices):
                    c = new_containers[idx]
                    p = props[i]
                    
                    if "canvas_x" in c: c["canvas_x"] = p["x"]
                    if "x" in c: c["x"] = p["x"]
                    
                    if "canvas_y" in c: c["canvas_y"] = p["y"]
                    if "y" in c: c["y"] = p["y"]
                    
                    if "width_px" in c: c["width_px"] = p["w"]
                    if "w" in c: c["w"] = p["w"]
                    
                    if "height_px" in c: c["height_px"] = p["h"]
                    if "h" in c: c["h"] = p["h"]
                    
                    if "rotation_deg" in c: c["rotation_deg"] = p["rot"]
                    
                swapped = True
                
        return new_containers if swapped else None

    def _save_template(self, folder, name, containers, description):
        filename = os.path.join(folder, f"{name}.json")
        data = {
            "presets": {
                name: {
                    "description": description,
                    "containers": containers
                }
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
