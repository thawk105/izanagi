## 所見対応表

根拠中の「生成器」「test」は、それぞれ指定の `plot_b10_waiting_grid_forest.py`、`test_plot_b10_waiting_grid_forest.py` を指す。

| id | 判定 | 根拠 |
|---|---|---|
| A-1 | closed | figures/README「入力」が「Holm 3 行の値」と「cell effects 36 行の行数」を明確に区別し、生成器 `_authority_data` と一致。 |
| A-2 | not-adopted | 親の refute は正しい。producer 逐語 L1895–1900 と生成器 `_relation` は、分類名・inside の `>= / <=`・outside の `< / >` が同一。 |
| A-3 | not-adopted | 裁定どおり epoch 定数を維持。`validate_repo_closure` が外部受領証を読まず report field を再構成する契約も不変。 |
| A-4 | not-adopted | 裁定どおり panel 題を維持。着地 PNG で題・凡例・追加脚注の重なりや切れは認めない。 |
| A-5 | closed | tools/plotting/README 末尾が用途・command・入力・出力・fig13 正本参照へ縮約され、同 README の `FIGURE_CONVENTIONS.md` 参照も残存。 |
| A-6 | partial | `s6-adjudication.md` で m4 再照準と m13a/m13b 分割は確定したが、新 anchor の赤 node 集合・検出理由の確定は変異 final に残る。 |
| B-1 | closed | `_authority_data` の条件検査、`measurement_conditions`、`_caption`、`make_figure`、日英 caption に必要な条件を追加。原 JSON・着地 PNG・SHA を照合できた。 |
| B-2 | closed | `test_relation_boundaries_match_producer_rule` の7ケースは producer と一致し、`test_cell_interval_on_margin_edge_is_inside` は実際の `load_evidence → _authority_data → _relation` を通る。 |
| B-3 | closed | A-1 と同じ README 修正で、Markdown の値照合と行数照合の境界が明確になった。 |

B-1 の実値照合結果は以下のとおり。

| report JSON の出所 | 実値・照合結果 |
|---|---|
| `calibration.records` | `1000000`。provenance・日英 caption・PNG の「1,000,000」と一致。 |
| `calibration.threads` / `spec.execution.threads` | 両方 `48`。実装は両者と定数48の一致を要求。 |
| `spec.workloads[].ycsb_zipf_skew` | `"0.9"` × 3。全 workload を検査し、表示値とも一致。 |
| `spec.workloads[].ycsb_rratio` | write-heavy / balanced / read-heavy の順に `"5" / "50" / "95"`。caption と脚注の対応順も一致。 |
| `ycsb_rmw` / `ycsb_max_ope` | 全3 workload で `"0"` / `"10"`。検査・provenance・caption と一致。 |
| `spec.execution.extime_s` / `performance_reps` | `3` / `5`。「3 秒」「3 s per repetition」「5 reps」と一致。 |

日本語 caption と拒否条件は実装に整合する。README「作図規約への適合」§6 の「測定条件は図の脚注と caption …にも出す」はやや広い表現で、**脚注は主要条件、rmw・max operations・秒数まで含む全条件は caption** に出る。必須の records・skew・threads・env は両方にあり、B-1 の解消を妨げないが、この区別を明記すると正確になる。

B-2 の7ケースは、順に inside / inside / overlaps / overlaps / outside / outside / overlaps で正しい。fixture の上端は算術照合でも **ちょうど `0.03`**。record・対差・cell・Markdown を同期して再封印しているため、端点分類より前の不整合で落ちるだけのテストにはなっていない。

## 回帰

**実装・値・限定の回帰は認めない。**

- 固定文8文は変更されず、着地 caption に全件存在する。禁句テストの8文字列も検出なし。新しい `Conditions:` は測定条件の転記だけで、事前登録 §3 の主張範囲を広げていない。
- 差分では描画本体・`artist_series` は不変。PNG は axes 3、各 μ 6行、±3%帯、参照空丸18、境界跨ぎの四角4を維持し、脚注の records・Zipf・rratio も読める。
- `validate_repo_closure` / `validate_external_sources` の契約、入力 pin、既存 key の削除・改名はない。条件 field が追加され、生成日時・generator SHA・画像 SHA・caption は再生成に伴って更新されている。
- tracked入力3件・生成器・画像2件の SHA は着地 provenance と一致。README の着地 SHA 3行と英文 caption も現物に一致。
- tools/plotting/README の fig13 正本参照と作図規約参照は残っている。

本レビューでは pytest・生成・変異を実走していない。親の「53 passed・再生成 rc=0」は報告として扱い、上記は静的読解・JSON/算術/SHA照合・画像確認による判断である。

## 変異への所見

以下は final での観測方針であり、今回の KILLED／SURVIVED 実測ではない。

| 変異 | 所見 |
|---|---|
| m0 | コメント変更の全 suite 対照が必要。焦点 closure test の生存だけで全 suite SURVIVED としない。 |
| m1 | pin 変異は既存の実 repo 読込・稿との pin 照合が対応。新 anchor で再確認する。 |
| m2 | receipt SHA 検査削除は専用負例が対応。追加変異は不要。 |
| m3 | 対差順序の変異は逆順負例が対応。追加変異は不要。 |
| m4 | 定数を保持し、CI 式の係数だけ `1.96` にする。`cell interval recalculation` での拒否を観測する。 |
| m5 | relation 照合削除は既存負例が対応。端点比較4方向の変異は別枠で追加すると B-2 の検出範囲を記録できる。 |
| m6 | Holm 再計算は Markdown 同期済み負例が対応。別層の拒否との混同を避ける。 |
| m7 | 固定文削除は独立した逐語期待が対応。追加条件文の欠落と混ぜない。 |
| m8 | 無効化する重なり検査 block を固定し、通常 Figure の成功と重なり注入後の差を観測する。 |
| m9 | constant の effect / low / high を個別に扱う既存負例でよい。 |
| m10 | top-level と record の検査削除を区別する。一括削除を単独理由の証拠にしない。 |
| m11 | identity 集合を保った重複族の負例が対応。追加変異は不要。 |
| m12 | raw p・Holm・Markdown を同期した負例が対応。分母整数性の検出として記録できる。 |
| m13a | 曝露検査削除を9999の負例で検出する。10000正例とは観測を分ける。 |
| m13b | `>= → >` を10000正例で検出する。通常 fixture 全般が赤なら裁定どおり過剰決定として境界感度の別枠に置く。 |
| m14 | prefix 緩和は `fig_invalid` / `fi13_invalid` の既存負例が対応。追加変異は不要。 |

追加条件検査について：

- **records：追加必要。** 検査削除を999999負例で再 probe し、fix1 の直接呼出し結果を final の証拠へ接続する。
- **threads：追加必要。** 検査全削除は47負例で検出できるが、現負例は calibration 側だけ。execution 側だけの不一致と、両方47の入力もあると、連鎖比較の各条件を区別できる。
- **skew：追加必要。** 検査削除に加え、第2・第3 workload の単独変更があると「先頭だけ検査」への退行も検出できる。
- **rratio：追加必要。** swap 負例は全検査削除に対応する。第3 workload の単独変更も加えると3件すべての対応づけを検証できる。

fix1 の4件 KILLED は有用な予備証拠だが、部分的な検査削除まで検出した証拠には拡張しない。

## 総括

regressed **0件**、partial **1件（A-6：変異 final の検出理由確定待ち）**。
B-1 / B-2 と採用された docs 修正は解消し、原データ・条件表示・着地 SHA は整合する。
判定は **GO：修正版を採用し、変異 final へ進めてよい**。
最終完了の宣言には、A-6 の新 anchor 観測と追加条件変異の記録を残す必要がある。