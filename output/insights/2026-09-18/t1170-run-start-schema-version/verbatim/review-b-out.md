## must-fix 所見

なし。現行 producer が v4 の時点で受理集合は不変。certified 選択、report の値、既存台帳の参照を変える実装差分は認めなかった。

## nit 所見

1. **F332 追記の分類説明が v4 まで拒否するように読める。** [frag-failures.md:11](/home/SFC/tanab/.claude/jobs/816f08f2/tmp/wave/frag-failures.md:11) の「v3 は `legacy`、他は `unknown` として fail-closed」は、対応版 v4 の除外と版 gate 到達条件を省略している。実装では v4 は既存の後続検査へ進む。

2. **D2064 の適用範囲を広く記述している。** [frag-decisions.md:44](/home/SFC/tanab/.claude/jobs/816f08f2/tmp/wave/frag-decisions.md:44) は「v3 decoder / alias」をまとめて D2064 決定3違反としている。しかし逐語の禁止対象は role payload の旧 throughput 名を受理する alias（`rulings-verbatim.md:73–80`）。run-start の歴史 decoder 一般を禁止する裁定ではない。本件で作らない根拠はユーザーの scope 指定と、D1669 の読み手確認条件で足りる。

3. **読み手探索の範囲が記録されていない。** [frag-decisions.md:29](/home/SFC/tanab/.claude/jobs/816f08f2/tmp/wave/frag-decisions.md:29) は「確認できない」と限定しており不在の断定ではないが、段4裁定が指定した「直接参照の検索」の限定も残すと正確になる。

## 依頼文 3 句と実装行の対応表

| 依頼文 | 実装・検証箇所 | 判定 |
|---|---|---|
| 世代を分け | consumer `autonomous_trial_completeness.py:428–429` の独立リテラル、`:2242–2254` の比較・診断。テスト `:2987–3000` は producer 定数だけを変えて独立性を検査 | 適合。run-start の版判定を分離している |
| 旧版として読む | consumer `:2244–2248` は実在確認済みの v3 のみ `legacy`、他の非対応版は `unknown`。テスト `:2954–2971` は旧形13 key の記録を明示的に拒否 | 適合。旧版と識別して拒否し、現行形へ変換しない |
| 互換層は足さず | consumer `:2243–2254` は非対応版を即時拒否。alias、decoder、fallback の追加なし | 適合。新 gate・一般化・機械可読属性の追加もない |

`git diff main..HEAD` は consumer とそのテストの2ファイルのみ。producer の差分は空で、現行 `SCHEMA_VERSION` は `p3_autonomous_workload_trial.py:142` の v4。run-start は同定数を `:5107` で使用する。

## docs 案への訂正

- **F332追記11行の置換案：**
  「版 gate に到達した非対応版は、v3 を `legacy`、それ以外（欠落を含む）を `unknown` として拒否する。対応版 v4 は従来の field 検査へ進む。」

- **decisions案44行の置換案：**
  「v3 decoder / alias を足す — 本件の依頼範囲外であり、歴史 decoder は D1669 の読み手確認条件も満たしていない。D2064 決定3の alias 禁止は role payload の旧 throughput 名を対象とする。」

- **decisions案29行の補足案：**
  「今回の直接参照検索で、v3 の歴史 decoder を必要とする読み手を確認できていないため作らない。」

その他の主要記述は実体と整合している。

- **v4 利用・v5 不要：** `4c6f03048` による共有定数の v3→v4 変更を確認した。既存の版境界を利用し、今回新たな形変更がないという理由付けは妥当。D1851 を「形変更のない bump の禁止」としていない点も正確。
- **形の説明：** producer `:5105–5140` は無条件14 key と条件付き7 key を作る。journal の seq/ts を含めて非binding16 key／binding23 key という段4裁定に一致する。
- **「構造化」の範囲：** decisions案28行は文言への明示であり機械可読属性ではないと正しく限定している。
- **診断の到達条件：** decisions案30–31行は適切。実際に journal hash・順序等の検査と report 版検査が先行する。
- **実装子報告：** 変更箇所、4テスト追加、共有fixture・producer無変更の説明に食い違いなし。author の295 passed は提示された別走行の報告として扱い、今回独立に再確認した結果とはしない。

## 裁定パッケージ候補 (scope 外)

以下は将来具体的な利用要求が生じた場合の論点であり、本差分へ混ぜていないことを確認した。

- run-start と role payload が共有する producer の schema 定数・系列を分離するか。
- v3 の歴史閲覧需要が実在した場合に、生成時コード・契約と D1669 の条件をどう適用するか。現行受理集合の拡張は提案しない。
- run-start field を直接読む registry／receipt 経路について、版検査の責任を別途整理する必要があるか。今回追加 gate を要求する根拠はない。
- 同じ v3 内の歴史的な形の混在をどう説明するか。既存記録の書換えや今回の decoder 追加は行わない。

## 総括

**実装は段4裁定と依頼に適合。docs は上記3点の表現訂正を推奨する。**

旧 run-start 拒否文言や新定数を pin する他の test・docs・contract JSON の取り残しは、検索範囲で見つからなかった。contract JSON の参照先関数も変更されていない。

焦点走の dispatch request は直接・間接 consumer を含む指定14ファイルを列挙し、[focus-run.log:21](/home/SFC/tanab/.claude/jobs/816f08f2/tmp/wave/logs/focus-run.log:21) は **1638 passed、5 skipped**、child rc=0 を記録する。5件は既存の growth hold による未実行で、成功扱いにはできない。冒頭のローカル走行はメモリ上限到達で終了しているが、本差分の機能回帰を示す assertion failure はなく、計算ノードでの再走は成功している。これは焦点走の結果であり、受入全走の完了を示すものではない。