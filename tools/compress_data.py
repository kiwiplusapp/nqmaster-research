"""Compress every file > 40 MB of the project into <file>.xz (multi-threaded xz) and write tools/data_manifest.json.
The originals stay on disk but are git-ignored; restore_data.py rebuilds them from the .xz files (cloud or a new PC)."""
import os, sys, json, hashlib, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIMIT = 40e6
SKIP_DIRS = {".git", "__pycache__", "tmp"}
def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()
man_path = os.path.join(ROOT, "tools", "data_manifest.json")
old = json.load(open(man_path)) if os.path.exists(man_path) else {}
man = {}
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in files:
        p = os.path.join(root, f)
        if f.endswith(".xz") or os.path.getsize(p) <= LIMIT: continue
        rel = os.path.relpath(p, ROOT).replace("\\", "/"); size = os.path.getsize(p); h = sha256(p)
        man[rel] = dict(size=size, sha256=h)
        if old.get(rel, {}).get("sha256") == h and os.path.exists(p + ".xz"): print("ok  ", rel); continue
        subprocess.run(["xz", "-T0", "-6", "-k", "-f", p], check=True)
        print("xz  ", rel, round(size / 1e6), "MB ->", round(os.path.getsize(p + ".xz") / 1e6), "MB", flush=True)
json.dump(man, open(man_path, "w"), indent=1, sort_keys=True)
# git-ignore the originals
gi = os.path.join(ROOT, ".gitignore"); lines = open(gi, encoding="utf-8").read().splitlines() if os.path.exists(gi) else []
start = "# >>> big originals (restored by tools/restore_data.py)"; end = "# <<< big originals"
if start in lines: lines = lines[:lines.index(start)] + lines[lines.index(end) + 1:]
lines += [start] + ["/" + r for r in sorted(man)] + [end]
open(gi, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
print(len(man), "big files in the manifest")
