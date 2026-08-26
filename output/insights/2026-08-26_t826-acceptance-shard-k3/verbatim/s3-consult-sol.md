## 総括

最大の blocker は、92 node の閉包が実際には閉じておらず、台帳外 reader による偽赤が既存実走で既に発生している点である。  
plan は candidate commit writer を修理するが、collection/import、runner preflight、複数の実 repo fixture、linked-worktree registry readerを閉じていない。  
さらに現行コードは reader の `@real-repo` suffix を既に除去済みで、222.7 秒の測定はその変更前の tip である。期待利得と D358 再裁定の根拠は成立しない。  
このままの実装は不可。先に lifecycle 全域の閉包、zero-write、cross-host/cross-worktree 到達範囲、受理集合の独立 baseline gateを確定すべきである。

## 所見

### 1. 実 repo 閉包の欠落は既に偽赤を起こしている

- 重大度: blocker
- 根拠:
  - `orchestrator/tests/test_t810_coordinator.py:1104-1150` は `_coordinate_authorized()` を実行する。
  - `tools/pegasus/t810_coordinator.py:1512-1521` から `prepare_group()`、同 `:701-712` から実 common-dir の linked-worktree registryへ到達する。
  - 同 `:524-558` は `.git/worktrees/*/gitdir` を列挙・読取する。
  - この node は `orchestrator/tests/conftest.py:341-460,623-626` の実 repo access mapに無い。
  - 一次資料自身が、この node が別 session の worktree撤去と競合して `FileNotFoundError` となり、a4k2が rc=1になったと記録する。`output/insights/2026-08-26_t1814-shard-time-balance/README.md:127-135`
- 失敗する具体シナリオ: acceptance実行中、別 session が `.git/worktrees/dev-wave-X/gitdir` を撤去する -> 台帳外 node が無 lock で同 pathを読む -> 本来コード差分と無関係な rc=1。
- 成果物影響: 選択済み node が偽赤となり、受入 verdict とその参照ログが変わる。P3の「閉包確定」は実測反例で否定される。

### 2. plan が列挙した scoped fixture と collection/import の穴を、plan 自身が修理していない

- 重大度: blocker
- 根拠:
  - lock は `pytest_runtest_protocol` のみを囲む。`orchestrator/tests/conftest.py:1826-1843`
  - 各 shard は deselect前に全 collectionを行う。`tools/acceptance_shards.py:763-780`
  - import時に実親 repoで Gitを実行する実例がある。`orchestrator/tests/test_codex_worker_launch.py:30-40`
  - 未登録の実 repo session fixtureもある。`orchestrator/tests/test_campaign_import_invariant.py:1073-1075`、consumerは同 `:1078-1101,1218-1253`
  - module fixtureの実履歴 readerは `orchestrator/tests/test_t139_approval_payload.py:69-71` と `orchestrator/tests/test_t793_approval_d291.py:29-37`。
  - planはこれらを `s2-plan.md:30-38` で認識する一方、修理対象はcandidate fixture、bytecode、3 Git helperだけである。同 `:49-53`
  - `PYTHONDONTWRITEBYTECODE` は shard childだけへ入れる計画だが、login collect-onlyも別 processで全moduleをimportする。`tools/run_tests.py:1402-1445`
- 失敗する具体シナリオ: resource shardで実 repo nodeが始まる一方、遅れて開始した別 shardまたはlogin collectionがmodule import、repository scan、履歴fixtureを実行する -> node affinity外で同じrepoを読む、または login側が `__pycache__` を書く。
- 成果物影響: 読取中の外部変更を観測して値が変わるか、collection errorによる偽赤となる。全 shardが同じ collection集合へ到達できず、受理集合または verdictが変わる。

### 3. `read` はzero-writeを含意せず、提案されたzero-write gateも対象面を覆わない

- 重大度: blocker
- 根拠:
  - `RealRepoAccess` は文字列2個だけである。`orchestrator/tests/conftest.py:463-468`
  - access mapの完全性検査は、手書きinventory内部の重なりと和だけを見る。同 `:576-620`
  - planの共通Git環境は3 helperだけを対象とし、collection prewarmで到達する `sort_swo_oracle_receipt_memo._repo_head()` を落としている。`orchestrator/tests/sort_swo_oracle_receipt_memo.py:112-125`
  - shard child自身もnode lock取得前に `git ls-files --deleted` を実行する。`tools/run_tests.py:784-819,2588-2604`
  - `s8b_ratified_freeze` は `cat-file`、`ls-tree`、`ls-files` 等を実 repoへ実行するが、現行環境には `GIT_OPTIONAL_LOCKS=0` も `GIT_NO_LAZY_FETCH=1` もない。`orchestrator/campaign/s8b_ratified_freeze.py:303-337,2617`
  - planのzero-write検査はobject directoryだけのbefore/after fingerprintである。`s2-plan.md:200-202`
- 失敗する具体シナリオ:
  - partial cloneで必要objectが欠落している -> SH readerの `cat-file` がlazy fetchを起こす -> `.git/objects` にpack/tempを書き込む。
  - `core.untrackedCache` やfsmonitorが有効なrepoで、未抑止Git readerがoptional index更新を行う -> SH同士が同時writerになる。
  - index、reflog、`FETCH_HEAD`、worktree登録、submodule indexだけが変わる -> object-only fingerprintは通る。
- 成果物影響: 不足objectが外部fetchで補われて本来の拒否が通過する偽緑、index/object競合による偽赤、または実 repo状態の非証拠化した変更が生じる。
- 追加問題: planの負例は `GIT_OBJECT_DIRECTORY` を外して実 repo objectを実際に増やすため、検査自身が不変条件を破る。負例は犠牲temp repoまたは書込syscall拒否層で行う必要がある。

### 4. lock keyと到達範囲が実資源identityに一致しない

- 重大度: blocker
- 根拠:
  - lock pathはworktree rootのrealpathをhashする。`orchestrator/tests/conftest.py:989-1007`
  - 親repoのobject databaseとlinked-worktree registryはGit common-dirに属するが、lock keyはcommon-dirを使わない。
  - 現worktree自身も `.git:1` から共有 common-dir 配下を指す。
  - lock fileは固定 `/tmp` で、保証を同一host・同一filesystem viewに限定している。`orchestrator/tests/conftest.py:981-993`
  - shardごとに別qsub jobを作り、各jobは1 node要求である。`tools/acceptance_shards.py:1243-1256`、`tools/pegasus/dispatch_compute.py:2839-2850,3117-3129`
  - D435は寿命、到達範囲、authority、過剰拒否を明記するよう要求する。`docs/decisions.md:18127-18149`
- 失敗する具体シナリオ:
  - 同じcommon-dirを共有するmainとlinked worktreeから2 acceptanceを起動する -> root realpathが違うため別lock fileになる -> 共通objects/worktree registryへ同時アクセスする。
  - 同じworktree pathを別compute hostから使う -> lock path文字列は同じでも `/tmp` inodeは別 -> 排他なし。
- 成果物影響: 実repo readerが一時writer状態を観測して偽赤または偽緑になる。affinityは単一invocation内の必要条件だが、cross-worktree、cross-host、別invocationを閉じない。

### 5. timeoutはfail-closedだが、starvationとlock inode交換は未解決

- 重大度: must-fix
- 根拠:
  - 245秒超過は `RuntimeError` を送出するので、静的にはfail-closedである。`orchestrator/tests/conftest.py:1090-1107`
  - 取得順は常にparent -> ccbenchである。同 `:1116-1128`。逆順の直接呼出しは確認できなかった。
  - ただしSH readerの到着を止める公平性機構はなく、plan自身もhard boundが無いと認める。`s2-plan.md:204-218`
  - lock fileはopen後のinodeだけを検査し、flock後にpathのinodeとの再一致を取らない。`orchestrator/tests/conftest.py:1042-1058,1086-1095`
- 失敗する具体シナリオ:
  - reader波が245秒以上連続する -> 正しいwriterがtimeout -> acceptance偽赤。
  - 同一UID processが保持中の `/tmp/...lock` をunlinkし同名fileを再作成する -> 後続processは別inodeをlock -> readerとwriterが同時進入。
- 成果物影響: 前者は受入 verdictの偽赤、後者は検査値の偽緑または偽赤を起こす。
- planのlock metricsは診断値であり、取得公平性、path交換、外側watchdogとの受理条件を強制するgateではない。

### 6. 新gateは受理集合不変を独立に証明せず、一部は両層stubで通る

- 重大度: blocker
- 根拠:
  - merge gateは各shardとloginが「現在の同じコード」から得た集合を比較するだけである。`tools/acceptance_shards.py:592-607`
  - planには変更前のcanonical collection multiset、恒久除外、growth/flaky hold適用結果を独立digestへ固定するgateがない。
  - affinity負例は手作り `ItemRecord` を直接gateへ渡すだけである。`s2-plan.md:110-134`
- 失敗する具体シナリオ:
  - test関数を1件誤って削除する -> 全shardとloginが同じ縮小集合を収集 -> universe一致、partition、finished、scheduler gateが全部通る。
  - `_canonical_item()` がlive itemのaffinity属性を常に無視する -> 手作りItemRecordの負例は赤になるためunit testは通るが、production reportは全affinity `None` になる。
  - `patch_ratified_loader` を別名束縛して呼ぶ -> 名前一致ASTならworker-serial導出から漏れる。
- 成果物影響: 受理集合が1 node以上静かに縮小する、またはreal-repo componentが複数shardへ割れ、受入が偽緑になる。

各新gateの裁定は以下である。

- worker serial exact gate: 現行の過剰markerを検出できる可能性はあるが、別名束縛を解決するcall graphと具体的負例が未定義。要修正。
- affinity closure gate: pure functionの負例は検出力を持つが、producer属性 -> payload -> parser -> allocator -> mergeの結線mutationを殺さない。要修正。
- worker group cardinality gate: `["gw7","gw9"]` は有効な負例。ただしgroup producerの全欠落をexact集合gateへ結ぶ必要がある。要修正。
- K domain/index gate: 現行K=4を拒否し、`bool`、9、重複indexを殺せるので採用可。
- zero-write gate: 対象面不足かつ負例自身が実repoを書くため不可。
- lock metrics: 診断用途としては可。ただしcorrectness gateには数えられない。

権威ある閉包は、grep名ではなく次から引く必要がある。

1. pluginmanagerが登録した全hook、module top-level、全fixture definitionとscope/finalizer、全collected callableをentrypointにする。
2. import、`from ... import ... as ...`、代入alias、decorator、fixture closureをfully-qualified callable identityへ解決して推移call graphを作る。
3. `ROOT`、Git common-dir、CCBench common-dirへのPath provenanceを追い、filesystem read/writeとsubprocess argv/envをsinkとして分類する。
4. live collection artifactのsource path、qualname、fixturedefs、marker、affinityと独立goldenを双方向一致させる。
5. 別名束縛、producer属性欠落、fixture consumer 1件欠落、module import副作用を個別mutationとして殺す。

### 7. 期待利得は変更前測定を現行baselineへ一般化している

- 重大度: must-fix
- 根拠:
  - 現行コードは既にprocess memo 4 node以外の `@real-repo` suffixを除去する。`orchestrator/tests/conftest.py:1702-1718,1811-1815`
  - plan自身もこの事実を認める。`s2-plan.md:3-6,64-66`
  - 222.68秒の鎖は計測tip `9463bcbc` の記録である。`output/insights/2026-08-26_t1814-shard-time-balance/README.md:3-6,80-90`
  - 同資料は残差を定数として扱うなと明記する。同 `:55-57`
- 失敗する具体シナリオ: behavior-neutralなmarker -> affinity置換後、K=4を1走だけ行い、旧307秒との差をmarker縮小効果としてD358へ記録する -> 実際の差はK、compute node、走間32秒ノイズが交絡する。
- 成果物影響: decisions fragmentの値と参照が誤り、D358を解く根拠が存在しない状態で排他緩和を恒久化する。
- planのA/B/B/A方針自体は妥当だが、同一実装上でold-serialとsplitを切り替える機構が計画されていない。

### 8. K=8の導出は成立せず、未閉鎖のcollection窓を拡大する

- 重大度: must-fix
- 根拠:
  - allocatorはcomponentを分割せず、完成componentをbinへ置く。`tools/acceptance_shards.py:323-385`
  - したがって親P6の「K>4はcomponent分割を要する」は誤り。
  - 一方、planの `ceil(4 x 1.9)=8` はduration倍率をshard数へ変換しており、allocation上の根拠にならない。`s2-plan.md:170-172`
  - Kごとに全collectionを繰り返すため、K増加はimport、未登録fixture、runner preflightの回数を増やす。
- 失敗する具体シナリオ: K=8を許可し8 jobが全moduleをcollectionする -> 最大componentはK=4時点から縮まらない一方、unlocked実repo接触が8倍近く発生 -> timeoutまたはraceによる偽赤。
- 成果物影響: 受入 verdictが不安定になり、job Elapseとresource使用量の参照値も悪化する。

### suffixと台帳の閉包

planどおりなら最終nodeidは現行から変わらない。現行も非memo nodeのsuffixを既に除去し、process memo 4 nodeだけを保持する。

参照対象は以下である。

- real-repo、receipt、oracle memo registry: `orchestrator/tests/conftest.py:623-639,762-799`
- growth hold: family key `file::function`。同 `:1491-1496`
- flaky hold:完全nodeid一致。同 `:1499-1503`。現物に `@real-repo` keyはない。
- duration ledger: canonical keyとmarker suffix fallback。同 `:1265-1300`。現物のsuffix keyは `orchestrator/tests/acceptance_duration_ledger.json:13118` の1件。
- shard/JUnit runtime normalization: `tools/acceptance_shards.py:679-705,825-831`
- red checkerとfold gate: plan記載どおり独立またはsuffix正規化済み。
- suffix意味論を直接固定するtest: `orchestrator/tests/test_real_repo_serialization.py:1161-1213`、`orchestrator/tests/test_acceptance_schedule_order.py:720-844`
- historical ledger keyを固定するtest: `orchestrator/tests/test_update_acceptance_duration_ledger.py:329-358`

## 親 brief への反論

- (P1) refuted。flockは登録nodeのruntest protocolしか覆わず、実測済みの台帳外reader、collection/import、runner preflight、未登録fixtureを覆わない。`conftest.py:1826-1843`、`README.md:127-135`
- (P2) real。ただし必要条件としてのみrealである。`/tmp` はhost localで、1 shardは1 qsub job、1 nodeである。`conftest.py:981-993`、`dispatch_compute.py:2839-2850`。別invocation、別worktree、collection窓への十分条件ではない。
- (P3) refuted。T-991の2 status修理はrealだが、閉包完全性はself-partition検査にすぎず、実測反例のT810 reader、candidate writer、未抑止Git経路が残る。`conftest.py:576-620`、`test_t810_coordinator.py:1104-1150`
- (P4) refuted。222.7秒は現行suffix split前のtipの値で、現行baselineは既にreaderをworker分散している。272秒は平均capacity指標、170秒は未実測仮想scenarioである。`README.md:55-75,96-107`
- (P5) refuted。scope外へ送る判断は可能だが、「固定費」「Kで縮まない」という一般化を一次資料自身が否定する。`README.md:55-57`
- (P6) refuted。K>4でもcomponentを分割せず他componentを別binへ置ける。cross-host lockを直ちに要するという含意はない。`acceptance_shards.py:323-385`。ただしK=8にも別の根拠はない。

## plan の採否

- 総括と修理順: 要修正。closure先行は正しいが、修理対象が不足している。
- Q1 worker直列化基準: 不可。T810、runner、collection、fixture finalizerまで含む閉包が無い。
- Q2 affinity分離: 要修正。単一invocation内の設計としては採用可能だが、live producer結線gateとresource identityが必要。
- Q3 shard上限: 要修正。権威の中央集約は採用可。MAX=8の導出とK引上げは不採用。
- Q4新設gate: 不可。K gate以外はalias、producer、zero-write、baseline集合のいずれかを落とす。
- Q5期待利得と測定: 要修正。仮想値は期待値にしない点は採用可。現行splitを切り替える同一tip feature flagを先に設計すること。
- Q6実装分割: 不可。少なくとも「closure/zero-write修理」「behavior-neutral affinity化」「K domainと対測定」の3段に分け、各段で受理集合digestを固定すべきである。

## 未確認事項

- pytest、collect-only、受入全走は実行していない。collection数、選択数、hold適用、worker配置はいずれも実測未確認。
- 各compute hostの `/tmp` filesystem type、mount namespace、PBS requeue時のhost移動。
- partial clone、promisor remote、untracked cache、fsmonitor設定下でのGit write syscall。
- K=4でのlock待ち、保持時間、writer starvation分布。
- `O_CLOEXEC` はexecを閉じるがforkのみではfdを継承する。inventory内からfork-only childがlockを延命する実経路は静的には確定できなかった。
- NFS/Lustre上のflock意味論は本lockが固定 `/tmp` を使うため通常経路では直接該当しないが、全compute hostでlocal filesystemである保証は未確認。
- temp cloneへ移したcandidate fixtureが現行のworktree snapshot意味論を維持するか。
- K=4/6/8のpytest wall、job Elapse、fixture再実行回数、memory peak。