# 段 4 裁定 — [T-2279] 変異 harness 経由の D612 queue-wait 上書き

判定日: 2026-09-09。入力: 段 2 プラン (s2-plan.md)、段 3 レンズ A (s3-lensA.md)、レンズ B (s3-lensB.md)、
親の段 1 実測 (spec 407 file 走査)。段 4 直前に local main を再確認 (b57e35426。対象コード file の変更なし、
docs/failures.md に別 wave の 49 行追加のみ)。

## R1. 904 秒の層 — real、採用

2026-09-03 の約 904 秒は、当時の collection が `dispatch_compute.py` を上書きなしで直接起動し、
既定 queue-wait 900 秒で `queue-wait-timeout` になったことで説明できる
(`229e030a:tools/mutation_harness.py:1408-1418`、`tools/pegasus/dispatch_compute.py:68-71,3951-3965`)。
当時の外側 watchdog は 5400 秒で、この時刻を作らない。両レンズが独立に同じ結論。
**特定は完了した。** ただし経過秒数だけでは断定できず、断定には receipt の
`reason=queue-wait-timeout` が要る (レンズ A 所見 9)。当時の記録 (F762) はその reason を
記録しているので、特定は一次資料に支持される。

## R2. 今日の HEAD に「上書きが届かない経路」は 0 件 — real、採用

collection (1e22c4cbd で転送済み)、baseline、通常 mutation、hang mutation、`--resume` の pending
mutation、fan-out 経由、wrapper 経由、restore、provenance、直接焦点走のいずれでも D612 の 2 変数は
落ちない。根拠は s2-plan.md Q1/Q2 と s3-lensB.md 所見 3・4・5 の file:line。
**したがって「特定できた分の修理」は、伝播については残っていない。** 本 wave はコードを変更しない。

## R3. 親 brief の誤り 4 件 — real、訂正する

1. 「watchdog の timeout が mutant の TIMEOUT として台帳へ帰属する」は誤り。dispatch mode の
   `timed_out` は status 算出より前に `_dispatch_orphan_stop` が `OrphanHoldStop` へ変換し、
   mutation record は書かれず rc=2 で全走が止まる (`tools/mutation_harness.py:327-390,2259-2269,3304-3313`)。
   実害は台帳の誤りではなく **走行の完了不能**。
2. fresh baseline と fresh non-hang mutation を欠陥に含めたのは過大。collection gate が同じ
   `spec.timeout_seconds` を先に検査している。
3. F762 の「collection / 本走がともに dispatcher 直呼び」は本走について誤り。当時も本走は
   `run_tests.py` を実行していた。
4. 「1800+300 = 待ち 2100 秒」という説明は dispatcher の締切構造と違う。queue 判定は Q 単独、
   G は RUN 観測後の期限にだけ加わる (`dispatch_compute.py:3891-3946,3951-3965`)。

## R4. 段 2 プランの新 gate — 不採用

レンズ B 所見 8 (real) とレンズ A 所見 5 (real)、レンズ B 所見 6 (real) を採用する。理由は 3 つ。

- **主題外。** 伝播は R2 のとおり既に成立しており、この gate は上書きの到達も混雑下の走行可能性も
  増やさない。
- **式が dispatcher を表していない。** `outer < Q + G` は queue 判定 (Q 単独) と RUN 後判定
  (walltime + G) を混同している。G が大きいだけの設定を過剰拒否し、G=0 の等号は取りこぼす。
  したがって `timeout_s == Q+G` は実 dispatch の安全性の正例ではない。
- **受理集合を縮める。** 現在は混雑が軽ければ完走しうる hang_risk 変異を、起動前に rc=2 で
  拒否するようになる。ユーザーが明示した scope 外 (gate の追加) にも当たる。

## R5. 新規に特定した real な欠陥 — 実装せず裁定パッケージへ

**欠陥:** harness の外側 watchdog (`spec.timeout_seconds` / `hang_timeout_seconds`) と、dispatcher の
締切構造 (queue は Q 単独、RUN 後は walltime + G、cleanup は別予算 90 秒) が対応していない。
発火する実在 artifact: `output/insights/2026-09-07_t2195-policy-binding/mutation-spec-final.json`
(timeout 3600 / hang 900、hang_risk 変異 5 件)。上書きを設定して混雑時に走らせると、最初の該当変異で
外側 watchdog が先に発火し、orphan hold と rc=2 で全走が止まる。

**なぜ本 wave で直さないか:** 直すには「外側 watchdog が dispatcher のどの区間を覆う契約か」を先に
決める必要がある。今日 main にある collection gate の式 (`mutation_harness.py:1462`) も同じ混同を
持っており、直せば受理集合が動く。式を決めずに実装すると、R4 と同じ誤りを別の場所で犯す。

**ユーザー裁定を求める点:** (a) 外側 watchdog の契約をどう定めるか、(b) 既存 collection gate の式を
その契約へ合わせるか (受理集合が緩む方向)、(c) 遅い orphan hold の代わりに理由付きの早期診断を
出すか (拒否ではなく診断なら受理集合は動かない)。

## R6. 記録 — 段 7 で行う

- F762 の訂正追記: 根本原因の「本走も直呼び」が誤りであること、collection 側は 2026-09-07 の
  1e22c4cbd で解消済みで「恒久対応: 未実装」が stale であること。
- worklog fragment、insight (一次資料として段 2・段 3 の全文と本裁定を repo 内へ保存)。
- decisions へは書かない。R5 は未裁定であり、既成事実にしない。

## 段の進行

実装面の差分ゼロにつき DW-S04 により段 5・6 を飛ばし、変異 matrix は免除。
受入全走は免除しない。`4→7→8→9` で進む。
