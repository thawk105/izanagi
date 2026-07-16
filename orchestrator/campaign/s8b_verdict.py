# -*- coding: utf-8 -*-
"""8b §6 判定表: prediction × oracle を結合する I/O 非依存な三値判定。

裁定 5 (output/insights/2026-07-16_s8b-ruling-package.md) が逐語凍結した
truth table を機械判定する純関数を提供する。

- 条件 1 (on/off 予測差): on の予測 choice が off の予測 choice と異なる holdout が存在する
  (存在量化)。floor は使わない。
- 条件 2 (swapped 追従): swapped の予測が swap 元への on 予測へ family ID 一致で追従する。
  両 holdout 必須 (全称量化)。全称の領域は prediction に現れた holdout ではなく、呼び手が渡す
  凍結 holdout 集合 (``expected_holdouts``) そのものである (裁定 5 項 1)。凍結集合の一部しか
  含まない prediction は「n=2 で実質 1 標本」の主張になるため判定不能へ倒す。
- 条件 3 (oracle floor 超): on 予測構成と off 予測構成の oracle 実測差が方向付きで当該 holdout の
  floor を超える (``oracle(on) − oracle(off) > floor_<holdout>``)。floor を使うのはこの条件のみ。
- 結論: 条件 2 と、「同一 holdout で 予測差 かつ floor 超」の存在量化の連言。条件 1 と条件 3 は
  結論において同一 holdout に束縛される (裁定 5 項 3)。

三値伝播はすべて fail-closed である。selector 出力の欠測・不正 (choice_id=null)、oracle の
exact tie (oracle 非一意)、excluded 観測を含む holdout、floor 未確定はいずれも当該条件を判定不能へ
倒し、§6 結論行へ伝播する。REFUTED (不成立) は関連データが完全なときにのみ返す。rationale は
成立判定に一切使わない (診断材料に限定。裁定 5 項 5)。

floor 数値は §8 再凍結 + ユーザー承認事項であり、本モジュールは値を持たず呼び手から受け取る。
未凍結・不正な floor は判定不能へ倒す (fail-closed の骨格)。
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections.abc import Collection, Mapping, Sequence
from pathlib import Path
from typing import Optional


SCHEMA_VERSION = "8b-combined-verdict/v1"
PREDICTION_SCHEMA = "8b-selector-prediction-freeze/v1"
ORACLE_SCHEMA = "8b-oracle-verdict/v1"

# 三値: 成立 / 不成立 / 判定不能。
HOLDS = "holds"
REFUTED = "refuted"
INDETERMINATE = "indeterminate"

_ARMS = ("on", "off", "swapped")


def _reason(code: str, message: str) -> dict:
    return {"code": code, "message": message}


def _sorted_reasons(reasons: Sequence[Mapping]) -> list[dict]:
    return sorted((dict(reason) for reason in reasons),
                  key=lambda reason: (str(reason.get("code")), str(reason.get("message"))))


def _is_real(value: object) -> bool:
    """bool を除く有限な実数のみ真。"""
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(float(value)))


def _existential(verdicts: Sequence[str]) -> str:
    """存在量化 (OR)。成立が優先、次に判定不能、全て不成立でのみ不成立。

    verdicts が空なら判定不能 (量化対象が無い = 検証不能)。
    """
    if not verdicts:
        return INDETERMINATE
    if any(verdict == HOLDS for verdict in verdicts):
        return HOLDS
    if any(verdict == INDETERMINATE for verdict in verdicts):
        return INDETERMINATE
    return REFUTED


def _conjunction(verdicts: Sequence[str]) -> str:
    """全称量化 / 連言 (AND)。全て成立でのみ成立、判定不能が不成立に優先する。

    不成立は全項が確定 (判定不能を含まない) で少なくとも 1 項が不成立のときのみ返す。
    verdicts が空なら判定不能。
    """
    if not verdicts:
        return INDETERMINATE
    if all(verdict == HOLDS for verdict in verdicts):
        return HOLDS
    if any(verdict == INDETERMINATE for verdict in verdicts):
        return INDETERMINATE
    return REFUTED


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

    swapped 追従 (§6 第 2 条件) は両 holdout 必須の全称量化であり、その領域は prediction に
    現れた holdout ではなく凍結集合そのものでなければならない。prediction 側から領域を採ると、
    片側 holdout だけを含む prediction で全称が実質 1 標本へ退化し「n=2 で実質 1 標本」の主張を
    素通ししてしまう。非集合・Mapping・str/bytes・空・非文字列要素・重複はいずれも判定不能へ
    倒す (fail-closed)。
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


def _floor_value(floors: Mapping, holdout: str) -> Optional[float]:
    """呼び手が渡す floor を検証する。非有限・非正・欠測は None (判定不能扱い)。"""
    if not isinstance(floors, Mapping):
        return None
    value = floors.get(holdout)
    if not _is_real(value) or float(value) <= 0.0:
        return None
    return float(value)


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


def _eligible_median(oracle_holdout: Mapping, choice: object) -> Optional[float]:
    """oracle holdout の当該 configuration が eligible なら有限 median を返す。"""
    if not isinstance(choice, str) or not choice:
        return None
    configurations = oracle_holdout.get("configurations")
    if not isinstance(configurations, Mapping):
        return None
    cell = configurations.get(choice)
    if not isinstance(cell, Mapping) or cell.get("status") != "eligible":
        return None
    median = cell.get("median_of_medians")
    return float(median) if _is_real(median) else None


def _floor_exceeded(oracle_holdout: object, on_choice: object,
                    off_choice: object, floor: Optional[float]) -> str:
    """条件 3 の holdout 単位判定: oracle(on) − oracle(off) > floor か (方向付き)。

    floor 未確定、oracle 判定不能、oracle exact tie (oracle 非一意)、予測欠測、
    構成の oracle 非 eligible はいずれも判定不能へ倒す。winner は使わず、あくまで
    on/off 予測構成の median 差を評価する (同一 holdout 束縛の要)。
    """
    if floor is None:
        return INDETERMINATE
    if not isinstance(oracle_holdout, Mapping):
        return INDETERMINATE
    verdict = oracle_holdout.get("verdict")
    if verdict == "tie":  # exact tie = oracle 非一意 (裁定 5 項 4)
        return INDETERMINATE
    if verdict != "unique-best":  # indeterminate / 未知値は fail-closed
        return INDETERMINATE
    if on_choice is None or off_choice is None:
        return INDETERMINATE
    on_median = _eligible_median(oracle_holdout, on_choice)
    off_median = _eligible_median(oracle_holdout, off_choice)
    if on_median is None or off_median is None:
        return INDETERMINATE
    return HOLDS if (on_median - off_median) > floor else REFUTED


def judge_combined(*, prediction: Mapping, oracle: Mapping,
                   floors: Mapping, expected_holdouts: object) -> dict:
    """prediction freeze・oracle verdict・floor から §6 の 3 条件と結論を判定する。

    ``prediction`` は検証済み prediction freeze 文書
    (``8b-selector-prediction-freeze/v1``)、``oracle`` は ``judge_oracle`` の出力
    (``8b-oracle-verdict/v1``)、``floors`` は holdout ID → floor 値の Mapping、
    ``expected_holdouts`` は凍結 holdout ID 集合 (裁定 5 項 1 の全称量化の領域) である。
    いずれも本関数は再検証せず構造だけを fail-closed に扱う。

    全称・存在量化の領域は ``expected_holdouts`` に固定する。prediction が凍結集合の一部しか
    含まない (片側 holdout 欠落) 場合や凍結集合外の holdout を含む場合は、構造破綻として全条件を
    判定不能へ倒す。凍結集合を prediction から採らないことで「n=2 で実質 1 標本」の主張を
    素通ししない (裁定 5 項 1)。
    """
    pred_index, pred_reasons = _prediction_index(prediction)
    expectations, exp_reasons = _swapped_expectations(prediction)
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

    prediction_body_sha256 = (prediction.get("body_sha256")
                              if isinstance(prediction, Mapping) else None)
    selector_basis_sha256 = (prediction.get("selector_basis_sha256")
                             if isinstance(prediction, Mapping) else None)
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

    for target in targets:
        on_choice = pred_index.get((target, "on"))
        off_choice = pred_index.get((target, "off"))
        swapped_choice = pred_index.get((target, "swapped"))
        expected_choice = expectations.get(target)
        oracle_holdout = oracle_holdouts.get(target)
        floor = _floor_value(floors, target)
        floors_used[target] = floor

        diff = _pred_diff(on_choice, off_choice)
        follow = _swapped_follow(swapped_choice, expected_choice)
        exceeded = _floor_exceeded(oracle_holdout, on_choice, off_choice, floor)
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
            "on_off_prediction_difference": diff,
            "swapped_follow": follow,
            "oracle_floor_exceeded": exceeded,
            "same_holdout_coupled": coupled,
            "oracle_verdict": (oracle_holdout.get("verdict")
                               if isinstance(oracle_holdout, Mapping) else None),
            "floor": floor,
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
                "derangement": (dict(prediction.get("derangement"))
                                if isinstance(prediction, Mapping)
                                and isinstance(prediction.get("derangement"), Mapping)
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
            },
        },
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "status": conclusion,
        "same_holdout_coupled_verdict": coupled_existential,
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


def _load_json_array(path: Path) -> list:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        parse_constant=lambda token: (_ for _ in ()).throw(
            ValueError(f"non-finite JSON constant: {token}")),
    )
    if not isinstance(value, list):
        raise ValueError(f"JSON top-level が array でない: {path}")
    return value


def _write_create_only(path: Path, value: Mapping) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    judge = sub.add_parser("judge", help="prediction × oracle × floor を結合判定する")
    judge.add_argument("--prediction", type=Path, required=True)
    judge.add_argument("--oracle", type=Path, required=True)
    judge.add_argument("--floors", type=Path, required=True,
                       help="holdout ID → floor 値の JSON object (§8 再凍結値)")
    judge.add_argument("--holdouts", type=Path, required=True,
                       help="凍結 holdout ID の JSON array (裁定 5 項 1 の全称量化の領域)")
    judge.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        prediction = _load_json_object(args.prediction)
        oracle = _load_json_object(args.oracle)
        floors = _load_json_object(args.floors)
        expected_holdouts = _load_json_array(args.holdouts)
        verdict = judge_combined(prediction=prediction, oracle=oracle, floors=floors,
                                 expected_holdouts=expected_holdouts)
        _write_create_only(args.out, verdict)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
