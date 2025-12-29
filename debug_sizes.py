
import json
import os
import sys
sys.path.append(os.getcwd())

from engine import templates

# Mock Inventory matches User's case
inventory = {
  "towel_hero.png": "hero",
  "bag_large.png": "support_large",
  "frame_medium.png": "support_medium_large",
  "greeting_medium.png": "support_medium_large",
  "notebook_medium.png": "support_medium_large",
  "magnet_small.png": "accessory_small",
  "mug_small.png": "accessory_small",
  "keyring_tiny.png": "accessory_tiny"
}

config = {} # dummy
fake_aspects = {} # assume square for calculation

print("--- DEBUGGING LAYOUT SIZES ---")

# 1. Get Options
options = templates.get_valid_templates(config, inventory, fake_aspects)

# 2. Extract the Grid Layout (Hero Right)
selected = next((o for o in options if "hero_right" in o['name']), None)

if not selected:
    print("Layout not found!")
    exit()

print(f"Selected: {selected['name']}")

for c in selected['containers']:
    role = ""
    if "large" in c['id']: role = "LARGE"
    elif "medium" in c['id']: role = "MEDIUM"
    elif "small" in c['id']: role = "SMALL"
    elif "tiny" in c['id']: role = "TINY"
    elif "hero" in c['id']: role = "HERO"
    
    print(f"Item: {c['id']:<20} | Role: {role:<8} | Size: {c['w']} x {c['h']}")
