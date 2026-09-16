# 実アンカー表 — [T-1642] 射程文言の統一

repo root = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1642-trace0-scope-wording`
(行番号は 2026-09-16 に同 worktree の現物で実測。基準 9d52ef145)

## A 群 — live (直す候補)

| # | path:line | 現状 | 射程注記 | 統一で主張の強さが変わるか |
|---|---|---|---|---|
| A1 | `tools/check_trace0_preprocess_identity.py:3` (module docstring) | 「選定した macro context における TRACE=0 正規化 preprocess 出力の同一性、および include 活性の同一性を検査する。」 | なし | 変わらない。現状も完全除去は主張していない。注記は読み手の外挿を塞ぐ **弱める方向** の追加 |
| A2 | 同 `:38-41` `GUARANTEE` 定数 | D297 が定めた保証名の逐語 | — | **変更しない**。値を変えると report / receipt / job-result の bytes と test の literal 複製が動く |
| A3 | 同 `:62-63` `class CheckError` docstring | 「…を確認できない。」 | なし | 変わらない |
| A4 | 同 `:421-424` `_mocc_trace_include_addition_index` docstring | 「D297 still requires the normalized TRACE=0 preprocess output to match below …」 | 部分 (例外の局所性のみ) | 変わらない |
| A5 | 同 `:539-541` コメント | 「D297 の保証（…）は以下で従来どおり比較する」 | なし | 変わらない |
| A6 | `tools/pegasus/mocc_trace_pilot.sh:1742-1743` | 「D297 checker is deliberately a hard gate.  Its nonzero result means that TRACE=0 execution is skipped; no fallback or relaxed branch is permitted.」 | なし | **弱まる**。「hard gate」だけだと、通れば規律 1 が満たされたと読める。射程注記を足すと「必要条件の一つを満たした」に落ちる。ここが本 wave で唯一、主張の強さが実際に下がるアンカー |

## B 群 — 既に D780 準拠 (変更不要)

| # | path:line | 現状 |
|---|---|---|
| B1 | `output/insights/2026-08-25_t1677-trace0-remeasure.md:95-96` | D780 決定 1 の統一文言そのもの。「完全除去を証明したと読んではならない」まで書いてある |
| B2 | `output/insights/2026-08-25_t1584-trace0-identity-holes.md:136-141, 163-164` | 「この checker は『trace の完全除去』を証明しない …規律 1 の必要条件の一つであって十分条件ではない」。逐語は違うが趣旨一致。D780 の起点 (R2) そのもの |
| B3 | `output/insights/2026-08-25_t1641-report-binding.md:19-24, 105` | guarantee の転記が保証の付与ではないこと、interpreter path が provenance を閉じないことを明記済み |

## C 群 — 歴史記録・裁定の正本 (遡及改変しない)

`docs/decisions.md` (D297:13750 付近, D774, D780:30019 付近)、`docs/failures.md:19795`、
`docs/spool/FOLDED.md`、`docs/archive/worklog-phase3-*.md`、
`output/insights/2026-08-27/ccbench-pin-precheck/{README.md,measurements-2.md}`、
`output/insights/2026-08-2{2,3,4}_*.md` (D780 以前の pilot 記録)

## 不在の実測 (純増の根拠)

- `docs/pegasus-runbook.md` に TRACE=0 / D297 / checker の記述は 0 件 (grep)。
- D780 以前の trace0 insight 3 本 (`2026-08-22_t755-…`, `2026-08-23_t1506-…`,
  `2026-08-24_t1582-…`) に「この検査が完全除去を証明した」と読める記述は 0 件。
  `2026-08-24_t1582-mocc-trace0-pilot.md:27` は逆に「trace artifact を性能値の正しさ証明へ
  読み替えない」と書いている。
- 「必要条件の一つ / 十分条件ではない」の既出は B1・B2 の 2 箇所のみ (archive 除く全 repo 走査)。

## 凍結 pin の実測 (DW-O09)

- `orchestrator/tests/test_check_trace0_preprocess_identity.py:24-27` に `_GUARANTEE` の literal 複製、
  `:230` で `report["guarantee"] == _GUARANTEE`、`:229` で schema `izanagi-trace0-preprocess-identity/v2`。
- `tools/pegasus/mocc_trace_pilot.sh:2878-2880` が report の guarantee を非空 string として検査し、
  `:2905-2911` で receipt の `trace0_preprocess_identity_report` へ転写、`:3358-3364` で
  job-result 側が `{path, sha256, schema, guarantee}` の 4 field 厳密一致を要求する。
- したがって A2 (GUARANTEE 定数) を動かすと 4 箇所が連動する。本 wave は動かさない。
