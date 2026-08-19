実装済みコードの静的敵対レビュー結果です。pytestは未実施です。schema.py と schema_v1.json の objective pattern は同期しており、`/`・`\`・`::`・CR/LFは両方で拒否されています。

### blocker

1. **pilot capを`incomplete`/`damaged`で回避できる**

(a) `tools/task_runs/ledger.py:88`, `:680`、`tools/task_runs/generation.py:669`  
(b) cap判定が`published`だけを数え、`incomplete`を除外しています。さらにautomatic経路は`damaged/unknown`をnon-blocking扱いします。task marker作成前にクラッシュする走行、またはeventsを破損させた走行を繰り返すと、10件を超えてstartできます。  
(c) `_create_file_at(task.json)`失敗を注入して10件作成後に11件目をstartするテスト。damaged runを10件作るテストも必要です。  
(d) **blocker**。

2. **repo/head bindingが同一性を保持しないTOCTOU**

(a) `tools/task_runs/generation.py:192`, `:260`, `:246`、`tools/task_runs/ledger.py:644`, `:690`  
(b) `O_NOFOLLOW`によりsymlink componentは拒否できますが、各componentのinodeを検証していません。祖先directoryを別の実directoryへ差し替えると別namespaceを開けます。またrepo pathを同じbasenameの別checkoutへ差し替えると、series base bindingは一致したまま、`_git_head()`だけ別repoのHEADを記録できます。  
(c) 同名repoを差し替えた後にstartし、taskの`base_commit`と書込先seriesの対応を検査。祖先directoryのreal-directory swapも検査します。  
(d) **blocker**。

3. **sidecar leaseがcrash・cleanup failure後に無限残留する**

(a) `tools/task_runs/generation.py:694`, `:717`, `:481`、`tools/run_tests.py:1081`, `:1197`  
(b) lease directory作成後の`fchmod/fsync`失敗、親のsignal、child crashではdirectoryが残ります。`validate_series()`はtransport directory自体しか検査せず、残留leaseを回収しません。`rmdir()`が余分なfileで失敗しても再試行・quarantineされません。  
(c) lease作成直後の例外、finish前のSIGINT、lease内の余分なfileを注入し、次回startで回収またはquarantineされることを確認します。  
(d) **blocker**。

4. **managed-generationの拒否をrepo移動とcheck/use raceで迂回できる**

(a) `tools/task_runs/generation.py:852`, `:865`、`tools/task_runs/cli.py:213`  
(b) symlink・相対path・現在存在する無関係な同名directoryは概ね閉じています。しかしseries作成後にrepoをrenameすると、`repo_candidate`不在でmanaged判定がfalseになり、旧seriesへCLI `event/finish`を書けます。また判定後のpath差替えをfdで再検証していません。  
(c) `foo` repoでgenerationを作成後、repoを`bar`へrenameして旧generationへのCLI writeを試す。判定直後にancestorを差し替えるraceも検査します。  
(d) **blocker**。

### must-fix

1. **damaged/unknownを無言で継続し、`series-invalid`診断を返さない**

(a) `tools/task_runs/generation.py:633`, `:780`  
(b) 裁定はclosure判定とseries-invalidを分離し、破損時は固定diagnosticにする契約です。しかし`_root_diagnostics_are_nonblocking()`がdamaged/unknownを許可し、diagnosticなしで新規runを作ります。  
(c) damaged run・generation内unknown entryごとに、`pilot-closed:*`ではなく固定`recording-unavailable:series-invalid`が出ることを検査します。  
(d) **must-fix**。

2. **final markerの実体・digestを検証せずclosure扱いする**

(a) `tools/task_runs/ledger.py:396`, `:423`、`tools/task_runs/generation.py:650`  
(b) markerのJSON形状と64hexは見るものの、`reports/<final_report>`の存在と`report_sha256`一致を確認していません。closure直前は`stat`だけで、再検証・root lockもありません。存在しないreportを指すmarkerや、検証後に差し替えたmarkerでpilotを閉じられます。  
(c) report欠落・偽digest・`final_report=".."`を拒否するテストと、validate後のmarker差替えraceを追加します。  
(d) **must-fix**。

3. **signalは再送出するがautomatic sidecar cleanupを飛ばす**

(a) `tools/run_tests.py:922`, `:1033`, `:1043`, `:1151`, `:1255`, `:1297`, `:1308`, `:1332`、`tools/task_runs/generation.py:834`  
(b) bootstrap、admission、queue、bind/release、dispatch、sidecar read、append、finishのcatchは`Exception`限定で、KeyboardInterrupt/SystemExitの再送出自体は正しいです。ただしchild起動・record・diagnostic出力中のsignalでは`session.finish()`へ到達せず、automatic leaseが残ります。bounded childの停止処理も保証されません。  
(c) signalを各call siteで注入し、再送出・lease cleanup・child停止を同時に検査します。task_endをsignal時に無理に追加しない契約も固定します。  
(d) **must-fix**。

4. **B4の「診断のみ」でもchild起動前にtask-runを作る**

(a) `tools/run_tests.py:1597`, `:1602`, `:1750`, `:2037`、`output/task-runs/README.md:95`  
(b) `Popen()`前に`ensure_started()`するため、scope setup failureでもtask directoryが作られ、finishでcapを消費します。pytest child未起動なのにautomatic task-runが残り、READMEの「childを実際に起動したinvocationのみ」と矛盾します。  
(c) `Popen`失敗・attestation failureでtask directoryが作られず、固定diagnosticだけになるテストを追加します。  
(d) **must-fix**。

5. **stderr/CLIのraw exceptionがprivacy境界を迂回する**

(a) `tools/run_tests.py:826`, `:1151`、`tools/task_runs/cli.py:253`、`tools/task_runs/ledger.py:162`  
(b) recording diagnosticの通常生成は固定語彙ですが、diagnostic検査はprefix確認だけです。またdispatcher例外とCLIの`LedgerError`を本文付きで出力し、argv・selector・repo pathを漏らせます。  
(c) sentinel path/selectorを含む例外をdispatcherに返し、stderrに残らないことを検査。diagnosticは完全なallowlist照合にします。  
(d) **must-fix**。

6. **sidecar read/removeがpath再解決でTOCTOU**

(a) `tools/task_runs/generation.py:717`, `:727`、`tools/task_runs/pytest_stats.py:147`  
(b) cleanupは元のlease fdを保持せず、transport/lease pathを再openします。real directory差替えを検出できず、別leaseの固定basenameをunlinkし得ます。`read_sidecar()`もlstat後に`read_bytes()`でpath追従します。  
(c) transport・lease差替えraceとsidecar file symlink差替えを検査し、openat＋fstat identity checkへ寄せます。  
(d) **must-fix**。

7. **`PilotClosedError`の直接CLI経路だけunderscore表現が残る**

(a) `tools/task_runs/ledger.py:54`, `:57`、`tools/task_runs/generation.py:828`、`tools/task_runs/cli.py:220`, `:253`  
(b) automatic経路は`.replace('_','-')`しますが、CLIの`start`は例外本文を直接表示し、`pilot closed: max_task_runs`になります。固定diagnostic vocabularyとの変換契約がCLIで途切れています。  
(c) CLIでcap到達を再現し、`pilot-closed:max-task-runs`またはtyped reasonの一貫した出力を検査します。  
(d) **must-fix**。

8. **R-LEASEの実dispatch証明が常時skip可能**

(a) `orchestrator/tests/test_run_tests_testops_observation.py:545`  
(b)実dispatch往復テストは`IZANAGI_RUN_REAL_DISPATCH_TEST=1`がないとskipされます。裁定が要求したcompute node実証を、skip結果からは確認できません。  
(c) Pegasus上で実dispatchを走らせ、sibling leaseの生成・compute側書込・親側読取・cleanupを実測記録します。  
(d) **must-fix（受入ゲート）**。

### nit

1. **既知flakyは本waveのseries lock変更とは直接結び付かない**

(a) `tools/task_runs/ledger.py:43`, `:798`、`orchestrator/tests/test_task_run_ledger.py:380`  
(b) concurrent appendはgeneration lockを使わず、従来どおりevents fdの2秒flockだけを使います。単独緑・full-suite同時実行で稀に赤という症状は、CPU/IO負荷で2秒を超える説明と整合し、本waveのlock契約変更が真因だというコード上の矛盾はありません。  
(c) `events lock timeout`の実待ち時間を記録し、負荷下で再現率を測ります。pytestは未実施です。  
(d) **nit（ただしテストの安定化は別途必要）**。

2. **record結果の型崩れを成功扱いする**

(a) `tools/run_tests.py:981`  
(b) `_record_task_run()`が不正なtupleを返すと`(True, None)`へ置換され、M1のdiagnosticなしfail-openになります。現実の実装では通常tupleですが、防壁として弱いです。  
(c) `None`・長さ1 tuple・未知diagnosticを返すテストを追加します。  
(d) **nit**。

## 総括

**NO-GO**。blocker 4件、must-fix 8件、nit 2件。TOCTOU、cap回避、sidecar残留、managed write迂回が実装上閉じていません。pytest・mutation・受入走行は未実施です。