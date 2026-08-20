# -*- coding: utf-8 -*-
"""P2-2: silo 全探索 (最初の実探索) — 実 fitness 計測 (直列, site-aware contract)。

silo の有効 8 genome (genome.SILO_SPACE, no-wait XOR) を site の確定 calibration
(records=1m / 48thread / skew0.9) で実機計測し、代表 workload
ごとに最速構成を分布比較で特定する (compare は p2_2_report.py が WAL から行う)。

**計測する** ので絶対規律4: 単一テナント直列。bench は pipeline が bench_lock + settle
で排他・静定する。workload ごとに独立 campaign (search_config に workload を刻む) →
WAL も別 → リカバリ独立 (途中で落ちても再実行で続きから)。

代表 workload は contention 域 (skew=0.9) を固定し read/write 比を振る:
  - read-heavy   : ycsb_rratio=95
  - balanced     : ycsb_rratio=50  (= 確定 calibration の点 = high-contention)
  - write-heavy  : ycsb_rratio=5
records は working set (tuple 数) 駆動なので rratio 不変 → 1m を全 workload で共有
(calibration §下限基準, D15)。rmw=0 は calibration と同じ (read set と write set を分離)。

  python orchestrator/campaign/p2_2.py            # 全 workload
  python orchestrator/campaign/p2_2.py read-heavy # 1 workload だけ
"""
from __future__ import annotations

import json
import hashlib
import sys
from dataclasses import dataclass, replace
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from ..calibrator import effective_clock_policy, schema_v2  # noqa: E402
from .genome import SILO_SPACE                          # noqa: E402
from . import buildcache, env_attestation, env_contract, ident, site_policy  # noqa: E402
from .build_admission import GeneratorId, build_run_context  # noqa: E402
from .layout import repo_output_root                    # noqa: E402
from .loop import run_campaign                          # noqa: E402
from .model import CampaignConfig                       # noqa: E402
from .pipeline import PerfConfig                        # noqa: E402


# 歴史的 pin を意図的に保持 (IDENT-1/IDENT-3、pin.py docstring 参照)。
# 再走には submodule を dff0f1e へ checkout する。
CCBENCH_COMMIT = "dff0f1e"
ENV_TAG = "linux-baremetal"
CLK = 1800
NUMA = ["numactl", "--interleave=all"]

_CAMPAIGN_ENV_KEY = "measurement_env"

# 確定 calibration (worklog 2026-06-18, output/env/linux-baremetal/calibration)。
RECORDS = 1_000_000
THREADS = 48
EXTIME = 3
REPS = 5

# A2: noise floor は用途で 2 種 (roadmap §3.6(3'))。混同すると偽 faster を出す。
#   within-run = その 1 測定の品質 (= remeasure 品質ゲート)。calibration noise_floor.cv = 2.28%。
#   between-run = **差が信用できるかの下限** (= compare の丸め閾値)。variant/baseline は別 run で
#     測るので採否 floor はこちら。
# between_run_floor.py で B0-L-W0 baseline を確定動作点で 8 独立セッション実測した結果、fresh な
# same-window between は write: 0.67% (within 2.19% より低) / balanced: 1.07% (within 1.07% と同値)
# = back-to-back では下がりこそすれ within を上回らない楽観的下限と判明 (median 集約 + 熱/周波数/
# cache 共有で真の run 間ドリフトを捉えない)。よって floor は fresh 値でなく **時間分離された
# cross-campaign の genuine データ** に錨を打つ:
#   no-backoff CV(n=2, sweep vs repro) = 2.09% (write) / 1.53% (balanced)、high-abort within ≤2.91%。
# 観測された最悪の run 間分散 (~2.91%) をカバーする保守値 = 0.030。
WITHIN_RUN_CV = 0.0228       # 旧 NOISE_CV_SKEW09。compare には使わない (within の参考/表示用)
BETWEEN_RUN_CV = 0.030       # 採否 floor。cross-campaign genuine + high-abort within の保守側 (~3%)

# 代表 workload。skew=0.9 固定で rratio を振る (rmw=0 は calibration と同じ)。
WORKLOADS = [
    ("read-heavy", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0"}),
    ("balanced", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"}),
    ("write-heavy", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "5", "ycsb_rmw": "0"}),
]


@dataclass(frozen=True)
class _LoadedCalibration:
    """一度だけ読んだ calibration bytes と、その bytes からの検証結果。"""

    raw: bytes
    verified: env_attestation.VerifiedCalibration
    parsed: object


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"JSON constant は calibration では許可しない: {value!r}")


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"calibration JSON の重複 key: {key!r}")
        result[key] = value
    return result


def _validate_legacy_calibration_shape(calibration: object) -> dict:
    """grandfathered v1 の比較に必要な schema 面を fail-closed 検査する。"""
    if type(calibration) is not dict:
        raise ValueError("legacy calibration の top-level は object でなければならない")
    env_tag = calibration.get("env_tag")
    threads = calibration.get("threads")
    clocks_per_us = calibration.get("clocks_per_us")
    saturation = calibration.get("saturation")
    if type(env_tag) is not str or not env_tag:
        raise ValueError("legacy calibration.env_tag が不正")
    if type(threads) is not int or isinstance(threads, bool) or threads <= 0:
        raise ValueError("legacy calibration.threads が正整数でない")
    if (type(clocks_per_us) is not int or isinstance(clocks_per_us, bool)
            or clocks_per_us <= 0):
        raise ValueError("legacy calibration.clocks_per_us が正整数でない")
    if type(saturation) is not dict:
        raise ValueError("legacy calibration.saturation が object でない")
    records = saturation.get("records")
    if type(records) is not int or isinstance(records, bool) or records <= 0:
        raise ValueError("legacy calibration.saturation.records が正整数でない")
    return calibration


def _load_calibration_once(
        contract: env_contract.ExecutionEnvironmentContract,
) -> _LoadedCalibration:
    """contract の calibration を一度だけ読み、hash 検証後の bytes を再利用する。

    none 経路で contract ref を再 open する実装は TOCTOU を作るため許さない。
    required/none ともに、ここで得た ``raw`` だけを parser に渡す。
    """
    if type(contract) is not env_contract.ExecutionEnvironmentContract:
        raise RuntimeError("calibration admission に exact execution contract が必要")
    try:
        repo_root = Path(repo_output_root()).resolve(strict=True).parent
        relative = Path(contract.calibration_ref.path)
        if relative.is_absolute():
            raise ValueError("calibration_ref.path は repository-relative でなければならない")
        artifact = (repo_root / relative).resolve(strict=True)
        artifact.relative_to(repo_root)
        raw = artifact.read_bytes()
    except (OSError, ValueError) as exc:
        raise RuntimeError(
            "calibration artifact を hash 検証前に安全に読み込めない: "
            f"{contract.calibration_ref.path}: {exc}"
        ) from exc

    observed_sha256 = hashlib.sha256(raw).hexdigest()
    if observed_sha256 != contract.calibration_ref.sha256:
        raise RuntimeError(
            "calibration sha256 不一致: "
            f"expected={contract.calibration_ref.sha256} observed={observed_sha256}"
        )

    if contract.attestation_mode == "required":
        try:
            parsed = schema_v2.validate_calibration_v2(raw)
        except schema_v2.CalibrationSchemaError as exc:
            raise RuntimeError(f"calibration/v2 schema が不正: {exc}") from exc
        if parsed.env_tag != contract.env_tag:
            raise RuntimeError(
                f"calibration env_tag 不一致: {parsed.env_tag!r} != {contract.env_tag!r}"
            )
        if parsed.clocks_per_us != contract.clocks_per_us:
            raise RuntimeError(
                "calibration clocks_per_us 不一致: "
                f"{parsed.clocks_per_us} != {contract.clocks_per_us}"
            )
        tolerance = parsed.attestation_profile.effective_clock.tolerance_pct
        if tolerance != effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT:
            raise RuntimeError(
                "calibration effective clock tolerance が current policy と不一致: "
                f"{tolerance!r} != "
                f"{effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT!r}"
            )
        verified = env_attestation.VerifiedCalibration(
            schema_version=schema_v2.SCHEMA_VERSION,
            sha256=observed_sha256,
            calibration=parsed,
            attestation_profile_sha256=env_attestation.profile_sha256(
                parsed.attestation_profile,
            ),
        )
        return _LoadedCalibration(raw=raw, verified=verified, parsed=parsed)

    if contract.attestation_mode == "none":
        if observed_sha256 != env_attestation.GRANDFATHERED_V1_SHA256:
            raise RuntimeError(
                "mode=none は grandfathered v1 calibration bytes だけを受理する"
            )
        try:
            parsed = json.loads(
                raw,
                object_pairs_hook=_unique_json_object,
                parse_constant=_reject_json_constant,
            )
            parsed = _validate_legacy_calibration_shape(parsed)
        except (TypeError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"legacy calibration schema が不正: {exc}") from exc
        verified = env_attestation.VerifiedCalibration(
            schema_version=env_attestation.LEGACY_SCHEMA_VERSION,
            sha256=observed_sha256,
            calibration=None,
            attestation_profile_sha256=None,
        )
        return _LoadedCalibration(raw=raw, verified=verified, parsed=parsed)

    raise RuntimeError(
        f"未対応 attestation_mode: {contract.attestation_mode!r}"
    )


def _admit_env_contract(
        site: str,
) -> env_contract.ExecutionEnvironmentContract:
    """実測 admission 用の site→contract 写像。未知 site は Linux fallback しない。"""
    if site == site_policy.PEGASUS_COMPUTE:
        required = env_contract.lookup_required_attestation_contract()
        return env_contract.lookup(required.env_tag)
    if site == site_policy.OTHER:
        return env_contract.lookup(ENV_TAG)
    raise RuntimeError(
        "実測 admission を拒否します: "
        f"site={site!r} は PEGASUS_COMPUTE/OTHER の許可集合にない"
    )


def _legacy_linux_contract() -> env_contract.ExecutionEnvironmentContract:
    """非実測の歴史的 config builder 用 Linux contract。site admission は行わない。"""
    return env_contract.lookup(ENV_TAG)


def resolve_site_runtime() -> tuple[
        str, env_contract.ExecutionEnvironmentContract,
        env_contract.AuthorizedContract,
]:
    """実測 admission 専用に site/contract/authorization を一度だけ解決する。

    identity 構築や dry-run へ一般化する resolver ではない。Pegasus login/suspect
    を Linux 契約へ fallback すると login node 上の重い計測を許すため、fail-closed にする。
    """
    site = site_policy.current_site()
    contract = _admit_env_contract(site)
    authorization = env_contract.authorize(contract.env_tag)
    if (not isinstance(authorization, env_contract.AuthorizedContract)
            or authorization.contract != contract
            or authorization.contract.contract_sha256 != contract.contract_sha256):
        raise RuntimeError(
            "authorization contract が resolved runtime contract と一致しない"
        )
    return site, contract, authorization


def _campaign_cfg_for_site(
        cfg: CampaignConfig, site: str,
        contract: env_contract.ExecutionEnvironmentContract,
) -> CampaignConfig:
    """site-aware contract を identity に束縛し、Pegasus だけ marker を刻む。"""
    if type(contract) is not env_contract.ExecutionEnvironmentContract:
        raise RuntimeError("campaign config に exact execution contract が必要")
    if site == site_policy.PEGASUS_COMPUTE:
        if contract.attestation_mode != "required":
            raise RuntimeError("Pegasus compute に required contract が束縛されていない")
        existing = cfg.search_config.get(_CAMPAIGN_ENV_KEY)
        if existing is not None and existing != contract.env_tag:
            raise ValueError(
                "Pegasus campaign の measurement_env を異なる値で上書きできない"
            )
        if existing != contract.env_tag:
            cfg = replace(
                cfg,
                search_config={
                    **cfg.search_config,
                    _CAMPAIGN_ENV_KEY: contract.env_tag,
                },
            )
    elif site == site_policy.OTHER:
        if contract.env_tag != ENV_TAG or contract.attestation_mode != "none":
            raise RuntimeError("OTHER site に Linux legacy contract が束縛されていない")
        if _CAMPAIGN_ENV_KEY in cfg.search_config:
            raise ValueError(
                "OTHER site の campaign に measurement_env marker は許可しない"
            )
    else:
        raise RuntimeError(f"未知または実測不可の site: {site!r}")
    return ident.bind_environment_contract(cfg, contract)


def _competing_bench_pids() -> list:
    """競合ベンチ検知 (canonical は calibrator.runner)。driver の pre-flight 用に再公開。

    pipeline も同じ runner.competing_bench_pids を bench 直前に呼ぶ (admission fails-closed)。
    driver は campaign 冒頭、pipeline は genome ごと = 二段の単一テナント保証 (絶対規律4)。"""
    from ..calibrator.runner import competing_bench_pids
    return competing_bench_pids()


def _assert_single_tenant() -> None:
    """競合ベンチが走っていたら計測を拒否する (規律4: 汚染した数値は無価値)。

    孤児/他者のプロセスを勝手に kill しない (規律6: 素性不明な実行物は人間が判断)。
    検出したら PID を表に出して停止する。"""
    comp = _competing_bench_pids()
    if comp:
        msg = ("競合する ccbench ベンチが稼働中 → 計測は規律4 違反になるので拒否する。\n"
               "  該当プロセス (孤児なら kill、他者の作業なら待つ — 自動で殺さない):\n"
               + "\n".join(f"    {ln}" for ln in comp))
        raise RuntimeError(msg)


def _assert_matches_calibration(
        contract: env_contract.ExecutionEnvironmentContract | None = None,
) -> None:
    """手書き動作点と contract の hash-bound calibration を実行時照合する。

    contract を省略した旧 caller は実測 resolver を通る。通常の実測経路は既に解決済み
    contract を渡し、resolver/authorization/calibration の世代を一つに束縛する。
    不在・schema・hash・records/threads/env/clocks の不一致は全て RuntimeError とする。
    """
    if contract is None:
        _, contract, _ = resolve_site_runtime()
    loaded = _load_calibration_once(contract)
    if isinstance(loaded.parsed, schema_v2.CalibrationV2):
        saturation = loaded.parsed.saturation
        cal_records = (saturation or {}).get("records") if saturation is not None else None
        cal_threads = loaded.parsed.threads
        cal_env_tag = loaded.parsed.env_tag
        cal_clocks = loaded.parsed.clocks_per_us
    else:
        calibration = loaded.parsed
        cal_records = (calibration.get("saturation") or {}).get("records")
        cal_threads = calibration.get("threads")
        cal_env_tag = calibration.get("env_tag")
        cal_clocks = calibration.get("clocks_per_us")
    expected = (RECORDS, THREADS, contract.env_tag, contract.clocks_per_us)
    actual = (cal_records, cal_threads, cal_env_tag, cal_clocks)
    if actual != expected:
        raise RuntimeError(
            "手書き動作点が contract の calibration と不一致: "
            f"expected={expected!r}, calibration={actual!r}"
        )


def config_for(tag: str, workload: dict) -> CampaignConfig:
    """workload タグ → CampaignConfig。レポート生成器が同じ campaign-id を再計算して
    WAL を引けるよう、campaign 同一性を決める入力をここに集約する (D13)。"""
    return CampaignConfig(
        spec_slug=f"p2-2-silo-{tag}", search_tag="enumerate",
        spec_content=f"P2-2: silo 全探索 (実 fitness) — workload={tag}",
        ccbench_commit=CCBENCH_COMMIT,
        search_config={"scale": "silo", "space": "xor-8", "workload": tag,
                       "records": RECORDS, "threads": THREADS,
                       "ycsb": workload},
        trial="p2-2")


def run_workload(tag: str, workload: dict, log=print):
    _assert_single_tenant()
    site, contract, authorization = resolve_site_runtime()
    _assert_matches_calibration(contract)
    genomes = SILO_SPACE.enumerate()
    cfg = _campaign_cfg_for_site(config_for(tag, workload), site, contract)
    perf = PerfConfig(records=RECORDS, threads=THREADS, workload=workload,
                      extime=EXTIME, reps=REPS)
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    resolved_cc, resolved_cxx = buildcache.compilers_for_current_site()
    expected_toolchain_manifest = buildcache.observed_toolchain_manifest(
        resolved_cc, resolved_cxx,
    )

    log(f"\n=== P2-2 workload={tag}  ({workload})  {len(genomes)} genome ===")
    s = run_campaign(cfg, genomes, perf, contract.env_tag,
                     contract.clocks_per_us, numactl=list(contract.numactl), log=log,
                     authorization_contract=authorization,
                     env_contract=contract,
                     expected_toolchain_manifest=expected_toolchain_manifest,
                     build_context=build_context,
                     declared_use_class="official")

    rows = [(r.fitness_tps, r) for r in s.results if r.fitness_tps is not None]
    rows.sort(key=lambda t: t[0], reverse=True)
    log(f"\n  --- {tag}: fitness ランキング (committed={s.committed} "
        f"aborted={s.aborted} skipped={s.skipped}) ---")
    for tps, r in rows:
        log(f"    {tps:>12,.0f} tps  CV {r.cv * 100:4.2f}%"
            f"{'  ⚠UNSTABLE' if r.unstable else ''}  {r.genome.canonical()}")
    for r in (r for r in s.results if r.aborted):
        log(f"    ✗ ABORT {r.genome.canonical()}: {r.verdict} / {r.notes}")
    return s


def main(argv) -> int:
    sel = argv[1] if len(argv) > 1 else None
    wls = [w for w in WORKLOADS if sel is None or w[0] == sel]
    if not wls:
        print(f"unknown workload: {sel} (選択肢: {[w[0] for w in WORKLOADS]})")
        return 2
    summaries = []
    for tag, workload in wls:
        summaries.append((tag, run_workload(tag, workload)))
    print("\n=== P2-2 完了 ===")
    for tag, s in summaries:
        print(f"  {tag}: {s.campaign_id}  committed={s.committed} "
              f"aborted={s.aborted}")
    ok = all(s.aborted == 0 for _, s in summaries)
    print(f"P2-2: {'全 genome 計測成功' if ok else 'abort あり (要確認)'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
