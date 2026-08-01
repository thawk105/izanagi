## 総括

- **[致命]** `generations == 1` を同一 campaign root で連続実行すれば、2 回目の planner/coder は前回の whiteboard を受け取る。提案 gate は禁止対象を塞がない。
- **[致命]** `_run_workload()` 直呼び、差替え可能な `drive`、`trigger.drive_iteration()` 直呼びは validator を通らず、2 iteration 以上と WAL `COMMIT` へ到達できる。
- **[高]** D106 の真の受理境界は「今回の引数が 1」ではなく「既存 campaign state が空、かつ今回 1」である。段 2 の D96 境界テスト同定は不完全。
- **[高]** 新規テストは stale state、private entry、bool/非 int/下限を覆わず、既存 `generations=3` を `1` にすると role-invalid の停止検出力まで失う。
- **[高]** 親 brief の前提 5・8・9 と「値でなく受理集合だけが変わる」は事実に反する。`result` は閉 enum でなく、既存テストは間接的に受理域・既定経路を固定し、role md は SHA-256 pin 済みである。

## 所見

以下、親 brief は `/home/SFC/tanab/.claude/jobs/2ba05a50/tmp/t244-wave/brief.md`、段 2 プランは同ディレクトリの `s2-plan.md` と略記する。

### [致命] 1 generation の連続実行で禁止 feedback に到達する

- **何が壊れるか:** 段 2 案の validator は「1 回の呼出しに渡された整数」しか見ない。同じ `trial_id`・workload・generation budget で fresh `run_root` を変えれば、2 回目も `generations=1` として受理される一方、planner/coder は前回の `result` を読む。したがって D106 の「1 generation/cell は還流が起きない」は偽である。
- **file:line の根拠:**
  - build 時の campaign layout は外側 `run_root` でなく config 由来である: `orchestrator/campaign/p3_autonomous_workload_trial.py:631-634`。
  - config は workload、`generation_budget`、`trial_id-workload` から作られる: 同 `:400-429`。campaign ID の preimage は search config と trial を含むが `run_root` は含まない: `orchestrator/campaign/ident.py:76-103`。
  - fresh 検査は外側 `run_root` だけ: `p3_autonomous_workload_trial.py:869-877`。
  - planner 前に既存 state を読む: 同 `:474-476`, `:655-676`。同じ whiteboard は coder にも入る: `:694-711`。
  - driver は iteration 後に state を保存する: `orchestrator/campaign/p3_s4_loop_trigger_gating.py:487-509`。
  - D106 自身も reuse を認める: `docs/decisions.md:4876-4879`。それにもかかわらず `:4863-4867` は 1 generation を「還流なし」として許可する。runbook も `:143-146` と `:161-164` が相互矛盾している。
- **成果物への影響:** 2 回目の `attempts.jsonl` と terminal report は予算を `1` と記録する (`p3_autonomous_workload_trial.py:880-891`, `:957-983`) が、`generation_record["harness"]["iteration"]` は 2 になりうる (`:802-804`)。driver が certified なら campaign WAL に `COMMIT` が増える (`orchestrator/campaign/pipeline.py:808-819`, `:854-870`)。本 module が certified selector 自体を直接更新するわけではないが、後段材料 report は同じ WAL と whiteboard を読むため、選択候補の材料集合が変わる (`orchestrator/campaign/layer3_report.py:355-420`)。
- **判定:** **must-fix**。段 2 プランの「異議 2」はコード上正しい。ただし `s2-plan.md:166-169` のように freshness gate を任意扱いするのは誤りである。D106 の禁止を機械化すると名乗るなら必須である。

### [致命] `_run_workload()` と driver seam が gate を素通りする

- **何が壊れるか:** CLI と `run_trial()` の二層を塞いでも、実際に role・driver を回す `_run_workload()` は無検査である。Python の先頭 underscore はアクセス制御ではない。さらに `run_trial()` は `drive` を外部注入でき、1 generation 中に複数回 driver を呼ぶ callable を渡せる。
- **file:line の根拠:**
  - `_run_workload()` は module-level callable で、`generations` をそのまま `range(1, generations + 1)` に使う: `p3_autonomous_workload_trial.py:614-620`, `:655`。
  - そこで role invocation、proposal 保存、driver 呼出しまで到達する: 同 `:677-800`。
  - `run_trial()` は `drive` を引数として公開し、そのまま下層へ渡す: 同 `:841-855`, `:916-930`。
  - `trigger.drive_iteration()` 自体は既存 state を復元して継続する設計: `p3_s4_loop_trigger_gating.py:468-518`。既存テストも public driver の 1→2 iteration resume を固定している: `orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1066-1102`。
  - repository-wide 検索では現在の `_run_workload()` caller は `run_trial()` の同 `:916` だけだが、これは「現在 caller が少ない」という事実であり機械遮断ではない。
- **到達路の判定:**

| 経路 | 段 2 案後 | 判定 |
|---|---:|---|
| CLI `--max-generations 2` | main validator で拒否 | 塞がる |
| `run_trial(generations=2)` | 共通 validator で拒否 | 塞がる |
| `_run_workload(generations=2)` 直呼び | validator なし | **開いたまま** |
| 同一 campaign へ `run_trial(generations=1)` を連続 | stale state 検査なし | **開いたまま** |
| `run_trial(generations=1, drive=multi_drive)` | 1 回の callable 内の iteration 数を数えない | **開いたまま** |
| `_campaign_for()` の cfg/layout で `trigger.drive_iteration()` を反復 | driver は resume を仕様化 | **開いたまま** |
| 別 driver/test が `loop_state.json` を seed 後に `run_trial(1)` | planner 前にその state を読む | **開いたまま** |
| stock CLI の `--workloads ycsb-a,ycsb-b,ycsb-c` | workload ごとに別 ID | whiteboard は分離 |

- **成果物への影響:** `_run_workload()` 直呼びでは terminal report の `run-start/run-finish` 契約すら経ずに proposal、role-attempt journal、campaign state、WAL `COMMIT` を作りうる。差替え `drive` は report 上の `generation=1` と実 driver iteration 数を乖離させる。certified selection bytesへの直接更新はないが、材料 WAL の受理集合が広がる。
- **判定:** **must-fix**。少なくとも `_run_workload()` 冒頭にも validator を置き、layout 決定後・最初の provider 呼出し前に既存 `loop_state` を拒否する必要がある。production API で任意 `drive` を許すかも裁定対象である。

### [高] 複数 workload は state 分離されるが、provider と wall budget は共有される

- **何が壊れるか:** stock provider では workload 間 whiteboard 共有は見つからない。一方、provider instance と全体 wall clock は全 cell で共有される。programmatic に同じ stateful object を複数 role keyへ渡せば、critic の観測を次 workload の planner へ持ち越せる。
- **file:line の根拠:**
  - workload 名・YCSB flag・trial suffix が campaign config に入る: `p3_autonomous_workload_trial.py:400-429`。
  - `prior_reverse` と `current_metrics` は `_run_workload()` ごとに初期化される: 同 `:646-653`。
  - duplicate workload は拒否される: 同 `:863-868`。
  - provider set は workload loop の外で一度だけ生成される: 同 `:892-907`。
  - stock Claude provider が保持する cross-call state は session-id 集合であり、payload feedback ではない: `orchestrator/campaign/claude_projected_provider.py:144-155`, `:230-268`。
- **成果物への影響:** stock CLI では各 cell の campaign WAL/whiteboard は別になる。ただし shared wall budget により後段 cell が実行されず partial report になること、注入 provider により payload・proposal・journal SHA が前 cell依存になることはある。certified selection への直接変更はない。
- **判定:** **must-fix ではなく scope 明記必須**。stock CLI の world 分離と、programmatic provider seam は保証を分けて記述すべきである。任意 provider まで保証するなら裁定パッケージへ送る。

### [高] gate は整数に対しては発火するが、禁止性質に対して恒真に近い

- **何が壊れるか:** `2` を渡せば確かに拒否されるため、構文的な恒真 gate ではない。しかし「cross-generation feedback が無い」という性質と `generations <= 1` が同値でない。positive control が全部通っても禁止運転へ到達できる。
- **file:line の根拠:** D106 の禁止対象は invocation 形式でなく運転条件である (`docs/decisions.md:4863-4867`)。一方、段 2 案は整数 validator のみ (`s2-plan.md:22-43`, `:51-61`) で、同じ plan 自身が stale-state 経路を認める (`:160-169`, `:320-329`)。
- **失敗型ごとの判定:**

| 型 | 判定 | 本提案での再演 |
|---|---|---|
| F9 対象不在 skip (`docs/failures.md:104-116`) | **部分再演** | 対象 file は存在するが、stale state・`_run_workload`・driver seam が検査母集団から丸ごと欠落する。nodeid 不在の rc を KILL と数える危険も残る。 |
| F14 無効 flag を防壁扱い (`:147-155`) | **実質再演** | scalar gate 自体は有効だが、これを「運転禁止の機械化」と記録すると、実効範囲外を防壁に数える同型になる。 |
| F21 配線 presence を live 防壁扱い (`:263-273`) | **部分再演** | main/run_trial の実 call はテスト可能なので exact 同型ではない。ただし実効 state 経路を発火させるテストが無い。 |
| F36 空証明 (`:607-647`) | **現段階では非再演** | `s2-plan.md:339-341` は pytest 未実施を明記している。後段で緑を先書きしない限り該当しない。 |
| F37 rc 握り潰し (`:649-676`) | **提案内には無し** | pipe 実行案は無い。親の mutation/acceptance では単独 rc を守る必要がある。 |
| F59 gate 自身の前処理違反 (`:1188-1198`) | **非再演** | 整数検査は O(1) で build 準備前。freshness 検査を追加しても state 1 ファイルの静的 read で足りる。 |
| F65 失敗 node 0 件 (`:1285-1300`) | **再演リスク高** | Pegasus dispatch は child 出力へ `| ` を付ける (`tools/pegasus/dispatch_compute.py:607-610`)。段 2 plan は rc≠0・node 0 件を MISMATCH にする契約を書いていない。 |

- **成果物への影響:** 恒真に近い保証を新 D/runbookへ書くと、`generation_budget_per_workload=1` の report と WAL を「設計欠陥が発火しない系列」と誤認する。certified selection 自体は直接変わらないが、その材料の有効性判定が変わる。
- **判定:** **must-fix**。gate の保証名を scalar admission に狭めるか、freshness・下層経路まで塞ぐ必要がある。

### [高] テスト母集団が実際の受理集合を代表していない

- **何が壊れるか:** 新規 3 本は fresh tmp path と整数 1/2 しか扱わない。bool guard、非 int、0/負値、stale campaign、private entry、custom drive の削除・境界ずらしが緑で残る。
- **file:line の根拠:**
  - helper は bool・非 int・一般範囲・承認上限の二段検査を計画するが (`s2-plan.md:22-30`)、新規テスト記述は 1/2 と承認上限+1だけ (`:98-115`)。
  - 現行 `test_invalid_role_is_single_attempt_and_stops_cell` は `generations=3` なので、planner-invalid 後の `break` を実際に固定している: `test_p3_autonomous_workload_trial.py:130-154` と production `:688-692`。
  - これを `generations=1` にすると `break` を削除しても loop が自然終了し、`len(generations)==1` が緑になる。段 2 plan の変更案は `s2-plan.md:126-130`。
  - `test_main_accepts_fixture_no_build_at_cli_gate` は fixture+no-build の正当組合せを固定する唯一の名前付き node でもある: `test_p3_autonomous_workload_trial.py:215-227`。default だけの名前へ改名すると責務が隠れる。
  - 非 int 比較が先に行われると素の `TypeError` が出る F68 型だが、負例計画が無い (`docs/failures.md:1351-1370`)。
- **成果物への影響:** 下限検査や bool guard が消えると、空 generation reportや `True` 予算が受理され、report/attempt journal の予算値と実 generation 数が変わる。role-invalid の `break` 退行は将来承認上限を上げたとき、同一 cell に invalid attempt を複数記録する。
- **判定:** **must-fix**。`generations=3` の停止検査は、テスト内だけ承認上限を一時的に 3 へ上げる等で検出力を保持すべきである。bool、非 int、0、stale state、`_run_workload` 直呼びも負例が要る。

### [高] `whiteboard.result` は 3 値の閉 enum ではない

- **何が壊れるか:** `success|fail|rejected` は annotation/comment と現行 producer の慣例であり、load・projection の実効 gateではない。未知値や非文字列値を含む checkpoint が planner/coder payload へ到達する。
- **file:line の根拠:**
  - comment 上の 3 値: `orchestrator/campaign/p3_s4_loop.py:109-118`, `:258-268`。
  - checkpoint loader はキー集合と `delta_pct` だけを検査し、`result=e["result"]` を無検査で格納する: 同 `:367-404`。
  - planner projection も値をそのまま返す: 同 `:273-286`。
  - `check_stop()` は literal `"rejected"` 以外を全て evaluated と数える: 同 `:310-317`。
  - planner/coder/auditor invalid は drive 前に停止し、whiteboard result 自体を書かない: `p3_autonomous_workload_trial.py:688-692`, `:723-727`, `:768-772`。no-build `dry-pass` も result を project しない: `p3_s4_loop_trigger_gating.py:411-428`。
- **成果物への影響:** 未知 `result` は planner/coder payload SHA、role response、proposal、停止判定、後続 WAL 候補を変える。role-invalid/infrastructure failure は粗分類すら次世代へ残らないため、S2 候補の入力前提も変わる。
- **判定:** **must-fix（前提訂正）**。enum closure の実装は S2 scope 外として裁定パッケージへ送ってよいが、「3 値が既に還流する」と無限定に書いてはならない。

### [高] default 変更は「値でなく受理集合だけ」ではない

- **何が壊れるか:** CLI 既定値 `2→1` は、flag 省略時の generation 数、campaign ID、report、journal の実値を変える。
- **file:line の根拠:**
  - 現行 default は 2: `p3_autonomous_workload_trial.py:1017`。変更案は `s2-plan.md:45-48`。
  - generation budget は campaign search config に焼かれる: `p3_autonomous_workload_trial.py:413`。
  - search config は campaign ID preimage: `orchestrator/campaign/ident.py:76-103`。
  - journal/reportにも値を記録する: `p3_autonomous_workload_trial.py:886`, `:966`。
  - 親 brief は「値でなく受理集合」と断言する: `brief.md:50-54`。
- **成果物への影響:** flag 省略 invocation は別 campaign root へ移り、最大 role attempt 数と report cell内容が変わる。直接 certified selection を改変しないが、生成される候補・WAL・材料 report の集合と参照 campaign ID が変わる。
- **判定:** **must-fix**。新 D の「研究状態への影響」に default 値、campaign identity、report/journal 値の変更を明記する必要がある。

### [高] 「role md に byte pin 無し」は事実誤認

- **何が壊れるか:** 今回 role md を編集しないため S1 実装面が直ちに広がるわけではない。しかし brief の DW-O09 根拠は偽であり、将来 S2 で role contract を変えると review ledger・adapter・checkerまで同時に赤になる。
- **file:line の根拠:**
  - 4 role の exact SHA は `orchestrator/codex_roles/review_ledger.py:15-28` に pin 済み。
  - checker は実 role bytes を再 hash して照合する: `orchestrator/codex_roles/spec.py:581-592`。
  - drift negative testも存在する: `orchestrator/tests/test_codex_agents.py:304-352`。
  - adapterにも source SHA が複製・束縛される:
    - planner: `.codex/role-adapters/planner-v4.json:106-124`, `:138-144`
    - coder: `.codex/role-adapters/coder-v4-autonomous-trigger-gating.json:145-165`, `:179-185`
    - auditor: `.codex/role-adapters/auditor.json:132-160`, `:174-179`
    - critic: `.codex/role-adapters/critic.json:72-96`, `:110-115`
  - 現物 SHA は静的 `sha256sum` で ledger と一致した。
  - 一方、`FROZEN_MANIFEST` 23 件に 8c module/runbook/output は無い: `orchestrator/tests/test_frozen_artifacts.py:38-85`。
- **成果物への影響:** 今回 role bytes を編集しなければ pin 値・adapter・certified selection・既存凍結成果物は変わらない。将来 role を触れば role provenance SHA、effective prompt、adapter参照、trial journalの `role_file_sha256` が変わる (`p3_autonomous_workload_trial.py:100-107`, `:304-305`)。
- **判定:** **must-fix（brief 前提訂正）**。S1コード scope の拡張は不要だが、「byte pin 無し」を根拠にしてはならない。

### [高] D96 の境界は scalar 1/2 だけではない

- **何が壊れるか:** 段 2 が同定した `1 accepted / 2 rejected` は「引数の境界」であり、「D106 が禁止した運転」の境界ではない。
- **file:line の根拠:**
  - D96 は新 D と、その受理集合を固定する境界テストを同一変更単位に要求する: `docs/decisions.md:4271-4279`。
  - plan は新 D を予定する: `s2-plan.md:73-90`。
  - 中心テストは hardcoded 1/2: 同 `:98-102`。
  - しかし既存 state + 1 が禁止 feedback に到達する根拠は前述の `p3_autonomous_workload_trial.py:631-676`。
- **成果物への影響:** scalar 境界だけ固定すると、report 上は budget 1のまま stale whiteboard・iteration 2・追加 WAL が受理される。受理集合と材料 report の参照集合が D の説明より広い。
- **判定:** **must-fix**。真の境界は少なくとも次の三点である。
  1. fresh state + `1` は受理
  2. fresh state + `2` は拒否
  3. existing state + `1` は拒否  
  この状態境界を含めない限り、D96 の二要件を満たしたとは判定できない。保証を「per-invocation scalar gate」に狭めるなら、1/2 テストで足りる代わりに D106 全体の機械化とは名乗れない。

## 変異の帰属検査

新規 test body はまだ存在しないため、以下は `s2-plan.md:137-143` の記述どおり実装された場合の静的判定である。

| 事前登録変異 | 指定された expected node | 本当に赤になるか | 帰属上の問題 |
|---|---|---|---|
| gate 削除 | `test_main_rejects_unapproved_generation_budget_before_build_preparation` | **条件付き KILL**。main の validator callだけを消せば、次の `competing_bench_pids()` poison が発火する (`trial.py:1043-1049`)。 | 「helper定義削除」「両 call削除」まで含む曖昧な変異なら boundary/artifact nodeも赤。削除 siteを exact に固定しないと F28 型。 |
| policy 比較 `>`→`>=` | `test_generation_budget_boundary_at_ratified_launch` | **KILL**。1 が拒否される。 | 既存 `test_fixture_trial_runs...` (`test...py:69-86`) と `test_supervisor_error...` (`:157-172`) も 1 で先に赤になりうる。kill は過剰決定で、full-file `-x` の最初の node は新テスト配置次第。 |
| default を 2 に戻す | renamed default CLI sentinel | **KILL**。validator が `_CliGateReached` より前に `AutonomousTrialError` を出す。 | `test_main_accepts_claude_headless_*` (`:230-260`) も flag を省略するため赤。指定 nodeだけの固有帰属ではない。 |
| gate を競合検査後へ移動 | build-preparation test | **KILL**。`competing_bench_pids` poison が赤を作る。 | `claude-headless` build経路を使うこと、移動 siteを exact に固定することが条件。 |
| `run_trial()` validator call削除 | artifact-before-rejection test | **KILL**。run root作成または provider初期化へ進み、期待した早期 `AutonomousTrialError` が得られない。 | helper定義自体の削除ではなく `run_trial` call siteだけを消す変異として固定すべき。 |

F60/F69 上、追加で事前登録すべき生存変異は次である。

| 未登録変異 | 現プランでの結果 |
|---|---|
| `MAX_APPROVED_GENERATIONS = 1` → `2` | hardcoded 1/2 boundary は赤。main testも planどおり error文面 `1..1` を literal 照合すれば赤。ただし `run_trial(...MAX_APPROVED+1)` artifact testは入力も3へ動き、**緑のまま**。 |
| `default=1` → `default=MAX_APPROVED_GENERATIONS` | 現時点では双方1なので**全値テストが緑**。将来上限を2へ上げた変更で defaultも無音連動する。F69 の exact 再演。AST/構造検査か parser既定値の独立 pinが必要。 |
| bool拒否を削除 | `True == 1` なので**全新規テスト緑**。 |
| 非 int拒否・下限拒否を削除 | 1/2 testは緑。0は空 run、1.0は後段の素の `TypeError` になりうる。 |
| `_run_workload()` validator削除 | 対応テスト自体が無いため**SURVIVED**。 |
| freshness gate削除 | freshness gateも対応テストも計画外なので**SURVIVED**。 |
| role-invalid の `break` 削除 | `generations=1` への変更後は既存テストが**緑**。 |

変異 harness 側も、F32/F33/F40に従って exact anchor・注入後 bytes・累積置換・内容一致復元を確認し、F65に従って `rc != 0 && failed node == 0` を KILLでなく MISMATCH に倒す必要がある。nodeid不在の pytest rc=4も KILLに数えてはならない。

## 親 brief の実測値への異議

| 前提 | 判定 | 異議 |
|---|---|---|
| 1. planner payload | **正しい** | common + current_perf + leading + whiteboardで、critic digestは無い (`trial.py:660-676`)。 |
| 2. coder payload | **正しい** | 記載の fieldと一致 (`:694-711`)。 |
| 3. criticだけが red digestを受ける | **正しい** | `critic_digest` は critic payloadだけ (`:806-818`)。 |
| 4. critic cross-generation channelは boolのみ | **正しい** | proposal記録・driveへ行く (`:779`, `:790`) が planner/coder payloadには無い。 |
| 5. 粗い失敗カテゴリが既に存在 | **過大一般化** | producerは3 literalを使うが enum gateは無い。role-invalid・supervisor failure・dry-passは whiteboard resultにならない。 |
| 6. planner contractの機序禁止 | **正しい** | `trial.py:110-123`。 |
| 7. default=2、1..10しか検査しない | **正しい** | `:859-860`, `:1017`。 |
| 8. 受理集合検査も既定値検査も無い | **誤り** | `generations=3` を受理して planner-invalidへ到達するテストが既にある (`test...py:130-154`)。また main acceptance 3本は flag省略経路を受理させる (`:215-260`)。explicit exact-value/boundary testが無い、が正確。 |
| 9. role mdに byte pinなし | **誤り** | review ledger、adapter、checker、negative testで exact SHA固定済み。8c成果物が `FROZEN_MANIFEST` に無いことだけは正しい。 |

加えて、brief の成果物説明 `brief.md:52-54` は default変更が report値・campaign ID・実行世代数を変える事実を落としている。

P1〜P4への反論は次のとおり。

- **P1 default=1:** 反論は成立する。runbook の全例は既に flag を明示している (`runbook:62-95`) ため、repository内運用に限れば required flag化の互換性損失は小さい。required化は将来の default連動も防ぐ。default=1も妥当案だが唯一解ではない。

- **P2 CLIだけ塞ぐ:** 決定的な反論が成立する。D106決定6は programmatic carve-outを明記した (`docs/decisions.md:4845-4846`) が、残余1にはその carve-outが無い (`:4863-4867`)。段2が `run_trial()` も塞ぐ判断は正しいが、まだ `_run_workload` と state reuse が残る。

- **P3 単一解除点:** 反論が成立する。policy上限は一定数でよいが、freshness、entry layer、default独立性は別の不変条件である。また `default=MAX_APPROVED_GENERATIONS` への同値 refactorを現在の値テストは検出しない。

- **P4 S2候補の具体化:** 候補 B〜D の粒度は十分で、大枠への反論は弱い。ただし候補Aで freshness gateを任意扱いした点 (`s2-plan.md:166-169`) は成立しない。現状維持を「1 generationだから欠陥不発」として許可するなら freshness は必須条件である。

## 裁定パッケージ候補

1. **推奨: S1 を「実効 1 iteration + fresh state」へ広げる**
   - main: build準備前の scalar validator
   - `run_trial()`: artifact作成前の scalar validator
   - `_run_workload()`: 直呼び用 validator
   - layout確定後・planner前: `load_loop_state(layout) is not None` を拒否
   - stale-state + 1 の境界テストを D96 testへ追加
   - 同一 root並行起動の claimまで行うなら、freshness checkと実行権取得を原子的にする

2. **狭い案: 保証名を限定する**
   - 「CLI/run_trial の generation引数 2..10を拒否」とだけ記録する。
   - D106の cross-generation運転禁止そのものは引き続き運用規律であり、機械化済みとは書かない。
   - 残余3と `_run_workload`/driver seamを明記する。

3. **driver層の扱い**
   - `p3_s4_loop_trigger_gating.drive_iteration()` は他の正当な human-supervised loopが反復利用するため、全体へ `MAX_APPROVED_GENERATIONS=1` を置くべきではない。
   - 8c専用 wrapperまたは policy/origin bindingを作り、raw driverと8c admissionを区別する。

4. **programmatic seam**
   - production `run_trial` から `drive/providers/preview` 注入を外し、内部 test helperへ分離するか、
   - 任意注入経路は「機械禁止の保証外」と新 Dに明記する。

5. **S2用の別裁定**
   - `WhiteboardEntry.result` の closed enum化
   - role-invalid / auditor-invalid / infrastructure failureを粗分類へ含めるか
   - role mdを変更する場合の review ledger・adapter・checker更新閉包  
   これらは今回実装せず、realな scope外所見として返すのが妥当である。

## 確認できなかったこと

- 指定された必須ファイルはすべて全文読了できた。読めなかった指定ファイルはない。
- sandbox/read-only条件に従い、pytest、CLI実行、mutation harness、build、計測は一切実行していない。緑は主張しない。
- 新規3テストはまだコードとして存在しないため、変異 kill判定は段2記述と現行制御フローに基づく静的判定である。
- 同一 campaign rootへの並行2 process競合は実測していない。逐次 reuseだけで既に禁止経路が成立するため、結論には不要である。
- repository外の既存 programmatic callerは確認できない。repository内検索では `_run_workload()` の外部 callerは無かったが、それは遮断の証明ではない。
- ファイル変更は行っておらず、`git status --short` は空だった。