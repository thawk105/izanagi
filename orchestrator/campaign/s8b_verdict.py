# -*- coding: utf-8 -*-
"""8b §6 判定表: prediction × oracle を結合する I/O 非依存な三値判定。

裁定 5 が定めた prediction の選択評価を機械判定する純関数を提供する。

- 条件 1 (on/off 予測差): on の予測 choice が off の予測 choice と異なる holdout が存在する
  (存在量化)。
- 条件 2 (swapped 追従): expected_holdouts の全 holdout で、swapped の予測が
  swap 元の on 予測へ family ID 一致で追従する (全称量化)。
- 結論: 条件 1 と条件 2 の連言。どちらかが判定不能なら結論も判定不能となる。

expected_holdouts は prediction から導出せず、呼び手が渡す凍結 holdout 集合を全称量化の領域とする。
bound floor_source は measurement-condition の claim gate と oracle 条件整合性の検証にだけ使い、
選択条件の値比較には使わない。

この撤去は between-run floor・scale gate・oracle unique-best 確定・両構成 eligibility 判定の
4 保証を判定基盤から外す**意図的な受理拡大**であり、§10.1/D510
(docs/phase3-8b-descriptor-design.md §10, docs/decisions.md D510) が明示承認している。

off=stock 契約は ``verify_prediction``/``_assert_off_stock_and_catalog`` が独立に担保し、
``judge_combined`` はこれを再検証しない (verify_prediction をバイパスする経路への防御は scope 外)。

三値伝播は fail-closed とし、selector の欠測・不正、oracle の構造破綻、expected_holdouts の欠落・
重複、measurement condition の不一致は判定不能へ倒す。``judge_combined`` は検証済み
``VerifiedPrediction`` と ``VerifiedOracleVerdict`` のみを受理し、未検証の生文書を拒否する。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from .s8b_freeze_io import FreezeIOError, load_verified_freeze
from .s8b_oracle_manifest import (
    STOCK_CONFIGURATION,
    ManifestError,
    _validate_execution_snapshot,
)
from .s8b_selector_freeze import (
    ROOT,
    SelectorFreezeError,
    verify_prediction_freeze,
)
from .s8b_selector_input import (
    CHOICE_TO_BINDING,
    STATIC_DEFAULT_CHOICE_ID,
    SelectorInputError,
)
from .s8b_descriptor import DescriptorError


from . import s8b_floor_stats as _floor_stats  # noqa: E402
from . import s8b_oracle_artifacts as _artifacts  # noqa: E402
from . import s8b_oracle_judge, s8b_oracle_manifest, s8b_oracle_spec  # noqa: E402
from . import s8b_ratified_freeze  # noqa: E402
from orchestrator.calibrator import perf_preflight as _perf_preflight  # noqa: E402



# schema v3: 条件3・per-pair floor・scale gate を判定基盤から撤去した出力形。
SCHEMA_VERSION = _artifacts.COMBINED_VERDICT_SCHEMA
PREDICTION_SCHEMA = "8b-selector-prediction-freeze/v1"
ORACLE_SCHEMA = _artifacts.OFFICIAL_VERDICT_SCHEMA

# 三値: 成立 / 不成立 / 判定不能。
HOLDS = "holds"
REFUTED = "refuted"
INDETERMINATE = "indeterminate"

_ARMS = ("on", "off", "swapped")
_MEASUREMENT_CONDITION_KEYS = {
    "campaign_id", "measurement_manifest_sha256", "perf_observation",
}
_DEGRADED_PLACEHOLDER_CMD = ("ccbench",)
_DEGRADED_PLACEHOLDER_INDICATORS = {
    "ipc": None,
    "llc_miss_rate": None,
}


class VerdictError(RuntimeError):
    """verdict 層の fail-closed 拒否 (型分離違反・入力破綻)。"""


def _verified_oracle_verdict_api():
    seal = object()

    @dataclass(frozen=True, init=False)
    class VerifiedOracleVerdict:
        """``verify_oracle_verdict`` 経由でのみ構築される oracle verdict token。

        production consumer が本型を要求し、正規構築を verifier に閉じる規律的保証である。
        任意 Python コードによる ``object.__new__`` 等の in-process 偽造は信頼境界外。
        発行後の document 改竄は ``judge_combined`` が canonical hash と plain-type で
        検出する。``object.__setattr__`` による field 差し替えは信頼境界外。
        """

        document: _artifacts.OfficialVerdict
        document_sha256: str

        def __init__(self, document, *, _seal=None):
            if _seal is not seal:
                raise VerdictError(
                    "VerifiedOracleVerdict は verify_oracle_verdict の検証結果からのみ構築できる"
                )
            if type(document) is not _artifacts.OfficialVerdict:
                raise VerdictError(
                    "VerifiedOracleVerdict.document は OfficialVerdict exact type でなければならない"
                )
            object.__setattr__(self, "document", document)
            object.__setattr__(
                self,
                "document_sha256",
                hashlib.sha256(_canonical_json_text(document).encode("utf-8")).hexdigest(),
            )

    def seal_verifier(function):
        def verified(
                oracle_source, *, observations_source, verified_manifest, approved_spec):
            return function(
                oracle_source,
                observations_source=observations_source,
                verified_manifest=verified_manifest,
                approved_spec=approved_spec,
                _seal=seal,
            )

        verified.__name__ = function.__name__
        verified.__qualname__ = function.__qualname__
        verified.__doc__ = function.__doc__
        verified.__annotations__ = {
            key: (VerifiedOracleVerdict if key == "return" else value)
            for key, value in function.__annotations__.items()
            if key != "_seal"
        }
        return verified

    return VerifiedOracleVerdict, seal_verifier


VerifiedOracleVerdict, _seal_verified_oracle_verdict = _verified_oracle_verdict_api()
del _verified_oracle_verdict_api


def _canonical_json_text(value: object) -> str:
    try:
        return json.dumps(
            value, sort_keys=True, ensure_ascii=False, allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise VerdictError(f"oracle verdict を canonical JSON に変換できない: {exc}") from exc


_PLAIN_JSON_TYPES = (dict, list, str, int, float, bool, type(None))


def _assert_plain_json_values(container, *, label: str) -> None:
    """nested 値が plain JSON 型ちょうどであることを再帰的に確認する。

    top-level は marker 型の dict subclass を許すが、その中身に subclass を混ぜることを
    禁じる。``__getitem__`` を上書きした dict subclass で canonical bytes と consumer が
    見る値を分離する攻撃を落とす。
    """
    if not isinstance(container, (dict, list)):
        raise VerdictError(f"{label} は JSON container でなければならない")

    def walk(value, *, path: str) -> None:
        value_type = type(value)
        if value_type not in _PLAIN_JSON_TYPES:
            raise VerdictError(
                f"{label} の nested 値は plain JSON 型でなければならない: {path}"
            )
        if value_type is dict:
            for key, item in value.items():
                if type(key) is not str:
                    raise VerdictError(
                        f"{label} の object key は plain str でなければならない: {path}"
                    )
                walk(item, path=f"{path}.{key}")
        elif value_type is list:
            for index, item in enumerate(value):
                walk(item, path=f"{path}[{index}]")

    if isinstance(container, dict):
        for key, value in container.items():
            if type(key) is not str:
                raise VerdictError(
                    f"{label} の object key は plain str でなければならない: $"
                )
            walk(value, path=f"$.{key}")
    else:
        for index, value in enumerate(container):
            walk(value, path=f"$[{index}]")


@_seal_verified_oracle_verdict
def verify_oracle_verdict(
        oracle_source, *, observations_source, verified_manifest, approved_spec, _seal,
) -> VerifiedOracleVerdict:
    """oracle verdict を authority に束縛して observations から再導出する。

    strict loader で両文書を一度だけ読み、authority token と SHA field の exact type、
    manifest document の plain JSON 型、schedule 射影、manifest document hash、spec 束縛、
    oracle の manifest authority、observations からの再導出、全文書の canonical JSON 型厳密一致
    を順に検査する。全検査通過時だけ封印 token を返す。
    """
    document = _artifacts.load_official_verdict(oracle_source)
    observations = _artifacts.load_official_observations(observations_source)

    if type(verified_manifest) is not s8b_oracle_manifest.VerifiedManifest:
        raise TypeError("VerifiedManifest exact type が必要")
    if type(approved_spec) is not s8b_oracle_spec.ReviewedSpec:
        raise VerdictError("approved_spec は ReviewedSpec exact type でなければならない")
    if type(verified_manifest.sha256) is not str:
        raise VerdictError("VerifiedManifest.sha256 は plain str でなければならない")
    if type(approved_spec.sha256) is not str:
        raise VerdictError("ReviewedSpec.sha256 は plain str でなければならない")

    _assert_plain_json_values(
        verified_manifest.document,
        label="VerifiedManifest.document",
    )
    schedule_projection = s8b_oracle_judge.project_verified_manifest_schedule(
        verified_manifest,
    )
    if (s8b_oracle_manifest._canonical_sha256(verified_manifest.document)
            != verified_manifest.sha256):
        raise VerdictError(
            "VerifiedManifest.document が発行時の canonical hash と一致しない (事後改竄)"
        )
    if verified_manifest.document.get("spec_sha256") != approved_spec.sha256:
        raise VerdictError(
            "approved_spec が検証済み manifest の spec_sha256 と一致しない"
        )
    if document.get("manifest_sha256") != verified_manifest.sha256:
        raise VerdictError(
            "oracle verdict の manifest_sha256 が検証済み manifest の実値と一致しない"
        )

    rederived = s8b_oracle_judge.judge_oracle(
        observations,
        schedule_projection=schedule_projection,
        verified_manifest_sha256=verified_manifest.sha256,
        approved_spec_sha256=approved_spec.sha256,
    )
    if _canonical_json_text(rederived) != _canonical_json_text(document):
        raise VerdictError("oracle verdict が observations からの再導出結果と一致しない")

    return VerifiedOracleVerdict(document=document, _seal=_seal)


del _seal_verified_oracle_verdict


def _reason(code: str, message: str) -> dict:
    return {"code": code, "message": message}


def _sorted_reasons(reasons: Sequence[Mapping]) -> list[dict]:
    return sorted((dict(reason) for reason in reasons),
                  key=lambda reason: (str(reason.get("code")), str(reason.get("message")),
                                      str(reason.get("holdout"))))


# ---------------------------------------------------------------------------
# 型分離 (C3-2): 検証済み prediction
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VerifiedPrediction:
    """``verify_prediction`` 経由でのみ構築される検証済み prediction 文書 (C3-2)。

    ``judge_combined`` はこの型だけを受理し、未検証の生 dict を拒否する。保証は
    「production consumer が本型を要求し、構築を ``verify_prediction`` に閉じる」規律に
    限定する (RatifiedFreeze/VerifiedManifest と同じ convention。任意 Python コードに
    対する偽造不能ではない)。frozen は field 束縛の再代入防止であって document dict の
    深い不変化ではない (後続 wave の責務)。
    """
    document: Mapping


def verify_prediction(document, *, freeze: Mapping, root=ROOT) -> VerifiedPrediction:
    """prediction freeze を全検証したうえで ``VerifiedPrediction`` を返す (C3-2)。

    検証内容:
    1. ``verify_prediction_freeze`` (hash chain / basis / 全セル再導出 / commit pin /
       agent raw 再 parse。SelectorFreezeError on fail)。
    2. off arm が stock 静的既定であること (decision_method=static_default かつ choice=
       静的既定 ID かつ binding=stock_common) の機械検査。
    3. 各セルの choice_id が catalog の合法 ID (欠測 null は許容、非空文字列なら合法)。

    いずれかに失敗したら例外 (fail-closed)。1 は SelectorFreezeError、2/3 は VerdictError。
    """
    verify_prediction_freeze(document, freeze=freeze, root=root)
    _assert_off_stock_and_catalog(document)
    return VerifiedPrediction(document=document)


def _assert_off_stock_and_catalog(document: Mapping) -> None:
    """off=stock 機械検査と choice_id catalog 合法性を defense-in-depth で再検査する。

    verify_prediction_freeze も off=静的既定を強制するが、C3-2 は verdict 側での
    独立した機械検査を要求するため二段目として明示する (恒真化しない — 実際に走る)。
    """
    if not isinstance(document, Mapping):
        raise VerdictError("prediction document が object でない")
    rows = document.get("rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        raise VerdictError("prediction rows が array でない")
    expected_stock_binding = CHOICE_TO_BINDING.get(STATIC_DEFAULT_CHOICE_ID)
    if expected_stock_binding != STOCK_CONFIGURATION:
        # catalog 定数と stock 構成名の不一致は信頼中核の内部矛盾 → fail-closed。
        raise VerdictError("静的既定 choice の binding が stock 構成名と一致しない")
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise VerdictError(f"rows[{index}] が object でない")
        choice_id = row.get("choice_id")
        if choice_id is not None and choice_id not in CHOICE_TO_BINDING:
            raise VerdictError(f"rows[{index}].choice_id が catalog 外: {choice_id!r}")
        if row.get("arm") == "off":
            if row.get("decision_method") != "static_default":
                raise VerdictError(f"rows[{index}] off arm が static_default でない")
            if choice_id != STATIC_DEFAULT_CHOICE_ID:
                raise VerdictError(
                    f"rows[{index}] off arm の choice が静的既定 ID でない: {choice_id!r}")
            if row.get("binding_key") != STOCK_CONFIGURATION:
                raise VerdictError(
                    f"rows[{index}] off arm の binding が stock 構成でない:"
                    f" {row.get('binding_key')!r}")


# ---------------------------------------------------------------------------
# prediction / oracle 索引
# ---------------------------------------------------------------------------

def _prediction_index(prediction: Mapping) -> tuple[dict, list[dict]]:
    """prediction 文書から (target, arm) → choice_id の索引を作る。

    choice_id が str でない (invalid/missing の null を含む) セルは None に落とす。
    schema/構造の破綻は reasons へ積む (呼び手が判定不能へ倒す)。
    """
    reasons: list[dict] = []
    if not isinstance(prediction, Mapping):
        reasons.append(_reason("prediction-type", "prediction が object でない"))
        return {}, reasons
    if prediction.get("schema_version") != PREDICTION_SCHEMA:
        reasons.append(_reason("prediction-schema", "prediction schema_version が不一致"))
    rows = prediction.get("rows")
    index: dict[tuple[str, str], object] = {}
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        reasons.append(_reason("prediction-rows", "prediction rows が array でない"))
        return {}, reasons
    for row in rows:
        if not isinstance(row, Mapping):
            reasons.append(_reason("prediction-row-type", "prediction row が object でない"))
            continue
        target = row.get("target_holdout")
        arm = row.get("arm")
        if not isinstance(target, str) or not target or arm not in _ARMS:
            reasons.append(_reason("prediction-cell", "prediction row の target/arm が不正"))
            continue
        cell = (target, arm)
        if cell in index:
            reasons.append(_reason("prediction-duplicate", f"prediction cell 重複: {cell}"))
            continue
        choice = row.get("choice_id")
        index[cell] = choice if isinstance(choice, str) and choice else None
    return index, reasons


def _swapped_expectations(prediction: Mapping) -> tuple[dict, list[dict]]:
    """swapped 追従の凍結期待値 (target → expected on-choice) を取り出す。"""
    reasons: list[dict] = []
    expectations = prediction.get("swapped_follow_expectations") if isinstance(
        prediction, Mapping) else None
    result: dict[str, object] = {}
    if not isinstance(expectations, Sequence) or isinstance(
            expectations, (str, bytes, bytearray)):
        reasons.append(_reason(
            "swapped-expectations", "swapped_follow_expectations が array でない"))
        return {}, reasons
    for entry in expectations:
        if not isinstance(entry, Mapping):
            reasons.append(_reason("swapped-entry", "swapped 期待 entry が object でない"))
            continue
        target = entry.get("target_holdout")
        if not isinstance(target, str) or not target:
            reasons.append(_reason("swapped-target", "swapped 期待の target が不正"))
            continue
        if target in result:
            reasons.append(_reason("swapped-duplicate", f"swapped 期待の target 重複: {target}"))
            continue
        expected = entry.get("expected_choice_id")
        result[target] = expected if isinstance(expected, str) and expected else None
    return result, reasons


def _expected_holdout_set(expected_holdouts: object) -> tuple[list[str], list[dict]]:
    """凍結 holdout ID 集合を検証する (裁定 5 項 1 の全称量化の領域)。

    非集合・Mapping・str/bytes・空・非文字列要素・重複はいずれも判定不能へ倒す (fail-closed)。
    """
    reasons: list[dict] = []
    if (not isinstance(expected_holdouts, Collection)
            or isinstance(expected_holdouts, (str, bytes, bytearray, Mapping))):
        reasons.append(_reason(
            "expected-holdouts", "expected_holdouts が holdout ID の集合でない"))
        return [], reasons
    seen: set[str] = set()
    for value in expected_holdouts:
        if not isinstance(value, str) or not value:
            reasons.append(_reason(
                "expected-holdout-id", "expected_holdouts に非空文字列でない要素がある"))
            continue
        if value in seen:
            reasons.append(_reason(
                "expected-holdout-duplicate", f"expected_holdouts の重複: {value}"))
            continue
        seen.add(value)
    if not seen:
        reasons.append(_reason("expected-holdouts-empty", "expected_holdouts が空"))
    return sorted(seen), reasons


def _oracle_holdouts(oracle: Mapping) -> tuple[dict, list[dict]]:
    reasons: list[dict] = []
    if not isinstance(oracle, Mapping):
        reasons.append(_reason("oracle-type", "oracle verdict が object でない"))
        return {}, reasons
    if oracle.get("schema_version") != ORACLE_SCHEMA:
        reasons.append(_reason("oracle-schema", "oracle verdict schema_version が不一致"))
    holdouts = oracle.get("holdouts")
    if not isinstance(holdouts, Mapping):
        reasons.append(_reason("oracle-holdouts", "oracle holdouts が object でない"))
        return {}, reasons
    return dict(holdouts), reasons


def _combined_measurement_conditions(
        oracle: Mapping, floor_source: Mapping | None,
) -> tuple[dict | None, list[dict], bool]:
    """bound floor observation と oracle campaign 条件を claim gate 後に比較する。"""
    reasons: list[dict] = []
    floor_observation = None
    if not isinstance(floor_source, Mapping):
        reasons.append(_reason(
            "floor-source-type", "bound floor_source が object でない",
        ))
    elif isinstance(floor_source, Mapping):
        raw_floor_observation = floor_source.get("perf_observation")
        if raw_floor_observation is not None:
            try:
                contexts = _floor_stats.floor_perf_validation_contexts(floor_source)
                run_cmd, leading_indicators = contexts[0]
                allowed = _perf_preflight.perf_claim_allowed(
                    raw_floor_observation,
                    "throughput",
                    run_cmd=run_cmd,
                    leading_indicators=leading_indicators,
                )
                floor_observation = _perf_preflight.validate_perf_observation(
                    raw_floor_observation,
                    run_cmd=run_cmd,
                    leading_indicators=leading_indicators,
                )
                for candidate_cmd, candidate_indicators in contexts[1:]:
                    candidate = _perf_preflight.validate_perf_observation(
                        raw_floor_observation,
                        run_cmd=candidate_cmd,
                        leading_indicators=candidate_indicators,
                    )
                    if candidate != floor_observation:
                        raise _perf_preflight.PerfPreflightError(
                            "floor session 間で perf observation が不一致"
                        )
                if not allowed:
                    reasons.append(_reason(
                        "floor-measurement-claim",
                        "floor measurement condition は throughput claim を許可しない",
                    ))
                if floor_observation.get("preflight") != floor_source.get("perf_preflight"):
                    reasons.append(_reason(
                        "floor-measurement-preflight",
                        "floor perf_observation.preflight が floor_source receipt と不一致",
                    ))
            except _perf_preflight.PerfPreflightError as exc:
                reasons.append(_reason(
                    "floor-measurement-condition",
                    f"floor perf_observation が不正: {exc}",
                ))

    raw_oracle_conditions = oracle.get("measurement_conditions")
    oracle_conditions: list[dict] | None = None
    oracle_observations: list[dict | None] = []
    if raw_oracle_conditions is not None:
        if (not isinstance(raw_oracle_conditions, Sequence)
                or isinstance(raw_oracle_conditions, (str, bytes, bytearray))
                or not raw_oracle_conditions):
            reasons.append(_reason(
                "oracle-measurement-conditions",
                "oracle measurement_conditions が空でない array でない",
            ))
            oracle_conditions = []
        else:
            oracle_conditions = []
            for entry in raw_oracle_conditions:
                if (not isinstance(entry, Mapping)
                        or set(entry) != _MEASUREMENT_CONDITION_KEYS):
                    reasons.append(_reason(
                        "oracle-measurement-condition-schema",
                        "oracle measurement condition の exact key 集合が不一致",
                    ))
                    continue
                normalized_entry = dict(entry)
                observation = entry.get("perf_observation")
                if observation is not None:
                    try:
                        normalized = _perf_preflight.validate_perf_observation(
                            observation,
                            run_cmd=_DEGRADED_PLACEHOLDER_CMD,
                            leading_indicators=_DEGRADED_PLACEHOLDER_INDICATORS,
                        )
                    except _perf_preflight.PerfPreflightError as exc:
                        reasons.append(_reason(
                            "oracle-measurement-condition",
                            f"oracle perf_observation が不正: {exc}",
                        ))
                        continue
                    normalized_entry["perf_observation"] = normalized
                    observation = normalized
                oracle_conditions.append(normalized_entry)
                oracle_observations.append(observation)

    conditions_present = (
        floor_observation is not None or raw_oracle_conditions is not None
    )
    mismatch = False
    if raw_oracle_conditions is None:
        mismatch = floor_observation is not None
    elif floor_observation is None:
        mismatch = True
    else:
        mismatch = (
            not oracle_observations
            or any(observation != floor_observation
                   for observation in oracle_observations)
        )
    if mismatch:
        reasons.append(_reason(
            "measurement-conditions-mismatch",
            "bound floor_source と oracle の測定条件が一致しない",
        ))
    evidence = None
    if conditions_present:
        evidence = {
            "floor_perf_observation": floor_observation,
            "oracle": oracle_conditions,
        }
    return evidence, reasons, mismatch or bool(reasons)


def _pred_diff(on_choice: object, off_choice: object) -> str:
    """条件 1 の holdout 単位判定: on 予測 choice と off 予測 choice が異なるか。"""
    if on_choice is None or off_choice is None:
        return INDETERMINATE
    return HOLDS if on_choice != off_choice else REFUTED


def _swapped_follow(swapped_choice: object, expected_choice: object) -> str:
    """条件 2 の holdout 単位判定: swapped 予測が swap 元 on 予測へ追従するか。"""
    if swapped_choice is None or expected_choice is None:
        return INDETERMINATE
    return HOLDS if swapped_choice == expected_choice else REFUTED


# ---------------------------------------------------------------------------
# 結合判定
# ---------------------------------------------------------------------------

def _existential(verdicts: Sequence[str]) -> str:
    """存在量化 (OR)。成立が優先、次に判定不能、全て不成立でのみ不成立。空なら判定不能。"""
    if not verdicts:
        return INDETERMINATE
    if any(verdict == HOLDS for verdict in verdicts):
        return HOLDS
    if any(verdict == INDETERMINATE for verdict in verdicts):
        return INDETERMINATE
    return REFUTED


def _conjunction(verdicts: Sequence[str]) -> str:
    """全称量化 / 連言 (AND)。全て成立でのみ成立、判定不能が不成立に優先する。空なら判定不能。"""
    if not verdicts:
        return INDETERMINATE
    if all(verdict == HOLDS for verdict in verdicts):
        return HOLDS
    if any(verdict == INDETERMINATE for verdict in verdicts):
        return INDETERMINATE
    return REFUTED


def judge_combined(*, prediction: VerifiedPrediction, oracle: VerifiedOracleVerdict,
                   expected_holdouts: object, floor_source: Mapping) -> dict:
    """検証済み prediction と oracle verdict から §6 の2条件と結論を判定する。

    ``expected_holdouts`` は凍結 holdout ID 集合であり、条件2の全称量化領域である。
    ``floor_source`` は ratified freeze に束縛された measurement-condition 検証用文書で、
    条件1/条件2の判定値には使わない。

    この撤去は between-run floor・scale gate・oracle unique-best 確定・両構成 eligibility 判定の
    4 保証を判定基盤から外す**意図的な受理拡大**であり、§10.1/D510
    (docs/phase3-8b-descriptor-design.md §10, docs/decisions.md D510) が明示承認している。
    off=stock 契約は ``verify_prediction``/``_assert_off_stock_and_catalog`` が独立に担保し、
    ``judge_combined`` はこれを再検証しない (verify_prediction をバイパスする経路への防御は scope 外)。

    出力は条件1・条件2、holdout ごとの prediction evidence、oracle provenance、および構造検証理由を
    含む。入力や測定条件に構造破綻があれば判定不能へ倒す。oracle の verdict は診断情報として残すが、
    結論計算には使わない。
    """
    if not isinstance(prediction, VerifiedPrediction):
        raise VerdictError(
            "judge_combined は VerifiedPrediction のみ受理する (未検証 object は渡せない)")
    if type(oracle) is not VerifiedOracleVerdict:
        raise VerdictError(
            "judge_combined は VerifiedOracleVerdict exact type のみ受理する")
    _assert_plain_json_values(
        oracle.document,
        label="VerifiedOracleVerdict.document",
    )
    oracle_document_sha256 = hashlib.sha256(
        _canonical_json_text(oracle.document).encode("utf-8")
    ).hexdigest()
    if oracle_document_sha256 != oracle.document_sha256:
        raise VerdictError(
            "VerifiedOracleVerdict.document が発行時の canonical hash と一致しない (事後改竄)"
        )
    document = prediction.document
    oracle_document = oracle.document
    pred_index, pred_reasons = _prediction_index(document)
    expectations, exp_reasons = _swapped_expectations(document)
    oracle_holdouts, oracle_reasons = _oracle_holdouts(oracle_document)
    expected_domain, holdout_reasons = _expected_holdout_set(expected_holdouts)
    structural_reasons = pred_reasons + exp_reasons + oracle_reasons + holdout_reasons
    measurement_conditions, measurement_reasons, _measurement_mismatch = (
        _combined_measurement_conditions(oracle_document, floor_source)
    )
    structural_reasons.extend(measurement_reasons)

    expected_set = set(expected_domain)
    present_targets = {target for (target, _arm) in pred_index}
    unexpected = sorted(present_targets - expected_set)
    if unexpected:
        structural_reasons.append(_reason(
            "unexpected-holdout",
            f"prediction が凍結 holdout 集合外の target を含む: {unexpected}"))
    missing = sorted(expected_set - present_targets)
    if missing:
        structural_reasons.append(_reason(
            "missing-holdout",
            f"prediction が凍結 holdout を欠く (両 holdout 必須): {missing}"))

    prediction_body_sha256 = (document.get("body_sha256")
                              if isinstance(document, Mapping) else None)
    selector_basis_sha256 = (document.get("selector_basis_sha256")
                             if isinstance(document, Mapping) else None)
    oracle_manifest_sha256 = oracle_document.get("manifest_sha256")
    oracle_status = oracle_document.get("status")

    targets = expected_domain

    per_holdout: dict[str, dict] = {}
    pred_diff_verdicts: list[str] = []
    follow_verdicts: list[str] = []

    for target in targets:
        on_choice = pred_index.get((target, "on"))
        off_choice = pred_index.get((target, "off"))
        swapped_choice = pred_index.get((target, "swapped"))
        expected_choice = expectations.get(target)
        oracle_holdout = oracle_holdouts.get(target)

        diff = _pred_diff(on_choice, off_choice)
        follow = _swapped_follow(swapped_choice, expected_choice)

        pred_diff_verdicts.append(diff)
        follow_verdicts.append(follow)

        per_holdout[target] = {
            "on_choice_id": on_choice,
            "off_choice_id": off_choice,
            "swapped_choice_id": swapped_choice,
            "expected_swapped_choice_id": expected_choice,
            "on_off_prediction_difference": diff,
            "swapped_follow": follow,
            "oracle_verdict": (oracle_holdout.get("verdict")
                               if isinstance(oracle_holdout, Mapping) else None),
        }

    structural_indeterminate = bool(structural_reasons) or not targets

    if structural_indeterminate:
        condition1 = INDETERMINATE
        condition2 = INDETERMINATE
    else:
        condition1 = _existential(pred_diff_verdicts)
        condition2 = _conjunction(follow_verdicts)

    conclusion = _conjunction([condition1, condition2])

    conditions = {
        "on_off_prediction_difference": {
            "verdict": condition1,
            "evidence": {
                "prediction_body_sha256": prediction_body_sha256,
                "selector_basis_sha256": selector_basis_sha256,
            },
        },
        "swapped_follow": {
            "verdict": condition2,
            "evidence": {
                "prediction_body_sha256": prediction_body_sha256,
                "selector_basis_sha256": selector_basis_sha256,
                "derangement": (dict(document.get("derangement"))
                                if isinstance(document, Mapping)
                                and isinstance(document.get("derangement"), Mapping)
                                else None),
            },
        },
    }

    result = {
        "schema_version": SCHEMA_VERSION,
        "status": conclusion,
        "conditions": conditions,
        "holdouts": per_holdout,
        "evidence": {
            "prediction_body_sha256": prediction_body_sha256,
            "selector_basis_sha256": selector_basis_sha256,
            "oracle_manifest_sha256": oracle_manifest_sha256,
            "oracle_status": oracle_status,
        },
        "reasons": _sorted_reasons(structural_reasons),
    }
    if measurement_conditions is not None:
        result["measurement_conditions"] = measurement_conditions
    return result


# ---------------------------------------------------------------------------
# CLI (C2-7): holdout 外部入力を廃止し検証済み freeze から導出
# ---------------------------------------------------------------------------

def _load_json_object(path: Path) -> dict:
    def unique_object(pairs):
        result: dict = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key!r}")
            result[key] = value
        return result

    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=unique_object,
        parse_constant=lambda token: (_ for _ in ()).throw(
            ValueError(f"non-finite JSON constant: {token}")),
    )
    if not isinstance(value, dict):
        raise ValueError(f"JSON top-level が object でない: {path}")
    return value


def _write_create_only(path: Path, value: Mapping) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def _holdout_ids(freeze_document: Mapping) -> list[str]:
    holdouts = freeze_document.get("holdouts")
    if not isinstance(holdouts, Mapping) or not holdouts:
        raise VerdictError("freeze.holdouts が空でない object でない")
    if not all(isinstance(name, str) and name for name in holdouts):
        raise VerdictError("freeze.holdouts の key が空でない文字列でない")
    return sorted(holdouts)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    judge = sub.add_parser(
        "judge",
        help=("prediction × oracle × 検証済み freeze を結合判定する。"
              "holdout 集合は freeze から導出し、freeze identity・manifest 整合を検証する。"
              "外部 --floors/--holdouts 入力は廃止した (C2-7)。"))
    judge.add_argument("--prediction", type=Path, required=True,
                       help="prediction freeze 文書 (verify_prediction で全検証する)")
    judge.add_argument("--oracle", type=Path, required=True,
                       help="judge_oracle 出力 (verify_oracle_verdict で再導出検証する)")
    judge.add_argument("--manifest", type=Path, required=True,
                       help="oracle verdict を束縛する official manifest")
    judge.add_argument("--observations", type=Path, required=True,
                       help="oracle verdict の再導出元 observations")
    judge.add_argument("--freeze", type=Path, required=True,
                       help="検証済み holdout freeze (identity・holdout 整合検証用)。sha256 一致を強制する")
    judge.add_argument("--freeze-sha256", required=True,
                       help="freeze bytes の期待 sha256 (fail-closed 照合)")
    judge.add_argument("--root", type=Path, default=ROOT,
                       help="prediction の commit pin / source / protocol path 解決 root")
    judge.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        verified_freeze = load_verified_freeze(args.freeze, args.freeze_sha256)
        root = Path(args.root)
        ratified = s8b_ratified_freeze.load_ratified_freeze(root)
        s8b_ratified_freeze.assert_g1_floor_selection_identity(ratified, root)
        reverified = s8b_ratified_freeze.reverify_published_freeze(ratified, root)
        approved = s8b_oracle_spec.load_approved_spec(root)
        verified_manifest = s8b_oracle_manifest.verify_manifest(
            args.manifest,
            root=root,
            freeze_document=reverified.ratified.document,
            freeze_sha256=reverified.ratified.sha256,
            approved_spec=approved,
        )
        if verified_freeze.sha256 != reverified.ratified.sha256:
            raise VerdictError(
                "--freeze が published ratified freeze の実値と一致しない"
            )

        freeze_document = verified_freeze.document
        holdout_ids = _holdout_ids(freeze_document)
        # floor の holdout 集合と budget を manifest と共通の validator で検査する。
        _validate_execution_snapshot(freeze_document, holdout_ids=holdout_ids)
        floor_source = _artifacts.strict_load_json_object(
            s8b_ratified_freeze.read_floor_source_blob(
                reverified.ratified, root,
            )
        )

        prediction_document = _load_json_object(args.prediction)
        verified_prediction = verify_prediction(
            prediction_document, freeze=freeze_document, root=root)
        verified_oracle = verify_oracle_verdict(
            args.oracle,
            observations_source=args.observations,
            verified_manifest=verified_manifest,
            approved_spec=approved,
        )

        verdict = judge_combined(
            prediction=verified_prediction, oracle=verified_oracle,
            expected_holdouts=set(holdout_ids), floor_source=floor_source)
        _write_create_only(args.out, verdict)
    except (OSError, json.JSONDecodeError, TypeError, ValueError,
            VerdictError, _artifacts.OracleArtifactTypeError,
            FreezeIOError, ManifestError, SelectorFreezeError,
            SelectorInputError, DescriptorError,
            s8b_ratified_freeze.RatifiedFreezeError,
            s8b_oracle_spec.ReviewedSpecError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
