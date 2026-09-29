"""Fresh Claude session for one silo policy contrast proposal opportunity."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

try:
    from .b5_llm_parent import classify_exit, FORBIDDEN, OUTAGE_RETRY_S
except ImportError:  # direct script execution
    from b5_llm_parent import classify_exit, FORBIDDEN, OUTAGE_RETRY_S

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from orchestrator.campaign.silo_policy_contrast import ContrastLedger

ALLOWED = ("Bash(python3 tools/silo_policy_contrast_round.py *)", "Agent", "Read", "Write")


def run_opportunity(ledger_root: Path, a: int, out: Path, *, settings: Path, model: str,
                    checkout: Path, spawn=subprocess.run, sleep=time.sleep) -> str:
    """Run one fresh session per attempt; preserve artifacts across 429 and failures."""
    if any(key in os.environ for key in FORBIDDEN):
        raise RuntimeError("forbidden parent environment")
    ledger = ContrastLedger(ledger_root)
    if ledger.header["arm"] not in {"llm-cpp", "llm-ir"}:
        raise ValueError("parent requires LLM arm")
    out.mkdir(parents=True, exist_ok=True)
    instructions = Path(__file__).with_suffix(".md").read_text()
    failures = launches = 0
    while True:
        launches += 1
        attempt = out / f"attempt-{launches:04d}"
        attempt.mkdir(exist_ok=False)
        prompt = (instructions + f"\n\nledger={ledger_root.resolve()}\na={a}\nout={out.resolve()}\n"
                  f"form={ledger.header['form']}\n")
        (attempt / "prompt.md").write_text(prompt)
        argv = ["claude", "-p", "--output-format", "json", "--settings", str(settings),
                "--model", model, "--allowedTools", *ALLOWED]
        with (attempt / "prompt.md").open("rb") as inp, (attempt / "out.json").open("wb") as stdout, \
                (attempt / "err.log").open("wb") as stderr:
            completed = spawn(argv, cwd=checkout, stdin=inp, stdout=stdout, stderr=stderr,
                              check=False)
        status = classify_exit(attempt / "out.json", completed.returncode)
        (attempt / "exit.json").write_text(json.dumps({"status": status, "rc": completed.returncode,
            "at": datetime.now(timezone.utc).isoformat()}) + "\n")
        if status == "outage":
            ContrastLedger(ledger_root).append("opportunity-end", a=a, outcome="outage",
                                               role_attempts=launches)
            sleep(OUTAGE_RETRY_S)
            continue
        if status == "success":
            events = [e for e in ContrastLedger(ledger_root).events if
                      e["kind"] == "opportunity-end" and e["a"] == a]
            if events:
                return events[-1]["outcome"]
            # A normal exit without proposal or explicit rejection is an empty proposal.
            ContrastLedger(ledger_root).append("opportunity-end", a=a, outcome="empty", role_attempts=launches)
            return "empty"
        failures += 1
        if failures > 2:
            ContrastLedger(ledger_root).append("opportunity-end", a=a, outcome="role-failure", role_attempts=launches)
            ContrastLedger(ledger_root).append("series-end", reason="unclassified-missing")
            return "role-failure"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ledger", type=Path, required=True)
    p.add_argument("--a", type=int, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--settings", type=Path, required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--checkout", type=Path, required=True)
    args = p.parse_args(argv)
    print(run_opportunity(args.ledger, args.a, args.out, settings=args.settings,
                          model=args.model, checkout=args.checkout))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
