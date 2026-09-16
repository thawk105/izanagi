## 機構が救う producer report の形 (現物からの数え上げ)

**空振りではありません。外側の厳密 key 集合は2形、実 producer を通す具体的な正例は3経路あります。**

以下、`C` は `autonomous_trial_completeness.py`、`P` は `p3_autonomous_workload_trial.py`、`T` は `test_autonomous_trial_completeness.py` を指します。すべて指定されたファイルです。

| 外側の形 | producer の具体的な生成経路 | 正例 |
|---|---|---|
| 基本11キー＋`error` | cell identity 構築後、role 開始前に例外。`P:4083`、`:4109` → `:3689` → admission failure | `T:5758`。role 0件・accounting 0を確認 |
| 基本11キー | cell 内 wall budget 到達で正常 return。その後 reports directory 不在で admission failure | `P:4117`、`:3110`、`:3740`。`T:5766` |
| 基本11キー＋`error` | planner/coder の valid raw 保存後、preview で例外。その後 admission failure | `P:2863`、`:4323`、`:3689`。`T:5773` |

最初と最後は同じ外側 key 形の別経路です。3本を「全到達可能経路の総数」とは数えていません。

`T:5698` の helper を確認すると、差し替えは layout、site、故障点の `_role_metric_payloads`／時計、注入 preview です。`T:5736` で実際に `A.run_trial` を呼び、`:5747` で返却 report と保存 bytes の一致を確認します。completeness、digest chain、render、Layer-3 chain の無効化はありません。

実 finalizer は `P:3261` から呼ばれ、今回の正例は `P:3110` の directory 不在で失敗するため、render に到達せず diagnosis も生じません。publish 前の completeness／chain は `P:3956`／`:3974` で実行されます。

**成果物への効果:** 従来 root 無しで拒否された上記 identity failure report に、非 certifying receipt を返す受理経路が実在します。

## 変異 M1〜M7 の kill 対応

以下は**静的予測**です。変異試験は実行していません。テスト名の `D_` は `test_failure_only_diagnostic_` の略です。

| 変異 | 現物からの対応 |
|---|---|
| **M1** opt-in 恒真化 | **kill 予測。** `C:5171` 付近の条件を恒真化すると、`D_requires_explicit_opt_in` の `T:5783` の `raises` が成立しなくなる |
| **M2** key 検査を追加キー許容へ変更 | **kill 予測。** `C:5054` を `keys <= set(cell)` 相当に緩めると、`D_rejects_nonexact_shape[cell-extra]` の `T:5854` が例外なしで赤。`[diagnosis]` も同様に kill する見込み |
| **M3** helper の chain 呼出し削除 | **3件とも kill 予測。** `C:5131` 削除で、persisted `[file]`／`[dangling-symlink]` の `T:5797` と independently admitted の `T:5926` が例外なしで赤 |
| **M4** role 件数照合削除 | **生存。** `C:5088` 削除後も、`D_rejects_role_count_drift` は先行 `C:3069` で落ちる。`T:5864` 自身がそのエラーを期待している |
| **M5** CLI 引数転送削除 | **kill 予測。** `C:5229` 付近の転送を削除すると従来 root 必須経路で CLI が失敗し、`T:5818` の `returncode == 0` が赤 |
| **M6** diagnostic dispatch 無効化 | **正例3件すべて kill 予測。** `T:5763`、`:5770`、`:5778` の receipt 検査へ進む前に、従来の root 必須エラーが発生する |
| **M7** admitted 排除の decision 条件削除 | **生存。** `C:5077` を削除しても `[admitted]` は `C:5041` の `status != partial`、`[mixed]` は `C:5044` の件数検査で拒否される。両方とも `T:5898` の期待エラーのまま |

M4 の mask は実在します。`C:2924` の非 skipped ordinal 件数と `C:3069` の accounting 照合、`:3207` の journal/report role 同一性、新述語の valid-only 制約を合わせると、helper 到達時には同じ件数関係が既に成立します。

**M4 の再照準案:** `C:5105` の raw bytes 検証を無効化する変異と、既存 `D_preserves_raw_binding`（`T:5868`）を対にする。この入力は raw ファイルだけを改変し、journal/report の値は維持するため、現行では `T:5873` の `failure-only-raw … sha256` に到達します。新しい gate の追加は不要です。

M3 は先行検査で遮られません。3入力とも role／generation が空の producer 正例を基にしています。persisted 2件は外部ファイルだけを変更し、独立 admitted ケースも `_persist` で journal hash を整合させています。対象の拒否はそれぞれ `C:4912` と `C:4918` 以降にあり、`C:5131` を消すと残りの diagnostic 処理はそれらを読みません。

なお、親の「期待 node は完全集合」という登録は更新が必要です。M1 は既存 `T:2353` も期待エラーメッセージの変化で赤にし、M2 は `[diagnosis]`、M6 は CLI や複数の負例も赤にする見込みです。

## must-fix (成果物影響を 1 行で書けるもの)

**確認範囲では、実装の受理集合・成果物の値・参照を誤らせる must-fix は見つかりませんでした。**

M4／M7 の生存は検証計画の問題です。現行成果物の誤受理を示すものではないため、DW-G05 に従い nit に分類します。ただし、7変異すべてを kill できる計画として承認することはできません。

## real だが scope 外

- **正式系列の identity failure は回復しない。** `C:1137`〜`:1141` が diagnostic dispatch より先に拒否し、`P:3961` は publish 前に同検査を呼びます。影響: 正式系列の該当 report は新 receipt の受理集合に入りません。
- **campaign root の包含保証は成立しない。** `C:4908` の path 結合は絶対 `campaign_id` によって置換され得ます。影響: chain 成功から `campaigns/<単一ID>` 配下への包含は導けません。今回の receipt はその保証を申告していません。

いずれも親裁定で既知の範囲外事項であり、追加 gate は要求しません。

## 反証した攻め

**負例の発火地点**

- `nonexact_shape[error-extra]`／`[decision-extra]`／`[disposition-extra]` は、各々 `terminal-projection`／`run-envelope`／`artifact-admission` で先に落ちます。`T:5838`、`:5841`、`:5844` はその地点を明示しており、**新述語の独立防護を証明するテストではありません**。
- `[cell-extra]`／`[diagnosis]`、invalid role 2件は新述語の入口拒否です。invalid role は helper 内 `C:5101` の証明にはなりません。
- role-count drift は先行 accounting 拒否です。
- raw 改変、provider 宣言、persisted 2件、独立 admitted はそれぞれ意図した helper／chain 検査を指定した regex で確認しています。
- supplied-root テストの後半 `T:5807` は広い `raises` ですが、直後に前半との例外文字列一致を確認しています。別エラーだけで通る構成ではありません。

**所要台帳**

AST から展開した新規23 nodeid と台帳23キーを比較し、差集合は双方とも空でした。`[admitted]`／`[mixed]`、その他 parametrize ID も一致します（台帳 `:23121`〜`:23143`）。pytest collection は未実行です。

**API 波及：指定ファイル内の2段追跡**

- 直接呼出しで戻り値を捨てる既存テスト: `T:1251`、`:2011`、`:2332`、`:2373`。
- 新規の直接呼出し: `T:5785`、`:5805` は戻り値を捨て、`:5913` は **`is None` を assertion**。
- `C.main` → API: `C:5226` で receipt を受け取り、`:5238` の **`is not None` 分岐**で JSON 出力。CLI テスト `T:5814` は subprocess 経由でこの経路を使います。
- `_diagnostic_verify` → API: `T:5752` が戻り値を転送。その呼び手は新規テストの `T:5763`、`:5770`、`:5778`、`:5799`、`:5808`、`:5820`、`:5855`、`:5865`、`:5874`、`:5900`、`:5914`、`:5928`、`:5939`、`:5951`。戻り値を使うのは正例3件、CLI receipt 比較、既存免除の **`is None` assertion** です。
- `T:2000` の `_verify` は completeness の直接呼出しであり、この API の間接呼び手ではありません。producer も API を呼びません。

**全リポジトリの呼び手列挙は未確認です。** 「指定6ファイルだけを読む」という制約に従い、投影外の caller／fixture 本文を読みませんでした。

## nit

- **M4／M7 の変異登録が未成立。** 根拠は `C:5088`／`T:5864` と `C:5077`／`T:5878`。M4 は上記 raw 検査へ再照準し、M7 は現行2入力で単独防護を証明できないことを登録へ反映すべきです。現行受理集合の欠陥としては数えません。
- **期待 KILLED node の完全性が不足。** 親裁定 §5 の一覧には上述の追加 kill 予測が含まれていません。最終 anchor と期待集合の固定が必要です。
- **完了報告に明白な現物矛盾は確認できませんでした。** `s5-author.md:49` の M4 留保、`:57` の nodeid 説明、`:61` の新規23件は現物と整合します。ただし M7 の mask は未記載です。
- `s5-author.md:39`〜`:47` の実走結果・既存本文不変・diff 検査は、今回の静的レビューでは独立検証していません。`T:16` が利用する共有 fixture の無変更も、投影外のため確認していません。

## 総括

機構は空振りではなく、2つの外側形について3つの実 producer 正例経路が残っています。
新規テスト本文は finalizer／検証器を無効化していません。
M3 は3件とも単一の chain 呼出し削除を検出できる構成です。
M4 と M7 は他の検査に遮られて生存するため、変異登録の修正が必要です。
追加23 nodeid と台帳は静的に一致し、機能上の must-fix は確認できませんでした。
pytest・変異試験は未実行で、全リポジトリの呼び手と共有 fixture は投影制約により未確認です。