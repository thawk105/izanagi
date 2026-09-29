## 1. 対応表

以下の「closed」は差分による静的判定です。fix 後のテスト・build は実行していません。

- **B1（patch 適用順）— closed。** 順序を `patch_order` 配列に保存し、再読込後もその順に適用する。hash は別に照合する。`orchestrator/campaign/vhash_cicada_hot_block.py:329,856–862`
- **A1 / B2（serializable を受け入れよ）— refuted-維持。** driver は `--protocol cicada --ccbench-root` を指定する。Cicada の証拠面では巡回 0 でも認証条件を満たさず、verdict は `indeterminate`、CLI の rc は 3 になる。`orchestrator/campaign/vhash_cicada_hot_block.py:529–550,642–648`、`orchestrator/verifier/model.py:77–82,510–519,554–567`、`orchestrator/verifier/cli.py:105–110`
- **A2 / B3（COUNT の extime）— closed。** COUNT と perf は 3 秒、trace と broken は 1 秒。`orchestrator/campaign/vhash_cicada_hot_block.py:383–391`
- **A3 / B5（build の二重計上）— partial。** smoke wall に build を再加算しなくなった。ただし新しい見積り差異を第 2 節に記す。`orchestrator/campaign/vhash_cicada_hot_block.py:158–185`
- **B4（共有失敗時の再 build）— closed。** 必要 binary の照合失敗で記録を残して停止し、再 build 経路はない。smoke は全 17 binary を事前照合する。`orchestrator/campaign/vhash_cicada_hot_block.py:831–848`
- **A4（B1 の changed 過大計数）— closed。** 元版と返す版を別ポインタと確認し、両方の status を `committed` に限定する。`deleted` は別 status なので元版の非削除条件も満たす。`patches/broken-cicada-vhash-stale-hot.patch:46–59`
- **A5（COUNT worker の false sharing）— closed。** `VHashStats` は `alignas(64)`。C++ の配列 stride も型の alignment の倍数になる。この定義は COUNT 条件内にあり、性能 build の前処理対象に入らない。`patches/cicada-vhash-hot-block-variant.patch:99–109`
- **B6（図の平均・95%区間）— closed。** 全点、中央値、最小〜最大へ変更された。`tools/plotting/plot_vhash_cicada_hot_block.py:59–92`
- **B7（README の旧壊し 3 本）— closed。** 対象を md_3 の旧 3 本と明記した。`patches/README.md:936`
- **focus-1 の条件 gate 登録テスト — closed。** 問題の一般化を外し、対象 macro を明示した。`orchestrator/tests/test_condition_meaning_gate.py:463,516,1582,1628`
- **focus-1 の perf file inventory — closed。** driver を登録した。`orchestrator/tests/test_official_perf_closure.py:47`
- **focus-2 の共有 ldd テスト — closed。** 記録済み依存 path と現在の ldd 解決 path を hash 照合より先に比較するため、ログの架空 `/lib/old.so` は指定の不一致として扱われる。`orchestrator/campaign/vhash_cicada_hot_block.py:353–380`
- **smoke1 の COUNT gate 拒否 — closed（静的）。** COUNT の DefineSpec に `CICADA_VHASH_K=1` の companion を登録し、test も pin した。実 gate の再走による確認はない。`orchestrator/campaign/condition_meaning_gate.py:268–272`、`orchestrator/tests/test_condition_meaning_gate.py:3627–3636`

## 2. 新しい所見

- **must-fix — trace job の見積りが裁定 §4 の式と異なる。** §4 は 2 job それぞれの走数を足すが、実装は多い側の走数を両 job に掛ける。全腕では `plan_trace` が 14 走と 5 走なのに、`2 × 14 × trace_wall` と見積もる。差は `9 × trace_wall`。放置すると 7,200 node 秒の境界で不要な縮小・投入停止が起き、成果物の round・cell・K が変わる。`orchestrator/campaign/vhash_cicada_hot_block.py:145–155,183–185`

共有照合の順序、B1 の条件、COUNT の alignment、companion の K=1 登録と test pin には、上記以外の新規欠陥を静的には確認しなかった。

## 3. 派生値の照合

- **「宣言 20 / 観測 8」:** patch 内の単独 `#if CICADA_VHASH_COUNT` 宣言 20 件は照合できた。K 未定義時の観測 8 件は、指定された focus ログには実測出力がなく**照合不能**。12 件が K 条件内にあるという裁定の説明とは整合する。`patches/cicada-vhash-hot-block-variant.patch:99–414`
- **「build 秒 8.8〜12.5」:** focus-1・focus-2 はテストログで、smoke1 の build 時間を含まないため**照合不能**。
- **「sizeof 256/320/384」:** driver が対象 target の compile flags で `sizeof(Tuple)` を測る経路は確認できた。値そのものの実測ログは指定資料になく**照合不能**。`orchestrator/campaign/vhash_cicada_hot_block.py:257–276,318`

## 総括

**NO-GO。** レビュー所見、焦点走の赤、smoke1 gate 拒否への修正は静的には閉じている。A1/B2 の refuted 裁定も driver の argv と verifier の verdict・rc 契約に合う。一方、trace 見積りの式が裁定 §4 と違い、縮小判断と成果物の範囲を変え得る。式の修正後、必要な gate・テスト・smoke で動作を確認する必要がある。