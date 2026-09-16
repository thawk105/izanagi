## 読んだ資料

指定の4資料はすべて読めました。以下では `plan` を段2プラン、`L` を `tools/check_branch_landed.py`、`TL` をそのテストと略記します。

- [brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2639-branch-rescue-path-first/prompts/brief.md)
- [stage2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2639-branch-rescue-path-first/artifacts/dev-wave-t2639-branch-rescue-path-first/stage2-plan.md)
- [D922-verbatim.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2639-branch-rescue-path-first/prompts/D922-verbatim.md)
- [D1231-verbatim.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2639-branch-rescue-path-first/prompts/D1231-verbatim.md)
- 許可された実装2本・テスト2本の関連箇所、`docs/failures.md:8–22`。

実在path確認として `git ls-files -z` の名前一覧も読みました。ファイル変更・commit・テスト実走・性能測定はしていません。

## 偽の landed を作れる経路 (real)

**未着地の四要素状態を、着地済みと誤認する具体的経路は確認できませんでした。** ただし、次の仕様上の不整合は実在します。

**real — 候補上限超過でも `landed` を返す方針と、D922の逐語が衝突しています。[ドリフト]**

`plan:130` は `limit + 1` 番目まで正例探索し、上限超過より正例を優先します。現行も `L:748–759` がこの順序で、`TL:830–850` は上限64・列挙65件での `landed` を要求しています。一方、`D922:15–18` と `brief:113` は上限超過を `indeterminate` としています。

これは**四要素の偽証ではありません**。一致した状態は実在するため、「未着地内容を失う反例」と数えるのは不正確です。しかし「打ち切りはすべて保守側」という保証の例外を、現行実装だけを根拠に裁定済み扱いしてはいけません。逐語に従うなら、検出済みの候補上限超過を正例で覆さない扱いが必要です。

## 作れないと確認した経路 (refuted)

**refuted — batch行ずれによる別commitの証拠流用。**

`plan:92–98` はchunk全体の終端LF・行数・連番・missing式を検査してから受理します。さらに `plan:59–60` は、候補commitを `_tree_entry` で再取得し、四要素を再比較します。したがってbatchの誤対応が絞り込みを誤らせても、それだけでは偽の `landed` になりません。

- 改行・空白・タブ・CR：行プロトコルへ入れず既存経路へ退避（`plan:106–110`）。
- `:`：最初の境界以降を保持。全区切りでの分解は禁止（`plan:108,118`）。
- `"`・先頭 `-`：具体的テストは未記載。ただしfull commit OIDに続く入力データであり、shell引数として解釈する構造ではありません。最終path比較も残ります（`plan:81`、`L:228–237,689–701`）。
- 非ASCII：UTF-8を保持し、非UTF-8は失敗側（`plan:109–110`）。
- 正常missing：期待する入力式との完全一致だけ許容。`ambiguous`・`dangling` は許可形式に含まれず、未知形式として失敗側（`plan:94–98`）。
- 候補0件：chunkループに入らず、一致を生成しません（`plan:50–62`）。
- stdout途中切れ：行数・終端検査で失敗側。短い入力に対する空stdoutも同様です。

実在path調査は25,475件、`:` を含むものが1,653件でした。例は `output/env/pegasus/calibration/job-staging/0:867863.nqsv/allocation-unavailable.json`（`plan:115`）。空白類・引用符・非ASCII・先頭`-`は今回のindexにはありませんでした。全履歴についての不存在証明ではありません。

**refuted — modeだけ別commitから合成する経路。**

`plan:122–124` は同じcommitの `_entry_matches` を必須とし、`L:704–710` はpath・mode・type・oidを同時比較します。tip優先経路も同じ比較です（`L:738–740`）。symlinkはblobですが、`120000` と通常ファイルmodeの差が残ります。削除・tree・gitlinkも既存経路です。

**refuted — spool所属だけで通る恒真ゲート、および `not-landed` への漏れ。**

S2の資格条件は探索を開始する条件で、受理条件ではありません（`plan:154–169`）。M3負例を静的に追うと、

`receipt不一致 → 通常blobのfallback → tip不一致 → 候補0 → not-matched → indeterminate`

となります（`L:738–763`、`plan:167–172`）。`_regular_decision` を呼ばないため、`L:1297–1305` のpure-add負証拠には到達しません。負例を誤って `landed` にする変更には、提案された `test_unlanded_pure_add_spool_stays_indeterminate` が反応する設計です。ただし実装・実走は未確認です。

**refuted — timeout・parse失敗・補助観測による新規受理。**

`Git.run` のtimeoutは例外（`L:213–242`）、batch異常も例外（`plan:97`）。S2ではerror／truncatedを `indeterminate` にします（`plan:170–179`）。receipt解析失敗をexactで覆す経路も禁止されています（`plan:154–160`）。全unitの連言とref再確認も維持されます（`L:1872–1890,1533–1536`）。

この確認は決定的証拠の探索についてです。非決定の観測失敗まで必ずverdictを変える、という保証ではありません（`L:1851–1867`）。

## 恒真な保証・発火しない検査

**real — 「decisiveが一層」は内容証明の保証になりません。[恒真ゲート]**

`test_spool_fallback_has_one_decisive_layer`（`plan:307–308`）は、一層だけtrueなら、その層が誤った証拠でも通ります。さらに `plan:214–219` はtimeout・不一致にもdecisiveを付けるため、これを「着地証拠が一つある」と読めません。

各ケースで具体的なlayer・outcome・verdictを照合し、正例ではpath・四要素・matched commitも特定する必要があります。

**real — 失敗stub検査は、fallback自体の消失に反応しません。[テスト代表性]**

`test_spool_fallback_does_not_call_regular_decision`（`plan:311–312`）は、全spoolを無条件 `indeterminate` にしても通り得ます。呼出し禁止の保証としては有効ですが、正例の証明には使えません。

同様に `test_spool_fallback_probe_result_never_changes_verdict`（`plan:317`）は、exactで解決済みのケースだけならprobe自体が呼ばれず、結果変更が発火しません（`plan:225–229`）。候補0の未解決fragmentでprobe実行を確認し、その結果を変えてもverdictが不変であることを検査すべきです。

**real — 異常応答テストには、分岐へ到達した証明が不足しています。**

`plan:284–295` のテストはmain tipを不一致にしないと、batchへ到達しません（`L:738–740`）。注入したbatch応答が実際に消費されたassertが必要です。空入力、余剰行、終端LF欠落、`ambiguous`、`dangling`、引用符、先頭`-`も明示ケースにはありません。

**refuted — 「両層をstubにしても既存統合テストは緑」という断定。**

提案テストの本文はまだなく、そう断定できません。既存 `test_p02_real_checker_landed_and_loose_deadline_is_rc0` は実repoに同じ状態を作り、対象commitのassessmentを検査しています（`orchestrator/tests/test_check_branch_rescue.py:304–319`）。新規S2統合テストでもこの実体性を保つべきです。

## 親 brief の実測と一般化への反論

| 判定 | 所見 |
|---|---|
| **real** | **M2の121倍は局所値。** `10.92 / 0.09 ≈ 121.3` は正しいものの、候補列挙を含めると `(10.92+0.48)/(0.09+0.48)=20`。さらにmode再確認等を含みません。「費用はsubprocess起動」と原因を一意に断定する根拠も不足しています（`brief:42–49`）。[テスト代表性] |
| **real** | **M2bは集合差の証拠が省略されています。** 89種類と71種類から分かるのは個数差18です。包含関係なしには「ちょうど18種類欠落」、各OIDの由来なしには「merge導入状態」と確定できません（`brief:51–53`）。rawへの置換を避ける方針自体は保守的です。[捏造/幻覚] |
| **real** | **M3正例はblob一致だけでは不足。** 5件のblob一致はmode込みの四要素証明ではありません。exact履歴の存在もfold完了そのものは証明しません（`brief:57–64`）。負例の候補0は `indeterminate` の根拠であり、未着地確定ではありません。 |
| **refuted／未確認** | **M5の数値誤りは確認できません。** 原本archiveは許可範囲外です。`brief:71–74` の転記だけから、4commit・3件indeterminateの正否や「1件timeout」との矛盾は確定できません。確定扱いは推測になります。[捏造/幻覚] |
| **real** | **I7のsymlink分類は誤り。** `brief:116` の「非blob（tree／symlink）」に対し、symlinkはblobです。既存テストも明示しています（`TL:769–783`）。planは訂正済みです。[ドリフト] |
| **real** | **rc改善を削除許可の改善へ一般化できません。** `brief:76–78` 自身が削除条件への非接続を説明し、`D1231:3–10` も可視化の完全さに限定しています。S1/S2を根拠に削除権限を拡張する余地はありません。[権限逸脱] |

## 総括

**受理する**とは、mainから到達可能な同一commitで四要素が一致するか、正式receiptが証明する範囲で `landed` とすることです。  
**拒否する**とは、証拠不足・解析失敗などを着地済みとして通さないことであり、spoolを `not-landed` と断定することではありません。

通る正例は、`docs/spool/worklog/2026-09-15-example-1.md` の通常blobがmain履歴のcommit `C` に同じpath・mode・type・oidで存在し、後に削除されたケースです。receipt不一致でも、探索が制限内に完了し、他の全unitと整合性検査も通ればD922(a)で `landed` にできます。

**新規の偽 `landed` 経路は未確認です。ただし、上限超過時の正例優先と裁定の不整合、証拠の実体を確認しないテスト保証は是正対象です。**