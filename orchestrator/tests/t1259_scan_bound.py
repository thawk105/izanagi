"""D2148 項 12 / F945: production の 30.0 は不変、この候補値は受入 fixture の module snapshot 1 回分にだけ効く。"""
from pathlib import Path
from typing import Any

from tools.pegasus.probes import t1259_qsub_env_delivery_probe as probe

FIXTURE_GIT_TIMEOUT_SECONDS: float = 120.0


def fixture_repo_snapshot(repo_root: Path) -> dict[str, Any]:
    return probe._repo_snapshot(
        repo_root, git_timeout_seconds=FIXTURE_GIT_TIMEOUT_SECONDS
    )
