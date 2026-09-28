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
    from vhash_forwarding_model.scenarios import NAMES, scenario
else:
    from . import SCHEMA
    from .model import explore
    from .scenarios import NAMES, scenario


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--scenario", choices=NAMES, default="S8")
    p.add_argument("--protocol", choices=("v0", "v1"), default="v1")
    p.add_argument("--fault", choices=("U1v", "U1f", "U2", "U3a", "U3b", "U4", "U5", "U6"),
                   default="")
    a = p.parse_args(argv)
    initial, witness = scenario(a.scenario)
    result = explore(initial, a.protocol, a.fault, witness)
    bounds = {"keys": len({v.key for v in initial.versions}),
              "transactions": len(initial.txns), "operations_per_transaction": 3,
              "versions_per_key": 3, "K": initial.k,
              "timestamps": sorted({v.wts for v in initial.versions} |
                                   {t.start for t in initial.txns}),
              "atomicity": "one key sequence observation, one version field write, or local state plus at most one shared write"}
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
            {**asdict(step), "reason": trace["reason"] if key == "counterexample"
             and i == len(steps) - 1 else {"rule": step.operation}}
            for i, step in enumerate(steps)
        ]
    payload = {"schema": SCHEMA, "scenario": a.scenario, "protocol": a.protocol,
               "faults": [a.fault] if a.fault else [], "bounds": bounds, **result}
    a.out.write_text(json.dumps(payload, default=encode, ensure_ascii=False, indent=2) + "\n")
    return payload


if __name__ == "__main__":
    main()
