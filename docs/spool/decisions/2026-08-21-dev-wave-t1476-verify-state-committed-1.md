---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: dev-wave-t1476-verify-state-committed
seq: 1
---

## {{D:verify-done-attempt-binding-scope}}. official report の verify_done 読み取りに committed attempt 束縛を追加し、scope は verify のみに限定する

**決定:** `orchestrator/campaign/s8b_oracle_report.py` の `_verify_state` に
`expected_attempt_id` (既定 `None`) を追加し、呼び出し元 `_assess_window` が window の
唯一の `build_start` から `build_attempt_id` を読んで渡す。候補の verify_done record が
一意でも `build_attempt_id` が `expected_attempt_id` と不一致なら certified 判定前に
`missing` + issue とする。`expected_attempt_id is None` (build_start に ID 欠落、または
`build_start` が0件/複数件の異常 window) では新検査を完全に skip し、legacy WAL の
既存挙動を変えない。`build_done`/`bench_done`/`abort`/`commit` payload の同型の
attempt_id 不問は本 wave では手当てせず、次task候補として残す。

**理由:**
- 段2 codex plan (reasoning=max) が具体的な反例 (stale attempt の legacy verify_done が
  committed attempt の s2 verify_done と共存し、report が stale 側を採用してしまう) を
  構成し、段3 敵対相談2レンズ (sol=正しさ境界, luna=整合・実効性・scope) が独立に成立を
  確認した。
- 起票文 (本 wave の originating command 引数) が `_verify_state` 周辺への scope 限定と、
  digest.py 等の別 consumer へ scope を広げないことを明示していた。
- sol が `build_done`/`bench_done`/`abort`/`commit` にも同型の脆弱性があると追加指摘したが、
  luna も含め「production diff は verify-only で段階導入として妥当、広い保証を掲げるなら
  scope 拡大が要る」という一致した判断だった。CLAUDE.md 規律5 (段階導入・盛らない) に従い、
  最小 diff を選んだ。
- legacy 互換: T-567 (`6130a1b9`) の follow-up fix (`55d6c019`) が
  「`build_attempt_id is None` の場合は新規厳格検証を skip して continue する」という
  後方互換パターンを既に確立していた。本決定はこの前例を踏襲する。ID を先に filter して
  候補を減らす実装は、診断シグナルを失い「正しい1件だけが残った」ように見えてしまうため
  採用しなかった (段2 plan・段3 sol が指摘)。

**却下した選択肢:**
- `digest.py` の `EvalState.committed_verify`/`wal.replay_admitted_records()` へ移行する案
  — s8b は `_trial_windows()` による schedule-level window 走査で `wal.replay()`/`EvalState`
  を経由しない独立実装であり、`digest.load_verify_abort_signals()` も admitted
  `CampaignView` 前提で raw window API と形状が異なる。non-committed outcome
  (correctness-red 等) の証拠を単純に committed projection へ落とすと失われるため、
  局所 anchor 方式 (window の `build_start` から `expected_attempt_id` を導出) を採用した。
- ID 不一致の候補を certified 判定前に filter で除外する実装 — 一意性検査の母数を
  減らしてから判定すると、除外された事実が issue に残らず診断力を失う。count-first
  (既存の `len(matches)!=1`) → ID 一致検査 (一意な候補が1件のときだけ) の順を維持した。
