# probe / launcher の逐語 (T-2766)

集計 script と測定 launcher は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-ab/` に置き、repo には commit しない (D95、probe を repo へ入れない)。ここは逐語と sha256 の記録。

| file | bytes | sha256 |
|---|---|---|
| `probe/t2766_ab_analyze.py` | 45368 | `c5ac201f370ef705c797d0c08a898ddefc158f02e8aacf6921364ba6305b2bc5` |
| `run-measure.sh` | 7970 | `7e46d63211da0186c25b8cdacdd7049b412496021d0681c681e3325465950409` |
| `run-series.sh` | 1083 | `322770845931322898067c27f2a0c682dbb089740073197779aa032f56c9aef6` |
| `run-warm2.sh` | 1029 | `16fa4ce7a66c6acb1ff6d5c7b9330ce1138ee3b52b7e2147a1a3ec3aa5029d8e` |
| `run-mutation.sh` | 1251 | `68b6783bbcc99e6a62d72ab504041de9f002e121a5d65465b60574f4c2fa6b77` |

## probe/t2766_ab_analyze.py — 集計 script (Codex author、fix2 / fix3 後)

```python
#!/usr/bin/env python3
"""Offline T-2766 adjacent-pair analysis; Python 3.10, standard library only.
Launcher keeps unsubmitted aborts outside runs/, so no extra attempt filtering is needed.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime
import json
import math
from pathlib import Path
import re
from statistics import median
import tempfile
import xml.etree.ElementTree as ET


ENV = "IZANAGI_ACCEPTANCE_PAIRING_V1"
TOKEN = "t2766-min-cost-partners"
PREFIX = "izanagi_acceptance_pairing_v1_"
FIELDS = ("scope", "rank", "partner", "worker")
CLAIMS = ("item → 実行 worker と JUnit 出現順からの復元であり、"
          "初期配布の送信順ではない。全 worker の2個目が partner とは限らない。")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def number(value):
    require(not isinstance(value, bool), "boolean duration")
    result = float(value)
    require(math.isfinite(result) and result >= 0, "invalid duration")
    return result


def split_group(nodeid):
    if nodeid.rfind("@") > nodeid.rfind("]"):
        base, group = nodeid.rsplit("@", 1)
        return base, group
    return nodeid, None


def scope(nodeid):
    base, group = split_group(nodeid)
    return base if group is None else group


def junit_key(nodeid):
    """Forward projection avoids guessing where dotted module paths end."""
    head, bracket, parameter = nodeid.partition("[")
    parts = head.split("::")
    parts[0] = parts[0].replace("/", ".").removesuffix(".py")
    return ".".join(parts[:-1]), parts[-1] + bracket + parameter


def testcase_rows(root, selected):
    lookup = defaultdict(list)
    for nodeid in selected:
        lookup[junit_key(split_group(nodeid)[0])].append(nodeid)
    rows = []
    for case in root.iter("testcase"):
        name, group = split_group(case.attrib["name"])
        matches = lookup[(case.attrib["classname"], name)]
        require(len(matches) == 1, f"ambiguous/unmatched JUnit testcase: {case.attrib}")
        selected_nodeid = matches[0]
        base, selected_group = split_group(selected_nodeid)
        if selected_group is not None:
            require(group == selected_group, "selected/JUnit group mismatch")
        runtime = base if group is None else f"{base}@{group}"
        properties = [
            (p.attrib["name"][len(PREFIX):], p.attrib.get("value", ""))
            for p in case.findall("./properties/property")
            if p.attrib.get("name", "").startswith(PREFIX)
        ]
        require(len(dict(properties)) == len(properties), "duplicate pairing property")
        rows.append({
            "selected": selected_nodeid, "nodeid": runtime,
            "properties": dict(properties), "time": number(case.attrib["time"]),
        })
    require(Counter(row["selected"] for row in rows) == Counter(selected),
            "JUnit/selected coverage mismatch (including skips)")
    require(len(set(selected)) == len(selected), "duplicate selected nodeid")
    return rows


def independent_units(rows, report, ledger):
    groups = {entry["nodeid"]: entry.get("group")
              for entry in report.get("observed_universe", [])}
    units = {}
    for row in sorted(rows, key=lambda entry: entry["selected"]):
        nodeid = row["nodeid"]
        base, suffix = split_group(nodeid)
        unit = units.setdefault(scope(nodeid), {"items": [], "cost": 0.0, "known": True})
        unit["items"].append(row["selected"])
        value = ledger.get(base)
        # real-repo runtime suffixes are stripped, but its marker survives in
        # observed_universe; historical ledger entries may still use that marker.
        group = suffix if suffix is not None else groups.get(row["selected"])
        if value is None and group is not None:
            value = ledger.get(f"{base}@{group}")
        if value is None:
            unit["known"] = False
        else:
            unit["cost"] += value
            if not math.isfinite(unit["cost"]):
                unit["known"] = False
    known = sorted((u["cost"] for u in units.values() if u["known"]), reverse=True)
    require(bool(known), "no known unit costs")
    unknown = known[min(96, len(known)) - 1]
    for unit in units.values():
        if not unit["known"]:
            unit["cost"] = unknown
    ordered = sorted(units, key=lambda key: -units[key]["cost"])
    realized = sorted(ordered, key=lambda key: -len(units[key]["items"]))
    return units, realized, unknown


def cost_distribution(costs):
    return {"count": len(costs), "min": min(costs) if costs else None,
            "max": max(costs) if costs else None, "zero_count": costs.count(0)}


def costs_close(actual, expected):
    actual, expected = sorted(actual), sorted(expected)
    return len(actual) == len(expected) and all(
        math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)
        for a, b in zip(actual, expected)
    )


def witness(root, report, ledger, condition):
    rows = testcase_rows(root, report["selected"])
    coverage = sum(bool(row["properties"]) for row in rows)
    units, realized, unknown = independent_units(rows, report, ledger)
    candidate_costs = sorted(units[key]["cost"] for key in realized[48:])
    result = {
        "claims": CLAIMS, "property_testcases": coverage, "selected_count": len(rows),
        "unknown_cost": unknown, "candidate_cost_distribution": cost_distribution(candidate_costs),
        "partner_cost_distribution": cost_distribution(candidate_costs[:48]),
    }
    if condition == "A":
        require(coverage == 0, "A has pairing properties")
        result["valid"] = True
        return result
    require(coverage == len(rows), "B witness coverage is not 100%")
    require(len(units) >= 96, "B pairing was not applicable (<96 units)")
    unit_ranks = {}
    rank_units = {}
    workers = defaultdict(list)
    rank_partners, flag_partners = set(), set()
    unit_workers = defaultdict(set)
    for row in rows:
        props = row["properties"]
        require(set(props) == set(FIELDS), "B requires exactly four pairing properties")
        key = scope(row["nodeid"])
        require(props["scope"] == key, "scope property differs from runtime nodeid")
        rank = int(props["rank"])
        require(str(rank) == props["rank"] and 0 <= rank < len(units), "invalid rank")
        require(props["partner"] in {"0", "1"}, "invalid partner flag")
        require(bool(props["worker"]), "missing execution worker")
        require(unit_ranks.setdefault(key, rank) == rank, "unit has inconsistent ranks")
        require(rank_units.setdefault(rank, key) == key, "rank shared by different units")
        if 48 <= rank < 96:
            rank_partners.add(row["selected"])
        if props["partner"] == "1":
            flag_partners.add(row["selected"])
        workers[props["worker"]].append({
            "nodeid": row["nodeid"], "selected": row["selected"],
            "scope": key, "rank": rank, "partner": props["partner"] == "1",
            "time": row["time"],
        })
        unit_workers[key].add(props["worker"])
    require(set(rank_units) == set(range(len(units))), "ranks do not cover units")
    require(rank_partners == flag_partners, "rank 48..95 and partner item sets differ")
    require(all(len(ws) == 1 for ws in unit_workers.values()), "unit split between workers")
    actual_head = [key for rank, key in rank_units.items() if rank < 48]
    expected_head = realized[:48]
    sizes = {len(units[key]["items"]) for key in actual_head + expected_head}
    require(all(costs_close(
        [units[key]["cost"] for key in actual_head if len(units[key]["items"]) == size],
        [units[key]["cost"] for key in expected_head if len(units[key]["items"]) == size],
    ) for size in sizes), "head cardinality/cost multiset mismatch")
    actual_partner = [units[key]["cost"] for rank, key in rank_units.items()
                      if 48 <= rank < 96]
    require(costs_close(actual_partner, candidate_costs[:48]), "partner cost multiset mismatch")
    ranked_sizes = [len(units[rank_units[rank]]["items"]) for rank in range(len(units))]
    require(ranked_sizes == sorted(ranked_sizes, reverse=True), "cardinality-infeasible queue")
    occupancy = report["worker_occupancy"]
    require(set(workers) == set(occupancy), "witness/report workers differ")
    require(all(len(items) == occupancy[worker]["items"] for worker, items in workers.items()),
            "witness/report worker item counts differ")
    worker_units = {}
    measured = defaultdict(float)
    for worker, items in workers.items():
        sequence = []
        for item in items:
            key = item["scope"]
            measured[key] += item["time"]
            if not sequence or sequence[-1]["scope"] != key:
                sequence.append({"scope": key, "partner": item["partner"],
                                 "ledger_cost": units[key]["cost"], "measured_time": 0.0})
            sequence[-1]["measured_time"] += item["time"]
        worker_units[worker] = sequence

    def describe(key):
        worker = next(iter(unit_workers[key]))
        items, sequence = workers[worker], worker_units[worker]
        return {"scope": key, "ledger_cost": units[key]["cost"],
                "measured_time": measured[key], "worker": worker,
                "second_unit": sequence[1] if len(sequence) > 1 else None,
                "second_item_in_worker_sequence": items[1] if len(items) > 1 else None,
                "second_item_is_within_first_unit": (
                    len(items) > 1 and items[0]["scope"] == items[1]["scope"])}

    longest_cost = max(unit["cost"] for unit in units.values())
    longest_time = max(measured.values())
    result.update(valid=True, worker_item_sequences=dict(workers),
                  worker_unit_sequences=worker_units,
                  ledger_max_units=[describe(key) for key in realized
                                    if units[key]["cost"] == longest_cost],
                  measured_longest_units=[describe(key) for key in realized
                                          if measured[key] == longest_time],
                  checks={
                      "coverage": True, "rank_partner_sets": True,
                      "independent_cost_multisets": True, "worker_reconstruction": True,
                  })
    return result


def analyze_shard(path, ledger, condition):
    report = read_json(path / "report.json")
    root = ET.parse(path / "junit.xml").getroot()
    suites = list(root.iter("testsuite"))
    require(len(suites) == 1, "expected exactly one pytest testsuite")
    suite = suites[0]
    wall = number(suite.attrib["time"])
    failures = [{"tag": failure.tag, "attributes": dict(failure.attrib),
                 "text": failure.text or "", "testcase": dict(case.attrib)}
                for case in root.iter("testcase") for failure in case
                if failure.tag in {"failure", "error"}]
    occupancy = report["worker_occupancy"]
    require(bool(occupancy), "missing worker occupancy")
    durations = {worker: number(entry["duration_s"]) for worker, entry in occupancy.items()}
    busiest = max(durations, key=durations.get)
    receipt_path = path / "dispatch" / "receipt.json"
    result = {
        "W": wall, "O": durations[busiest], "F": wall - durations[busiest],
        "busiest_worker": {"id": busiest, **occupancy[busiest]},
        "pytest_rc": report.get("pytest_rc"), "failures": failures,
        "terminal_counts": report.get("terminal_counts", {}),
        "session_timeline": report.get("session_timeline"),
        "group_to_workers": report.get("group_to_workers"),
        "receipt": read_json(receipt_path) if receipt_path.exists() else None,
        "valid": False, "reasons": [],
    }
    if report.get("pytest_rc") != 0:
        result["reasons"].append("report pytest_rc != 0")
    if failures or any(int(suite.attrib.get(key, "0")) for key in ("failures", "errors")):
        result["reasons"].append("JUnit failures/errors")
    if Counter(report.get("finished", [])) != Counter(report["selected"]):
        result["reasons"].append("report finished != selected")
    try:
        result["witness"] = witness(root, report, ledger, condition)
    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        result["witness"] = {"valid": False, "reason": str(exc)}
        result["reasons"].append(f"witness: {exc}")
    result["valid"] = not result["reasons"]
    return result


def analyze_run(path, ledger, measurement_tip):
    meta = read_json(path / "run.json")
    result = {**meta, "id": path.name, "shards": [], "reasons": []}
    condition = meta.get("condition")
    if condition not in {"A", "B"} or not path.name.endswith(f"-{condition}"):
        result["reasons"].append("invalid/mismatched condition")
    for field in ("tip_sha", "tip_sha_after"):
        if not measurement_tip or meta.get(field) != measurement_tip:
            result["reasons"].append(f"{field} differs from measurement tip")
    for field in ("dirty_lines_before", "dirty_lines_after"):
        if type(meta.get(field)) is not int or meta[field] != 0:
            result["reasons"].append(f"{field} != 0 (or missing)")
    if meta.get("rc") != 0:
        result["reasons"].append("run rc != 0")
    env = meta.get("env", {})
    if env.get("PYTHONDONTWRITEBYTECODE_SET") != "no":
        result["reasons"].append("bytecode env が測定走に渡っている")
    if (condition == "A" and ENV in env) or (
        condition == "B" and env.get(ENV) != TOKEN
    ):
        result["reasons"].append("condition/env mismatch")
    if meta.get("copy_ok") is not True:
        result["reasons"].append("copy_ok is not true")
    session_ok = meta.get("session_dir") == "session"
    if not session_ok:
        result["reasons"].append("session_dir must be relative path 'session'")
    session = path / "session"
    for j in range(3):
        try:
            require(session_ok, "invalid copied session path")
            for filename in ("junit.xml", "report.json"):
                require((session / f"shard-{j}" / filename).is_file(),
                        f"missing copied artifact: shard-{j}/{filename}")
            shard = analyze_shard(session / f"shard-{j}", ledger, condition)
        except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as exc:
            shard = {"valid": False, "reasons": [str(exc)]}
        shard["index"] = j
        result["shards"].append(shard)
        result["reasons"].extend(f"shard-{j}: {reason}" for reason in shard["reasons"])
    measured = [s for s in result["shards"] if "W" in s]
    result["W_max"] = max((s["W"] for s in measured), default=None)
    result["argmax"] = [s["index"] for s in measured if s["W"] == result["W_max"]]
    if result["W_max"] is None or result["W_max"] <= 0:
        result["reasons"].append("missing/nonpositive W_max")
    result["valid"] = not result["reasons"]
    return result


def decision(pairs):
    valid = [pair for pair in pairs if pair["valid"]]
    deltas = [p["delta_W"] for p in valid]
    rates = [p["r"] for p in valid]
    medians = {"paired_delta_W": median(deltas), "paired_r": median(rates),
               "condition_W_difference": median(p["W_A"] for p in valid)
               - median(p["W_B"] for p in valid)} if valid else None
    if len(valid) < 3:
        return {"class": "undetermined", "label": "判定不能 (反復不足)",
                "valid_pairs": len(valid), "medians": medians}
    require(len(valid) == 3, "analysis must use exactly three valid pairs")
    if all(d > 0 for d in deltas):
        category = "i" if median(rates) >= .10 else "ii"
        label = "方向一致・閾値以上" if category == "i" else "方向一致・閾値未満"
        subclasses = []
    else:
        category, label = "iii", "効果未確立"
        subclasses = []
        if min(deltas) < 0 < max(deltas):
            subclasses.append("符号混在")
        if 0 in deltas:
            subclasses.append("ゼロを含む")
        if all(d < 0 for d in deltas):
            subclasses.append("全対負 (退行の観測)")
    return {"class": category, "label": label, "subclasses": subclasses,
            "valid_pairs": 3, "medians": medians}


def pair_runs(runs):
    require(len(runs) <= 12, "measurement runs exceed 12-run cap")
    pairs, valid_count = [], 0
    for i in range(0, len(runs), 2):
        members = runs[i:i + 2]
        reasons = []
        slot = valid_count + 1
        expected = ["A", "B"] if slot % 2 else ["B", "A"]
        if valid_count == 3:
            reasons.append("上限後 / 余剰")
        else:
            if [r.get("condition") for r in members] != expected:
                reasons.append("順序違反")
        if any("pair_slot" in r and (
                type(r["pair_slot"]) is not int or r["pair_slot"] != slot)
               for r in members):
            reasons.append("pair_slot differs from expected slot")
        if len(members) != 2 or {r.get("condition") for r in members} != {"A", "B"}:
            reasons.append("adjacent pair must contain one A and one B")
        if not all(r["valid"] for r in members):
            reasons.append("invalid run in pair")
        if len({r.get("tip_sha") for r in members}) != 1:
            reasons.append("pair tip mismatch")
        pair = {"id": i // 2 + 1, "expected_slot": slot, "expected_order": expected,
                "runs": [r["id"] for r in members],
                "order": [r.get("condition") for r in members],
                "valid": not reasons, "reasons": reasons}
        if (len(members) == 2 and {r.get("condition") for r in members} == {"A", "B"}
                and all(isinstance(r.get("W_max"), (int, float)) and r["W_max"] > 0
                        for r in members)):
            a = next(r for r in members if r["condition"] == "A")
            b = next(r for r in members if r["condition"] == "B")
            delta = a["W_max"] - b["W_max"]
            rate = delta / a["W_max"]
            pair.update(W_A=a["W_max"], W_B=b["W_max"], delta_W=delta, r=rate,
                        D357="変化なし (単走比較 |r| < 10%)" if abs(rate) < .1 else "|r| >= 10%")
        if not reasons:
            valid_count += 1
        for run in members:
            run["pair_valid"] = pair["valid"]
            run["pair_reasons"] = list(reasons)
        pairs.append(pair)
    return pairs


def numbered_run_paths(runs_root):
    paths = sorted((p for p in Path(runs_root).iterdir()
                    if p.is_dir() and re.fullmatch(r"\d+-[AB]", p.name)),
                   key=lambda p: (int(p.name.split("-")[0]), p.name))
    require(bool(paths), "no numbered A/B run directories")
    require(len(paths) <= 12, "measurement runs exceed 12-run cap")
    numbers = [int(p.name.split("-")[0]) for p in paths]
    require(len(numbers) == len(set(numbers)), "duplicate run number")
    require(numbers == list(range(1, len(paths) + 1)), "run number gap: expected consecutive from 01")
    require(all(p.name == f"{n:02d}-{p.name[-1]}" for p, n in zip(paths, numbers)),
            "run number must use two digits")
    return paths


def validate_run_times(runs):
    previous = None
    for run in runs:
        times = {}
        for field in ("submitted_at", "finished_at"):
            value = run.get(field)
            try:
                times[field] = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{run['id']}: invalid {field}={value!r}") from exc
        require(times["submitted_at"] <= times["finished_at"],
                f"{run['id']}: finished_at={run['finished_at']} precedes "
                f"submitted_at={run['submitted_at']}")
        if previous is not None:
            prev, prev_times = previous
            require(prev_times["submitted_at"] < times["submitted_at"],
                    f"submission order: {prev['id']} submitted_at={prev['submitted_at']} "
                    f">= {run['id']} submitted_at={run['submitted_at']}")
            require(prev_times["finished_at"] <= times["submitted_at"],
                    f"run overlap: {prev['id']} finished_at={prev['finished_at']} "
                    f"> {run['id']} submitted_at={run['submitted_at']}")
        previous = run, times


def analyze(runs_root, ledger_path, measurement_tip):
    require(bool(measurement_tip), "measurement tip is required")
    paths = numbered_run_paths(runs_root)
    raw = read_json(ledger_path)["duration_seconds_by_nodeid"]
    ledger = {}
    for key, value in raw.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        try:
            ledger[key] = number(value)
        except (ValueError, OverflowError):
            pass
    runs = []
    for path in paths:
        try:
            runs.append(analyze_run(path, ledger, measurement_tip))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            runs.append({"id": path.name, "condition": path.name[-1], "valid": False,
                         "reasons": [str(exc)], "shards": []})
    validate_run_times(runs)
    pairs = pair_runs(runs)
    return {"measurement_tip": measurement_tip, "claims": CLAIMS, "runs": runs, "pairs": pairs,
            "decision": decision(pairs), "failure_counts_by_arm": {
                arm: sum(len(s.get("failures", [])) for r in runs if r["condition"] == arm
                         for s in r["shards"]) for arm in ("A", "B")},
            "notes": ["逐次の隣接対比較。別 job/allocation 間の比較である。",
                      "F = W - O は同じ shard の残差。固定費とは実証していない。",
                      "中央値率 10% は本 wave 独自の保守基準。3/3 は有意差判定ではない。",
                      "worker item 列は JUnit 出現順。全 worker の2個目を保証しない。",
                      "測定 tip は必須 CLI 引数で固定し、前後 SHA と clean を照合する。"]}


def markdown(data):
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = ["## T-2766 A/B analysis", "", *data["notes"], "", "## 走表", "",
             "| ID | 条件 | tip | 投入 / 完了 | W_max | argmax | rc | session_dir_origin (参照しない) | 有効 / 理由 | 対の採否 / 理由 |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for run in data["runs"]:
        values = (run["id"], run["condition"], run.get("tip_sha"),
                  f'{run.get("submitted_at")} / {run.get("finished_at")}', run.get("W_max"),
                  run.get("argmax"), run.get("rc"), run.get("session_dir_origin"),
                  "valid" if run["valid"] else run["reasons"],
                  "valid" if run["pair_valid"] else run["pair_reasons"])
        lines.append("| " + " | ".join(map(cell, values)) + " |")
    lines += ["", "## Shard / witness", "",
              "| 走 | shard | W | O | F (残差) | 最忙 worker / items / duration | witness | partner cost |",
              "|---|---|---|---|---|---|---|---|"]
    for run in data["runs"]:
        for shard in run["shards"]:
            w = shard.get("witness", {})
            values = (run["id"], shard["index"], shard.get("W"), shard.get("O"), shard.get("F"),
                      shard.get("busiest_worker"), w.get("valid", False),
                      w.get("partner_cost_distribution"))
            lines.append("| " + " | ".join(map(cell, values)) + " |")
    lines += ["", "## 対表", "", "| 対 | 期待 slot / 順序 | 走順 | 有効 / 理由 | ΔW | r | D357 |",
              "|---|---|---|---|---|---|---|"]
    for pair in data["pairs"]:
        values = (pair["id"], f'{pair["expected_slot"]} / {pair["expected_order"]}',
                  pair["runs"], "valid" if pair["valid"] else pair["reasons"],
                  pair.get("delta_W"), pair.get("r"), pair.get("D357"))
        lines.append("| " + " | ".join(map(cell, values)) + " |")
    lines += ["", "## 中央値と事前登録判定", "", "```json",
              json.dumps(data["decision"], ensure_ascii=False, indent=2), "```",
              "", "## Witness・時刻・負荷・receipt・赤の詳細", ""]
    for run in data["runs"]:
        lines += [f'## {run["id"]}', "", "```json",
                  json.dumps(run, ensure_ascii=False, indent=2), "```", ""]
    return "\n".join(lines)


def write_analysis(data, out):
    out.mkdir(parents=True, exist_ok=True)
    (out / "analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    (out / "analysis.md").write_text(markdown(data), encoding="utf-8")


def selftest():
    selected, ledger, scope_items = [], {}, {}
    for i in range(120):
        items = []
        for j in range(3 if i == 0 else 2 if i == 1 else 1):
            name = f"test_{i:03d}_{j}" + ("[mail@host::value]" if i == 3 else "")
            base = "orchestrator/tests/test_fixture.py::" + ("TestClass::" if i == 3 else "") + name
            selected.append(base)
            items.append(base)
            ledger[base] = (120 - i) * 6.0 / (3 if i == 0 else 2 if i == 1 else 1)
        scope_items[f"u{i:03d}"] = items
    ranks = {f"u{i:03d}": rank for rank, i in enumerate(
        (*range(48), *range(119, 71, -1), *range(48, 72))
    )}

    def fixture(condition, wall=100):
        root = ET.Element("testsuites")
        suite = ET.SubElement(root, "testsuite", time=str(wall), failures="0", errors="0")
        for key, items in scope_items.items():
            for base in items:
                classname, name = junit_key(f"{base}@{key}")
                case = ET.SubElement(suite, "testcase", classname=classname, name=name,
                                     time="10" if key == "u001" else "1")
                if key == "u002":
                    ET.SubElement(case, "skipped", message="held")
                if condition == "B":
                    props = ET.SubElement(case, "properties")
                    for field, value in {
                        "scope": key, "rank": str(ranks[key]),
                        "partner": "1" if 48 <= ranks[key] < 96 else "0",
                        "worker": "gw0" if key == "u000" else "gw1",
                    }.items():
                        ET.SubElement(props, "property", name=PREFIX + field, value=value)
        report = {
            "selected": selected, "finished": selected, "pytest_rc": 0,
            "observed_universe": [{"nodeid": nodeid, "group": key}
                                  for key, items in scope_items.items() for nodeid in items],
            "worker_occupancy": {"gw0": {"items": 3, "duration_s": 70},
                                 "gw1": {"items": 120, "duration_s": 50}},
            "session_timeline": {}, "group_to_workers": {},
        }
        return root, report

    root, report = fixture("B")
    observed = witness(root, report, ledger, "B")
    require(all(observed["checks"].values()), "positive witness")
    require(observed["property_testcases"] == 123, "skipped testcase coverage")
    require(observed["partner_cost_distribution"] == {
        "count": 48, "min": 6.0, "max": 288.0, "zero_count": 0,
    }, "independent partner distribution")
    require(observed["ledger_max_units"][0]["second_item_in_worker_sequence"]["nodeid"].endswith("test_000_1@u000"),
            "worker second item")
    require(not observed["ledger_max_units"][0]["second_item_in_worker_sequence"]["partner"], "second item counterexample")
    require(len(observed["worker_item_sequences"]["gw1"]) == 120, "worker reconstruction")
    require(observed["ledger_max_units"][0]["second_unit"] is None,
            "three-item unit has no second unit")
    require(observed["ledger_max_units"][0]["second_item_is_within_first_unit"],
            "second item is within first unit")
    require(observed["measured_longest_units"][0]["scope"] == "u001"
            and observed["measured_longest_units"][0]["measured_time"] == 20,
            "measured longest differs from ledger maximum")
    require(observed["measured_longest_units"][0]["worker"] == "gw1"
            and observed["measured_longest_units"][0]["second_unit"]["scope"] == "u002",
            "measured longest worker and second unit")

    # Move a later unit to the three-item worker: its next unit may be a
    # partner or a non-partner, while its second item stays inside u000.
    for key, partner, cost in (("u119", True, 6.0), ("u048", False, 432.0)):
        xml, rep = fixture("B")
        for case in xml.iter("testcase"):
            if split_group(case.attrib["name"])[1] == key:
                next(prop for prop in case.findall("./properties/property")
                     if prop.attrib["name"] == PREFIX + "worker").set("value", "gw0")
        rep["worker_occupancy"]["gw0"]["items"] = 4
        rep["worker_occupancy"]["gw1"]["items"] = 119
        result = witness(xml, rep, ledger, "B")
        longest = result["ledger_max_units"][0]
        require(longest["second_unit"] == {
            "scope": key, "partner": partner, "ledger_cost": cost, "measured_time": 1.0,
        }, f"second unit partner={partner}")
        require(longest["second_item_in_worker_sequence"]["scope"] == "u000"
                and not longest["second_item_in_worker_sequence"]["partner"],
                "second item must not stand in for second unit")
        require([unit["scope"] for unit in result["worker_unit_sequences"]["gw0"]]
                == ["u000", key], "collapse contiguous item scopes")
    require(costs_close([0.1 + 0.2, 2.0], [2.0, 0.3]), "isclose roundoff")
    require(costs_close([0.0], [1e-9]), "isclose absolute tolerance")
    require(not costs_close([0.0], [1.01e-9]), "isclose tight absolute rejection")
    require(costs_close([100.0], [100.0 + 5e-8]), "isclose relative tolerance")
    require(not costs_close([100.0], [100.0 + 2e-7]), "isclose tight relative rejection")
    require(not costs_close([1.0, 1.0], [1.0]), "cost multiset multiplicity")

    require(witness(*fixture("A"), ledger, "A")["property_testcases"] == 0, "A properties")

    def rejected(xml, rep, costs, arm, text):
        try:
            witness(xml, rep, costs, arm)
        except ValueError as exc:
            require(text in str(exc), f"wrong rejection: {exc}; expected {text}")
        else:
            raise AssertionError(f"accepted damaged witness: {text}")

    # Rounding may change independent ordering at near-equal cost boundaries.
    for key, boundary, reason in (
        ("u047", 432.0, "head cardinality/cost"),
        ("u071", 288.0, "partner cost"),
    ):
        costs = {**ledger, scope_items[key][0]: boundary - 1e-8}
        require(witness(root, report, costs, "B")["valid"], f"isclose witness: {reason}")
        costs[scope_items[key][0]] = boundary - 1e-4
        rejected(root, report, costs, "B", reason)

    rejected(root, report, ledger, "A", "A has pairing")
    damaged = deepcopy(root)
    case = next(damaged.iter("testcase"))
    case.remove(case.find("properties"))
    rejected(damaged, report, ledger, "B", "coverage")
    damaged = deepcopy(root)
    next(p for p in damaged.iter("property") if p.attrib["name"] == PREFIX + "partner").set("value", "1")
    rejected(damaged, report, ledger, "B", "partner item sets")
    damaged = deepcopy(root)
    for props in damaged.iter("properties"):
        rank = next(p for p in props if p.attrib["name"] == PREFIX + "rank")
        if rank.attrib["value"] == "2":
            rank.set("value", "96")
        elif rank.attrib["value"] == "96":
            rank.set("value", "2")
    rejected(damaged, report, ledger, "B", "head cardinality/cost")
    damaged_costs = dict(ledger)
    damaged_costs[scope_items["u119"][0]] = 300.0
    rejected(root, report, damaged_costs, "B", "partner cost")
    damaged = deepcopy(report)
    damaged["worker_occupancy"]["gw0"]["items"] = 4
    rejected(root, damaged, ledger, "B", "worker item counts")
    damaged = deepcopy(root)
    next(p for p in damaged.iter("property") if p.attrib["name"] == PREFIX + "scope").set("value", "forged")
    rejected(damaged, report, ledger, "B", "scope property")

    rows = testcase_rows(root, selected)
    costs = dict(ledger)
    del costs[scope_items["u065"][0]]
    historical = scope_items["u118"][0]
    costs[historical + "@u118"] = costs.pop(historical)
    units, _, unknown = independent_units(rows, report, costs)
    require(unknown == 144 and units["u065"]["cost"] == 144, "unknown 96th cost")
    require(units["u118"]["cost"] == 12, "historical suffixed ledger fallback")
    # The real-repo marker can survive only in the report after suffix stripping.
    real_base = "orchestrator/tests/test_real.py::test_case"
    unit, _, _ = independent_units(
        [{"nodeid": real_base, "selected": real_base}],
        {"observed_universe": [{"nodeid": real_base, "group": "real-repo"}]},
        {real_base + "@real-repo": 7.0},
    )
    require(unit[real_base]["cost"] == 7, "stripped real-repo ledger fallback")
    require(split_group("test[param@literal]") == ("test[param@literal]", None), "parameter @")

    with tempfile.TemporaryDirectory(prefix="t2766-analyze-") as temp:
        base = Path(temp)
        ledger_path = base / "ledger.json"
        ledger_path.write_text(json.dumps({"duration_seconds_by_nodeid": ledger}))
        runs = base / "runs"
        runs.mkdir()
        for index, (arm, wall) in enumerate(zip("ABBAAB", (100, 80, 120, 200, 300, 290)), 1):
            run = runs / f"{index:02d}-{arm}"
            session = run / "session"
            session.mkdir(parents=True)
            (run / "run.json").write_text(json.dumps({
                "condition": arm, "tip_sha": "fixed-tip", "tip_sha_after": "fixed-tip",
                "dirty_lines_before": 0, "dirty_lines_after": 0, "copy_ok": True,
                "pair_slot": (index + 1) // 2, "rc": 0,
                "session_dir_origin": str(base / "deleted-origin"),
                "submitted_at": f"2026-09-19T{index:02d}:00:00+0900",
                "finished_at": f"2026-09-19T{index:02d}:30:00+0900",
                "session_dir": "session", "env": {
                    **({ENV: TOKEN} if arm == "B" else {}),
                    "PYTHONDONTWRITEBYTECODE_SET": "no",
                },
                "other_leaders": 1, "load1": 5,
            }))
            for j in range(3):
                shard = session / f"shard-{j}"
                shard.mkdir()
                xml, rep = fixture(arm, wall - j)
                ET.ElementTree(xml).write(shard / "junit.xml", encoding="utf-8")
                (shard / "report.json").write_text(json.dumps(rep))
        analysis = analyze(runs, ledger_path, "fixed-tip")
        require(all(r["valid"] for r in analysis["runs"]), "end-to-end valid runs")
        require([p["delta_W"] for p in analysis["pairs"]] == [20, 80, 10], "adjacent AB/BA pairs")
        require(analysis["decision"]["medians"] == {
            "paired_delta_W": 20, "paired_r": .2, "condition_W_difference": 80,
        }, "three separate medians")
        require(analysis["runs"][0]["shards"][0]["F"] == 30, "same-shard residual")
        require(analysis["runs"][0]["argmax"] == [0], "argmax")
        write_analysis(analysis, base / "out")
        require((base / "out" / "analysis.md").exists(), "Markdown output")
        require(analysis["claims"] == CLAIMS and "初期配布の送信順ではない" in CLAIMS,
                "claims scope")
        require(str(base / "deleted-origin") in markdown(analysis), "origin in table")
        run_path = runs / "03-B" / "run.json"
        original = read_json(run_path)
        for field, value, reason in (
            ("tip_sha", "different-tip", "tip_sha differs"),
            ("tip_sha_after", "different-tip", "tip_sha_after differs"),
            ("dirty_lines_before", 1, "dirty_lines_before"),
            ("dirty_lines_after", 1, "dirty_lines_after"),
            ("copy_ok", False, "copy_ok"),
            ("copy_ok", 1, "copy_ok"),
            ("session_dir", str(runs / "03-B" / "session"), "session_dir"),
            ("session_dir", "../03-B/session", "session_dir"),
            ("session_dir", None, "session_dir"),
        ):
            meta = {**original, field: value}
            run_path.write_text(json.dumps(meta))
            damaged = analyze(runs, ledger_path, "fixed-tip")
            require(not damaged["runs"][2]["valid"]
                    and any(reason in r for r in damaged["runs"][2]["reasons"]),
                    f"run exclusion: {field}={value}")
            require(damaged["decision"]["class"] == "undetermined", "invalid pair exclusion")
            require(reason in markdown(damaged), "exclusion reason in table")
        for field in ("tip_sha_after", "dirty_lines_before", "dirty_lines_after", "copy_ok"):
            meta = dict(original)
            del meta[field]
            run_path.write_text(json.dumps(meta))
            require(not analyze(runs, ledger_path, "fixed-tip")["runs"][2]["valid"],
                    f"missing required field: {field}")
        run_path.write_text(json.dumps(original))
        require(not any(r["valid"] for r in analyze(runs, ledger_path, "other-tip")["runs"]),
                "CLI tip never derived from first run")

        for filename in ("report.json", "junit.xml"):
            artifact = runs / "06-B" / "session" / "shard-2" / filename
            saved = artifact.read_bytes()
            artifact.unlink()
            damaged = analyze(runs, ledger_path, "fixed-tip")
            require(damaged["decision"]["class"] == "undetermined"
                    and any(f"missing copied artifact: shard-2/{filename}" in reason
                            for reason in damaged["runs"][5]["reasons"]),
                    f"missing copied {filename}")
            artifact.write_bytes(saved)

        def fails_analysis(reason):
            try:
                analyze(runs, ledger_path, "fixed-tip")
            except ValueError as exc:
                require(reason in str(exc), f"wrong series rejection: {exc}")
            else:
                raise AssertionError(f"accepted invalid series: {reason}")

        for field, value, reason in (
            ("submitted_at", "2026-09-19T01:59:59+0900", "submission order"),
            ("submitted_at", "2026-09-19T02:00:00+0900", "submission order"),
            ("submitted_at", "2026-09-19T02:29:59+0900", "run overlap"),
            ("submitted_at", "bad-time", "invalid submitted_at"),
            ("finished_at", None, "invalid finished_at"),
            ("finished_at", "2026-09-19T02:59:59+0900", "precedes"),
        ):
            run_path.write_text(json.dumps({**original, field: value}))
            fails_analysis(reason)
        run_path.write_text(json.dumps({
            **original, "submitted_at": "2026-09-19T02:30:00+0900",
        }))
        require(all(r["valid"] for r in analyze(runs, ledger_path, "fixed-tip")["runs"]),
                "previous finish equals next submission")
        run_path.write_text(json.dumps(original))

        for run_id in ("01-A", "03-B"):
            env_path = runs / run_id / "run.json"
            saved_meta = read_json(env_path)
            for value in ("yes", "", None):
                meta = deepcopy(saved_meta)
                if value is None:
                    del meta["env"]["PYTHONDONTWRITEBYTECODE_SET"]
                else:
                    meta["env"]["PYTHONDONTWRITEBYTECODE_SET"] = value
                env_path.write_text(json.dumps(meta))
                damaged = analyze(runs, ledger_path, "fixed-tip")
                run = next(r for r in damaged["runs"] if r["id"] == run_id)
                require(not run["valid"] and "bytecode env が測定走に渡っている" in run["reasons"],
                        f"bytecode env exclusion: {run_id}={value!r}")
            for value in ("", None, "wrong-token"):
                meta = deepcopy(saved_meta)
                meta["env"][ENV] = value
                env_path.write_text(json.dumps(meta))
                damaged = analyze(runs, ledger_path, "fixed-tip")
                run = next(r for r in damaged["runs"] if r["id"] == run_id)
                require(not run["valid"] and "condition/env mismatch" in run["reasons"],
                        f"pairing env exclusion: {run_id}={value!r}")
            env_path.write_text(json.dumps(saved_meta))

        (runs / "02-B").rename(runs / "08-B")
        fails_analysis("gap")
        (runs / "08-B").rename(runs / "02-B")
        (runs / "02-A").mkdir()
        fails_analysis("duplicate")
        (runs / "02-A").rmdir()
        for index in range(7, 14):
            (runs / f"{index:02d}-A").mkdir()
        fails_analysis("12-run cap")
        for index in range(7, 14):
            (runs / f"{index:02d}-A").rmdir()

    def pairs_for(deltas):
        return [{"valid": True, "delta_W": d, "r": d / 100, "W_A": 100, "W_B": 100 - d}
                for d in deltas]

    for deltas, category, subclass in (
        ((10, 20, 30), "i", None), ((1, 2, 3), "ii", None),
        ((1, -1, 2), "iii", "符号混在"), ((1, 0, 2), "iii", "ゼロを含む"),
        ((-1, -2, -3), "iii", "全対負 (退行の観測)"),
        ((0, 0, 0), "iii", "ゼロを含む"),
    ):
        result = decision(pairs_for(deltas))
        require(result["class"] == category, f"decision branch {category}")
        require(subclass is None or subclass in result["subclasses"], "decision subclass")
    require(decision(pairs_for((1, 2)))["class"] == "undetermined", "insufficient pairs")
    def run_sequence(arms):
        return [{"id": f"{i:02d}-{arm}", "condition": arm, "tip_sha": "fixed",
                 "valid": True, "W_max": 100 if arm == "A" else 99}
                for i, arm in enumerate(arms, 1)]

    pseudo = run_sequence("ABBAABBA")
    pairs = pair_runs(pseudo)
    require([p["valid"] for p in pairs] == [True, True, True, False],
            "stop at first three valid pairs")
    require("上限後 / 余剰" in pairs[-1]["reasons"]
            and "上限後 / 余剰" in pseudo[-1]["pair_reasons"], "surplus retained in run table")
    require("変化なし" in pairs[0]["D357"], "D357 per-pair annotation")

    retry = run_sequence("ABABBAAB")
    retry[0]["valid"] = False
    for run, slot in zip(retry, (1, 1, 1, 1, 2, 2, 3, 3)):
        run["pair_slot"] = slot
    pairs = pair_runs(retry)
    require([p["valid"] for p in pairs] == [False, True, True, True]
            and [p["expected_slot"] for p in pairs] == [1, 1, 2, 3],
            "invalid pair retries same slot and order")
    wrong = run_sequence("BAABBAAB")
    pairs = pair_runs(wrong)
    require([p["valid"] for p in pairs] == [False, True, True, True]
            and "順序違反" in pairs[0]["reasons"], "order violation then same-slot retry")
    wrong = run_sequence("ABABBAAB")
    pairs = pair_runs(wrong)
    require([p["valid"] for p in pairs] == [True, False, True, True],
            "even slot requires BA and retries BA")
    wrong = run_sequence("AB")
    wrong[1]["pair_slot"] = 2
    require("pair_slot differs" in " ".join(pair_runs(wrong)[0]["reasons"]),
            "pair_slot mismatch")
    wrong[1]["pair_slot"] = True
    require(not pair_runs(wrong)[0]["valid"], "pair_slot must be integer")
    require(not pair_runs(run_sequence("A"))[0]["valid"], "incomplete adjacent pair")
    capped = run_sequence("AB" * 6)
    for run in capped:
        run["valid"] = False
    require(not any(p["valid"] for p in pair_runs(capped)), "12-run cap insufficient pairs")
    try:
        pair_runs(run_sequence("AB" * 7))
    except ValueError as exc:
        require("12-run cap" in str(exc), "12-run cap rejection")
    else:
        raise AssertionError("accepted more than 12 runs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-root", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--measurement-tip")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        try:
            selftest()
        except Exception as exc:
            print(f"FAIL: {type(exc).__name__}: {exc}")
            return 1
        print("PASS: synthetic JUnit/report/ledger, witness, pairs, decision branches; tip/dirty, order/retry/numbering/cap, copied artifacts, second unit/measured longest, isclose, submission times/overlap, bytecode/pairing env")
        return 0
    if any(v is None for v in (args.runs_root, args.ledger, args.out, args.measurement_tip)):
        parser.error("--runs-root, --ledger, --out and --measurement-tip are required unless --selftest")
    try:
        data = analyze(args.runs_root, args.ledger, args.measurement_tip)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    write_analysis(data, args.out)
    print(data["decision"]["label"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## run-measure.sh — 測定 launcher (親、レビュー B / 焦点再レビュー後)

```bash
#!/bin/bash
# dev-wave-t2766-pairing-ab 測定走 (門番 + 直接投入)。codex/detach.sh 経由で呼ぶ。
#  usage: run-measure.sh <NN> <A|B> <pair-slot>
#  形: 同一 SHA (MEASUREMENT_TIP) の wave worktree から IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py
#      を直接投入 (待ち手 dev_wave_wait.py acceptance は claim 直後に main を取り込み tip が変わるので測定には使わない)。
#  B: IZANAGI_ACCEPTANCE_PAIRING_V1=t2766-min-cost-partners を export。A: unset。PYTHONDONTWRITEBYTECODE は明示 unset
#     (計算ノード既定の "1" に委ねる。warm-up だけが空文字を渡した)。
#  直列化: job dir の flock を **最初に** 取り、門番待ち → 投入 → 成果物保存 → run.json まで保持する。
#         取れなければ何も作らずに rc=94 で終わる (未投入 attempt を系列へ混ぜない)。
#  RUN dir: 門番が開き投入直前照合を通った時点で `mkdir` (既存なら失敗 = 同一 NN の再利用拒否) して作る。
#           それ以前の停止 (門番未開放・tip 不一致・dirty) は runs/ に dir を作らず aborts/ に記録する。
#  門番: 他 session の受入待ち手 (`dev_wave_wait.py … acceptance`、自 slug 除外、この検索式で数えた本数) <= 1
#        かつ 1 分 load < 30 を 100〜140 秒乱数周期で判定し、2 回連続で開いていたら 0〜45 秒乱数待ち → 再判定 → 投入。
#  終了 rc: 子 rc が 0 でも複製・sha・run.json 生成に失敗したら 96/97 (子 rc は run.json の `rc` に別記)。
set -u
JOBDIR=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-ab
WT=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2766-pairing-ab
SLUG=dev-wave-t2766-pairing-ab
MEASUREMENT_TIP=0eabe67bad429403a2eadfddcac4c1252d55dda3
NN=${1:?run number (2 digits)}
COND=${2:?A or B}
SLOT=${3:?pair slot}
TAG="$NN-$COND"
RUN="$JOBDIR/runs/$TAG"
LEADERS_MAX=1
L1_MAX=30
GATE_MAX_ROUNDS=90
mkdir -p "$JOBDIR/runs" "$JOBDIR/aborts"
STAMP=$(date '+%Y%m%dT%H%M%S')
ABORT="$JOBDIR/aborts/$TAG-$STAMP.log"
abort() { echo "$(date '+%Y-%m-%dT%H:%M:%S%z') $2" >> "$ABORT"; exit "$1"; }
if [ "$COND" != "A" ] && [ "$COND" != "B" ]; then abort 2 "bad condition: $COND"; fi

# 直列化: 最初に flock (fd 9)。取れなければ何も作らない。
exec 9> "$JOBDIR/measure.lock"
if ! flock -n 9; then abort 94 "another measurement holds the lock"; fi
if [ -e "$RUN" ]; then abort 2 "run dir exists (attempt reuse refused): $RUN"; fi

export IZANAGI_ACCEPTANCE_SHARDS=3
unset IZANAGI_ACCEPTANCE_PAIRING_V1
unset PYTHONDONTWRITEBYTECODE
if [ "$COND" = "B" ]; then export IZANAGI_ACCEPTANCE_PAIRING_V1=t2766-min-cost-partners; fi
cd "$WT" || abort 90 "cd failed"

count_leaders() { ps -eo args | grep '[d]ev_wave_wait.py' | grep ' acceptance' | grep -vc "$SLUG"; }
load1() { read -r l1 _ < /proc/loadavg; echo "$l1"; }
dirty_lines() { git status --porcelain --untracked-files=all --ignore-submodules=none | wc -l; }
glog() { echo "$(date '+%Y-%m-%dT%H:%M:%S%z') $*" >> "$JOBDIR/aborts/$TAG-$STAMP.gate.log"; }

gate_open() {
  l1=$(load1)
  leaders=$(count_leaders)
  glog "gate: load1=$l1 leaders=$leaders (max $LEADERS_MAX, l1 < $L1_MAX)"
  python3 - "$l1" "$leaders" "$LEADERS_MAX" "$L1_MAX" <<'PY'
import sys
l1, leaders, lmax, l1max = float(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4])
sys.exit(0 if (leaders <= lmax and l1 < l1max) else 1)
PY
}

round=0; stable=0; opened=0
while [ "$round" -lt "$GATE_MAX_ROUNDS" ]; do
  round=$((round + 1))
  if ! gate_open; then stable=0; sleep $((100 + RANDOM % 41)); continue; fi
  stable=$((stable + 1))
  if [ "$stable" -lt 2 ]; then sleep $((100 + RANDOM % 41)); continue; fi
  sleep $((RANDOM % 46))
  if ! gate_open; then stable=0; sleep $((100 + RANDOM % 41)); continue; fi
  opened=1
  break
done
if [ "$opened" -ne 1 ]; then abort 93 "gate never opened"; fi

# 投入直前の照合: HEAD == MEASUREMENT_TIP、clean。
TIP=$(git rev-parse HEAD)
DIRTY_BEFORE=$(dirty_lines)
if [ "$TIP" != "$MEASUREMENT_TIP" ]; then abort 95 "HEAD $TIP != measurement tip"; fi
if [ "$DIRTY_BEFORE" -ne 0 ]; then abort 91 "worktree dirty before launch ($DIRTY_BEFORE lines)"; fi

# ここで初めて RUN dir を作る (既存なら mkdir が失敗 = 再利用拒否)。
if ! mkdir "$RUN"; then abort 2 "mkdir failed (exists?): $RUN"; fi
CHAIN="$RUN/chain.log"
echo $$ > "$RUN/measure.pid"
mv "$JOBDIR/aborts/$TAG-$STAMP.gate.log" "$RUN/gate.log" 2>/dev/null
log() { echo "$(date '+%Y-%m-%dT%H:%M:%S%z') $*" >> "$CHAIN"; }
MAIN=$(git rev-parse refs/heads/main)
LEADERS=$(count_leaders)
L1=$(load1)
START=$(date '+%Y-%m-%dT%H:%M:%S%z')
log "launch: cond=$COND slot=$SLOT tip=$TIP main=$MAIN leaders=$LEADERS load1=$L1"
env | grep '^IZANAGI_\|^PYTHONDONTWRITEBYTECODE' > "$RUN/env.txt"
echo "PYTHONDONTWRITEBYTECODE_SET=$( [ -n "${PYTHONDONTWRITEBYTECODE+x}" ] && echo yes || echo no )" >> "$RUN/env.txt"
python3 tools/run_tests.py > "$RUN/child.log" 2>&1
rc=$?
END=$(date '+%Y-%m-%dT%H:%M:%S%z')
ROOT=$(grep -o '"session_root":"[^"]*"' "$RUN/child.log" | head -1 | cut -d'"' -f4)
DIRTY_AFTER=$(dirty_lines)
TIP_AFTER=$(git rev-parse HEAD)
log "finished: child_rc=$rc session_root=$ROOT dirty_after=$DIRTY_AFTER tip_after=$TIP_AFTER"

# 複製: shard-0/1/2 の junit.xml と report.json (+ dispatch/receipt.json があれば) を session/ へ。sha256 で検算。
COPY_OK=0
if [ -n "$ROOT" ] && [ -d "$ROOT" ]; then
  mkdir -p "$RUN/session"
  COPY_OK=1
  for s in 0 1 2; do
    mkdir -p "$RUN/session/shard-$s"
    for f in junit.xml report.json; do
      if [ -f "$ROOT/shard-$s/$f" ]; then
        cp "$ROOT/shard-$s/$f" "$RUN/session/shard-$s/$f" || COPY_OK=0
        a=$(sha256sum "$ROOT/shard-$s/$f" | cut -d' ' -f1); b=$(sha256sum "$RUN/session/shard-$s/$f" | cut -d' ' -f1)
        if [ "$a" != "$b" ]; then COPY_OK=0; log "sha mismatch shard-$s/$f"; fi
        echo "$b  shard-$s/$f" >> "$RUN/session/SHA256SUMS"
      else
        COPY_OK=0; log "missing $ROOT/shard-$s/$f"
      fi
    done
    if [ -f "$ROOT/shard-$s/dispatch/receipt.json" ]; then
      mkdir -p "$RUN/session/shard-$s/dispatch"
      cp "$ROOT/shard-$s/dispatch/receipt.json" "$RUN/session/shard-$s/dispatch/receipt.json" || log "receipt copy failed shard-$s"
    fi
  done
  if [ -f "$ROOT/junit.xml" ]; then cp "$ROOT/junit.xml" "$RUN/session/junit.xml" || log "top junit copy failed"; fi
fi
log "copy_ok=$COPY_OK"
python3 - "$RUN/run.json" "$COND" "$TIP" "$MAIN" "$START" "$END" "$ROOT" "$LEADERS" "$L1" "$rc" "$DIRTY_BEFORE" "$DIRTY_AFTER" "$TIP_AFTER" "$NN" "$SLOT" "$COPY_OK" "$MEASUREMENT_TIP" "$LEADERS_MAX" "$L1_MAX" <<'PY'
import json, sys
(path, cond, tip, main, start, end, root, leaders, l1, rc, dirty_before, dirty_after, tip_after, nn, slot, copy_ok, mtip, lmax, l1max) = sys.argv[1:]
env = {}
for line in open(path.replace("run.json", "env.txt")):
    k, _, v = line.rstrip("\n").partition("=")
    env[k] = v
json.dump({
    "run": nn, "condition": cond, "pair_slot": int(slot),
    "measurement_tip": mtip, "tip_sha": tip, "tip_sha_after": tip_after,
    "main_sha_at_launch": main,
    "submitted_at": start, "finished_at": end,
    "session_dir": "session" if copy_ok == "1" else None,
    "session_dir_origin": root or None, "copy_ok": copy_ok == "1",
    "env": env, "other_leaders": int(leaders), "load1": float(l1), "rc": int(rc),
    "dirty_lines_before": int(dirty_before), "dirty_lines_after": int(dirty_after),
    "gate": {"leaders_max": int(lmax), "load1_max_exclusive": float(l1max),
             "leader_query": "ps -eo args | grep '[d]ev_wave_wait.py' | grep ' acceptance' | grep -vc <slug>"},
}, open(path, "w"), indent=2, ensure_ascii=True)
PY
json_rc=$?
final=$rc
if [ "$json_rc" -ne 0 ]; then final=97; log "run.json generation failed rc=$json_rc"; fi
if [ "$COPY_OK" -ne 1 ] && [ "$final" -eq 0 ]; then final=96; log "copy failed with child rc=0"; fi
echo "$final" > "$RUN/measure.done"
exit "$final"
```

## run-series.sh — 測定連結 (親)

```bash
#!/bin/bash
# 親専用: 測定走の連結 (01-A は先行投入済み)。01-A の done を待ってから 02-B → 03-B → 04-A → 05-A → 06-B を逐次投入する。
# 各走の rc は run.json と measure.done に残す。赤でも次へ進む (対の有効性は集計器が判定)。
set -u
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-ab
echo $$ > "$J/series.pid"
rm -f "$J/series.done"
log() { echo "$(date '+%Y-%m-%dT%H:%M:%S%z') $*" >> "$J/series.log"; }
log "series start; waiting for runs/01-A/measure.done"
while [ ! -f "$J/runs/01-A/measure.done" ]; do
  if ! pgrep -f "run-measure.sh 01 A" > /dev/null; then
    if [ ! -f "$J/runs/01-A/measure.done" ]; then log "01-A launcher died without done -> stop"; echo 90 > "$J/series.done"; exit 90; fi
  fi
  sleep 30
done
log "01-A done rc=$(cat "$J/runs/01-A/measure.done")"
for spec in "02 B 1" "03 B 2" "04 A 2" "05 A 3" "06 B 3"; do
  set -- $spec
  log "launch $1-$2 slot $3"
  bash "$J/run-measure.sh" "$1" "$2" "$3"
  rc=$?
  log "$1-$2 rc=$rc"
done
echo 0 > "$J/series.done"
log "series end"
exit 0
```

## run-warm2.sh — warm-up (親)

```bash
#!/bin/bash
# 親専用: collect-only を 1 回走らせ orchestrator/tests/__pycache__ を温める (T-2710 §4)。
# login の admission が headroom 0 で dispatch へ倒れるため、PYTHONDONTWRITEBYTECODE を空 (= 「書かない」指定を外す) で
# allowlist 経由で計算ノードへ渡し、共有 FS の __pycache__ へ pytest の書換 pyc を書かせる。測定走にはこの env を渡さない。
set -u
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-ab
W=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2766-pairing-ab
echo $$ > "$J/warm2.pid"
rm -f "$J/warm2.done"
cd "$W" || { echo 90 > "$J/warm2.done"; exit 90; }
export PYTHONDONTWRITEBYTECODE=
date '+%Y-%m-%dT%H:%M:%S%z' > "$J/warm2.started.txt"
python3 tools/run_tests.py --collect-only -q -p no:cacheprovider > "$J/warm2.log" 2>&1
rc=$?
date '+%Y-%m-%dT%H:%M:%S%z' > "$J/warm2.finished.txt"
find orchestrator/tests/__pycache__ -name '*.pyc' 2>/dev/null | wc -l > "$J/warm2.pyc-count.txt"
echo "$rc" > "$J/warm2.done"
exit "$rc"
```

## run-mutation.sh — 変異 harness 起動 (親)

```bash
#!/bin/bash
# 親専用: 変異 harness を独立 clone (D1009) の固定 commit で走らせる。detach.sh 経由で呼ぶ。
# usage: run-mutation.sh <tag> <spec> <spec-sha256> <wrapper-attempt>
set -u
TAG=${1:?tag}
SPEC=${2:?spec}
SHA=${3:?spec sha256}
ATT=${4:?wrapper attempt}
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-ab
SRC="$J/mutation-source"
COMMIT=0eabe67bad429403a2eadfddcac4c1252d55dda3
mkdir -p "$J/mutation-scratch"
echo $$ > "$J/mutation-$TAG.pid"
rm -f "$J/mutation-$TAG.done"
cd "$SRC" || { echo 90 > "$J/mutation-$TAG.done"; exit 90; }
export IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600
export IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600
python3 tools/mutation_worktree.py --source-repo "$SRC" --commit "$COMMIT" \
  --scratch-root "$J/mutation-scratch" \
  --spec "$SPEC" --expected-spec-sha256 "$SHA" \
  --out "$J/mutation-$TAG-results.json" \
  --attempt-out "$J/mutation-$TAG-attempts.json" --wrapper-attempt "$ATT" \
  --runner-mode dispatch --detached \
  -- python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_acceptance_schedule_order.py orchestrator/tests/test_pegasus_dispatch_compute.py -q -rf \
  > "$J/mutation-$TAG.log" 2>&1
rc=$?
echo "$rc" > "$J/mutation-$TAG.done"
exit "$rc"
```
