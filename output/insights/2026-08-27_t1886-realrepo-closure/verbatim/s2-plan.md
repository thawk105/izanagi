## 総括

現行コードは既に、process memo 4 本を除く real-repo node の `@real-repo` suffix を除去しており、90 node の単一直列鎖ではない。親の 258.73 秒は marker 付き node の ledger 合計であって、現在の runtime 直列長には一般化できない。  
実装対象は「新しい細分化」ではなく、既存の singleton 分散を維持したまま、T810 reader、長寿命 fixture、common-dir lock key の閉包を完成させることになる。  
D358(a) と (c) はともに生きている。特に unprotected Git 呼出しと、worker ごとに再構築される高コスト module/session fixture が残る。  
`tools/acceptance_shards.py` と `tools/run_tests.py` は変更不要。後者は一切変更しない。  
以下は静的検査結果であり、pytest や A/B は実行していない。

## 前提の反証

親 brief の「全 real-repo node が単一 worker」という記述は、現物と一致しない。

- `orchestrator/tests/conftest.py:1702-1718` は `REAL_REPO_PROCESS_MEMO_NODES` 以外から `@real-repo` を除去する。
- この処理は xdist と shard plugin の hook が終わった後、duration reorder より前に実行される (`conftest.py:1811-1823`)。
- `orchestrator/tests/test_acceptance_schedule_order.py:721-844` は「4 本の process memo だけが同一 work unit」という現行契約を明示的に検査している。
- `orchestrator/tests/real_repo_ratified_memo.py:29-32` も同じ設計を正本として説明している。

したがって親の access 別 258.73 秒は「同じ marker を持つ node の合計」ではあるが、現在の排他鎖長ではない。P1 の実行時細分化は既に存在する。

また指定 anchor には drift がある。

- T810 の live reader は現在 `test_t810_coordinator.py:964-1036`、registry scanner の本体は `t810_coordinator.py:524-558`。
- predicates の実親 object writer は現在 `test_s8c_preregistration_predicates.py:3914-3954`、consumer は `:3972-3977`。
- 指定された旧行 `test_t810_coordinator.py:1104-1150` は別テスト、`t810_coordinator.py:1512-1521` は単に `prepare_group()` を呼ぶ上位関数である。

## 実装 plan

### 1. 穴 (i): linked-worktree registry reader

実際の経路は次の三つの live node から始まる。

- `test_t810_coordinator.py:964-981`  
  `test_prepare_group_rejects_forged_git_identity_before_any_mkdir`
- `test_t810_coordinator.py:984-1018`  
  `test_prepare_group_rejects_self_consistent_foreign_git_identity_before_any_mkdir`
- `test_t810_coordinator.py:1021-1036`  
  `test_prepare_group_accepts_external_root_with_anchor_union`

`_LIVE_AUTHORITY_NODES` の独立 literal は `test_t810_coordinator.py:46-62`、AST による完全性検査は `:1396-1448` に既にある。

共有状態は `t810_coordinator.py:524-558` が読む次の範囲である。

- 親 Git common-dir の `worktrees/` directory entry 集合 (`:532-535`)。
- 各 `.git/worktrees/<admin>/gitdir` regular file (`:535-543`)。
- そこに記録された linked worktree `.git` path と、その親 worktree root の実在性・realpath (`:547-557`)。

これは親 working-tree 内容ではなく、親 Git common-dir の linked-worktree registry である。suite 内で親 registry を更新する writer は、`REAL_REPO_ACCESS_BY_NODE`、`git worktree` 呼出し、`patchharness.checkout()` の base root を追った範囲では見つからない。CCBench writer は CCBench common-dir 側であり、親 registry writer ではない。

実装:

- `conftest.py:471-500` の parent-only partition に上記 3 node を追加する。
- access は全て `RealRepoAccess("read", None)`。
- `conftest.py:341-460` の inventory と、`test_real_repo_serialization.py:51-153,155-203` の独立 golden も同時更新する。
- 通常の resource node なので marker は `real-repo`、runtime suffix は除去し singleton work unit とする。node protocol の parent SH が setup/call/teardownを覆う。

負例:

- `test_real_repo_serialization.py` に、`_LIVE_AUTHORITY_NODES` を test module の AST/literal から独立導出し、全てが parent read map に存在することを検査する。
- map からいずれか一つを除く mutation を positive control として同じ検査へ通し、missing node 名付きで赤になることを確認する。
- 候補集合を `REAL_REPO_ACCESS_BY_NODE` 自身から導出しないため恒真ではない。

### 2. 穴 (ii): 実親 object writer の長寿命 fixture

#### invariant 側

書込みは `test_s8c_preregistration_invariant.py:190-214` の次の Git 操作である。

- alternate index への `read-tree` / `add`。
- 親 object database への `write-tree` / `commit-tree`。

fixture は `:361-364`、consumer は次の 5 本。

- `:382` `test_candidate_freeze_matches_contract_and_generation_chain`
- `:422` `test_candidate_freeze_batch_is_bounded_by_frozen_touch_points`
- `:442` `test_repository_tip_binds_current_decider_version_without_activation`
- `:596` `test_candidate_is_not_effective_and_has_zero_satisfied_predicates`
- `:613` `test_wave_files_do_not_contaminate_production_holdout_scan`

#### predicates 側

writer は `test_s8c_preregistration_predicates.py:3914-3946`、fixture は `:3949-3954`、consumer は `:3972-3977` の一つ。

node protocol の lock に載せる案は採らない。session fixture は worker の複数 node より長く生存し、node を access map に登録すると fixture lock と node lock の自己競合も作りうる。

実装:

- `conftest.py:1064-1128` の lock context を返す、状態を持たない fixture factory を追加する。factory 自身は session scope でもよいが、lock は呼出側の `with` 期間だけ保持する。
- invariant の `repository_candidate_commit` は session から module scope に狭める。全 consumer が同一 module かつ同じ retained loadgroup に入るため意味は変わらない。
- predicates 側は consumer が一つなので function scope に狭める。
- candidate 作成中は parent EX:
  `with real_repo_fixture_lock(RealRepoAccess("write", None))`
- object 作成完了後は parent SH を取り直し、その内側で `yield candidate` する。EX 解放から SH 取得まで repo read は行わず、生成済み Git object は immutable なので無保護な観測窓にはならない。
- consumer node は `REAL_REPO_ACCESS_BY_NODE` へ入れない。代わりに後述の long-lived fixture closure に入れ、fixture が lock の全寿命を所有する。

既存 `s8c-preregistration-candidate` marker は削除し、5 consumer と predicates の1 consumerを canonical `real-repo` shard groupへ移す。全 consumer は suffix を保持させ、同一 worker で fixture を一回だけ構築する。

### 3. 穴 (ii'): repository scan fixture

`test_campaign_import_invariant.py:1073-1075` は parent worktree の tracked/untracked file を列挙し、source bytes を `RepositoryScan` へ materialize する read-only fixture である。consumer は `:1078` と `:1218,1222,1227,1231,1235` の6本。

candidate writer とは分ける。

- mode は parent SH。
- session scope は module scopeへ狭める。
- `with parent SH: yield scan_repository(REPOSITORY)` とし、fixture snapshot の全 consumer 寿命を覆う。
- `:1078-1097` は fixture snapshot 以外にも実 repository を再列挙・read するため、SH を yield 中保持することが必要。
- 6 consumer を long-lived fixture group として canonical `real-repo` markerへ移し、同一 workerでscanを一回だけ払う。
- access mapには登録しない。

これは「書込み fixture と同型」ではない。writer fixture は setup中 EX、その後 SH、scan fixture は最初から最後まで SH で足りる。

### 4. 追加で見つかった同型の穴

親 brief の3穴だけでは閉包しない。

`test_s8c_preregistration_predicates.py:198-207` の `current_commit_snapshot` は実親 HEAD、evidence path、Git archive を読み、現在は独立 `s8c-predicate-snapshot` groupにしか入っていない。consumer は `:229-264` の3本である。

- module fixture 全体を parent SH で囲む。
-3 consumer を long-lived fixture groupへ加え、`s8c-predicate-snapshot` decoratorを削除して canonical `real-repo` markerへ統合する。
- この追加を省くと、別 shard/host の parent writer と `/tmp` flock が協調できず、閉包が再び開く。

### 5. 穴 (iii): common-dir 由来の lock key

現行 `conftest.py:989-1007` は worktree root の realpath を hash しているため、同じ Git common-dirを共有する sibling worktreeが別 lockを取る。

変更:

- `conftest.py:981-1007` に resource root の正本を追加する。
  - parent: `_ACCEPTANCE_DURATION_LEDGER_REPO_ROOT`
  - ccbench: `_ACCEPTANCE_DURATION_LEDGER_REPO_ROOT / "external/ccbench"`
- `_real_repo_common_dir(resource, repo_root=None)` を追加し、次を実行する。
  - `git -C <resource-root> rev-parse --path-format=absolute --git-common-dir`
  - Git authority envを除去し、`GIT_OPTIONAL_LOCKS=0` を必ず設定する。
  - rc、単一行、absolute path、strict realpath、directory shapeを fail-closed で検査する。
- `_real_repo_lock_path()` は worktree rootでなく common-dir realpathの bytesをSHA-256へ入れる。
- resource名は引き続き filenameに残し、同じ common-dirを渡しても parent/ccbench lockが衝突しないようにする。
- Git解決失敗時にworktree-root hashへfallbackしない。

CCBench対応物は、submodule worktreeの `.git` marker pathではなく、`external/ccbench` から解決した submodule Git common-dirである。これにより、親の sibling worktreeから見える共有 submodule admin repositoryも同じ keyになる。

## group 設計

`conftest.py:623-639` 付近に次の集合を明示する。

- `REAL_REPO_RESOURCE_NODES`: node protocolでP/S lockを取る既存nodeとT810の3本。
- `REAL_REPO_PROCESS_MEMO_NODES`: 現行4本のまま。一字も意味を広げない。
- `REAL_REPO_LONG_LIVED_FIXTURE_NODES`: candidate 6本、campaign scan 6本、current predicate snapshot 3本の計15本。
- `REAL_REPO_SHARD_NODES`: `RESOURCE_NODES | LONG_LIVED_FIXTURE_NODES`
- `REAL_REPO_RETAINED_LOADGROUP_NODES`: `PROCESS_MEMO_NODES | LONG_LIVED_FIXTURE_NODES`

割付は次の通り。

| class | marker/runtime scope | 排他 |
|---|---|---|
| 通常 resource node。T810 3本を含む | markerは `real-repo`、suffix除去、nodeごとのsingleton | node protocolのSH/EX flock |
| process memo 4本 | `@real-repo` を保持 | 同一process要求とnode protocol lock |
| 長寿命fixture 15本 | `@real-repo` を保持 | fixture自身のparent SH/EX |
| local-only 2本 | markerなし | 実repoへ触れない |

`_strip_real_repo_loadgroup_suffix` (`conftest.py:1702-1718`) は次の契約に変える。

- `REAL_REPO_SHARD_NODES` 外は変更しない。
- `REAL_REPO_RETAINED_LOADGROUP_NODES` はsuffixを保持する。
- それ以外のresource nodeだけsuffixを除去する。

これによりprocess memo 4本の意味は維持される。fixture nodeを process memo と称することはせず、「fixture lifetimeを一workerに閉じる別理由」として別集合で機械固定する。

排他を弱めていないことは、次の三層で固定する。

1. `RealRepoAccess` の全pairについて、同じresourceを共有し一方がwriteなら、同一common-dir lock pathへ到達することをpairwise検査する。
2. fixture access vectorも独立表に入れ、candidate parent write対parent reader、scan parent read対candidate writerを同じ検査へ含める。
3. live collectionから `acceptance_shards._components()` 相当を独立再構成し、競合pairが同じ shard componentにあることを検査する。`/tmp` flockはhost跨ぎで効かないため、この検査は必須。

## `tools/acceptance_shards.py` の判定

変更不要。ただし「複数名を扱えるから常に安全」というP8の一般化は強すぎる。

- `:288-320` は file/group のunion-find connected componentを作る。
- `shard_count >= len(group_names)` の枝 (`:340-346`) は、groupを一つだけ持つ各componentをgroup名順に別shardへ置く。複数groupが同一componentに接続していれば `connected-exclusive-groups` で停止する。
- `shard_count < len(group_names)` の枝 (`:347-356`) は、grouped componentを丸ごとLPT配置する。component内部は分割しない。
- `assignment_closure_gate()` (`:388-411`) は全fileと各groupが一shardに閉じることをallocatorから独立に再検査する。

したがってgroup名を増やしても「同じgroup」は割れないが、別group名に跨る実resource競合はこのtoolには見えない。本planはfixture groupをcanonical `real-repo`へ統合し、さらに conflict-pair-to-component gateを追加するため、tool変更なしでよい。

## exact pin 閉包

### 更新する consumer

- `orchestrator/tests/conftest.py:1670-1699`  
  exact `{"real-repo"}` 検査を `REAL_REPO_SHARD_NODES` 全体へ広げる。
- `conftest.py:1702-1718`  
  retained集合をprocess memo 4本だけでなくlong-lived fixture集合とのunionにする。
- `conftest.py:1749-1757`  
  marker付与対象を`REAL_REPO_SHARD_NODES`へ広げる。
- `orchestrator/tests/test_real_repo_serialization.py:235-240`  
  `_XDIST_GROUP_NAMES_GOLDEN` から `s8c-predicate-snapshot` と `s8c-preregistration-candidate` を除く。
- 同ファイル `:1197-1249,1252-1413,1416-1484`  
  resource node、shard-only fixture node、retained nodeの三集合を別々に監査する。
- `orchestrator/tests/test_acceptance_schedule_order.py:721-844`  
  「4本だけretain」から「process memo 4本はexact、fixture nodeは別理由でretain、通常resourceはsplit」へ更新する。
- `orchestrator/tests/real_repo_ratified_memo.py:29-32`  
  process memo自体は4本のままだが、同じloadgroupに長寿命fixture nodeもいることを説明する。
- `orchestrator/tests/README.md:260-290`  
  shard marker、runtime singleton、fixture-owned lockの三者を区別する。

### 更新しない consumer

- `test_growth_test_holds_contract.py:344,368`: held resource nodeのmarkerは引き続きexact `real-repo`。
- `test_dev_waves_isolation_contract.py:129-154`: fixture-only nodeはresource mapへ入れないため、既存のoverlap検査は壊れない。
- `test_check_acceptance_reds.py:3106-3126`: 任意の`@real-repo` rerun selector正規化であり、group名は維持される。
- `test_update_acceptance_duration_ledger.py:341-348`: historical suffixed ledger keyの互換検査。`_acceptance_duration_for_item()` のfallback契約も維持する。
- `test_real_repo_serialization.py:1498-1596,1631`: synthetic marker shape/name負例なのでcanonical名を維持する。
- `test_real_repo_serialization.py:3636,3639`: receipt memoのxdist hook入力は引き続き`@real-repo`。
- `test_acceptance_schedule_order.py:1474,1531`: scheduler一般のsynthetic groupであり変更不要。
- `tools/pegasus/run_acceptance_nproc_study.py:566,2140`: offline JUnit分類器で、marker文字列は変わらない。ただしこの値を現在のexclusive chain時間と解釈してはならない。
- `tools/run_tests.py:2676`:文言は現状と既にずれているがD838により変更禁止。このwaveでは1 byteも変更しない。
- `docs/decisions.md` のD63/D358/D532/D1008/D1035等: historical decision本文は改変せず、新decision fragmentでsupersede関係を書く。
- `test_s8b_floor_campaign.py:9696`、`test_spool_fold.py:4156` はtmp path/slugの偶然の文字列で、group consumerではない。

## D358 の却下理由

### (a) Git optional lock: 生きている

全90 canonical nodeの所在17 test fileと、その実repo helperを追った。共有rootへ到達するGit呼出しは次のfamilyへ集約できる。

抑止済み:

- repo status/ls-files: `repo_tree_util.py:21-40,109-130`
- CCBench patch/status/common-dir: `patchharness.py:73-90,272-292`
- source digest: `source_digest.py:1785-1804`
- T080 history: `t080_freeze_migration.py:559-580,620-625`
- T810 identity: `t810_validator.py:334-385`
- floor protocol read: `s8b_floor_campaign.py:732-796,866-876`
- RuleOps: `tools/ruleops.py:347,410`

未抑止:

- protocol builderの実親 `git ls-tree`: `test_s8b_protocol_builder.py:70-87`
- known axesの親/CCBench Git: `s1_known_axes_freeze.py:186-193,735-736,867-876`
- measurement freeze: `s1_measurement_freeze.py:104-113,265,428-429`
- sort SWOの実親/実CCBench direct probe: `test_sort_swo_oracle.py:725-733,1008-1020`
- Codex snapshot source reads: `tools/codex_reasoning_ab.py:428-453,879-885`; `_clean_environment()` は全`GIT_*`を除去するが`GIT_OPTIONAL_LOCKS=0`を追加しない (`:3598-3611`)。
- S8C candidate writers: `test_s8c_preregistration_invariant.py:157-187,190-214`、`test_s8c_preregistration_predicates.py:3927-3946`。

共有rootに対する未抑止の`git status`は見つからず、D358が例示したstatus経路自体は修理済みである。しかし依頼の判定規則どおり、未抑止Git経路が一件でもあれば(a)を生存とするなら、上記により(a)は生きている。

### (b) 閉包未確定

現在は生きている。本planでT810、fixture、common-dir key、追加発見した`current_commit_snapshot`を閉じた後に退役できる。

### (c) worker跨ぎfixture重複: 生きている

controller-only prewarmは二系統ともworker guard済みである。

- receipt: `conftest.py:834-870`
- oracle environment: `conftest.py:889-943`

しかし高コストfixtureはそれだけではない。

- `test_codex_reasoning_ab.py:761-810` `benchmark_snapshots`  
  多数consumerは `:1929-3195,6076-6945,8431-9181,11752-11792`。通常resource suffixが除去されるためworkerごとにmodule fixtureを再構築しうる。
- `test_s1_measurement_freeze.py:44-61` `real_known_axes_doc`  
  consumerはfixture closure経由で複数workerへ散りうる。
- `test_campaign_import_invariant.py:1073-1075` `repository_scan`
- S8C candidate session fixture二本。
- `test_s8c_preregistration_predicates.py:198-207` `current_commit_snapshot`

検索範囲は `orchestrator/tests/**/*.py` の全 `scope="module"` / `scope="session"` fixtureと、`REAL_REPO_CLASSIFIED_NODES`を含む全fileのfixture closureである。したがって「prewarm以外に無い」とは言えず、P6(c)は反証される。

## 新設する負例

- T810: live authority AST集合とparent-read access mapの差集合を検査する。候補集合はtest moduleのliteral/AST由来なのでmap自身には含意されない。
- candidate fixture: fake builderを注入し、EX setup中とSH yield中に別threadのparent writerがtimeoutし、fixture解放後に成功することを検査する。単に「lock関数名がsourceにある」検査ではない。
- campaign/current snapshot:二つのfixture SHが同時に入れる一方、parent EXは入れないことを実lockで検査する。
- common-dir key:独立repo、linked worktree、CCBench形のlinked worktreeを作り、同common-dirなら同key、別common-dirなら別keyになることを検査する。
- group closure: live collectionのfixture closureと独立fixture-consumer goldenを比較し、全long-lived consumerが`@real-repo`を保持することを検査する。
- shard closure: conflict matrixから得たpairが同一union-find componentに属することを検査し、別groupを同一shardと仮定する恒真化を避ける。

## 変異事前登録

親が実装後に登録する候補は次の8件。

- `_REAL_REPO_PARENT_ONLY_NODES` からT810の1本を削除  
  → `orchestrator/tests/test_real_repo_serialization.py::test_real_repo_closure_mutations[t810-live-reader-missing]`
- invariant fixtureのsetup modeを`write`から`read`へ変更  
  → `...::test_real_repo_closure_mutations[invariant-candidate-write-downgraded]`
- predicates candidate fixtureからlock contextを除去  
  → `...::test_real_repo_closure_mutations[predicate-candidate-lock-removed]`
- campaign scan fixtureのSHを`nullcontext`へ変更  
  → `...::test_real_repo_closure_mutations[campaign-scan-lock-removed]`
- `_real_repo_common_dir()` がcommon-dirでなくrepo rootを返す  
  → `...::test_real_repo_closure_mutations[parent-key-uses-worktree-root]`
- CCBench resource rootを誤ってparent rootへ向ける  
  → `...::test_real_repo_closure_mutations[ccbench-key-uses-parent-root]`
- `_strip_real_repo_loadgroup_suffix()` のretain判定をprocess memo 4本だけへ戻す  
  → `...::test_real_repo_closure_mutations[fixture-loadgroup-suffix-stripped]`
- shard conflict gateからcandidate writer対parent reader edgeを削除  
  → `...::test_real_repo_closure_mutations[parent-writer-shard-edge-removed]`

全parametrize idはASCIIである。

## P1からP8の判定

- P1: 方向は正しいが、新規案ではなく現行実装済み。access classごとのnamed groupではなく、singleton scopeとSH/EX flockで実現されている。
- P2: process memo 4本がwriter集合と互いに素なのは現物どおり。4本はexact集合のまま維持する。
- P3: 未実装。採用する。
- P4: そのままでは不十分。session寿命のEXは過大で、別shardでは`/tmp` flockも届かない。scope縮小、fixture-owned lock、canonical shard groupへの統合まで必要。
- P5: suite内のparent registry writerが無い点は支持。T810の3 live nodeをparent SH readerとする。
- P6: 反証。上記のとおり(a)(c)とも生きている。
- P7: A/B自体は必要。ただしbaselineは「現行singleton分散」と「suffix strip無効化」の同一commit比較にする。ledger合計やmarker数をwall短縮量に使わない。
- P8: 本planでは変更不要。ただし別group名間のresource競合までtoolが自動で守るわけではないため、conflict-to-component gateを追加することが条件。