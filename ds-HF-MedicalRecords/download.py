"""Download 100 Handwritten Medical Records from HuggingFace."""
import json, os, ssl, urllib.request

# Allow unverified SSL on Windows if certifi not available
ctx = ssl.create_default_context()
try:
    import certifi
    ctx.load_verify_locations(certifi.where())
except Exception:
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

API = ("https://datasets-server.huggingface.co/rows?"
       "dataset=chaithanyakota%2F100-handwritten-medical-records"
       "&config=default&split=train&offset=0&length=100")

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
GT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ground_truth.json")

os.makedirs(OUT_DIR, exist_ok=True)

print("Fetching metadata...")
req = urllib.request.Request(API, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, context=ctx) as resp:
    data = json.loads(resp.read())

ground_truth = []
failed = []
for row_obj in data["rows"]:
    idx = row_obj["row_idx"]
    row = row_obj["row"]
    img_url = row["image"]["src"]
    medicines = row["medicines"]
    filename = f"record_{idx:03d}.jpg"

    filepath = os.path.join(OUT_DIR, filename)
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        print(f"  [{idx+1}/100] {filename} (cached)")
    else:
        try:
            img_req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(img_req, context=ctx, timeout=30) as img_resp:
                with open(filepath, "wb") as f:
                    f.write(img_resp.read())
            print(f"  [{idx+1}/100] {filename} -> {medicines[:50]}...")
        except Exception as e:
            print(f"  [{idx+1}/100] FAILED: {e}")
            failed.append(filename)
            continue

    ground_truth.append({
        "filename": filename,
        "medicines": medicines,
    })

with open(GT_FILE, "w") as f:
    json.dump(ground_truth, f, indent=2)

print(f"\nDone! {len(ground_truth)} images saved, {len(failed)} failed")
print(f"Ground truth saved to {GT_FILE}")
