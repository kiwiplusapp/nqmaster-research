"""Put the build code of dense_build.py and ict_redo.py under a __main__ guard: importing dense() / ictf() rebuilt the base grids
and wiped every key added later (U:ICTF, WR:*, C6:*, N:ENG0610, N:LATEFH)."""
for f, mark in (("dense_build.py", "meta = {}\n"), ("ict_redo.py", "rows = []\n")):
    s = open(f, encoding="utf-8").read()
    if "__main__" in s: print(f, "already guarded"); continue
    i = s.index(mark)
    body = "".join(("    " + l if l.strip() else l) for l in s[i:].splitlines(True))
    open(f, "w", encoding="utf-8").write(s[:i] + 'if __name__ == "__main__":      # build only when run directly (importing must not rebuild the grids)\n' + body)
    print(f, "guarded")
