## 裁定の字義との距離

親 brief の「字義どおりは実装不能」は誤りです。[D1772](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/docs/decisions.md:53830) 自身が、既存 literal を再発行せず「追加 exact 条件として重ねられるか」を実測するよう命じています。したがって採用案の値述語は「裁定から距離のある代替」ではなく、D1772 が明記した第一候補そのものです。

また、「凍結 135 file の書換え」対「系列別の whole-WAL digest」の二択でもありません。例えば対象を `variant`、tag、3 field に限定した WAL projection digest なら、block record を変更せず、timestamp、commit 数、`proof_surfaces` も固定しません。従って「read-heavy に `proof_surfaces` があるから系列別 literal が必須」という論証も成立しません。

ただし projection digest は新たな digest producer、期待値、対応規則を要します。D1772 の「新しい gate 機構は作らない」には、既存ループへ値述語を直接加える案の方が近いです。第三案は存在しますが、採用案を覆す理由にはなりません。

採用案は新しい拒否条件ではありますが、新しい gate「機構」ではありません。既存の WAL reader、既存の固定 3 campaign の経路、既存ループを使い、helper、dispatch、digest 族を新設しないためです。

## 親の実測の検算

現物の再計測結果は親と一致しました。

| 系列 | WAL 総数 | stage 内訳 | 3 field の値 | 欠落 | tag | `proof_surfaces` |
|---|---:|---|---|---|---|---:|
| write-heavy | 135 | build_start 15 / build_done 15 / verify_done 90 / commit 15 | 0 / true / serializable が各 90 | 各 0 | legacy 15 / performance 75 | 0 |
| balanced | 135 | 同左 | 同左 | 各 0 | 同左 | 0 |
| read-heavy | 135 | 同左 | 同左 | 各 0 | 同左 | 90 |

block record も各系列 45 file でした。`anomalies`、`certified`、`verdict` は record 直下だけでなく全 nested object を調べても各 0 件で、`correctness_certified=true` は各 45/45 でした。

135 literal も再現しました。各封筒に埋め込まれた canonical `record` bytes を抽出して sha256 を再計算し、file 内 `record_sha256` と実装定数を三者比較した結果です。

| 系列 | literal | file 内 hash | bytes から再計算 | 不一致 |
|---|---:|---:|---:|---:|
| write-heavy | 45 unique | 45 unique | 45 unique | 0 |
| balanced | 45 unique | 45 unique | 45 unique | 0 |
| read-heavy | 45 unique | 45 unique | 45 unique | 0 |

親の実測値に数値上の誤りはありません。ただし証明できるのは、指定された 3 campaign の現時点の 405 WAL frame と 135 block file だけです。「3 field は verify_done にのみ存在」「read-heavy だけ proof_surfaces を持つ」を、将来の B-10 WAL や一般 schema の性質へ広げることはできません。

## 凍結証拠への副作用

現行 [b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/campaign/b10_backoff_shape_sweep.py:92) の whole-file sha256 は `3795bcef673752641332e76b4f7cc0abc058d00cf1a3f0b0ed744227c238d3d9` で、現在の HEAD blob と一致しました。

編集後の影響は次の通りです。

- commit 前は dirty 検査と current bytes == HEAD blob 検査で live 経路が停止します。
- commit 後は新しい `analysis_code_sha256` が binding SHA、将来の formal campaign identity、将来の block record、report provenance と report directory identity に伝播します。
- legacy 3 系列は固定された旧 analysis hash、旧 binding、135 record digest を使うため、既存 block record bytes は変わりません。
- 実 WAL 正例を `_collect_report_inputs` まで通すだけなら report は書かれません。現物に対して full `phase=report` を走らせれば、新しい binding 配下へ新 report を発行するので実施してはいけません。
- プランは `_legacy_*_binding()`、3 validator、`_assert_report_lock_binding()`、135 literal に触れず、T-2408 面を踏んでいません。
- `_collect_report_inputs` を module 直下の `FunctionDef` のまま維持するため、既知の AST 条件にも抵触しません。

## 所見

1. **[real][must-fix] 親 brief とプランは D1772 を「実装不能なので限定代替」と誤って再解釈している。** 採用案は D1772 が明記した「literal を再発行しない追加 exact 条件」の実施だと記録すべきです。新しい裁定や P1 による読み替えは不要です。  
   放置時の影響: 受理集合は狭まる一方、insight と decision fragment が確定裁定を「未達の代替実装」と誤参照します。

2. **[real][must-fix] 親の二択と `proof_surfaces` 論証は偽です。** relevant-field projection digest という第三形があり、whole-WAL digest の余計な固定は必須ではありません。ただし新機構に近いため、存在を認めたうえで不採用にすべきです。  
   放置時の影響: 成果物値は変わりませんが、採否理由が存在しない技術的必然に依存し、後続レビューの参照を誤らせます。

3. **[refuted][nit] 採用案が禁止された「新しい gate 機構」に当たるとの攻撃。** 新しい拒否述語ではありますが、既存 WAL read と既存受理ループへの局所追加であり、D1772 が要求した挙動です。  
   放置時の影響: 3 field が悪い WAL だけが受理集合から除かれ、digest literal や凍結 record の値は変わりません。

4. **[refuted][nit] 親の現物件数・分布・135 digest 再現に誤りがあるとの攻撃。** 指定された全数を再計測し、すべて一致しました。  
   放置時の影響: 現物 3 系列の値と正例受理は変わらず、数値修正も不要です。

5. **[real][nit] 親の「のみ」という表現は観測範囲を越えています。** 3 campaign の現物については正しいものの、将来の WAL schema や他 campaign まで保証していません。  
   放置時の影響: 現在の受理集合は変わりませんが、証拠参照が 405 frame の観測から一般仕様へ過大化します。

6. **[real][nit] `ANALYSIS_REL` の live 波及範囲が brief では短く書かれています。** hash だけでなく binding SHA、将来の campaign identity、block record、report path/provenance も変わります。  
   放置時の影響: 凍結 bytes は変わりませんが、将来の live 成果物は新しい identity と参照先になります。

7. **[refuted][nit] プランが凍結成果物の変更または再発行を要求するとの攻撃。** 計画どおり collector の読取までに留めれば、135 block file、既存 report、literal、golden は変更されません。  
   放置時の影響: 既存成果物の bytes と identity は不変です。現物で full report phase を追加実行した場合だけ新 report が発行されます。

8. **[refuted][nit] AST 条件または T-2408 領域を踏むとの攻撃。** 予定編集は `_verification_source_disclosure` 内の文追加であり、collector の構造や 2863–3210 行の担当領域を変えません。  
   放置時の影響: 既存 validator の受理集合と T-2408 の参照面は不変です。

## 総括

実装案そのものは採用可能です。ただし根拠は「D1772 を字義どおり実装できないので代替する」ではなく、「D1772 が明示した literal 再発行なしの exact-condition 分岐を、実測結果に基づいて選んだ」です。

必須修正は親 brief、プラン、今後の insight・decision fragment の裁定解釈と、存在しない二択の説明です。コード面では、予定どおり既存ループへの直接述語追加、凍結 literal・validator 無変更、現物確認は collector まで、とすればよいです。pytest は実行しておらず、緑とは判定していません。