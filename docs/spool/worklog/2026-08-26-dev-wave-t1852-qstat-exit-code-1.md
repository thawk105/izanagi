---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1852-qstat-exit-code
seq: 1
title: [T-1852] qstat -J -f の Exit Code は失敗事由を名指ししないことを実測で確立した (docs のみ、branch worktree-dev-wave-t1852-qstat-exit-code、実装面の差分ゼロ)
---

## 本文

- 依頼は事実確立だけで、`S8B_RETRYABLE_FAILURE_REASONS` への登録と retry 方針の変更は
  scope 外と明示されていた。**実装面の差分はゼロで land する。**
  `FAILURE_REASON_RULES`・`OBSERVED_EXIT_CODE_COUNTS`・`_FLOOR_RECOVERY_AUTHORITIES` は
  1 byte も触っていない。
- **問いの答えは「どの値もどちらの事由も名指ししない」だった。** `Exit Code` は
  `wait(2)` status の 16 進表記で、job の最上位プロセスが**どう終わったか**しか持たない。
  実行時間超過 (D740 が retry 不可として除外) と実行中の `qdel` が**同じ `9`** を返す。
  値・逐語・未観測の範囲は
  `output/insights/2026-08-26_t1852-nqsv-exit-code-mapping/RESULT.md`。
- **D1006 の結論は裏付けられたが、理由が変わった。** D1006 は「対応表が未確立だから登録しない」
  と書いていた。実測の結果は「この surface にはそもそも事由が入っていないので、
  表を作る道が無い」である。**後続が「もっと観測を集めれば表ができる」と読まないよう、
  この差を成果物に明記した。**
- **13 事由を誘発し、3 事由を未観測として空欄のまま残した。** 誘発できたのは終了コード
  5 種 (0 / 7 / 11 / 17 / 255)、job 自身の SIGKILL・SIGTERM、外から `qsig` で送る
  SIGTERM・SIGUSR1、実行時間超過 2 走、実行中の `qdel` 2 種、実行開始前の `qdel`。
  誘発できなかったのは node 故障、
  operator / scheduler が発行する削除、保守停止・preemption である。
- **敵対レビュー 1 本 (codex、read-only) が must-fix 5 件・should-fix 6 件を返し、全件採用した。**
  中身は 1 件残らず「証拠が支えている範囲を超えて書いている」であり、実装の誤りではない。
  最大のものは**符号化の一般化**で、有限の観測点から「`Exit Code` は常に wait status」
  「事由は 1 bit も入らない」と普遍則を書いていた。D1006 が却下したのはまさにこの形なので、
  結論を観測できた範囲の中へ畳み直した。2 番目は **E4 を D740 の retry 可側として
  扱っていた**こと — E4 は user 発行の `qdel` であって `scheduler_external_interruption`
  ではない。「retry 可否が衝突する」から「`9` は事由を 1 つに定めない」へ縮めた。
  残りは逐語の不足で、**添付証拠から「誘発条件 → 観測値」を独立に辿れなかった**。
  case ごとに script・qsub 出力・介入時刻と rc・`.e`・境界 snapshot 4 種を束ねた
  manifest を作って閉じた。
- **レビューの指摘 1 件は、親が根拠に挙げた snapshot が実際には添付に無い形だった。**
  `qstat -J -f` が投入直後に `does not exist` を返す件で、主張を消すのではなく
  当該 snapshot を manifest の境界として抽出し直して支えた。
- **レビューの指摘 2 件が、追加の実測で潰せる形だった。** `/opt/nec/nqsv/bin` を数えて
  `qsig` を見つけ、外から任意 signal を送れることが分かったので、
  過去台帳の `A` (signal 10) を `qsig -s SIGUSR1` で独立に再現した。
  同じ棚卸しで会計 command (`racctreq` / `racctjob`) の実在も分かり、
  「履歴照会 command が無い」という当初の記述を「命令はあるが権限が無い」へ訂正した。
- **過去台帳の値 5 種のうち 3 種を再現し、1 種は整合の指摘に留めた。** `1100` は
  終了コード 17 の表記であることを `exit 17` の job で再現した (**scheduler の事由コードではない**)。
  `9` と `A` も再現した。`F` (signal 15) だけは再現できていない — 既定では SIGTERM が
  job に効かず、`qsig` で外から撃っても完走した。**整合の指摘であって実測ではない**と
  書き分けた。`1100` を 2026-08-15 に出した producer が
  何だったかは特定していない。
- **登録を考える前に効く運用上の制約を 2 つ実測した。** (a) 終端記録が `qstat` に見えている窓は
  **約 5〜6 秒**しかなく (5 走で 5〜6 秒)、終了 request の履歴照会 command がこの scheduler に無い。
  (b) 実行開始前に削除された request には `Exit Code` が最後まで付かない。
- **親が自分の観測器の欠陥を実測中に見つけて直した。** `qstat` は**存在しない request にも
  終了コード 0 を返す**ため、rc で存在判定していた停止条件が一度も発火せず、
  poller が全件で上限まで回り続けていた。本文判定へ直した。
  同型の罠として `qstat -J -f` が待ち行列中も `does not exist` を返すことも見つけ、
  両方を `docs/pegasus-runbook.md` §3 へ足した。
- **親は E15 の説明を一度書き誤り、記録前に訂正した。** `--accept-sigterm` を付けた走行が
  警告時点で終わらなかったのを「job script が SIGTERM で死なないため」と書いたが、
  request 記録を確認すると **`Accept Sigterm` が `No` のまま**だった (警告値 60 秒は効いていた)。
  qsub は syntax error を返さず受理している。**原因は特定できていないので、
  特定できていないと書いた。**
- 最初の削除 case (E5) は poller を張る前に `qdel` を撃ったため観測を取り逃がした。
  順序を入れ替えた E11 で取り直している。**取り逃がした走行を成果として数えていない。**
- 投入は背景 job セッションの Bash から行い (runbook §8 の F49 (ii) 例外)、
  削除したのは本 wave の request だけである。観測終了後に `qstat` が空であることを確認した。

## 次の一手差分

### 完了

- [T-1852] `qstat -J -f` の `Exit Code` と失敗事由の対応を実測で確立した。答えは
  「どの値もどちらの事由も名指ししない」で、`Exit Code` は `wait(2)` status の 16 進表記である。
  誘発できない 3 事由は未観測として空欄のまま残した。
  remaining: none
  base: d95300839eb96765d75668f6f5b34942c923000adc73a51581192185bf7560c3

### 更新

- [T-1853] **P1・ユーザー裁定待ち**: `_FLOOR_RECOVERY_AUTHORITIES` への登録時期。
  D880 は本作業へ割り当てたが、対応表が未確立のままでは正当な発行 0 件のまま受理 bytes だけが
  広がる。[T-1852] の実測で前提が変わった — 表が未確立なのではなく、
  `Exit Code` に事由が入っていないため**この surface を根拠にした登録は成立しない**。
  別の証拠源を選ぶか登録しないかの択一になる。
  base: 1e63c783f44f34471836767d10f1ecfa441abeb1d123cca382ba3512c4d5d151

### 新規

- {{T:node-failure-signature-unobserved}} **P2・新規**: node 故障時の
  `State Transition Reason` が未観測である。共有環境で誘発できないため、
  偶発事例を取りこぼさず拾う経路 (終端の約 5〜6 秒窓に張り付く収集) が要る。
  これが無い限り、`DELETE` を外因性の証拠として使う述語は恒真か恒偽に倒れる。
- {{T:accept-sigterm-not-applied}} **P2・新規**: `qsub --accept-sigterm` を渡しても
  request の `Accept Sigterm` が `No` のままになる。qsub は受理し、
  同時に渡した警告値は効いている。[T-362] が未実測として残した mitigation leg は
  この経路では投入できない。
