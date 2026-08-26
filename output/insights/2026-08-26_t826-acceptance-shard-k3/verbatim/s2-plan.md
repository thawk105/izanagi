## 総括

親案のまま実装するのは非推奨である。affinity 分離と K 引上げ自体は実装価値があるが、先に real-repo 閉包を修復すべきである。  
最大のリスクは、session fixture が実親 repo で `write-tree` / `commit-tree` を実行するのに `REAL_REPO_ACCESS_BY_NODE` 外である点である。  
また現行コードはすでに suffix 除去で大半の worker 直列化を外しており、親の「これから外す」という把握も正確でない。  
推奨順は、実 repo 書込みの hermetic 化、明示 affinity、marker の縮小、K 上限の中央集約、最後に同一 branch の対測定である。  
以下は静的検査だけによる計画であり、pytest や受入全走は実行していない。

## Q1 worker 直列化を残す基準

残す基準は「実 repo に触る node」ではなく、次の性質で定義する。

- 同一 Python process に置かないと process-local memo、長命状態、または lifecycle の契約が成立しない node。
- SH/EX flock では表現できない process identity を共有する node。
- 既存の別 group が守る長命な外部資源を持つ node。その既存 group は維持し、`real-repo` を二重付与しない。

現物では `REAL_REPO_PROCESS_MEMO_NODES` の4 nodeが該当する。`real_repo_ratified_memo` は process-local `lru_cache` を使い、同一 worker に置く理由を明記しているためである（`orchestrator/tests/real_repo_ratified_memo.py:67-85,88-112`、`orchestrator/tests/conftest.py:632-639`）。この集合は人手列挙だけにせず、`patch_ratified_loader` へ到達する test 関数を AST で導出し、marker 集合との完全一致と導出数下限4を `orchestrator/tests/test_real_repo_serialization.py:1962-2011` 周辺へ置く。

### lock の範囲

`pytest_runtest_protocol` の wrapper は lock を取得してから inner protocol を実行するので、対象 node の setup、call、teardown は覆う（`orchestrator/tests/conftest.py:1826-1843`）。関数 fixtureだけでなく、最初の consumer の setup 中に初期化される module/session fixtureのsetupも、その consumerが正しく stampされていれば lock 内である。

ただし、次は覆わない。

- test module の import と collection。
- `pytest_collection_finish` の controller prewarm（`orchestrator/tests/conftest.py:1846-1870`）。
- inventory 外 node が最初に払う module/session fixture。
- node protocol 外の session hookや、fixture closureが不完全な場合の実接触。

実在する共有 fixture は次のとおり。

- `real_known_axes_doc` は実 ccbench sourceを読む module fixture（`test_s1_measurement_freeze.py:44-61`）。
- `benchmark_snapshots` は実親 repoとsubmoduleをclone sourceとして読む module fixture（`test_codex_reasoning_ab.py:761-800`）。
- `repository_candidate_commit` は実親 repoで候補objectを書く session fixtureが2系統ある（`test_s8c_preregistration_invariant.py:190-214,361-364`、`test_s8c_preregistration_predicates.py:3873-3913`）。
- `current_commit_snapshot` は実HEADを読み、temp repoへ写す module fixture（`test_s8c_preregistration_predicates.py:138-177`）。
- `repository_scan` は実作業木を走査する session fixture（`test_campaign_import_invariant.py:1073-1097`）。
- `fixed_decisions_bytes` と `canonical_decisions_blob` も実履歴readerである（`test_t139_approval_payload.py:69-71`、`test_t793_approval_d291.py:29-37`）。

したがって「module/session fixtureならnode lockでは守れない」は一律には正しくない。しかし、fixture consumer閉包が欠けた場合やcollection/import時接触には効かない。この区別を検査へ固定する。

### read 分類の健全性

`RealRepoAccess("read", ...)` は単なる手動分類であり、ゼロbyte書込みを型として含意しない（`orchestrator/tests/conftest.py:463-468,576-620`）。現に次の穴がある。

- 2つの `repository_candidate_commit` はtemp indexを使うが、`write-tree` / `commit-tree` のobject出力先は実親 repoのobject databaseである（`test_s8c_preregistration_invariant.py:190-214`、`test_s8c_preregistration_predicates.py:3873-3905`）。
- shard childはpytest cacheを無効化するが（`tools/run_tests.py:1495-1502`）、bytecode書込みは明示抑止していない。launcherも `PYTHONDONTWRITEBYTECODE` が既に存在するときだけ尊重する（`tools/acceptance_launcher.py:51-61,213-227`）。したがってcollection/import時の `__pycache__` 作成経路が残る。
- real-repo lock fileとreceipt memo cacheは `/tmp` なのでrepo外である（`conftest.py:981-1007`、`real_repo_receipt_memo.py:131-163`）。JUnitもsession root配下でありrepo外である。問題は候補Git objectとbytecodeである。

実装前に次を行う。

- `test_s8c_preregistration_invariant.py:190-214,361-364` と `test_s8c_preregistration_predicates.py:3873-3913` を、temp cloneまたはtemp object storeで候補commitを作り、consumerへ `(temp_repo, candidate)` を渡す形へ変える。実親object databaseには書かない。
- shard dispatch環境へ `PYTHONDONTWRITEBYTECODE=1` を入れる。外側受入argvは変えず、`tools/run_tests.py:2310-2349` のshard child環境だけで固定する。
- acceptanceから到達するread-only Git helperへ統一sanitized envを渡す。対象は `s1_known_axes_freeze._run_git`（`orchestrator/campaign/s1_known_axes_freeze.py:186-193`）、`s8b_ratified_freeze._git/_git_ok`（`orchestrator/campaign/s8b_ratified_freeze.py:303-337`）、`real_repo_receipt_memo._repo_head`（`orchestrator/tests/real_repo_receipt_memo.py:120-128`）。少なくとも `GIT_OPTIONAL_LOCKS=0` とGit repository指示環境の除去を共通化する。

T-991が実際に直した `git status` 経路は `repo_tree_util._repo_status` と `source_digest._tracked_status_paths` の2本で、両方に `GIT_OPTIONAL_LOCKS=0` がある（`repo_tree_util.py:25-40`、`source_digest.py:1785-1804`、記録は `docs/archive/worklog-phase3-0813-524.md:65-88`）。

`silo_ladder_rung1.py` の未抑止 `git status` 2経路は、受入testから実repoについては到達しない。

- `third_party_source_contract` のstatusは `silo_ladder_rung1.py:930-980`。唯一のtest呼出しは不存在rootでloop前に拒否される（`test_silo_ladder_rung1_driver.py:1069-1073`）。
- `_dependency_contract` のstatusは `silo_ladder_rung1.py:2066-2109`。呼出しは実build/job経路（同 `:2286,3768-3782,4098`）で、test側参照はない。

この「到達しない」部分は親推定どおりだが、閉包全体が完全という結論にはならない。

### nodeid 台帳への影響

明示 affinityへ移しても、worker分割対象の最終nodeidは変えない。現行も `_strip_real_repo_loadgroup_suffix` が大半をすでにunsuffixedへ戻している（`conftest.py:1702-1718,1811-1815`）。process memo 4 nodeだけは引き続き `@real-repo` を持つ。

参照関係上の台帳は次のとおり。

- real-repo inventory/access/process memoは `file::function` 形で、`_real_repo_node_id` がparam/group suffixを正規化する（`conftest.py:623-639,762-790`）。
- receipt/oracle memo consumer台帳も専用normalizerで `@...` を落とす（同 `:773-799`）。
- growth holdは `file::function`、flaky holdは完全nodeidである（同 `:1524-1545`、`growth_test_holds.py:652-678`、`flaky_test_holds.py:294-303`）。最終nodeidを現状維持するため登録簿変更は不要。
- acceptance duration ledgerはcanonical unsuffixed keyが基本で、historical suffixをfallbackする（`conftest.py:1260-1304`）。現物の `@real-repo` keyは1件だけ（`acceptance_duration_ledger.json:13118`）。markerを外すとfallback情報を失うため、新 affinity属性もhistorical fallback候補として読むよう `conftest.py:1289-1303` を改訂する。ledger自体は書き換えない。
- shard inventory/reportのnodeidは `_canonical_item` が既にgroup suffixを除く（`acceptance_shards.py:679-705`）。変わるのはrecordの `group` / `affinity` で、nodeidではない。
- fold gateは `test_spool_fold.py::...` の独立登録簿で、real-repo nodeとは交差しない（`fold_gate_nodes.py:91-143`）。
- red checkerはgroup suffix付きログを明示的に解釈できる（`tools/check_acceptance_reds.py:589-629`）。

## Q2 affinity の分離

最小機構は、pytest markerを増やさず、collection itemのprivate属性と `ItemRecord.affinity` を使う形である。

### production変更

- `orchestrator/tests/conftest.py:950` 付近に `_REAL_REPO_AFFINITY_ATTR` と `REAL_REPO_WORKER_SERIAL_NODES` を置く。後者はprocess memo集合と一致させる。
- `conftest.py:1741-1758` で、全 `REAL_REPO_RESOURCE_NODES` へ `affinity="real-repo"` 属性をstampする。一方 `xdist_group("real-repo")` は `REAL_REPO_WORKER_SERIAL_NODES` だけへ付ける。
- 既存の別 `xdist_group` があるnodeは二重markerにせず、affinityだけを付ける。
- `conftest.py:1670-1699` は全resource recordの `affinity=="real-repo"`、process memoだけの `group=="real-repo"`、それ以外にreal-repo groupがないことを検査する。
- `_strip_real_repo_loadgroup_suffix` とpost-yield strip（`conftest.py:1702-1718,1811-1815`）を削除する。

`tools/acceptance_shards.py` は次のように変える。

- `:50` のinternal report schemaをv2へ上げる。
- `ItemRecord`（`:85-90`）へ `affinity: Optional[str] = None` を追加。
- `_record_payload` / `parse_records`（`:226-262`）を exact 4 field `nodeid,file,group,affinity` にする。`affinity` の実環境値域は `None` または `"real-repo"` の閉集合とする。
- `_canonical_item`（`:679-705`）は実markerから `group`、private属性から `affinity` を独立に読む。
- `_components`（`:288-320`）へ `a:<affinity>` vertexを足し、file-groupとfile-affinityの両辺をunionする。component reportにも `affinities` を出す。
- `assignment_closure_gate`（`:388-411`）はfile、group、affinityの3写像すべてでshard集合のcardinalityが1であることを独立検査する。
- `_scheduler_gate`（`:440-447`）と `_scheduler`（`:834-847`）は変更しない。worker schedulingは引き続きloadgroupで、affinityはschedulerへ見せない。

### report / JUnit consumer

- `observed_universe` のentry shapeとdigestが変わるため、worker payload、controller state、`validate_report_evidence`、`merge_reports`をv2 recordへ更新する（`acceptance_shards.py:450-537,540-607,850-905`）。
- top-level reportには新しいaffinity写像を重複して持たせない。`observed_universe + selected` からmerge側が再計算する。
- `group_to_workers` は実worker groupだけを表し、affinityを混ぜない（同 `:920-959`）。
- JUnit nodeidにはaffinity suffixを付けない。`_normalize_runtime_nodeid` と `merge_junit` はロジック変更不要（同 `:641-676,825-831`）。
- login collect-only universeはnodeidだけなので変更不要（`tools/run_tests.py:1380-1458`）。
- `test_real_repo_serialization.py:1380-1448` と `test_run_tests_shards.py:62-110,706-796` のfixture record、payload、mutation killerを4 fieldへ更新する。
- `test_acceptance_schedule_order.py:720-833` はsuffix strip順序検査を削除し、「affinity stamp後もduration reorderが同一nodeid集合を保つ」検査へ置換する。

機械検査の署名は次の形にする。

正例:

```text
records = (
  ItemRecord("a.py::test_read",  "a.py", None,        "real-repo"),
  ItemRecord("b.py::test_memo",  "b.py", "real-repo", "real-repo"),
  ItemRecord("c.py::test_other", "c.py", None,        None),
  ItemRecord("d.py::test_other", "d.py", None,        None),
)
assignment_closure_gate(records, allocate(records, 2).selected) is True
```

負例:

```text
selections = (
  ("a.py::test_read", "c.py::test_other"),
  ("b.py::test_memo", "d.py::test_other"),
)
assignment_closure_gate(records, selections) is False
```

この負例はfile閉包もgroup閉包も単独では通るが、同じ `"real-repo"` affinityが2 shardへ割れたため発火する。したがって恒真ではない。

## Q3 shard 上限

上限の権威は1か所へ集約する。`acceptance_shards.py:49-69` に例えば次を置く。

```text
MIN_PARALLEL_SHARDS = 2
MAX_PARALLEL_SHARDS = 8
SUPPORTED_PARALLEL_SHARDS = frozenset(range(2, MAX_PARALLEL_SHARDS + 1))
```

`type(value) is int` を含む共通predicateを公開し、別moduleで `{2,3,...}` を再列挙しない。

変更閉包は次のとおり。

- `acceptance_shards.allocate` の `{2,3}`（`:323-330`）。
- `acceptance_shards.create_session` の `{2,3}`（`:970-988`）。
- `_emit_aggregate_no_verdict_attestation` の `{2,3}`（`:1149-1159`）。
- `run_tests._acceptance_shard_request` の字句閉集合（`tools/run_tests.py:253-264`）。`1` はopt-out、並列値は共有権威から生成する。
- `_resolve_acceptance_shard_count` の `{2,3}`（同 `:267-298`）。
- internal child検証（同 `:1460-1488`）。
- `explicit_shard_mode` 判定（同 `:2472-2492`）。
- `test_run_tests_shards.py:168-290` のpositive/negative、resolver、internal spec、rc=16期待。
- no-verdict testのK列挙（同 `:976-1062`）。
- report index gate自体は `range(expected_k)` で一般化済み（`acceptance_shards.py:414-421`）。K=4とK=MAXのmissing/duplicate正負例だけ追加する。
- `merge_reports`、`run_parallel`、report loader、JUnit path生成は既に `range(shard_count)` なのでロジック変更不要（同 `:540-638,1048-1059,1181-1390`）。K=4のmerge/JUnit正例を追加する。

launcherとwaiterは外側argvを増やしてはならない。

- `acceptance_launcher` はexact `["python3","tools/run_tests.py"]` を維持する（`tools/acceptance_launcher.py:20-28,126-135`）。
- `test_acceptance_launcher.py:280-300` のenvをK=4へ更新し、internal shard optionが外側argvに入る負例を維持する。
- `dev_wave_wait` はKをargvへ埋め込まずambient envを継承する（`tools/dev_wave_wait.py:800-838,3735-3774`）。`test_dev_wave_wait.py:4538-4558` 付近に `IZANAGI_ACCEPTANCE_SHARDS=4` がenv preflightで拒否されず、launcher argvがexactなままという正例を追加する。
- 受入receipt schemaへ `shard_count` を足さない。receiptはlog SHAで実行ログを束縛し、既存exact field集合を保つ（`acceptance_launcher.py:347-398`、`test_dev_wave_land.py:1012-1024`）。schema変更は不要。
- `tools/pegasus/run_acceptance_nproc_study.py:598,2144,2393,3382-3384` のK=2は特定study armの定数であり、一般上限gateではない。ここは変更せず、一般上限と混同しないtestを残す。

上限は4ではなく8を推奨する。ただし既定値は4でよい。

K=4 plateauは台帳durationを現在の連結成分へ投影した結果であり、実走では台帳比が最大1.9倍動く。最小値の証明ではなく運用上限を決めるなら、`ceil(4 × 1.9) = 8` まで入口を開け、K=4/6/8を実測できるようにするのが妥当である。K>4でもreal-repo affinity component自体は分割せず、他componentをさらに分けるだけなので、cross-host lockは不要である。8が最適という意味ではなく、4を閉上限にして再改修を要する事態を避けるための明示上限である。

## Q4 新設 gate

### 1. worker serial集合のexact gate

入力は実collection reportのmarker列とfixture closureで、既存test reportに `marks` / `fixture_closure` として存在する（`test_real_repo_serialization.py:1005-1065`）。

値域は、marker数0または1、group名は非空文字列、fixture scopeはpytestが報告する `function/module/session`。process memo語彙へ到達する関数集合と `REAL_REPO_WORKER_SERIAL_NODES` を双方向一致させ、導出数4以上を要求する。

### 2. affinity closure gate

入力はshard `report.json` の `observed_universe[*].affinity` と `selected`。producerは `acceptance_shards.py:936-959`、consumerは `:540-607`。

実環境値域は `None` または `"real-repo"`。正負例はQ2の署名を使う。file/groupだけをsplitした既存負例とは別に、affinityだけをsplitするため恒真にならない。

### 3. worker group cardinality gate

入力は実reportの `group_to_workers`（`acceptance_shards.py:921-949`）。現producerが作るworker名はxdistの非空 `worker_id`、serial fallback、または観測欠落時の `"unobserved"`（同 `:799-809,923-929`）。

受理時は各groupのworker集合をexactly oneとし、`"unobserved"` を拒否する。正例 `{"real-repo":["gw7"]}`、負例 `{"real-repo":["gw7","gw9"]}` とする。現行validatorは非空・unique・occupancy内だけを要求し、複数workerを許しているため改訂が必要（同 `:486-519`）。

### 4. K domain / index gate

入力はenv文字列、internal specの整数、reportの `shard_count` / `shard_index`。実環境ではenvは任意文字列、internal値はJSON由来整数、report indexはproducerの `range(K)` である。

受理値をenvでは `"1"` と `"2"` から `"8"`、並列内部ではexact int 2から8、indexは0以上K未満とする。`bool`、先頭ゼロ、空白、9を負例にする。

### 5. real-repo zero-write closure

候補commit fixtureの実repo書込みを殺す正負例を、両fixture moduleと `test_real_repo_serialization.py` に置く。入力はfixture前後の実repo object directory tree fingerprintとtemp repo fingerprintである。実値はSHA-256、file count、byte countの非負整数。正例では実repo fingerprint不変かつtemp側増加、負例では `GIT_OBJECT_DIRECTORY` を外した合成helperが実repo fingerprintを変え、検査が発火する形にする。

### lock timeout

245秒の元の導出は、split後には成立しない。旧loadgroupでは同一worker内に内部lock競合がほぼなく、主に外部sessionへのfail-close期限だった。48 workerへreaderを散らすとwriter待ちとreaderの後続波が発生し、flockにwriter公平性のhard boundもない（`conftest.py:981-984,1065-1107`）。

ただし現成果物にlock待ち時間fieldはない。`worker_occupancy.duration_s` はsetup/call/teardown合計で、lock待ちだけを分離できない（`acceptance_shards.py:799-809`、実測説明 `output/insights/2026-08-26_t1814-shard-time-balance/README.md:55-57`）。したがってDW-O13上、今この場で新timeout値やtimeout gateを採用してはならない。

実装時はreport v2へ診断専用 `real_repo_lock_metrics` を追加する。各resource/modeについて `acquisitions>0`、有限非負の `wait_max_s` / `hold_max_s` を記録し、resourceのないshardは `{}` とする。最終値の導出は次とする。

- 母集合: 同一tip、K=4、48 worker、受入exact形を少なくとも3走した全lock acquisition。
- regime: Pegasus compute、同じsuite、growth holdの同じopt-in状態。
- `Qmax`: 全取得成功の最大待ち、`Hmax`: 最大保持時間。
- 候補 `T = ceil(2.0 × Qmax)`。
- `T + Hmax + finalization reserve < 外側watchdog` を満たさなければ、timeoutを切り詰めずsplit採用を止める。

それまでは245秒をfail-close互換値として維持するが、「5分上限を保証する値」とは報告しない。

## Q5 期待利得

親の170秒は次の仮想計算としては再現できる。

```text
real-repo component capacity
= 2174.1 / 48 × 1.9
= 86.1 秒

仮想 wall
= max(86.1, 最長単体 42.77) + 残差 84.61
= 170.7 秒
```

したがって307.29秒からの短縮率は約44.5%で、数値上の「約170秒、約45%」は整合する。

一方K=2の272秒は、観測された最遅非鎖worker 191.4秒ではなく `W_shard0/48 = 187.1秒` を使っている。

```text
平均capacity使用: 187.1 + 84.61 = 271.7 秒
観測最遅使用:     191.4 + 84.61 = 276.0 秒
```

272秒はcapacity指標であり、wall期待値ではない。

170秒が成立するには少なくとも次が必要である。

- component内workが48 workerへ十分均等に散る。
- 台帳から実走への膨張が1.9倍以内で、component間で極端に偏らない。
- module fixtureのworker別再実行がこの倍率内に収まる。特に `benchmark_snapshots` と `real_known_axes_doc` の重複setupが増える。
- writer待ち、reader波、I/O・memory競合がcritical pathを増やさない。
- 39.2から84.6秒の残差がK=4で増えない。
- real-repo以外のgroupやcomponentが86秒を超えない。
- 比較するcompute node性能が同程度である。

これらは未実測なので、170秒は「K=1 durationを固定した仮想capacityシナリオ」と報告し、期待値や下界とは呼ばない。D713の4層では次を別々に出す。

- queue待ち: 記録するが目標から除外。
- job Elapse: 各shardと最大値。
- pytest wall: 各shardと最大値。これを主効果とする。
- 外側wall: waiter全体として記録するが、所要採否には使わない。

測定は同一branch上で、K=2旧serial / K=2splitをA/B/B/A、続いてsplit K=2 / K=4を交互に行う。既存同一tip K=2だけでもwallが32.27秒動いているため（`README.md:96-107`）、最終受入1回と過去307秒の単純差では採否を決めない。

## Q6 分割

実装子は1単位でよい。affinity record schema、conftest hook順序、nodeid normalization、K domain、report merge testが相互にlockstepであり、分けると中間commitが必ず不整合になる。

編集対象は少なくとも次を同一所有にする。

- `orchestrator/tests/conftest.py`
- `tools/acceptance_shards.py`
- `tools/run_tests.py`
- `orchestrator/tests/test_real_repo_serialization.py`
- `orchestrator/tests/test_acceptance_schedule_order.py`
- `orchestrator/tests/test_run_tests_shards.py`
- `orchestrator/tests/test_acceptance_launcher.py`
- `orchestrator/tests/test_dev_wave_wait.py`
- 2つのcandidate fixture module
- reachable Git helper 3 module

1単位なので編集ファイル所有の素集合条件は自明に満たす。

## 親 brief への反論

- **(P1) refuted.** SH/EX flockはnode protocol全域を覆うが、collection/importとinventory外session fixtureは覆わない（`conftest.py:1826-1848`）。実親object writerがinventory外に存在する（`test_s8c_preregistration_invariant.py:190-214,361-364`、`test_s8c_preregistration_predicates.py:3873-3913`）。
- **(P2) real.** lock pathは `/tmp` で同host・同filesystem viewに限定される（`conftest.py:981-994`）。全resourceを同一shardへ留めるaffinityは必要である。
- **(P3) refuted.** T-991が直したstatus経路2本とsiloの未到達推定は正しいが、92 node閉包は後発session Git object writerを含まない。`RealRepoAccess` の完全性gateは既存登録集合内部のpartition一致しか検査しない（`conftest.py:576-620`）。
- **(P4) refuted.** 170秒は仮想capacity算術として再現できるが、K=2の272秒は平均 `W/48` を使い、観測最遅workerなら276秒になる。module fixture再実行、lock待ち、残差変動も未計上である（`README.md:37-57,80-105`）。
- **(P5) refuted.** 残差をscope外に送る判断は妥当だが、39.2から84.6秒を「固定費」と呼び、Kで変わらないと断定する根拠はない。一次資料自身が「定数として扱ってはならない」としている（`README.md:55-57`）。
- **(P6) refuted.** K=4 plateauは台帳投影のcomponent値であり実wallの上限ではない。K>4はreal-repo componentを割らず他componentだけをさらに分割できるので、直ちにcross-host lockを要しない（`acceptance_shards.py:288-385`）。明示上限は8を推奨する。

## 未確認事項

- K=4、48 workerでのlock待ち時間・保持時間分布。
- `benchmark_snapshots` と `real_known_axes_doc` がworker分散後に何回再実行され、総仕事量とmemory peakをどれだけ増やすか。
- temp cloneへ移したcandidate fixtureが現行と同じ検出力を保つか。
- K=4/6/8それぞれのpytest wall、job Elapse、残差、dispatcher資源消費。
- K=4で全resource nodeがexactly one shardへ入り、process memo 4 nodeだけがexactly one workerへ入ること。
- 受理集合、collection数、恒久除外、growth/flaky hold、fold gate集合の実測不変性。
- 本回答ではpytest、collection subprocess、受入全走を実行していないため、いずれも緑とは報告しない。