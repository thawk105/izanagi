---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-13
wave: t979-cheap-history-scan
seq: 1
---

## {{D:cheap-first-history-scan}}. 受領証の履歴走査を安価先行の二段構えにし、構文検証を通した安価出力を不在の証明とする

**決定:** `_batched_history_touches_path` は、まず rename/copy 検出を外した安価走行
(`--no-renames`) で対象 path と対象 blob OID の不在を確かめ、**どちらも現れなければ即 `False`**
を返す。どちらかが現れたときだけ、全 commit を従来の高価 argv (`-M -C`) で再走査し、その判定を返す。
安価側と高価側は**同一の厳格 parser**を通し、commit group の欠落・順序不一致・終端不正・
未知形式はどちらの走行でも `receipt.git_error` で止める。

**信頼境界を明示する:** この設計は「git が構文的に妥当な出力を返したなら必要な record を
省略しない」ことを前提にしている。安価走行が構文を保ったまま record を落とす故障モデルでは、
従来 `True` だった履歴が `False` になる。ユーザー裁定 (選択肢 (i)) はこの境界を承認しており、
docstring に明記する。**高価コマンド固有の故障を毎回は観測しなくなる**点も同じ裁定に含まれる。

**argv は凍結 tuple の定数 2 つに閉じ、`_git` へ渡す直前に定数から導出しない独立な検査を通す。**
検査内容は許可 token 集合 (独立 literal)、`-C` と `-M` の重複禁止、`--find-copies-harder` の不在。
`assert` は `-O` で消えるため使わず `MigrationError` を送出する。

**理由:**

- 本番入力 (reachable 3,572、descendants 2,920、targets 2,919) の実測で、同一機体・同一入力の
  高価走行単独が 26.271 秒であるのに対し、二段構えは 0.704 / 0.706 / 0.710 秒だった。判定は
  `False` のまま変わらない。従来の走査は commit 数に比例して伸びる構造だった。
- 包含は git の意味論から従う。diffcore の rename/copy 検出は**既存の filepair を対応付けるだけ**で、
  新しい destination path も新しい非零 dst OID も生成しない。rename の source は安価側に `D`、
  destination は `A` として現れ、`--find-copies-harder` を使わない `-C` の copy 元は
  同じ commit 内で変更済みなので安価側にも現れる。実測でも、本番入力 2,919 commit に対して
  安価側と高価側の path 集合 (11,448 件) と非零 dst OID 集合 (12,279 件) が完全一致した。
  **有限観測は普遍性を含意しない**ため、根拠は実測ではなく上記の filepair 制約に置く。
- 敵対レンズが merge (`-m`、2 親・3 親・octopus)、root commit、mode change、
  regular/symlink/gitlink の type change、実 submodule の gitlink、非 UTF-8 / 空白 / 改行を含む path、
  空 blob、同一 OID の複数 destination、削除と追加の同居、`.gitattributes` の diff driver、
  `diff.renameLimit` 超過の巨大 commit について反例を探し、**いずれも反例を構成できなかった**。

**`--find-copies-harder` の検出器がこの変更で移動する。** `-C` を 2 回書くのは
`--find-copies-harder` と同義である (git 2.34.1 で実測確認)。二段構え前は、内容を変えた copy
(near-copy) の期待値 `False` がこの flag の混入を振る舞いとして検出していた。二段構え後は
near-copy が安価 trigger を発火させないため高価走行に到達せず、**その検出は失われる**。
そのため argv の機械検査は「あれば良い追加検査」ではなく、受理集合の保存そのものを担う。
同一変異を wave 前後の HEAD へ当てた実測では、赤になる node が 1 件 (振る舞いによる検出) から
14 件 (うち 13 件は production guard 由来) へ増えた。

**却下した選択肢:**

- **禁止文字列 `--find-copies-harder` の不在だけを検査する** — `-C` の重複、`-C90` 形、
  長形式の重複がすべて素通りする。実測で `-C -C` が harder と 1 byte 違わぬ raw 出力を出すことを
  確認しており、この検査では受理集合を守れない。
- **完成 argv が凍結定数のいずれかと一致することだけを検査する** — 比較対象も同時に変わるため、
  **定数そのものを書き換える変異を通す**。段 6 の敵対レビューが摘出した。多重防壁として残すが、
  安全性の根拠は独立検査の側に置く。
- **高価 fallback を trigger が発火した commit の部分集合へ絞る** — per-commit の包含主張が別途要り、
  健全な repo では trigger 自体が発火しないので利得がない。
- **`_history_touches_path` / `_any_history_touches_path` も二段構えにする** — production の
  呼び出し元は一括版だけであり、逐次版は等価性 control として単段のまま残す方が対照になる。
- **安価側に緩い parser (部分文字列検索など) を置く** — 未知 metadata・marker 欠落・NUL 終端不正を
  見逃す。同一 parser 1 回の走査から集合証拠と従来判定を同時に作る。

**D260 との関係:** D260 は当時「`diff-tree --stdin` で 1 process に畳む」を、process 起動が
0.02 秒未満で節約が 1% 未満という実測に基づき却下していた。その後の一括化でこの前提は変わっており、
本決定はさらに走査そのものを安価側へ倒す。D260 の argv 決定 (`--raw` の destination OID で
exact copy を検出し `--find-copies-harder` を使わない) は**不変のまま引き継ぐ**。

**研究状態への影響:** certified 選択・材料レポート・proof chain・凍結 bytes は不変である。
正常な git 出力に対する受理集合も不変である。変わるのは (a) 走査の所要時間、
(b) 安価側が構文を保ったまま record を落とす故障モデルと高価コマンド固有の故障の扱い、
(c) 安価側の起動・parse 失敗が従来の正常判定を `receipt.git_error` へ倒す過剰拒否の追加である。
