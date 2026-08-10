# -*- coding: utf-8 -*-
"""8b §6 判定表: prediction × oracle を結合する I/O 非依存な三値判定。

裁定 5 (output/insights/2026-07-16_s8b-ruling-package.md) が逐語凍結した
truth table を機械判定する純関数を提供する。strict v2 wave (2026-07-18) で
per-pair floor / trusted projector / scale gate / VerifiedPrediction を導入した
(C3-1/C3-2/C3-8、§5-iii/iv の実装解釈)。

- 条件 1 (on/off 予測差): on の予測 choice が off の予測 choice と異なる holdout が存在する
  (存在量化)。floor は使わない。
- 条件 2 (swapped 追従): swapped の予測が swap 元への on 予測へ family ID 一致で追従する。
  両 holdout 必須 (全称量化)。全称の領域は prediction に現れた holdout ではなく、呼び手が渡す
  凍結 holdout 集合 (``expected_holdouts``) そのものである (裁定 5 項 1)。
- 条件 3 (oracle floor 超): on 予測構成と off 予測構成の oracle 実測差が方向付きで当該 holdout の
  当該 pair floor を超える。floor を使うのはこの条件のみ。
- 結論: 条件 2 と、「同一 holdout で 予測差 かつ floor 超」の存在量化の連言 (裁定 5 項 3)。

**名前空間 (C3-1/C4-2 の核):** prediction の choice は不透明 ID (c01..c06)、oracle の
configurations と floor の pairs はいずれも構成名 (binding_key = configuration_id) を key と
する。両者は名前空間が異なるため、判定は必ず trusted な choice→binding 対応
(``CHOICE_TO_BINDING``。prediction 検証時に selector_basis で freeze へ束縛済み) を経由して
解決する。choice_id を直接 oracle/floor の key に使ってはならない。

**per-pair floor (C3-1、§5-iii):** floor は ``freeze.floor.by_holdout.<h>`` の per-pair 表
(``{pairs, scale_ref, scalar_alt}``) を持ち、pairs は「構成集合 − stock」を key とする。
verdict は holdout→scalar 契約 (``_floor_exceeded`` は単一 float を受ける) を維持したまま、
trusted projector (``project_pair_floor``) が on の予測構成へ解決した pair floor だけを渡す。
- on == off (予測構成が同一) → 差は定義上 0 で正の floor を超えない。floor 照会なしで不成立側
  (REFUTED)。off は静的既定で stock 固定のため、これは on も stock の縮退ケース。
- off が stock でない → protocol violation として構造化記録し、当該 holdout の条件 3 を判定不能へ。
- pair floor が null (機械異常の伝播) → 判定不能。

**scale gate (C3-8、§5-iv):** judge (oracle 観測の集約) 完了後に、holdout ごとに stock 構成の
実測 median を ``scale_ref`` (floor campaign 由来の期待値) と比較する。相対差
``abs(observed − scale_ref) / scale_ref`` を分母 scale_ref・Fraction 厳密算術で評価し、
``scale_adequacy_rel_tolerance`` を超えたら scale-inadequate とする (ちょうど tolerance は
adequate)。tolerance は暗黙 default を禁じ、呼び手が protocol 由来値を明示引数で渡す。
scale inadequate / stock 非 eligible / scale_ref null は、当該 holdout の **条件 3 のみ**
判定不能へ倒す (他条件は不変)。scale 状態は verdict 出力 schema に構造化して残す。
なお on == off の短絡 (差 0) は floor も oracle median も参照しないため scale gate の対象外
(§5-iii が「不成立側」と定めた縮退ケースを scale の不確かさで覆さない)。

三値伝播はすべて fail-closed である。selector 出力の欠測・不正 (choice_id=null)、oracle の
exact tie (oracle 非一意)、excluded 観測を含む holdout、floor 未確定・scale 不適はいずれも当該
条件を判定不能へ倒し、§6 結論行へ伝播する。REFUTED (不成立) は関連データが完全なときにのみ返す。

**型分離 (C3-2):** ``judge_combined`` は検証済み ``VerifiedPrediction`` のみを受理する。
未検証の生 prediction 文書を渡すと fail-closed に拒否する。``VerifiedPrediction`` は
``verify_prediction`` 経由でのみ構築され、その内部で prediction freeze の全検証 + off=stock
の機械検査 + choice_id の catalog 合法性検査を通す。
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
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


from . import s8b_oracle_artifacts as _artifacts  # noqa: E402



# schema v2: per-pair floor / scale gate / protocol_violations の導入で出力形が
# 変わったため v1 から bump した (namespace 修正・scale 状態・floor evidence の per-pair 化)。
SCHEMA_VERSION = _artifacts.COMBINED_VERDICT_SCHEMA
PREDICTION_SCHEMA = "8b-selector-prediction-freeze/v1"
ORACLE_SCHEMA = _artifacts.OFFICIAL_VERDICT_SCHEMA

# 三値: 成立 / 不成立 / 判定不能。
HOLDS = "holds"
REFUTED = "refuted"
INDETERMINATE = "indeterminate"

# scale gate の 4 態 (§5-iv)。adequate 以外はいずれも当該 holdout の条件 3 を判定不能へ倒す。
SCALE_ADEQUATE = "adequate"
SCALE_INADEQUATE = "inadequate"
SCALE_STOCK_INELIGIBLE = "stock-ineligible"
SCALE_REF_NULL = "scale-ref-null"

# projector の解決結果。
_PROJECT_QUERY = "query"            # pair floor を取得できた (query して条件 3 を判定)
_PROJECT_REFUTED = "refuted"        # on == off 短絡 (差 0 で不成立側、floor 照会なし)
_PROJECT_INDETERMINATE = "indeterminate"  # off≠stock / pair null / 欠測 → 判定不能

_ARMS = ("on", "off", "swapped")


class VerdictError(RuntimeError):
    """verdict 層の fail-closed 拒否 (型分離違反・tolerance 契約違反・入力破綻)。"""


def _reason(code: str, message: str) -> dict:
    return {"code": code, "message": message}


def _sorted_reasons(reasons: Sequence[Mapping]) -> list[dict]:
    return sorted((dict(reason) for reason in reasons),
                  key=lambda reason: (str(reason.get("code")), str(reason.get("message")),
                                      str(reason.get("holdout"))))


def _is_real(value: object) -> bool:
    """bool を除く有限な実数のみ真。"""
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(float(value)))


def _tolerance_fraction(value: object) -> Optional[Fraction]:
    """scale tolerance を厳密な Fraction へ変換する。不正なら None。

    protocol document は ``scale_adequacy_rel_tolerance`` を十進文字列 ("0.10") で
    保持するため、``Fraction(str)`` で 1/10 を厳密に得る。float も受けるが二進
    近似のまま Fraction 化する (呼び手が str を渡せば厳密)。bool・非有限・非数値は None。
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return Fraction(value)
    if isinstance(value, str):
        try:
            return Fraction(value)
        except (ValueError, ZeroDivisionError):
            return None
    return None


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


def _eligible_median(oracle_holdout: Mapping, configuration_id: object) -> Optional[float]:
    """oracle holdout の当該 configuration (binding_key) が eligible なら有限 median を返す。

    oracle の configurations は configuration_id (= binding_key) を key とする。choice_id を
    渡してはならない (名前空間混同。C3-1)。
    """
    if not isinstance(configuration_id, str) or not configuration_id:
        return None
    configurations = oracle_holdout.get("configurations")
    if not isinstance(configurations, Mapping):
        return None
    cell = configurations.get(configuration_id)
    if not isinstance(cell, Mapping) or cell.get("status") != "eligible":
        return None
    median = cell.get("median_of_medians")
    return float(median) if _is_real(median) else None


# ---------------------------------------------------------------------------
# trusted floor projector (C3-1、§5-iii)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProjectedFloor:
    """``project_pair_floor`` の解決結果。

    ``resolution`` は ``_PROJECT_QUERY / _PROJECT_REFUTED / _PROJECT_INDETERMINATE``。
    ``floor`` は query 時の pair floor (有限正 float)、それ以外は None。
    ``on_binding_key`` / ``off_binding_key`` は解決済み構成名 (oracle median 照会に使う)。
    ``violations`` は protocol violation (off≠stock 等) の構造化記録。
    """
    resolution: str
    floor: Optional[float]
    on_binding_key: Optional[str]
    off_binding_key: Optional[str]
    violations: tuple


def project_pair_floor(floor_by_holdout, choice_to_binding, holdout,
                       on_choice_id, off_choice_id) -> ProjectedFloor:
    """opaque choice を trusted 構成名へ解決し、on 予測構成の pair floor を投影する (C3-1)。

    ``floor_by_holdout`` は ``freeze.floor.by_holdout`` (holdout → {pairs, scale_ref,
    scalar_alt})、``choice_to_binding`` は信頼中核の choice→構成名 対応 (prediction 検証で
    selector_basis 経由に freeze へ束縛済み)。scalar 契約 (``_floor_exceeded`` は単一 float を
    受ける) は本 projector の外側で維持する。

    §6 縁 (§5-iii の実装解釈):
    - off が欠測 → 判定不能。
    - off が catalog 外 / stock 構成でない → protocol violation を記録して判定不能。
    - on が欠測 / catalog 外 → 判定不能。
    - on == off → 差 0 で不成立側 (REFUTED)。floor を照会しない (stock に pair は無い)。
    - on の pair floor が欠落 / null / 非有限正 → 判定不能。
    - それ以外 → query (有限正 pair floor)。
    """
    violations: list[dict] = []
    # --- off arm 側: stock 固定の機械検査 ---
    if off_choice_id is None:
        return ProjectedFloor(_PROJECT_INDETERMINATE, None, None, None, ())
    off_binding = (choice_to_binding.get(off_choice_id)
                   if isinstance(off_choice_id, str) else None)
    if off_binding is None:
        violations.append(_reason(
            "off-choice-unknown", f"off choice_id が catalog 外: {off_choice_id!r}"))
        return ProjectedFloor(_PROJECT_INDETERMINATE, None, None, None, tuple(violations))
    if off_binding != STOCK_CONFIGURATION:
        violations.append(_reason(
            "off-not-stock",
            f"off 予測構成が stock でない: {off_choice_id!r}→{off_binding!r}"))
        return ProjectedFloor(
            _PROJECT_INDETERMINATE, None, None, off_binding, tuple(violations))
    # --- on arm 側 ---
    if on_choice_id is None:
        return ProjectedFloor(_PROJECT_INDETERMINATE, None, None, off_binding, tuple(violations))
    on_binding = (choice_to_binding.get(on_choice_id)
                  if isinstance(on_choice_id, str) else None)
    if on_binding is None:
        violations.append(_reason(
            "on-choice-unknown", f"on choice_id が catalog 外: {on_choice_id!r}"))
        return ProjectedFloor(
            _PROJECT_INDETERMINATE, None, None, off_binding, tuple(violations))
    # on == off → 差 0 で不成立側 (floor 照会なし)。off が stock なので on も stock の縮退。
    if on_choice_id == off_choice_id:
        return ProjectedFloor(
            _PROJECT_REFUTED, None, on_binding, off_binding, tuple(violations))
    # --- pair floor 照会 ---
    entry = floor_by_holdout.get(holdout) if isinstance(floor_by_holdout, Mapping) else None
    pairs = entry.get("pairs") if isinstance(entry, Mapping) else None
    if not isinstance(pairs, Mapping) or on_binding not in pairs:
        violations.append(_reason(
            "floor-pair-missing",
            f"pair floor に on 構成 {on_binding!r} が無い (holdout={holdout!r})"))
        return ProjectedFloor(
            _PROJECT_INDETERMINATE, None, on_binding, off_binding, tuple(violations))
    pair_value = pairs[on_binding]
    if pair_value is None:
        return ProjectedFloor(
            _PROJECT_INDETERMINATE, None, on_binding, off_binding, tuple(violations))
    if not _is_real(pair_value) or float(pair_value) <= 0.0:
        violations.append(_reason(
            "floor-pair-invalid",
            f"pair floor {on_binding!r} が有限正でない: {pair_value!r}"))
        return ProjectedFloor(
            _PROJECT_INDETERMINATE, None, on_binding, off_binding, tuple(violations))
    return ProjectedFloor(
        _PROJECT_QUERY, float(pair_value), on_binding, off_binding, tuple(violations))


def _floor_exceeded(oracle_holdout: object, on_binding: object,
                    off_binding: object, floor: Optional[float]) -> str:
    """条件 3 の holdout 単位判定: oracle(on) − oracle(off) > floor か (方向付き)。

    floor 未確定、oracle 判定不能、oracle exact tie (oracle 非一意)、構成の oracle 非
    eligible はいずれも判定不能へ倒す。median は binding_key で照会する (名前空間の要)。
    """
    if floor is None:
        return INDETERMINATE
    if not isinstance(oracle_holdout, Mapping):
        return INDETERMINATE
    holdout_verdict = oracle_holdout.get("verdict")
    if holdout_verdict == "tie":  # exact tie = oracle 非一意 (裁定 5 項 4)
        return INDETERMINATE
    if holdout_verdict != "unique-best":  # indeterminate / 未知値は fail-closed
        return INDETERMINATE
    if on_binding is None or off_binding is None:
        return INDETERMINATE
    on_median = _eligible_median(oracle_holdout, on_binding)
    off_median = _eligible_median(oracle_holdout, off_binding)
    if on_median is None or off_median is None:
        return INDETERMINATE
    return HOLDS if (on_median - off_median) > floor else REFUTED


# ---------------------------------------------------------------------------
# scale gate (C3-8、§5-iv)
# ---------------------------------------------------------------------------

def _scale_state(oracle_holdout: object, scale_ref: object,
                 tolerance: Fraction) -> tuple[str, Optional[float]]:
    """当該 holdout の scale 適否を判定する。戻り値 = (state, observed_stock_median)。

    - scale_ref が null / 非有限正 → SCALE_REF_NULL。
    - stock 構成が oracle で非 eligible → SCALE_STOCK_INELIGIBLE。
    - それ以外: abs(observed − scale_ref)/scale_ref を分母 scale_ref・Fraction 厳密で評価し、
      tolerance 超過なら SCALE_INADEQUATE、ちょうど・未満なら SCALE_ADEQUATE。
    """
    if scale_ref is None:
        return SCALE_REF_NULL, None
    if not _is_real(scale_ref) or float(scale_ref) <= 0.0:
        return SCALE_REF_NULL, None
    observed = (_eligible_median(oracle_holdout, STOCK_CONFIGURATION)
                if isinstance(oracle_holdout, Mapping) else None)
    if observed is None:
        return SCALE_STOCK_INELIGIBLE, None
    ratio = abs(Fraction(observed) - Fraction(scale_ref)) / Fraction(scale_ref)
    if ratio > tolerance:
        return SCALE_INADEQUATE, observed
    return SCALE_ADEQUATE, observed


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


def judge_combined(*, prediction: VerifiedPrediction, oracle: _artifacts.OfficialVerdict,
                   floor_by_holdout: Mapping, expected_holdouts: object,
                   scale_tolerance: object) -> dict:
    """検証済み prediction・oracle verdict・per-pair floor から §6 の 3 条件と結論を判定する。

    ``prediction`` は ``VerifiedPrediction`` (未検証 dict は fail-closed に拒否)、
    ``oracle`` は ``judge_oracle`` の出力 (``8b-oracle-verdict/v1``)、``floor_by_holdout`` は
    ``freeze.floor.by_holdout`` の per-pair 表 (holdout → {pairs, scale_ref, scalar_alt})、
    ``expected_holdouts`` は凍結 holdout ID 集合 (裁定 5 項 1 の全称量化の領域)、
    ``scale_tolerance`` は protocol 由来の ``scale_adequacy_rel_tolerance`` (暗黙 default 禁止)。

    出力 schema (``8b-combined-verdict/v2``): conditions 3 条件 + holdouts per-pair 詳細
    (各 holdout に ``scale`` 状態 + 解決済み binding + pair floor) + ``protocol_violations``。
    oracle / floor_by_holdout の構造破綻は再検証せず fail-closed に判定不能へ倒す。
    """
    if not isinstance(prediction, VerifiedPrediction):
        raise VerdictError(
            "judge_combined は VerifiedPrediction のみ受理する (未検証 object は渡せない)")
    if type(oracle) is not _artifacts.OfficialVerdict:
        raise VerdictError(
            "judge_combined は OfficialVerdict exact type のみ受理する")
    tolerance = _tolerance_fraction(scale_tolerance)
    if tolerance is None or tolerance < 0:
        raise VerdictError(
            "scale_tolerance が非負の有限値でない (protocol 由来値を明示引数で渡す。暗黙 default 禁止)")

    document = prediction.document
    pred_index, pred_reasons = _prediction_index(document)
    expectations, exp_reasons = _swapped_expectations(document)
    oracle_holdouts, oracle_reasons = _oracle_holdouts(oracle)
    expected_domain, holdout_reasons = _expected_holdout_set(expected_holdouts)
    structural_reasons = pred_reasons + exp_reasons + oracle_reasons + holdout_reasons

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
    oracle_manifest_sha256 = (oracle.get("manifest_sha256")
                              if isinstance(oracle, Mapping) else None)
    oracle_status = oracle.get("status") if isinstance(oracle, Mapping) else None

    targets = expected_domain

    per_holdout: dict[str, dict] = {}
    pred_diff_verdicts: list[str] = []
    follow_verdicts: list[str] = []
    floor_verdicts: list[str] = []
    coupled_verdicts: list[str] = []
    floors_used: dict[str, Optional[float]] = {}
    scale_states: dict[str, str] = {}
    protocol_violations: list[dict] = []

    for target in targets:
        on_choice = pred_index.get((target, "on"))
        off_choice = pred_index.get((target, "off"))
        swapped_choice = pred_index.get((target, "swapped"))
        expected_choice = expectations.get(target)
        oracle_holdout = oracle_holdouts.get(target)
        floor_entry = (floor_by_holdout.get(target)
                       if isinstance(floor_by_holdout, Mapping) else None)
        scale_ref = floor_entry.get("scale_ref") if isinstance(floor_entry, Mapping) else None

        diff = _pred_diff(on_choice, off_choice)
        follow = _swapped_follow(swapped_choice, expected_choice)

        projected = project_pair_floor(
            floor_by_holdout, CHOICE_TO_BINDING, target, on_choice, off_choice)
        for violation in projected.violations:
            protocol_violations.append({**violation, "holdout": target})

        scale_state, observed_stock = _scale_state(oracle_holdout, scale_ref, tolerance)
        scale_states[target] = scale_state

        if projected.resolution == _PROJECT_REFUTED:
            # on == off の短絡 (差 0)。floor も oracle median も参照しないため scale gate 対象外。
            exceeded = REFUTED
            floor_used: Optional[float] = None
        elif projected.resolution == _PROJECT_INDETERMINATE:
            exceeded = INDETERMINATE
            floor_used = None
        else:  # _PROJECT_QUERY
            floor_used = projected.floor
            if scale_state != SCALE_ADEQUATE:
                # scale inadequate / stock 非 eligible / scale_ref null → 条件 3 のみ判定不能。
                exceeded = INDETERMINATE
            else:
                exceeded = _floor_exceeded(
                    oracle_holdout, projected.on_binding_key,
                    projected.off_binding_key, floor_used)
        floors_used[target] = floor_used
        coupled = _conjunction([diff, exceeded])  # 同一 holdout 束縛 (裁定 5 項 3)

        pred_diff_verdicts.append(diff)
        follow_verdicts.append(follow)
        floor_verdicts.append(exceeded)
        coupled_verdicts.append(coupled)

        per_holdout[target] = {
            "on_choice_id": on_choice,
            "off_choice_id": off_choice,
            "swapped_choice_id": swapped_choice,
            "expected_swapped_choice_id": expected_choice,
            "on_binding_key": projected.on_binding_key,
            "off_binding_key": projected.off_binding_key,
            "on_off_prediction_difference": diff,
            "swapped_follow": follow,
            "oracle_floor_exceeded": exceeded,
            "same_holdout_coupled": coupled,
            "oracle_verdict": (oracle_holdout.get("verdict")
                               if isinstance(oracle_holdout, Mapping) else None),
            "floor": floor_used,
            "scale": {
                "state": scale_state,
                "scale_ref": scale_ref,
                "observed_stock_median": observed_stock,
            },
        }

    structural_indeterminate = bool(structural_reasons) or not targets

    if structural_indeterminate:
        condition1 = INDETERMINATE
        condition2 = INDETERMINATE
        condition3 = INDETERMINATE
        coupled_existential = INDETERMINATE
    else:
        condition1 = _existential(pred_diff_verdicts)
        condition2 = _conjunction(follow_verdicts)
        condition3 = _existential(floor_verdicts)
        coupled_existential = _existential(coupled_verdicts)

    conclusion = _conjunction([coupled_existential, condition2])

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
        "oracle_floor_exceeded": {
            "verdict": condition3,
            "evidence": {
                "prediction_body_sha256": prediction_body_sha256,
                "oracle_manifest_sha256": oracle_manifest_sha256,
                "oracle_status": oracle_status,
                "floors": dict(floors_used),
                "scale_states": dict(scale_states),
                "scale_tolerance": str(scale_tolerance),
            },
        },
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "status": conclusion,
        "same_holdout_coupled_verdict": coupled_existential,
        "conditions": conditions,
        "holdouts": per_holdout,
        "protocol_violations": _sorted_reasons(protocol_violations),
        "evidence": {
            "prediction_body_sha256": prediction_body_sha256,
            "selector_basis_sha256": selector_basis_sha256,
            "oracle_manifest_sha256": oracle_manifest_sha256,
            "oracle_status": oracle_status,
            "scale_tolerance": str(scale_tolerance),
        },
        "reasons": _sorted_reasons(structural_reasons),
    }


# ---------------------------------------------------------------------------
# CLI (C2-7): floors/holdouts 外部入力を廃止し検証済み freeze から導出
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


def _resolve_scale_tolerance(freeze_document: Mapping, *, root: Path) -> object:
    """freeze.floor_protocol が指す protocol document から scale tolerance を取得する。

    protocol document を hash 検証つきで読み、``scale_adequacy_rel_tolerance`` を返す
    (十進文字列を想定。厳密 Fraction 化のため str のまま渡す)。暗黙 default は持たない。
    """
    floor_protocol = freeze_document.get("floor_protocol")
    if (not isinstance(floor_protocol, Mapping)
            or not isinstance(floor_protocol.get("path"), str)
            or not isinstance(floor_protocol.get("sha256"), str)):
        raise VerdictError("freeze.floor_protocol が {path, sha256} でない")
    protocol_rel = floor_protocol["path"]
    protocol_path = Path(protocol_rel)
    if not protocol_path.is_absolute():
        protocol_path = Path(root) / protocol_path
    verified = load_verified_freeze(protocol_path, floor_protocol["sha256"])
    tolerance = verified.document.get("scale_adequacy_rel_tolerance")
    if _tolerance_fraction(tolerance) is None:
        raise VerdictError(
            f"protocol の scale_adequacy_rel_tolerance が不正: {tolerance!r}")
    return tolerance


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    judge = sub.add_parser(
        "judge",
        help=("prediction × oracle × 検証済み freeze を結合判定する。"
              "floor 表・holdout 集合・scale tolerance は freeze (+ floor_protocol) から"
              "導出する — 外部 --floors/--holdouts 入力は廃止した (C2-7)。"))
    judge.add_argument("--prediction", type=Path, required=True,
                       help="prediction freeze 文書 (verify_prediction で全検証する)")
    judge.add_argument("--oracle", type=Path, required=True,
                       help="judge_oracle 出力 (8b-oracle-verdict/v1)")
    judge.add_argument("--freeze", type=Path, required=True,
                       help="検証済み holdout freeze (v2 per-pair floor)。sha256 一致を強制する")
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
        freeze_document = verified_freeze.document
        holdout_ids = _holdout_ids(freeze_document)
        # per-pair floor / budget を manifest と同等の validator で strict 検査する (二重定義回避)。
        _validate_execution_snapshot(freeze_document, holdout_ids=holdout_ids)
        floor_by_holdout = freeze_document["floor"]["by_holdout"]
        scale_tolerance = _resolve_scale_tolerance(freeze_document, root=args.root)

        prediction_document = _load_json_object(args.prediction)
        verified_prediction = verify_prediction(
            prediction_document, freeze=freeze_document, root=args.root)
        oracle = _artifacts.load_official_verdict(args.oracle)

        verdict = judge_combined(
            prediction=verified_prediction, oracle=oracle,
            floor_by_holdout=floor_by_holdout, expected_holdouts=set(holdout_ids),
            scale_tolerance=scale_tolerance)
        _write_create_only(args.out, verdict)
    except (OSError, json.JSONDecodeError, TypeError, ValueError,
            VerdictError, _artifacts.OracleArtifactTypeError,
            FreezeIOError, ManifestError, SelectorFreezeError,
            SelectorInputError, DescriptorError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
