# [T-360] 変異本走 transport と汎用コマンド送出を投入表の task として実装する

wave: `dev-wave-t360-mutation-transport-task` / branch `worktree-dev-wave-t360-mutation-transport-task`
base main: `53c61414` → 前方取り込みで `15134faa`

## 何を納めたか

`tools/pegasus/dispatch_compute.py` の `TASKS` を `{tests, provenance}` から
`{tests, provenance, mutation, generic}` へ広げた。D105 決定 3 の閉集合を supersede する。

- `mutation` = 変異 wrapper 1 呼び出しを計算ノードの 1 job へ束ねる。既存 dispatch 経路と並存。
- `generic` = 任意 argv を `shell=False` で計算ノードだけで実行する。

あわせて D117 決定 4 の 4 契約を同じ変更単位で満たした (D105 supersede、子側の環境 allowlist
全キー強制、stdin / cwd / artifact 可視性、子 rc の意味)。

## 実測

| 項目 | 値 |
|---|---|
| 焦点走 (8 file) | 1686 passed / 5 skipped / rc 0 |
| 変異 matrix | baseline PASSED・7/7 KILLED・SURVIVED 0・MISMATCH 0 |
| 汎用 task の dogfood | bnode011 で実行・子 rc 7 が伝播・stdin 非 TTY・cwd = repo root |
| 変異 task の dogfood | 投入 1 回で baseline PASSED + 変異 1 件 KILLED (従来経路なら 3 回) |

## 成果物の主張の限界 (ここを読まずに引用しない)

- **「変異本走を 1 ジョブへ束ねた」は無条件に成り立たない。** 束ねが成立するのは、変異対象が
  runner 実行経路 (`tools/run_tests.py` / `tools/pegasus/dispatch_compute.py`) を含まず、
  selector を要さず、attempt 対応証拠を要さない入力に限る。
- **attempt 対応の永続証拠は束ね経路では成立しない。** 束ねた job の内側は local になるが、
  wrapper と harness は local と attempt pair の同時指定を無条件に拒否する。残すと停止し、
  落とすと証拠を失う。**恒久 transport の要件は未充足である。**
- **共有 lock の移行は task 経路についてだけ閉じた。** harness の直接起動は共有 lock を通らない。
- **hook の綴り依存は未修正。** hooks subtree は guard 自身が編集を拒否するため、
  通常の wave では直せない。

## 記録に残す認識の誤り

- 親は段 1 で「汎用 task は作らない」を暫定裁定したが、汎用 task の追加を明示的に決めた
  後発のユーザー裁定を見落としていた。段 3 の敵対レンズが発見した。
- 親は段 4 で「hook を広げる変更」と書いたが、実測は逆だった。現行 hook は
  `--task <任意> -- <重量コマンド>` を既に許しており、本 wave 以前から在る穴である。
  実際に未知 task を止めているのは dispatcher の閉集合である。
- 親の裁定文が内部矛盾していた (束ね文脈で attempt sidecar を許すと書きながら、
  実装子へはその制約を緩めるなと指示した)。段 6 のレビューが検出した。

## 変異 matrix の経緯 (erratum)

3 走している。**1 走目と 2 走目の結果は消さない。**

1. 期待 node に parametrize 引数を書いておらず、harness が起動前に fail-closed で停止した。
   変異は 1 件も走っていない。
2. 期待 node を部分集合で登録したため M3 / M4 / M5 が MISMATCH。ただし 3 件とも
   「期待した node が落ちなかった」のではなく「期待より多く落ちた」もの (25 / 16 / 2 node)。
   検出力は登録より強かった。
3. 観測した完全集合で再登録し 7/7 KILLED。`mutation-ledger.json` は 3 走目のものである。

## 逐語

`verbatim/` に段 1 の brief、段 2 のプラン、段 3 の敵対相談 2 本、段 4 の裁定と 2 度の修正、
親の追加実測 2 本、段 5 の実装子 3 本、段 6 のレビュー 2 本・fix 3 本・merge 合成監査を置く。
