---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1726-freeze-rederive
seq: 5
---

## 再発

### F333

- **再発: 2026-08-26 (3 例目)** — 親が焦点走へ `timeout 3000` を掛けて打ち切ったため
  dispatch 親が落ち、PBS job `948508.nqsv` が孤児化して
  `output/pegasus-dispatch/orphan-hold.json` が武装し、この worktree からの dispatch が全停止した。
  打ち切りの見積り自体が誤りで、**実際の所要は 2 分 20 秒**だった
  (`test_real_repo_serialization.py` が pytest を再帰起動する型だと知っていたため過大に見積もった)。
  既載の再発検知どおりの型だが、次の 3 点は台帳に無かった。
  (i) **hold の記録は実態を過小に書く。** 本件の hold は `phase: "pending-qsub"` /
  `request_id: null` / `qdel.attempted: false` だったが、`qstat` には
  `948508.nqsv izdw-b2d ... PRR` が**生きて**いた。qsub は通っており記録更新前に打ち切られている。
  **記録の phase を job 不在の根拠にしてはならない。** job 名 (`job_name`) で `qstat` を引く。
  (ii) **hold は自己解除される。** 孤児 job が終端に達し dispatch 機構が成果物を収集した時点で
  `orphan-hold.json` は機構自身が削除した。手動削除の前に不在を確認すると空振りする。
  復旧手順の "final-step" は、既に消えている場合を想定した書き方になっていない。
  (iii) **打ち切った走行の結果は捨てなくてよい。** 提出 dir
  (`output/pegasus-dispatch/<hash>/`) に `<job>.o<id>` が残り、本件では
  `619 passed, 9 skipped in 140.01s` が読めた。再走せずに済んだ。
  親は手動 qdel をしていない (hold の `manual-qdel-warning` どおり、手動 qdel は F47 の
  `submission-disabled.json` を武装させ、その解除もユーザー手番になるため)。
