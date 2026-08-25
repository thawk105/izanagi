# -*- coding: utf-8 -*-
"""段 6 候補提出の前提関門 adapter。

この adapter を呼ぶ operational caller は 0 件であり、段 6 の候補提出経路は
未実装である。
"""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar, NoReturn

from orchestrator.tests import calibration_freeze_authority_contract as contract


class Stage6CandidateSubmissionBlocked(RuntimeError):
    """段 6 候補提出前の fail-closed 終端に共通する基底例外。"""

    reason_code: ClassVar[str]


class Stage6FixtureObligationGateRejected(Stage6CandidateSubmissionBlocked):
    """段 0 から繰り越した fixture 義務が未解消である。"""

    reason_code = "stage0-fixture-obligation-gate-rejected"


class Stage6PolicyUnresolvedAfterFixtureObligations(
    Stage6CandidateSubmissionBlocked
):
    """Fixture 義務通過後も段 6 policy が未解決である。"""

    reason_code = "stage0-fixture-obligations-passed-stage6-policy-unresolved"


def require_stage6_candidate_submission_ready(
    fixture_root: Path = contract.FIXTURE_ROOT,
    design_doc: Path = contract.DESIGN_DOC,
) -> NoReturn:
    """段 6 候補提出の前提関門を検査し、現在は必ず fail-closed にする。

    この adapter を呼ぶ operational caller は 0 件であり、段 6 の候補提出経路は
    未実装である。
    """

    try:
        contract.require_stage0_fixture_obligations_discharged(
            fixture_root=fixture_root,
            design_doc=design_doc,
        )
    except contract.ContractError as exc:
        raise Stage6FixtureObligationGateRejected(
            "stage 6 candidate submission fixture obligation gate rejected: "
            f"{exc}"
        ) from exc

    raise Stage6PolicyUnresolvedAfterFixtureObligations(
        "stage 6 candidate submission is blocked: "
        "CFAB-STAGE6-POLICY-PREDICATE is unresolved"
    )
