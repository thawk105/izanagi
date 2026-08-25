---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-acceptance-parallel-dispatch
seq: 2
---

## 新規

### {{F:fresh-worktree-probe-misrepresents-production}}. 新品 worktree で測った probe を本番の代表値として裁定に使いかけた [測定条件] [near-miss]

- 事象: 受入全走の高速化 wave で、親が自分の新品 worktree から計算ノードへ probe を投げ、
  test 0 件の走行に 49.32 秒かかることを「受入の固定 overhead」として brief と裁定へ書いた。
  同じ probe を cache が満ちた worktree で走らせると 15.40 秒だったため、親は
  「外部 cache を足せば 34 秒縮む」と結論しかけた。段 5 の直前に自分で反証し、実装へ進む前に止めた。
- 根本原因: probe を走らせた worktree は pytest を一度も実行していなかった。実運用の受入は
  必ず focus 走の後に走るため、repo 内 `__pycache__` が既に満ちている。**probe の条件が
  本番の条件と違うことを、probe を投げる前にも後にも照合していなかった。**
  実在する wave worktree 49 個はすべて 247〜259 件の pytest rewrite cache を持ち、
  ある wave の 4 回の受入はいずれも 254 件以上が既に書かれた後に走っていた。
- 恒久対応: {{D:pytest-rewrite-cache-already-warm}} に、この cache が既に効いている事実と
  その確認手順 (実在 worktree の rewrite pyc 件数と mtime + size 有効性、受入時刻との前後関係) を
  凍結した。同種の高速化を再提案する場合は、この節の実測値を先に反証する必要がある。
- 再発検知: 同じ probe を「本番と同じ状態の worktree」でもう一度走らせて値が変わるか見る。
  変わるなら probe 条件が本番を代表していない。

### {{F:parallel-probe-output-mislabelled}}. 並列に投げた probe の出力を投入順と取り違えて報告した [帰属誤り]

- 事象: 同じ wave で、`IZANAGI_TEST_NPROC` を 8 と 24 に変えた probe を 1 つの背景 command で
  連続投入し、2 つの log を `grep -h` でまとめて読んだ。出力の並びを投入順と仮定したため、
  8 worker = 41.00 秒 / 24 worker = 36.57 秒と報告した。正しくは 8 = 36.57 / 24 = 41.00 である。
  この取り違えにより「固定 overhead は worker 数にほぼ依存しない」という誤った一般化を
  brief と親のユーザー報告へ書いた。段 3 の敵対レンズが実成果物から指摘し、親が
  dispatch receipt の `request.json` と job stdout を突き合わせて訂正した。
- 根本原因: 値の帰属を、実行条件を持つ成果物 (`request.json` の環境と job の stdout が
  同じ dispatch directory に同居する) ではなく、**log を読んだ順序**という外部の仮定から決めた。
- 恒久対応: `docs/dev-wave/operations.md` の `DW-O02` が要求する「wave 専用 subdirectory の
  artifact から読む」に従い、条件つきの測定値は条件を保持している成果物 field から
  join して読む。並べた log の行順を条件の代理にしない。
- 再発検知: 条件を変えた測定を報告する前に、条件 field と値を 1 行ずつ同じ成果物から
  join して表にする。表を作れないなら帰属が確定していない。
