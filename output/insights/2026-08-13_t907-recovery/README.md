# 2026-08-13 dev-wave t907-recovery — 受入 receipt の非帰属受理と log hash 束縛

裁定待ちで停止していた受入 integrity wave ([T-907] / [T-908] / [T-910]) の取り残し branch を
回収し、2026-08-13 第 9 束の裁定 3 件を反映して land した wave の一次資料。

- 回収元 branch: `worktree-dev-wave-t907-t908-t910-acceptance-integrity` tip `44b4a9ba` (7 commit)
- 本 wave branch: `worktree-dev-wave-t907-recovery`
- 前 wave の一次資料: `output/insights/` には無い (前 wave は land しなかった)。
  段 1〜4 の成果物は job directory
  `/work/1/SFC/tanab/dev-wave-jobs/2026-08-13_t907-t908-t910-acceptance-integrity/` にある。

## 反映した裁定

| # | 内容 |
|---|---|
| #1 | 批准既知赤 registry は作らず、receipt 条件を「rc=0 または非帰属 checker 緑」へ拡張 |
| #9 | [T-1019] 待ち手の receipt へ log hash 束縛 (checker 自身の走行所有は不採用) |
| #10 | [T-1020] 新規機構は作らず本 wave の land で閉じる |

## 中身

- `verbatim/s4-adjudication-delta.md` — 親の段 4 差分裁定 (erratum 込み)。
  §1 に、裁定文の「非帰属 checker 緑」を機械語へ落とす際の唯一の分岐点をコード実測で示す。
- `verbatim/s5-author.md` — 段 5 実装子の報告 (codex `gpt-5.6-sol` / effort high)。
- `verbatim/s6-revA.md` — 敵対レビュー A (受理集合)。blocker 1 + nit 2。
- `verbatim/s6-revB.md` — 敵対レビュー B (全層 scope・実効性)。NO-GO、blocker 3 + must-fix 5。
- `verbatim/s6-fix1.md` / `s6-fix2.md` — fix 2 巡分の対応表。
- `spec-r3.json` / `result-r3.json` — 変異 matrix の確定 spec と生台帳。

## 変異 matrix (確定走、anchor は fix 後の統合 tip)

**baseline PASSED、7/7 KILLED、SURVIVED 0 / TIMEOUT 0。** うち 6 件は期待完全集合と exact 一致。

| ID | 壊した gate | 層 | 結果 |
|---|---|---|---|
| N1 | checker の `status` 検査 + 赤 nodeid 非空検査 | both-layers | KILLED (1 node) |
| N2 | checker rc≠0 の fail-closed | negative | KILLED (5 node、期待 6 との差はフレーク) |
| N3 | checker receipt の `log_sha256` 照合 | negative | KILLED (1 node) |
| N4 | 非帰属経路へ入る条件 `child_rc == 1` | negative | KILLED (9 node) |
| N5 | land の `checker_blob_sha` 照合 | negative | KILLED (1 node) |
| N6 | land の `child-green` × `child_rc == 0` 整合 | negative | KILLED (2 node) |
| N7 | land の `non-attributable-only` × `child_rc == 1` 整合 | negative | KILLED (7 node) |

N1 を both-layers にしたのは、`status` 検査だけを壊しても
「赤 nodeid が 1 件以上ある」という二層目が受理を止めるためである (`DW-M04` の事前登録)。
実装子が最初に提案した単層変異は登録前のコード確認で mask を検出したので採らなかった。

登録を見送った変異が 1 件ある。待ち手 receipt の invariant
(`child_rc != 1 or red_check is None or not red_check.red_nodeids`) は、
同じ入力を拒否する層が前後にあり赤理由が一つに絞れないため、`DW-M01` / F28 に従い
登録せず実効 gate へ再照準した。

## フレークの実測 (帰属させなかった赤)

変異走行間で `test_dev_wave_wait.py` の signal handler 復元テストが揺れた。

- 2 巡目: `test_signal_after_core_success_uses_restored_real_handler` が
  **`tools/dev_wave_land.py` だけを変異させた N5 の失敗集合に出現**。
- 3 巡目: `test_public_main_failure_restores_handler_without_release` が N2 の集合から消失。

land のみの変異が待ち手の signal テストを落とすことは依存関係上ありえないので、
変異へ帰属させずフレークとして扱い、期待完全集合から除外した。

## 焦点走 (計算ノード、2026-08-13 09:17 JST)

- `orchestrator/tests/test_dev_wave_wait.py` = **179 passed / 0 failed**
- `orchestrator/tests/test_dev_wave_land.py` = **143 passed / 1 failed**
  唯一の赤は `test_exploration_external_root_keeps_wave_clean` = 既知事象 [T-892]
  (2026-08-12 起票。`conftest.py` の autouse fixture が campaign の遅延 import に効かず、
  部分集合走を計算ノードで回すと必ず落ちる。受入全走では落ちない)。本差分と無関係。

本 wave が新設した `test_real_non_attributable_waiter_receipt_passes_real_land_end_to_end` は
**緑**。合成の既知赤を作り、実 waiter → 実 checker → 実 land を通す唯一の経路である。

## 実データ検証の限界 (「実データで 1 回通した」とは書かない)

非帰属経路を**実受入データ**で通すには [T-1027] (`check_acceptance_reds.py` が実 log で rc=2 の
まま実運用に到達していない) の land が要る。本 wave の end-to-end 試験は実 checker を
**合成 log** へ当てたものであり、実受入 log での検証は未達である。
