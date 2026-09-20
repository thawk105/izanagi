# probe / launcher の逐語と sha256 (repo へ実行可能 file として入れない。原本は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-adopt/`)

| file | sha256 | byte | 用途 |
|---|---|---|---|
| `probe/t2766_adopt_analyze.py` | `4fc9463e2d1ce8a7d4b0af6947ec86a4c41d99e4e712c82ef3a9e9faa812e381` | 48622 | 集計器 (Codex author が前 wave の t2766_ab_analyze.py から改作。標準 library のみ、--selftest PASS) |
| `run-acceptance.sh` | `b193db71a4d29d04cee6bf1cf4a74475b56573b7b22371a83f805a6339a76ab3` | 2613 | 受入 1 走の launcher (待ち手経由、A/B 共通、親) |
| `gate-series.sh` | `6062c7ab90b21b356600aa29862fe1d6a0a42dd827ed64b0a7cf2e3d53259d41` | 3461 | 門番 + 直列投入 loop (親) |
| `write_run_json.py` | `556f064020e981d4787ab2f4fc21b40f7e63824d6a0693f64e44b232e79f8afd` | 3915 | run.json と session 写しの生成 (親) |
| `make-a-worktree.sh` | `13aeeb1b910989239ee79cf021500f75b8665b31b8df67386899a5fec9fbbaf4` | 820 | A 測定木の作成 (親) |
| `run-mutation.sh` | `8315647714e5d37780d110046162a93878ec46d2fbaa43fdf58f3789a832eb69` | 1213 | 変異 harness の起動 (親) |
| `make-mutation-source.sh` | `fc66f2198e6cccc6a7dd5eb27221f5f13acc3d87f858b28ee1b9b4ee94c0d7c8` | 931 | 独立 clone の作成 (親) |
| `init-mutation-source-submodules.sh` | `176d289003069a1e29658654cbba6f481bffa56ff43ece968ce1d3afbe69e15f` | 614 | 独立 clone の submodule 初期化 (親) |
| `make_final_spec.py` | `41d62eba82a38dc758d750b5a066720f9935a427f3e4246e973bb002a04732d6` | 905 | probe 観測 node から final spec を作る (親) |


## `probe/t2766_adopt_analyze.py`

```python
#!/usr/bin/env python3
"""Offline T-2766 adoption adjacent-pair analysis; Python 3.10, standard library only.
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


def analyze_run(path, ledger, allowed_tips):
    meta = read_json(path / "run.json")
    result = {**meta, "id": path.name, "shards": [], "reasons": []}
    condition = meta.get("condition")
    if condition not in {"A", "B"} or not path.name.endswith(f"-{condition}"):
        result["reasons"].append("invalid/mismatched condition")
    if meta.get("tip_sha") not in allowed_tips.get(condition, set()):
        result["reasons"].append("tip_sha not in arm allowed tips")
    if not meta.get("tip_sha") or meta.get("tip_sha") != meta.get("tip_after"):
        result["reasons"].append("tip_sha differs from tip_after")
    if not isinstance(meta.get("tested_main"), str) or not meta["tested_main"]:
        result["reasons"].append("missing tested_main")
    if meta.get("verdict") != "child-green":
        result["reasons"].append("verdict != child-green")
    for field in ("dirty_lines_before", "dirty_lines_after"):
        if type(meta.get(field)) is not int or meta[field] != 0:
            result["reasons"].append(f"{field} != 0 (or missing)")
    if type(meta.get("rc")) is not int or meta["rc"] != 0:
        result["reasons"].append("run rc != 0")
    env = meta.get("env", {})
    if env.get("PYTHONDONTWRITEBYTECODE_SET") != "no":
        result["reasons"].append("bytecode env が測定走に渡っている")
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
                "verdict": "undetermined: insufficient-pairs",
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
    return {"class": category, "label": label,
            "verdict": {"i": "land", "ii": "no-land: below-threshold",
                        "iii": "no-land: effect-not-established"}[category],
            "subclasses": subclasses,
            "valid_pairs": 3, "medians": medians}


def pair_runs(runs):
    require(len(runs) <= 10, "measurement runs exceed 10-run cap")
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
        if any((
                type(r.get("pair_slot")) is not int or r["pair_slot"] != slot)
               for r in members):
            reasons.append("pair_slot differs from expected slot")
        if len(members) != 2 or {r.get("condition") for r in members} != {"A", "B"}:
            reasons.append("adjacent pair must contain one A and one B")
        if not all(r["valid"] for r in members):
            reasons.append("invalid run in pair")
        pair = {"id": i // 2 + 1, "expected_slot": slot, "expected_order": expected,
                "runs": [r["id"] for r in members],
                "order": [r.get("condition") for r in members],
                "main_moved": (len(members) == 2 and
                               members[0].get("tested_main") != members[1].get("tested_main")),
                "tips": [{"run": r["id"], "tip_sha": r.get("tip_sha"),
                          "tested_main": r.get("tested_main")} for r in members],
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
    require(len(paths) <= 10, "measurement runs exceed 10-run cap")
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


def analyze(runs_root, ledger_path, a_tips, b_tips):
    allowed_tips = {"A": set(a_tips), "B": set(b_tips)}
    require(all(allowed_tips.values()), "both arm tip sets are required")
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
            runs.append(analyze_run(path, ledger, allowed_tips))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            runs.append({"id": path.name, "condition": path.name[-1], "valid": False,
                         "reasons": [str(exc)], "shards": []})
    validate_run_times(runs)
    pairs = pair_runs(runs)
    for run in runs:
        for shard in run["shards"]:
            detail = shard.get("witness", {})
            sequences = detail.pop("worker_item_sequences", {})
            unit_sequences = detail.pop("worker_unit_sequences", {})
            detail["worker_sequences"] = {
                worker: {"item_count": len(items),
                         "unit_count": len(unit_sequences[worker]),
                         "first_two_units": unit_sequences[worker][:2]}
                for worker, items in sequences.items()
            }
    return {"allowed_tips": {arm: sorted(tips) for arm, tips in allowed_tips.items()}, "claims": CLAIMS, "runs": runs, "pairs": pairs,
            "decision": decision(pairs), "failure_counts_by_arm": {
                arm: sum(len(s.get("failures", [])) for r in runs if r["condition"] == arm
                         for s in r["shards"]) for arm in ("A", "B")},
            "notes": ["逐次の隣接対比較。別 job/allocation 間の比較である。",
                      "F = W - O は同じ shard の残差。固定費とは実証していない。",
                      "中央値率 10% は本 wave 独自の保守基準。3/3 は有意差判定ではない。",
                      "worker item 列は JUnit 出現順。全 worker の2個目を保証しない。",
                      "各 arm の許容 tip 集合・tested tip と終了後 HEAD の一致・clean を照合する。"]}


def markdown(data):
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = ["## T-2766 A/B analysis", "", *data["notes"], "", "## 走表", "",
             "| ID | 条件 | tip | tested_main | other_leaders | load1 | 投入 / 完了 | W_max | argmax | rc | session_dir_origin (参照しない) | 有効 / 理由 | 対の採否 / 理由 |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for run in data["runs"]:
        values = (run["id"], run["condition"], run.get("tip_sha"), run.get("tested_main"),
                  run.get("other_leaders"), run.get("load1"),
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
    lines += ["", "## 対表", "", "| 対 | 期待 slot / 順序 | 走順 | 有効 / 理由 | ΔW | r | D357 | main_moved | tips / tested_main |",
              "|---|---|---|---|---|---|---|---|---|"]
    for pair in data["pairs"]:
        values = (pair["id"], f'{pair["expected_slot"]} / {pair["expected_order"]}',
                  pair["runs"], "valid" if pair["valid"] else pair["reasons"],
                  pair.get("delta_W"), pair.get("r"), pair.get("D357"),
                  pair["main_moved"], pair["tips"])
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
                "condition": arm, "tip_sha": arm + "-tip", "tip_after": arm + "-tip",
                "tested_main": ("main-0", "main-1", "main-1", "main-1", "main-1", "main-2")[index - 1],
                "tip_before": arm + "-before", "verdict": "child-green",
                "dirty_lines_before": 0, "dirty_lines_after": 0, "copy_ok": True,
                "pair_slot": (index + 1) // 2, "rc": 0,
                "session_dir_origin": str(base / "deleted-origin"),
                "submitted_at": f"2026-09-19T{index:02d}:00:00+0900",
                "finished_at": f"2026-09-19T{index:02d}:30:00+0900",
                "session_dir": "session", "env": {
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
        analysis = analyze(runs, ledger_path, {"A-tip"}, {"B-tip"})
        require(all(r["valid"] for r in analysis["runs"]), "end-to-end valid runs")
        require([p["main_moved"] for p in analysis["pairs"]] == [True, False, True],
                "main_moved tracks tested_main independently of tip")
        require(all(p["valid"] and p["tips"][0]["tip_sha"] != p["tips"][1]["tip_sha"]
                    for p in analysis["pairs"]), "different arm tips remain valid pairs")
        require("worker_item_sequences" not in json.dumps(analysis)
                and "worker_unit_sequences" not in json.dumps(analysis), "compact sequences")
        require(analysis["decision"]["verdict"] == "land", "land verdict")
        # Each arm can advance independently between acceptance runs.
        moved_path = runs / "03-B" / "run.json"
        moved_original = read_json(moved_path)
        moved_path.write_text(json.dumps({**moved_original, "tip_sha": "B-new",
                                         "tip_after": "B-new"}))
        advanced = analyze(runs, ledger_path, {"A-tip"}, {"B-tip", "B-new"})
        require(all(r["valid"] for r in advanced["runs"]), "multiple allowed tips")
        moved_path.write_text(json.dumps(moved_original))
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
            ("tip_sha", "different-tip", "tip_sha not in arm allowed tips"),
            ("tip_sha", "A-tip", "tip_sha not in arm allowed tips"),
            ("verdict", "green", "verdict != child-green"),
            ("rc", 1, "run rc != 0"),
            ("tip_after", "different-tip", "tip_sha differs from tip_after"),
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
            damaged = analyze(runs, ledger_path, {"A-tip"}, {"B-tip"})
            require(not damaged["runs"][2]["valid"]
                    and any(reason in r for r in damaged["runs"][2]["reasons"]),
                    f"run exclusion: {field}={value}")
            require(damaged["decision"]["class"] == "undetermined", "invalid pair exclusion")
            require(reason in markdown(damaged), "exclusion reason in table")
        for field in ("tip_after", "tested_main", "verdict", "dirty_lines_before", "dirty_lines_after", "copy_ok"):
            meta = dict(original)
            del meta[field]
            run_path.write_text(json.dumps(meta))
            require(not analyze(runs, ledger_path, {"A-tip"}, {"B-tip"})["runs"][2]["valid"],
                    f"missing required field: {field}")
        run_path.write_text(json.dumps(original))
        require(not any(r["valid"] for r in analyze(runs, ledger_path, {"other-A"}, {"other-B"})["runs"]),
                "CLI tip never derived from first run")

        for filename in ("report.json", "junit.xml"):
            artifact = runs / "06-B" / "session" / "shard-2" / filename
            saved = artifact.read_bytes()
            artifact.unlink()
            damaged = analyze(runs, ledger_path, {"A-tip"}, {"B-tip"})
            require(damaged["decision"]["class"] == "undetermined"
                    and any(f"missing copied artifact: shard-2/{filename}" in reason
                            for reason in damaged["runs"][5]["reasons"]),
                    f"missing copied {filename}")
            artifact.write_bytes(saved)

        def fails_analysis(reason):
            try:
                analyze(runs, ledger_path, {"A-tip"}, {"B-tip"})
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
        require(all(r["valid"] for r in analyze(runs, ledger_path, {"A-tip"}, {"B-tip"})["runs"]),
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
                damaged = analyze(runs, ledger_path, {"A-tip"}, {"B-tip"})
                run = next(r for r in damaged["runs"] if r["id"] == run_id)
                require(not run["valid"] and "bytecode env が測定走に渡っている" in run["reasons"],
                        f"bytecode env exclusion: {run_id}={value!r}")
            env_path.write_text(json.dumps(saved_meta))

        (runs / "02-B").rename(runs / "08-B")
        fails_analysis("gap")
        (runs / "08-B").rename(runs / "02-B")
        (runs / "02-A").mkdir()
        fails_analysis("duplicate")
        (runs / "02-A").rmdir()
        for index in range(7, 14):
            (runs / f"{index:02d}-A").mkdir()
        fails_analysis("10-run cap")
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
        require(result["verdict"] == {"i": "land", "ii": "no-land: below-threshold",
                                     "iii": "no-land: effect-not-established"}[category],
                "decision verdict")
        require(subclass is None or subclass in result["subclasses"], "decision subclass")
    require(decision(pairs_for((1, 2)))["class"] == "undetermined", "insufficient pairs")
    def run_sequence(arms):
        return [{"id": f"{i:02d}-{arm}", "condition": arm, "tip_sha": "fixed",
                 "valid": True, "pair_slot": (i + 1) // 2,
                 "W_max": 100 if arm == "A" else 99}
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
    for run, slot in zip(wrong, (1, 1, 1, 1, 2, 2, 3, 3)):
        run["pair_slot"] = slot
    pairs = pair_runs(wrong)
    require([p["valid"] for p in pairs] == [False, True, True, True]
            and "順序違反" in pairs[0]["reasons"], "order violation then same-slot retry")
    wrong = run_sequence("ABABBAAB")
    for run, slot in zip(wrong, (1, 1, 2, 2, 2, 2, 3, 3)):
        run["pair_slot"] = slot
    pairs = pair_runs(wrong)
    require([p["valid"] for p in pairs] == [True, False, True, True],
            "even slot requires BA and retries BA")
    wrong = run_sequence("AB")
    wrong[1]["pair_slot"] = 2
    require("pair_slot differs" in " ".join(pair_runs(wrong)[0]["reasons"]),
            "pair_slot mismatch")
    wrong[1]["pair_slot"] = True
    require(not pair_runs(wrong)[0]["valid"], "pair_slot must be integer")
    del wrong[1]["pair_slot"]
    require(not pair_runs(wrong)[0]["valid"], "pair_slot is required")
    require(not pair_runs(run_sequence("A"))[0]["valid"], "incomplete adjacent pair")
    capped = run_sequence("AB" * 5)
    for run in capped:
        run["valid"] = False
    require(not any(p["valid"] for p in pair_runs(capped)), "10-run cap insufficient pairs")
    try:
        pair_runs(run_sequence("AB" * 6))
    except ValueError as exc:
        require("10-run cap" in str(exc), "10-run cap rejection")
    else:
        raise AssertionError("accepted more than 10 runs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-root", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--a-tips", help="comma-separated verified A tips")
    parser.add_argument("--b-tips", help="comma-separated verified B tips")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        try:
            selftest()
        except Exception as exc:
            print(f"FAIL: {type(exc).__name__}: {exc}")
            return 1
        print("PASS: synthetic JUnit/report/ledger, witness, pairs, decision branches; tip/dirty, order/retry/numbering/cap, copied artifacts, second unit/measured longest, isclose, submission times/overlap, bytecode env, arm tip sets/main_moved, compact output")
        return 0
    if any(v is None for v in (args.runs_root, args.ledger, args.out, args.a_tips, args.b_tips)):
        parser.error("--runs-root, --ledger, --out, --a-tips and --b-tips are required unless --selftest")
    try:
        data = analyze(args.runs_root, args.ledger,
                       {tip.strip() for tip in args.a_tips.split(",") if tip.strip()},
                       {tip.strip() for tip in args.b_tips.split(",") if tip.strip()})
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    write_analysis(data, args.out)
    print(data["decision"]["label"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


## `run-acceptance.sh`

```bash
#!/bin/bash
# 受入全走 (待ち手経由、A/B 共通)。引数: <arm A|B> <tag 例 01>。set -e は使わない。
# A = 採用前 main の木 (dev-wave-t2766-pairing-adopt-a)、B = wave 木 (採用後)。
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-adopt
ARM=${1:?arm}
TAG=${2:?tag}
case "$ARM" in
  A) WT=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2766-pairing-adopt-a; WAVE=dev-wave-t2766-pairing-adopt-a ;;
  B) WT=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2766-pairing-adopt; WAVE=dev-wave-t2766-pairing-adopt ;;
  *) echo "bad arm $ARM"; exit 90 ;;
esac
R="$J/runs/$TAG-$ARM"
mkdir -p "$R"
export IZANAGI_WAVE_LEASE_DIR=/work/1/SFC/tanab/dev-wave-jobs/land-lease
export IZANAGI_ACCEPTANCE_SHARDS=3
unset PYTHONDONTWRITEBYTECODE
unset IZANAGI_ACCEPTANCE_PAIRING_V1
echo $$ > "$R/acceptance.pid"
cd "$WT" || exit 90
git rev-parse main > "$R/main-at-launch.txt"
git rev-parse HEAD > "$R/tip-before.txt"
git status --porcelain --untracked-files=all --ignore-submodules=none | grep -vc "^?? output/pegasus-dispatch/" > "$R/dirty-before.txt"
ps -eo args | grep "[d]ev_wave_wait.py" | grep " acceptance" | grep -vc "dev-wave-t2766-pairing-adopt" > "$R/other-leaders.txt"
cut -d' ' -f1 /proc/loadavg > "$R/load1.txt"
env | grep -c '^PYTHONDONTWRITEBYTECODE=' > "$R/bytecode-env-set.txt"
date '+%Y-%m-%dT%H:%M:%S%z' > "$R/started.txt"
python3 tools/dev_wave_wait.py acceptance \
  --wave "$WAVE" \
  --lease-dir /work/1/SFC/tanab/dev-wave-jobs/land-lease \
  --receipt-file "$R/acceptance-receipt.json" \
  --log-file "$R/acceptance-child.log" \
  -- python3 tools/run_tests.py \
  > "$R/acceptance.log" 2>&1
rc=$?
date '+%Y-%m-%dT%H:%M:%S%z' > "$R/finished.txt"
# 成功後に保持される lease (land 用、TTL 40 分) は次の同 wave の受入 claim を claim-self-unverified で落とすので、
# 取得済み ("lease is held") の走だけ終端で release する (未取得の走は release しない、DW-O27)。
if grep -q "lease is held" "$R/acceptance.log"; then
  python3 tools/wave_land_window.py release --lease-dir /work/1/SFC/tanab/dev-wave-jobs/land-lease --wave "$WAVE" > "$R/lease-release.json" 2>&1
  echo "$?" > "$R/lease-release.rc"
fi
ps -eo args | grep "[d]ev_wave_wait.py" | grep " acceptance" | grep -vc "dev-wave-t2766-pairing-adopt" > "$R/other-leaders-at-finish.txt"
cut -d' ' -f1 /proc/loadavg > "$R/load1-at-finish.txt"
git rev-parse HEAD > "$R/tip-after.txt"
git status --porcelain --untracked-files=all --ignore-submodules=none | grep -vc "^?? output/pegasus-dispatch/" > "$R/dirty-after.txt"
echo "$rc" > "$R/acceptance.done"
exit "$rc"
```


## `gate-series.sh`

```bash
#!/bin/bash
# 受入 A/B 系列 (待ち手経由) の門番 + 直列投入。順序 A,B / B,A / A,B (対 4・5 は無効対の追加用)。
# 門番: 他 session の受入 leader ≤ 1 かつ 1 分負荷 < 60 が 2 周連続 → 乱数 0〜45 秒 → 再カウントで ≤ 1 なら投入。周期 100〜140 秒乱数。
# 自 wave の待ち手が残っていれば投入しない (同一 worktree の dispatch は直列)。
# 終端: 各走 rc=0 → run.json を書いて次へ。競走型 (claim / merge / postcheck) → 走 dir を aborts へ退避して同じ走を再投入 (上限 3)。
#       それ以外の赤 → run.json を書いて停止 (親が DW-O18 で判定)。上限 12 時間。set -e は使わない。
# usage: gate-series.sh <start index 1..10> <end index>
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-adopt
SELF=dev-wave-t2766-pairing-adopt
PLAN=("01 A 1" "02 B 1" "03 B 2" "04 A 2" "05 A 3" "06 B 3" "07 A 4" "08 B 4" "09 B 5" "10 A 5")
START=${1:-1}
END=${2:-6}
echo $$ > "$J/series.pid"
rm -f "$J/series.done"
LOG="$J/series.log"
deadline=$(( $(date +%s) + 12*3600 ))
count_leaders() { ps -eo args | grep "[d]ev_wave_wait.py" | grep " acceptance" | grep -vc "$SELF"; }
count_self() { ps -eo args | grep "[d]ev_wave_wait.py" | grep " acceptance" | grep -c "$SELF"; }
gate_wait() {
  streak=0
  while : ; do
    now=$(date +%s)
    leaders=$(count_leaders)
    selfn=$(count_self)
    read l1 l5 _ < /proc/loadavg
    ok_load=$(awk -v x="$l1" 'BEGIN{print (x<60)?1:0}')
    pigz=$(ps -eo comm | grep -c '^pigz$')
    if [ "$leaders" -le 1 ] && [ "$ok_load" -eq 1 ] && [ "$selfn" -eq 0 ]; then streak=$((streak+1)); else streak=0; fi
    echo "$(date '+%H:%M:%S') gate leaders=$leaders self=$selfn load1=$l1 load5=$l5 pigz=$pigz streak=$streak" >> "$LOG"
    if [ "$streak" -ge 2 ]; then
      sleep $(( RANDOM % 46 ))
      leaders=$(count_leaders)
      selfn=$(count_self)
      echo "$(date '+%H:%M:%S') recount leaders=$leaders self=$selfn" >> "$LOG"
      if [ "$leaders" -le 1 ] && [ "$selfn" -eq 0 ]; then return 0; fi
      streak=0
    fi
    if [ "$now" -ge "$deadline" ]; then echo "$(date '+%H:%M:%S') DEADLINE" >> "$LOG"; return 98; fi
    sleep $(( 100 + RANDOM % 41 ))
  done
}
i=$START
while [ "$i" -le "$END" ]; do
  set -- ${PLAN[$((i-1))]}
  TAG=$1; ARM=$2; SLOT=$3
  attempt=0
  while : ; do
    attempt=$((attempt+1))
    gate_wait
    g=$?
    if [ "$g" -ne 0 ]; then echo "$g" > "$J/series.done"; exit "$g"; fi
    echo "$(date '+%H:%M:%S') GO run=$TAG arm=$ARM slot=$SLOT attempt=$attempt" >> "$LOG"
    bash "$J/run-acceptance.sh" "$ARM" "$TAG"
    rc=$(cat "$J/runs/$TAG-$ARM/acceptance.done" 2>/dev/null || echo 99)
    cls=$(grep -o '"classification":"[a-z-]*"' "$J/runs/$TAG-$ARM/acceptance.log" | tail -1)
    echo "$(date '+%H:%M:%S') run=$TAG arm=$ARM rc=$rc $cls" >> "$LOG"
    if [ "$rc" -eq 0 ]; then
      python3 "$J/write_run_json.py" "$J/runs/$TAG-$ARM" "$SLOT" >> "$LOG" 2>&1
      break
    fi
    case "$cls" in
      *postcheck*|*merge*|*receipt-main-moved*|*claim*)
        mkdir -p "$J/aborts"
        mv "$J/runs/$TAG-$ARM" "$J/aborts/$TAG-$ARM.attempt$attempt"
        if [ "$attempt" -ge 3 ]; then echo "$rc" > "$J/series.done"; exit "$rc"; fi
        sleep 60
        continue ;;
    esac
    python3 "$J/write_run_json.py" "$J/runs/$TAG-$ARM" "$SLOT" >> "$LOG" 2>&1
    echo "$rc" > "$J/series.done"
    exit "$rc"
  done
  i=$((i+1))
done
echo 0 > "$J/series.done"
exit 0
```


## `write_run_json.py`

```python
"""親専用: 受入 1 走の記録 dir (runs/<TAG>-<ARM>/) から run.json を書き、session の 3 shard 成果物を複製する。
使い方: python3 write_run_json.py <runs dir> <pair_slot>
receipt が無い / rc≠0 の走も run.json を書く (集計器が無効走として扱う)。
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path


def read(path, default=None):
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return default


def main() -> int:
    run_dir = Path(sys.argv[1]).resolve()
    pair_slot = int(sys.argv[2])
    tag, arm = run_dir.name.rsplit("-", 1)
    receipt = {}
    receipt_path = run_dir / "acceptance-receipt.json"
    if receipt_path.is_file():
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    session_root = None
    log = run_dir / "acceptance-child.log"
    if log.is_file():
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("IZANAGI_ACCEPTANCE_SHARD_ARTIFACTS_V1 "):
                session_root = json.loads(line.split(" ", 1)[1])["session_root"]
    copy_ok = False
    sums = []
    if session_root and Path(session_root).is_dir():
        dest = run_dir / "session"
        copy_ok = True
        for shard in ("shard-0", "shard-1", "shard-2"):
            src = Path(session_root) / shard
            (dest / shard).mkdir(parents=True, exist_ok=True)
            for name in ("junit.xml", "report.json"):
                s = src / name
                if not s.is_file():
                    copy_ok = False
                    continue
                d = dest / shard / name
                shutil.copyfile(s, d)
                digest = hashlib.sha256(d.read_bytes()).hexdigest()
                sums.append(f"{digest}  {shard}/{name}")
        (dest / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")
    rc_text = read(run_dir / "acceptance.done", "")
    rc = int(rc_text) if rc_text.lstrip("-").isdigit() else None
    bytecode_set = read(run_dir / "bytecode-env-set.txt", "1")
    meta = {
        "run": tag,
        "condition": arm,
        "pair_slot": pair_slot,
        "tip_sha": receipt.get("tested_tip") or read(run_dir / "tip-after.txt"),
        "tip_before": read(run_dir / "tip-before.txt"),
        "tip_after": read(run_dir / "tip-after.txt"),
        "tested_main": receipt.get("tested_main"),
        "main_sha_at_launch": read(run_dir / "main-at-launch.txt"),
        "submitted_at": read(run_dir / "started.txt"),
        "finished_at": read(run_dir / "finished.txt"),
        "session_dir": "session",
        "session_dir_origin": session_root,
        "copy_ok": copy_ok,
        "env": {
            "IZANAGI_ACCEPTANCE_SHARDS": "3",
            "PYTHONDONTWRITEBYTECODE_SET": "no" if bytecode_set == "0" else "yes",
        },
        "other_leaders": int(read(run_dir / "other-leaders.txt", "0") or 0),
        "load1": float(read(run_dir / "load1.txt", "0") or 0),
        "other_leaders_at_finish": int(read(run_dir / "other-leaders-at-finish.txt", "-1") or -1),
        "load1_at_finish": float(read(run_dir / "load1-at-finish.txt", "-1") or -1),
        "rc": rc,
        "verdict": receipt.get("verdict"),
        "child_rc": receipt.get("child_rc"),
        "red_nodeids": receipt.get("red_nodeids"),
        "dirty_lines_before": int(read(run_dir / "dirty-before.txt", "0") or 0),
        "dirty_lines_after": int(read(run_dir / "dirty-after.txt", "0") or 0),
        "receipt_file": str(receipt_path) if receipt else None,
    }
    (run_dir / "run.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: meta[k] for k in ("run", "condition", "tip_sha", "tested_main", "rc", "verdict", "copy_ok")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```


## `make-a-worktree.sh`

```bash
#!/bin/bash
# 親専用: A 測定木 (採用前 main) を作る。branch 名は待ち手の --wave 末尾一致に合わせる。
# usage: make-a-worktree.sh <base-sha>
set -u
BASE=${1:?base sha (local main)}
MAIN=/work/1/SFC/tanab/izanagi
A="$MAIN/.claude/worktrees/dev-wave-t2766-pairing-adopt-a"
cd "$MAIN" || exit 2
git worktree add -b "worktree-dev-wave-t2766-pairing-adopt-a" "$A" "$BASE"
rc=$?
echo "worktree add rc=$rc"
if [ "$rc" -ne 0 ]; then exit "$rc"; fi
python3 "$MAIN/tools/dev_wave_submodule_init.py" --worktree "$A"
echo "submodule init rc=$?"
ls "$A/external/ccbench" | head -3
git -C "$MAIN" worktree lock "$A" --reason "dev-wave-t2766-pairing-adopt A measurement tree"
echo "lock rc=$?"
git -C "$A" rev-parse HEAD
git -C "$A" status --porcelain --untracked-files=all --ignore-submodules=none | wc -l
```


## `run-mutation.sh`

```bash
#!/bin/bash
# 親専用: 変異 harness を独立 clone (D1009) の固定 commit で走らせる。detach.sh 経由で呼ぶ。
# usage: run-mutation.sh <tag> <spec> <spec-sha256> <wrapper-attempt> <commit>
set -u
TAG=${1:?tag}
SPEC=${2:?spec}
SHA=${3:?spec sha256}
ATT=${4:?wrapper attempt}
COMMIT=${5:?commit}
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-adopt
SRC="$J/mutation-source"
mkdir -p "$J/mutation-scratch"
echo $$ > "$J/mutation-$TAG.pid"
rm -f "$J/mutation-$TAG.done"
cd "$SRC" || { echo 90 > "$J/mutation-$TAG.done"; exit 90; }
export IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600
export IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600
unset PYTHONDONTWRITEBYTECODE
python3 tools/mutation_worktree.py --source-repo "$SRC" --commit "$COMMIT" \
  --scratch-root "$J/mutation-scratch" \
  --spec "$SPEC" --expected-spec-sha256 "$SHA" \
  --out "$J/mutation-$TAG-results.json" \
  --attempt-out "$J/mutation-$TAG-attempts.json" --wrapper-attempt "$ATT" \
  --runner-mode dispatch --detached \
  -- python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_acceptance_schedule_order.py -q -rf \
  > "$J/mutation-$TAG.log" 2>&1
rc=$?
echo "$rc" > "$J/mutation-$TAG.done"
exit "$rc"
```


## `make-mutation-source.sh`

```bash
#!/bin/bash
# 親専用: 変異 harness 用の独立 clone (D1009) を作り、main を対象 commit に固定して submodule を初期化する。
# usage: make-mutation-source.sh <target-commit>
set -u
TARGET=${1:?target commit}
MAIN=/work/1/SFC/tanab/izanagi
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-adopt
SRC="$J/mutation-source"
if [ -e "$SRC" ]; then echo "exists: $SRC"; exit 2; fi
git clone --local --no-checkout "$MAIN" "$SRC" || exit 3
cd "$SRC" || exit 4
git fetch -q "$MAIN" refs/heads/worktree-dev-wave-t2766-pairing-adopt || exit 5
git update-ref refs/heads/main "$TARGET" || exit 6
git checkout -q main || exit 7
echo "HEAD=$(git rev-parse HEAD)"
python3 "$SRC/tools/dev_wave_submodule_init.py" --worktree "$SRC"
echo "submodule init rc=$?"
git submodule status --recursive | head -5
ls "$SRC/external/ccbench" | head -3
git status --porcelain --untracked-files=all --ignore-submodules=none | wc -l
```


## `init-mutation-source-submodules.sh`

```bash
#!/bin/bash
# 親専用: 独立 clone の submodule を共有 repo の .git/modules から (fetch なしで) 初期化する。
set -u
MAIN=/work/1/SFC/tanab/izanagi
SRC=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-adopt/mutation-source
cd "$SRC" || exit 2
git submodule init || exit 3
git config submodule.external/ccbench.url "$MAIN/.git/modules/external/ccbench" || exit 4
git -c protocol.file.allow=always submodule update --init --recursive || exit 5
git submodule status --recursive
ls "$SRC/external/ccbench" | head -3
git status --porcelain --untracked-files=all --ignore-submodules=none | wc -l
```


## `make_final_spec.py`

```python
"""親専用: probe 走の観測 node を期待集合 (KILLED) にして final spec を書く。"""
import hashlib
import json

J = "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-adopt"
probe = json.load(open(J + "/mutation-probe-results.json"))
spec = json.load(open(J + "/mutation-spec-probe.json"))
observed = {r["id"]: sorted(r["failed_nodes"]) for r in probe["mutations"]}
for m in spec["mutations"]:
    m["expected_nodes"] = observed[m["id"]]
    m["expected_status"] = "KILLED"
    assert m["expected_nodes"], m["id"]
with open(J + "/mutation-spec-final.json", "w") as f:
    f.write(json.dumps(spec, ensure_ascii=False, indent=2) + "\n")
with open(J + "/mutation-expected-nodes.json", "w") as f:
    json.dump(observed, f, ensure_ascii=False, indent=2)
print(hashlib.sha256(open(J + "/mutation-spec-final.json", "rb").read()).hexdigest())
print({k: len(v) for k, v in observed.items()})
```
