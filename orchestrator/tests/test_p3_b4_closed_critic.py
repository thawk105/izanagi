# -*- coding: utf-8 -*-
"""Tests for the P3 B-4 route-local closed critic candidate.

Every rejection has a nearby admitted control.  The identity controls use real
policy-admitted synthetic WAL fixtures and call ``make_critic_digest`` for both
arms; no synthetic string stands in for the digest itself.
"""
from __future__ import annotations

import contextlib
from dataclasses import dataclass, replace
import hashlib
import io
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest.mock

import pytest

_HERE = Path(__file__).resolve().parent
_ORCH = _HERE.parent
sys.path.insert(0, str(_ORCH.parent))

from orchestrator.campaign import ident, p3_b4_closed_critic as C  # noqa: E402
from orchestrator.campaign import p3_b4_admission_record as A  # noqa: E402
from orchestrator.campaign import p3_b4_launcher as B4L  # noqa: E402
from orchestrator.campaign import claude_projected_provider as P  # noqa: E402
from orchestrator.campaign import p3_s4_loop as L, source_digest, wal  # noqa: E402
from orchestrator.campaign import (  # noqa: E402
    p3_s4_loop_trigger_gating as TRIGGER_LOOP,
    site_policy,
)
from orchestrator.campaign.artifact_admission import (  # noqa: E402
    CampaignReadPurpose,
    require_admitted_campaign,
)
from orchestrator.campaign.build_admission import (  # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.layout import CampaignLayout  # noqa: E402
from orchestrator.campaign.model import Genome  # noqa: E402
from orchestrator.campaign.pipeline import variant_id  # noqa: E402
from orchestrator.campaign.source_digest import (  # noqa: E402
    EMPTY_TRACKED_DIFF_SHA256,
    SourceEvidence,
)
from campaign_lock_test_support import build_v2_lock  # noqa: E402
import commit_receipt_support  # noqa: E402
from p3_b4_proposal_binding_support import (  # noqa: E402
    issue_proposal_binding_fixture,
    proposal_document,
)


_G = Genome("silo", {
    "NO_WAIT_LOCKING_IN_VALIDATION": 1,
    "NO_WAIT_OF_TICTOC": 0,
    "WAL": 0,
    "BACK_OFF": 1,
    "BACKOFF_FIXED": 20,
})
_DECISION_OBJECT = {
    "attribution": "fixture attribution",
    "recommend": "fixture recommendation",
    "avoid": "fixture avoidance",
    "uncertainty": "fixture uncertainty",
    "reverse_recommended": False,
}
_ADMISSION_MODEL = "claude-opus-5"
_ADMISSION_SCHEMA_VERSION = "p3-b4-prerun-admission/v1"
_PREREGISTRATION_REPOSITORY_PATH = (
    "docs/phase3-b4-reflux-ablation-preregistration.md"
)
_REQUIRED_ADMISSION_RECORD_REPOSITORY_PATH_BY_DRIVER = {
    "base": "docs/phase3-b4-reflux-ablation-admission-record-base.json",
    "sort": "docs/phase3-b4-reflux-ablation-admission-record-sort.json",
    "trigger": "docs/phase3-b4-reflux-ablation-admission-record-trigger.json",
}
_SECTION5_LABELS = (
    "対象 driver と軸",
    "赤 precursor の母集合 (workload・赤形状・初期 proposal)",
    "アームあたり block 数 n と検定単位",
    "primary outcome の演算定義 (純関数)",
    "floor (対象動作点で再実測した between-run floor) の artifact パスと hash",
    "校正済み `PerfConfig` (records / threads / reps / extime) の artifact パスと hash",
    "総計測予算 (role query 数・build/verify/bench admission 数・累積 bench 秒) と arm ごとの上限",
    "env_tag (実測環境)",
    "model snapshot / prompt hash / projection hash",
    "実行責任者・開始時刻",
)
_EXPECTATION_ROW_LABEL = "model snapshot / prompt hash / projection hash"
_EXPECTED_MEDIATED_CRITIC_CONTRACT = """
Runtime capabilities are intentionally lowered to tools=[]: use only the
projected_digest and result in the JSON object on stdin. Never request or infer
filesystem data and never weaken correctness. Missing metrics must remain
uncertainty. Return JSON only, exactly:
{"attribution":"string","recommend":"string","avoid":"string","uncertainty":"string","reverse_recommended":false}
reverse_recommended must be a JSON boolean and is returned as data only. Do not
emit Markdown or extra keys.
""".strip()


def _production_launch_context(
    cfg=None,
    *,
    driver_kind="base",
    arm="on",
    admission=None,
    action=None,
    layout=None,
    trigger_site=None,
):
    """Capture a production context only through the real admission verifier."""
    if admission is None:
        admission = _committed_admission_fixture(driver_kind=driver_kind)
    parent = Path(tempfile.mkdtemp(prefix="izanagi-b4-context-capture-"))
    proposal_path = parent / "bootstrap-proposal.json"
    document = proposal_document(driver_kind)
    proposal_path.write_text(
        json.dumps(document, ensure_ascii=False), encoding="utf-8"
    )
    binding = issue_proposal_binding_fixture(
        parent / "prerun",
        driver_kind=driver_kind,
        document=document,
        label="context",
    )
    layouts = {}

    def layout_for(campaign_id):
        if layout is not None:
            return layout
        return layouts.setdefault(
            campaign_id,
            CampaignLayout(str(parent / campaign_id)),
        )

    def capture_driver(_argv, *, _b4_launch_context):
        if cfg is not None:
            assert _b4_launch_context.campaign_id == str(ident.campaign_id(cfg))
        selected_layout = layout_for(_b4_launch_context.campaign_id)
        if action is None:
            return _b4_launch_context
        return action(_b4_launch_context, selected_layout)

    with contextlib.ExitStack() as stack:
        stack.enter_context(unittest.mock.patch.object(
            C, "REPOSITORY_ROOT", admission.repository,
        ))
        stack.enter_context(unittest.mock.patch.object(
            B4L, "exploration_campaign_layout", side_effect=layout_for,
        ))
        stack.enter_context(unittest.mock.patch.dict(
            B4L.DRIVER_REGISTRY, {driver_kind: capture_driver},
        ))
        if trigger_site is not None:
            stack.enter_context(unittest.mock.patch.object(
                TRIGGER_LOOP, "_current_site", return_value=trigger_site,
            ))
        return B4L.launch_bootstrap(
            driver_kind=driver_kind,
            arm=arm,
            admission_record_path=admission.record_path,
            proposal_path=proposal_path,
            b4_prerun_publication=Path(binding.publication.publication_root),
            b4_attempt_id=binding.attempt_id,
        )


def _marked_driver_configs(driver_kind="base"):
    """Build the same marker-bearing pair as the production launcher."""
    config_context = B4L.create_b4_launch_context_for_test(
        driver_kind=driver_kind,
    )
    return B4L._driver_configs(driver_kind, config_context)


def _raises(error_type, callable_, *, contains: str | None = None):
    try:
        callable_()
    except error_type as exc:
        if contains is not None:
            assert contains in str(exc), str(exc)
        return exc
    raise AssertionError(f"expected {error_type.__name__}")


def _write_admitted_attempt(
    layout: CampaignLayout,
    cfg,
    *,
    source_tag: str,
    attempt_id: str,
) -> None:
    """Create one policy-admitted synthetic WAL attempt via production APIs."""
    src_token = hashlib.sha256(source_tag.encode("utf-8")).hexdigest()
    evidence = SourceEvidence(
        schema_version="source-evidence/v1",
        source_root=os.path.realpath(layout.root),
        ccbench_commit=L.PIN,
        genome_sha256=hashlib.sha256(_G.canonical().encode("utf-8")).hexdigest(),
        src_token=src_token,
        source_bytes_sha256=hashlib.sha256(
            f"b4-source:{source_tag}".encode("utf-8")
        ).hexdigest(),
        tracked_clean=False,
        tracked_diff_sha256=hashlib.sha256(
            f"b4-diff:{source_tag}".encode("utf-8")
        ).hexdigest(),
        tracked_paths=("include/b4-fixture.hh",),
    )
    assert evidence.tracked_diff_sha256 != EMPTY_TRACKED_DIFF_SHA256
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    capability = attest_generator_output(
        context,
        evidence,
        generator_input_sha256=hashlib.sha256(
            f"b4-input:{source_tag}".encode("utf-8")
        ).hexdigest(),
    )
    admission = derive_build_admission(
        context,
        evidence,
        generator_receipt=capability,
    )
    receipt = admission.as_wal_receipt()
    candidate = variant_id(_G, src_token)
    wal.write_lock(layout, build_v2_lock(ident.canonical_preimage(cfg)))
    wal.log(layout, candidate, L.STAGE_BUILD_START, L.ENV_TAG, {
        "genome": _G.canonical(),
        "src_token": src_token,
        "build_attempt_id": attempt_id,
        "build_admission": receipt,
        "build_admission_receipt_sha256": receipt["receipt_sha256"],
    })
    wal.log(layout, candidate, L.STAGE_ABORT, L.ENV_TAG, {
        "reason": "b4-fixture-reject",
        "build_attempt_id": attempt_id,
        "build_admission_receipt_sha256": receipt["receipt_sha256"],
    })


def _make_admitted_fixture(
    root: Path,
    cfg,
    *,
    source_tag: str,
    iteration: int = 1,
    whiteboard_iteration: int | None = None,
    direction: str = "increase",
) -> CampaignLayout:
    layout = CampaignLayout(root=str(root)).ensure()
    _write_admitted_attempt(
        layout,
        cfg,
        source_tag=source_tag,
        attempt_id=f"{source_tag}-attempt",
    )
    wb_iteration = iteration if whiteboard_iteration is None else whiteboard_iteration
    state = L.LoopState(iteration=iteration, start_wall=1.0)
    state.whiteboard.append(L.WhiteboardEntry(
        iteration=wb_iteration,
        direction=direction,
        magnitude="small",
        result="rejected",
        delta_pct=None,
    ))
    L.save_loop_state(layout, state)
    return layout


def _admitted_digest(layout: CampaignLayout, *, reflux: bool) -> str:
    view = require_admitted_campaign(
        layout,
        purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    )
    return L.make_critic_digest(
        view,
        tag="p3-b4-test",
        reflux=reflux,
        identity_projection=L.make_critic_identity_projection(view),
    )


def _fake_runner_factory(
    *,
    envelope_updates: dict | None = None,
    repeated_session: bool = False,
    timeout: bool = False,
):
    calls = []

    def runner(argv, **kwargs):
        calls.append((list(argv), dict(kwargs)))
        if timeout:
            raise subprocess.TimeoutExpired(argv, kwargs["timeout"])
        ordinal = 1 if repeated_session else len(calls)
        envelope = {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "num_turns": 1,
            "permission_denials": [],
            "result": json.dumps(
                _DECISION_OBJECT,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            "session_id": f"b4-session-{ordinal}",
            "modelUsage": {
                "claude-opus-5": {"inputTokens": 11, "outputTokens": 7},
            },
            "usage": {"server_tool_use": {}},
        }
        if envelope_updates:
            envelope.update(envelope_updates)
        return subprocess.CompletedProcess(
            argv,
            0,
            stdout=json.dumps(envelope, separators=(",", ":")).encode("utf-8"),
            stderr=b"",
        )

    return runner, calls


@contextlib.contextmanager
def _pair_fixture(
    *,
    runner=None,
    repeated_session: bool = False,
    envelope_updates: dict | None = None,
    timeout: bool = False,
    bad_on_iteration: bool = False,
    query_observer=None,
):
    parent = Path(tempfile.mkdtemp(prefix="izanagi-b4-pair-"))
    on_cfg = L.default_cfg(reflux=True)
    off_cfg = L.default_cfg(reflux=False)
    on_id = str(ident.campaign_id(on_cfg))
    off_id = str(ident.campaign_id(off_cfg))
    layouts = {
        on_id: _make_admitted_fixture(
            parent / "campaign-on",
            on_cfg,
            source_tag="b4-on",
            iteration=1,
            whiteboard_iteration=(2 if bad_on_iteration else 1),
        ),
        off_id: _make_admitted_fixture(
            parent / "campaign-off",
            off_cfg,
            source_tag="b4-off",
            direction="decrease",
        ),
    }
    if runner is None:
        runner, calls = _fake_runner_factory(
            repeated_session=repeated_session,
            envelope_updates=envelope_updates,
            timeout=timeout,
        )
    else:
        calls = []
    if query_observer is not None:
        observed_runner = runner

        def runner(argv, **kwargs):
            query_observer(parent)
            return observed_runner(argv, **kwargs)
    home = parent / "home"
    home.mkdir()

    def layout_for(campaign_id):
        return layouts[campaign_id]

    with contextlib.ExitStack() as stack:
        stack.enter_context(unittest.mock.patch.object(
            C,
            "exploration_campaign_layout",
            side_effect=layout_for,
        ))
        pair = C.create_b4_closed_critic_pair_for_test(
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            artifact_root=parent / "artifacts",
            repository_root=C.REPOSITORY_ROOT,
            executable=sys.executable,
            runner=runner,
            environ={"HOME": str(home)},
        )
        try:
            yield pair, layouts, calls
        finally:
            pair.close()


def _invoke_pair():
    context = _pair_fixture()
    pair, layouts, calls = context.__enter__()
    try:
        on = pair.on.invoke(invocation_id="b4-on-1")
        off = pair.off.invoke(invocation_id="b4-off-1")
        return context, pair, layouts, calls, on, off
    except BaseException:
        context.__exit__(*sys.exc_info())
        raise


@contextlib.contextmanager
def _certified_pair_fixture(*, reverse_recommended: bool = False):
    """Build certified-shaped receipts while keeping injection test-local."""
    admission = _committed_admission_fixture()
    parent = Path(tempfile.mkdtemp(prefix="izanagi-b4-certified-live-"))
    config_context = B4L.create_b4_launch_context_for_test(
        driver_kind="base"
    )
    on_cfg = L.default_cfg(
        reflux=True,
        b4_reflux_ablation=True,
        _b4_launch_context=config_context,
    )
    off_cfg = L.default_cfg(
        reflux=False,
        b4_reflux_ablation=True,
        _b4_launch_context=config_context,
    )
    launch_context = _production_launch_context(
        on_cfg,
        admission=admission,
    )
    on_id = str(ident.campaign_id(on_cfg))
    off_id = str(ident.campaign_id(off_cfg))
    layouts = {
        on_id: _make_admitted_fixture(
            parent / "campaign-on", on_cfg, source_tag="certified-live-on"
        ),
        off_id: _make_admitted_fixture(
            parent / "campaign-off", off_cfg, source_tag="certified-live-off"
        ),
    }
    for layout in layouts.values():
        state = L.load_loop_state(layout)
        assert state is not None
        state.start_wall = time.time()
        L.save_loop_state(layout, state)
    decision = {
        **_DECISION_OBJECT,
        "reverse_recommended": reverse_recommended,
    }
    runner, calls = _fake_runner_factory(envelope_updates={
        "result": json.dumps(decision, separators=(",", ":")),
    })
    home = parent / "home"
    home.mkdir()

    def layout_for(campaign_id):
        return layouts[campaign_id]

    with contextlib.ExitStack() as stack:
        stack.enter_context(unittest.mock.patch.object(
            C, "REPOSITORY_ROOT", admission.repository,
        ))
        stack.enter_context(unittest.mock.patch.object(
            C, "ROLE_FILE", admission.role_file,
        ))
        stack.enter_context(unittest.mock.patch.object(
            C.shutil, "which", return_value=sys.executable,
        ))
        stack.enter_context(unittest.mock.patch.object(
            C, "exploration_campaign_layout", side_effect=layout_for,
        ))
        pair = C.create_b4_closed_critic_pair(
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            artifact_root=parent / "artifacts",
            admission_record_path=admission.record_path,
            expected_driver_kind="base",
            _b4_launch_context=launch_context,
            repository_root=admission.repository,
            environ={"HOME": str(home)},
        )
        pair.on._B4ClosedCriticController__provider._runner = runner
        pair.off._B4ClosedCriticController__provider._runner = runner
        try:
            yield pair, on_cfg, layouts[on_id], calls
        finally:
            pair.close()


def _capture_certified_pair_construction(
    parent: Path,
    *,
    driver_kind: C.DriverKind = "base",
):
    constructions = []
    admission = _committed_admission_fixture(driver_kind=driver_kind)

    class CapturingController:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            constructions.append(kwargs)

        def _pair_identity(self):
            return self.kwargs["controller_id"], str(self.kwargs["artifact_root"])

        def close(self):
            return None

    with unittest.mock.patch.object(
        C, "REPOSITORY_ROOT", admission.repository
    ), unittest.mock.patch.object(
        C, "ROLE_FILE", admission.role_file
    ), unittest.mock.patch.object(
        C.shutil, "which", return_value=sys.executable
    ) as which_mock, unittest.mock.patch.object(
        C, "B4ClosedCriticController", CapturingController
    ):
        config_context = B4L.create_b4_launch_context_for_test(
            driver_kind=driver_kind,
        )
        on_cfg, off_cfg = B4L._driver_configs(driver_kind, config_context)
        launch_context = _production_launch_context(
            on_cfg,
            admission=admission,
            driver_kind=driver_kind,
        )
        pair = C.create_b4_closed_critic_pair(
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            artifact_root=parent / "captured",
            admission_record_path=admission.record_path,
            expected_driver_kind=driver_kind,
            _b4_launch_context=launch_context,
            repository_root=admission.repository,
            environ={"HOME": str(parent)},
        )
        pair.close()
    which_mock.assert_called_once_with("claude")
    assert len(constructions) == 2
    return constructions


def _canonical_payload(digest: str, result: str = "rejected") -> bytes:
    entry = L.WhiteboardEntry(1, "increase", "small", result, None)
    payload = C.project_b4_critic_payload(
        projected_digest=digest,
        whiteboard_entry=entry,
    )
    return C._canonical_json_bytes(payload)


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _git(repository: Path, *args: str) -> bytes:
    completed = subprocess.run(
        [
            "/usr/bin/git",
            "-c",
            "commit.gpgsign=false",
            "-C",
            str(repository),
            *args,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    return completed.stdout


def _effective_prompt_sha256(role_bytes: bytes) -> str:
    _frontmatter, body = P._parse_frontmatter(
        role_bytes,
        expected_name="critic",
    )
    effective_prompt = (
        body.rstrip()
        + "\n\n---\n\n"
        + "# T-178 mediated projection contract (this section takes precedence)\n\n"
        + _EXPECTED_MEDIATED_CRITIC_CONTRACT
        + "\n"
    )
    return hashlib.sha256(effective_prompt.encode("utf-8")).hexdigest()


def _independent_projection_sha256(
    role_file: Path,
    *,
    driver_kind: C.DriverKind = "base",
) -> str:
    repository_root = _ORCH.parent
    paths = {
        "orchestrator/campaign/p3_b4_closed_critic.py": (
            repository_root / "orchestrator/campaign/p3_b4_closed_critic.py"
        ),
        "orchestrator/campaign/claude_projected_provider.py": (
            repository_root / "orchestrator/campaign/claude_projected_provider.py"
        ),
        "orchestrator/campaign/p3_s4_loop.py": (
            repository_root / "orchestrator/campaign/p3_s4_loop.py"
        ),
        "orchestrator/campaign/artifact_admission.py": (
            repository_root / "orchestrator/campaign/artifact_admission.py"
        ),
        "orchestrator/campaign/s8b_prediction_runner.py": (
            repository_root / "orchestrator/campaign/s8b_prediction_runner.py"
        ),
        "orchestrator/campaign/role_session_isolation.py": (
            repository_root / "orchestrator/campaign/role_session_isolation.py"
        ),
        "orchestrator/campaign/p3_b4_admission_record.py": (
            repository_root / "orchestrator/campaign/p3_b4_admission_record.py"
        ),
        "orchestrator/campaign/p3_b4_launcher.py": (
            repository_root / "orchestrator/campaign/p3_b4_launcher.py"
        ),
        "orchestrator/campaign/p3_b4_protocol.py": (
            repository_root / "orchestrator/campaign/p3_b4_protocol.py"
        ),
        "orchestrator/critic/digest.py": (
            repository_root / "orchestrator/critic/digest.py"
        ),
        "orchestrator/critic/identity_projection.py": (
            repository_root / "orchestrator/critic/identity_projection.py"
        ),
        ".claude/agents/critic.md": role_file,
    }
    if driver_kind == "sort":
        paths["orchestrator/campaign/p3_s4_loop_sort.py"] = (
            repository_root / "orchestrator/campaign/p3_s4_loop_sort.py"
        )
    elif driver_kind == "trigger":
        paths["orchestrator/campaign/p3_s4_loop_trigger_gating.py"] = (
            repository_root
            / "orchestrator/campaign/p3_s4_loop_trigger_gating.py"
        )
    entries = {
        key: hashlib.sha256(path.read_bytes()).hexdigest()
        for key, path in paths.items()
    }
    entries["mediated-contract:utf-8"] = hashlib.sha256(
        _EXPECTED_MEDIATED_CRITIC_CONTRACT.encode("utf-8")
    ).hexdigest()
    manifest = {
        "schema_version": "p3-b4-projection-closure/v1",
        "entries": entries,
    }
    canonical = json.dumps(
        manifest,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class _AdmissionFixture:
    repository: Path
    role_file: Path
    record_path: Path
    expected_model: str
    expected_prompt: str
    expected_projection: str
    expected_projections: dict[C.DriverKind, str]


def _stale_projection(live: str) -> str:
    replacement = "0" if live[0] != "0" else "1"
    return replacement + live[1:]


def _committed_admission_fixture(
    *,
    expected_model: str = _ADMISSION_MODEL,
    expected_prompt: str | None = None,
    expected_projection: str | None = None,
    document_projections: dict[C.DriverKind, str] | None = None,
    driver_kind: C.DriverKind = "base",
    verify_record: bool = True,
) -> _AdmissionFixture:
    repository = Path(tempfile.mkdtemp(prefix="izanagi-b4-closed-admission-"))
    _git(repository, "init")
    _git(repository, "config", "user.name", "B4 Closed Critic Test")
    _git(repository, "config", "user.email", "b4-closed@example.invalid")
    role_file = repository / ".claude" / "agents" / "critic.md"
    role_file.parent.mkdir(parents=True)
    role_bytes = C.ROLE_FILE.read_bytes()
    role_file.write_bytes(role_bytes)
    prompt = (
        _effective_prompt_sha256(role_bytes)
        if expected_prompt is None
        else expected_prompt
    )
    live_projections = {
        kind: _independent_projection_sha256(role_file, driver_kind=kind)
        for kind in A.B4_PROJECTION_DRIVER_KINDS
    }
    projections = (
        live_projections
        if document_projections is None
        else dict(document_projections)
    )
    projection = (
        live_projections[driver_kind]
        if expected_projection is None
        else expected_projection
    )
    values = {
        label: f"closed-critic-fixture-{index}"
        for index, label in enumerate(_SECTION5_LABELS, start=1)
    }
    values[_EXPECTATION_ROW_LABEL] = (
        f"expected_claude_model_snapshot={expected_model}; "
        f"expected_effective_critic_prompt_sha256={prompt}; "
        "expected_closed_critic_projection_closure_sha256[base]="
        f"{projections['base']}; "
        "expected_closed_critic_projection_closure_sha256[sort]="
        f"{projections['sort']}; "
        "expected_closed_critic_projection_closure_sha256[trigger]="
        f"{projections['trigger']}"
    )
    document_lines = [
        "# Closed critic fixture",
        "",
        "## 5. 実走前に数値で埋める欄",
        "",
        "|欄|値|",
        "|---|---|",
    ]
    document_lines.extend(
        f"|{label}|{values[label]}|" for label in _SECTION5_LABELS
    )
    document_lines.extend(("", "### 5.1 欄別の解除条件", "", "fixture"))
    document_bytes = "\n".join(document_lines).encode("utf-8")
    document_path = repository / _PREREGISTRATION_REPOSITORY_PATH
    document_path.parent.mkdir(parents=True)
    document_path.write_bytes(document_bytes)
    _git(
        repository,
        "add",
        ".claude/agents/critic.md",
        _PREREGISTRATION_REPOSITORY_PATH,
    )
    _git(repository, "commit", "-m", "fixture preregistration")
    content_commit = _git(repository, "rev-parse", "HEAD").decode().strip()
    value = {
        "schema_version": _ADMISSION_SCHEMA_VERSION,
        "preregistration_binding": {
            "repository_path": _PREREGISTRATION_REPOSITORY_PATH,
            "content_commit": content_commit,
            "content_sha256": hashlib.sha256(document_bytes).hexdigest(),
        },
        "closed_critic_expectations": {
            "expected_claude_model_snapshot": expected_model,
            "expected_effective_critic_prompt_sha256": prompt,
            "expected_closed_critic_projection_closure_sha256": projection,
        },
    }
    record_repository_path = (
        _REQUIRED_ADMISSION_RECORD_REPOSITORY_PATH_BY_DRIVER[driver_kind]
    )
    record_path = repository / record_repository_path
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_bytes(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    )
    _git(repository, "add", record_repository_path)
    _git(repository, "commit", "-m", "fixture admission")
    if verify_record:
        verified = A.verify_b4_admission_record(
            record_path,
            repository_root=repository,
            driver_kind=driver_kind,
        )
        assert verified.expected_claude_model_snapshot == expected_model
        assert dict(
            verified.expected_closed_critic_projection_closure_sha256_by_driver
        ) == projections
    return _AdmissionFixture(
        repository=repository,
        role_file=role_file,
        record_path=record_path,
        expected_model=expected_model,
        expected_prompt=prompt,
        expected_projection=projection,
        expected_projections=projections,
    )


@contextlib.contextmanager
def _certified_environment(admission: _AdmissionFixture):
    parent = Path(tempfile.mkdtemp(prefix="izanagi-b4-certified-pair-"))
    on_cfg, off_cfg = _marked_driver_configs()
    on_id = str(ident.campaign_id(on_cfg))
    off_id = str(ident.campaign_id(off_cfg))
    layouts = {
        on_id: _make_admitted_fixture(
            parent / "campaign-on",
            on_cfg,
            source_tag="certified-on",
        ),
        off_id: _make_admitted_fixture(
            parent / "campaign-off",
            off_cfg,
            source_tag="certified-off",
            direction="decrease",
        ),
    }
    home = parent / "home"
    home.mkdir()

    def layout_for(campaign_id):
        return layouts[campaign_id]

    with contextlib.ExitStack() as stack:
        stack.enter_context(unittest.mock.patch.object(
            C,
            "REPOSITORY_ROOT",
            admission.repository,
        ))
        stack.enter_context(unittest.mock.patch.object(
            C,
            "ROLE_FILE",
            admission.role_file,
        ))
        stack.enter_context(unittest.mock.patch.object(
            C.shutil,
            "which",
            return_value=sys.executable,
        ))
        stack.enter_context(unittest.mock.patch.object(
            C,
            "exploration_campaign_layout",
            side_effect=layout_for,
        ))
        yield parent, on_cfg, off_cfg, layouts, home


def test_p1_policy_admitted_synthetic_wal_digests_pass_payload_identity_gate():
    parent = Path(tempfile.mkdtemp(prefix="izanagi-b4-real-digest-"))
    on_cfg = L.default_cfg(reflux=True)
    off_cfg = L.default_cfg(reflux=False)
    on_layout = _make_admitted_fixture(
        parent / "on", on_cfg, source_tag="synthetic-on"
    )
    off_layout = _make_admitted_fixture(
        parent / "off", off_cfg, source_tag="synthetic-off"
    )
    on_digest = _admitted_digest(on_layout, reflux=True)
    off_digest = _admitted_digest(off_layout, reflux=False)
    assert "# rejections" in on_digest
    assert "# rejections" not in off_digest
    for cfg, layout, digest in (
        (on_cfg, on_layout, on_digest),
        (off_cfg, off_layout, off_digest),
    ):
        payload_bytes = _canonical_payload(digest)
        assert set(json.loads(payload_bytes)) == {"projected_digest", "result"}
        C.assert_no_campaign_identity(
            payload_bytes,
            campaign_path=Path(layout.root).resolve(),
            campaign_id=str(ident.campaign_id(cfg)),
            repository_root=C.REPOSITORY_ROOT,
        )


def test_m1_campaign_id_gate_accepts_real_digest_and_rejects_only_literal_injection():
    parent = Path(tempfile.mkdtemp(prefix="izanagi-b4-m1-"))
    cfg = L.default_cfg(reflux=True)
    layout = _make_admitted_fixture(parent / "on", cfg, source_tag="m1")
    digest = _admitted_digest(layout, reflux=True)
    campaign_id = str(ident.campaign_id(cfg))
    C.assert_no_campaign_identity(
        _canonical_payload(digest),
        campaign_path=Path(layout.root).resolve(),
        campaign_id=campaign_id,
    )
    error = _raises(
        C.B4CampaignDisclosureError,
        lambda: C.assert_no_campaign_identity(
            _canonical_payload(digest + "\n" + campaign_id),
            campaign_path=Path(layout.root).resolve(),
            campaign_id=campaign_id,
        ),
    )
    assert error.identity_kind == "campaign_id" and error.checked_view == "raw"


def test_m2_repository_root_gate_accepts_real_digest_and_rejects_only_literal_injection():
    parent = Path(tempfile.mkdtemp(prefix="izanagi-b4-m2-"))
    cfg = L.default_cfg(reflux=False)
    layout = _make_admitted_fixture(parent / "off", cfg, source_tag="m2")
    digest = _admitted_digest(layout, reflux=False)
    campaign_id = str(ident.campaign_id(cfg))
    C.assert_no_campaign_identity(
        _canonical_payload(digest),
        campaign_path=Path(layout.root).resolve(),
        campaign_id=campaign_id,
    )
    error = _raises(
        C.B4CampaignDisclosureError,
        lambda: C.assert_no_campaign_identity(
            _canonical_payload(digest + "\n" + str(C.REPOSITORY_ROOT)),
            campaign_path=Path(layout.root).resolve(),
            campaign_id=campaign_id,
        ),
    )
    assert error.identity_kind == "repository_root" and error.checked_view == "raw"


def test_m3_campaign_path_gate_accepts_real_digest_and_rejects_only_literal_injection():
    parent = Path(tempfile.mkdtemp(prefix="izanagi-b4-m3-"))
    cfg = L.default_cfg(reflux=True)
    layout = _make_admitted_fixture(parent / "on", cfg, source_tag="m3")
    digest = _admitted_digest(layout, reflux=True)
    campaign_path = Path(layout.root).resolve()
    campaign_id = str(ident.campaign_id(cfg))
    C.assert_no_campaign_identity(
        _canonical_payload(digest),
        campaign_path=campaign_path,
        campaign_id=campaign_id,
    )
    error = _raises(
        C.B4CampaignDisclosureError,
        lambda: C.assert_no_campaign_identity(
            _canonical_payload(digest + "\n" + str(campaign_path)),
            campaign_path=campaign_path,
            campaign_id=campaign_id,
        ),
    )
    assert error.identity_kind == "campaign_path" and error.checked_view == "raw"


def test_m4_module_root_control_accepts_exact_root_and_rejects_decoy_before_factory():
    C.assert_no_campaign_identity(
        _canonical_payload("admitted digest"),
        campaign_path=Path(tempfile.mkdtemp(prefix="izanagi-b4-root-positive-")).resolve(),
        campaign_id="campaign-positive",
        repository_root=C.REPOSITORY_ROOT,
    )
    fake_root = Path(tempfile.mkdtemp(prefix="izanagi-b4-decoy-root-"))
    artifact = Path(tempfile.mkdtemp(prefix="izanagi-b4-decoy-artifact-parent-")) / "new"
    error = _raises(
        C.B4TrustRootError,
        lambda: C.create_b4_closed_critic_pair_for_test(
            on_cfg=L.default_cfg(reflux=True),
            off_cfg=L.default_cfg(reflux=False),
            artifact_root=artifact,
            repository_root=fake_root,
            executable=sys.executable,
            runner=lambda *_args, **_kwargs: None,
            environ={"HOME": str(fake_root)},
        ),
    )
    assert "module-derived" in str(error)
    assert not artifact.exists()


def test_m5_certified_factory_has_no_runner_seam_and_binds_subprocess_run():
    parent = Path(tempfile.mkdtemp(prefix="izanagi-b4-certified-runner-"))
    admission = _committed_admission_fixture()
    signature = inspect.signature(C.create_b4_closed_critic_pair)
    assert "runner" not in signature.parameters
    assert (
        signature.parameters["admission_record_path"].default
        is inspect.Parameter.empty
    )
    assert (
        signature.parameters["admission_record_path"].kind
        is inspect.Parameter.KEYWORD_ONLY
    )
    assert not hasattr(C, "_CERTIFIED_RUNNER")
    assert not hasattr(C, "_CERTIFIED_WHICH")
    injected_runner, _calls = _fake_runner_factory()
    rejected_root = parent / "rejected"
    on_cfg, off_cfg = _marked_driver_configs()
    launch_context = _production_launch_context(on_cfg, admission=admission)
    error = _raises(
        TypeError,
        lambda: C.create_b4_closed_critic_pair(
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            artifact_root=rejected_root,
            admission_record_path=admission.record_path,
            expected_driver_kind="base",
            _b4_launch_context=launch_context,
            repository_root=admission.repository,
            runner=injected_runner,
            environ={"HOME": str(parent)},
        ),
    )
    assert "unexpected keyword argument 'runner'" in str(error)
    assert not rejected_root.exists()

    constructions = _capture_certified_pair_construction(parent)
    assert all(item["evidence_class"] == "certified" for item in constructions)
    assert all(item["runner"] is subprocess.run for item in constructions)


def test_admission_keyword_and_binding_failures_precede_executable_artifact_provider():
    parent = Path(tempfile.mkdtemp(prefix="izanagi-b4-admission-order-"))
    missing_root = parent / "missing-keyword"
    on_cfg, off_cfg = _marked_driver_configs()
    launch_context = _production_launch_context(on_cfg)
    error = _raises(
        TypeError,
        lambda: C.create_b4_closed_critic_pair(
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            artifact_root=missing_root,
            expected_driver_kind="base",
            _b4_launch_context=launch_context,
        ),
    )
    assert "missing 1 required keyword-only argument: 'admission_record_path'" in str(
        error
    )
    assert not missing_root.exists()

    for index, message in enumerate((
        "[admission-record] record is unavailable",
        "[admission-record] record is not committed at execution HEAD",
        "[admission-preregistration] document binding is not verifiable",
    )):
        artifact_root = parent / f"binding-{index}"
        with unittest.mock.patch.object(
            C,
            "verify_b4_admission_record",
            side_effect=A.B4AdmissionRecordError(message),
        ), unittest.mock.patch.object(
            C.shutil,
            "which",
            side_effect=AssertionError("executable lookup must not run"),
        ), unittest.mock.patch.object(
            C,
            "B4ClosedCriticController",
            side_effect=AssertionError("provider construction must not run"),
        ):
            raised = _raises(
                A.B4AdmissionRecordError,
                lambda artifact_root=artifact_root: C.create_b4_closed_critic_pair(
                    on_cfg=on_cfg,
                    off_cfg=off_cfg,
                    artifact_root=artifact_root,
                    admission_record_path=parent / "record.json",
                    expected_driver_kind="base",
                    _b4_launch_context=launch_context,
                ),
            )
        assert str(raised) == message
        assert not artifact_root.exists()


def test_repository_checked_record_with_nonempty_cells_and_three_matching_expectations_yields_certified_pair_using_fake_runner():
    """Check only three runtime expectations; nine cells have no meaning check."""
    admission = _committed_admission_fixture()
    fake_runner, calls = _fake_runner_factory()
    with _certified_environment(admission) as (
        parent,
        on_cfg,
        off_cfg,
        _layouts,
        home,
    ):
        sidecar_present_at_query = []

        def runner(argv, **kwargs):
            sidecar_present_at_query.append(
                (parent / "artifacts/admission_record_sidecar.json").is_file()
            )
            return fake_runner(argv, **kwargs)

        with C.create_b4_closed_critic_pair(
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            artifact_root=parent / "artifacts",
            admission_record_path=admission.record_path,
            expected_driver_kind="base",
            _b4_launch_context=_production_launch_context(
                on_cfg, admission=admission,
            ),
            repository_root=admission.repository,
            environ={"HOME": str(home)},
        ) as pair:
            pair.on._B4ClosedCriticController__provider._runner = runner
            pair.off._B4ClosedCriticController__provider._runner = runner
            on = pair.on.invoke(invocation_id="admitted-on")
            off = pair.off.invoke(invocation_id="admitted-off")
            comparison = C.assert_b4_certified_arm_pair(
                pair,
                on.terminal_receipt_path,
                off.terminal_receipt_path,
                admission_record_path=admission.record_path,
            )
            sidecar_path = pair.admission_sidecar_path
            sidecar_sha256 = pair.admission_sidecar_sha256
            sidecar_bytes = sidecar_path.read_bytes()
            sidecar_path.write_bytes(sidecar_bytes + b"\n")
            _raises(
                C.B4ReceiptError,
                lambda: C.assert_b4_certified_arm_pair(
                    pair,
                    on.terminal_receipt_path,
                    off.terminal_receipt_path,
                    admission_record_path=admission.record_path,
                ),
                contains="admission sidecar differs",
            )
            sidecar_path.write_bytes(sidecar_bytes)
        assert len(calls) == 2
        assert sidecar_present_at_query == [True, True]
        assert on.receipt.schema_version == C.B4_CLOSED_CRITIC_RECEIPT_SCHEMA
        assert off.receipt.schema_version == C.B4_CLOSED_CRITIC_RECEIPT_SCHEMA
        assert on.receipt.evidence_class == "certified"
        assert off.receipt.evidence_class == "certified"
        assert comparison.iteration_equal
        exact_keys = {
            "schema_version",
            "status",
            "evidence_class",
            "pair_id",
            "arm",
            "campaign_id",
            "controller_id",
            "invocation_id",
            "session_id",
            "provider_kind",
            "driver_kind",
            "provider_instance_id",
            "neutral_root_identity_sha256",
            "model_snapshot",
            "role_file_sha256",
            "effective_prompt_sha256",
            "projection_sha256",
            "digest_sha256",
            "admitted_view_sha256",
            "loop_state_sha256",
            "iteration",
            "decision_sha256",
            "decision_reverse_recommended",
            "claimed_fresh_context",
            "claimed_capability_lowering",
            "claimed_source_declared_tools",
            "claimed_declared_tools",
            "claimed_observed_tool_events",
            "evidence_executable_path",
            "evidence_executable_sha256",
            "evidence_payload_sha256",
            "evidence_raw_envelope_sha256",
            "evidence_argv_sha256",
            "evidence_num_turns",
            "evidence_permission_denials_empty",
            "evidence_server_tool_use_all_zero",
            "exact_identity_literals_absent_from_canonical_payload",
            "identity_non_guarantees",
            "trust_non_guarantees",
            "capability_non_guarantees",
            "snapshot_non_guarantees",
            "storage_non_guarantees",
            "start_receipt_sha256",
            "finished_at_ns"
        }
        assert set(json.loads(on.terminal_receipt_path.read_bytes())) == exact_keys
        assert C._read_verified_terminal_receipt(
            on.terminal_receipt_path
        ) == on.receipt
        record = json.loads(admission.record_path.read_bytes())
        expected_sidecar = {
            "schema_version": "p3-b4-prerun-admission-sidecar/v1",
            "admission_record_repository_path": (
                admission.record_path.relative_to(
                    admission.repository
                ).as_posix()
            ),
            "admission_record_sha256": hashlib.sha256(
                admission.record_path.read_bytes()
            ).hexdigest(),
            "verification_head_commit": _git(
                admission.repository, "rev-parse", "HEAD"
            ).decode().strip(),
            "preregistration_repository_path": (
                "docs/phase3-b4-reflux-ablation-preregistration.md"
            ),
            "preregistration_content_commit": record[
                "preregistration_binding"
            ]["content_commit"],
            "preregistration_content_sha256": record[
                "preregistration_binding"
            ]["content_sha256"],
            "expected_claude_model_snapshot": admission.expected_model,
            "expected_effective_critic_prompt_sha256": admission.expected_prompt,
            "expected_closed_critic_projection_closure_sha256": (
                admission.expected_projection
            ),
        }
        expected_sidecar_bytes = json.dumps(
            expected_sidecar,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        assert sidecar_path.read_bytes() == expected_sidecar_bytes
        assert sidecar_sha256 == hashlib.sha256(
            expected_sidecar_bytes
        ).hexdigest()


def test_pair_creation_rejects_stale_nonselected_document_projection_before_provider():
    document_projections = {
        kind: C.projection_sha256(kind)
        for kind in A.B4_PROJECTION_DRIVER_KINDS
    }
    document_projections["sort"] = _stale_projection(
        document_projections["sort"]
    )
    admission = _committed_admission_fixture(
        document_projections=document_projections,
        expected_projection=document_projections["base"],
        driver_kind="base",
    )
    with unittest.mock.patch.object(
        C,
        "assert_b4_document_projection_closures_are_live",
        return_value=document_projections,
    ):
        launch_context = _production_launch_context(
            admission=admission,
        )
    artifact_root: Path | None = None
    with _certified_environment(admission) as (
        parent,
        on_cfg,
        off_cfg,
        _layouts,
        home,
    ), unittest.mock.patch.object(
        C.shutil,
        "which",
    ) as which_mock, unittest.mock.patch.object(
        C,
        "ClaudeProjectedRoleProvider",
        side_effect=AssertionError("provider construction must not run"),
    ) as provider_mock:
        artifact_root = parent / "stale-nonselected"
        error = _raises(
            A.B4AdmissionRecordError,
            lambda: C.create_b4_closed_critic_pair(
                on_cfg=on_cfg,
                off_cfg=off_cfg,
                artifact_root=artifact_root,
                admission_record_path=admission.record_path,
                expected_driver_kind="base",
                _b4_launch_context=launch_context,
                repository_root=admission.repository,
                environ={"HOME": str(home)},
            ),
        )
        which_mock.assert_not_called()
        provider_mock.assert_not_called()
    assert artifact_root is not None and not artifact_root.exists()
    assert str(error) == (
        "[admission-mismatch] "
        "expected_closed_critic_projection_closure_sha256[sort]"
    )


def test_pair_creation_rejects_three_stale_document_projections_before_provider():
    document_projections = {
        kind: _stale_projection(C.projection_sha256(kind))
        for kind in A.B4_PROJECTION_DRIVER_KINDS
    }
    admission = _committed_admission_fixture(
        document_projections=document_projections,
        expected_projection=document_projections["base"],
        driver_kind="base",
    )
    with unittest.mock.patch.object(
        C,
        "assert_b4_document_projection_closures_are_live",
        return_value=document_projections,
    ):
        launch_context = _production_launch_context(
            admission=admission,
        )
    with _certified_environment(admission) as (
        parent,
        on_cfg,
        off_cfg,
        _layouts,
        home,
    ), unittest.mock.patch.object(
        C,
        "ClaudeProjectedRoleProvider",
        side_effect=AssertionError("provider construction must not run"),
    ):
        error = _raises(
            A.B4AdmissionRecordError,
            lambda: C.create_b4_closed_critic_pair(
                on_cfg=on_cfg,
                off_cfg=off_cfg,
                artifact_root=parent / "three-stale",
                admission_record_path=admission.record_path,
                expected_driver_kind="base",
                _b4_launch_context=launch_context,
                repository_root=admission.repository,
                environ={"HOME": str(home)},
            ),
        )
    assert str(error) == (
        "[admission-mismatch] "
        "expected_closed_critic_projection_closure_sha256[base]"
    )


def test_certified_invoke_rejects_nonselected_projection_change_before_query():
    admission = _committed_admission_fixture()
    fake_runner, calls = _fake_runner_factory()
    with _certified_environment(admission) as (
        parent,
        on_cfg,
        off_cfg,
        _layouts,
        home,
    ):
        launch_context = _production_launch_context(
            on_cfg,
            admission=admission,
        )
        with C.create_b4_closed_critic_pair(
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            artifact_root=parent / "invoke-stale-nonselected",
            admission_record_path=admission.record_path,
            expected_driver_kind="base",
            _b4_launch_context=launch_context,
            repository_root=admission.repository,
            environ={"HOME": str(home)},
        ) as pair:
            pair.on._B4ClosedCriticController__provider._runner = fake_runner
            live_projections = {
                kind: C.projection_sha256(kind)
                for kind in A.B4_PROJECTION_DRIVER_KINDS
            }

            def projection_after_pair_creation(driver_kind="base"):
                if driver_kind == "sort":
                    return _stale_projection(live_projections[driver_kind])
                return live_projections[driver_kind]

            with unittest.mock.patch.object(
                C,
                "projection_sha256",
                side_effect=projection_after_pair_creation,
            ):
                error = _raises(
                    A.B4AdmissionRecordError,
                    lambda: pair.on.invoke(invocation_id="stale-sort"),
                )
    assert str(error) == (
        "[admission-mismatch] "
        "expected_closed_critic_projection_closure_sha256[sort]"
    )
    assert calls == []


def test_final_certification_rechecks_nonselected_projection_closures():
    admission = _committed_admission_fixture()
    fake_runner, calls = _fake_runner_factory()
    with _certified_environment(admission) as (
        parent,
        on_cfg,
        off_cfg,
        _layouts,
        home,
    ):
        launch_context = _production_launch_context(
            on_cfg,
            admission=admission,
        )
        with C.create_b4_closed_critic_pair(
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            artifact_root=parent / "certification-stale-nonselected",
            admission_record_path=admission.record_path,
            expected_driver_kind="base",
            _b4_launch_context=launch_context,
            repository_root=admission.repository,
            environ={"HOME": str(home)},
        ) as pair:
            pair.on._B4ClosedCriticController__provider._runner = fake_runner
            pair.off._B4ClosedCriticController__provider._runner = fake_runner
            on = pair.on.invoke(invocation_id="certification-on")
            off = pair.off.invoke(invocation_id="certification-off")
            live_projections = {
                kind: C.projection_sha256(kind)
                for kind in A.B4_PROJECTION_DRIVER_KINDS
            }

            def projection_before_certification(driver_kind="base"):
                if driver_kind == "trigger":
                    return _stale_projection(live_projections[driver_kind])
                return live_projections[driver_kind]

            with unittest.mock.patch.object(
                C,
                "projection_sha256",
                side_effect=projection_before_certification,
            ):
                error = _raises(
                    A.B4AdmissionRecordError,
                    lambda: C.assert_b4_certified_arm_pair(
                        pair,
                        on.terminal_receipt_path,
                        off.terminal_receipt_path,
                        admission_record_path=admission.record_path,
                    ),
                )
    assert str(error) == (
        "[admission-mismatch] "
        "expected_closed_critic_projection_closure_sha256[trigger]"
    )
    assert len(calls) == 2


def test_pair_creation_reads_each_live_projection_closure_once():
    admission = _committed_admission_fixture()
    with _certified_environment(admission) as (
        parent,
        on_cfg,
        off_cfg,
        _layouts,
        home,
    ):
        launch_context = _production_launch_context(
            on_cfg,
            admission=admission,
        )
        real_projection_sha256 = C.projection_sha256
        projection_calls = []

        def counted_projection(driver_kind="base"):
            projection_calls.append(driver_kind)
            return real_projection_sha256(driver_kind)

        with unittest.mock.patch.object(
            C,
            "projection_sha256",
            side_effect=counted_projection,
        ):
            with C.create_b4_closed_critic_pair(
                on_cfg=on_cfg,
                off_cfg=off_cfg,
                artifact_root=parent / "single-projection-read",
                admission_record_path=admission.record_path,
                expected_driver_kind="base",
                _b4_launch_context=launch_context,
                repository_root=admission.repository,
                environ={"HOME": str(home)},
            ):
                pass
    assert projection_calls == list(A.B4_PROJECTION_DRIVER_KINDS)


def test_certified_admission_rejects_projection_and_prompt_before_query():
    projection_admission = _committed_admission_fixture(
        expected_projection=_stale_projection(C.projection_sha256("base")),
        verify_record=False,
    )
    provider_events = []
    real_provider = C.ClaudeProjectedRoleProvider

    class CountingProvider(real_provider):
        def __init__(self, **kwargs):
            provider_events.append("created")
            super().__init__(**kwargs)

        def invoke(self, **kwargs):
            provider_events.append("query")
            return super().invoke(**kwargs)

    with _certified_environment(projection_admission) as (
        parent,
        on_cfg,
        off_cfg,
        _layouts,
        home,
    ), unittest.mock.patch.object(
        C,
        "ClaudeProjectedRoleProvider",
        CountingProvider,
    ):
        valid_launch_context = _production_launch_context(on_cfg)
        _raises(
            A.B4AdmissionRecordError,
            lambda: C.create_b4_closed_critic_pair(
                on_cfg=on_cfg,
                off_cfg=off_cfg,
                artifact_root=parent / "projection-artifacts",
                admission_record_path=projection_admission.record_path,
                expected_driver_kind="base",
                _b4_launch_context=valid_launch_context,
                repository_root=projection_admission.repository,
                environ={"HOME": str(home)},
            ),
            contains=(
                "[admission-mismatch] "
                "expected_closed_critic_projection_closure_sha256"
            ),
        )
    assert provider_events == []

    prompt_admission = _committed_admission_fixture(
        expected_prompt="f" * 64,
    )
    provider_events.clear()
    with _certified_environment(prompt_admission) as (
        parent,
        on_cfg,
        off_cfg,
        _layouts,
        home,
    ), unittest.mock.patch.object(
        C,
        "ClaudeProjectedRoleProvider",
        CountingProvider,
    ):
        _raises(
            A.B4AdmissionRecordError,
            lambda: C.create_b4_closed_critic_pair(
                on_cfg=on_cfg,
                off_cfg=off_cfg,
                artifact_root=parent / "prompt-artifacts",
                admission_record_path=prompt_admission.record_path,
                expected_driver_kind="base",
                _b4_launch_context=_production_launch_context(
                    on_cfg, admission=prompt_admission,
                ),
                repository_root=prompt_admission.repository,
                environ={"HOME": str(home)},
            ),
            contains=(
                "[admission-mismatch] "
                "expected_effective_critic_prompt_sha256"
            ),
        )
    assert provider_events == ["created"]


def test_certified_admission_model_mismatch_queries_once_and_writes_failure_terminal():
    admission = _committed_admission_fixture(
        expected_model="claude-opus-other",
    )
    runner, calls = _fake_runner_factory()
    with _certified_environment(admission) as (
        parent,
        on_cfg,
        off_cfg,
        _layouts,
        home,
    ):
        with C.create_b4_closed_critic_pair(
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            artifact_root=parent / "model-artifacts",
            admission_record_path=admission.record_path,
            expected_driver_kind="base",
            _b4_launch_context=_production_launch_context(
                on_cfg, admission=admission,
            ),
            repository_root=admission.repository,
            environ={"HOME": str(home)},
        ) as pair:
            pair.on._B4ClosedCriticController__provider._runner = runner
            error = _raises(
                A.B4AdmissionRecordError,
                lambda: pair.on.invoke(invocation_id="model-mismatch"),
                contains="[admission-mismatch] expected_claude_model_snapshot",
            )
            assert str(error) == (
                "[admission-mismatch] expected_claude_model_snapshot"
            )
            terminal_path = (
                pair.on._B4ClosedCriticController__artifact_root
                / "receipt_model-mismatch_terminal.json"
            )
            terminal = json.loads(terminal_path.read_bytes())
            assert terminal["status"] == "failure"
            assert terminal["error_type"] == "B4AdmissionRecordError"
            assert terminal["error_signature"] == (
                "[admission-mismatch] expected_claude_model_snapshot"
            )
            assert not any(
                value.get("status") == "success"
                for value in (
                    json.loads(path.read_bytes())
                    for path in terminal_path.parent.glob("receipt_*_terminal.json")
                )
            )
        assert len(calls) == 1


def test_unregistered_arm_derivation_control_rejects_swapped_factory_slots():
    signature = inspect.signature(C.B4ClosedCriticController.invoke)
    assert "arm" not in signature.parameters
    with _pair_fixture() as (pair, _layouts, _calls):
        assert not hasattr(pair.on, "arm")
        assert not hasattr(pair.off, "arm")
    root = Path(tempfile.mkdtemp(prefix="izanagi-b4-arm-parent-")) / "pair"
    _raises(
        C.B4ArmBindingError,
        lambda: C.create_b4_closed_critic_pair_for_test(
            on_cfg=L.default_cfg(reflux=False),
            off_cfg=L.default_cfg(reflux=True),
            artifact_root=root,
            executable=sys.executable,
            runner=lambda *_args, **_kwargs: None,
            environ={"HOME": str(root.parent)},
        ),
        contains="slot on",
    )
    assert not root.exists()


def test_p2_successful_test_only_invocation_records_snapshot_and_returns_data_only():
    with _pair_fixture() as (pair, layouts, calls):
        before = L.LoopState(reverse_recommendations=3)
        campaign_before = {
            campaign_id: _tree_bytes(Path(layout.root))
            for campaign_id, layout in layouts.items()
        }
        invocation = pair.on.invoke(invocation_id="p2-on")
        assert invocation.decision == C.B4CriticDecision(**_DECISION_OBJECT)
        assert before.reverse_recommendations == 3
        receipt = invocation.receipt
        assert receipt.arm == "on"
        assert receipt.evidence_class == "test-only"
        assert receipt.iteration == 1
        assert len(receipt.admitted_view_sha256) == 64
        assert len(receipt.loop_state_sha256) == 64
        assert len(calls) == 1
        sent_payload_bytes = calls[0][1]["input"]
        sent_payload = json.loads(sent_payload_bytes)
        assert set(sent_payload) == {"projected_digest", "result"}
        layout = layouts[receipt.campaign_id]
        assert campaign_before[receipt.campaign_id] == _tree_bytes(Path(layout.root))
        assert receipt.admitted_view_sha256 == hashlib.sha256(
            Path(layout.wal_file).read_bytes()
        ).hexdigest()
        state_bytes = Path(L.loop_state_path(layout)).read_bytes()
        assert receipt.loop_state_sha256 == hashlib.sha256(state_bytes).hexdigest()
        assert receipt.digest_sha256 == hashlib.sha256(
            sent_payload["projected_digest"].encode("utf-8")
        ).hexdigest()
        assert receipt.schema_version == C.B4_CLOSED_CRITIC_RECEIPT_SCHEMA
        assert receipt.decision_sha256 == hashlib.sha256(
            C._canonical_json_bytes(_DECISION_OBJECT)
        ).hexdigest()
        assert receipt.decision_reverse_recommended is False
        assert receipt.evidence_payload_sha256 == hashlib.sha256(
            sent_payload_bytes
        ).hexdigest()
        assert receipt.evidence_argv_sha256 == hashlib.sha256(
            C._canonical_json_bytes(calls[0][0])
        ).hexdigest()
        assert receipt.start_receipt_sha256 == hashlib.sha256(
            invocation.start_receipt_path.read_bytes()
        ).hexdigest()
        forbidden_names = {
            path.name
            for path in invocation.terminal_receipt_path.parents[1].rglob("*")
            if "proposal" in path.name or "checkpoint" in path.name
        }
        assert forbidden_names == set()


def test_unregistered_pair_control_rejects_reused_session_after_byte_recheck():
    context, _pair, _layouts, _calls, on, off = _invoke_pair()
    try:
        C.assert_b4_arm_pair(
            on.terminal_receipt_path,
            off.terminal_receipt_path,
        )
        envelope_path = off.terminal_receipt_path.parent / "envelope_b4-off-1.json"
        envelope = json.loads(envelope_path.read_bytes())
        envelope["session_id"] = on.receipt.session_id
        envelope_bytes = C._canonical_json_bytes(envelope)
        envelope_path.write_bytes(envelope_bytes)
        terminal = json.loads(off.terminal_receipt_path.read_bytes())
        terminal["session_id"] = on.receipt.session_id
        terminal["evidence_raw_envelope_sha256"] = hashlib.sha256(
            envelope_bytes
        ).hexdigest()
        off.terminal_receipt_path.write_bytes(C._canonical_json_bytes(terminal))
        _raises(
            C.B4ReceiptError,
            lambda: C.assert_b4_arm_pair(
                on.terminal_receipt_path,
                off.terminal_receipt_path,
            ),
            contains="session_id",
        )
    finally:
        context.__exit__(None, None, None)


def test_unregistered_pair_control_rejects_reused_provider_identity():
    context, _pair, _layouts, _calls, on, off = _invoke_pair()
    try:
        C.assert_b4_arm_pair(
            on.terminal_receipt_path,
            off.terminal_receipt_path,
        )
        assert on.receipt.provider_instance_id != off.receipt.provider_instance_id
        assert (
            on.receipt.neutral_root_identity_sha256
            != off.receipt.neutral_root_identity_sha256
        )
        terminal = json.loads(off.terminal_receipt_path.read_bytes())
        terminal["provider_instance_id"] = on.receipt.provider_instance_id
        terminal["neutral_root_identity_sha256"] = (
            on.receipt.neutral_root_identity_sha256
        )
        neutral_path = off.terminal_receipt_path.parent / (
            "neutral_root_identity_b4-off-1.json"
        )
        neutral_path.write_bytes(
            (on.terminal_receipt_path.parent / "neutral_root_identity_b4-on-1.json").read_bytes()
        )
        off.terminal_receipt_path.write_bytes(C._canonical_json_bytes(terminal))
        _raises(
            C.B4ReceiptError,
            lambda: C.assert_b4_arm_pair(
                on.terminal_receipt_path,
                off.terminal_receipt_path,
            ),
            contains="provider instance or neutral root",
        )
    finally:
        context.__exit__(None, None, None)


def test_unregistered_payload_exact_key_control_rejects_harmless_extra_key():
    exact = {"projected_digest": "real digest", "result": "rejected"}
    C.validate_b4_critic_payload(exact)
    extra = {**exact, "harmless": "value"}
    _raises(
        C.B4PayloadSchemaError,
        lambda: C.validate_b4_critic_payload(extra),
        contains="exact schema",
    )


def test_m10_p3_response_parser_accepts_exact_five_fields_and_rejects_extra_key():
    raw = json.dumps(_DECISION_OBJECT, separators=(",", ":"))
    decision = C.parse_b4_critic_response(raw)
    assert decision == C.B4CriticDecision(**_DECISION_OBJECT)
    extra = {**_DECISION_OBJECT, "extra": "not admitted"}
    _raises(
        C.B4CriticResponseError,
        lambda: C.parse_b4_critic_response(json.dumps(extra)),
        contains="exact schema",
    )
    duplicated = raw[:-1] + ',"attribution":"duplicate"}'
    _raises(
        C.B4CriticResponseError,
        lambda: C.parse_b4_critic_response(duplicated),
        contains="duplicate key",
    )


def test_r10_response_field_types_have_exact_one_field_positive_negative_pairs():
    raw = json.dumps(_DECISION_OBJECT, separators=(",", ":"))
    assert C.parse_b4_critic_response(raw) == C.B4CriticDecision(
        **_DECISION_OBJECT
    )
    for field_name in ("attribution", "recommend", "avoid", "uncertainty"):
        malformed = {**_DECISION_OBJECT, field_name: 1}
        error = _raises(
            C.B4CriticResponseError,
            lambda malformed=malformed: C.parse_b4_critic_response(
                json.dumps(malformed)
            ),
        )
        assert str(error) == f"critic response {field_name} must be an exact str"
    malformed_bool = {**_DECISION_OBJECT, "reverse_recommended": 1}
    error = _raises(
        C.B4CriticResponseError,
        lambda: C.parse_b4_critic_response(json.dumps(malformed_bool)),
    )
    assert str(error) == (
        "critic response reverse_recommended must be an exact bool"
    )


def test_r10_payload_field_values_have_exact_one_field_positive_negative_pairs():
    positive = {"projected_digest": "digest", "result": "rejected"}
    C.validate_b4_critic_payload(positive)
    empty_digest = {**positive, "projected_digest": ""}
    error = _raises(
        C.B4PayloadSchemaError,
        lambda: C.validate_b4_critic_payload(empty_digest),
    )
    assert str(error) == "projected_digest must be a non-empty exact str"
    non_string_digest = {**positive, "projected_digest": 1}
    error = _raises(
        C.B4PayloadSchemaError,
        lambda: C.validate_b4_critic_payload(non_string_digest),
    )
    assert str(error) == "projected_digest must be a non-empty exact str"
    unknown_result = {**positive, "result": "unknown"}
    error = _raises(
        C.B4PayloadSchemaError,
        lambda: C.validate_b4_critic_payload(unknown_result),
    )
    assert str(error) == "result must be success, fail, or rejected"
    non_string_result = {**positive, "result": 1}
    error = _raises(
        C.B4PayloadSchemaError,
        lambda: C.validate_b4_critic_payload(non_string_result),
    )
    assert str(error) == "result must be success, fail, or rejected"


def test_r9_json_decode_accepts_literal_escape_explanation_and_rejects_json_alias():
    parent = Path(tempfile.mkdtemp(prefix="izanagi-b4-m11-"))
    cfg = L.default_cfg(reflux=False)
    layout = _make_admitted_fixture(parent / "off", cfg, source_tag="m11")
    digest = _admitted_digest(layout, reflux=False)
    campaign_id = str(ident.campaign_id(cfg))
    literal_explanation = digest + "\n" + (
        r"the literal escape \u002fwork is documentation, not a path alias"
    )
    C.assert_no_campaign_identity(
        _canonical_payload(literal_explanation),
        campaign_path=Path(layout.root).resolve(),
        campaign_id=campaign_id,
    )
    escaped_root = str(C.REPOSITORY_ROOT).replace("/", r"\u002f")
    raw_alias_payload = _canonical_payload(
        digest + "\n" + str(C.REPOSITORY_ROOT)
    ).replace(
        str(C.REPOSITORY_ROOT).encode("utf-8"),
        escaped_root.encode("ascii"),
    )
    error = _raises(
        C.B4CampaignDisclosureError,
        lambda: C.assert_no_campaign_identity(
            raw_alias_payload,
            campaign_path=Path(layout.root).resolve(),
            campaign_id=campaign_id,
        ),
    )
    assert error.identity_kind == "repository_root"
    assert error.checked_view == "json-escape-decoded"


def test_r9_quoted_space_path_accepts_policy_digest_and_rejects_normalized_alias():
    parent = Path(tempfile.mkdtemp(prefix="izanagi-b4-space-path-"))
    cfg = L.default_cfg(reflux=True)
    layout = _make_admitted_fixture(parent / "on", cfg, source_tag="space-path")
    digest = _admitted_digest(layout, reflux=True)
    campaign_id = str(ident.campaign_id(cfg))
    C.assert_no_campaign_identity(
        _canonical_payload(digest),
        campaign_path=Path(layout.root).resolve(),
        campaign_id=campaign_id,
    )
    root = C.REPOSITORY_ROOT
    quoted_alias = (
        f'"{root.parent}/component with spaces/../{root.name}"'
    )
    error = _raises(
        C.B4CampaignDisclosureError,
        lambda: C.assert_no_campaign_identity(
            _canonical_payload(digest + "\n" + quoted_alias),
            campaign_path=Path(layout.root).resolve(),
            campaign_id=campaign_id,
        ),
    )
    assert error.identity_kind == "repository_root"
    assert error.checked_view == "path-lexically-normalized"


def test_m12_normalized_view_accepts_real_digest_and_rejects_parent_alias():
    parent = Path(tempfile.mkdtemp(prefix="izanagi-b4-m12-"))
    cfg = L.default_cfg(reflux=True)
    layout = _make_admitted_fixture(parent / "on", cfg, source_tag="m12")
    digest = _admitted_digest(layout, reflux=True)
    campaign_id = str(ident.campaign_id(cfg))
    C.assert_no_campaign_identity(
        _canonical_payload(digest),
        campaign_path=Path(layout.root).resolve(),
        campaign_id=campaign_id,
    )
    root = C.REPOSITORY_ROOT
    aliased = root.parent / "b4-alias-component" / ".." / root.name
    assert str(root) not in str(aliased)
    error = _raises(
        C.B4CampaignDisclosureError,
        lambda: C.assert_no_campaign_identity(
            _canonical_payload(digest + "\n" + str(aliased)),
            campaign_path=Path(layout.root).resolve(),
            campaign_id=campaign_id,
        ),
    )
    assert error.identity_kind == "repository_root"
    assert error.checked_view == "path-lexically-normalized"


def test_m13_success_receipt_separates_claims_and_binds_raw_envelope_payload_argv():
    with _pair_fixture() as (pair, _layouts, _calls):
        invocation = pair.on.invoke(invocation_id="m13-on")
        receipt = invocation.receipt
        envelope = invocation.terminal_receipt_path.parent / "envelope_m13-on.json"
        payload = invocation.terminal_receipt_path.parent / "payload_m13-on.json"
        assert receipt.evidence_raw_envelope_sha256 == hashlib.sha256(
            envelope.read_bytes()
        ).hexdigest()
        assert receipt.evidence_payload_sha256 == hashlib.sha256(
            payload.read_bytes()
        ).hexdigest()
        assert len(receipt.evidence_argv_sha256) == 64
        assert receipt.claimed_observed_tool_events == ()
        terminal = json.loads(invocation.terminal_receipt_path.read_bytes())
        assert "claimed_observed_tool_events" in terminal
        assert "observed_tool_events" not in terminal
        assert terminal["evidence_raw_envelope_sha256"] == (
            receipt.evidence_raw_envelope_sha256
        )


def test_m14_success_and_failure_both_create_start_and_exclusive_terminal_receipts():
    with _pair_fixture() as (pair, _layouts, _calls):
        success = pair.on.invoke(invocation_id="m14-success")
        assert json.loads(success.start_receipt_path.read_bytes())["status"] == "started"
        assert json.loads(success.terminal_receipt_path.read_bytes())["status"] == "success"
    updates = {
        "num_turns": 2,
        "permission_denials": [{"tool": "Bash"}],
        "usage": {"server_tool_use": {"web_search_requests": 1}},
    }
    with _pair_fixture(envelope_updates=updates) as (pair, _layouts, _calls):
        _raises(Exception, lambda: pair.on.invoke(invocation_id="m14-failure"))
        start = pair.on._B4ClosedCriticController__artifact_root / (
            "receipt_m14-failure_start.json"
        )
        terminal = pair.on._B4ClosedCriticController__artifact_root / (
            "receipt_m14-failure_terminal.json"
        )
        assert json.loads(start.read_bytes())["status"] == "started"
        failure = json.loads(terminal.read_bytes())
        assert failure["status"] == "failure"
        assert failure["error_signature"] == (
            "[closed-critic-error] unclassified"
        )
        assert len(failure["evidence_raw_envelope_sha256"]) == 64


def test_m15_m20_projection_manifest_exactly_hashes_all_independent_sources():
    manifest = C.projection_closure_manifest()
    repository_root = _ORCH.parent
    expected_paths = {
        "orchestrator/campaign/p3_b4_closed_critic.py": (
            repository_root / "orchestrator/campaign/p3_b4_closed_critic.py"
        ),
        "orchestrator/campaign/claude_projected_provider.py": (
            repository_root / "orchestrator/campaign/claude_projected_provider.py"
        ),
        "orchestrator/campaign/p3_s4_loop.py": (
            repository_root / "orchestrator/campaign/p3_s4_loop.py"
        ),
        "orchestrator/campaign/artifact_admission.py": (
            repository_root / "orchestrator/campaign/artifact_admission.py"
        ),
        "orchestrator/campaign/s8b_prediction_runner.py": (
            repository_root / "orchestrator/campaign/s8b_prediction_runner.py"
        ),
        "orchestrator/campaign/role_session_isolation.py": (
            repository_root / "orchestrator/campaign/role_session_isolation.py"
        ),
        "orchestrator/campaign/p3_b4_admission_record.py": (
            repository_root / "orchestrator/campaign/p3_b4_admission_record.py"
        ),
        "orchestrator/campaign/p3_b4_launcher.py": (
            repository_root / "orchestrator/campaign/p3_b4_launcher.py"
        ),
        "orchestrator/campaign/p3_b4_protocol.py": (
            repository_root / "orchestrator/campaign/p3_b4_protocol.py"
        ),
        "orchestrator/critic/digest.py": (
            repository_root / "orchestrator/critic/digest.py"
        ),
        "orchestrator/critic/identity_projection.py": (
            repository_root / "orchestrator/critic/identity_projection.py"
        ),
        ".claude/agents/critic.md": repository_root / ".claude/agents/critic.md",
    }
    expected_contract = _EXPECTED_MEDIATED_CRITIC_CONTRACT.encode("utf-8")
    expected_entries = {
        key: hashlib.sha256(path.read_bytes()).hexdigest()
        for key, path in expected_paths.items()
    }
    expected_entries["mediated-contract:utf-8"] = hashlib.sha256(
        expected_contract
    ).hexdigest()
    assert manifest == {
        "schema_version": "p3-b4-projection-closure/v1",
        "entries": expected_entries,
    }
    for record_repository_path in (
        _REQUIRED_ADMISSION_RECORD_REPOSITORY_PATH_BY_DRIVER.values()
    ):
        assert record_repository_path not in manifest["entries"]
    expected = hashlib.sha256(C._canonical_json_bytes(manifest)).hexdigest()
    assert C.projection_sha256() == expected


def test_driver_specific_projection_closure_pins_only_selected_consumer():
    entries = {
        kind: set(C.projection_closure_manifest(kind)["entries"])
        for kind in ("base", "sort", "trigger")
    }
    sort_path = "orchestrator/campaign/p3_s4_loop_sort.py"
    trigger_path = "orchestrator/campaign/p3_s4_loop_trigger_gating.py"
    assert sort_path not in entries["base"]
    assert trigger_path not in entries["base"]
    assert sort_path in entries["sort"]
    assert trigger_path not in entries["sort"]
    assert trigger_path in entries["trigger"]
    assert sort_path not in entries["trigger"]
    assert len({C.projection_sha256(kind) for kind in entries}) == 3


@pytest.mark.parametrize("driver_kind", ("base", "sort", "trigger"))
def test_admission_projection_expectation_selects_the_pair_driver_closure(
    driver_kind,
):
    parent = Path(tempfile.mkdtemp(prefix=f"izanagi-b4-{driver_kind}-admission-"))
    constructions = _capture_certified_pair_construction(
        parent,
        driver_kind=driver_kind,
    )
    assert len(constructions) == 2
    expected = C.projection_sha256(driver_kind)
    expected_by_driver = {
        kind: C.projection_sha256(kind)
        for kind in A.B4_PROJECTION_DRIVER_KINDS
    }
    assert all(
        item["binding"].driver_kind == driver_kind
        and item["initial_projection_sha256"] == expected
        and (
            item["verified_admission"]
            .expected_closed_critic_projection_closure_sha256
            == expected
        )
        and dict(
            item["verified_admission"]
            .expected_closed_critic_projection_closure_sha256_by_driver
        ) == expected_by_driver
        for item in constructions
    )


def test_a4_snapshot_binding_accepts_stable_state_and_rejects_iteration_mismatch():
    with _pair_fixture() as (pair, _layouts, _calls):
        invocation = pair.on.invoke(invocation_id="snapshot-positive")
        assert invocation.receipt.iteration == 1
        assert len(invocation.receipt.admitted_view_sha256) == 64
        assert len(invocation.receipt.loop_state_sha256) == 64
    with _pair_fixture(bad_on_iteration=True) as (pair, _layouts, calls):
        _raises(
            C.B4SnapshotError,
            lambda: pair.on.invoke(invocation_id="snapshot-negative"),
            contains="whiteboard entry iteration",
        )
        assert calls == []
        terminal = pair.on._B4ClosedCriticController__artifact_root / (
            "receipt_snapshot-negative_terminal.json"
        )
        assert json.loads(terminal.read_bytes())["status"] == "failure"


def test_p4_test_only_pair_reports_precursor_differences_without_rejecting_them():
    context, _pair, _layouts, _calls, on, off = _invoke_pair()
    try:
        comparison = C.assert_b4_arm_pair(
            on.terminal_receipt_path,
            off.terminal_receipt_path,
        )
        assert comparison.iteration_equal
        assert not comparison.admitted_view_sha256_equal
        assert not comparison.loop_state_sha256_equal
    finally:
        context.__exit__(None, None, None)


def test_certified_pair_gate_rejects_test_only_pair_while_legacy_gate_accepts_it():
    context, pair, _layouts, _calls, on, off = _invoke_pair()
    try:
        C.assert_b4_arm_pair(
            on.terminal_receipt_path,
            off.terminal_receipt_path,
        )
        _raises(
            C.B4ReceiptError,
            lambda: C.assert_b4_certified_arm_pair(
                pair,
                on.terminal_receipt_path,
                off.terminal_receipt_path,
                admission_record_path=Path("missing-admission.json"),
            ),
            contains="live production factory pair",
        )
    finally:
        context.__exit__(None, None, None)


def test_r1_terminal_pair_revalidation_rejects_status_and_payload_byte_tamper():
    context, _pair, _layouts, _calls, on, off = _invoke_pair()
    try:
        C.assert_b4_arm_pair(
            on.terminal_receipt_path,
            off.terminal_receipt_path,
        )
        terminal_bytes = on.terminal_receipt_path.read_bytes()
        terminal = json.loads(terminal_bytes)
        terminal["status"] = "failure"
        on.terminal_receipt_path.write_bytes(C._canonical_json_bytes(terminal))
        _raises(
            C.B4ReceiptError,
            lambda: C.assert_b4_arm_pair(
                on.terminal_receipt_path,
                off.terminal_receipt_path,
            ),
            contains="success terminal receipt",
        )
        on.terminal_receipt_path.write_bytes(terminal_bytes)

        payload_path = on.terminal_receipt_path.parent / "payload_b4-on-1.json"
        payload_bytes = payload_path.read_bytes()
        payload = json.loads(payload_bytes)
        payload["projected_digest"] += "tamper"
        payload_path.write_bytes(C._canonical_json_bytes(payload))
        _raises(
            C.B4ReceiptError,
            lambda: C.assert_b4_arm_pair(
                on.terminal_receipt_path,
                off.terminal_receipt_path,
            ),
            contains="payload hash does not match",
        )
        payload_path.write_bytes(payload_bytes)
    finally:
        context.__exit__(None, None, None)


def test_r1_terminal_pair_revalidation_rejects_raw_envelope_byte_tamper():
    context, _pair, _layouts, _calls, on, off = _invoke_pair()
    try:
        C.assert_b4_arm_pair(
            on.terminal_receipt_path,
            off.terminal_receipt_path,
        )
        envelope_path = on.terminal_receipt_path.parent / "envelope_b4-on-1.json"
        envelope_path.write_bytes(envelope_path.read_bytes() + b"\n")
        error = _raises(
            C.B4ReceiptError,
            lambda: C.assert_b4_arm_pair(
                on.terminal_receipt_path,
                off.terminal_receipt_path,
            ),
        )
        assert str(error) == "raw envelope hash does not match its bytes"
    finally:
        context.__exit__(None, None, None)


def test_m16_sent_on_off_payload_bytes_match_independent_admitted_view_digests():
    with _pair_fixture() as (pair, layouts, calls):
        loop_state_before = {
            campaign_id: Path(L.loop_state_path(layout)).read_bytes()
            for campaign_id, layout in layouts.items()
        }
        campaign_before = {
            campaign_id: _tree_bytes(Path(layout.root))
            for campaign_id, layout in layouts.items()
        }
        on = pair.on.invoke(invocation_id="m16-on")
        off = pair.off.invoke(invocation_id="m16-off")
        assert len(calls) == 2

        for invocation, call, reflux in (
            (on, calls[0], True),
            (off, calls[1], False),
        ):
            receipt = invocation.receipt
            layout = layouts[receipt.campaign_id]
            view = require_admitted_campaign(
                layout,
                purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
            )
            expected_digest = L.make_critic_digest(
                view,
                tag="p3-b4-closed-critic",
                reflux=reflux,
                identity_projection=L.make_critic_identity_projection(view),
            )
            state = L.state_from_dict(
                json.loads(Path(L.loop_state_path(layout)).read_bytes())
            )
            expected_payload_bytes = C._canonical_json_bytes({
                "projected_digest": expected_digest,
                "result": state.whiteboard[-1].result,
            })
            sent_payload_bytes = call[1]["input"]
            assert sent_payload_bytes == expected_payload_bytes
            assert json.loads(sent_payload_bytes)["projected_digest"].encode(
                "utf-8"
            ) == expected_digest.encode("utf-8")
            assert receipt.digest_sha256 == hashlib.sha256(
                expected_digest.encode("utf-8")
            ).hexdigest()
            assert receipt.decision_sha256 == hashlib.sha256(
                C._canonical_json_bytes(_DECISION_OBJECT)
            ).hexdigest()
            assert receipt.decision_reverse_recommended is False
            assert receipt.evidence_payload_sha256 == hashlib.sha256(
                sent_payload_bytes
            ).hexdigest()
            assert receipt.evidence_argv_sha256 == hashlib.sha256(
                C._canonical_json_bytes(call[0])
            ).hexdigest()
            assert receipt.admitted_view_sha256 == hashlib.sha256(
                Path(layout.wal_file).read_bytes()
            ).hexdigest()
            assert receipt.loop_state_sha256 == hashlib.sha256(
                loop_state_before[receipt.campaign_id]
            ).hexdigest()
            assert receipt.start_receipt_sha256 == hashlib.sha256(
                invocation.start_receipt_path.read_bytes()
            ).hexdigest()
            assert campaign_before[receipt.campaign_id] == _tree_bytes(
                Path(layout.root)
            )

        on_payload = calls[0][1]["input"]
        off_payload = calls[1][1]["input"]
        assert b"b4-fixture-reject" in on_payload
        assert b"b4-fixture-reject" not in off_payload
        C.assert_b4_arm_pair(
            on.terminal_receipt_path,
            off.terminal_receipt_path,
        )


def test_m17_pair_id_accepts_one_factory_and_rejects_mixed_factories_only():
    with _pair_fixture() as (pair_one, _layouts_one, _calls_one):
        one_on = pair_one.on.invoke(invocation_id="m17-one-on")
        one_off = pair_one.off.invoke(invocation_id="m17-one-off")
        C.assert_b4_arm_pair(
            one_on.terminal_receipt_path,
            one_off.terminal_receipt_path,
        )
        with _pair_fixture() as (
            pair_two,
            _layouts_two,
            _calls_two,
        ):
            pair_two.on.invoke(invocation_id="m17-two-on")
            two_off = pair_two.off.invoke(invocation_id="m17-two-off")
            assert one_on.receipt.session_id != two_off.receipt.session_id
            assert one_on.receipt.provider_instance_id != (
                two_off.receipt.provider_instance_id
            )
            assert one_on.receipt.pair_id != two_off.receipt.pair_id
            _raises(
                C.B4ReceiptError,
                lambda: C.assert_b4_arm_pair(
                    one_on.terminal_receipt_path,
                    two_off.terminal_receipt_path,
                ),
                contains="different pair_id",
            )


def test_m18_certified_factory_has_no_executable_seam_and_resolves_fixed_claude():
    parent = Path(tempfile.mkdtemp(prefix="izanagi-b4-certified-executable-"))
    admission = _committed_admission_fixture()
    signature = inspect.signature(C.create_b4_closed_critic_pair)
    assert "executable" not in signature.parameters
    assert "which" not in signature.parameters
    decoy = str(Path("/bin/sh").resolve())
    rejected_root = parent / "rejected"
    on_cfg, off_cfg = _marked_driver_configs()
    launch_context = _production_launch_context(on_cfg, admission=admission)
    error = _raises(
        TypeError,
        lambda: C.create_b4_closed_critic_pair(
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            artifact_root=rejected_root,
            admission_record_path=admission.record_path,
            expected_driver_kind="base",
            _b4_launch_context=launch_context,
            repository_root=admission.repository,
            executable=decoy,
            environ={"HOME": str(parent)},
        ),
    )
    assert "unexpected keyword argument 'executable'" in str(error)
    assert not rejected_root.exists()

    constructions = _capture_certified_pair_construction(parent)
    expected = str(Path(sys.executable).resolve())
    assert all(item["executable"] == expected for item in constructions)
    assert all(item["executable"] != decoy for item in constructions)


def test_m19_pair_gate_accepts_terminal_paths_and_rejects_promoted_dataclasses():
    signature = inspect.signature(C.create_b4_closed_critic_pair_for_test)
    assert {"runner", "executable"} <= set(signature.parameters)
    assert "evidence_class" not in signature.parameters
    rejected_parent = Path(tempfile.mkdtemp(prefix="izanagi-b4-test-class-"))
    rejected_root = rejected_parent / "rejected"
    injected_runner, _calls = _fake_runner_factory()
    error = _raises(
        TypeError,
        lambda: C.create_b4_closed_critic_pair_for_test(
            on_cfg=L.default_cfg(reflux=True),
            off_cfg=L.default_cfg(reflux=False),
            artifact_root=rejected_root,
            executable=sys.executable,
            runner=injected_runner,
            evidence_class="certified",
        ),
    )
    assert "unexpected keyword argument 'evidence_class'" in str(error)
    assert not rejected_root.exists()

    test_context, test_pair, _layouts, _calls, test_on, test_off = _invoke_pair()
    try:
        assert test_on.receipt.evidence_class == "test-only"
        assert test_off.receipt.evidence_class == "test-only"
        C.assert_b4_arm_pair(
            test_on.terminal_receipt_path,
            test_off.terminal_receipt_path,
        )
        promoted_on = replace(test_on.receipt, evidence_class="certified")
        promoted_off = replace(test_off.receipt, evidence_class="certified")
        _raises(
            C.B4ReceiptError,
            lambda: C.assert_b4_arm_pair(promoted_on, promoted_off),
            contains="terminal receipt file paths",
        )
        promoted_on_terminal = json.loads(
            test_on.terminal_receipt_path.read_bytes()
        )
        promoted_on_terminal["evidence_class"] = "certified"
        test_on.terminal_receipt_path.write_bytes(
            C._canonical_json_bytes(promoted_on_terminal)
        )
        _raises(
            C.B4ReceiptError,
            lambda: C.assert_b4_arm_pair(
                test_on.terminal_receipt_path,
                test_off.terminal_receipt_path,
            ),
            contains="start and terminal receipt differ: evidence_class",
        )

        promoted_on_start = json.loads(test_on.start_receipt_path.read_bytes())
        promoted_on_start["evidence_class"] = "certified"
        promoted_on_start_bytes = C._canonical_json_bytes(promoted_on_start)
        test_on.start_receipt_path.write_bytes(promoted_on_start_bytes)
        promoted_on_terminal["start_receipt_sha256"] = hashlib.sha256(
            promoted_on_start_bytes
        ).hexdigest()
        test_on.terminal_receipt_path.write_bytes(
            C._canonical_json_bytes(promoted_on_terminal)
        )
        _raises(
            C.B4ReceiptError,
            lambda: C.assert_b4_arm_pair(
                test_on.terminal_receipt_path,
                test_off.terminal_receipt_path,
            ),
            contains="different evidence_class",
        )

        promoted_off_start = json.loads(
            test_off.start_receipt_path.read_bytes()
        )
        promoted_off_start["evidence_class"] = "certified"
        promoted_off_start_bytes = C._canonical_json_bytes(promoted_off_start)
        test_off.start_receipt_path.write_bytes(promoted_off_start_bytes)
        promoted_off_terminal = json.loads(
            test_off.terminal_receipt_path.read_bytes()
        )
        promoted_off_terminal["evidence_class"] = "certified"
        promoted_off_terminal["start_receipt_sha256"] = hashlib.sha256(
            promoted_off_start_bytes
        ).hexdigest()
        test_off.terminal_receipt_path.write_bytes(
            C._canonical_json_bytes(promoted_off_terminal)
        )
        C.assert_b4_arm_pair(
            test_on.terminal_receipt_path,
            test_off.terminal_receipt_path,
        )
        _raises(
            C.B4ReceiptError,
            lambda: C.assert_b4_certified_arm_pair(
                test_pair,
                test_on.terminal_receipt_path,
                test_off.terminal_receipt_path,
                admission_record_path=Path("missing-admission.json"),
            ),
            contains="live production factory pair",
        )
    finally:
        test_context.__exit__(None, None, None)


def test_a3_shared_tracker_accepts_unique_sessions_and_rejects_cross_arm_reuse():
    with _pair_fixture() as (pair, _layouts, _calls):
        pair.on.invoke(invocation_id="tracker-on-positive")
        pair.off.invoke(invocation_id="tracker-off-positive")
    with _pair_fixture(repeated_session=True) as (pair, _layouts, _calls):
        pair.on.invoke(invocation_id="tracker-on-negative")
        _raises(
            Exception,
            lambda: pair.off.invoke(invocation_id="tracker-off-negative"),
        )
        terminal = pair.off._B4ClosedCriticController__artifact_root / (
            "receipt_tracker-off-negative_terminal.json"
        )
        assert json.loads(terminal.read_bytes())["status"] == "failure"


def test_a7_receipt_names_exact_literal_guarantee_and_indirect_non_guarantees():
    with _pair_fixture() as (pair, _layouts, _calls):
        receipt = pair.on.invoke(invocation_id="a7-fields").receipt
        assert receipt.exact_identity_literals_absent_from_canonical_payload is True
        joined = " ".join(receipt.identity_non_guarantees)
        for phrase in ("variant labels", "src tokens", "genome labels", "WAL"):
            assert phrase in joined
        assert "PATH" in " ".join(receipt.trust_non_guarantees)
        assert "same-process Python" in " ".join(receipt.trust_non_guarantees)
        assert "unreported tool events" in " ".join(
            receipt.capability_non_guarantees
        )
        assert "logical generation" in " ".join(
            receipt.snapshot_non_guarantees
        )
        assert "storage failure" in " ".join(receipt.storage_non_guarantees)


def test_a8_parser_returns_reverse_boolean_as_data_without_state_or_proposal_fold():
    state = L.LoopState(reverse_recommendations=5)
    value = {**_DECISION_OBJECT, "reverse_recommended": True}
    decision = C.parse_b4_critic_response(json.dumps(value))
    assert decision.reverse_recommended is True
    assert state.reverse_recommendations == 5
    with _pair_fixture() as (pair, layouts, _calls):
        campaign_id = str(ident.campaign_id(L.default_cfg(reflux=True)))
        layout = layouts[campaign_id]
        state_path = Path(L.loop_state_path(layout))
        actual_state_before = state_path.read_bytes()
        campaign_before = _tree_bytes(Path(layout.root))
        invocation = pair.on.invoke(invocation_id="r6-no-fold")
        assert state_path.read_bytes() == actual_state_before
        assert _tree_bytes(Path(layout.root)) == campaign_before
        artifact_root = invocation.terminal_receipt_path.parents[1]
        forbidden = [
            path
            for path in artifact_root.rglob("*")
            if "proposal" in path.name.lower()
            or "checkpoint" in path.name.lower()
        ]
        assert forbidden == []
    assert not any(
        name in C.B4ClosedCriticController.invoke.__code__.co_names
        for name in ("_fold_critic_reverse", "save_loop_state", "project_whiteboard")
    )


def test_a9_invocation_id_single_use_and_timeout_have_positive_terminal_controls():
    with _pair_fixture() as (pair, _layouts, _calls):
        invocation = pair.on.invoke(invocation_id="safe.id-1")
        assert invocation.receipt.status == "success"
        _raises(
            C.B4ReceiptError,
            lambda: pair.on.invoke(invocation_id="second-id"),
            contains="single-use",
        )
    with _pair_fixture() as (pair, _layouts, calls):
        _raises(
            C.B4ReceiptError,
            lambda: pair.on.invoke(invocation_id="../escape"),
            contains="closed character set",
        )
        assert calls == []
    with _pair_fixture(timeout=True) as (pair, _layouts, _calls):
        _raises(Exception, lambda: pair.on.invoke(invocation_id="timeout-1"))
        terminal = pair.on._B4ClosedCriticController__artifact_root / (
            "receipt_timeout-1_terminal.json"
        )
        timeout_receipt = json.loads(terminal.read_bytes())
        assert timeout_receipt["status"] == "timeout"
        assert timeout_receipt["error_signature"] == (
            "[closed-critic-error] timeout"
        )


def test_r11_terminal_slot_precedes_query_and_start_failure_gets_terminal_record():
    observed = []

    def observe_reserved_terminal(parent: Path) -> None:
        terminal = parent / "artifacts/on/receipt_r11-reserved_terminal.json"
        observed.append((terminal.is_file(), terminal.read_bytes()))

    with _pair_fixture(query_observer=observe_reserved_terminal) as (
        pair,
        _layouts,
        calls,
    ):
        success = pair.on.invoke(invocation_id="r11-reserved")
        assert observed == [(True, b"")]
        assert len(calls) == 1
        assert json.loads(success.terminal_receipt_path.read_bytes())[
            "status"
        ] == "success"

    with _pair_fixture() as (pair, _layouts, calls):
        artifact_root = pair.on._B4ClosedCriticController__artifact_root
        with unittest.mock.patch.object(
            C,
            "_write_exclusive_json",
            side_effect=C.B4ReceiptError("simulated start receipt storage failure"),
        ):
            _raises(
                C.B4ReceiptError,
                lambda: pair.on.invoke(invocation_id="r11-start-failure"),
                contains="simulated start receipt storage failure",
            )
        assert calls == []
        terminal = artifact_root / "receipt_r11-start-failure_terminal.json"
        failure = json.loads(terminal.read_bytes())
        assert failure["status"] == "failure"
        assert failure["start_receipt_sha256"] is None


def test_a13_fake_envelope_positive_control_and_combined_tool_surface_negative():
    with _pair_fixture() as (pair, _layouts, _calls):
        receipt = pair.on.invoke(invocation_id="a13-positive").receipt
        assert receipt.evidence_num_turns == 1
        assert receipt.evidence_permission_denials_empty is True
        assert receipt.evidence_server_tool_use_all_zero is True
    updates = {
        "permission_denials": [{"tool": "Bash"}],
        "num_turns": 2,
        "usage": {"server_tool_use": {"web_search_requests": 1}},
    }
    with _pair_fixture(envelope_updates=updates) as (pair, _layouts, _calls):
        _raises(Exception, lambda: pair.on.invoke(invocation_id="a13-negative"))
        terminal = pair.on._B4ClosedCriticController__artifact_root / (
            "receipt_a13-negative_terminal.json"
        )
        failure = json.loads(terminal.read_bytes())
        assert failure["status"] == "failure"
        envelope = pair.on._B4ClosedCriticController__artifact_root / (
            "envelope_a13-negative.json"
        )
        raw = json.loads(envelope.read_bytes())
        assert raw["permission_denials"]
        assert raw["num_turns"] == 2
        assert any(raw["usage"]["server_tool_use"].values())


def _assert_single_tool_surface_rejection(
    *, updates: dict, invocation_id: str, reason: str,
) -> None:
    with _pair_fixture() as (pair, _layouts, _calls):
        positive = pair.on.invoke(invocation_id=f"{invocation_id}-positive")
        assert positive.receipt.evidence_num_turns == 1
        assert positive.receipt.evidence_permission_denials_empty is True
        assert positive.receipt.evidence_server_tool_use_all_zero is True
        envelope = json.loads(
            (
                positive.terminal_receipt_path.parent
                / f"envelope_{invocation_id}-positive.json"
            ).read_bytes()
        )
        assert envelope["usage"]["server_tool_use"] == {}

    with _pair_fixture(envelope_updates=updates) as (pair, _layouts, _calls):
        error = _raises(
            C.PredictionRunnerError,
            lambda: pair.on.invoke(invocation_id=f"{invocation_id}-negative"),
        )
        assert str(error) == reason
        terminal = pair.on._B4ClosedCriticController__artifact_root / (
            f"receipt_{invocation_id}-negative_terminal.json"
        )
        failure = json.loads(terminal.read_bytes())
        assert failure["status"] == "failure"
        assert failure["error_type"] == "PredictionRunnerError"
        assert failure["error_signature"] == (
            "[closed-critic-error] unclassified"
        )


def test_r4_num_turns_gate_has_one_field_positive_negative_pair():
    _assert_single_tool_surface_rejection(
        updates={"num_turns": 2},
        invocation_id="r4-turns",
        reason="claude envelope num_turns は 1 固定",
    )


def test_r4_permission_denials_gate_has_one_field_positive_negative_pair():
    _assert_single_tool_surface_rejection(
        updates={"permission_denials": [{"tool": "Bash"}]},
        invocation_id="r4-denials",
        reason="claude envelope permission_denials は [] 固定",
    )


def test_r4_server_tool_use_gate_has_one_field_positive_negative_pair():
    _assert_single_tool_surface_rejection(
        updates={"usage": {"server_tool_use": {"web_search_requests": 1}}},
        invocation_id="r4-tools",
        reason="server tool use を観測したため拒否",
    )


def test_r7_a10_thin_cli_drives_factory_both_arms_pair_gate_and_failure_rc():
    """M17: the retired real CLI always directs callers to the launcher."""
    factory_spy = unittest.mock.Mock()
    error = _raises(
        B4L.B4LauncherAuthorizationError,
        lambda: C.main(
            ["--artifact-root", "/tmp/retired"],
            pair_factory=factory_spy,
        ),
    )
    assert "orchestrator.campaign.p3_b4_launcher" in str(error)
    assert factory_spy.call_count == 0


def test_launcher_positive_uses_real_factory_and_real_base_main_for_commit(
    monkeypatch,
):
    """Route one COMMIT while leaving factory, driver main, and WAL unpatched.

    Replaced targets: ``C.REPOSITORY_ROOT``, ``C.ROLE_FILE``,
    ``C.shutil.which``, ``C.B4ClosedCriticController.__init__`` and its runner,
    ``C.exploration_campaign_layout``, ``C._load_stable_snapshot``,
    ``C.require_admitted_campaign``, ``C.make_critic_digest``,
    ``C.make_critic_identity_projection``, ``B4L.exploration_campaign_layout``,
    ``L.exploration_campaign_layout``, ``L.ident.ensure_resumable_attempts``,
    ``patchharness.assert_pinned_clean``, ``p2_2._assert_single_tenant``,
    ``L._run_one_iteration_resolved``, ``L.require_admitted_campaign``,
    ``L.make_critic_identity_projection``, and ``L.make_critic_digest``.
    This positive proves routing, not the substance of the scientific work.
    It is not a substitute for any M01-M18 negative.
    """
    from orchestrator.campaign import p2_2, patchharness

    admission = _committed_admission_fixture()
    config_context = B4L.create_b4_launch_context_for_test(
        driver_kind="base",
    )
    on_cfg, off_cfg = B4L._driver_configs("base", config_context)
    parent = Path(tempfile.mkdtemp(prefix="izanagi-b4-launch-positive-"))
    layouts = {}
    for cfg, source in ((on_cfg, "launcher-on"), (off_cfg, "launcher-off")):
        campaign_id = str(ident.campaign_id(cfg))
        layouts[campaign_id] = _make_admitted_fixture(
            parent / campaign_id,
            cfg,
            source_tag=source,
        )
        state = L.load_loop_state(layouts[campaign_id])
        assert state is not None
        state.start_wall = time.time()
        L.save_loop_state(layouts[campaign_id], state)
    proposal = parent / "proposal.json"
    stdout = io.StringIO()
    runner, runner_calls = _fake_runner_factory()
    commit_calls = []
    controller_init = C.B4ClosedCriticController.__init__

    class ReadySignal:
        def readline(self):
            terminal = Path(stdout.getvalue().strip())
            terminal_sha256 = hashlib.sha256(terminal.read_bytes()).hexdigest()
            proposal.write_text(json.dumps({
                "planner": {
                    "axis": L.MARKER_ID,
                    "direction": "increase",
                    "magnitude": "small",
                },
                "coder": {
                    "axis": L.MARKER_ID,
                    "value": 20.0,
                    "implementation": "double now_backoff = 20.0;",
                },
                L.B4_PROPOSAL_RECEIPT_SHA256_KEY: terminal_sha256,
            }), encoding="utf-8")
            return "ready\n"

    def layout_for(campaign_id):
        return layouts[campaign_id]

    def fixture_synthesis(
        _cfg, _perf, planner, _coder, state, _sub, do_build,
        layout, _contract, _resolved_site, **_kwargs,
    ):
        assert do_build is True
        payload = {"launcher_positive": True}
        record = commit_receipt_support.log_receipted_commit(
            layout,
            "launcher-positive-variant",
            L.ENV_TAG,
            payload,
        )
        commit_calls.append(record)
        L.project_whiteboard(state, planner, "success", delta_pct=None)
        return {
            "outcome": "certified",
            "variant": record.variant,
            "fitness_tps": 1.0,
            "verdict": "PASS",
            "records": {L.STAGE_COMMIT: record.payload},
        }

    def controller_init_with_fixture_runner(self, **kwargs):
        controller_init(self, **kwargs)
        self._B4ClosedCriticController__provider._runner = runner

    def stable_snapshot(binding):
        layout = CampaignLayout(str(binding.layout_root))
        wal_bytes = Path(layout.wal_file).read_bytes()
        state_bytes = Path(L.loop_state_path(layout)).read_bytes()
        state = L.state_from_dict(json.loads(state_bytes))
        return C._Snapshot(
            view=object(),
            wal_bytes=wal_bytes,
            loop_state_bytes=state_bytes,
            iteration=state.iteration,
            whiteboard_entry=state.whiteboard[-1],
        )

    monkeypatch.setattr(C, "REPOSITORY_ROOT", admission.repository)
    monkeypatch.setattr(C, "ROLE_FILE", admission.role_file)
    monkeypatch.setattr(C.shutil, "which", lambda _name: sys.executable)
    monkeypatch.setattr(
        C.B4ClosedCriticController,
        "__init__",
        controller_init_with_fixture_runner,
    )
    monkeypatch.setattr(C, "exploration_campaign_layout", layout_for)
    monkeypatch.setattr(C, "_load_stable_snapshot", stable_snapshot)
    monkeypatch.setattr(C, "require_admitted_campaign", lambda *_a, **_k: object())
    monkeypatch.setattr(C, "make_critic_digest", lambda *_a, **_k: "digest")
    monkeypatch.setattr(
        C, "make_critic_identity_projection", lambda _view: object(),
    )
    monkeypatch.setattr(B4L, "exploration_campaign_layout", layout_for)
    monkeypatch.setattr(L, "exploration_campaign_layout", layout_for)
    monkeypatch.setattr(L.ident, "ensure_resumable_attempts", lambda *_a, **_k: None)
    monkeypatch.setattr(patchharness, "assert_pinned_clean", lambda *_a: None)
    monkeypatch.setattr(p2_2, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(L, "_run_one_iteration_resolved", fixture_synthesis)
    monkeypatch.setattr(L, "require_admitted_campaign", lambda *_a, **_k: object())
    monkeypatch.setattr(
        L, "make_critic_identity_projection", lambda _view: object(),
    )
    monkeypatch.setattr(L, "make_critic_digest", lambda *_a, **_k: "digest")

    rc = B4L.launch_continuation(
        driver_kind="base",
        arm="on",
        admission_record_path=admission.record_path,
        artifact_root=parent / "critic-artifacts",
        proposal_path=proposal,
        stdin=ReadySignal(),
        stdout=stdout,
    )
    assert rc == 0
    assert B4L.DRIVER_REGISTRY["base"] is L.main
    assert len(runner_calls) == 2
    assert len(commit_calls) == 1
    assert commit_calls[0].stage == L.STAGE_COMMIT
    selected_layout = layouts[str(ident.campaign_id(on_cfg))]
    assert (Path(selected_layout.root) / B4L.B4_LAUNCH_SIDECAR).is_file()
    assert Path(L.loop_state_path(selected_layout)).is_file()


def test_receipt_v3_binds_decision_without_copying_natural_language():
    with _certified_pair_fixture(reverse_recommended=True) as (
        pair, _cfg, _layout, _calls,
    ):
        invocation = pair.on.invoke(invocation_id="receipt-v3-decision")
        receipt = invocation.receipt
        expected = {**_DECISION_OBJECT, "reverse_recommended": True}
        assert receipt.schema_version == C.B4_CLOSED_CRITIC_RECEIPT_SCHEMA
        assert receipt.decision_sha256 == hashlib.sha256(
            C._canonical_json_bytes(expected)
        ).hexdigest()
        assert receipt.decision_reverse_recommended is True
        terminal_bytes = invocation.terminal_receipt_path.read_bytes()
        terminal = json.loads(terminal_bytes)
        assert set(terminal) == C._SUCCESS_TERMINAL_KEYS
        for natural_field in ("attribution", "recommend", "avoid", "uncertainty"):
            assert natural_field not in terminal
            assert expected[natural_field].encode("utf-8") not in terminal_bytes

        terminal["decision_sha256"] = "0" * 64
        invocation.terminal_receipt_path.write_bytes(
            C._canonical_json_bytes(terminal)
        )
        _raises(
            C.B4ReceiptError,
            lambda: C._read_verified_terminal_receipt(
                invocation.terminal_receipt_path
            ),
            contains="decision hash",
        )
        terminal = json.loads(terminal_bytes)
        terminal["decision_reverse_recommended"] = False
        invocation.terminal_receipt_path.write_bytes(
            C._canonical_json_bytes(terminal)
        )
        _raises(
            C.B4ReceiptError,
            lambda: C._read_verified_terminal_receipt(
                invocation.terminal_receipt_path
            ),
            contains="decision reverse bit",
        )
        terminal = json.loads(terminal_bytes)
        terminal.pop("decision_sha256")
        invocation.terminal_receipt_path.write_bytes(
            C._canonical_json_bytes(terminal)
        )
        _raises(
            C.B4ReceiptError,
            lambda: C._read_verified_terminal_receipt(
                invocation.terminal_receipt_path
            ),
            contains="keys do not match exact schema",
        )


def test_public_b4_receipt_gate_accepts_live_certified_bound_receipt():
    signature = inspect.signature(C.require_b4_closed_critic_receipt)
    assert tuple(signature.parameters) == (
        "terminal_receipt_path", "cfg", "layout",
    )
    assert "runner" not in signature.parameters
    assert "executable" not in signature.parameters
    with _certified_pair_fixture() as (pair, cfg, layout, _calls):
        invocation = pair.on.invoke(invocation_id="public-live-positive")
        receipt = C.require_b4_closed_critic_receipt(
            invocation.terminal_receipt_path,
            cfg=cfg,
            layout=layout,
        )
        assert receipt == invocation.receipt
        assert receipt.driver_kind == "base"
        terminal_sha256 = hashlib.sha256(
            invocation.terminal_receipt_path.read_bytes()
        ).hexdigest()
        proposal_path = invocation.terminal_receipt_path.parent / "proposal.json"
        proposal_path.write_text(json.dumps({
            "planner": {
                "axis": L.MARKER_ID,
                "direction": "increase",
                "magnitude": "small",
            },
            "coder": {
                "axis": L.MARKER_ID,
                "value": 20.0,
                "implementation": "double now_backoff = 20.0;",
            },
            L.B4_PROPOSAL_RECEIPT_SHA256_KEY: terminal_sha256,
        }), encoding="utf-8")
        planner, coder, prior = L.load_proposal_file(
            str(proposal_path),
            b4_reflux_ablation=True,
            b4_closed_critic_receipt_sha256=terminal_sha256,
        )
        synthesis_calls = []

        def fake_synthesis(
            _cfg, _perf, planner, _coder, state, *_args, **_kwargs,
        ):
            synthesis_calls.append(state.iteration)
            L.project_whiteboard(state, planner, "fail")
            return {"outcome": "dry-pass", "variant": None}

        with unittest.mock.patch.object(
            L, "exploration_campaign_layout", return_value=layout,
        ), unittest.mock.patch.object(
            L.ident, "ensure_resumable_attempts", return_value=None,
        ), unittest.mock.patch.object(
            L, "_run_one_iteration_resolved", side_effect=fake_synthesis,
        ):
            outcome = L.drive_iteration(
                cfg,
                L.default_perf(),
                planner,
                coder,
                prior,
                sub="unused-by-positive-control",
                do_build=True,
                layout=layout,
                build_context=build_run_context(
                    generator_id=GeneratorId.BACKOFF_SWEEP
                ),
                b4_closed_critic_receipt=invocation.terminal_receipt_path,
                b4_proposal_receipt_sha256=terminal_sha256,
                _b4_launch_context=_production_launch_context(cfg),
            )
        assert outcome["ran"] is True
        assert synthesis_calls == [2]


def test_public_b4_receipt_gate_rejects_real_test_only_evidence():
    with _pair_fixture() as (pair, layouts, _calls):
        invocation = pair.on.invoke(invocation_id="public-test-only")
        cfg = L.default_cfg(reflux=True)
        layout = layouts[str(ident.campaign_id(cfg))]
        _raises(
            C.B4ReceiptError,
            lambda: C.require_b4_closed_critic_receipt(
                invocation.terminal_receipt_path,
                cfg=cfg,
                layout=layout,
            ),
            contains="must be certified",
        )


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    (
        ("schema_version", "not-v3", "schema_version"),
        ("status", "failure", "status"),
        ("driver_kind", "sort", "driver_kind"),
        ("campaign_id", "different-campaign", "campaign_id"),
        ("arm", "off", "arm differs"),
        ("iteration", 2, "iteration"),
        ("digest_sha256", "0" * 64, "regenerated live digest"),
        ("admitted_view_sha256", "1" * 64, "live WAL bytes"),
        ("loop_state_sha256", "2" * 64, "live checkpoint bytes"),
    ),
    ids=(
        "schema-version",
        "status",
        "different-driver-receipt",
        "campaign-id-m3",
        "arm-m4",
        "iteration-m5",
        "digest-m6",
        "wal-m7",
        "loop-state-m8",
    ),
)
def test_public_b4_receipt_gate_rejects_one_live_binding_mismatch(
    field_name, value, message,
):
    with _certified_pair_fixture() as (pair, cfg, layout, _calls):
        invocation = pair.on.invoke(
            invocation_id=f"public-live-negative-{field_name}"
        )
        verified = C._read_verified_terminal_receipt(
            invocation.terminal_receipt_path
        )
        assert verified.evidence_class == "certified"
        mismatched = replace(verified, **{field_name: value})
        with unittest.mock.patch.object(
            C,
            "_read_verified_terminal_receipt",
            return_value=mismatched,
        ):
            _raises(
                C.B4ReceiptError,
                lambda: C.require_b4_closed_critic_receipt(
                    invocation.terminal_receipt_path,
                    cfg=cfg,
                    layout=layout,
                ),
                contains=message,
            )


def test_public_b4_receipt_gate_rejects_nonexact_layout_type_m15():
    with _certified_pair_fixture() as (pair, cfg, layout, _calls):
        invocation = pair.on.invoke(invocation_id="public-layout-negative")
        assert C._read_verified_terminal_receipt(
            invocation.terminal_receipt_path
        ).evidence_class == "certified"
        wrong = SimpleNamespace(
            root=layout.root,
            wal_file=layout.wal_file,
        )
        _raises(
            C.B4ReceiptError,
            lambda: C.require_b4_closed_critic_receipt(
                invocation.terminal_receipt_path,
                cfg=cfg,
                layout=wrong,
            ),
            contains="exact CampaignLayout",
        )


def test_public_b4_receipt_gate_rejects_exact_nonauthoritative_layout():
    with _certified_pair_fixture() as (pair, cfg, _layout, _calls):
        invocation = pair.on.invoke(invocation_id="public-wrong-root-negative")
        wrong = CampaignLayout(
            root=tempfile.mkdtemp(prefix="izanagi-b4-wrong-layout-")
        )
        _raises(
            C.B4ReceiptError,
            lambda: C.require_b4_closed_critic_receipt(
                invocation.terminal_receipt_path,
                cfg=cfg,
                layout=wrong,
            ),
            contains="not the authoritative",
        )


def test_public_b4_receipt_gate_requires_exact_protocol_marker():
    with _certified_pair_fixture() as (pair, _cfg, layout, _calls):
        invocation = pair.on.invoke(invocation_id="public-marker-negative")
        unmarked = L.default_cfg(reflux=True)
        _raises(
            C.B4ReceiptError,
            lambda: C.require_b4_closed_critic_receipt(
                invocation.terminal_receipt_path,
                cfg=unmarked,
                layout=layout,
            ),
            contains="exact B-4 protocol marker",
        )


# Recorded T-816 policy epoch; current T-2304 IDs remain independent literals.
_T816_MARKED_CAMPAIGN_IDS = {
    "base": (
        "p3-s4-loop-s4-autonomous-47062c3f",
        "p3-s4-loop-s4-autonomous-6e844e5b",
    ),
    "sort": (
        "p3-s5-sort-loop-s5-sort-autonomous-48e2968e",
        "p3-s5-sort-loop-s5-sort-autonomous-c0614e6c",
    ),
    "trigger": (
        "p3-s8a-trigger-loop-s8a-trigger-autonomous-2adb6cf7",
        "p3-s8a-trigger-loop-s8a-trigger-autonomous-6328b84a",
    ),
}


@pytest.mark.parametrize(
    ("driver", "expected_ids"),
    (
        (
            "base",
            (
                "p3-s4-loop-s4-autonomous-36636f6e",
                "p3-s4-loop-s4-autonomous-97e99268",
            ),
        ),
        (
            "sort",
            (
                "p3-s5-sort-loop-s5-sort-autonomous-5e23ed3e",
                "p3-s5-sort-loop-s5-sort-autonomous-365dfaba",
            ),
        ),
        (
            "trigger",
            (
                "p3-s8a-trigger-loop-s8a-trigger-autonomous-44860c77",
                "p3-s8a-trigger-loop-s8a-trigger-autonomous-6c36625a",
            ),
        ),
    ),
)
def test_closed_critic_cli_has_fixed_marked_configs_for_all_drivers(
    driver, expected_ids,
):
    context = B4L.create_b4_launch_context_for_test(driver_kind=driver)
    with contextlib.ExitStack() as stack:
        if driver == "trigger":
            stack.enter_context(unittest.mock.patch.object(
                TRIGGER_LOOP,
                "_current_site",
                return_value=site_policy.OTHER,
            ))
        factory = C.B4_DRIVER_CONFIG_FACTORIES[driver]
        configs = tuple(
            factory(
                reflux=reflux,
                b4_reflux_ablation=True,
                _b4_launch_context=context,
            )
            for reflux in (True, False)
        )

    assert tuple(C.B4_DRIVER_CONFIG_FACTORIES) == ("base", "sort", "trigger")
    assert tuple(str(ident.campaign_id(cfg)) for cfg in configs) == expected_ids
    assert all(
        current != historical
        for current, historical in zip(expected_ids, _T816_MARKED_CAMPAIGN_IDS[driver])
    )
    assert tuple(cfg.search_config["reflux"] for cfg in configs) == ("on", "off")
    assert all(
        cfg.search_config[L.B4_PROTOCOL_KEY] == L.B4_PROTOCOL_VALUE
        for cfg in configs
    )
    assert all(C._driver_kind_from_cfg(cfg) == driver for cfg in configs)

    if driver == "trigger":
        contract = TRIGGER_LOOP._admit_env_contract(site_policy.OTHER)
        expected = tuple(
            TRIGGER_LOOP._campaign_cfg_for_site(
                TRIGGER_LOOP.default_cfg(
                    reflux=reflux,
                    b4_reflux_ablation=True,
                    _b4_launch_context=context,
                ),
                site_policy.OTHER,
                _contract=contract,
            )
            for reflux in (True, False)
        )
        assert configs == expected


def test_closed_critic_cli_constructs_only_fixed_marked_base_configs():
    """The retired CLI cannot parse around G7 or invoke an injected factory."""
    factory = unittest.mock.Mock()
    for argv in ([], ["--driver", "base"], ["--artifact-root", "/tmp/x"]):
        _raises(
            B4L.B4LauncherAuthorizationError,
            lambda argv=argv: C.main(argv, pair_factory=factory),
            contains="p3_b4_launcher",
        )
    assert factory.call_count == 0


if __name__ == "__main__":
    import traceback

    functions = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_")
    ]
    failures = 0
    for function in functions:
        try:
            function()
            print(f"[PASS] {function.__name__}")
        except Exception:
            failures += 1
            print(f"[FAIL] {function.__name__}")
            traceback.print_exc()
    print(f"\n{len(functions) - failures}/{len(functions)} passed")
    raise SystemExit(1 if failures else 0)
