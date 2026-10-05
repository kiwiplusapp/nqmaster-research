"""Rebuild the big data files (price history, trade sets) from their .xz copies in the repo.
Run once after cloning:  python tools/restore_data.py   (add --check to only verify)."""
import os, sys, json, lzma, hashlib, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
man = json.load(open(os.path.join(ROOT, "tools", "data_manifest.json")))
check_only = "--check" in sys.argv
def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()
bad = 0
for rel, m in sorted(man.items()):
    p = os.path.join(ROOT, rel)
    if os.path.exists(p) and os.path.getsize(p) == m["size"] and sha256(p) == m["sha256"]: print("ok      ", rel); continue
    if check_only: print("MISSING ", rel); bad += 1; continue
    src = p + ".xz"
    if not os.path.exists(src): print("NO .xz  ", rel); bad += 1; continue
    tmp = p + ".part"
    with lzma.open(src, "rb") as fi, open(tmp, "wb") as fo: shutil.copyfileobj(fi, fo, 1 << 22)
    if sha256(tmp) != m["sha256"]: os.remove(tmp); print("BAD HASH", rel); bad += 1; continue
    os.replace(tmp, p); print("restored", rel, round(m["size"] / 1e6), "MB", flush=True)
print("done," if not bad else f"{bad} problem(s),", len(man), "files in the manifest")
sys.exit(1 if bad else 0)
