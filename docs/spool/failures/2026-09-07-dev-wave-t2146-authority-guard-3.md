---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t2146-authority-guard
seq: 3
---

## 新規

### {{F:perf-output-weakened-existing-trees}}. 防護を足す変更が、無関係な既存の防護対象を弱めた [受理集合の後退] [検査 corpus の穴]

- 事象: 発行主体 subtree の防護を `perf` の出力先判定へ足した際、出力値を後段の既存判定から
  除外したため、**末端でない既存の防護対象**が `perf` の出力先として通るようになった。
  退化した形は 6 つ (official / exploration の campaign tree、exploration の namespace marker、
  `hooks/` 配下 2 本、ccbench)。拒否だけを増やすはずの変更が既存の拒否を解いており、規律 2 に
  直接触れる。
- 根本原因: 出力 option とその値の index を記録して後段の走査から除く実装にしたが、
  除く前の直接検査が末端判定と新しい発行主体判定しか見ていなかった。末端でない既存の防護 tree が
  どちらの網にも掛からない隙間に落ちた。
- **検査が取り逃した理由**: 親が D428 の反転検査を回したが、corpus 61 件に
  「既存の防護対象を `perf` の出力先に取る形」が 1 件も入っていなかった。反転検査は仕組みとして
  正しく動いたが、入力集合が薄かった。見つけたのは段 6 の敵対レビューである。
- 恒久対応: `orchestrator/tests/test_hooks.py` の
  `test_t2146_guard_bash_perf_output_keeps_all_protected_trees_denied` が、3 つの option 形について
  発行主体と既存の防護対象 5 種の拒否を固定する。変異 `mf1-perf-existing-tree` (この判定を無効化)
  が本走で KILLED になることを実測し、歯が立っていることを確かめた。
- 再発検知: 上記テストと変異。加えて {{D:authority-guard-mirrors-existing-tree-protection}} が
  「既存対象が持つ性質だけを足す」線を引いており、既存判定を迂回する実装はこの線から外れる。
- 併せて記録する対の教訓: **D428 の反転検査は corpus の広さが命である。**
  受理集合を変える wave では、変更した分岐が触る**既存の防護対象すべて**を corpus に入れる。
  「発行主体だけを対象にした corpus」は、まさに今回の型を構造的に見逃す。

### {{F:second-worktree-locks-itself-after-guard-write}}. guard 編集用の第 2 worktree が、自分自身の変更で施錠されて fix を適用できなくなった [作業場の自己施錠] [手順漏れ]

- 事象: D427 の経路で第 2 worktree に `guard_write` の新版 (発行主体判定入り) を commit した後、
  段 6 の fix 子を同じ worktree へ投入したところ、`hooks/` への apply_patch が自己保護で拒否され、
  fix を適用できなかった。子は迂回を試みず「原因と修正案は特定したが未適用」と正しく報告して
  止まった (この挙動自体は正しい fail-closed)。
- 根本原因: `guard_write` に hooks 判定が入った瞬間から、その worktree でも `hooks/` 配下が
  どのツールからも編集できなくなる。D427 は経路を定めるが、「第 2 worktree も 1 度きりで
  使い切りになる」ことは書いていない。
- 恒久対応: `hooks/README.md` の「guard 自身の保守境界」へ運用知見 3 点として記録した
  ({{D:d427-guard-edit-route}})。修正が要るときは `guard_write` に判定が入る前の commit から
  fix 用 branch を作って作業場を復活させる。本 wave では実際にこの手順で復旧し、
  復旧後の worktree で `hooks/` への apply_patch が通ることを実測してから再投入した。
- 再発検知: 同じ状況に入った子は apply_patch の拒否で必ず止まる (fail-closed)。
  親が README の 3 点を読めば復旧手順が引ける。

## 再発

### F23

- **再発: 2026-09-07** — 子の producer script を包む runner shell が外側から落とされ、
  `.done` が書かれないまま子だけが正常完走した。receipt は `outcome=accepted` /
  `stop_reason=completed` / `codex_exit_code=0` / `validator_rc=0` で、成果物は
  `attempt-0001.output.md` に残っていた。`.done` 不在を子の失敗と読むと、完走した 410 秒・
  22 model call を捨てて投げ直すことになる。**`.done` が無いときは receipt と attempt file を
  先に見る。** 本 wave では attempt file から成果物を回収して先へ進めた。
