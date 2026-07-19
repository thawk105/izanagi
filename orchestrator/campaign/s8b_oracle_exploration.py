# -*- coding: utf-8 -*-
"""generic pipeline の 8b 探索成果を隔離 artifact として包装する入口。"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Optional

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    _ORCHESTRATOR = Path(__file__).resolve().parent.parent
    if str(_ORCHESTRATOR) not in sys.path:
        sys.path.insert(0, str(_ORCHESTRATOR))

from campaign import s8b_oracle_artifacts as _artifacts  # noqa: E402
from campaign.layout import (  # noqa: E402
    ExplorationCampaignLayout,
    exploration_campaign_layout,
)


def package_exploration_artifact(
    *, layout: ExplorationCampaignLayout, artifact_role: str,
    extime_s: int, reps: int, payload: Mapping,
) -> _artifacts.ExplorationArtifact:
    """探索を実行・判定せず、既存 payload を隔離 envelope へ create-only 包装する。"""
    if type(layout) is not ExplorationCampaignLayout:
        raise _artifacts.OracleArtifactTypeError(
            "package_exploration_artifact は ExplorationCampaignLayout exact type のみ受理する")
    campaign_id = os.path.basename(layout.root)
    document = _artifacts.validate_exploration_artifact({
        "schema_version": _artifacts.EXPLORATION_ARTIFACT_SCHEMA,
        "artifact_role": artifact_role,
        "campaign_id": campaign_id,
        "measurement_hint": {"extime_s": extime_s, "reps": reps},
        "payload": dict(payload) if isinstance(payload, Mapping) else payload,
    })
    try:
        encoded = (json.dumps(
            document, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False,
        ) + "\n").encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise _artifacts.OracleArtifactTypeError(
            f"exploration artifact を JSON 化できない: {exc}") from exc
    layout.ensure()
    output = Path(layout.reports_dir) / f"{artifact_role}.exploration.json"
    with output.open("xb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    return document


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--campaign-id", required=True)
    parser.add_argument(
        "--role", dest="artifact_role", choices=sorted(_artifacts.EXPLORATION_ARTIFACT_ROLES),
        required=True,
    )
    parser.add_argument("--extime-s", type=int, required=True)
    parser.add_argument("--reps", type=int, required=True)
    parser.add_argument("--input", type=Path, required=True)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload = _artifacts.strict_load_json_object(args.input)
        layout = exploration_campaign_layout(
            args.campaign_id, output_root=args.output_root,
        )
        package_exploration_artifact(
            layout=layout,
            artifact_role=args.artifact_role,
            extime_s=args.extime_s,
            reps=args.reps,
            payload=payload,
        )
    except (OSError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
