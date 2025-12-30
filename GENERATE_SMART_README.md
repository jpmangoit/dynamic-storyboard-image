# generate_smart.py - Complete Dependency Documentation

## Overview
This document lists all file dependencies, package requirements, and commands needed to run `generate_smart.py`.

---

## 1. File Dependencies

### Core Script
- **`generate_smart.py`** - Main entry point

### Direct Dependencies (Imported Files)
1. **`generate_from_json.py`**
   - Function used: `load_config()`
   - Loads configuration from `a3_storyboard_master.json` and templates

2. **`engine/smart_classify.py`**
   - Functions used: `load_ai()`, `scan_directory()`
   - Handles AI-based product classification using CLIP model

3. **`engine/layout_generator.py`**
   - Function used: `generate_dynamic_layout()`
   - Generates layout configurations based on inventory

4. **`engine/smart_renderer.py`**
   - Function used: `render_smart_storyboard()`
   - Renders the final storyboard with shadows and effects

### Conditional Dependencies (When using `--ai-layout` flag)
5. **`engine/layout_brain.py`**
   - Class used: `LayoutBrain`
   - Uses Google Gemini AI to generate layout strategies

6. **`engine/layout_solver.py`**
   - Class used: `LayoutSolver`
   - Solves layout geometry from AI-generated strategies

7. **`engine/layout_validator.py`**
   - Class used: `LayoutValidator`
   - Validates layout configurations

### Indirect Dependencies (Required by above files)
8. **`engine/templates.py`**
   - Imported by: `layout_generator.py`
   - Function used: `get_valid_templates()`
   - Loads and manages layout templates

9. **`engine/__init__.py`**
   - Package initialization file for the `engine` module

### Configuration & Data Files
10. **`a3_storyboard_master.json`** (Required)
    - Main configuration file containing:
      - Canvas dimensions and DPI
      - Header/Footer configuration
      - Size classes for products
      - Preset layouts

11. **`templates/*.json`** (Required for `--template` flag)
    - Layout template files, e.g.:
      - `layout_C_classic.json`
      - `layout_A_classic.json`, etc.
    - Contains container positions and dimensions

12. **`.env`** (Required for `--ai-layout` flag)
    - Contains `GEMINI_API_KEY` for Google Generative AI

13. **`products/` directory** (Required)
    - Must contain product images (PNG/JPG format)
    - Example files: `towel.png`, `bag.png`, `mug.png`, etc.

14. **`assets/` directory** (Optional)
    - Contains header and footer images:
      - `header.png`
      - `footer_brush.png`
      - `cornflower_logo.png`

---

## 2. Python Package Dependencies

### Required Packages (Core Functionality)

```text
# Image Processing
Pillow>=10.0.0           # PIL for image manipulation

# AI Classification (for product recognition)
transformers>=4.30.0     # Hugging Face transformers for CLIP model
torch>=2.0.0             # PyTorch (CLIP model backend)
```

### Required Packages (When using `--ai-layout` flag)

```text
# Google Generative AI
google-genai>=0.2.0      # Google Generative AI SDK (Gemini)
python-dotenv>=1.0.0     # For loading .env file
```

### Standard Library (Built-in)
- `os` - File system operations
- `sys` - System-specific parameters
- `json` - JSON parsing
- `datetime` - Timestamp generation
- `argparse` - Command-line argument parsing
- `importlib.util` - Module loading utilities
- `math` - Mathematical operations
- `random` - Random selections

---

## 3. Installation Commands

### Step 1: Install Core Dependencies
```powershell
# Install Python packages
pip install Pillow transformers torch
```

### Step 2: Install AI Layout Dependencies (Optional)
```powershell
# Only needed if using --ai-layout flag
pip install google-genai python-dotenv
```

### Step 3: Create .env File (For AI Layout)
```powershell
# Create .env file with your Gemini API key
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

### Complete Installation (All Features)
```powershell
# Install all dependencies at once
pip install Pillow transformers torch google-genai python-dotenv
```

---

## 4. Usage Commands

### Basic Command (Using Template)
```powershell
# Syntax
python generate_smart.py "<customer_name>" --template <template_name>

# Example: Using Legacy Layout C Classic template
python generate_smart.py "ProjectName" --template Legacy_layout_C_classic

# Example: Using Layout A template
python generate_smart.py "Durham University" --template layout_A_classic
```

### Available Options
```powershell
# Show help
python generate_smart.py --help

# Basic usage (default customer name)
python generate_smart.py

# With custom customer name
python generate_smart.py "My Company Name"

# With specific template
python generate_smart.py "My Company" --template layout_B_classic

# With flexible product placement
python generate_smart.py "My Company" --flexible

# With AI-generated layout (requires Gemini API)
python generate_smart.py "My Company" --ai-layout

# Combined options
python generate_smart.py "My Company" --template layout_C_classic --flexible
```

### Command Arguments Explained

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `customer_name` | Positional | No | Customer/project name (default: "Generative Client") |
| `--template` | Option | No | Force specific layout template (e.g., "Legacy_layout_C_classic") |
| `--flexible` | Flag | No | Allow flexible/random placement within categories |
| `--ai-layout` | Flag | No | Use Gemini AI to design layout dynamically |

---

## 5. Directory Structure Required

```
AI-storyboard-gemini-layout/
├── generate_smart.py           # Main script
├── generate_from_json.py       # Config loader
├── a3_storyboard_master.json   # Main configuration
├── .env                        # API keys (for --ai-layout)
├── engine/
│   ├── __init__.py
│   ├── smart_classify.py       # AI product classification
│   ├── layout_generator.py     # Layout generation
│   ├── smart_renderer.py       # Rendering with effects
│   ├── templates.py            # Template management
│   ├── layout_brain.py         # AI layout generation (optional)
│   ├── layout_solver.py        # Layout geometry solver (optional)
│   └── layout_validator.py     # Layout validation (optional)
├── templates/
│   ├── layout_A_classic.json
│   ├── layout_B_classic.json
│   ├── layout_C_classic.json
│   └── ...
├── products/
│   ├── towel.png
│   ├── bag.png
│   ├── mug.png
│   └── ...
├── assets/                     # Optional
│   ├── header.png
│   ├── footer_brush.png
│   └── cornflower_logo.png
└── output/                     # Created automatically
    └── storyboard_*.png        # Generated outputs
```

---

## 6. Common Issues & Solutions

### Issue 1: AI modules not available
**Error**: `[ERROR] AI modules not available. Cannot proceed with smart generation.`

**Solution**:
```powershell
pip install transformers torch
```

### Issue 2: Template not found
**Error**: `Preferred template 'Legacy_layout_C_classic' not found`

**Solution**:
- Check that `templates/layout_C_classic.json` exists
- Template name should be: `Legacy_layout_C_classic` (with "Legacy_" prefix)
- List available templates: check files in `templates/` directory

### Issue 3: No products found
**Error**: `[ERROR] No products found.`

**Solution**:
- Ensure `products/` directory exists
- Add product images (PNG/JPG) to `products/` directory
- Supported filenames: towel.png, bag.png, mug.png, etc.

### Issue 4: Gemini API error (when using --ai-layout)
**Error**: Authentication or API errors

**Solution**:
```powershell
# Create/update .env file
echo "GEMINI_API_KEY=your_actual_api_key" > .env

# Install required package
pip install google-genai python-dotenv
```

---

## 7. Output Files

### Generated Files
- **Location**: `output/` directory (created automatically)
- **Filename Format**: `storyboard_smart_YYYYMMDD_HHMMSS.png`
- **Resolution**: 4961×3508 pixels @ 300 DPI (A3 size)

### Template Files (When using --ai-layout)
- **Location**: `templates/` directory
- **Filename Format**: `layout_ai_gen_YYYYMMDD_HHMMSS.json`
- **Purpose**: Reusable layout template for future use

---

## 8. Example Workflows

### Workflow 1: Quick Generation with Template
```powershell
# 1. Ensure products exist
dir products\

# 2. Run with template
python generate_smart.py "Durham University" --template Legacy_layout_C_classic

# 3. Check output
dir output\
```

### Workflow 2: AI-Powered Generation
```powershell
# 1. Set up API key
echo "GEMINI_API_KEY=your_key" > .env

# 2. Install AI dependencies
pip install google-genai python-dotenv

# 3. Generate with AI
python generate_smart.py "My Company" --ai-layout

# 4. Reuse generated template
python generate_smart.py "Another Client" --template layout_ai_gen_20251230_133844
```

### Workflow 3: Debugging Product Sizes
```powershell
# Enable verbose output and check sizing
python generate_smart.py "Test" --template Legacy_layout_C_classic

# Compare with generate_collage.py
python generate_collage.py classic_collage.json
```

---

## 9. Performance Notes

- **First run**: Slower due to CLIP model download (~1GB)
- **Subsequent runs**: Faster as model is cached
- **AI Layout mode**: Requires API calls (1-3 seconds per layout)
- **Recommended**: Keep products under 5000×5000 pixels for best performance

---

## 10. Related Scripts

For comparison and alternative workflows:

- **`generate_collage.py`** - Original renderer (correct product sizes)
- **`generate_from_json.py`** - JSON-based generator
- **`compare_output.py`** - Compare outputs from different scripts
- **`debug_sizes.py`** - Debug product sizing issues
