# probe の逐語 — F241 裏取りの測定に使ったものすべて

本書は測定に使った script と argv の逐語である。**repo に実装面を増やさないため、
これらは `.py` / `.sh` として repo へ入れず、本書へ逐語で貼る。**
実物は wave の job dir (repo 外) にあった。

各 file の SHA-256 を併記する。本書から再実行することを運用契約にはしない。

## 投入 argv

```
cd /work/1/SFC/tanab/dev-wave-jobs/dev-wave-f241-perf-attribution
for i in 1 .. 24; do qsub -o "sched/job$i.o" -e "sched/job$i.e" perf_pairing_probe.sh; done
```

request は `975569`〜`975576` (第 1 波 8 本)、`975584`〜`975591` (第 2 波 8 本)、
`975612`〜`975619` (第 3 波 8 本)。うち `975613` だけが scheduler 出力・probe 出力とも
戻らなかった。

ログインノードの 1 標本は同じ probe を直接実行した。

```
python3 perf_pairing_probe.py --output runs/login-pegasus0X/probe.json
```

集計は次で行い、`measurements/pairing-rows.json` を得た。

```
python3 summarize.py
```

## `/usr/bin/perf` の該当部分 (2026-09-04 に login node で読了)

振り分けの全体は「完全一致する版があれば exec、無ければ warning を出して exit 2」である。
fallback は無い。

```bash
#!/bin/bash
full_version=`uname -r`

# First check for a fully qualified version.
this="/usr/lib/linux-tools/$full_version/`basename $0`"
if [ -f "$this" ]; then
	exec "$this" "$@"
fi
```

同 script の末尾は次で終わる。

```bash
		echo "WARNING: `basename $0` not found for kernel $version" >&2
```

(中略。導入すべき package 名の案内が数行続く)

```bash
exit 2
```

## probe 本体 `perf_pairing_probe.py`

SHA-256 = `337e287af9292d89bfb0ffb2f5c9b73034a6ae69f297223c17f1ff1aa27ecdbf`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F241 裏取り: 同じ計算ノード・同じ run で literal `perf` と絶対 path を対で測る。

出力は JSON 1 file。判定はしない (親が行う)。両側 control を同じ run に含める。
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import time

SCHEMA_VERSION = "izanagi-f241-perf-pairing/v1"
EVENTS = "cycles,instructions,LLC-loads,LLC-load-misses"
NEGATIVE_CONTROL = "/usr/lib/linux-tools/izanagi-f241-no-such-kernel/perf"
TRUNCATE = 4000


def _run(argv):
    started = time.time()
    try:
        proc = subprocess.run(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
            check=False,
        )
    except FileNotFoundError as exc:
        return {
            "argv": list(argv),
            "launched": False,
            "error": "FileNotFoundError: %s" % exc,
            "elapsed_s": round(time.time() - started, 4),
        }
    except PermissionError as exc:
        return {
            "argv": list(argv),
            "launched": False,
            "error": "PermissionError: %s" % exc,
            "elapsed_s": round(time.time() - started, 4),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": list(argv),
            "launched": True,
            "error": "TimeoutExpired: %s" % exc,
            "elapsed_s": round(time.time() - started, 4),
        }
    return {
        "argv": list(argv),
        "launched": True,
        "returncode": proc.returncode,
        "stdout": proc.stdout.decode("utf-8", "replace")[:TRUNCATE],
        "stderr": proc.stderr.decode("utf-8", "replace")[:TRUNCATE],
        "elapsed_s": round(time.time() - started, 4),
    }


_COUNT_RE = re.compile(
    r"^\s*(?P<value><[^>]+>|[0-9][0-9,\.]*)\s+(?P<event>[A-Za-z][A-Za-z0-9_\-\.:]*)"
)


def _parse_counters(text):
    """`perf stat` の出力から event -> 生の値文字列を拾う。判定はしない。"""
    found = {}
    for line in text.splitlines():
        match = _COUNT_RE.match(line)
        if match is None:
            continue
        event = match.group("event")
        value = match.group("value")
        if event in ("seconds", "msec"):
            continue
        found.setdefault(event, value)
    return found


def _numeric_events(counters):
    """実数値を返した event 名 (`<not supported>` 等を除く)。"""
    numeric = []
    for event, value in sorted(counters.items()):
        if value.startswith("<"):
            continue
        if re.fullmatch(r"[0-9][0-9,\.]*", value):
            numeric.append(event)
    return numeric


def _file_facts(path):
    facts = {"path": path}
    try:
        facts["exists"] = os.path.exists(path)
        facts["is_symlink"] = os.path.islink(path)
        facts["executable"] = os.access(path, os.X_OK)
        if facts["is_symlink"]:
            facts["symlink_target"] = os.readlink(path)
        if facts["exists"]:
            stat = os.stat(path)
            facts["size"] = stat.st_size
            facts["mode"] = oct(stat.st_mode)
            facts["realpath"] = os.path.realpath(path)
    except OSError as exc:
        facts["stat_error"] = str(exc)
    return facts


def _sha256(path):
    try:
        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except OSError as exc:
        return "unreadable: %s" % exc


def _read_text(path, limit=TRUNCATE):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read(limit)
    except OSError as exc:
        return "unreadable: %s" % exc


def _measure(label, command, launcher_kind):
    entry = {
        "label": label,
        "command": command,
        "launcher_kind": launcher_kind,
        "file_facts": _file_facts(command) if command.startswith("/") else None,
    }
    entry["version"] = _run([command, "--version"])
    stat = _run([command, "stat", "-e", EVENTS, "--", "/bin/true"])
    entry["stat"] = stat
    if stat.get("launched") and "stderr" in stat:
        counters = _parse_counters(stat["stderr"] + "\n" + stat.get("stdout", ""))
        entry["counters"] = counters
        entry["numeric_events"] = _numeric_events(counters)
        entry["counters_obtained"] = sorted(
            set(_numeric_events(counters)) & set(EVENTS.split(","))
        ) == sorted(EVENTS.split(","))
    else:
        entry["counters"] = {}
        entry["numeric_events"] = []
        entry["counters_obtained"] = False
    return entry


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    report = {
        "schema_version": SCHEMA_VERSION,
        "purpose": (
            "F241 の「計算ノードに perf が無い」という帰属を、同一 node・同一 run で "
            "literal `perf` と絶対 path の対比により裏取りする。"
        ),
        "events_requested": EVENTS.split(","),
        "site": {
            "hostname": socket.gethostname(),
            "uname_release": platform.uname().release,
            "PBS_JOBID": os.environ.get("PBS_JOBID", ""),
            "PBS_O_WORKDIR": os.environ.get("PBS_O_WORKDIR", ""),
            "observed_epoch": int(time.time()),
            "observed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "python": sys.executable,
            "PATH": os.environ.get("PATH", ""),
        },
    }

    paranoid_path = "/proc/sys/kernel/perf_event_paranoid"
    report["site"]["perf_event_paranoid"] = _read_text(paranoid_path, 64).strip()

    try:
        report["site"]["linux_tools_dir"] = sorted(os.listdir("/usr/lib/linux-tools"))
    except OSError as exc:
        report["site"]["linux_tools_dir"] = "unreadable: %s" % exc

    which_perf = shutil.which("perf")
    report["literal_perf_resolution"] = {
        "shutil_which": which_perf,
        "file_facts": _file_facts(which_perf) if which_perf else None,
        "sha256": _sha256(which_perf) if which_perf else None,
        "head": _read_text(which_perf, 400) if which_perf else None,
    }

    measurements = []
    # (1) literal — production が現に使っている呼び方。
    measurements.append(_measure("literal-perf", "perf", "PATH lookup"))
    # (2) 絶対 path — /usr/lib/linux-tools/<version>/perf の全件。
    absolute_candidates = sorted(glob.glob("/usr/lib/linux-tools/*/perf"))
    report["absolute_candidates"] = absolute_candidates
    for candidate in absolute_candidates:
        measurements.append(_measure("absolute:%s" % candidate, candidate, "absolute path"))
    report["measurements"] = measurements

    report["controls"] = {
        "note": (
            "同じ node・同じ run・同じ subprocess 実装で両側 control を取る。"
            "positive が失敗するなら測定機構自体が壊れており、"
            "negative が成功するなら不在の検出力が無い。"
        ),
        "positive_plain_binary": _run(["/bin/true"]),
        "negative_absent_perf": _run([NEGATIVE_CONTROL, "--version"]),
    }

    report["sample_scope"] = (
        "この結果は上記 hostname・observed_epoch・uname_release の 1 標本に限定され、"
        "gen_S の全 node や将来の allocation へ一般化しない。"
    )

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    print("wrote %s" % args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## job script `perf_pairing_probe.sh`

SHA-256 = `231394637357fcdf1babae271f1441e4b7b5ba92287d15556e2f58b29689771a`

```bash
#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=00:05:00
#PBS -b 1

# F241 裏取り probe。repo の外だけを読み書きし、repo の作業木には一切触れない。
set -u

JOB_ROOT=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-f241-perf-attribution
JOB_TAG=${PBS_JOBID//:/_}
OUT="$JOB_ROOT/runs/$JOB_TAG"

mkdir -p "$OUT" || exit 2

{
  printf 'hostname=%s\n' "$(hostname)"
  printf 'PBS_JOBID=%s\n' "${PBS_JOBID:-}"
  printf 'epoch=%s\n' "$(date +%s)"
  printf 'uname_r=%s\n' "$(uname -r)"
} > "$OUT/marker"

PY=""
for candidate in python3.12 python3.11 python3.10 python3; do
  resolved=$(command -v -- "$candidate" 2>/dev/null || true)
  [[ -n "$resolved" ]] || continue
  if "$resolved" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3,8) else 1)' \
      >/dev/null 2>&1; then
    PY="$resolved"
    break
  fi
done
if [[ -z "$PY" ]]; then
  printf 'no usable python3\n' > "$OUT/probe.err"
  exit 2
fi
printf '%s\n' "$PY" > "$OUT/interpreter"

"$PY" "$JOB_ROOT/perf_pairing_probe.py" --output "$OUT/probe.json" \
  > "$OUT/probe.log" 2>&1
PROBE_RC=$?

printf '%s\n' "$PROBE_RC" > "$OUT/probe.rc"
printf 'probe_rc=%s\n' "$PROBE_RC" > "$OUT/done-marker"
exit "$PROBE_RC"
```

## 集計 `summarize.py`

SHA-256 = `eacc406cd07d7b62b639764da93cb2ff91e3239247f31027ae4f5ed84ebcf72e`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe.json を集計して literal / 絶対 path の対を 1 行ずつ出す。判定はしない。"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
EVENTS = ["cycles", "instructions", "LLC-loads", "LLC-load-misses"]

rows = []
for path in sorted(glob.glob(os.path.join(ROOT, "runs", "*", "probe.json"))):
    doc = json.load(open(path, encoding="utf-8"))
    site = doc["site"]
    controls = doc["controls"]
    pos = controls["positive_plain_binary"].get("returncode")
    neg = controls["negative_absent_perf"]
    neg_ok = not neg.get("launched", False)
    for m in doc["measurements"]:
        ver = m["version"]
        stat = m["stat"]
        rows.append({
            "run": os.path.basename(os.path.dirname(path)),
            "host": site["hostname"],
            "kernel": site["uname_release"],
            "paranoid": site["perf_event_paranoid"],
            "jobid": site["PBS_JOBID"],
            "label": m["label"],
            "kind": m["launcher_kind"],
            "symlink": (m["file_facts"] or {}).get("is_symlink"),
            "version_rc": ver.get("returncode", ver.get("error")),
            "stat_rc": stat.get("returncode", stat.get("error")),
            "counters_obtained": m["counters_obtained"],
            "numeric": [e for e in m["numeric_events"] if e in EVENTS],
            "stderr_head": (stat.get("stderr", "") or "").strip().splitlines()[:1],
            "control_pos_rc": pos,
            "control_neg_unlaunched": neg_ok,
        })

print("run                     host       kernel            par kind          "
      "verRC statRC counters  first stderr line")
for r in rows:
    print("%-23s %-10s %-17s %-3s %-13s %-5s %-6s %-9s %s" % (
        r["run"][:23], r["host"], r["kernel"], r["paranoid"],
        ("literal" if r["kind"] == "PATH lookup" else
         os.path.basename(os.path.dirname(r["label"].split(":", 1)[-1]))),
        r["version_rc"], r["stat_rc"],
        ("%d/4" % len(r["numeric"])) if r["counters_obtained"] or r["numeric"] else "0/4",
        (r["stderr_head"][0][:70] if r["stderr_head"] else ""),
    ))

print()
print("controls: positive rc set = %s ; negative unlaunched set = %s" % (
    sorted({r["control_pos_rc"] for r in rows}),
    sorted({r["control_neg_unlaunched"] for r in rows}),
))
compute = [r for r in rows if r["host"].startswith("bnode")]
print("distinct compute nodes: %s" % sorted({r["host"] for r in compute}))
lit = [r for r in compute if r["kind"] == "PATH lookup"]
absl = [r for r in compute if r["kind"] == "absolute path"]
print("compute literal:  n=%d  rc set=%s  counters ok=%d" % (
    len(lit), sorted({str(r["stat_rc"]) for r in lit}),
    sum(1 for r in lit if r["counters_obtained"])))
print("compute absolute: n=%d  rc set=%s  counters ok=%d" % (
    len(absl), sorted({str(r["stat_rc"]) for r in absl}),
    sum(1 for r in absl if r["counters_obtained"])))
print("absolute symlink flags: %s" % sorted({str(r["symlink"]) for r in absl}))
json.dump(rows, open(os.path.join(ROOT, "pairing-rows.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2, sort_keys=True)
sys.stdout.write("wrote pairing-rows.json\n")
```
