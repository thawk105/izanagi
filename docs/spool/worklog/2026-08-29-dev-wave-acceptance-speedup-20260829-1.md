---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: dev-wave-acceptance-speedup-20260829
seq: 1
title: 受入全走の高速化を 5 軸で評価し、一時領域 I/O 軸を実 regime で棄却して所要を 4 層へ分解した (docs のみ、branch worktree-dev-wave-acceptance-speedup-20260829、実装面差分ゼロにつき変異 matrix は DW-S04 の免除)
---

## 本文

- ユーザー依頼は「受入全走の高速化。並列化の余地をまず考える。不要なテストの削除も考える。
  CPU 並列・書き込み並列も考える。その次に読み取りの効率化を考える。その次に計算ノードへの
  分散ジョブ化を考える」。**5 軸すべてを評価し、実装は 0 件で閉じた。** 実装面の差分はゼロ。
- 5 軸のうち 4 軸は既裁定で閉じていた (並列化 = D1287 / D1103 / D1019 / D820、テスト削除 = D747、
  CPU 並列 = D820 と絶対規律 2、分散 = 実装済み)。残る書き込み・読み取り軸を本 wave が実測した。
- **一時領域 I/O 軸は実 regime で棄却した。** 詳細は {{D:acceptance-tmpdir-axis-refuted}}。
  親はログインノードで「`/tmp` の fsync が 32 並列で 15 倍に崩れる」を実測し、
  全 unit へ一様に効く候補として立てた。しかし受入成果物 568 session の全数解析で
  **549 session 中 549 が計算ノードへ dispatch** しており、ログインノードで走るのは
  単一 process の `--collect-only` だけと判明した。計算ノードで同じ probe を走らせたところ
  (bnode041、loadavg 0.80、request 958445.nqsv)、**`/tmp` は 48 並列でも崩れず、
  Lustre のほうが fsync で 3.3 倍・小 file で 12 倍遅かった。**
  絶対量も 48 並列で 0.2 秒未満であり、実行の中央値 191 秒に対して効きようがない。
- **最初のログインノードの実測は誤りではない。** 誤っていたのは「受入がそこで走る」という
  親の前提である。訂正の連鎖 (立案 → regime 保留 → 棄却) をそのまま記録に残した。
- 段 3 の 2 レンズは独立に BLOCKER 3 件ずつを返し、いずれも「実装すべきでない」で一致した。
  レンズ B は親が気づいていなかった点を出した — **plan の測定形はそもそも実現できない。**
  `IZANAGI_ACCEPTANCE_SHARDS=1` は shard を止めるだけで、login admission が dispatch を選べば
  単一 compute job へ送られる。
- **レンズ A が実装前の near miss を 1 件捕まえた。** {{F:tmpdir-mixed-regime-lock-fragmentation}}。
  性能目的の変更が正しさ防壁を退行させる向きで、しかも plan が用意する予定だったテストでは
  検出できない形だった。絶対規律 2 が想定する事象そのものである。
- **親が同じ raw 集合の別 column を混ぜて比・差・処理量を書いた。** レンズ B が指摘し、
  親が再計算して訂正した。F473 の再発として記録した。結論は変わらない。
- **親の (P5) の推論が既裁定に反証された。** 親は「直列鎖がある以上 node を増やしても
  `max(shard)` は動かない」と D820 を根拠に書いたが、D1103 は「床が動かない」という前提が
  排他鎖の細分化で失効したと明記し、K=2 から K=3 で pytest wall が 124.60 秒縮んだことを
  実測している。一般命題としては偽であり、レンズ B の指摘を受けて撤回した。
- **所要を 4 層へ分解した。** 詳細は {{D:acceptance-phase-decomposition}}。
  NQSV 会計サマリ 1297 件 (parse 失敗 0) で queue 待ち中央値 9 秒 / 実行 191 秒 / job 合計 263 秒。
  **queue 待ちは job の 5.1% で律速ではない。** 依頼に対して queue を削る施策の上限は中央値 9 秒。
- **副産物として D1260 と D1019 を独立に裏取りした。** 3 shard 揃った 206 session の
  最大 shard 中央値 244.9 秒は D1260 の paired K=3 実測 244.810 / 245.707 秒と一致する。
  shard 間の最大差は中央値 116.3 秒あるが、D1019 が「完璧な予言者でも利得 0.0 秒」を
  確定済みであり、本集計はそれを K=3 で裏取りする (D1019 の一次資料は K=2 の 2 走だった)。
- **残っている唯一の user 裁定済みの方向は D1035 (排他閉包の細分化) である。**
  本 wave の全実測がこの方向を裏づけた。本 wave の brief の scope 外なので実装せず、
  次の一手へ起票した。
- 新規の受入走行は本 wave の受入全走 1 回だけで、解析はすべて既存成果物の事後解析である。
  計算ノードへは probe job 1 本 (20 分枠) だけを投入した。
- ログインノードでの TMPDIR A/B 実走は、他 wave が 32 worker の pytest と変異 harness を
  複数走らせて loadavg 20.75 だったため、単独性を確認できず中止した。値は採っていない。
- 段 8 の自己改善は候補 2 件をいずれも**既存 F の再発として台帳へ閉じ、dev-wave docs は
  編集しなかった**。観測 regime と適用対象 regime の差は F29 の 3 例目、単独性未確認のまま
  A/B を投入したのは F3 の再発である。F29 が 2026-07-28 に「dev-wave docs へ prose を
  追加せず裁定側へ記録する」で閉じた前例をそのまま維持した (byte 予算は満杯のまま)。
- 一次資料は `output/insights/2026-08-29_acceptance-speedup-tmpdir/`。

## 次の一手差分

### 新規

- {{T:acceptance-exclusive-closure-subdivision}} **P1・新規**: 受入 wall の床を D1035
  (ユーザー裁定) のとおり排他閉包の細分化で下げる。本 wave の実測で、他の全軸
  (worker 数・shard 数・割付・テスト削除・一時領域 I/O・queue) が閉じたか棄却されたため、
  これが残る唯一の方向である。D820 が real-repo の直列性を正しさ防壁と呼んでいるので、
  細分化は排他の意味を弱めない範囲に限る。着手時は D1008 の資源別 reader/writer lock を起点にする。
- {{T:acceptance-session-residual-decomposition}} **P2・新規**: session 合計 338 秒と
  job 合計 263 秒の差 (約 75 秒) の内訳を測る。候補はログインノードの全件 collection、
  dispatch の帳簿処理、handled の検知遅れ。現 artifact では分解できていない。
  親開始・各 qsub・confirm・job 開始・pytest 開始と終了・handled・collection 開始と終了を
  同一 session で時刻化する。
- {{T:conftest-tmpdir-docstring-correction}} **P3・新規**: `orchestrator/tests/conftest.py` の
  module docstring が「遅さが気になる場所ではディスク上の速い TMPDIR を明示せよ」と誘導している
  根拠は単一 process の測定だけであり、計算ノードでは順位が逆転する。実装面なので Codex author が要る。
  DW-G05 では成果物の値・受理集合・参照を変えないため must-fix ではなく backlog とした。
- {{T:multi-node-shard-effect}} **P3・新規**: multi-node shard の効果は未測定である。
  D1103 が K=3 を確定しているので K の再提案ではない。D820 を不可能性の根拠に使わない
  (D1103 が前提の失効を明記している)。着手前に測定設計をユーザー裁定へ諮る。
