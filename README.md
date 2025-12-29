# AI Smart Storyboard Generator

## Overview
This project is an AI-driven tool that automatically generates professional product storyboards. It uses computer vision (CLIP) to identify products from a folder and an intelligent layout engine to arrange them into aesthetically pleasing compositions.

## Key Features
- **AI Classification**: Automatically detects product roles (e.g., "Hero" item vs "Accessory") using OpenAI's CLIP model.
- **Dynamic Layout Engine**: Uses a constraint solver to pick the perfect layout strategy based on the inventory count and types.
- **Hybrid Templates**: Supports both legacy fixed layouts (JSON) and flexible dynamic archetypes.
- **Smart Rendering**: Features auto-scaling, drop shadows, and Z-sorting for depth.

---

## 📦 Dependencies
Ensure you have the following Python packages installed (Python 3.9+ recommended):

```bash
pip install torch transformers pillow
```

*   `torch`: PyTorch backend for the AI model.
*   `transformers`: Hugging Face library for the CLIP model.
*   `pillow`: Advanced image processing (PIL) for rendering and composition.

---

## ⚙️ System Flow & Logic

The generation process (`generate_smart.py`) follows a strict 3-step pipeline:

### 1. The "Eyes": Inventory Scan
*   **Source**: `smart_classify.py`
*   **Logic**:
    1.  Scans the `products/` directory.
    2.  Loads the **CLIP (ViT-B/32)** model.
    3.  Classifies every image against a set of labels (`"tea towel"`, `"mug"`, `"frame"`, etc.).
    4.  **Heuristics**: If AI is unsure, it uses **Aspect Ratio** to decide (e.g., a very tall rectangle is likely a Towel/Hero, a square is a Magnet).
    5.  **Output**: A clean JSON inventory (e.g., `{"hero_left": "path/towel.png", "accessory_small": "path/magnet.png"}`).
    *   *Note*: Handles duplicate items by appending indices (e.g., `accessory_small_2`).

### 2. The "Brain": Layout Selection
*   **Source**: `layout_generator.py` & `engine/templates.py`
*   **Logic**:
    1.  **Constraint Solver**: It looks at the inventory (e.g., "2 Heroes, 3 Accessories") and finding ALL compatible templates.
    2.  **Hybrid Library**:
        *   **Legacy Layouts**: Fixed JSON layouts loaded from `a3_storyboard_layout.json` (perfect for exact replicas). Rejects these if your inventory has *more* heroes than the layout supports.
        *   **Dynamic Archetypes**: Flexible Python functions (e.g., `layout_quadrant_split`) that mathematically arrange items based on safe area percentiles.
    3.  **Random Shuffle**: It randomly selects one valid strategy from the list to ensure variety.

### 3. The "Hands": Rendering
*   **Source**: `engine/smart_renderer.py`
*   **Logic**:
    1.  **Canvas Setup**: Creates a 300DPI canvas based on configuration.
    2.  **Smart Fit**: Resizes product images to fit their assigned "Container Slots" using `contain` logic (aspect ratio preserved).
    3.  **Visual Polish**:
        *   **Drop Shadows**: Generates soft blurred shadows for depth.
        *   **Z-Sorting**: Ensures small accessories render *on top* of large background supports.
        *   *(Rotation is currently disabled per user config)*.

---

## 🚀 How to Run

1.  Place your product images in the `products/` folder.
2.  **Basic Run** (AI decides everything):
    ```bash
    python generate_smart.py "Client Name"
    ```
3.  **Advanced Run** (Force a specific template):
    ```bash
    python generate_smart.py "Client Name" --template layout_A_classic
    ```

## 🎮 Manual Control
**Overriding AI Roles (`manifest.json`)**
If you want to force a specific product to be a "hero" or "tiny", create a `manifest.json` file in your `products/` folder:

```json
{
  "my_bag.png": "hero",
  "small_magnet.png": "tiny",
  "big_print.png": "large"
}
```
*Supported roles: `hero`, `large`, `medium`, `small`, `tiny`, `support`, `cluster`.*

## 🛠 Extensibility & Structure
**Adding New Templates (No Code Required):**
*   All layouts are now stored as individual JSON files in the `templates/` directory (e.g., `templates/layout_A_classic.json`).
*   To add a new one, simply drop a `.json` file with your coordinates into that folder. The system will automatically detect and use it.
