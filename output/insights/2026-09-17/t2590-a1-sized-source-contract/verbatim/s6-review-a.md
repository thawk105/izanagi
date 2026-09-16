## 凍結 bytes と digest の検算

**[refuted] 凍結物の改変・digest 不一致はありません。** `sha256sum` を実行して検算しました。

| 対象 | 実 bytes の SHA-256 |
|---|---|
| v1 契約 | `21477b74ad440f9eed8c27f78417f0469d757cb2bea2f579b2b212632b69f4b7` |
| v2 契約 | `b50a4edf86250033aa0e2b18efa2d7842d7c90025fdb901011fdad7adf052fe1` |
| sized 追補 README | `6093de244e6fc90607094608617032f427db4951ebffc847c7bcaa795309789b` |
| patch | `a5e0710c3f76744755b58ec66024c277daba00e49ce3cbf3d6d263cd7228580a` |
| sized policy | `a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a` |
| sized 事前登録 | `6047eff005fbd94bad8df0313124bd4ca037dedf0f2e3db05224d04ad34fd3c2` |

v2 の各 digest は実値と一致し、`SIZED_CONTRACT_SHA256` も v2 の実値と一致します。`canonical_head` は v1・sized policy と同じ `511c9538e4e8efa54b45cda62e72389ed3b706ec` です。

根拠：`orchestrator/campaign/paper_story_a1_source.py:24`、`orchestrator/campaign/paper_story_a1_source.v2.json:4`。

指定差分は所有 6 path のみで、適用後の各ファイルは diff の新 blob と一致しました。v1・patch・両 policy／事前登録・T-2397 README・sizing 入力 2 file は brief の基準 commit と bytes 同一。sized 追補は HEAD と同一で、実装差分に含まれません。

成果物影響：凍結登録と pilot の既存 digest 束縛は維持されます。

## pilot 経路の不変

**[refuted] pilot の閉包・既定 binding 判定の変更はありません。**

`paper_story_a1_paired.py:2243` の置換後も、pilot は同じ `SOURCE_PATHS` を同じ基礎 tuple の末尾へ追加します。`non_certifying=False` は 9 path、`True` は 14 path で、順序も不変です。

`paper_story_a1_source.py:50` の既定引数は pilot。照合するのは従来と同じ v1 契約・patch・T-2397 README の 3 digest です。`paper_story_a1_paired.py:4862` でも pilot 閉包に含まれる v1 契約から pilot を選択します。

成果物影響：公開 pilot binding の履歴 module SHA を現行 SHA に更新する必要はありません。

**[real] 公開受領証が non-certifying validator を通る、という要求は成立しません。**

公開 `receipt.json:226` の binding は 9 path。`paper_story_a1_paired.py:4850` は集合完全一致を要求するため、14 path を要求する `_validate_non_certifying_source_binding` では変更前後とも拒否されます。静的に導ける判定は次のとおりです。

| 呼出先 | 変更前 | 適用後 |
|---|---|---|
| `_validate_source_binding(binding, pilot_policy)` | True | True |
| `_validate_non_certifying_source_binding(binding, pilot_policy)` | False | False |
| `binding_matches(files)` | True | True |

適用後の test 8 は既に terminal 用 validator を呼んでいます：`orchestrator/tests/test_paper_story_a1_paired.py:4849`。

成果物影響：実装による pilot 受領証の判定変更はありませんが、誤った呼出先を受入基準にすると正常な公開受領証を失敗扱いします。

## 受理集合の変化

**[real・仕様内] 次の拡大／縮小があります。**

| 入力 | 変更前 → 適用後 |
|---|---|
| 契約なし sized binding（5／10 path） | 受理 → 拒否 |
| v2 契約入り sized binding（9／14 path、正しい digest） | 拒否 → 受理 |
| hydrate なし sized submit | 新しい hydrate 検査で拒否 |
| 登録条件を満たす sized measurement | pilot 専用照合で拒否 → 後続経路へ進行可能 |

根拠：`paper_story_a1_paired.py:2243`、`:2636`、`:3411`、`:4862`、`:7129`。これらと対応する job／consumer の対称化以外に、独立した受理条件変更は見つかりませんでした。

成果物影響：sized は登録済み amended source 経路へ進める構造になります。実走成功を意味しません。

**[refuted] exact 述語の緩和・両契約入り binding の抜け穴はありません。**

- `_trace0_commands_match`（`paper_story_a1_paired.py:4978`）は変更前 blob と関数本文が文字単位で同一。
- `binding_matches` 単体は以前から余分な key を無視します。今回も同じです。
- consumer の `any(...)`（同 `:5222`）は両契約でも発火しますが、正規経路では `:4850` の閉包完全一致と `:5324` の binding 検査で拒否されます。

成果物影響：両契約を混ぜても、有効な sized／pilot 成果物としては受理されません。

## 規律 2 と D1323

**[refuted] verifier・anomaly・condition gate・formal／promotion 条件の緩和、新しい bytes 検査はありません。**

source 契約の digest 検算と materialization 検査は既存機構の study 別適用です。`SourceContext.validate` は不変です：`paper_story_a1_source.py:79`。

**[refuted] T-2081 test が検査本体まで stub した恒真テスト、という疑いは退けられます。**

- `test_paper_story_a1_job_contract.py:3362` は `_run_git` だけを置換し、実際の `_parent_porcelain` と `_assert_ccbench_acceptance` を呼びます。親 status が空でも submodule dirty を拒否する構造です。
- 同 `:3390` は実際の sized `SourceContext` を生成し、`pipeline.py:1101` から実際の `validate` に到達します。誤 pin の負例もあります。
- ただし後者の Git 応答・期待 materialization 生成／比較は stub です。実 tree 検査を実証するテストではありません。

成果物影響：既存の source 拒否条件は維持されます。T-2081 の記録は「既存機構への接続確認」と stub 範囲を明記する必要があります。

## test の弱体化

**[refuted] 既存 test の削除・skip・xfail・期待値緩和はありません。**

差分前 blob と適用後について、自分で `grep -c "^def test_"` と関数名集合を比較しました。

| file | 前 | 後 | 消失 |
|---|---:|---:|---|
| `test_paper_story_a1_job_contract.py` | 88 | **97** | なし |
| `test_paper_story_a1_paired.py` | 133 | 138 | なし |

既存 test の変更は AST assert の追加です（TJ `:2244`）。submit fixture の実 bytes コピーは従来から存在し、今回 study 選択と sizing 入力を追加しています（TJ `:3190`）。公開 pilot binding の歴史 SHA 差し替えはありません。

**[refuted・静的範囲] test 7 の負例は期待する拒否条件を狙っています。**

TP `:4908` の期待 error は実装と一致します。

| 改変 | 期待 error |
|---|---|
| 非 canonical root | `amended-source-admission-mismatch` |
| `tracked_clean=True` | 同上 |
| canonical commit 不一致 | 同上 |
| canonical だが configure と異なる root | `trace0-source-route-incomplete` |

前 3 件は driver `:5227`、最後は `:5029` の source token 不一致に対応します。単に `valid=False` だけを要求せず、該当 error を assert し、別 node の正例もあります（TP `:4903`）。

成果物影響：既存の拒否被覆は削られていません。ただし実行時の成功は本レビューでは未確認です。

## 報告と実体

**[real・must-fix] author 報告が適用済み差分と異なる時点を記述しています。**

根拠：[s5-author.md:66](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2590-a1-sized-source-contract/artifacts/dev-wave-t2590-a1-sized-source-contract/s5-author.md:66)。

| 報告 | 適用後の実体 |
|---|---|
| test 8 は non-certifying 検査で失敗し、訂正判断待ち | TP `:4853` は既に terminal 用 validator |
| TJ は 95 test | 97 test |
| sized measurement fixture／test は残作業 | TJ `:3417`／`:3489` に存在 |
| pilot measure の attempt 拒否 test は残作業 | TJ `:3516` に存在 |

成果物影響：放置すると、受入記録に旧版の FAIL と最終版の未確認状態が混在し、何を検証したか追跡できなくなります。是正は既存報告を最終差分に合わせ、変更済み・実行済み・未実行を分ける局所修正です。

**[unverifiable] 直接呼出し結果と反実仮想の実施履歴。**

報告に列挙された 12 nodeid はすべて存在します。ただし直接呼出しの実行ログは射影に含まれず、結果を独立確認できません。報告は反実仮想を「未実施」としており、KILLED／SURVIVED の証拠はありません（[s5-author.md:74](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2590-a1-sized-source-contract/artifacts/dev-wave-t2590-a1-sized-source-contract/s5-author.md:74)）。

成果物影響：最終差分の test 成功や変異検出力を、現報告から受入台帳へ転記できません。

## must-fix / nit の一覧

- **must-fix［real］：author 報告と最終差分の時点を合わせる。** 対象は test 8、test 数、追加済み measurement tests、実行結果の適用範囲。実装の受理条件を変える必要はありません。
- **nit［real］：sized の hydrate 不足にも `attempt-0004 requires ...` と表示される。** `paper_story_a1_paired.py:2641`。plan どおりの既存文言ですが紛らわしく、受理判定への影響はありません。
- production code の must-fix は、この静的レビューでは見つかりませんでした。

## 総括

凍結 bytes、pilot の既存判定、exact 述語、既存 test は維持されています。sized への分岐対称化は裁定の範囲内です。

**受入記録としては author 報告の訂正が必要です。** pytest・直接テスト呼出し・変異実験は本レビューでは実行しておらず、最終差分の実行成功は未確認です。