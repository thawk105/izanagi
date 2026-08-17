# 段 1 brief — [T-338] RF validator 発火条件と pilot 解禁条件の組み直し

wave = `dev-wave-t338-rf-trigger-realign` / branch = `worktree-dev-wave-t338-rf-trigger-realign`
worktree = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign` (HEAD = local main `699c9cae`)

## scope

canonical decision を 1 本書き、`docs/spool/decisions/` の fragment として land する。あわせて
worklog fragment で [T-339] を [T-338] へ戻す。**それ以外は何も変えない。**

## 確定済みユーザー裁定 (2026-08-16 /rulings 全件、D1 + D2 → B)

- **D1**: D162 決定 (10) の発火条件 (ii) から `attestation` を落とす。**環境タグは落とさない**
  (D320 が「測定の公正 (環境契約タグ)」を対象外=不変と明記)。
- **D2**: pilot 投入の解禁条件から公表層実装を切り離す。
- **B**: `producer → pilot → validator/consumer` を 1 scope へ戻す ([T-339] を [T-338] へ)。
- 択 C (validator を pilot より先) は不採用確定。

## 起動時の実測 (一次資料から。既存 docs の要約を根拠にしない)

| # | 事実 | 実アンカー |
|---|---|---|
| M1 | pilot を止めている条文の実体 = `addendum_p_freeze_precondition` の末文「pilot もそれまで投入しない」 | `docs/decisions.md` D291 の `operational_state_on_fold` 節 |
| M2 | D291 の同節は sha256 で byte 固定。かつ payload は **固定 commit の blob** から読む | `orchestrator/publication/approval_d291.py` `_EXACT_SECTION_SHA256["operational_state_on_fold"]`, `D291_DECISIONS_REF` |
| M3 | D162 を機械参照する consumer は **0 件** | `grep -rn "D162" --include=*.py orchestrator/ tools/` = 0 |
| M4 | `attestation_mode: "required"` は環境契約 (受理集合) 側であり D162 発火条件とは別物 | `orchestrator/qualification/contract.py:156` |
| M5 | HEAD の `docs/decisions.md` を読む live consumer は 1 つだけ。supersession scan は既に `possible_supersession` (`D292,D305,D313,D316`) | `orchestrator/publication/report.py` `_scan_d291_supersession` |
| M6 | その scan の ID 列は exact pin されていない (membership + sorted のみ) | `orchestrator/tests/test_t793_report.py:41-45` |
| M7 | 解禁権威は canonical decision のみ。解禁条件の中身は D292 では未定義 | `docs/decisions.md` D292 |
| M8 | 着手順序 `producer → pilot → validator/consumer` は D229 決定 (6)。pilot 自身を (i)(ii) の充足計測にする設計 | `docs/decisions.md` D229 決定 (6) |
| M9 | `docs/decisions.md` は check_docs の予算対象外 (追記型凍結台帳) | `tools/check_docs.py:44` |

## 不変条件 (破ったら停止)

1. **D291 の bytes を 1 byte も変えない。** 前向き失効 (D282 / D322 と同型) だけを使う。
2. **受理集合を緩めない (規律 2)。** `orchestrator/qualification/contract.py` の
   `env_tag` / `attestation_mode` は触らない。verifier / admission / 変異検査も触らない。
3. **本 decision は解禁ではない。** `pilot_submission` は `forbidden` のまま。
   `report.py` の top-level literal は変えない (deny-only の fail-closed 表明)。
4. 実装差分ゼロ。コード・テスト・schema・凍結 artifact・certified 選択・材料レポート・
   proof chain は 1 byte も動かさない。

## provisional 裁定 (親のもの。攻撃対象)

- **(P1)** D2 の射程は「`addendum_p_freeze_precondition` の末文だけを前向きに失効させる」であり、
  追補 P の凍結条件そのもの (公表台帳の実体確定) は不変。
- **(P2)** D1 は「発火条件 (ii) を 4 項 → 3 項 (環境タグ・測定 checkout・pin) に前向き改訂」で足り、
  D162 本文の編集も、機械側の変更も不要。
- **(P3)** 本 wave の実装差分はゼロであり、段 5 / 段 6 の実装子は起動しない (`4→7→8→9`)。
- **(P4)** B の履行は worklog fragment 上での task scope の統合であり、
  [T-339] を「完了」とは書かず [T-338] へ統合したと書く (二重在籍を作らない)。
- **(P5)** 解禁後に残る実質条件は (a) RF producer と attempt registry の実体、
  (b) pilot の記録項目確定 (D229 決定 (6) の単独 gate)、(c) 環境契約下での実走 — の 3 点である。

## 成果物の形

- `docs/spool/decisions/2026-08-17-dev-wave-t338-rf-trigger-realign-1.md` (D placeholder 1 本)
- `docs/spool/worklog/2026-08-17-dev-wave-t338-rf-trigger-realign-1.md`
- `output/insights/2026-08-17_t338-rf-trigger-realign/` (README + verbatim)

## 並列分割方針

段 2 = codex plan 1 本。段 3 = 敵対 2 レンズ (A: 正しさ境界と規律 2 / B: 整合と実効性)。
段 5 / 6 は実装差分ゼロのため起動しない (段 4 で確定)。受入全走は免除しない。

## 環境

実測・受入とも Pegasus。テストは `python3 tools/run_tests.py` を repo root から。
