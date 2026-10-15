"""Static import-guard scanner for research/ (no code is executed).

Many research scripts do their heavy work at module level. When another script imports them, that work silently re-runs and can
overwrite shared files (2026-10-06: importing dense_build.py / ict_redo.py wiped keys in research/tmp/dense/*.npz).

This tool lists every .py under research/ (recursive) that
  (a) is imported by at least one other script in research/: `import X` / `from X import ...` (any nesting level, incl. inside
      functions) where X is a module in the importer's own directory or in research/ (same directory wins); and
  (b) has unsafe top-level statements: anything other than imports, def/class, docstrings, `if __name__ == "__main__":`
      (also `if __name__ == "__main__" and ...:`), sys.path manipulation, simple constant / config assignments (literals,
      names, arithmetic, os.path.*, os.environ.get, pure builtins), harmless config calls (pd.set_option,
      warnings.filterwarnings, matplotlib.use, os.makedirs, ...), and if / try / for / while blocks made only of those.
      Top-level calls of anything else (pickle.dump, np.savez, run(...), print, data loads) and `with` blocks are unsafe.
A top-level statement can be accepted explicitly with a `# guard-ok: <reason>` comment on one of its lines or on the line right
above it, or by putting it between `# guard-ok-begin: <reason>` and `# guard-ok-end` lines. Use this only for READ-ONLY work that
importers rely on (data loads, derived tables, numba compiles); never for anything that writes files. Accepted statements are
listed as "accepted" and do not fail the check.

Calls count as harmless when they are builtins / os.path / numpy constructors, pure methods (str/dict/list building), or calls of
functions (in the module itself or imported from another research module) whose bodies contain only such calls. Loops (for /
while) and if / try blocks made only of harmless statements are treated as constant building. Unsafe statements that write files
(to_csv, pickle/json dump, np.save*, open(..., "w"), ...; directly or through any function they call, also across modules and
class methods) are marked with W and the file gets status WRITES.

The text-prefix pattern `exec(open("X.py").read().split(MARK)[0])` (the importer runs the first part of X.py) is listed in a
separate table: the scanner checks that MARK still occurs in X and that the prefix still parses (a broken split fails the
check) and says whether the prefix writes files (that is the importer's intended work, so it does not fail the check).

Usage: python3 tools/check_guards.py [--all] [--root research]
  --all  also list unsafe files nobody imports (informational; they never fail the check).
Exit code 1 if any imported module has unsafe (non-accepted) top-level statements or an exec-split is broken, else 0."""
import argparse, ast, os, sys
from collections import defaultdict

SAFE_CALLS = {
    # builtins without side effects
    "range", "len", "list", "tuple", "dict", "set", "frozenset", "sorted", "int", "float", "str", "bool", "zip", "enumerate",
    "min", "max", "abs", "round", "sum", "map", "filter", "reversed", "isinstance", "getattr", "hasattr", "slice", "bytes",
    "chr", "ord", "any", "all", "repr", "type", "object", "complex", "divmod", "pow", "hash", "id", "iter", "vars",
    # stdlib constructors / pure helpers
    "namedtuple", "defaultdict", "OrderedDict", "Counter", "partial", "Path", "compile",
    "re.compile", "collections.namedtuple", "collections.defaultdict", "collections.OrderedDict", "collections.Counter",
    "functools.partial", "pathlib.Path", "dataclasses.field", "field", "TypeVar", "typing.TypeVar",
    "os.environ.get", "os.getenv", "os.cpu_count", "os.getcwd", "os.sep.join", "os.pathsep.join",
    "datetime.date", "datetime.datetime", "datetime.time", "datetime.timedelta", "dt.date", "dt.datetime", "dt.time",
    "dt.timedelta", "date", "time", "timedelta", "datetime", "math.sqrt", "math.log", "math.exp", "math.ceil", "math.floor",
    "pd.Timestamp", "pd.Timedelta", "pd.to_datetime", "pd.DateOffset", "np.dtype",
    # numba decorators (compile lazily) and numba types
    "njit", "jit", "numba.njit", "numba.jit", "nb.njit", "nb.jit", "prange", "numba.prange", "nb.prange",
}
SAFE_PREFIXES = ("os.path.", "np.", "numpy.", "math.", "string.", "nb.types.", "numba.types.", "types.")
# np.* is allowed only for these cheap constructors / ufuncs (not np.load / np.save*)
NP_BAD = {"load", "save", "savez", "savez_compressed", "savetxt", "loadtxt", "genfromtxt", "fromfile", "memmap", "tofile"}
SAFE_EXPR_CALLS = {  # call statements allowed at top level (configuration only)
    "sys.path.insert", "sys.path.append", "sys.path.extend", "sys.setrecursionlimit", "pd.set_option", "pd.options.display",
    "np.set_printoptions", "np.seterr", "warnings.filterwarnings", "warnings.simplefilter", "matplotlib.use", "mpl.use",
    "os.makedirs", "os.environ.setdefault", "plt.switch_backend", "numba.config", "logging.basicConfig",
}


PURE_METHODS = {  # method calls that only build / read in-memory values
    "get", "items", "keys", "values", "copy", "split", "rsplit", "replace", "startswith", "endswith", "format", "strip",
    "lstrip", "rstrip", "lower", "upper", "title", "join", "zfill", "partition", "rpartition", "encode", "decode", "count",
    "index", "find", "append", "extend", "add", "update", "setdefault", "insert", "union", "intersection", "difference",
    "issubset", "issuperset", "astype", "tolist", "reshape", "ravel", "flatten", "strftime", "isoformat", "isdigit",
    "isalpha", "fromkeys", "sort", "discard", "weekday", "isoweekday", "toordinal",
}
SAFE_MODULE_PREFIXES = ("itertools.", "functools.", "operator.", "string.")
WRITE_ATTRS = {  # calls that create / change files
    "to_csv", "to_pickle", "to_parquet", "to_json", "to_excel", "to_feather", "to_hdf", "to_html", "dump", "savez",
    "savez_compressed", "save", "savetxt", "savefig", "write", "writelines", "write_text", "write_bytes", "tofile", "remove",
    "unlink", "rmtree", "rename", "copyfile", "copy2", "copytree", "move", "urlretrieve",
}


def is_write_call(call):
    f = call.func
    if isinstance(f, ast.Attribute) and f.attr in WRITE_ATTRS:
        return not (f.attr == "copy" or (f.attr == "replace" and dotted(f) != "os.replace"))
    if isinstance(f, ast.Name) and f.id == "open":   # open(path, mode) with a writing mode
        mode = call.args[1] if len(call.args) > 1 else next((k.value for k in call.keywords if k.arg == "mode"), None)
        return isinstance(mode, ast.Constant) and isinstance(mode.value, str) and any(c in mode.value for c in "wax+")
    return dotted(f) in ("os.replace", "shutil.copy", "shutil.move", "os.system", "subprocess.run", "subprocess.call")


def dotted(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr); node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id); return ".".join(reversed(parts))
    return None


class Scope:
    """purity of the module's own functions / lambdas (fixpoint over their bodies)"""
    def __init__(self, tree, extern=frozenset(), extern_w=frozenset()):
        self.extern = extern                 # pure functions imported from other research modules (dotted local names)
        self.extern_w = extern_w             # functions imported from other research modules that write files
        self.funcs = {}
        for s in tree.body:
            if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)): self.funcs[s.name] = s
            elif isinstance(s, ast.Assign) and isinstance(s.value, ast.Lambda):
                for t in s.targets:
                    if isinstance(t, ast.Name): self.funcs[t.id] = s.value
        self.pure = set(self.funcs)          # optimistic start, remove impure ones until stable
        changed = True
        while changed:
            changed = False
            for n in list(self.pure):
                f = self.funcs[n]
                body = f.body if isinstance(f.body, list) else [f.body]
                nodes = [x for b in body for x in ast.walk(b)]
                if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    nodes += [x for d in f.decorator_list for x in ast.walk(d)]
                bad = any(isinstance(x, (ast.With, ast.AsyncWith)) for x in nodes) or \
                    any(isinstance(x, ast.Call) and not self.call_pure(x) for x in nodes)
                if bad: self.pure.discard(n); changed = True
        self.writes = set(); changed = True   # own functions / classes that write files (directly or through other writers)
        units = dict(self.funcs)
        units.update({s.name: s for s in tree.body if isinstance(s, ast.ClassDef)})
        while changed:
            changed = False
            for n, f in units.items():
                if n in self.writes: continue
                body = f.body if isinstance(f.body, list) else [f.body]
                if any(isinstance(x, ast.Call) and self.call_writes(x) for b in body for x in ast.walk(b)):
                    self.writes.add(n); changed = True

    def call_writes(self, call):
        name = dotted(call.func)
        return is_write_call(call) or (name is not None and (name in self.writes or name in self.extern_w))

    def stmt_writes(self, s):
        return any(isinstance(x, ast.Call) and self.call_writes(x) for x in ast.walk(s))

    def call_pure(self, call):
        name = dotted(call.func)
        if isinstance(call.func, ast.Attribute) and call.func.attr in PURE_METHODS: return True
        if name is None: return isinstance(call.func, ast.Lambda)
        if name in SAFE_CALLS or name in self.pure or name in self.extern or name.startswith(SAFE_MODULE_PREFIXES): return True
        if name.startswith(SAFE_PREFIXES):
            last = name.split(".")[-1]
            return not (name.startswith(("np.", "numpy.")) and (last in NP_BAD or (".random." in name and last != "default_rng")))
        return False

    def expr_ok(self, e):
        return e is None or all(self.call_pure(c) for c in ast.walk(e) if isinstance(c, ast.Call))

    def stmt_ok(self, s):
        ok = self.expr_ok
        if isinstance(s, (ast.Import, ast.ImportFrom, ast.Pass, ast.Global, ast.Nonlocal, ast.Delete, ast.Break, ast.Continue)):
            return True
        if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = s.args
            return all(ok(d) for d in list(a.defaults) + [d for d in a.kw_defaults if d is not None] + s.decorator_list)
        if isinstance(s, ast.ClassDef):
            return all(ok(d) for d in s.decorator_list + s.bases) and all(self.stmt_ok(b) for b in s.body)
        if isinstance(s, ast.Expr):
            if isinstance(s.value, ast.Constant): return True                  # docstring / bare literal
            if isinstance(s.value, ast.Call):
                name = dotted(s.value.func) or ""
                cfg = name in SAFE_EXPR_CALLS or any(name.startswith(p + ".") for p in SAFE_EXPR_CALLS)
                return (cfg or self.call_pure(s.value)) and all(ok(x) for x in s.value.args + [k.value for k in s.value.keywords])
            return ok(s.value)
        if isinstance(s, ast.Assign): return ok(s.value) and all(ok(t) for t in s.targets)
        if isinstance(s, (ast.AnnAssign, ast.AugAssign)): return ok(s.value)
        if isinstance(s, ast.Assert): return ok(s.test) and ok(s.msg)
        if isinstance(s, ast.If):
            if is_main_guard(s.test): return True
            return ok(s.test) and all(self.stmt_ok(b) for b in s.body + s.orelse)
        if isinstance(s, ast.Try):
            hs = [b for h in s.handlers for b in h.body]
            return all(self.stmt_ok(b) for b in s.body + hs + s.orelse + s.finalbody)
        if isinstance(s, (ast.For, ast.While)):   # a loop that only builds in-memory constants (pure calls only) is config
            return ok(s.iter if isinstance(s, ast.For) else s.test) and all(self.stmt_ok(b) for b in s.body + s.orelse)
        return False                   # while / with / raise / match / anything else


def is_main_guard(test):
    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.And):     # `__name__ == "__main__" and ...`
        return any(is_main_guard(v) for v in test.values)
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq): return False
    sides = [test.left, test.comparators[0]]
    return any(isinstance(x, ast.Name) and x.id == "__name__" for x in sides) and \
        any(isinstance(x, ast.Constant) and x.value == "__main__" for x in sides)


def unsafe_lines(tree, lines, extern=frozenset(), extern_w=frozenset()):
    """-> (unsafe, accepted, writing): top-level line numbers (writing = unsafe statements that write files)"""
    sc = Scope(tree, extern, extern_w); bad, acc, wr = [], [], set()
    block, inside = set(), False          # lines between '# guard-ok-begin: <reason>' and '# guard-ok-end'
    for i, l in enumerate(lines, 1):
        t = l.strip()
        if t.startswith("# guard-ok-begin"): inside = True
        elif t.startswith("# guard-ok-end"): inside = False
        elif inside: block.add(i)
    for s in tree.body:
        if sc.stmt_ok(s): continue
        first = s.lineno; end = getattr(s, "end_lineno", None) or first
        if sc.stmt_writes(s): wr.add(first)
        # a guard-ok comment may sit on any line of the statement or on the line right above it
        span = lines[max(first - 2, 0):end]
        tgt = acc if (first in block or any("guard-ok:" in l and "guard-ok-" not in l for l in span)) else bad
        if first not in tgt: tgt.append(first)
    return bad, acc, wr


def exec_targets(tree):
    """exec(open("X.py").read()...) -> [(X.py, split marker or None, lineno)]"""
    out = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "exec" and n.args): continue
        mark, path = None, None
        for m in ast.walk(n.args[0]):
            if isinstance(m, ast.Call) and isinstance(m.func, ast.Name) and m.func.id == "open" and m.args \
                    and isinstance(m.args[0], ast.Constant) and str(m.args[0].value).endswith(".py"):
                path = m.args[0].value
            if isinstance(m, ast.Call) and isinstance(m.func, ast.Attribute) and m.func.attr == "split" and m.args \
                    and isinstance(m.args[0], ast.Constant) and mark is None:
                mark = m.args[0].value
        if path: out.append((path, mark, n.lineno))
    return out


def imported_names(tree):
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names: out.add(a.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            out.add(n.module.split(".")[0])
    return out


def import_bindings(tree, resolve):
    """[(local dotted prefix or name, target path, imported name or None)] for imports of research modules"""
    out = []
    for n in tree.body:
        if isinstance(n, ast.Import):
            for a in n.names:
                p = resolve(a.name.split(".")[0])
                if p and "." not in a.name: out.append((a.asname or a.name, p, None))
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level and "." not in n.module:
            p = resolve(n.module)
            if p:
                for a in n.names: out.append((a.asname or a.name, p, a.name))
    return out


def pure_externs(trees, mods, root):
    """fixpoint: names each module imports that are pure functions of another research module"""
    bind = {}
    for f, t in trees.items():
        d = os.path.dirname(f)
        bind[f] = import_bindings(t, lambda x, d=d: mods[d].get(x) or mods[root].get(x))
    ext = {f: frozenset() for f in trees}; extw = {f: frozenset() for f in trees}
    for _ in range(12):
        sc = {f: Scope(t, ext[f], extw[f]) for f, t in trees.items()}
        pure = {f: sc[f].pure | {e for e in ext[f] if "." not in e} for f in trees}
        wr = {f: sc[f].writes | {e for e in extw[f] if "." not in e} for f in trees}
        new, neww = {}, {}
        for f in trees:
            e, w = set(), set()
            for local, p, name in bind[f]:
                if p not in pure: continue
                if name is None:
                    e |= {local + "." + q for q in pure[p]}; w |= {local + "." + q for q in wr[p]}
                else:
                    if name in pure[p]: e.add(local)
                    if name in wr[p]: w.add(local)
            new[f] = frozenset(e); neww[f] = frozenset(w)
        if new == ext and neww == extw: break
        ext, extw = new, neww
    return ext, extw


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research"))
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    files = []
    for d, ds, fs in os.walk(root):
        ds[:] = sorted(x for x in ds if x != "__pycache__" and not x.startswith("."))
        files += [os.path.join(d, f) for f in sorted(fs) if f.endswith(".py")]
    mods = defaultdict(dict)                       # dir -> {module name: path}
    for f in files: mods[os.path.dirname(f)][os.path.basename(f)[:-3]] = f
    trees, srcs, errors = {}, {}, []
    for f in files:
        try:
            srcs[f] = open(f, encoding="utf-8-sig", errors="replace").read(); trees[f] = ast.parse(srcs[f], f)
        except SyntaxError as e:
            errors.append(f"SYNTAX {os.path.relpath(f, root)}: {e}")
    importers = defaultdict(set); execers = defaultdict(set); exec_rows = []
    for f, t in trees.items():
        d = os.path.dirname(f)
        for x in imported_names(t):
            tgt = mods[d].get(x) or mods[root].get(x)
            if tgt and tgt != f: importers[tgt].add(f)
        for p, mark, ln in exec_targets(t):
            tgt = os.path.normpath(os.path.join(d, p))
            if tgt not in srcs:
                errors.append(f"EXEC  {os.path.relpath(f, root)}:{ln} runs missing file {p}"); continue
            execers[tgt].add(f); state = "whole file" if mark is None else "ok"
            if mark is not None:
                if mark not in srcs[tgt]:
                    state = "MARKER MISSING"
                    errors.append(f"EXEC  {os.path.relpath(f, root)}:{ln} split marker {mark!r} not found in {p}")
                else:
                    try:
                        pt = ast.parse(srcs[tgt].split(mark)[0])
                        if Scope(pt).writes or any(Scope(pt).stmt_writes(x) for x in pt.body): state = "ok, prefix WRITES files"
                    except SyntaxError as e:
                        state = "PREFIX BROKEN"
                        errors.append(f"EXEC  {os.path.relpath(f, root)}:{ln} prefix of {p} no longer parses: {e}")
            exec_rows.append((os.path.relpath(tgt, root), f"{os.path.relpath(f, root)}:{ln}", repr(mark), state))
    ext, extw = pure_externs(trees, mods, root)
    rows, fail = [], False
    for f in files:
        if f not in trees: continue
        imp = importers.get(f, set()); ex = execers.get(f, set())
        bad, acc, wr = unsafe_lines(trees[f], srcs[f].splitlines(), ext[f], extw[f])
        if imp and bad: fail = True
        if (imp and (bad or acc)) or (a.all and bad):
            rows.append((os.path.relpath(f, root), sorted(os.path.relpath(i, root) for i in imp),
                         sorted(os.path.relpath(i, root) for i in ex), bad, acc, wr))
    w = max([len(r[0]) for r in rows] + [4])
    print(f"{'file':<{w}}  {'status':<8}  {'unsafe top-level lines':<28}  importers")
    print(f"{'-' * w}  {'-' * 8}  {'-' * 28}  {'-' * 9}")
    for fn, imp, ex, bad, acc, wr in sorted(rows, key=lambda r: (not (r[1] and r[3]), not (set(r[3]) & r[5]), r[0])):
        st = ("WRITES" if set(bad) & wr else "UNSAFE") if imp and bad else ("unused" if not imp else "ok")
        ln = ",".join(f"{x}W" if x in wr else str(x) for x in bad) or "-"
        if acc: ln += f" (accepted: {','.join(map(str, acc))})"
        im = ", ".join(imp) or "-"
        if ex: im += f"  | exec-prefix by: {', '.join(ex)}"
        print(f"{fn:<{w}}  {st:<8}  {ln:<28}  {im}")
    n_imp = sum(1 for f in files if importers.get(f))
    n_bad = sum(1 for r in rows if r[1] and r[3])
    n_w = sum(1 for r in rows if r[1] and set(r[3]) & r[5])
    print(f"\n{len(files)} files scanned, {n_imp} imported by another script, {n_bad} imported AND unsafe "
          f"({n_w} of them write files at import). Lines: W = statement writes files (directly or via a function).")
    if exec_rows:
        print("\nexec-prefix dependencies (importer runs the text of the target up to the marker; keep the marker and the code above it"
              " unchanged, a prefix that writes files is intended work of that importer):")
        for t_, i_, m_, st_ in sorted(exec_rows): print(f"  {t_:<22} <- {i_:<26} marker {m_:<52} {st_}")
    for e in errors: print(e)
    if errors and any(e.startswith("EXEC") and "missing file" not in e for e in errors): fail = True
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
