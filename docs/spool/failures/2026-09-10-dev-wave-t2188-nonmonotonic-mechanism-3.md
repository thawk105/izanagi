---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-10
wave: dev-wave-t2188-nonmonotonic-mechanism
seq: 3
---

## 新規

### {{F:detached-submit-tree-needs-submodule-init}}. 計測投入用の detached worktree で submodule を初期化せず、probe が外側 repo の HEAD を submodule の HEAD と読んだ [手順漏れ]

- 事象: 更新間隔 10 µs の `Backoff_` trace 計測を投入したところ、job が 17 秒で終了し成果物が 0 件だった
  (request `986864.nqsv`)。stderr は
  `ccbench HEAD 'e7d5d4b1153426e6fd3949451c77b7a46142267a' does not match required pin '511c9538…'`。
  示された値は**外側 repo の wave commit**であり、submodule の commit ではない。
- 根本原因: 投入元として `git worktree add --detach` で専用 checkout を作ったが、
  **その checkout の submodule を初期化していなかった。** `external/ccbench` は gitlink だけが存在し
  作業ツリーが空なので、driver の `_ccbench_head()` が親 repo の HEAD を拾った。
  wave 用 worktree には `DW-C01` / `DW-O20` の手順で初期化を行っていたが、
  **計測投入用に後から作った checkout には同じ手順を適用していなかった。**
- 恒久対応: `git worktree add` で作った checkout は、**用途を問わず**
  `python3 tools/dev_wave_submodule_init.py --worktree <ABSOLUTE>` を通してから使う。
  計測投入用の detached submit-tree も例外にしない。
  投入前に `git -C <submit-tree>/external/ccbench rev-parse HEAD` が pin と一致することを確かめる。
- 再発検知: 投入直前に submodule の HEAD を pin と照合する。job が数十秒で終わったら
  まず job の stderr を読み、pin 不一致でないかを見る。

### {{F:aggregate-agreement-is-not-identity}}. 走行ごとの合計一致を「同一性の実証」として報告した [恒真ゲート]

- 事象: 保存済み `directional_success` が独立な正解に対する的中率でないことを示すため、
  親が「走行ごとの保存合計」と「次勾配が正だった件数の合計」を比べ、
  **468 走行すべてで差が最大 3 件・相対 0.46% 以内**であることをユーザーへ報告した。
- 根本原因: 比べたのは**合計どうし**であり、event 対ごとの一致ではない。
  符号の食い違いが相殺すれば合計は一致する。段 6 の敵対レビューがこれを指摘し、
  対ごとの分割表を作ったところ **合計は 101,857 = 101,857 で完全一致するのに、
  359,969 対のうち 260 対 (0.072%) が食い違っていた。**
  相殺は実在し、合計一致は同一性の証拠になっていなかった。
- 恒久対応: 2 つの量が「同じ」であることを示すときは、**集約後の値ではなく要素ごとに突き合わせる。**
  一致率を新しい精度情報として扱わない。同じ観測量から代数的に導かれる 2 量については、
  `ground_truth_independent: false` と依存関係の式を成果物へ literal で残す。
- 再発検知: 「一致した」と書く前に、集約前の要素で不一致件数を数える。
  不一致が 0 でないのに合計が一致する例が作れるなら、その比較は同一性を測っていない。
