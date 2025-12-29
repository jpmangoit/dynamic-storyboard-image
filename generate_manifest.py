import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

def generate_manifest():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    # Get list of product files
    prod_dir = "products"
    if not os.path.exists(prod_dir):
        print("Product directory missing")
        return
        
    product_files = [f for f in os.listdir(prod_dir) if f.lower().endswith('.png')]
    print(f"Products: {product_files}")
    
    # Reference image
    ref_img = "reference.png"
    if not os.path.exists(ref_img):
        print("Reference image missing")
        return

    prompt = f"""
    You are setting up a configuration for a storyboard generator.
    
    Product List: {json.dumps(product_files)}
    
    Look at the Reference Image provided. It defines the style (e.g. one huge Hero, some medium items, some tiny fillers).
    
    Assign a Role to EACH product in the Product List to best match this style.
    Roles: "hero", "large", "medium", "small", "tiny".
    
    Rules:
    1. Pick exactly ONE "hero".
    2. Assign remaining items to roles that seem appropriate for their likely physical size (e.g. 'bag' is large, 'keyring' is tiny).
    
    Output JSON ONLY:
    {{
      "bag.png": "hero",
      "keyring.png": "tiny",
      ...
    }}
    """
    
    parts = [prompt]
    with open(ref_img, "rb") as f:
        parts.append(genai.types.Part.from_bytes(data=f.read(), mime_type="image/png"))
        
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=parts
    )
    
    print("\nGemini Suggestion:")
    print(response.text)
    
    # Save to file (naively parsing for now, assuming valid json from flash-latest)
    try:
        text = response.text.replace('```json', '').replace('```', '').strip()
        manifest = json.loads(text)
        with open(os.path.join(prod_dir, "manifest.json"), "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"Saved manifest to {os.path.join(prod_dir, 'manifest.json')}")
    except Exception as e:
        print(f"Failed to save manifest: {e}")

if __name__ == "__main__":
    generate_manifest()
