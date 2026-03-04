"""Download 100 Handwritten Medical Records from HuggingFace."""
import json, os, urllib.request

API = ("https://datasets-server.huggingface.co/rows?"
       "dataset=chaithanyakota%2F100-handwritten-medical-records"
       "&config=default&split=train&offset=0&length=100")

OUT_DIR = os.path.join(os.path.dirname(__file__), "images")
GT_FILE = os.path.join(os.path.dirname(__file__), "ground_truth.json")

os.makedirs(OUT_DIR, exist_ok=True)

print("Fetching metadata...")
with urllib.request.urlopen(API) as resp:
    data = json.loads(resp.read())

ground_truth = []
for row_obj in data["rows"]:
    idx = row_obj["row_idx"]
    row = row_obj["row"]
    img_url = row["image"]["src"]
    medicines = row["medicines"]
    filename = f"record_{idx:03d}.jpg"

    print(f"  [{idx+1}/100] {filename} -> {medicines[:50]}...")
    filepath = os.path.join(OUT_DIR, filename)
    if not os.path.exists(filepath):
        urllib.request.urlretrieve(img_url, filepath)

    ground_truth.append({
        "filename": filename,
        "medicines": medicines,
    })

with open(GT_FILE, "w") as f:
    json.dump(ground_truth, f, indent=2)

print(f"\nDone! {len(ground_truth)} images saved to {OUT_DIR}")
print(f"Ground truth saved to {GT_FILE}")
