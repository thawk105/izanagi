---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-18
wave: dev-wave-t1311-arm-authority
seq: 2
---

## {{D:arm-execution-digest}}. arm authority は実入力 bytes の二層 digest で作る

**決定:** arm (`on` / `off` / `swapped`) の authority は、arm が選んだ**実入力 descriptor の
canonical bytes** から次の二層で導く。

- `content_digest = SHA256(canonical_execution_input_bytes(selected_descriptor))`
  — arm 名・holdout 名・trial ID・path・campaign ID を preimage に含めない
- `arm_binding_digest = SHA256(domain_separator || holdout || arm || content_digest)`

加えて、同一 holdout の 3 arm の `content_digest` が相異なることを launch 前に要求する
(pairwise 非同一検査)。解決不能な arm は起動を拒否し、`on` への fallback や空 descriptor を作らない。

**理由:**
- 一層目に arm 名を混ぜると、同一 bytes に別 label を付けただけで digest が変わる。
  「digest が違えば実入力が違う」という含意が崩れ、label の自己申告を信じることになる。
- 二層目が無いと、resolver 退行で 2 つの arm が同一 bytes へ潰れた場合を検出できない。
  一層目だけでは、その状態でも各 arm の digest は「正しく」一致する。
- pairwise 検査が無いと、二層目があっても潰れた実験が 6 cell として受理される。
  6 cell 比較が実質 4 cell 以下になったまま緑になる。

**却下した選択肢:**
- 実行 report へ宣言 arm を書き戻して照合する形 — 宣言値どうしの往復であり定義上恒真。
  ユーザー裁定が明示的に不採用としている。
- arm 名を含めた単層 hash — 同一 content への label 交換を識別できるが、
  producer と verifier が同じ manifest label を読む限り再び恒真になる。
- report へ nested record として arm label を戻す形 — 往復照合への誘導になるため、
  record には入力 schema 版と 2 つの digest だけを置く。

## {{D:off-neutral-input-projection}}. `off` の中立入力は projector 経由で生成し 2 根拠で束縛する

**決定:** `off` arm の「凍結済み中立入力」は、手書き literal ではなく既存の descriptor projector を
通して生成する。生成器は値の根拠を実 module から読んで照合し、不一致なら literal を書き換えず失敗する。

- 中立点 = 凍結 holdout 端点の read ratio の算術中点であり、かつ同 module が
  `rr50-positive-control` として既に凍結している軸値と一致すること
- skew / rmw / scale / objective / correctness は holdout 間で完全一致する共通値を複製すること
- canonical bytes は 281 bytes、sha256 は
  `8ecce69906410c451aa20a242634ba8ce82525636ed912493af6d12487340e89`

**理由:**
- 手書き literal だと `source` field が `human_declared` になり、`on` / `swapped` の
  `campaign_search_config_projection` と**一 field で区別できる**。role がその 1 語を見れば
  自分が対照 arm にいると分かり、descriptor 非使用対照としての blind 性が壊れる。
- projector を通せば `source` が一致し、入力の見た目から arm が漏れない。
- 中立値の非恣意性は 1 本の根拠では担保できない。中点だけなら「なぜ中点か」が残り、
  凍結定数だけなら「なぜその定数か」が残る。2 本が一致することを生成器に確かめさせる。

**却下した選択肢:**
- `null` や field 欠落で「descriptor 無し」を表す — payload schema が arm 別に分岐し、
  構造そのものから arm が漏れる。
- 中立入力を workload ごとに変える — 固定中立入力という規範に反し、
  off arm 間で入力が揃わなくなる。

## {{D:new-gate-must-not-preempt-existing-diagnostic}}. 新設 gate は既存診断の優先順位を奪わない

**決定:** 既存の検査が pin している診断より前に新設 gate を発火させてはならない。
両者が同じ変異で同時に成立する場合は、**新設 gate の呼び出し位置**を既存検査の後段へ移す。
既存テストの期待診断を書き換えて辻褄を合わせること、および既存検査を新設側へ重複させることを禁じる。

**理由:**
- 既存テストが pin しているのは「どの層が何を理由に拒否するか」という構造であり、
  拒否されること自体ではない。診断が入れ替わると、その構造の主張が黙って失われる。
- 新設側へ既存検査を重複させると、合成 fixture が両方の検査を同時に満たす必要が生じ、
  fixture が構造的に噛み合わない場面 (探索形の golden に正式形の宣言を差し込む型の検査) で
  必ず赤になる。そこで fixture を歪めると、元の検査の意図が壊れる。
- 呼び出し位置の移動だけなら、検査項目を 1 つも減らさずに順序を確定できる。
  ただし移動先が 1 経路だけだと他の呼び出し元から検査が消えるため、
  **移動後に全呼び出し経路を列挙して被覆を確かめる**ことを手順に含める。

**却下した選択肢:**
- 既存テストの期待正規表現を新診断へ合わせる — 既存の設計主張の反転にあたる。
- 新設 gate を既存検査の内部へ重複実装する — 上記のとおり合成 fixture を壊す。
- 新設 gate の適用条件を緩めて発火しにくくする — 検出力を落とす方向であり規律 2 に反する。
