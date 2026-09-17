# 段 1 brief — [T-2293][T-2687][T-2688][T-2692] D2104 項 3 / 21 / 22 / 30 の追記・手順改訂 (2026-09-17 21:37 JST)

## 研究前進

土台の整備。裁定済み 4 項 (D2104 項 3 / 21 / 22 / 30) の追記・手順改訂で、決定台帳・運用 doc の記述を
実装の現物に合わせる。完了判定 = 4 項の追記が canonical へ fold され、`check_docs.py` と受入全走が緑で land。
止めている研究: T-2293 Q2〜Q4 の保留条件 (D1875) の前提が古いままだと、8c 多世代運転の再開判断が誤った
予算 (1) を前提にする。本 wave は前提の訂正だけを行い、保留は解かない。

## scope (本題の 4 追記だけ)

| # | T | 裁定 | 編集対象 (実アンカー) | 種別 |
|---|---|---|---|---|
| (a) | T-2293 | D2104 項 3 | `docs/spool/decisions/` fragment: 新 D「D1875 の『承認済み generation 予算 1』を D410 (2026-08-15) の 2 と訂正し、Q2〜Q4 の保留は維持」。対象逐語 = D1875 決定文「D114 が定めた承認済み generation 予算 1」(decisions.md `## D1875.` 節)。実装 `orchestrator/campaign/p3_autonomous_workload_trial.py:145` `MAX_APPROVED_GENERATIONS = 2`、D410 背景「D114 の承認上限 1 を 2 へ上げる」を現物で確認済み | docs (fragment) |
| (b) | T-2687 | D2104 項 21 | `docs/spool/decisions/` fragment: 新 D「D922 点 4 の打ち切りを `indeterminate` へ倒す対象は負判定に限る」。対象逐語 = D922 点 4「探索の打ち切り・timeout・上限超過・… はすべて `indeterminate` に倒す」。実装 `tools/check_branch_landed.py:784` (`# Positive proof is checked before a candidate-limit truncation is reported.`) を現物で確認済み。実装は変えない | docs (fragment) |
| (c) | T-2688 | D2104 項 22 | `docs/unreachable-object-ledger.md` rc 表 (`| \`2\` | timeout、上限超過、…技術的に不完全 |` 行) へ「landed 判定に `indeterminate` を含む場合も rc=2」を追記。実装 `tools/check_branch_rescue.py` (`complete = expected_conclusive = verdict != "indeterminate"` → `technical_incomplete` → `return 2`) を現物で確認済み。この doc は check_docs の pin 対象外 (grep 0 件) | docs (直接編集) |
| (d) | T-2692 | D2104 項 30 | `docs/dev-wave/operations.md` `## DW-O18` から hold 登録の一般手順 3 文を取り下げ、「hold 登録簿へ登録しない (契約 test が 1 件に固定、F1000)。真に決定的な不安定 test は 1 件ごとに pin 更新を裁定送り」へ (997 → 971 bytes、案文は job dir `dw-o18-new.md`)。**DW-O18 は `tools/check_docs.py:605` `DEV_WAVE_DW_O18_SECTION_LITERAL` に逐語 pin され、`orchestrator/tests/test_check_docs.py:166` `_SYNTHETIC_DW_O18_SECTION` と変異 needle M2 (`:9582`) / M11 (`:9639`) が旧文言に依存する。** docs 編集は親、`.py` 2 file の追随は Codex author | docs (親) + 実装面 (Codex author) |

scope 外: Q2〜Q4 の着手、実装 (`check_branch_landed.py` / `check_branch_rescue.py` / `flaky_test_holds.py`) の変更、
新しい gate・検査・台帳、F1000 の書き換え (supersede 追記 1 行の要否は段 4 で決める)。

## 確定済みユーザー裁定

D2104 (2026-09-17、「推奨通りで」) 項 3 / 21 / 22 / 30。逐語は `d2104.md` (job dir) と decisions.md `## D2104.` 節。
「決定台帳への追記は直接編集せず fragment」「規律 2 を緩めない」「本題の 4 追記だけ」は command 引数。

## 不変条件

- canonical 3 台帳は fold だけが書く (既存 bytes 不変)。既存 D の訂正は追補 D として新規 fragment (先例 D2049・D1694)。
- 実装面 (`tools/check_docs.py`、`orchestrator/tests/test_check_docs.py`) は親が編集しない (D95)。
- DW-O18 の見出し文字列は変えない (見出しは check_docs・test の多数箇所で pin)。「同一tipで各1回だけ」は維持 (D2104 項 30)。
- 規律 2: verifier / 正しさゲートに触れない。DW-O18 の改訂は既存防壁 (F1000 の契約 test) を強める向きのみ。
- push・remote 操作なし。land は段 9 の共通 operation。

## (P1) 親の provisional 裁定・攻撃対象

- (P1-1) (d) の新文言は hold 登録手順の取り下げとして十分か。「hold登録簿へ登録しない」+「1件ごとにpin更新を裁定送り」で
  F1000 の防壁 (wave が自分を緑にするために除外集合を広げない) と整合し、かつ再投入の回数制限 (同一tipで各1回) を残す。
- (P1-2) 実装面の差分は文字列定数と test fixture/needle の追随だけであり、変異 matrix は `check_docs.py` の literal に対する
  最小構成 (M0 等価 + 負例 2〜3) で足りる (先例 t2445 wave、`run_tests.py orchestrator/tests/test_check_docs.py`)。
- (P1-3) (c) の追記は rc 表 `2` 行の末尾へ 1 句 (表の行数を変えない)。
- (P1-4) 軽量版: 段 2 プランは省略 (本 brief が file:line を持つ)、段 3 consult 1 本、段 5 author 1 本、段 6 review 1 本 + fix。

## 成果物

- fragments: `docs/spool/decisions/2026-09-17-dev-wave-t2293-d2104-docs-addenda-1.md` (D 2 本)、
  `docs/spool/worklog/2026-09-17-dev-wave-t2293-d2104-docs-addenda-1.md`
  (T-2293 更新 / T-2687・T-2688・T-2692 完了)、failures supersede は段 4 で決める。
- `docs/unreachable-object-ledger.md`、`docs/dev-wave/operations.md`、`tools/check_docs.py`、`orchestrator/tests/test_check_docs.py`。
- insight `output/insights/2026-09-17/t2293-d2104-docs-addenda/README.md` + `verbatim/`。

## 分割方針

実装子 1 本 (所有: `tools/check_docs.py` の DW-O18 literal、`orchestrator/tests/test_check_docs.py` の合成 fixture と M2/M11 needle)。
親は docs 4 箇所と fragment。受入環境: 受入全走は `tools/dev_wave_wait.py acceptance` (計算ノード dispatch)、
焦点走は login node (`test_check_docs.py` + consumer)、変異は container worktree + dispatch。

## 編集面重複

稼働 wave `worktree-dev-wave-t2293-origin-producer` (7ecf1ed66) は `p3_autonomous_workload_trial.py` とその test だけを触り、
本 wave の対象 3 file は分岐点 f5423e2ff の blob と一致 (未 commit 編集なし)。重複 0。
