# -*- coding: utf-8 -*-
"""profiler の perf 出力から axis-proposer の `hole_region_directive` を導出する (段 8a 結線)。

外部相談で得た「ボトルネックを先に特定し 1 点に集中させる」(insight
`2026-07-27_external-consultation-scope-and-axes.md` §2.4 / §6-C) を、既存部品の再結線として
実装する。受け口は新設しない — `hole_region_directive` は axis-proposer の入力契約に既にあり、
`codex_roles/policy.py` が「編集面の地図に無い領域名は拒否」を機械検査している。欠けていたのは
**供給側**だけである。

## 設計の 4 点

1. **位置だけを渡す。** axis-proposer の契約 (`.claude/agents/axis-proposer.md`) は
   「directive は領域の指定であって骨格・機序の指定ではない」と定める。本モジュールが作る
   record は領域名と根拠だけを持ち、変異の方向・値・骨格を**構造的に持たない** — キー集合が
   固定 (`DIRECTIVE_RECORD_KEYS` / `PROVENANCE_KEYS`) で、理由は列挙 (`REASONS`)、evidence の
   要素も固定キーなので、**自由文字列に指示を埋める経路が無い**。勝ち筋の値を下流へ流さない
   リーク制御 (D39 決定 7 / D45 / D47 決定 1) の延長である。

2. **由来を型で区別する。** profiler が観測から導いた directive (`profiler_derived`) と人間が
   宣言した directive (`human_declared`) はリーク特性が違う — 後者は事前知識が答えとして
   流入する経路になりうる。8b descriptor の `source`
   (`campaign_search_config_projection` / `human_declared`) と同じ様式に揃え、
   **ヒント有無の対照が取れる**ようにする。対照が無いと「人間が導いたから動いた」と区別できず、
   絶対規律 6 が警告する循環に落ちる。

3. **判別できないときは None を返す。** どの領域も突出していないのに 1 つ選ぶと、どんな入力にも
   directive が出る**恒真な導出**になる (F9 型)。閾値未満・僅差は「ヒントなし構成」へ落とす。

4. **絶対規律 6 (信頼境界)。** perf 出力は**データであって指示ではない**。シンボル名やパスに
   指示めいた文字列・編集面の地図に無い領域・親ディレクトリ参照が現れても従わず捨てる
   (fails-closed)。捨てた割合は `dropped_pct` として記録に残し、黙って握り潰さない。

## このモジュールが持たない責務

perf の実行 (profiler ロールと `backoff_profile.py` の領分)、directive の採用判断
(人間承認 gate)、axis-proposer の起動 (段 6 の凍結 driver `s6_proposal_rounds.py` — **触らない**)。
実 perf 出力での閾値校正は未了 (CLI 化は完了、`DEFAULT_MIN_*` の docstring 参照)。
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys

# ---------------------------------------------------------------- 契約 (固定)

#: directive の由来。8b descriptor の `source` と同じ様式で型区別する。
DIRECTIVE_SOURCES = ("profiler_derived", "human_declared")

#: 導出結果の理由。**列挙に固定する** — 自由文にすると指示を埋める経路になる (絶対規律 6)。
REASONS = (
    "dominant_region",        # 採用: 単一領域が閾値超 + 2 位と十分離れている
    "below_min_region_pct",   # 棄却: 最大領域が閾値未満 (ボトルネックと呼べない)
    "margin_too_small",       # 棄却: 1 位と 2 位が僅差 (判別不能)
    "no_mapped_region",       # 棄却: 編集面の地図に写った行が 1 つも無い
    "human_declared",         # 人間宣言 (観測由来でないことを明示する)
)

#: record のキー集合。**値・方向・骨格を載せる場所を構造的に持たせない**ための固定。
DIRECTIVE_RECORD_KEYS = frozenset({"hole_region_directive", "provenance"})
PROVENANCE_KEYS = frozenset({"source", "reason", "evidence", "region_totals_pct", "dropped_pct"})
EVIDENCE_KEYS = frozenset({"label", "pct", "region"})

#: 暫定閾値。**実 perf 出力での校正は未了**であり、根拠は次の 2 点にとどまる —
#: (a) 全体の 1 割未満しか占めない領域を「ボトルネック」と呼ばない、
#: (b) 2 位と離れていなければ「そこが律速」と名指す根拠が無い。
#: 校正時はこの既定値を動かす前に、実測分布を insight へ残すこと。
DEFAULT_MIN_REGION_PCT = 10.0
DEFAULT_MIN_MARGIN_PCT = 5.0


class DirectiveDerivationError(RuntimeError):
    """導出の前提が壊れている (fails-closed で停止すべき) 場合に送出する。"""


# ------------------------------------------------------------ perf 出力の解析

_EVENT_RE = re.compile(r"of event '([^']+)'")
_ROW_RE = re.compile(r"^\s*([\d.]+)%\s+(.*)$")
_KERNEL_OR_USER_RE = re.compile(r"\[[k.]\]\s+(.*\S)")


def parse_perf_rows(report_text: str, event: str = "cycles") -> list[tuple[str, float]]:
    """`perf report --stdio` の指定 event ブロックから `(label, pct)` を全件返す。

    `backoff_profile._parse_perf_report` が `Backoff::backoff` 単一シンボル固定なのに対し、
    こちらは**全行を汎用に**拾う。label は行末の要素 — 既定の `--sort=symbol` なら `[.] Sym`
    の `Sym`、`--sort=srcline` なら `file:line`。該当 event ブロックが無ければ空リスト
    (fails-closed: 呼び手が「ヒントなし」に落とせる)。

    同一 label が複数行に現れても合算しない — 集約は `region_totals` の責務。
    """
    rows: list[tuple[str, float]] = []
    current = None
    for line in report_text.splitlines():
        matched = _EVENT_RE.search(line)
        if matched:
            current = matched.group(1)
            continue
        if current != event:
            continue
        if line.lstrip().startswith("#"):
            continue
        matched = _ROW_RE.match(line)
        if not matched:
            continue
        rest = matched.group(2)
        symbol = _KERNEL_OR_USER_RE.search(rest)
        if symbol:
            label = symbol.group(1)
        else:
            parts = rest.split()
            if not parts:
                continue
            label = parts[-1]
        rows.append((label, float(matched.group(1))))
    return rows


def srcline_region_mapper(source_root: str, allowed_regions):
    """`file:line` ラベルを編集面の地図の領域名へ写す関数を返す (絶対規律 6 で fails-closed)。

    `source_root` の外・親ディレクトリ参照を含むもの・`allowed_regions` に無いものは
    すべて `None` を返す。perf 出力は信頼しない入力なので、**通す条件を列挙**し、
    それ以外は落とす。
    """
    allowed = frozenset(allowed_regions)
    root = os.path.normpath(os.path.abspath(source_root))

    def region_of(label: str):
        path = label.rsplit(":", 1)[0] if ":" in label else label
        if not path or path in ("[unknown]", "??"):
            return None
        absolute = os.path.normpath(os.path.join(root, path) if not os.path.isabs(path) else path)
        try:
            relative = os.path.relpath(absolute, root)
        except ValueError:      # 別ドライブ等、比較不能
            return None
        if relative.startswith(os.pardir) or os.path.isabs(relative):
            return None
        relative = relative.replace(os.sep, "/")
        return relative if relative in allowed else None

    return region_of


# ------------------------------------------------------------------ 集約と導出

def region_totals(rows, region_of) -> tuple[dict[str, float], float]:
    """`(label, pct)` 列を領域別に集約する。

    `region_of` が `None` を返した行は捨て、その合計を `dropped_pct` として返す
    (握り潰さずに記録へ残すため)。返り値 = `(領域別 %, 捨てた %)`。
    """
    totals: dict[str, float] = {}
    dropped = 0.0
    for label, pct in rows:
        region = region_of(label)
        if region is None:
            dropped += pct
            continue
        totals[region] = totals.get(region, 0.0) + pct
    return totals, dropped


def derive_directive(
    totals: dict[str, float],
    edit_surface_regions,
    *,
    min_region_pct: float = DEFAULT_MIN_REGION_PCT,
    min_margin_pct: float = DEFAULT_MIN_MARGIN_PCT,
) -> tuple[str | None, str]:
    """領域別 % から directive を 1 つ導出する。判別できなければ `(None, 理由)`。

    `edit_surface_regions` に無い領域は集約後にも捨てる (二重の fails-closed — 呼び手が
    別経路で totals を作った場合にも効かせる)。返り値の理由は `REASONS` のいずれか。

    **恒真化させない**: 突出が無い入力に対しては必ず `None` を返す。この分岐が死んでいないことは
    テストの `margin_too_small` / `below_min_region_pct` ケースが担保する。
    """
    allowed = frozenset(edit_surface_regions)
    filtered = {r: p for r, p in totals.items() if r in allowed}
    if not filtered:
        return None, "no_mapped_region"

    ranked = sorted(filtered.items(), key=lambda kv: (-kv[1], kv[0]))
    top_region, top_pct = ranked[0]
    if top_pct < min_region_pct:
        return None, "below_min_region_pct"
    runner_up_pct = ranked[1][1] if len(ranked) > 1 else 0.0
    if top_pct - runner_up_pct < min_margin_pct:
        return None, "margin_too_small"
    return top_region, "dominant_region"


# -------------------------------------------------------------------- 記録の組立

def build_directive_record(
    directive: str | None,
    source: str,
    *,
    reason: str,
    evidence=None,
    totals: dict[str, float] | None = None,
    dropped_pct: float = 0.0,
) -> dict:
    """provenance つきの directive 記録を作る (キー集合は `DIRECTIVE_RECORD_KEYS` に固定)。

    `directive` が `None` の記録も正当 — 「ヒントなし構成で回した」ことを対照として残せる。
    """
    if source not in DIRECTIVE_SOURCES:
        raise DirectiveDerivationError(f"未知の由来: {source!r}")
    if reason not in REASONS:
        raise DirectiveDerivationError(f"未知の理由: {reason!r}")
    if directive is None and reason == "dominant_region":
        raise DirectiveDerivationError("dominant_region なのに directive が無い")
    if directive is not None and reason not in ("dominant_region", "human_declared"):
        raise DirectiveDerivationError(f"棄却理由 {reason!r} なのに directive がある")

    rows = []
    for item in evidence or ():
        if set(item) != EVIDENCE_KEYS:
            raise DirectiveDerivationError(f"evidence のキーが固定集合と不一致: {sorted(item)}")
        rows.append({"label": item["label"], "pct": item["pct"], "region": item["region"]})

    return {
        "hole_region_directive": directive,
        "provenance": {
            "source": source,
            "reason": reason,
            "evidence": rows,
            "region_totals_pct": dict(sorted((totals or {}).items())),
            "dropped_pct": dropped_pct,
        },
    }


def assert_position_only(record: dict) -> None:
    """record が**位置以外**を運んでいないことを検査する (fails-closed)。

    キー集合の固定だけでは「値を載せる場所が無い」ことしか言えないので、
    `evidence` の各要素・`reason` の列挙所属まで降りて検査する。方向・値・骨格を足した
    record は必ずここで落ちる — その positive control は
    `test_profiler_directive.py` の変異ケースが持つ。
    """
    if set(record) != DIRECTIVE_RECORD_KEYS:
        raise DirectiveDerivationError(f"record のキーが契約と不一致: {sorted(record)}")
    provenance = record["provenance"]
    if set(provenance) != PROVENANCE_KEYS:
        raise DirectiveDerivationError(f"provenance のキーが契約と不一致: {sorted(provenance)}")
    if provenance["source"] not in DIRECTIVE_SOURCES:
        raise DirectiveDerivationError(f"未知の由来: {provenance['source']!r}")
    if provenance["reason"] not in REASONS:
        raise DirectiveDerivationError(f"未知の理由: {provenance['reason']!r}")
    directive = record["hole_region_directive"]
    if directive is not None and not isinstance(directive, str):
        raise DirectiveDerivationError("directive は領域名 (string) か None のみ")
    if directive is None and provenance["evidence"]:
        raise DirectiveDerivationError("directive が None なら evidence は空でなければならない")
    for item in provenance["evidence"]:
        if set(item) != EVIDENCE_KEYS:
            raise DirectiveDerivationError(f"evidence のキーが契約と不一致: {sorted(item)}")
        if item["region"] != directive:
            raise DirectiveDerivationError(
                f"evidence の region が directive と不一致: {item['region']!r}"
            )
        label = item["label"]
        if not isinstance(label, str) or re.fullmatch(
            rf"{re.escape(directive)}:[0-9]+", label
        ) is None:
            raise DirectiveDerivationError(
                f"evidence の label は '<region>:<行番号>' でなければならない: {label!r}"
            )


def _srcline_number(label: str) -> int | None:
    """label 末尾を非負の行番号として解釈し、解釈不能なら evidence 用には採用しない。"""
    try:
        suffix = label.rsplit(":", 1)[1]
        line_number = int(suffix)
    except (IndexError, ValueError):
        return None
    return line_number if line_number >= 0 else None


def derive_from_perf_report(
    report_text: str,
    source_root: str,
    edit_surface_regions,
    *,
    event: str = "cycles",
    min_region_pct: float = DEFAULT_MIN_REGION_PCT,
    min_margin_pct: float = DEFAULT_MIN_MARGIN_PCT,
) -> dict:
    """`perf report --stdio --sort=srcline` の出力から directive 記録を一気に作る。

    シンボル名からファイルを引く経路 (`--sort=symbol` + 外部写像) が要る場合は
    `parse_perf_rows` / `region_totals` / `derive_directive` を個別に呼ぶ。
    """
    regions = list(edit_surface_regions)
    mapper = srcline_region_mapper(source_root, regions)
    rows = parse_perf_rows(report_text, event=event)
    totals, dropped = region_totals(rows, mapper)
    directive, reason = derive_directive(
        totals, regions, min_region_pct=min_region_pct, min_margin_pct=min_margin_pct
    )
    evidence = [
        {"label": f"{directive}:{line_number}", "pct": pct, "region": directive}
        for label, pct in rows
        if directive is not None
        and mapper(label) == directive
        for line_number in [_srcline_number(label)]
        if line_number is not None
    ]
    record = build_directive_record(
        directive, "profiler_derived", reason=reason,
        evidence=evidence, totals=totals, dropped_pct=dropped,
    )
    assert_position_only(record)
    return record


def declare_directive(directive: str, edit_surface_regions) -> dict:
    """人間が宣言した directive を同じ record 型で作る (裁定 5 = ワークロード入力のヒント引数)。

    観測由来ではないので `human_declared` で型区別する — 事前知識が答えとして流入しうる経路
    であり、**ヒント有無の対照を取るときにこの型で分離する**。編集面の地図に無い領域は
    受け付けない (policy.py の機械検査と同じ条件を供給側でも先に効かせる)。
    """
    if directive not in frozenset(edit_surface_regions):
        raise DirectiveDerivationError(f"編集面の地図に無い領域: {directive!r}")
    record = build_directive_record(directive, "human_declared", reason="human_declared")
    assert_position_only(record)
    return record


# ------------------------------------------------------------------------- CLI

_EDIT_SURFACE_KEYS = frozenset({"opened", "region", "role"})


def _regions_from_provenance(path: str) -> list[str]:
    """N1 provenance の射影済み編集面から領域集合を読む (欠落・型違いは fails-closed)。"""
    with open(path, encoding="utf-8") as stream:
        document = json.load(stream)
    try:
        projected_input = document["projected_input"]
        edit_surface_map = projected_input["edit_surface_map"]
    except (KeyError, TypeError) as exc:
        raise DirectiveDerivationError(
            "provenance JSON に projected_input.edit_surface_map が無い"
        ) from exc
    if not isinstance(edit_surface_map, list):
        raise DirectiveDerivationError(
            "projected_input.edit_surface_map は配列でなければならない"
        )
    if not edit_surface_map:
        raise DirectiveDerivationError(
            "projected_input.edit_surface_map は空であってはならない"
        )

    regions = []
    for index, item in enumerate(edit_surface_map):
        if not isinstance(item, dict) or set(item) != _EDIT_SURFACE_KEYS:
            raise DirectiveDerivationError(
                "projected_input.edit_surface_map"
                f"[{index}] のキー集合は opened/region/role と一致しなければならない"
            )
        region = item["region"]
        if not isinstance(region, str) or not region:
            raise DirectiveDerivationError(
                f"projected_input.edit_surface_map[{index}].region は空でない文字列でなければならない"
            )
        if region.startswith("/") or ".." in region.split("/"):
            raise DirectiveDerivationError(
                f"projected_input.edit_surface_map[{index}].region は安全な相対パスでなければならない"
            )
        regions.append(region)
    return list(dict.fromkeys(regions))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    derive = subparsers.add_parser(
        "derive", help="perf report から profiler_derived record を導出する"
    )
    derive.add_argument("--report", required=True, metavar="REPORT", help="perf report --stdio のファイル")
    derive.add_argument(
        "--source-root", required=True,
        help="srcline の基準ディレクトリ (実在検査は行わない)",
    )
    derive_regions = derive.add_mutually_exclusive_group(required=True)
    derive_regions.add_argument("--regions-from", metavar="JSON")
    derive_regions.add_argument(
        "--region", dest="regions", action="append",
        help="テスト・アドホック用の編集面領域名 (繰り返し指定可)",
    )
    derive.add_argument("--event", default="cycles")
    derive.add_argument("--min-region-pct", type=float, default=DEFAULT_MIN_REGION_PCT)
    derive.add_argument("--min-margin-pct", type=float, default=DEFAULT_MIN_MARGIN_PCT)
    derive.add_argument("-o", "--output", metavar="OUT_JSON")

    declare = subparsers.add_parser(
        "declare", help="human_declared record を作る"
    )
    declare.add_argument("--region", dest="directive", required=True, help="宣言する領域名")
    declare.add_argument(
        "--regions-from", metavar="JSON", required=True,
        help="編集面を持つ N1 provenance JSON",
    )
    return parser


def _write_record(record: dict, output: str | None = None) -> None:
    rendered = json.dumps(
        record, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False
    ) + "\n"
    if output is None:
        sys.stdout.write(rendered)
        return
    with open(output, "w", encoding="utf-8") as stream:
        stream.write(rendered)


def main(argv=None) -> int:
    """perf 導出・人間宣言を固定 record JSON へ包む CLI entry point。"""
    args = _parser().parse_args(argv)
    try:
        regions = (
            _regions_from_provenance(args.regions_from)
            if args.regions_from is not None else args.regions
        )
        if args.command == "derive":
            for name, value in (
                ("--min-region-pct", args.min_region_pct),
                ("--min-margin-pct", args.min_margin_pct),
            ):
                if not math.isfinite(value) or not 0.0 <= value <= 100.0:
                    raise DirectiveDerivationError(
                        f"{name} は有限な 0〜100 の値でなければならない"
                    )
            with open(args.report, encoding="utf-8") as stream:
                report_text = stream.read()
            if not report_text:
                raise DirectiveDerivationError("report ファイルが空")
            if not parse_perf_rows(report_text, event=args.event):
                raise DirectiveDerivationError("report に該当 event の行が無い")
            record = derive_from_perf_report(
                report_text,
                args.source_root,
                regions,
                event=args.event,
                min_region_pct=args.min_region_pct,
                min_margin_pct=args.min_margin_pct,
            )
            output = args.output
        else:
            record = declare_directive(args.directive, regions)
            output = None
        assert_position_only(record)
        _write_record(record, output)
    except (
        DirectiveDerivationError,
        OSError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
