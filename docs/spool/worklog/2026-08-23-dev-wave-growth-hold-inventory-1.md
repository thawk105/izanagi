---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-growth-hold-inventory
seq: 1
title: 成長比例保留 16 件を棚卸しし 14 件を既定走行へ戻した。判定は秒数でなく承認済み例外の成立で行った (コード+テスト、branch worktree-dev-wave-growth-hold-inventory、変異matrix = 2件ともKILLED・SURVIVED 0)
---

## 本文

ユーザーが直接起票した棚卸しである。対象は `orchestrator/tests/growth_test_holds.py` の
`_HOLD_ROWS` のうち `test_codex_reasoning_ab.py` の 16 件。裁定は再導入 14 / 削除 0 / 保留継続 2。

**引数が挙げた前提 2 件はいずれも実測で否定された。** 「snapshot corpus の不在」は成り立たず、
corpus は実在した。セッション開始時 5,482 file / 5.13 GiB で、約 50 分後には 5,505 file に
増えていた。増えた分は本 wave 自身が起動した codex 子が書いた rollout である。
16 件は opt-in 実走で 20 items 全 PASS (544.05 秒)。登録 reason の本文も「不在」ではなく
成長比例コストであり、引数の前提は変数名 `_ROLLOUT_REASON` からの推測だった。

裁定を決めたのは秒数ではなく 2 つの構造的矛盾である。詳細は
{{D:growth-hold-release-by-approved-exception}}。

1. `benchmark_snapshots` は module scope で、既定で走る consumer が 4 本残っていた。
   よって fixture は既定走行で必ず構築されており (setup 実測 15.32 秒)、14 件の保留は
   corpus 列挙費を 1 秒も節約していなかった。
2. `test_codex_reasoning_ab.py` の module docstring が変異期待 node の正本なのに、
   そこで名指しされた node の 7 件が保留中だった。M1 / M2 / M3 は既定で走る期待 node が
   1 件も無く、変異が必ず SURVIVED になる状態だった。変更後は保留されたままの期待 node がゼロ。

**親 brief の予算前提が誤っていた。** 「全走 5 分が絶対上限」と書いたが、権威元は D312 で
「受入全走 5 分などの数値目標は達成目標であって合否判定ではない」「設計択一を閾値の跨ぎで
決めない」である。段 3 の敵対レンズが権威元の欠落を指摘し、親が D312 を引いて是正した。
この誤りのまま進めば、171.83 秒の replay node を「遅いから保留継続」と裁定していた。

段 3 の敵対 2 レンズは親の provisional 裁定を 3 点是正した。(a) 保留は fixture 費を
節約しないが body 費は節約している、(b) `pinned_label` を渡しても `rglob` は残るので
D463 上は依然比例、(c) `F(t)` は body でなく node 単位で取る。いずれも採用した。

**比例源の除去** は当初案 (`pinned_label="POS"` を渡す) を捨てた。`rglob` が残り比例性が
消えないうえ、fast path を外れると沈黙して全走査経路へ戻り、遅くなるだけで緑のまま通るためである。
採ったのは固定定数 `_REAL_ROLLOUT` の直接参照と SHA 検証で、`F(t)` が固定 path になり
D463 の非比例へ移った。実測は 3 param 合計 250.68 秒から 2.28 秒。

**親の pin 閉包監査に漏れがあった。** 識別子 grep で 3 箇所を挙げて閉包を取ったと判断したが、
`test_hold_inventory.py` が期待表を literal で複製しており grep に掛からなかった。
段 5 の実装子が発見し、親の焦点走が赤 2 件として顕在化させた
({{F:literal-expectation-table-escapes-identifier-grep}})。

焦点走で本 wave と無関係な赤を 1 件踏んだ。原因はセッション環境の `FORCE_COLOR=3` で、
同変数を外すと緑になる。並行セッションは同じ赤を差分ゼロの main 作業ツリーで再現して
「repo 側の決定的な赤」と周知したが、差分を消しても環境は継承されるため証明になっていなかった
({{F:zero-diff-worktree-does-not-clear-inherited-env}})。修理前 main への受入全走の実測は
14,310 passed / 96 skipped / 赤 0 件で、受入では最初から発火していない。

背景 job の完了通知が producer の完了より先に届く事象も踏んだ
({{F:background-completion-notice-precedes-producer-exit}})。

保留を継続する 2 行の reason には、実測日・両成長軸の実測・当該 node の call 秒・
生き残る既定走行の防壁 node・`IZANAGI_HOLD_REEVAL_V1` sentinel を書いた。sentinel の
`advisory` には評価主体が存在しない事実を明記した ({{D:machine-readable-hold-reeval-is-record-not-gate}})。

変異 matrix は 2 件とも期待どおり KILLED で、失敗 node は期待集合と完全一致した。
baseline は PASSED (365 passed / 2 skipped / 402.76 秒)、SURVIVED と MISMATCH は 0。
MUT-1 は 2 経路の一致比較を返り値が同一のまま消す変異で、殺したのは
`test_m2_production_golden_requires_both_routes` 1 本。MUT-2 は期待 session 行の構築を
actual と一致させる変異で、grep 対象の文字列を変えないため静的 node が mask せず、
殺したのは `test_verify_replays_complete_fake_codex_experiment` 1 本。
両 node とも変更前は既定 skip なので、旧側では同じ変異が SURVIVED する。

**本走は `--runner-mode local` で行った。** DW-M07 は dispatch を既定とするが、その理由は
runner の実行経路を変異させると runner が自壊し収集段が rc=16 になることである。
本 wave の変異対象は `tools/codex_reasoning_ab.py` で runner の実行経路ではないため
この失敗モードに当たらず、baseline PASSED と期待 node 完全一致で結果は有効である。

**段 8 の自己改善は候補 5 件すべてを裁定項目へ送った。** 統合を試みた 2 件
(焦点走の consumer 拡張へ literal 複製 consumer を足す / 変異走行中は repo へ書かない) は、
節単位では収まった (DW-O26 688 byte、DW-M05 976 byte、いずれも上限 1000 以内) が、
**L1.5 層の集約が 9,776 / 9,566 byte で 210 byte 超過**した。DW-O26 には exact 契約の pin もあり
文面変更自体が抵触する。自己改善契約が「予算のために安全義務を削除・弱化してはならない」
「予算値を上げる変更は理由付きの独立審査対象にする」と定めるため、追加は巻き戻した。
残る 3 件のうち 2 件は DW-O18 が 1000/1000 byte で余裕ゼロ、1 件は候補と重複があるため見送った。
事象と根本原因は failures 台帳側に残る。

エージェント工数は codex 子 8 本 (plan 1 / consult 2 / author 1 / review 2 / fix 1 / 段 8 fix 1)、
いずれも `gpt-5.6-sol` / `xhigh`。author 子は wall 566.5 秒 / model call 27。
author 子と fix 子はいずれも Pegasus dispatch 障害で pytest を実走できず、
「実装済み・未実走」「partial」と正しく申告した。実走はすべて親が行った。

## 次の一手差分

### 新規

- {{T:hold-reeval-token-evaluator}} **P2・新規**: 保留行の `IZANAGI_HOLD_REEVAL_V1` を
  評価する既定走行の主体を作るか裁定する。`_validate_hold_rows` を拡張して
  `barrier_nodes` が保留集合に入っていないことを検査すれば、既存の import 時 enforcement 点を
  使って非恒真にできる。gate 新設にあたるため本 wave では実装していない。
- {{T:mutation-expected-node-hold-consistency-check}} **P2・新規**: 変異期待 node の正本と
  保留 registry の整合を機械検査する。本 wave では 7 件の矛盾が人手の読みでしか
  見つからなかった。
- {{T:unpinned-rollout-scan-guard}} **P2・新規**: `_find_rollout` の pin 無し全走査に
  上限か警告を設けるか裁定する。production も pin 無しで呼ぶ経路を持ち、corpus が
  伸び続ける以上いずれ production 側でも顕在化する。
- {{T:dev-wave-l1-5-budget-exhausted}} **P1・ユーザー裁定待ち**: dev-wave reference の
  L1.5 層が満杯で自己改善が入らない。本 wave は実測に基づく候補 5 件を起こしたが、
  1 件も統合できなかった。集約は 9,776 / 9,566 byte で 210 byte 超過、
  DW-O18 は 1000 / 1000 byte で余裕ゼロ、DW-O26 には exact 契約の pin がある。
  予算値を上げるか、L1.5 の既存節を L2 へ移すか、自己改善の routing 先を変えるかを諮る。
- {{T:focus-run-env-and-completion-discipline}} **P2・新規**: 予算が空いた時点で、
  親の焦点走を `FORCE_COLOR` / `COLORTERM` を外して走らせる義務と、親の実走も
  終端マーカーと終了 rc で判定し背景 job の完了通知を完了判定に使わない義務を
  DW-O18 へ統合する。実測と根本原因は failures 台帳側に記録済み。
