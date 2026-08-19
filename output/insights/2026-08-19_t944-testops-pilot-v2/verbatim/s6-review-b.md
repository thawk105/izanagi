必読3文書・実装差分・READMEを静的に照合しました。pytestは未実施です。

## 20所見の照合

| 所見 | 判定 | 主な実装位置 |
|---|---|---|
| A2 | 部分 | `tools/run_tests.py:403-580`, `orchestrator/tests/test_run_tests_testops_observation.py:131-162` |
| A3 | 閉鎖（namespace/TOCTOU） | `tools/task_runs/generation.py:192-282`, tests:185-229 |
| A4 | 部分 | `generation.py:774-831`, tests:290-299 |
| A5 | 部分 | `generation.py:111-137,592-626`, `aggregate.py:517-521,813-829` |
| A6 | 閉鎖 | `run_tests.py:936-952,1111-1125,1584-1606` |
| A7 | 閉鎖 | `generation.py:289-349`, `ledger.py:630-681` |
| A8 | 閉鎖 | `ledger.py:647-690`, `generation.py:260-282` |
| A9 | 部分 | `schema.py:25-29,291-296`, tests:823-843 |
| A10 | 部分 | README:86-92, tests:522-539 |
| A11 | 閉鎖 | `run_tests.py:922-998,1252-1331`, tests:385-500 |
| B1 | 部分 | `generation.py:633-675,778-810`, `ledger.py:88-101,630-681` |
| B2 | 部分 | `generation.py:393-467`, tests:232-269 |
| B3 | 部分 | `run_tests.py:1186-1212`, `dispatch_compute.py:78-103,583-584,661-664` |
| B4 | 閉鎖（R-B4SCOPE） | `run_tests.py:1719-1758`, README:95-97, tests:287-303 |
| B5 | 部分 | README:90-97,115-116, tests:522-539 |
| M1 | 閉鎖 | `generation.py:758-771`, `run_tests.py:910-1045` |
| M2 | 部分 | `cli.py:213-220`, `ledger.py:1020-1034`, tests:390-403 |
| M3 | 閉鎖 | `run_tests.py:902-908`, tests:64-104 |
| M4 | 未閉鎖 | `generation.py:774-816`, `ledger.py:1020-1094` |
| M5 | 未閉鎖 | `generation.py:1-911` |

R-B4SCOPE自体は一貫しています。現在のコード・README・テストは「non-`CHILD_RC` は event ではなく `scope-outcome-*` 診断のみ」となっており、旧 `test_bounded_scope_records_all_outcomes` も現実装では改名済みです。旧表現はs2-planの履歴として残るだけです。

## blocker

1. **A4/B1: damaged・unknown・incomplete が cap と開始拒否を迂回する**

   (a) `generation.py:633-647` は damaged/unknown だけなら自動開始を許可し、`ledger.py:630-681` は従来の damaged/unknown 拒否を削除しています。cap判定も `len(report.published)` のみです。`RootReport.published_run_count` (`ledger.py:88-101`) も incomplete を数えません。  
   (b) 裁定R-CLOSEORDER/R-INCOMPLETEの「無条件series-invalid」「publish済みとしてcap消費」に反します。`test_damaged_run_does_not_block_new_automatic_start...` (`tests/test_task_run_generation.py:290-299`) と `test_validate_root_classifies_damaged_and_unknown` (`test_task_run_ledger.py:880-897`) は、裁定と逆の挙動を明示的に固定しています。  
   (c) 9 healthy + 1 damaged、または incomplete を作り、開始後のtask directory数と診断を検査する。既存の「damage後はstart拒否」期待を復元する。  
   (d) 重大度: blocker。

2. **A5: series reader がaggregate/reportまで閉じていない**

   (a) `aggregate.py:813-829` は個別rootの`_locked_root_snapshot()`だけを読み、README header (`aggregate.py:517-521`) にも「series全体の健全性は別途validate-series」とありません。さらに空のseriesは `SeriesReport.is_valid` (`generation.py:111-112`) が真になります。  
   (b) siblingにgenerationが無い、または別generationが壊れていても、個別reportは健全に見えます。fail-closed readerの「空seriesも不正」「既存consumerに接続」の閉じ方が不足しています。  
   (c) healthy generation-1と破損generation-2を作ってreport生成し、明示的series-invalidまたは警告が出ることを検査する。generationゼロのseriesもinvalidにする。  
   (d) 重大度: blocker。

3. **B3/R-COVERAGE: dispatchがchild未起動でもtest_runを記録できる**

   (a) `run_tests.py:1186-1212` はdispatcherの戻り値をintとして受けた後、常に`session.record()`します。`dispatch_compute.py:1520-1533` にはqsub前のsubmission-disabled/orphan-hold returnがありますが、親側はreceiptの`child_started`を読みません。  
   (b) README (`:19,90-97`) は「実際にchildを起動したinvocationのみevent」と約束しています。現在はdispatch setup failureでもtest_run eventを作り得ます。テスト `test_force_dispatch_consumes_shared_sidecar_once` (`:224-255`) もmockの戻り値をchild実行済みとして扱うだけです。  
   (c) auto dispatchを「qsub前failure」で止め、`record_test_run`が呼ばれないこと、固定diagnosticだけであることを検査する。実child成功時だけeventを許可する。  
   (d) 重大度: blocker。

4. **M2: managed generationへのCLI write拒否をselfcheckが迂回する**

   (a) CLI guard (`tools/task_runs/cli.py:213-220`) 対象は`init-pilot/start/event/finish`だけで、`selfcheck` (`:218-219`) は除外されています。selfcheckは`ledger.py:1023-1034`でmanaged root内に一時entryを作ります。テスト (`test_task_run_generation.py:390-403`) はstartしか検査しません。  
   (b) 「managed generationへCLI write不可」「byte作成前拒否」と整合しません。  
   (c) managed generationに対して5コマンドをparametrizeし、呼出し前後のbytesが完全一致することを検査する。  
   (d) 重大度: blocker。

5. **M4: automatic live siblingにselfcheckが接続されていない**

   (a) `start_automatic_test_run()` (`generation.py:774-816`) は`ledger.selfcheck()`を一度も呼びません。README (`:53,100-101`) のselfcheck既定rootはCLIのcheckout-local `output/task-runs` (`cli.py:47-55`) であり、automaticが使うrepo siblingとは別物です。  
   (b) 裁定の「実rootのFS前提を確認してからpilot開始」を満たしていません。  
   (c) sibling rootに対するselfcheck failureを注入し、固定diagnosticを出しつつpytest本体は継続するテストを追加する。  
   (d) 重大度: blocker。

## must-fix

1. **A2のtruth-tableテストが自己比較で恒真**

   (a) `test_four_gate_truth_table_is_unchanged_across_recording_modes` (`orchestrator/tests/test_run_tests_testops_observation.py:131-162`) は、同じ変更後関数をbefore/afterの両方で呼んでいます。  
   (b) gate定数を1項削除しても両方が同じ値になり、テストは通ります。production diffにgate本体のhunkが無いことは確認できますが、テストは裁定の検査になっていません。  
   (c) 固定された期待表を持ち、`PYTEST_ADDOPTS`、selector、unknown option、direct/dispatch/scopeの全経路で検査する。  
   (d) 重大度: must-fix。

2. **B2のcrash recoveryテストが境界を実証していない**

   (a) `generation.py:393-467` はstagingを残してrecovery/quarantineする構造ですが、テスト (`:232-269`) は「init後に手でstagingを作る」1ケースだけです。  
   (b) 裁定はmkdir/init/fsync/rename各境界でkill後の挙動を要求しています。実際のkill、valid recovery、到達不能diagnosticの検査がありません。  
   (c) subprocessで各境界にfault injectionし、再起動後にrename・quarantine・固定diagnosticのいずれかになり、無限retryしないことを検査する。  
   (d) 重大度: must-fix。

3. **R-LEASEの実dispatchテストは既定skipかつUnit A lifecycleをmockしている**

   (a) `test_force_dispatch_real_path_sidecar_roundtrip_when_enabled` (`orchestrator/tests/test_run_tests_testops_observation.py:542-592`) は環境変数未設定時にskipし、`AutomaticRun`、start、finish、record writerをmockしています。  
   (b) scheduler経路とsidecar readは検査しますが、実generationのlease作成・cleanup・ledger appendは検査しません。READMEにも`IZANAGI_RUN_REAL_DISPATCH_TEST=1`の受入条件やskip時のartifact記録がありません。段5記録も「実装済み・未実走」です。  
   (c) acceptanceではskipを許す通常走と、skipなら失敗する`REQUIRE_REAL_DISPATCH`走を分け、実generation leaseとcleanupまで確認する。  
   (d) 重大度: must-fix。

4. **dispatchの環境保持がprovenance taskにも漏れる**

   (a) `dispatch_compute.py:99-102` ではprovenanceのallowlistは空ですが、job script (`:583-584`) と`_job_run()` (`:661-664`) はsidecar/auto markerをtask無関係に保持します。  
   (b) 親環境に古い`IZANAGI_TASK_RUN_SIDECAR`があると、provenance childへ漏れます。tests taskの3箇所は整合していますが、task-specific allowlistの意味を壊しています。  
   (c) provenance dispatchにsidecar/autoを親環境として与え、request/job/childの全段で不在を検査する。  
   (d) 重大度: must-fix。

5. **A9のprivacy検査が実bytesまで通っていない**

   (a) Python/JSON schemaのdenylist (`schema.py:25-29`, `schema_v1.json:71-75`) とnegative test (`test_task_run_ledger.py:823-843`) は妥当です。  
   (b) しかし裁定が要求したsentinelのtask.json/events.jsonl/sidecar/diagnostic横断検査はありません。diagnosticテスト (`test_run_tests_testops_observation.py:192-198`) は固定文字列を直接呼ぶだけです。  
   (c) path、selector、nodeid、argvのsentinelを実direct/dispatch/bounded記録へ通し、全生成bytesとstderrに不在であることを検査する。  
   (d) 重大度: must-fix。

6. **B5/A10のREADMEとテストが一部不正確・弱い**

   (a) README `:90-97` は`tools/run_tests.py`限定、raw pytest/mutation/clone/gate/preflight reject未被覆と正しく書いています。一方、report読み方 (`:115-116`) は「自動観測はpytest + check wrapper」と記載しています。`task_run_check.py`はmanual ID経路であり、automaticではありません。テスト `:522-539` は文言の存在しか見ません。  
   (b) 「actual child only」のevent境界も、上記dispatch failureで破れます。  
   (c) READMEに「check wrapperはmanual」と明記し、`全走行`等の旧表現が無いことをnegative assertionにする。  
   (d) 重大度: must-fix。

7. **M5: production差分が再見積りを大幅超過**

   (a) `tools/task_runs/generation.py` は911行。tracked production差分は追加542/削除137行で、未追跡generationを含めると追加1453/削除137、net +1316行です。  
   (b) s4見積りproduction 480–700行に対し、追加行だけで上限の約2倍です。理由はfd chain、staging recovery、series reader、lease、diagnosticの実装がgeneration.pyへ集中したためと推測できます。安全面を削るべきではありませんが、見積り乖離と未計上理由は記録必須です。README変更は追加29/削除7で、README見積り35–55の範囲内です。  
   (c) 段6 artifactへ「production追加/削除、new file、要求別行数、未削除要求」を分けて記録し、再見積りを確定する。  
   (d) 重大度: must-fix。

## nit

1. **M3は実装閉鎖だが、planned nodeidと検査範囲がずれる**

   (a) `run_tests.py:902-908` はautomaticを常に`unspecified`にし、テスト` :64-104`も親環境の`final`を無視することを確認しています。  
   (b) 実装欠陥はありませんが、planned nameの`test_auto_trigger_is_unspecified_without_explicit_trigger`は存在せず、invalid triggerのautomaticケースも直接はありません。  
   (c) unset/invalid/`final`をparametrizeし、manualの`final`だけ保持するケースを追加する。  
   (d) 重大度: nit。

2. **旧nodeidのin-tree参照は見当たらないが、外部選択実行は壊れ得る**

   (a) `test_run_tests_task_run.py:52-57,142` で旧test名を変更し、現checkout内の旧nodeid参照は履歴文書以外にありません。  
   (b) 現行CIの見落としは確認できませんが、外部の固定nodeid選択は失敗します。また旧ledger testはdamage後の拒否期待自体を変更しています。  
   (c) CI selector検索を受入artifactへ残し、旧nodeid変更と意図した受理挙動変更を別々に記録する。  
   (d) 重大度: nit。

3. **新規production/testファイルがuntracked**

   (a) `tools/task_runs/generation.py:1-911`、`orchestrator/tests/test_task_run_generation.py`、`test_run_tests_testops_observation.py` は`git status`上で`??`です。  
   (b) `git diff main`だけでは中心実装・テストが表示されず、commit/land時に取り込み漏れが起きます。  
   (c) stage6完了前にcached diffへ3ファイルが含まれることを確認し、production差分統計にもnew fileを含める。  
   (d) 重大度: nit。

## 総括

NO-GO。blocker 5件、must-fix 7件、nit 3件。pytestは未実施です。