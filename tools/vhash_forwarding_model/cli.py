"""Run a finite scenario and write its complete bounded-search report."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from vhash_forwarding_model import SCHEMA
    from vhash_forwarding_model.model import explore
    from vhash_forwarding_model.scenarios import NAMES, GC_NAMES, danger_witness, scenario
else:
    from . import SCHEMA
    from .model import explore
    from .scenarios import NAMES, GC_NAMES, danger_witness, scenario


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--scenario", choices=NAMES + GC_NAMES, default="S8")
    p.add_argument("--protocol", choices=("v0", "v1"), default="v1")
    p.add_argument("--fault", choices=("U1v", "U1f", "U2", "U3a", "U3b", "U4", "U5", "U6",
                                       "UG1", "UG2", "UG2r", "UG3", "UF1"),
                   default="")
    p.add_argument("--o1", action="store_true")
    p.add_argument("--pressure", choices=("off", "self"), default="off")
    p.add_argument("--revert-after-confirm", action="store_true")
    p.add_argument("--max-seconds", type=float, default=120.0)
    a = p.parse_args(argv)
    initial, witness = scenario(a.scenario)
    danger = danger_witness(a.scenario) if a.scenario in ("S3", "S8") or a.scenario.startswith("G") else None
    result = explore(initial, a.protocol, a.fault, witness, o1=a.o1,
                     max_seconds=a.max_seconds, danger=danger,
                     pressure=a.pressure, revert_after_confirm=a.revert_after_confirm)
    if danger is None:
        result["danger"] = None
    counts = {key: sum(v.key == key for v in initial.versions) for key in {v.key for v in initial.versions}}
    bounds = {"keys": len(counts),
              "transactions": len(initial.txns),
              "operations_per_transaction": {t.id: len(t.ops) for t in initial.txns},
              "versions_per_key": counts, "K": initial.k,
              "timestamps": sorted({v.wts for v in initial.versions} |
                                   {t.start for t in initial.txns}),
              "atomicity": "one key sequence observation, one version field write, or local state plus at most one shared write"}
    population = {"versions": [asdict(v) for v in initial.versions],
                  "transactions": [asdict(t) for t in initial.txns]}
    limits = {"keys": 2 if a.scenario in NAMES else 3, "transactions": 3,
              "operations_per_transaction": 3,
              "operations_including_WAIT": 4,
              "versions_per_key": 3, "K": [1, 2]}
    def encode(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        raise TypeError(type(obj))
    for key in ("counterexample", "witness"):
        trace = result[key]
        if trace is None:
            continue
        steps = trace["steps"]
        trace["steps"] = [
            {**asdict(step), **({"reason": trace["reason"]} if key == "counterexample"
             and i == len(steps) - 1 else {})}
            for i, step in enumerate(steps)
        ]
    payload = {"schema": SCHEMA, "scenario": a.scenario, "protocol": a.protocol,
               "faults": [a.fault] if a.fault else [], "o1": a.o1,
               "pressure": a.pressure, "revert_after_confirm": a.revert_after_confirm,
               "bounds": bounds, "limits": limits, "population": population, **result}
    a.out.write_text(json.dumps(payload, default=encode, ensure_ascii=False, indent=2) + "\n")
    return payload


if __name__ == "__main__":
    main()
