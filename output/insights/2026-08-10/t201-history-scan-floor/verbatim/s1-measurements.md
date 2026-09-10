# 親の前提実測 (段 1 v2 追補) — 2026-08-09

**測定環境: ログインノード pegasus02、worktree `dev-wave-suite-floor-recheck` (main ee2da0bf 相当)。
共有ノードの単独走行 1 回であり、一次証拠にしない (D104 決定 4)。桁と一致性の判断にだけ使う。**

対象 path = `output/t080-migration/legacy-freeze-repin.receipt.json` (= `RECEIPT_REL`)。

## 単価 (HEAD 1 commit に対する `git diff-tree`)

| 形 | wall | user | sys | 出力行数 |
|---|---|---|---|---|
| 現行 (`-m -r -M -C --find-copies-harder`) 1 回目 | **4.208 s** | 0.168 | 0.795 | 5 |
| 同上 2 回目 (warm 期待) | **7.609 s** | 0.170 | 0.925 | 5 |
| `--find-copies-harder` を外す (`-M -C`) | **0.019 s** | 0.001 | 0.008 | 5 |
| 現行のまま **pathspec `-- <RECEIPT_REL>` を付ける** | **0.014 s** | 0.000 | 0.007 | 0 |

## この 4 行から言えること

1. **`--find-copies-harder` の費用は CPU ではなく I/O が主である。** wall 4.2〜7.6 秒に対し
   user+sys は約 **1.0 秒**しかない。並行セッションが報告した「4.13 秒 = diffcore の計算」という
   解釈は**この機体では成り立たない**。`--find-copies-harder` は copy 元候補として
   **未変更ファイルの中身まで読む**ため、`output/` の 9435 ファイル / 284 MB を
   commit ごとに共有 FS から読むことになる。
2. **2 回目のほうが遅い (4.2 → 7.6 秒)。** page cache では説明できず、共有ログインノードの
   外乱を強く受けている。ノード間 1.8 倍 (M5) と整合する。**wall を一次証拠にしてはならない**
   という D104 決定 (4) の妥当性がここでも再確認された。
3. **`--stdin` batching は効かない。** process 起動は 0.019 秒側の測定から 0.02 秒未満と分かる。
   節約できるのはそこだけなので、期待効果は 1% 未満である (段 2 v2 の推奨候補への反証)。
4. **pathspec 限定は 300〜500 倍速い**が、`-C --find-copies-harder` の rename/copy 検出は
   pathspec の外にある相手を見つけられなくなるため、**受理集合が変わりうる**。
   現行が捕らえている「RECEIPT_REL が copy の source として現れた commit」がこれに当たる。

## さらに決定的な事実

```
$ git log --format=%H -- output/t080-migration/legacy-freeze-repin.receipt.json | wc -l
1
$ git log --format=%H -- output/t080-migration/legacy-freeze-repin.receipt.json
8bec195d096f852fd2b47070aa18a3b151613f0a
```

**全 2183 commit のうち、この path を触った commit は導入 commit 1 個だけである。**
現行の検証は、descendant 1529 commit に対して毎回 284 MB 級の全ツリー copy 検出を回し、
**毎回「何も見つからない」ことを確認している**。

## 帰結 (段 4 で裁定する材料)

- 全史 equivalence を「新旧の判定値が全件一致」で取ると、**新旧とも全件 False** になる公算が高い。
  これは**恒真な control** であり、受理集合不変の証拠として弱い (段 3 v2 レンズ A の攻撃点)。
  → 改竄を実際に仕込んだ合成履歴での差分検出能力を、control の中核に据える必要がある。
- 「効果ありだが受理集合が変わる」候補 (pathspec 限定・`--find-copies-harder` 除去) と
  「安全だが効果なし」候補 (`--stdin` batching) の二分が現時点の姿である。
  両方を避ける道があるとすれば **2 段構え** (安い検査で候補を絞り、絞った commit だけ現行方式で
  確認する) であり、その等価性条件を段 3 v2 レンズ B に詰めさせている。
