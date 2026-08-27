# -*- coding: utf-8 -*-
"""Exclusive launcher and process-local capability for formal P3 B-4 runs.

The capability deliberately stays outside ``CampaignConfig`` and
``search_config``.  A marked campaign is therefore distinguished by the same
identity bytes as before, while formal execution additionally requires this
live, sealed value and the launch sidecar written in its authoritative root.
"""
from __future__ import annotations

import argparse
import contextlib
import contextvars
from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Iterator, Literal

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import ident
from .layout import CampaignLayout, exploration_campaign_layout
from .p3_b4_admission_record import verify_b4_admission_record
from . import p3_s4_loop
from . import p3_s4_loop_sort
from . import p3_s4_loop_trigger_gating
from . import p3_b4_closed_critic


DriverKind = Literal["base", "sort", "trigger"]
Arm = Literal["on", "off"]

B4_LAUNCH_SIDECAR = "b4_launch_context.json"
B4_LAUNCH_SIDECAR_SCHEMA = "p3-b4-launch-context/v1"

_TRUST_NON_GUARANTEES = (
    "same-process closure introspection and module attribute replacement "
    "are not resisted",
)

_B4_TEST_CONTEXT_SEAL = object()


class B4LauncherAuthorizationError(RuntimeError):
    """A formal B-4 boundary did not receive the launcher capability."""


@dataclass(frozen=True)
class B4LaunchContext:
    """Sealed, admission-bound capability retained only in this process."""

    _seal: object
    evidence_class: Literal["production", "test-only"]
    driver_kind: DriverKind
    arm: Arm
    admission_record_sha256: str
    admission_record_commit: str
    campaign_id: str | None
    context_sha256: str


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _context_value(
    *,
    evidence_class: str,
    driver_kind: str,
    arm: str,
    admission_record_sha256: str,
    admission_record_commit: str,
    campaign_id: str | None,
) -> dict[str, Any]:
    return {
        "evidence_class": evidence_class,
        "driver_kind": driver_kind,
        "arm": arm,
        "admission_record_sha256": admission_record_sha256,
        "admission_record_commit": admission_record_commit,
        "campaign_id": campaign_id,
    }


def _context_sha256(**kwargs: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(_context_value(**kwargs))).hexdigest()


def _validate_context_shape(context: object) -> B4LaunchContext:
    if type(context) is not B4LaunchContext:
        raise B4LauncherAuthorizationError("B-4 launch context is not sealed")
    if context.driver_kind not in DRIVER_REGISTRY:
        raise B4LauncherAuthorizationError("B-4 launch context driver kind is invalid")
    if context.arm not in {"on", "off"}:
        raise B4LauncherAuthorizationError("B-4 launch context arm is invalid")
    if (
        type(context.admission_record_sha256) is not str
        or len(context.admission_record_sha256) != 64
        or any(c not in "0123456789abcdef" for c in context.admission_record_sha256)
    ):
        raise B4LauncherAuthorizationError(
            "B-4 launch context admission hash is invalid"
        )
    if (
        type(context.admission_record_commit) is not str
        or len(context.admission_record_commit) != 40
        or any(c not in "0123456789abcdef" for c in context.admission_record_commit)
    ):
        raise B4LauncherAuthorizationError(
            "B-4 launch context admission commit is invalid"
        )
    if context.campaign_id is not None and (
        type(context.campaign_id) is not str or not context.campaign_id
    ):
        raise B4LauncherAuthorizationError("B-4 launch context campaign id is invalid")
    expected = _context_sha256(
        evidence_class=context.evidence_class,
        driver_kind=context.driver_kind,
        arm=context.arm,
        admission_record_sha256=context.admission_record_sha256,
        admission_record_commit=context.admission_record_commit,
        campaign_id=context.campaign_id,
    )
    if context.context_sha256 != expected:
        raise B4LauncherAuthorizationError("B-4 launch context digest differs")
    return context


DRIVER_REGISTRY = {
    "base": p3_s4_loop.main,
    "sort": p3_s4_loop_sort.main,
    "trigger": p3_s4_loop_trigger_gating.main,
}


def _driver_configs(
    driver_kind: DriverKind,
    context: B4LaunchContext,
) -> tuple[Any, Any]:
    if driver_kind == "base":
        factory = p3_s4_loop.default_cfg
    elif driver_kind == "sort":
        factory = p3_s4_loop_sort.default_cfg
    else:
        factory = p3_s4_loop_trigger_gating.default_cfg
    configs = tuple(
        factory(
            reflux=reflux,
            b4_reflux_ablation=True,
            _b4_launch_context=context,
        )
        for reflux in (True, False)
    )
    if driver_kind == "trigger":
        site = p3_s4_loop_trigger_gating._current_site()
        contract = p3_s4_loop_trigger_gating._admit_env_contract(site)
        configs = tuple(
            p3_s4_loop_trigger_gating._campaign_cfg_for_site(
                cfg, site, _contract=contract,
            )
            for cfg in configs
        )
    return configs


def _driver_argv(
    *,
    arm: Arm,
    proposal_path: Path,
    terminal_receipt_path: Path | None,
) -> list[str]:
    argv = [
        "--reflux",
        arm,
        "--b4-reflux-ablation",
        "--run-iteration",
        str(proposal_path),
        "--allow-coder-derived-build",
    ]
    if terminal_receipt_path is not None:
        argv.extend(["--b4-closed-critic-receipt", str(terminal_receipt_path)])
    return argv


def _build_launcher_closure():
    """Keep production issuance off the module's direct attribute surface."""
    production_seal = object()
    active_context: contextvars.ContextVar[B4LaunchContext | None] = (
        contextvars.ContextVar("active_b4_launch_context", default=None)
    )

    def new_context(
        *,
        seal: object,
        evidence_class: Literal["production", "test-only"],
        driver_kind: DriverKind,
        arm: Arm,
        admission_record_sha256: str,
        admission_record_commit: str,
        campaign_id: str | None = None,
    ) -> B4LaunchContext:
        values = {
            "evidence_class": evidence_class,
            "driver_kind": driver_kind,
            "arm": arm,
            "admission_record_sha256": admission_record_sha256,
            "admission_record_commit": admission_record_commit,
            "campaign_id": campaign_id,
        }
        return B4LaunchContext(
            _seal=seal,
            **values,
            context_sha256=_context_sha256(**values),
        )

    def create_test_context(
        *,
        driver_kind: DriverKind,
        arm: Arm = "on",
    ) -> B4LaunchContext:
        """Create an unmistakably test-only context for config fixtures."""
        return new_context(
            seal=_B4_TEST_CONTEXT_SEAL,
            evidence_class="test-only",
            driver_kind=driver_kind,
            arm=arm,
            admission_record_sha256="0" * 64,
            admission_record_commit="0" * 40,
        )

    def require_production_seal(
        context: object, *, boundary: str,
    ) -> B4LaunchContext:
        if type(context) is not B4LaunchContext:
            raise B4LauncherAuthorizationError(
                f"B-4 {boundary} requires a production launch context"
            )
        context = _validate_context_shape(context)
        if (
            context._seal is not production_seal
            and context._seal is not _B4_TEST_CONTEXT_SEAL
        ):
            raise B4LauncherAuthorizationError(
                f"B-4 {boundary} requires a production launch context"
            )
        if context._seal is _B4_TEST_CONTEXT_SEAL:
            raise B4LauncherAuthorizationError(
                f"test-only B-4 launch context cannot authorize {boundary}"
            )
        if context.evidence_class != "production":
            raise B4LauncherAuthorizationError(
                f"B-4 {boundary} requires a production launch context"
            )
        return context

    def require_any_context(
        context: object,
        *,
        expected_driver_kind: DriverKind,
        boundary: str,
    ) -> B4LaunchContext:
        """Accept either exact seal for config construction only."""
        if type(context) is not B4LaunchContext:
            raise B4LauncherAuthorizationError(
                f"B-4 {boundary} requires a sealed launch context"
            )
        context = _validate_context_shape(context)
        valid_seal = (
            context._seal is production_seal
            and context.evidence_class == "production"
        ) or (
            context._seal is _B4_TEST_CONTEXT_SEAL
            and context.evidence_class == "test-only"
        )
        if not valid_seal:
            raise B4LauncherAuthorizationError(
                f"B-4 {boundary} requires a sealed launch context"
            )
        if context.driver_kind != expected_driver_kind:
            raise B4LauncherAuthorizationError(
                f"B-4 launch context driver kind differs at {boundary}"
            )
        return context

    def require_production_context(
        context: object,
        *,
        expected_driver_kind: DriverKind,
        expected_campaign_id: str,
        expected_arm: Arm,
        boundary: str,
    ) -> B4LaunchContext:
        """Require exact production kind, campaign, arm, seal, and digest."""
        context = require_production_seal(context, boundary=boundary)
        if context.driver_kind != expected_driver_kind:
            raise B4LauncherAuthorizationError(
                f"B-4 launch context driver kind differs at {boundary}"
            )
        if type(expected_campaign_id) is not str or not expected_campaign_id:
            raise B4LauncherAuthorizationError(
                f"B-4 {boundary} expected campaign id is invalid"
            )
        if context.campaign_id != expected_campaign_id:
            raise B4LauncherAuthorizationError(
                f"B-4 launch context campaign id differs at {boundary}"
            )
        if expected_arm not in {"on", "off"}:
            raise B4LauncherAuthorizationError(
                f"B-4 {boundary} expected arm is invalid"
            )
        if context.arm != expected_arm:
            raise B4LauncherAuthorizationError(
                f"B-4 launch context arm differs at {boundary}"
            )
        return context

    def issue_context(
        admission_record_path: Path,
        *,
        driver_kind: DriverKind,
        arm: Arm,
    ) -> B4LaunchContext:
        verified = verify_b4_admission_record(
            admission_record_path,
            repository_root=p3_b4_closed_critic.REPOSITORY_ROOT,
        )
        return new_context(
            seal=production_seal,
            evidence_class="production",
            driver_kind=driver_kind,
            arm=arm,
            admission_record_sha256=verified.admission_record_sha256,
            admission_record_commit=verified.admission_record_commit,
        )

    def bind_campaign(
        context: B4LaunchContext,
        campaign_id: str,
    ) -> B4LaunchContext:
        context = require_production_seal(context, boundary="campaign binding")
        if type(campaign_id) is not str or not campaign_id:
            raise B4LauncherAuthorizationError("B-4 campaign binding is invalid")
        values = _context_value(
            evidence_class=context.evidence_class,
            driver_kind=context.driver_kind,
            arm=context.arm,
            admission_record_sha256=context.admission_record_sha256,
            admission_record_commit=context.admission_record_commit,
            campaign_id=campaign_id,
        )
        return replace(
            context,
            campaign_id=campaign_id,
            context_sha256=_context_sha256(**values),
        )

    def sidecar_value(context: B4LaunchContext) -> dict[str, str]:
        context = require_production_seal(context, boundary="launch sidecar")
        if context.campaign_id is None:
            raise B4LauncherAuthorizationError(
                "B-4 launch sidecar requires a campaign-bound launch context"
            )
        return {
            "schema_version": B4_LAUNCH_SIDECAR_SCHEMA,
            "campaign_id": context.campaign_id,
            "arm": context.arm,
            "driver_kind": context.driver_kind,
            "admission_record_sha256": context.admission_record_sha256,
            "launch_context_sha256": context.context_sha256,
        }

    def write_sidecar(
        layout: CampaignLayout,
        context: B4LaunchContext,
    ) -> Path:
        """Atomically replace the launch record so a campaign can be remeasured."""
        expected = sidecar_value(context)
        if Path(layout.root).name != expected["campaign_id"]:
            raise B4LauncherAuthorizationError(
                "B-4 launch sidecar layout differs from campaign binding"
            )
        layout.ensure()
        target = Path(layout.root) / B4_LAUNCH_SIDECAR
        temporary = target.with_name(
            f".{target.name}.tmp-{os.getpid()}-{os.urandom(16).hex()}"
        )
        try:
            with temporary.open("xb") as stream:
                stream.write(_canonical_json_bytes(expected))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
            directory_fd = os.open(layout.root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            temporary.unlink(missing_ok=True)
        return target

    @contextlib.contextmanager
    def activate_context(
        context: B4LaunchContext,
    ) -> Iterator[B4LaunchContext]:
        context = require_production_seal(context, boundary="process activation")
        if context.campaign_id is None:
            raise B4LauncherAuthorizationError(
                "B-4 process activation requires a campaign-bound launch context"
            )
        token = active_context.set(context)
        try:
            yield context
        finally:
            active_context.reset(token)

    def verify_launch_context(
        layout: CampaignLayout,
        *,
        expected_driver_kind: DriverKind,
        expected_campaign_id: str,
        expected_arm: Arm,
    ) -> B4LaunchContext:
        """G4: bind a marked COMMIT to lock-derived exact expectations."""
        sidecar_path = Path(layout.root) / B4_LAUNCH_SIDECAR
        try:
            raw = sidecar_path.read_bytes()
        except OSError as exc:
            raise B4LauncherAuthorizationError(
                "B-4 COMMIT requires b4_launch_context.json"
            ) from exc
        try:
            value = json.loads(raw)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise B4LauncherAuthorizationError(
                "B-4 launch sidecar is invalid"
            ) from exc
        if type(value) is not dict or set(value) != {
            "schema_version",
            "campaign_id",
            "arm",
            "driver_kind",
            "admission_record_sha256",
            "launch_context_sha256",
        }:
            raise B4LauncherAuthorizationError("B-4 launch sidecar is invalid")
        if value.get("schema_version") != B4_LAUNCH_SIDECAR_SCHEMA:
            raise B4LauncherAuthorizationError("B-4 launch sidecar is invalid")
        if (
            Path(layout.root).name != expected_campaign_id
            or value.get("campaign_id") != expected_campaign_id
        ):
            raise B4LauncherAuthorizationError(
                "B-4 launch sidecar is bound to another campaign"
            )
        context = active_context.get()
        if type(context) is not B4LaunchContext:
            raise B4LauncherAuthorizationError(
                "B-4 COMMIT requires the live launch context"
            )
        context = require_production_context(
            context,
            expected_driver_kind=expected_driver_kind,
            expected_campaign_id=expected_campaign_id,
            expected_arm=expected_arm,
            boundary="certified sink",
        )
        expected_sidecar = sidecar_value(context)
        if any(
            value[key] != expected_sidecar[key]
            for key in expected_sidecar
            if key != "campaign_id"
        ):
            raise B4LauncherAuthorizationError(
                "B-4 launch sidecar differs from the live launch context"
            )
        return context

    def prepare_launch(
        *,
        driver_kind: DriverKind,
        arm: Arm,
        admission_record_path: Path,
    ) -> tuple[B4LaunchContext, Any, Any]:
        context = issue_context(
            admission_record_path,
            driver_kind=driver_kind,
            arm=arm,
        )
        on_cfg, off_cfg = _driver_configs(driver_kind, context)
        selected_cfg = on_cfg if arm == "on" else off_cfg
        context = bind_campaign(context, str(ident.campaign_id(selected_cfg)))
        return context, on_cfg, off_cfg

    def launch_bootstrap_impl(
        *,
        driver_kind: DriverKind,
        arm: Arm,
        admission_record_path: Path,
        proposal_path: Path,
    ) -> int:
        """Verify admission before touching the real driver, then run bootstrap."""
        context, on_cfg, off_cfg = prepare_launch(
            driver_kind=driver_kind,
            arm=arm,
            admission_record_path=admission_record_path,
        )
        selected_cfg = on_cfg if arm == "on" else off_cfg
        layout = exploration_campaign_layout(str(ident.campaign_id(selected_cfg)))
        write_sidecar(layout, context)
        with activate_context(context):
            return DRIVER_REGISTRY[driver_kind](
                _driver_argv(
                    arm=arm,
                    proposal_path=proposal_path,
                    terminal_receipt_path=None,
                ),
                _b4_launch_context=context,
            )

    def launch_continuation_impl(
        *,
        driver_kind: DriverKind,
        arm: Arm,
        admission_record_path: Path,
        artifact_root: Path,
        proposal_path: Path,
        stdin=sys.stdin,
        stdout=sys.stdout,
    ) -> int:
        """Mint a certified pair, emit its receipt, wait one line, then continue."""
        context, on_cfg, off_cfg = prepare_launch(
            driver_kind=driver_kind,
            arm=arm,
            admission_record_path=admission_record_path,
        )
        with p3_b4_closed_critic.create_b4_closed_critic_pair(
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            artifact_root=artifact_root,
            admission_record_path=admission_record_path,
            expected_driver_kind=driver_kind,
            _b4_launch_context=context,
        ) as pair:
            on = pair.on.invoke(invocation_id="b4-on")
            off = pair.off.invoke(invocation_id="b4-off")
            p3_b4_closed_critic.assert_b4_certified_arm_pair(
                pair,
                on.terminal_receipt_path,
                off.terminal_receipt_path,
                admission_record_path=admission_record_path,
            )
            selected = on if arm == "on" else off
            print(str(selected.terminal_receipt_path), file=stdout, flush=True)
            if stdin.readline() == "":
                raise B4LauncherAuthorizationError(
                    "B-4 continuation requires one ready-signal line"
                )
            selected_cfg = on_cfg if arm == "on" else off_cfg
            layout = exploration_campaign_layout(
                str(ident.campaign_id(selected_cfg))
            )
            write_sidecar(layout, context)
            with activate_context(context):
                return DRIVER_REGISTRY[driver_kind](
                    _driver_argv(
                        arm=arm,
                        proposal_path=proposal_path,
                        terminal_receipt_path=selected.terminal_receipt_path,
                    ),
                    _b4_launch_context=context,
                )

    return (
        create_test_context,
        require_any_context,
        require_production_context,
        verify_launch_context,
        launch_bootstrap_impl,
        launch_continuation_impl,
    )


(
    create_b4_launch_context_for_test,
    require_b4_any_context,
    require_b4_production_context,
    verify_b4_launch_context,
    launch_bootstrap,
    launch_continuation,
) = _build_launcher_closure()
del _build_launcher_closure


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P3 B-4 exclusive launcher")
    parser.add_argument("mode", choices=("bootstrap", "continuation"))
    parser.add_argument("--driver", choices=tuple(DRIVER_REGISTRY), required=True)
    parser.add_argument("--arm", choices=("on", "off"), required=True)
    parser.add_argument("--admission-record", required=True, type=Path)
    parser.add_argument("--proposal", required=True, type=Path)
    parser.add_argument("--artifact-root", type=Path)
    args = parser.parse_args(argv)
    if args.mode == "bootstrap":
        if args.artifact_root is not None:
            parser.error("bootstrap does not accept --artifact-root")
        return launch_bootstrap(
            driver_kind=args.driver,
            arm=args.arm,
            admission_record_path=args.admission_record,
            proposal_path=args.proposal,
        )
    if args.artifact_root is None:
        parser.error("continuation requires --artifact-root")
    return launch_continuation(
        driver_kind=args.driver,
        arm=args.arm,
        admission_record_path=args.admission_record,
        artifact_root=args.artifact_root,
        proposal_path=args.proposal,
    )


if __name__ == "__main__":
    raise SystemExit(main())
