---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t2265-backoff-itt
seq: 1
---

## 再発

### F24

- **再発: 2026-09-07** — 変異本走の生死確認に `pgrep -f` を道具名だけで掛け、**別 session の
  変異走行を自分の子と誤認した**。自分の harness は約 50 分前に中止していたのに「実行中」と
  報告し続け、ユーザーへの報告そのものが誤りになった。2026-08-26 の再発と同型
  (`DW-M05` が要求する worktree path での一意化を、待ち直しのたびの生存判定へ適用していない) で、
  **違いは実害がゼロでなかったこと**である。判定を spec path で掛け直して是正した。
  同じ wave で `tools/dev_wave_wait.py producer` の argv を 2 つ誤り
  (`--artifact-file` 欠落、および存在しない `--max-wait-s`)、待ち手が `stage=cli-usage rc=2` で
  即戻ったのに待ち手 shell の rc は 0 だったため「完了」と誤読しかけた。
  `.done` の実在確認 (F24 の恒久対応) がそのまま効いて子の生存を捕まえた。

### F42

- **再発: 2026-09-07** — 7 回目。新設した `orchestrator/tests/test_backoff_counterfactual_analysis.py`
  が自走 harness を持たず、受入全走 (21,309 passed / 68 skipped) を
  `test_plain_runner_coverage.py` の 1 件赤にした。2026-08-11・2026-09-04 と同じ degrade 経路
  (Pegasus では codex 実装子が計算ノードへ dispatch できずテストを 1 件も走らせられないため、
  実測義務が親へ移る) である。
  **本 wave の追加事実は、恒久対応が既に入口の dispatch 表から届く節へ逐語で書かれていたことである** —
  `DW-O26` の「新規 test file を足す走は file 集合列挙のメタテストも焦点走に含める」は、
  条件 18 (親のテスト・受入前) で必読に指定されている。親はその条件で節を読みながら、
  焦点走の集合を wave の対象 module から組み、横断メタ検査を入れなかった。
  **型は「手順書の不足」ではなく「必読に指定された逐語を読んだ上で適用しない」**であり、
  2026-09-04 の「逐語を親が守らなかった再発」と同じ位置にある。
  費用は受入全走 1 回分 + fix 子 1 本 + worktree 1 本。是正後の焦点走は 24 passed・赤 0。
