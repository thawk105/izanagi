---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-10-01
wave: worktree-md23-gen-opt-novelty
seq: 2
---

## 再発

### F139

- **再発: 2026-09-30** — md_23 (gen-opt の余地の測定) の repo 外の計測 driver (Codex author) を `dispatch_compute.py --task generic` で計算ノードへ投げると、build が 1 回に 1 件ずつ落ちた。(1) generic は環境変数を消すので `os.environ["TMPDIR"]` が `KeyError`、(2) third-party の cache に空 dir を渡して `fetch_third_party.py hydrate` が `cache root is absent`、(3) CCBench の object dir は `CMakeFiles/<wl>_<proto>.exe.dir/` なのに `.exe` を `.dir` に置換して探し `missing compile command`。さらに plan が smoke の timeout 1 回を variant 全体の見積りに使い 66 job に割れた (投げる前に直した)。2026-09-22 の再発で効いた「既存 driver の成功経路と前提を突き合わせる表を実装子に作らせる」を最初の author prompt に入れておらず、3 度目の fix で初めて求めて build が通った。次から先に確かめること: 計算ノードで走る新しい driver の最初の author prompt に、既存の成功経路 (`tools/vhash_cicada_tuning/driver.py` の `execute`) との段ごとの突き合わせと、環境変数・cache・object dir の名前・見積りの 4 点を名指しで入れる。記録 = `output/insights/2026-09-30/gen-opt-novelty-and-regime/README.md` §6、memory `new-compute-driver-preconditions`。

### F333

- **再発: 2026-10-01** — md_23 の受入全走の 1 回目 (2026-09-30 23:50) で、`tools/dev_wave_wait.py acceptance` の前段 (preclaim) の全履歴 provenance 監査が計算ノードへ dispatch され、gen_S の待ち行列 (同じ利用者の他 session の job で RUN 5・PRR 2・QUE 3) で待たされた。監査の job は 00:11:59 に child_rc=0 で終わったが、前段の上限 1,200 秒が先に切れて親が signal 15 で打ち切られ、孤児 hold (`40051.nqsv`) が wave の worktree に残った (受入は rc=70 `terminal-preclaim-history-provenance`)。共有の受入門番 (`run-acceptance-gated.sh`) は「子の log が無く rc=70」を無条件に再投入する作りで、原因を変えずに 2 回目を投げた (2 回目は待ち行列に空きがあり約 4 分で前段を通過したが、親が「hold で必ず落ちる」と誤認して止めた)。次から先に確かめること: 受入を投げる前と rc=70 の再投入の前に、gen_S の待ち (QUE・PRR) と同時実行数を qstat で数え、待ちがあれば投げない (本 wave は job dir の `gate.conf` で門を閉じる条件として実装した)。再投入の前に `output/pegasus-dispatch/orphan-hold.json` の有無を見る。
