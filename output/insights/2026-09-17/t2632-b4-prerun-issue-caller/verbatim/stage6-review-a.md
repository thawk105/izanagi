## 所見一覧 (番号・must-fix/nit・real/plausible/refuted・file:line)

以下、`caller` は `orchestrator/campaign/p3_b4_prerun_caller.py`、`test` は `orchestrator/tests/test_p3_b4_prerun_caller.py` を指します。実行結果ではなく静的レビューです。

1. **must-fix / real — 欠落元の参照が候補の所在と混同される。** `caller:97`、`test:128`。未定義の `bootstrap_member` の根拠まで `loop_state.json` を指します。放置すると不足レポートの参照値が誤ります。欠落根拠の artifact が未定義なら `artifact_path: null` とし、候補の所在は既存の campaign・index・iteration で示す最小修正が必要です。
2. **must-fix / real — 深い JSON が typed stop を迂回する。** `caller:62`、`:80`、`:148`。`json.loads` の `RecursionError` は捕捉されず、所定の JSON／rc=2 が未捕捉例外終了に変わります。発行はされませんが、入力異常レポートが失われます。既存の捕捉対象へ `RecursionError` を加える局所修正で足ります。
3. **must-fix / real — M3・M4を fail-closed の KILLED と認定できない。** `caller:32`、`:37`、`test:113`、`:238`、`s5-author.md`「変異 matrix」。欠落を一項目除いても残り11項目で停止し、真偽値を持つ行は作られません。変わるのは欠落報告です。DW-M03／DW-M08 に従い diagnostic sensitivity pin と区別しないと、変異結果の意味を誤記します。
4. **nit / plausible — M10の置換内容では赤理由を確定できない。** `caller:113`、`:114`、`s5-author.md`「変異 matrix」。ID重複、path重複、全件の入替えでは検出層が異なります。具体的な置換を固定してから帰属を確定してください。
5. **nit / real — `registry_ordinal` は将来の概念に留まる。** `caller:54`、`:79`、`:104`。候補順は保持しますが、番号や台帳行は生成しません。今回の限定スコープには整合します。
6. **nit / refuted — 候補ありの正常入力から欠落なしで発行する経路。** `caller:25`、`:82`、`:91`、`:156`。現行コード内にはありません。
7. **nit / refuted — 実発行器の stub 化・root patch の通常終了時の漏れ。** `test:50`、`:56`、`:59`、`:175`。wrapper は実物へ委譲し、patch は復元される構造です。

## fail-closed の穴

`_MISSING_SOURCES` は12項目の固定辞書で、コード内に削除・再代入はありません。候補は campaign ごとの `rejected` を `extend` して保持します。正常に読めた候補数を n とすると欠落は12n件となり、n>0なら発行器へ進みません。後続 campaign の読込みに失敗した場合も、部分結果で発行せず typed stop します。

`row.keys()` は `isinstance(row, dict)` と短絡評価で保護されています。root が通常ファイルなら読込みで `NotADirectoryError` が発生し、`OSError` として捕捉されます。JSON構文異常、文字コード異常、未知trialも捕捉対象です。

実在する漏れは所見2です。深くネストしたJSONは、内容の型検査より前に `RecursionError` を起こせます。これは**発行については閉じていますが、typed report の契約を満たしません**。

## 発行器の呼び方

`caller:122` は呼出し時に `issuer._REPOSITORY_ROOT` を参照します。import時のコピーではなく、`preregistered_publication_root` の `mock.patch.object` が効きます。

空batchに対する planned path は `()` です。発行器の `_normalize_planned_results`（`:374`）は空同士のID集合・件数一致を受理します。その後、通常のfixture条件では `:846` 付近の適格行不足で `design_not_feasible` になります。名指しroot異常などがあれば、その先行検査で拒否されます。

`B4PrerunIssuerError.__init__`（発行器`:103`）は全reasonで `f"{reason.value}: {detail}"` を使うため、`removeprefix` は適切です。detail内に同じ文字列があっても先頭一回だけを除きます。

呼び手にディレクトリ作成処理はありません。空候補時の発行器呼出しは `main` から一回です。発行器・台帳の受理集合、201行条件、四つの真偽値の判定は変更されていません。

## 出力の正直さ

`loop_state.json` は実際に読んでいます。そのため「存在しないファイルを読んだ」とする捏造ではありません。しかし、**候補を発見した場所と、欠落した根拠の参照先は別です**。

特に `bootstrap_member` のartifactは未定義です。WALや事前登録欄に関係する欠落も、このコードはそれらの現物を読みません。全項目の `artifact_path` と `artifact_key` をwhiteboardに固定すると、欠落根拠の所在としては誤った参照になります。DW-G05上、レポートの参照値に直接影響するため所見1はmust-fixです。

最小修正は未定義の参照をnullにすることです。WAL resolverや新しい証拠台帳を追加する必要はありません。`test:128` の一律checkpoint期待は、この新規テストが誤参照を固定している箇所です。既存の発行器・consumerテストの期待値変更は不要です。

なお、射影された `s4-ruling.md` の確定planにはnullの逐語指定はありませんでした。null方針は今回のレビュー指示に明記された条件として扱っています。

## 変異の単一理由性

| 変異 | 静的判定 |
|---|---|
| M0 | `caller:90` はdocstringではなく通常の `#` コメントです。そのコメント本文だけの変更なら動作は等価。SURVIVEDは未実測です。 |
| M1 | T3の`fail`が候補になり、空候補拒否から欠落報告へ変化します。T3に帰属可能です。 |
| M2 | 欠落分岐で実際に発行する置換ならT2が検出します。追加の全候補テストも呼出しゼロを要求しており、そちらも失敗候補です。 |
| M3 | T2の集合一致・個別assert・件数は同じ欠落を観測しています。ただし残る11項目が発行を止めるため、bootstrap判定を破った証拠にはなりません。追加の全候補テストも36件期待で失敗します。 |
| M4 | M3と同様です。Falseを持つ行を生成する経路はなく、欠落項目除去の診断感度だけを検査します。 |
| M5 | T1の複数回呼出しとT2の先頭success campaignでの早期呼出しは、双方とも登録済みの検出です。複数nodeになること自体は問題ではありません。正確な失敗集合は具体的な移動内容次第です。 |
| M6 | `Path.cwd() / "output/b4-prerun-publication"` と置換すると、`elsewhere/output/...` になり、fixtureの`repository/output/...`とは異なります。発行器の名指し検査で拒否され、T1・T5が検出します。T3も同じ空候補期待なので失敗します。 |
| M7 | T1のrc=2期待で検出します。T3も同じく失敗します。 |
| M8 | 空候補で`({}, 0)`相当を返すなら、`issued`の検査以前にT1のrc=2期待で失敗します。T3も失敗します。 |
| M9 | T5の成功キー集合一致で検出します。ただし発行内容・受理集合は変わらず、DW-M08上は構造化出力のdiagnostic sensitivity pinです。 |
| M10 | 下記のとおり、具体的置換なしでは単一理由を確定できません。 |

M3について、**同じtest node内なら自動的に単一理由性を満たす、とはいえません**。今回は複数assert自体は同じ欠落を見ていますが、肝心の発行停止には他の欠落が残ります。

M10で一行の `attempt_id` を別行と重複させれば、発行器`:409`付近のmapping検査が拒否します。pathだけを重複させれば別reasonのpath重複拒否です。ID/pathを全件一対一で入れ替える形なら集合検査を通る場合があり、T5のP4対応assertが検出します。したがって「別行のID/path」という記述だけでmapping不一致を保証できません。

既存issuerテストは新callerを呼びません。callerだけの変異を既存issuerテストが先に殺す経路は見つかりませんでした。**T5の内部で実発行器が拒否することと、既存issuerテストへの帰属は別です。**

DW-M08は期待nodeの完全集合を要求します。author表のT1〜T5は代表的な検出先であり、現状のまま完全な期待集合として使えません。

## test の弱体化

`observed_issuer` は呼出しを記録後、保存した実発行関数へ委譲します。T5も201件の `B4ScheduledAttemptInput` を実発行器へ渡し、receipt実体のhashとloaderによる再読込みを検査します。成功値を返すstubはありません。

proposal等のhashは合成ラベルから生成しています。現行実装のhashをfixtureへ注入して期待値を追従させる操作はありません。receiptのhashを実ファイルから再計算する検査も妥当です。

`captured.err == ""` は警告追加に敏感ですが、現在のissuer・ledgersに警告出力経路は見つかりません。現状の偽赤としてはrefutedです。

ただしT5が証明するのは `issue` と成功直列化です。`main` の成功経路や現物からの非空batch構成を証明していない点は、authorの限定と一致しています。

## consumer test への波及

指定3consumerテストと対応moduleに、新callerのimportやcampaign Python moduleの全件列挙は見つかりませんでした。raw-record-producerテストのglobは生成JSON対象です。

新callerのimportは関数・定数の定義に留まり、発行や `_REPOSITORY_ROOT` 書換えを実行しません。新fixtureのroot patchはcontext manager、wrapperとcwdはmonkeypatchで通常のteardown時に復元されます。

別の走査テストについても、callerは次の抽出条件に該当しません。

- build authorityの`--build`文字列。
- exploration namespaceの`exploration_campaign_layout`マーカー。
- analysis pathの`evaluate_analysis`文字列。

したがって、この追加が指定3consumerを赤にする具体的経路は静的には見つかりません。rc=130は中断の記録であり、sandbox起因ともコード起因とも断定できません。完走結果は未確認です。

## 総括

**局所修正が必要です。** 欠落artifactの誤参照と`RecursionError`のtyped stop漏れを修正し、変異記録では診断感度とfail-closedの検出を区別してください。M10は具体的置換、期待nodeは完全集合の確定が必要です。

候補ありで発行する通常経路、真偽値の無根拠な補完、台帳行の捏造、既存受理集合の変更は見つかりませんでした。ファイル変更・pytest・変異実行は行っていません。