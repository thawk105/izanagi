---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1647-a2-cert-run
seq: 3
title: [T-1647] A-2 4-cell certification の実走を試み、land 済み実装の 3 欠陥を閉じた。計測自体は批准待ちで未了 (コード + docs、branch worktree-dev-wave-t1647-a2-cert-run、変異 matrix = baseline PASSED・16/16 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 依頼は「land 済み A-2 driver で 4-cell certification を実走する」であり、実装差分ゼロで
  終わる想定だった。実走 1 回目が 6 秒で `driver_rc=1` 終了し、**land 済み実装のままでは
  certification が原理的に終端しない**と判明したため、読み込み契約に従って段 1 へ巻き戻し、
  3 欠陥の修理 wave として進めた。逐語証拠と probe の実測は
  `output/insights/2026-08-25_paper-story-a2-certification-run-defects.md`。
- 欠陥は (1) job body が driver を素の `python3` で起動しており計算ノードの oneAPI
  Python 3.9 に解決される、(2) 投入時の可視性述語が実 NQSV では満たせない、
  (3) `PBS_JOBID` のコロンが依存 prefix を経由して build を殺す、の 3 件。
  (1) は failures 台帳の F46・F84 と同型で**独立 3 例目**であり、F84 の恒久対応
  (dispatch_compute の interpreter 選択と PATH 先頭化を逐語で写す) が写されていなかった。
- 段 2 プランは「`Current State` として実測した `{Staging, Running}` だけ受理する」を推したが、
  親は既存 canonical 語彙の再利用へ裁定を覆した ({{D:nqsv-state-vocabulary-single-source}})。
  **本走 2 回目が投入後 `Current State = Queued` で待機したため、プラン案なら正常運用で
  fail-closed していたことが実環境で確定した。** 親 brief 自身の「実測値だけを受理集合の
  権威にする」という不変条件も過学習として書き直した。
- 敵対レンズ B が挙げた「次の実走で落ちる箇所」6 件のうち 5 件を計算ノードの probe 2 本で
  反証した (GitHub egress は通る、必要 command は全実在、`/tmp` に 128GB、統合依存 prefix は
  compute の GCC 11 で完全 build 成功 19 秒、env contract の attestation も通る)。
  代わりに probe が欠陥 (3) を発見した。**probe を先に回したことで 6 時間の walltime を
  捨てずに済んだ。**
- 段 6 の敵対レビューは A が NO-GO (must-fix 2)、B が GO (must-fix 0)。A の 2 件は
  `Ended Request Time` 検査が 0 件で素通りする穴と、可視 block と request 消滅署名を
  連結した自己矛盾 stdout が通る穴で、どちらも突破用 stdout 付きだった。
- **修正が実環境で効くことは実証できた。** 本走 2 回目で実 `qstat -f` の
  `Current State = Staging` が canonical に `QUE` へ正規化され、**submission receipt が
  初めて記録できた**。欠陥 (2) の修正の実環境実証である。
- **計測は完了していない。** 本走 2 回目は `run_workload` まで到達したあと 16 秒で
  `enforcement-source-closure-unratified` により停止した。F498 の再発で、
  批准台帳が main に存在しないためである。本 wave は閉包 25 path のいずれにも触れておらず、
  HEAD の closure digest は main と完全一致する。D526 により追記経路は AI に閉じており、
  解除は人間手番である。詳細と必要な digest は failures 台帳の F498 再発項に書いた。
- 受入 1 回目の赤 8 件は既登録の再発型 (受入 shard 経路の `_real_output_snapshot` 汚染) で、
  台帳が定める帰属否定 3 点を実測で満たし、2 回目で消えた。2 回目の赤 1 件は
  **本 wave 由来の真の赤**で、新設テスト node が受入所要時間台帳に無く被覆率が
  89.902546% となって 90% の gate を割った。親が自分で台帳を再生成して commit したところ
  provenance 検査が「実装面には Codex author が必要」と決定的に判定したため commit を戻し、
  land 済み生成器を Codex author 子に走らせて再取得した (14457 -> 15904 node)。
- 親の手順違反を 1 件記録した ({{F:mutation-run-broken-by-parent-commit}})。
  変異走行中に merge を commit して HEAD を動かし、harness を fail-closed で止めた。
  受入走行中に insight を書いて未追跡 file を増やし、`postrun-clean` で 1 回捨てた失敗も
  同じ型 (走行中に repo の状態を動かした) である。

## 次の一手差分

### 更新

- [T-1647] **P1・人間手番待ち**: A-2 の 4-cell certification 実走。実装側の欠陥 3 件は
  閉じ、submission receipt までは実環境で通ることを実証した。残る障壁は
  enforcement-source closure の批准だけである (F498 の再発)。
  main の現行 closure digest
  `1111720da46ae17801b13af608c0b9e119b23c87a6eeb8686df7df478d64df71` に対する批准行が
  `hooks/enforcement-source-closure-ratifications.v1.jsonl` に無い。
  A-1 wave が land すれば closure が
  `db511c3d841128bfdbf5ba7c6bbdb2ce4da1fe0fdefe8d52aaacb0906ddeea44` へ動き既存の
  批准行と一致する。どちらの経路を採るかは人間の裁定。
  批准後は新しい attempt_id で再投入するだけでよい。
  base: 9d140130b02abc93048dcd906a8f2d66a32c58237d7724ffbecf4c5afb401289

### 新規

- {{T:a2-rr5-cost-calibration}} **P2・新規**: rr5 (write-heavy, rratio=5) の
  full-scale trace 量・verifier 時間・RSS を実測する。現在の見積り根拠
  (539MB / 16.9M 行 / verifier 141 秒) は rr50 の値であり、rr5 へ転移しない。
  4 cell が 6 時間の walltime に収まるかは判定不能のままである。
  cold build は 19 秒と実測済みなので、walltime のほぼ全部を correctness と performance に
  使える。批准が解けた後、最初の実走で rr5 の実コストを採るのが最も安い。
- {{T:acceptance-shard-taskrun-isolation}} **P2・新規**: 受入 shard 経路が
  `output/task-runs/` と `output/runs/` へ書くため、`_real_output_snapshot` 系の
  副作用ゼロ検査が全 wave で間欠的に赤くなる。本 wave でも 8 件踏んだ。
  task-run 記録の書き出し先を shard session root へ逃がす seam
  (`dispatch_compute.dispatch()` の `output_root` と同型) が筋である。
  受入基盤の所有 wave の判断に委ねる項目として F136 系が繰り返し挙げてきたが、
  独立事例が積み上がっており費用は全 wave が払い続けている。
