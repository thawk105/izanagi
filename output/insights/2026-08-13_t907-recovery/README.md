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

## 変異 matrix (確定走 = `spec-r5.json` / `result-r5.json`、anchor は fix 後の最終 commit)

**baseline PASSED、7/7 KILLED、MISMATCH 0 / SURVIVED 0 / TIMEOUT 0 — 全件が期待完全集合と exact 一致。**

`spec-r3.json` / `result-r3.json` は午前の走行 (6/7 exact、N2 のみフレーク 1 件分の差) で、
経緯として残す。確定は r5 である。r5 では signal handler フレーク族 4 件を
**走行対象と期待集合の両方から**外した (この族はどの変異とも因果が無く、
1 回目の再走ではこの族が baseline を赤にして harness が正しく fail-closed した)。

以下の表は r3 時点の内訳で、gate と変異の対応は r5 でも同じである。

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

## 午後の続き — ユーザー裁定と checker 強化への追随

ユーザー裁定「**既知の赤で main へ land できない状態は許さない**」を受けて続行した。

その最中に [T-1027] の wave が `tools/check_acceptance_reds.py` を強化して land した
(3 commit・+559 行)。うち `67a46f10` は「打ち切られた collect 出力を権威にせず、
判定不能から非帰属を出さない」で、**親が受入 3 回で実測した collect timeout の欠陥を、
より良い形 (collect 出力に pytest の集計行があることを要求する) で塞いでいた。**

本 wave はその契約へ 3 段階で追随した (いずれも計算ノードで 1 つずつ実測)。

| 実測時刻 | 観測した拒否 | 追随 |
|---|---|---|
| 11:33 受入全走 | `pytest collection footer is missing or non-unique` | 合成 runner の collect 出力へ集計行 |
| 11:53 焦点走 | `single-node rerun rc=1 lacks matching FAILED/ERROR outcome` | 単独再走の出力へ summary と `FAILED` 行 |
| 12:04 焦点走 | 待ち手の receipt field 集合 exact 一致で拒否 | checker receipt に増えた `collections` を検査対象へ |

**受理集合は一切広げていない。** field 集合を exact 一致で見る設計 (checker の schema 変化を
機械で検知する防壁) も維持しており、「未知 key を無視する」形にはしていない。

## 到達点と、残る 1 点

**12:14 JST の焦点走で `test_real_non_attributable_waiter_receipt_passes_real_land_end_to_end` が緑。**
合成の既知赤に対し、**強化後の実 checker** が `non-attributable-only` を返し、
実 waiter が receipt を発行し、実 land がそれを受理する経路が通った。
すなわち「既知の赤があっても land できる」は実物で成立している。

残るのは **実受入で赤が出たときの非帰属受理を 1 度観測すること**だけである
(本 wave の受入が緑で終われば、その経路は通らない)。end-to-end 試験は実 checker を
**合成 log** へ当てたものであり、実受入 log での発火は別の機会を要する。
