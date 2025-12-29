import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def compare_images():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    ref_img = "reference-1.png"
    gen_img = "output/storyboard_A3_20251225_164332.png"
    
    print(f"Comparing {ref_img} vs {gen_img}...")
    
    parts = ["""
    Compare these two storyboard layouts.
    Image 1: Reference (Target Style)
    Image 2: Generated Output (Current Status)
    
    Critique the Generated Output based on the Reference:
    1. Does it match the "Hierarchical" composition?
    2. Are the overlaps similar in style?
    3. Is the spacing/density correct?
    4. What acts as the Hero in the output? Is it distinct layout-wise?
    5. Give a score (1-10) on how well the output mimics the reference style.
    """]
    
    with open(ref_img, "rb") as f:
        parts.append(genai.types.Part.from_bytes(data=f.read(), mime_type="image/png"))
    with open(gen_img, "rb") as f:
        parts.append(genai.types.Part.from_bytes(data=f.read(), mime_type="image/png"))
        
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=parts
    )
    
    print("\nCOMPARISON RESULTS:")
    print("="*60)
    print(response.text)
    print("="*60)

if __name__ == "__main__":
    compare_images()
