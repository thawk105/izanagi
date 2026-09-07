## 総括

静的レビューの結論は **must-fix 4 件、nit 1 件**です。推定量、seed の policy 2 限定配線、exact 軸への hash 付与、run identity、trace と性能の分離は概ね事前登録どおりです。

一方、認証 argv の受理集合と解析入力の build identity が fail closed になっていません。また、事前登録した M13/M14 変異を独立に赤くできないテスト構造です。

凍結値は現物と一致しました。

- 事前登録 SHA-256: `ee7617f57bf6816fd8bfb42b5830926be1174ebcca617ed122c3fbca62f127a6`
- patch C SHA-256: `794b7b48dd19e30560dddc27f4408d67923d801241046df53257a8aefe82a396`

pytest は指示どおり実行していません。

## 所見 1 — certify の直接呼出しが新しい seed argv を受理する

**主張:** `--step-policy-seed` が共通 parser に追加されたため、PBS は certify 分岐へ渡さなくても、driver の直接呼出しでは seed 付き certify が受理されます。exact 2 cell の値自体は維持されていますが、認証要求の受理集合は baseline より広がっています。

**根拠 (file:line):**

- 共通 parser が seed option を無条件に受理: `tools/pegasus/probes/t2187_adaptive_const_probe.py:2692`
- `main()` は seed を検査した後、そのまま certify へ dispatch: 同 `:3242`
- policy 2 を含まない認証 cell では `_validate_step_policy_seed` が何も拒否しない: 同 `:2788`
- `_certification_contract` に seed 非指定条件がない: 同 `:1182`
- PBS certify 分岐へ seed を渡していないことだけは固定済み: `tools/pegasus/probes/t2187_adaptive_const_probe.pbs:404`
- テストも PBS 分岐の非伝搬だけを確認し、直接 certify の拒否を確認していない: `orchestrator/tests/test_t2187_adaptive_const_probe.py:2193`

**境界:** 絶対規律 2 の正しさ境界。

**must-fix か nit か:** **must-fix**

**成果物影響 1 行:** 従来なら unknown argv で停止した seed 付き認証要求が、seed を無視したまま certified artifact を生成できます。

**提案:** `mode == "certify"` かつ `step_policy_seed is not None` を `_certify_main` 前で明示拒否し、直接 driver 呼出しの負例を追加してください。

**反証されたら何が変わるか:** exact cell 以外の無関係 option を認証契約が意図的に許すと示されれば nit に下げられますが、「certify argv は不変」という完了報告は修正が必要です。

## 所見 2 — genome 検査が部分集合検査で、基底 flag の変異を受理する

**主張:** 解析器は backoff 関連 flag の期待値だけを確認し、genome の flag 集合全体を exact に比較していません。`NO_WAIT_LOCKING_IN_VALIDATION`、`NO_WAIT_OF_TICTOC`、`WAL` の欠落・変更や任意の追加 flag を受理します。

**根拠 (file:line):**

- 実 driver の genome は `BASE` を必ず含む: `tools/pegasus/probes/t2187_adaptive_const_probe.py:155`、同 `:581`
- 解析側の `expected_flags` は基底 3 flag を含まない: `orchestrator/campaign/backoff_counterfactual_analysis.py:174`
- 検査は `expected_flags` の各項目だけを見る部分集合検査: 同 `:189`
- 成功 fixture 自体が基底 flag を省略している: `orchestrator/tests/test_backoff_counterfactual_analysis.py:55`

**境界:** 事前登録された build identity の正しさ境界。

**must-fix か nit か:** **must-fix**

**成果物影響 1 行:** 異なる CC compile flag で作られた binary の outcome が、事前登録どおりの run として ITT に混入できます。

**提案:** driver が生成する全 flag を期待集合へ含め、`flags == expected_flags` の exact equality にしてください。基底 flag の変更と余分な flag の追加を拒否する負例も必要です。

**反証されたら何が変わるか:** 解析前に別の信頼済み attestation が exact genome を必ず検証すると証明されれば統合上の nit に下げられますが、射影内にはその前提がありません。

## 所見 3 — 解析器が凍結事前登録と patch/build identity を検証しない

**主張:** `analyze_counterfactual()` は caller が渡した任意の事前登録 file の hash を正として扱い、成果物の ccbench pin、patch A/B/C、patch stack、trace binary count、repo binding を検査しません。

**根拠 (file:line):**

- 事前登録は exact ccbench pin と patch A/B/C hash を固定: `docs/backoff-counterfactual-preregistration.md:103`
- 成果物へ記録すべき identity field を列挙: 同 `:267`
- 解析器は任意の `preregistration_path` を hash 化して正本扱いする: `orchestrator/campaign/backoff_counterfactual_analysis.py:478`、同 `:491`
- top-level の期待値は axes と hash までで、patch/build identity がない: 同 `:258`
- row の binary 検査も 64 桁 hex の形だけ: 同 `:231`
- 成功 fixture は patch stack、ccbench pin、trace symbol/string count、repo identity を持たない: `orchestrator/tests/test_backoff_counterfactual_analysis.py:123`

**境界:** 凍結事前登録との束縛に関する正しさ境界。

**must-fix か nit か:** **must-fix**

**成果物影響 1 行:** 別 patch または別事前登録 bytes に由来する artifact が、v1 の確認的判定へ入力できます。

**提案:** v1 の凍結 SHA-256 を独立 pin として確認し、事前登録済みの ccbench commit、patch A/B/C hash、ordered patch stack、trace binary count と row/top-level の一致だけを検査してください。新しい一般 gate や台帳は不要です。seed 間で genome/binary の一致を要求してはいけません。

**反証されたら何が変わるか:** API が検証器ではなく、信頼済み入力専用の計算関数だと契約されていれば nit にできます。しかし docstring と完了報告はいずれも artifact を fail closed に検査すると述べています。

## 所見 4 — M13/M14 の定数変異が自己参照 oracle を通過できる

**主張:** CI critical value と等価域のテストが実装 module の定数を期待値にも使っています。したがって定数自体を変異させると実装と oracle が一緒に動き、事前登録した M13/M14 の独立な赤を保証できません。

**根拠 (file:line):**

- M13/M14 は 90% CI と `±ln(1.03)` の変異を赤にすると登録済み: `output/insights/2026-09-07_t2265-backoff-itt/verbatim/s4-ruling.md:93`
- 実装定数: `orchestrator/campaign/backoff_counterfactual_analysis.py:68`
- テストは critical value と半幅を同じ module 定数から導出: `orchestrator/tests/test_backoff_counterfactual_analysis.py:181`
- 境界テストも `margin = analysis.EQUIVALENCE_MARGIN` と自己参照: 同 `:315`
- `1.7958848`、`2.2009852`、`math.log(1.03)` の独立 pin はこの test file にありません。

**境界:** 正しさ境界に触る検査実効性。

**must-fix か nit か:** **must-fix**

**成果物影響 1 行:** 等価域または CI 水準が変わって確認的 decision が変化しても、焦点テストが緑のままになりえます。

**提案:** `EQUIVALENCE_MARGIN == math.log(1.03)`、`T90_DF11 == 1.7958848`、`T95_DF11 == 2.2009852` を module 定数から独立した期待値で固定してください。

**反証されたら何が変わるか:** 実際の変異実行で定数置換を含む M13/M14 が別 node により赤になる証拠があれば解消します。

## 所見 5 — source 全文の `pending` 禁止テストが裁定外

**主張:** 親は生成 field の exact hex を検査し、source 全文の `"pending"` 禁止は行わないと裁定しましたが、実装テストには全文禁止が残っています。

**根拠 (file:line):**

- source 全文禁止を scope 外とした裁定: `output/insights/2026-09-07_t2265-backoff-itt/verbatim/s4-ruling.md:31`
- 実際の source 全文禁止: `orchestrator/tests/test_t2187_adaptive_const_probe.py:2099`
- 生成値の exact SHA 検査は直前ですでに存在: 同 `:2094`

**境界:** 整合・scope の問題。現在の成果物正しさには触れません。

**must-fix か nit か:** **nit**

**成果物影響 1 行:** 現在の artifact bytes は変わりませんが、無関係な説明文への単語追加でテストが赤くなります。

**提案:** 全文 scan だけを外し、生成 metadata が exact 64 文字小文字 hex である検査を残してください。

**反証されたら何が変わるか:** s4 後に全文禁止を採用する新しい裁定があれば所見を撤回します。

## 事前登録との照合表

| 項目 | 判定 | 照合結果 |
| --- | --- | --- |
| seed 配線 | 適合、一部境界不適合 | policy 2 のみ可変 seed、policy 0/1 は既定 seed。cell literal に seed なし。PBS は performance へ 1 回だけ渡す。ただし直接 certify の受理集合は所見 1 |
| hash 付与範囲 | 適合 | exact 3 腕、workload、threads、rep、reps、extime、trace を全て比較。各軸をずらす負例あり |
| top-level / row | 適合 | 解析時に両方を凍結 file hash と比較。policy 2 row だけ seed を保持 |
| `pending` | 生成不能 | driver の生成経路には残っていない。全文禁止テストだけが scope 外 |
| 絶対規律 2 | 部分不適合 | exact 2 cell、patch A hard pin、既存 validator 本体は差分なし。直接 certify argv の拡大が所見 1 |
| 絶対規律 1 | 適合 | hash は trace 有効時だけ。trace-disabled build の除去検査あり。解析出力に `median_tps` 比較なし |
| run identity | 適合 | `cell literal, seed, binary_sha256` を出力し、seed 間の genome/binary 一致を要求していない |
| build identity の入力検査 | 不適合 | genome exactness は所見 2、patch/prereg binding は所見 3 |
| 主推定量と判定 | 実装値は適合 | 次窓、最後の割当除外、run 等重み、zero commit・片腕欠落・12 未満 inconclusive を実装 |
| 変異事前登録 | 部分不適合 | M1〜M12、M15、M16 の対応は確認。M13/M14 の独立 oracle が不足 |
| scope | 概ね適合 | CLI、glob、最新 artifact 選択、性能比較、新 ledger なし。既存 deferred sink 行は `3013` / `3382` に追随 |

## 見つからなかったもの (探したが無かった)

- seed が cell literal へ混入する経路
- 明示 seed による policy 0/1 genome の変化
- PBS certify 分岐への seed argv 伝搬
- 軸を 1 つずらしても事前登録 hash が付く経路
- top-level と row で異なる事前登録 hash を解析が受理する経路
- 生成 field に `"pending"` を出す経路
- exact 2 certification cell 自体の拡張
- patch A hard pin の変更
- `_validate_backoff_trace_contract` 本体の変更
- trace instrumentation が trace-disabled build に残る新経路
- 解析 module による `median_tps` の腕間比較
- 12 artifact 間で genome、buildcache key、binary SHA の一致を要求する処理
- 公開 CLI、glob、最新 artifact 自動選択
- deferred gate 台帳への新規 sink 追加や行番号の取り残し