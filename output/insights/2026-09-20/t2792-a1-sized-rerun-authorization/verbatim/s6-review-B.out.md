## 判定と確認範囲

**現状の land は NO-GO。must-fix は 1 件です。** 認可機能自体の受理集合に逸脱は見つかりませんでしたが、既存の spawn-site 検査への波及が未修正です。

指定資料・適用後コード・呼び手を静的に照合しました。pytest、変異、ファイル書き込みは実施していません。以下の driver／paired test／job test は、指定された 3 ファイルを指します。

## must-fix

**MF1：driver の行移動で既存の spawn-site 照合が失敗している。**

- **根拠：** `focus/selfharness-post-s5.log:218–222` は `test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink` の失敗を記録しています。ログ中の登録位置は `run_measurement:7428`、適用後の該当 `run_campaign` は driver **7549 行**です。差は今回の前方への追加 121 行と一致します。
- **放置時の影響：** 既存の実行箇所を照合できず、関連検査が赤のまま land されます。
- **是正案：** 親の統合作業で、当該登録とその exact 期待値の位置だけを最終コードに合わせて更新してください。sink の種類・scope・件数を弱める変更や、検査の削除は不要です。行番号は残りの修正後に確定してください。

もう一つの失敗 `test_existing_a1_non_touch_manifest_is_empty_from_base` は、ログ上では今回の 3 ファイルが未 commit であることによる作業木チェックの失敗です。固定された過去の範囲比較が失敗した記録ではありません。こちらは検査を変更せず、commit 後に確認する対象です。

## should

該当なし。成果物への影響を示せない削減・報告上の改善は、以下の nit としました。

## nit

**N1：digest helper 内の supplied digest 検査は重複している。**

- **根拠：** driver **2995–2999 行**。reader は **2700–2710 行**で文字列型と SHA256 形式を検査してから helper を呼び、producer は digest 未付与の record を **3508 行**で渡します。
- **放置時の影響：** 現行呼び手の受理集合・record bytes・公開先・変異検出力は変わらず、検査が重複します。
- **是正案：** helper は digest field の除去と canonical hash 計算だけに縮められます。reader の形式検査は残すため、M8 の一理由性も維持されます。

**N2：malformed record の duplicate ケースは過剰決定されている。**

- **根拠：** paired test **4538 行以降**の `duplicate` は、`study_id` 二つだけの JSON です。duplicate-key 拒否を外しても、必要 key 不足で driver **2699 行**が拒否します。
- **放置時の影響：** 現在の受理集合は変わりませんが、このケースを「duplicate-key 拒否の独立した検出力」とは数えられません。
- **是正案：** 他は正常で digest も正しい record に同値の重複 key だけを入れて再照準するか、当該ケースを削除してください。削除しても登録済み M1〜M14 の検出力は失われません。

**N3：producer の既存 record 拒否は二つの test で重複している。**

- **根拠：** paired test **4604–4615 行**の再作成拒否と、**4636–4651 行**の namespace `[record]` は、同じ事前検査を通ります。後者の不正 bytes は producer が解析しません。
- **放置時の影響：** 現行の producer では同じ存在拒否・bytes 保持を重ねて検査します。
- **是正案：** 段 4 が namespace の三ケース統合を指定しているため、無条件削除より整理対象です。削減するなら `[record]` を外し、初回生成・再作成拒否・bytes 保持・M13 は `is_create_only` に集約できます。intent／attempt root のケースは残します。

**N4：dogfood log 単独では複製手順と field の現物照合までは追えない。**

- **根拠：** `replica-dogfood-post-s5.log:1–14` は入力ラベル・結果・base の entry 名だけを記録しています。
- **放置時の影響：** gate の受理／拒否結果は読めますが、「実 base から何を複製し、どの絶対 path／digest を調整したか」は再確認できません。
- **是正案：** 親の報告では証明範囲を限定してください。既存の複製スクリプト・入力資料があるなら参照を付けるだけで足り、新しい台帳や gate は不要です。

## 過剰・削除・helper 再利用

今回の次の要素は、**段 4 が明示採用しており、author 独自の過剰追加ではありません**。

- 一件の `frozenset` と prior attempt の固定。
- reader／digest helper の分離。
- unsafe／corrupt／differs の区別。
- 公開先の全 None／部分指定／全指定の処理と base 検査。
- create-only producer、既存 base 要求、directory fsync。
- 新 test の「受理／拒否」docstring。

複数 record の走査、可変 registry、将来 attempt の管理機能は追加されていません。producer argv の `--decision-item` も D2172 **項 2**と段 4 の P4 に対応しており、名指しを超える入力ではありません。

既存 helper は適切に再利用されています。

| 対象 | 判断 |
|---|---|
| `_submission_intent_digest` | そのまま流用不可。除外 field が `intent_sha256` なので record digest が変わる。汎用引数化より、短い専用 helper を維持する方が局所的 |
| `_exclusive_write` | producer が既に使用。事前存在検査の代わりにするだけでは、裁定済みの拒否メッセージと M13 の構造が変わる |
| `_validate_attempt_root` | producer／公開先が既に使用。これは既存の実 directory を許すので、producer の root 不在検査は代替できない |
| reader | submit と materialize の共通照合。片方へ inline 化すると重複するため、削除理由なし |

受理集合と test 検出力を保つ確実なコード削減は N1 です。reader の型・形式検査を広く削る案は、拒否区分や直接呼出しの挙動まで変えるため勧めません。

## 配線・dogfood・既存 caller

**配線 test は段 4 の B1 を満たしています。**

job test **3336 行以降**は実 `run_submit` → 実 reader／rear gate → 実 `_v3_group_intent` → intent の create-only 書き込み → `_run_qsub` 捕捉を通ります。driver **3311–3323 行**で gate、intent 作成、書き込みの順序を確認でき、test は qsub 三回と intent file を確認しています。

fixture の stub は author の報告と一致します。policy-ready、CCBench、git、durable base、hostname に加え、qsub と qstat visibility が差し替えられています。したがって証明対象は **scheduler 境界までの配線**です。実 scheduler の受理、fresh submit-tree の全前提、測定成立の証明ではありません。

dogfood log は明確に次を示します。

- record 不在：`group rerun is prohibited`
- exact record：`ACCEPTED`
- source／study／attempt／decision／digest 等の不一致：拒否

実 reader／gate を使った記録という前提では、exact record の受理は、訪問した先行証拠が gate の field 検査を通ったことと整合します。ただし複製内容そのものの証明限界は N4 のとおりです。これは qsub 到達の代替にはなりません。

**既存 test の期待値変更はありません。** diff の既存 test の削除行は、三つの gate 呼出しに `source_commit` を追加するための置換だけです。既存公開先 test には assertion が追加されていますが、元の assertion は保持されています。

caller の列挙も author と一致します。

- rear gate：production caller は driver **3311 行**だけ。既存 test 三呼出しも更新済み。
- 公開先：v3 caller **8868 行**には三引数を追加。非 v3 caller **9013 行**は従来呼出しを維持。
- job shell：`materialize`／`--destination` argv はありません。
- anomaly consumer：driver **8859 行**で公開先判定より前に実行され、認可による早期 return はありません。

## test の数・粒度・追加検出力

静的集計は **paired test 20 関数・47 ケース、job test 2 関数・5 ケース、合計 22 関数・52 ケース**。author 報告と一致します。

段 4 の統合方針は守られています。不正 record は一関数の parametrize、従来公開先は既存 test に集約、producer namespace は parametrize、親 directory 不在は独立関数にしていません。paired test の「14〜16 関数」は目安を超えますが、関数数だけで過剰とは判定しません。

| 分類 | test 群と評価 |
|---|---|
| 裁定の主要負例 | 不在・別 attempt・別 study・別 source。定数側／比較側の分離は M2〜M5 に必要 |
| 保存条件 | submit の intent／root、先行証拠 integrity、既存 sibling、既存 anomaly test。producer の namespace test とは責務が異なる |
| A1 | 別 prior attempt の禁止。単なる exact record 正例では代替不可 |
| 検出力を追加 | bench-go／ready-triple 正例、decision の各 field、digest、unsafe file、producer の生成内容／不正 source／定数不一致 |
| 公開先固有の検出力 | 不在時 fallback、認可時の旧 leaf 拒否、不一致 record を無視しないこと、部分 context 拒否 |
| 重複・再照準候補 | N2 の duplicate ケース、N3 の producer `[record]` |

materialize の identity 負例は reader 単体と似ていますが、公開先側の引数誤配線や reader の省略を検出できるため、一括削除は勧めません。

## M1〜M14 の一理由性

以下は静的判定であり、KILLED 実績ではありません。

| 変異 | 判定・再照準 |
|---|---|
| M1 | 不要。正常 prior と record 不在だけで拒否。定数を返す変異なら解除される |
| M2 | 不要。current／filename／record はすべて attempt-0003。定数側 attempt だけが不一致 |
| M3 | 不要。current／filename は attempt-0002、record root だけ attempt-0003。digest は再計算済み |
| M4 | 不要。caller／record／prior は pilot。定数側 study だけが拒否 |
| M5 | 不要。caller／prior は pilot、record は sized。比較側 study を除けば定数側は通る |
| M6 | 不要。別 source は有効な SHA、digest 正常。他の identity は一致 |
| M7 | 不要。id 単独変更のケースを使用。item／日付は正常 |
| M8 | 不要。digest は形式の正しい別値。形式検査では mask されない |
| M9 | 不要。正常 ready-triple の epoch 一つだけを 0 に変更。検査前 continue なら拒否が消える |
| M10 | 不要。二つの prior は正常。全候補解除への変異なら attempt-0003 の禁止が消える |
| M11 | 不要。exact sibling・record・親 directory は正常で、存在だけが拒否理由 |
| M12 | absent ケースで成立。不一致 record まで受理する変異を称するなら reader の raise も変更対象であることを明確化する |
| M13 | 登録された二 hunk なら成立。record 事前検査と producer 内の排他的書き込みを両方外す必要がある |
| M14 | **具体化が必要。** 固定値を `"b" * 40` にする。head と同じ `"a" * 40` では検出不能 |

M13 の二回目は intent／attempt root が存在せず、record だけが存在します。したがって record の事前検査を除き、producer の書き込みを実際の上書きに替えれば、再作成は可能になります。片側だけではそれぞれ `_exclusive_write`／事前検査が mask します。既存 helper 全体を変更する必要はありません。

なお M13 は同じ内容を再生成するため、変異を kill する主 assertion は二回目の戻り値です。bytes 保持だけでは、同値上書きを検出できません。

M1〜M14 の対象 fixture に、N2 のような別理由による過剰決定は見つかりませんでした。複数 test が同じ変異を kill することと、一つの fixture が複数理由で拒否されることは区別すべきです。

## 報告の正確さ

author は冒頭から「実装済み・未実走」と記し、pytest 未起動、nodeid 範囲なし、変異実績なしを明記しています。緑への誤記はありません。

親の焦点走は別の実績で、**1695 passed／2 failed／6 skipped**。ログ自身も受入全走ではないと記しています。この集計から新規 52 ケースの個別実行範囲までは復元できないため、「新規全件 green」「受入完了」とは書けません。

## 総括

- **must-fix：1 件。現状 NO-GO。** spawn-site の位置照合を局所修正し、関連検査を確認する必要があります。
- 認可の受理集合、先行証拠検査、namespace 拒否、公開先 create-only、anomaly の順序に実装上の逸脱は見つかりません。
- **削除候補：** digest helper 内の重複形式検査、独立検出力のない duplicate-key ケース、producer namespace `[record]` の重複ケース。後二つは再照準・統合でも可。
- **変異：** M1〜M11 は再照準不要。M12 は不在側で成立し、不一致側を称する範囲を明確化。M13 は二 hunk を実際の上書きまで具体化。M14 は固定値 `"b" * 40` を明記。M1〜M14 の削除・追加は不要です。