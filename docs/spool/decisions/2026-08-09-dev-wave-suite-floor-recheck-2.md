---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-09
wave: dev-wave-suite-floor-recheck
seq: 2
---

## {{D:history-scan-copy-clause}}. freeze receipt の履歴走査から `--find-copies-harder` を外し、exact copy を blob OID 一致で検出する

**背景 (実測):** `_history_touches_path` は descendant commit ごとに
`git diff-tree --root --no-commit-id --name-status -m -r -M -C --find-copies-harder <commit>` を撃つ。
`--find-copies-harder` は**未変更ファイルまで copy 元候補として読む**ため、単価が tracked bytes に
比例して伸びる。ログインノードでの実測は次のとおり (共有ノード 1 回走行、桁の目安)。

| 形 | descendant 20 commit | 1 commit あたり |
|---|---|---|
| 現行 (`--find-copies-harder`) | 45.31 秒 / CPU 13.2 秒 | 2.27 秒 |
| `--find-copies-harder` 除去 (`--name-status`) | 0.180 秒 | 0.009 秒 |
| `--raw` (OID 付き、本決定の形) | 0.075 秒 | 0.004 秒 |

`_any_history_touches_path` は descendant を**全件** 8-thread pool へ submit し、`any()` は戻り値の
意味論だけで投入済みの仕事を打ち切らない。したがって receipt 検証 1 回の発火数 = descendant 数であり、
その数は D104 当時の 298 から 1529 へ 5.13 倍になっていた。現行方式を外挿すると 8-thread でも
約 434 秒で、受入全走 1055〜1210 秒の約 4 割を 1 機構が占める。**D104 決定 (2) は現規模でも成立し、
当時より強く効いている。**

一方、全 2183 commit のうち対象 path を触った commit は導入 commit 1 個だけである。現行は毎回
1529 commit を全走査して「何も見つからない」ことを確認していた。

**決定 (1): argv を `--name-status` から `--raw` へ変え、`--find-copies-harder` を外す。**
`--raw` は同じ 1 回の呼び出しで destination blob OID を返すため、追加の git 呼び出しなしに
下記の検査を載せられる。`-M -C -m --root -r` は変えない。

**決定 (2): 従来の述語を維持し、exact copy を blob OID 一致で検出する clause を足す。**
従来の述語 (status の 1 文字目が `{M,D,R,C,T}` かつ対象 path が path 欄に出現) はそのまま残し、
加えて「destination blob OID が対象の期待 OID と一致し、かつその entry の path が対象自身でない」
entry を exact copy として検出する。期待 OID は callsite から `duplicate_oid` として渡し、
既定値 `None` で既存呼び出しの挙動を変えない。

**決定 (3): 受理集合の変化は 1 点だけであり、それは意図的な縮小である。**
検出しなくなるのは「対象を未変更のまま、**中身を変えた**別ファイルへコピーした commit」
(旧 `-C --find-copies-harder` が拾っていた 50〜99% 類似の copy) だけである。exact copy は
決定 (2) の検査が従来どおり拒否するため、既存の
`test_state_rename_copy_type_change_and_worktree_loss_are_rejected` は**無改変で緑**である。
これはユーザー裁定による意図的な縮小であり、positive control の matrix が逆行を検出する。

**決定 (4): 受理集合不変の証明は合成 matrix が担い、実履歴の全件一致は証拠にしない。**
実 repo の履歴は receipt が改竄されていない歴史なので、新旧の判定値は**両方とも全件 False** になり、
「全史で 0 差」は恒真な control になる。したがって positive control は合成 git 履歴上の 18 ケース
(M / D / rename の両方向 / symlink・submodule の typechange / 2 親・3 親 merge / root /
追加のみ / exact copy / 近似コピー / `duplicate_oid` 既定値 / 過剰検出しない正例 /
集約の error precedence / 空集合) を固定し、**`True` を返すケースが 1 件以上あることを
テスト自身が assert** して恒真化を防ぐ。

**却下した選択肢:**
- **`diff-tree --stdin` で 1 process に畳む** — 受理集合は完全に安全だが、process 起動は 0.02 秒未満と
  実測できたので節約は 1% 未満であり、D104 決定 (3)「効果を示せない機構は land しない」に反する。
- **pathspec `-- <path>` で限定する** — 300 倍速いが、rename/copy 検出が pathspec の外にある相手を
  見つけられなくなり、受理集合が変わる。
- **逆引き `git log -- <path>`** — 既定の history simplification が merge の片親を刈るうえ、
  copy 元としての出現を拾えない。
- **`--find-copies-harder` を外すだけ (OID 検査なし)** — exact copy の検出まで失われ、既存テストの
  期待値を「拒否」から「受理」へ反転させることになる。ユーザー裁定で退けた。
- **走査そのものを消す (直前の blob OID 一致検査で十分とする)** — 未変更 copy 元と外部親 merge は
  OID 検査を通るため冗長ではない。受理集合の縮小になるので採らない。

**研究状態への影響:** certified 選択・材料レポート・proof chain・凍結 bytes は不変である。
変わるのは freeze receipt 検証の受理集合のうち、上記 1 ケースだけである。
