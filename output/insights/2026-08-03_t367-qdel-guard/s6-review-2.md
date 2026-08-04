結論は受理不可です。M02 の意味論どおりの変異が生存し、過剰拒否・qdel once-only にも未検出領域があります。以下は静的読解のみであり、pytest は実行していません。

### [所見 1] M02 が生存し、M04/M07/M10 の KILL も条件付き / 深刻度: blocker

根拠 (`file:line`):

| ID | 生存予測 | 実際に赤くなるテスト |
|---|---|---|
| M01 | KILL | RUN snapshot で qdel 非実行を要求する `orchestrator/tests/test_pegasus_dispatch_compute.py:1713-1741` |
| M02 | **SURVIVE 予測** | `:1286-1303` は classifier 単体だけ。さらに `_gate_qstat_result()` は rc≠0なら stdout を必ず空にする (`:806-813`) |
| M03 | KILL | mixed-block・重複・矛盾の3例 `:867-901` |
| M04 | KILL だが診断値だけ | request 不在の `gate.reason` を固定する `:1234-1254`。target parser が別途拒否するので、qdel 受理集合は変わらない |
| M05 | KILL | END履歴後の fresh QUE `:1363-1378` |
| M06 | KILL | qdel非ゼロ・例外 `:1519-1551`、非ゼロ＋clock例外 `:1031-1060` |
| M07 | 条件付きKILL | 予算テスト `:974-1001`。ただし実装には同種の検査が3箇所ある (`tools/pegasus/dispatch_compute.py:1085,1115,1123`) |
| M08 | **KILL** | QUE/HLD/STGの正例が qstat→qdel の完全な command 列を固定している (`test_pegasus_dispatch_compute.py:816-847`) |
| M09 | KILL | helper 境界 `:912-926` と production 境界 `:1634-1646` |
| M10 | KILL（直接名呼出しのみ） | AST caller閉包 `:1063-1077` |

M02 は classifier の `returncode == 0` を表層的に削除すれば `:1286-1303` が赤になります。しかし gate 内で「classification が transient でも、stdout に対象ID＋QUEがあれば success-visible として扱う」と変異すれば、classifier test は不変です。既存の非ゼロ stdout は `Request State = RUN` だけで対象IDがなく (`:1827-1833`)、この意味論的 M02 は静的に全テストを通過できます。

M07 は3検査を一括削除する coupled mutation なら赤になりますが、一箇所だけの削除は残りの検査に拒否されて生存します。M04も裁定 `ruling.md:113-115` の「手前に同じ拒否がない」という条件を満たしていません。M10は `_best_effort_qdel` を別名へ束縛して呼べば AST の `ast.Name` call 検査を迂回できます。

再現または成立条件: rc=153、stdout が対象IDと `Request State = QUE` を含む応答を gate に一回返す。意味論的M02では qdel が発行されるが、現テストにはこの入力がありません。

成果物影響: mutation trial ledger の M02 は `SURVIVED/matches_expectation=false` になるべきです。表層M04を `KILLED` と記録すると、受理集合を検査していないのに proof chain が成立したように見えます。M02が実装へ混入すれば transport receipt は非ゼロ応答にも `qdel.gate.allowed=true` を記録し、走行へ遷移したジョブを消し得ます。

提案: rc=153でも対象ID＋QUEを stdout に残す専用テストを追加し、qstat一回・qdelゼロ・`qstat-transient-retries-exhausted` を固定してください。M04は受理集合変異としては取り消すかM03へ統合し、M07は3箇所すべてを削除する multi-replacement と明記すべきです。

### [所見 2] M08 は殺せるが、Current State-only の過剰拒否は生存する / 深刻度: major

根拠 (`file:line`): M08正例の応答はすべて `Request State = ...` です (`orchestrator/tests/test_pegasus_dispatch_compute.py:806-847`)。gate parserの唯一の正例も `Request State` と `Current State` の併存形です (`:904-909`)。`Current State` 単独のテスト `:787-803` は監視用 `_scheduler_state()` しか呼ばず、gate parserを通りません。

再現または成立条件: `_target_bound_qstat_state()` に「`Request State` がなければ拒否」を加える。既存の正例・矛盾負例はすべて通過する一方、裁定が受理する次の実応答は拒否されます。

```text
Request ID = 424242.nqsv
Current State = Queued
```

同様に `Held`、`Staging` の Current State-only 受理も未固定です。

成果物影響: Current State形式だけを返す環境では `qdel.gate.scheduler_state=UNKNOWN`、`attempted=false`、`job_may_remain=true` となり、テスト/provenance jobが残ります。親 task-run ledger は rc=16のままなのに、後から旧jobのログが生成され、受入レポートとの対応が切れます。現行task enumでは certified選択への直接経路はありませんが、将来T-360再利用時は試行台帳にも波及します。

提案: `Current State = Queued/Held/Staging` 単独の3正例を helper経由で qdel まで通し、command列を完全一致で固定してください。

### [所見 3] qdel の once-only は失敗経路で検査されていない / 深刻度: major

根拠 (`file:line`): 通常成功の正例は command列を固定します (`orchestrator/tests/test_pegasus_dispatch_compute.py:840-843`)。しかし非ゼロ・例外テスト `:1524-1551` と post-qdel clock例外テスト `:1031-1060` は、qdel command の回数を検査していません。

再現または成立条件: `_best_effort_qdel()` が非ゼロまたは例外を返したとき、fresh qstatを取り直さず同じ qdel をもう一度発行する変異を入れる。最終 `returncode`、`exception`、`job_may_remain` は現状と同じなので既存テストは生存予測です。

成果物影響: 一回目の失敗後に QUE→RUN へ遷移すると、二回目の qdel は fresh snapshotなしでRUN jobを消せます。receiptには `attempted=true` と最終結果しか残らず、受入レポートから複数発行を識別できません。

提案: 両失敗テストで qstat一回・qdel一回の完全な command列をassertし、例外時も同じく一回だけであることを固定してください。

### [所見 4] receipt v2 の「additive拡張」に反して既存 `qdel.reason` を上書きしている / 深刻度: major

根拠 (`file:line`): HEADのrequest discovery失敗は `qdel.reason="qsub accepted but request ID discovery failed"` でした (`HEAD:tools/pegasus/dispatch_compute.py:1397-1403`)。実装後は全gate拒否で `qdel.reason="fresh-qstat-gate-denied"` に置換されます (`tools/pegasus/dispatch_compute.py:1053-1061`)。該当テストは新しい `gate.reason` しか検査しません (`orchestrator/tests/test_pegasus_dispatch_compute.py:1613-1631`)。これは ruling の v2据え置き・additive方針 (`ruling.md:83-85`) にありません。

また、成功qdelの正例 `:840-847` は既存の `request_id/returncode/stdout/stderr` と新しい `job_may_remain=false` を固定していません。

再現または成立条件: qsub出力を解析不能にし、引数なしqstat discoveryも不成立にする。HEADと実装後で同じ v2 fieldの値が変わります。

成果物影響: transport receipt/report の既存 `qdel.reason` 語彙が変わります。repo内consumerはこのfieldを読んでいませんが、v2 proof chainや外部集計が旧値を分類軸にしていれば別カテゴリになります。certified選択値への現行直接影響はありません。

提案: request ID不明経路では旧 `qdel.reason` を維持し、詳細を新しい `qdel.gate.reason` に加えてください。成功正例には既存fieldの保持assertも追加すべきです。

### [所見 5] 現在の暗黙DONE偽緑はゼロだが、gate回数未固定テストが残る / 深刻度: minor

根拠 (`file:line`): `_Scheduler` はstate枯渇後に副作用付き `DONE` を返します (`orchestrator/tests/test_pegasus_dispatch_compute.py:169-181`)。今回、既定tupleへ明示 `EXT` が追加され (`:45`)、RUN/UNKNOWN/HLD負例にもgate用stateが明示されたため、現在の負例で暗黙DONEを消費して通る箇所は静的追跡上ゼロです。

一方、gate qstat回数を固定していないテストは次です。

- `test_missing_compute_marker_relays_collected_stdout` (`:681-695`)
- `test_accounting_grace_failure_relays_collected_stdout` (`:697-707`)
- `test_post_collection_exception_relays_collected_stdout` (`:709-725`)
- `test_fresh_qstat_gate_only_guards_snapshot_not_qdel_time_que_can_run` (`:1004-1028`)
- `test_qdel_result_is_not_overwritten_by_post_qdel_gate_clock_exception` (`:1031-1060`)
- `test_allowed_qdel_failure_records_job_may_remain_and_warns` (`:1524-1551`)

再現または成立条件: gate qstatを余分に発行する、またはgate自体を省略する変異を入れる。前半3テストはgate/qdelを一切assertしていないため、relay側だけ成立して通り得ます。

成果物影響: 現実装のreceipt値を直ちに変える欠陥ではないためminorです。ただし将来の余分なqstatでfake stateがずれ、受入レポートが異なるgate snapshotを検査していても見逃します。

提案: 上記テストへ総qstat回数または `gate.qstat_attempts` 件数を追加してください。根治策は、fake schedulerのstate枯渇を暗黙DONEではなく `AssertionError` にし、DONE/EXTを全テストで明示することです。

## 総括

- 変異検出: M08の常時拒否は確実に赤になります。一方、意味論的M02はSURVIVE予測で、M04/M07/M10は登録方法次第で浅いKILLまたは生存になります。
- テスト弱体化: skip・削除・xfail・assert削減はありません。qdel期待の反転は `:1228,1244,1314,1409,1702,1732,1799,1854` で、いずれも裁定された許可集合縮小です。
- 偽緑: 現在の暗黙DONE通過はゼロ。ただし6テストでgate回数が未固定です。
- 受理集合: valid IDに対するqsub・監視・収集・latch・rc・state_historyは静的差分上維持されています。未裁定の変化は discovery失敗時の既存 `qdel.reason` 上書きです。
- 揮発値: working-tree hashや環境依存payloadの期待値焼き込みはありません。`cleanup_elapsed_s == 91` は注入fake clock由来です (`:974-1001`)。
- meta-test: `test_frozen_artifacts.py:139-153` の23件assertは凍結manifestだけを数え、この差分では赤になりません。test名のexact-vocabulary/count制約も見つかりません。`check_docs` のTASKS exact mapも不変です。
- consumer: `run_tests.py:826-836` と `check_ai_provenance.py:1019-1024` は整数rcだけを消費し、additive fieldでは壊れません。`mutation_harness.py:1008-1095` もqdelを読みません。ただし現在の未commit差分・untracked rulingのままではHEAD/cleanliness pin (`mutation_harness.py:360-390,475-488,625-639`) に拒否されるため、修正後のclean commitからfresh ledgerを作る必要があります。旧ledgerのresumeは不可です。

pytestは実行しておらず、緑は主張しません。