"""Quick test of TrOCR model loading and inference."""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

os.environ["HF_HOME"] = "./.hf_cache"

print("1. Importing transformers...")
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
print("   OK")

print("2. Loading processor...")
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
print("   OK")

print("3. Loading model...")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")
print("   OK")

print("4. Testing model.eval()...")
model.eval()
print("   OK")

print("5. Testing generate capability...")
print(f"   model has 'generate': {hasattr(model, 'generate')}")

# Try with a dummy image
from PIL import Image
import numpy as np
print("6. Creating test image...")
dummy_img = Image.fromarray(np.zeros((50, 200, 3), dtype=np.uint8) + 255)
print("   OK")

print("7. Running inference...")
import torch
pixel_values = processor(images=dummy_img, return_tensors="pt").pixel_values
with torch.no_grad():
    generated_ids = model.generate(pixel_values, max_new_tokens=128)
text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
print(f"   Result: '{text}'")
print("\nALL TESTS PASSED!")
