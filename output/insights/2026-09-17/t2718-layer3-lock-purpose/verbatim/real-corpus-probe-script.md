# 実 corpus probe の実行形 (逐語、Codex role=author 作。repo へは入れず親が repo 外で実行した)

```python
"""Read-only T-2718 probe; run a relocated copy with PYTHONPATH set to the repo.

Arguments are repeated triples: <out_json> <campaign_dir> <output_root>.
The parent runs this probe; it never renders a report into the campaign.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import traceback

from orchestrator.campaign import layer3_report


def _error(exc: BaseException) -> dict:
    cause = exc.__cause__
    return {
        "ok": False,
        "type": type(exc).__name__,
        "message": str(exc),
        "cause": None if cause is None else f"{type(cause).__name__}: {cause}",
        "traceback": "".join(traceback.format_exception(exc)),
    }


def _hashes(campaign: Path) -> dict:
    result = {}
    for relative in ("campaign.lock", "runs/wal.jsonl"):
        try:
            result[relative] = {
                "ok": True,
                "sha256": hashlib.sha256((campaign / relative).read_bytes()).hexdigest(),
            }
        except Exception as exc:
            result[relative] = _error(exc)
    return result


def _probe(campaign: Path, output_root: Path) -> dict:
    result = {"campaign_dir": str(campaign), "output_root": str(output_root)}
    result["before"] = _hashes(campaign)
    for purpose in layer3_report.CampaignReadPurpose:
        try:
            decoded = layer3_report._read_campaign_lock(
                campaign / "campaign.lock", purpose=purpose,
            )
            reading = {"ok": True, "type": type(decoded).__name__}
            if purpose is layer3_report.CampaignReadPurpose.HISTORICAL_RAW:
                reading["identity_keys"] = list(decoded.identity)
                reading["recorded_contract_loader_relative_paths_length"] = (
                    None if decoded.authority is None else
                    len(decoded.authority.recorded_contract_loader_relative_paths)
                )
            result[purpose.value] = reading
        except Exception as exc:
            result[purpose.value] = _error(exc)
    try:
        report = layer3_report.build_report(
            campaign, generated_from_head="0" * 40, output_root=output_root,
        )
        result["build_report"] = {"ok": True, "schema_version": report["schema_version"]}
    except Exception as exc:
        result["build_report"] = _error(exc)
    result["after"] = _hashes(campaign)
    result["unchanged"] = {
        relative: (
            result["before"][relative]["sha256"] == result["after"][relative]["sha256"]
            if result["before"][relative]["ok"] and result["after"][relative]["ok"]
            else None
        )
        for relative in result["before"]
    }
    return result


def main(argv: list[str]) -> int:
    if not argv or len(argv) % 3:
        print("usage: probe <out_json> <campaign_dir> <output_root> [...]", file=sys.stderr)
        return 2
    triples = [tuple(map(Path, argv[i:i + 3])) for i in range(0, len(argv), 3)]
    failed = False
    for out_json, campaign, output_root in triples:
        try:
            # Protect every input campaign, including against an output symlink.
            if any(out_json.resolve().is_relative_to(item[1].resolve()) for item in triples):
                raise ValueError("out_json must be outside every campaign directory")
            try:
                result = _probe(campaign, output_root)
            except Exception as exc:
                result = _error(exc)
            out_json.write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
            )
        except Exception as exc:
            # Even an unwritable output must not prevent probing later triples.
            failed = True
            print(json.dumps({"out_json": str(out_json), **_error(exc)}, ensure_ascii=False),
                  file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```
