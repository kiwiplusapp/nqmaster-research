import re, sys
src = open(sys.argv[1], encoding='utf-8-sig').read()
# find string.Format( ... ) calls, parse args at top level
i = 0; n = 0; bad = 0
while True:
    k = src.find('string.Format(', i)
    if k < 0: break
    j = k + len('string.Format(')
    depth = 1; args = []; cur = ''; instr = False; esc = False; inchar = False
    while depth > 0 and j < len(src):
        c = src[j]
        if instr:
            cur += c
            if esc: esc = False
            elif c == '\\': esc = True
            elif c == '"': instr = False
        elif inchar:
            cur += c
            if esc: esc = False
            elif c == '\\': esc = True
            elif c == "'": inchar = False
        else:
            if c == '"': instr = True; cur += c
            elif c == "'": inchar = True; cur += c
            elif c in '([{': depth += 1; cur += c
            elif c in ')]}':
                depth -= 1
                if depth == 0: args.append(cur); break
                cur += c
            elif c == ',' and depth == 1: args.append(cur); cur = ''
            else: cur += c
        j += 1
    line = src.count('\n', 0, k) + 1
    a0 = args[0].strip()
    off = 0
    if a0.startswith('CultureInfo'): a0 = args[1].strip(); off = 1
    # concat string literals
    lits = re.findall(r'"((?:[^"\\]|\\.)*)"', a0)
    fmt = ''.join(lits)
    idx = [int(m) for m in re.findall(r'(?<!\{)\{(\d+)', fmt.replace('{{','').replace('}}',''))]
    nargs = len(args) - 1 - off
    mx = max(idx) + 1 if idx else 0
    n += 1
    if mx > nargs or not lits:
        bad += 1
        print(f"line {line}: placeholders need {mx}, args {nargs}: {fmt[:90]!r}")
    i = j
print("calls", n, "suspicious", bad)
