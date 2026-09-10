# 変異本走の裁定 — [T-342]+[T-343]+[T-344]

本走 = `mutation-ledger.json` (repo_head `44f080be9f1f4ddae27a8c379ac44cd12d42d870`、
baseline PASSED、Pegasus gen_S 計算ノード)。事前登録は `mutation-spec.json`。

**集計: registered 12 / completed 12 / KILLED 7 / MISMATCH 5 / SURVIVED 0 / TIMEOUT 0。**

`SURVIVED 0` が最重要の結果である。登録した 12 変異はすべて検出された。MISMATCH は
「殺せなかった」ではなく「赤くなった test node の集合が事前登録と食い違った」という意味であり、
`DW-M08` に従って親が以下のとおり裁定する。**初回結果は消さず erratum として残す** (`DW-M02`)。

## 裁定表

| ID | harness 判定 | 親の裁定 | 根拠 |
|---|---|---|---|
| M01 | MISMATCH | **real kill・単一理由** | 登録 2 node のうち実際に赤くなったのは `test_dirty_noop_does_not_derive_stock` の 1 件だけ。登録が過大だったのであり、単一理由性はむしろ登録より強い。erratum: 期待 node を 1 件へ絞る |
| M02 | MISMATCH | **kill 確認・帰属不成立** | 登録 1 node に対し実測 89 node。repo 正本 pin の照合を外すと stock 導出が広範に壊れ、受理集合が**開く方向でなく閉じる方向**へ動く。gate の歯を示す証拠にならないため再照準が要る |
| M03 | KILLED | real kill・単一理由 | 実測が登録と exact 一致 |
| M04 | KILLED | real kill・単一理由 | 同上 (2 node、いずれも legacy key の class 束縛) |
| M05 | KILLED | real kill・単一理由 | 同上 |
| M06 | KILLED | real kill・単一理由 | 同上 |
| M07 | KILLED | real kill・単一理由 | 同上。段 6 レビュー 2 が「mask されている」と静的に予測した変異だが、再照準後は実測で単一理由に落ちた |
| M08 | MISMATCH | **kill 確認・帰属不成立** | 登録 5 node に対し実測 65 node。campaign preimage から policy を外すと全 campaign ID が変わるため、identity を pin する検査が一斉に赤くなる。再照準が要る |
| M09 | MISMATCH | **real kill・単一理由** | 実測 2 node のうち 1 件は登録どおり。追加の `test_unlisted_post_policy_receiptless_terminal_is_denied` は**同じ不変条件 (receipt 欠落 terminal の拒否) を別入口で見る node** であり、二つ目の理由ではない。erratum: 期待 node に追加する |
| M10 | KILLED | real kill・単一理由 | 実測が登録と exact 一致 (6 node、いずれも overlay の deny)。**T-344 の中核が実測で殺されたことの証拠** |
| M11 | MISMATCH | **kill 確認・要追試** | 登録 1 node は赤くなった。加えて `test_codex_worker_launch.py` の 2 node が赤くなっており、差分が到達しうるか静的に説明できていない。`DW-O18` に従い、単独再走で再現性を実測してから実装差分へ帰属させる。本走では帰属を保留する |
| P01 | KILLED (正例) | **正例として成立** | 登録どおり `test_stock_machine_and_opted_in_coder_paths_remain_accepted` と `test_public_sweep_reaches_pipeline_with_exact_stock_and_machine_classes` の 2 node が反応した。clean stock・registered machine sweep・opt-in coder の 3 経路が gate の変更に対して敏感であることを示す |

## 何が実証されたか

- **T-343 の 4 identity 面はいずれも実測で歯を持つ。** legacy key (M04)、legacy sidecar (M05)、
  v2 preimage (M06)、completion manifest (M07)、campaign preimage (M08)、replay の receipt 照合 (M09)
  がすべて検出された。
- **T-344 の overlay は実測で歯を持つ。** M10 は overlay の deny 分岐を無効化すると、
  実 3 campaign を使う 6 つの consumer 入口 (overlay 直接・移設後・critic・Layer 3・S6・S8a) が
  同時に赤くなることを示した。
- **T-342 の capability 導出は実測で歯を持つ。** M01 (tracked_clean)、M03 (parser 発行 token) が
  それぞれ単一理由で検出された。

## 何が実証されていないか

- **M02 と M08 は帰属不成立**である。殺せてはいるが、無効化した不変条件が suite 全体に load-bearing で
  あるため、赤の理由が一つに絞れていない。「gate が受理集合を守っている」証拠としては使えない。
  再照準した変異を別途走らせる必要がある。
- **M11 の追加 2 node は未説明**である。再現性を実測するまで実装差分へ帰属させない。
- 再照準と追試はいずれも計算ノードの全走を要するため本 wave では行わず、後続へ送る。
  本走の結果は上記のとおり erratum 付きで凍結する。
