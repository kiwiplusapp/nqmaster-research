#!/usr/bin/env bash
# Type-check a NinjaScript file against a minimal NinjaTrader 8 API stub with the C# 5 compiler rules (mono mcs).
# Usage: bash tools/nt8_stub/check.sh NQMaster.cs   (or GoldMaster.cs). Prints nothing and exits 0 when it type-checks.
# This is NOT a real NinjaTrader compile: the real check is F5 in the NinjaScript Editor on the Windows PC.
set -e
here="$(cd "$(dirname "$0")" && pwd)"
src="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
out="$(mktemp -d)"
if mcs -langversion:5 -target:library -out:"$out/x.dll" "$here/NT8ApiStub.cs" "$src" > "$out/log" 2>&1; then rm -rf "$out"; exit 0; fi
grep -o "error CS[0-9]*: .*" "$out/log" | sort | uniq -c | sort -rn; rm -rf "$out"; exit 1
