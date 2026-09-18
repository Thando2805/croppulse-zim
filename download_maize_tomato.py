import os
from datasets import load_dataset
from tqdm import tqdm

print("Loading dataset from Hugging Face...")
# Use 'default' config instead of 'color'
dataset = load_dataset("mohanty/PlantVillage", "default", trust_remote_code=True)

split = "train" if "train" in dataset else list(dataset.keys())[0]
data = dataset[split]

os.makedirs("training_data", exist_ok=True)
print(f"Loaded {len(data)} items. Extracting Maize and Tomato images...")

saved_count = 0
for idx, sample in enumerate(tqdm(data, desc="Saving images")):
    text_val = sample.get("text", "")
    if not text_val:
        continue
    
    # Strip prefix to parse the exact class name
    class_name = str(text_val).replace("image of ", "").strip()
    
    # Filter strictly for Corn (Maize) and Tomato classes
    if "Corn" in class_name or "Tomato" in class_name:
        folder_name = class_name.replace(" ", "_").replace("/", "_")
        target_dir = os.path.join("training_data", folder_name)
        os.makedirs(target_dir, exist_ok=True)
        
        img = sample.get("image")
        if img is not None:
            if img.mode != "RGB":
                img = img.convert("RGB")
            
            img.save(os.path.join(target_dir, f"img_{idx}.jpg"))
            saved_count += 1

print(f"\nDone! Saved {saved_count} images to 'training_data/'.")