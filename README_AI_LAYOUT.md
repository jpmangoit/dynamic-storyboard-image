# AI Storyboard Generator & Layout Engine

This project now includes advanced AI capabilities for generating storyboard layouts.

## Features

### 1. Smart Inventory Scanning
The system automatically scans the `products/` directory and assigns roles to images based on:
- **Manifest Overrides**: `products/manifest.json` (Highest priority)
- **Filename Tags**: e.g., `bag_hero.png` -> `hero`
- **AI Classification**: Uses CLIP to detect object types (e.g., "tote bag" -> `hero`, "mug" -> `cluster`)
- **Aspect Ratio Heuristics**: Assigns roles based on shape (Tall -> Hero/Support, Square -> Accessory)

### 2. Generative Layouts (Google Gemini)
Uses a Large Language Model to design bespoke layouts based on the specific inventory.
- **Usage**: `python generate_smart.py "Project Name" --ai-layout`
- **How it works**:
    1. Analyzes inventory aspect ratios.
    2. Sends inventory list to Gemini.
    3. Gemini generates a "Layout Tree" (Splits, Grids, Slots).
    4. `LayoutSolver` calculates pixel-perfect coordinates.

### 3. Template Remixing
The system can programmatically generate thousands of layout variations from a few base templates.
- **Strategies**: Mirroring, Role Shuffling, Hybrid Mixing (Left Half of A + Right Half of B).
- **Generate Templates**: `python generate_templates.py`
    - Creates JSON files in `templates/`.
- **Usage**: `python generate_smart.py "Project Name"` (Auto-selects best fit)
- **Force Template**: `python generate_smart.py "Project Name" --template Remix_Mix_A_X_B`

## Command Line Usage

**Basic Auto-Mode** (Best Fit Template):
```bash
python generate_smart.py "Client Name"
```

**AI Generative Mode** (Unique Layouts):
```bash
python generate_smart.py "Client Name" --ai-layout
```

**Force Specific Template**:
```bash
python generate_smart.py "Client Name" --template Remix_Mirror_layout_A_classic
```

**Flexible Mode** (Allow loose role matching):
```bash
python generate_smart.py "Client Name" --flexible
```

## Configuration

- **Master Config**: `a3_storyboard_master.json` (Header/Footer styles)
- **Base Layouts**: `a3_storyboard_layout.json`
- **Manifest**: `products/manifest.json`

## Requirements

- Python 3.10+
- `google-genai` (for AI layout)
- `transformers`, `torch`, `Pillow` (for Smart Classify)
- `python-dotenv`
