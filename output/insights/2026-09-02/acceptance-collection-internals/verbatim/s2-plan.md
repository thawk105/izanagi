## 結論

最初に opt-in の timeline を別 artifact として実装し、48 worker の起動、collection、xdist 通信、prewarm、lock 待ちを計算ノードの同一 monotonic clock 上で分離するべきです。

静的に採用候補まで進められるのは次の三つです。

- P3 driver 探索の安全な字句 prefilter: collection を約 2.5〜3.0 秒短縮。
- duration ledger の workerinput 圧縮: worker 起動・通信を推定 1〜5 秒短縮。
- controller prewarm と残存 worker collection の重畳: 最大約 22 秒、実効値は timeline 次第。

一方、97.4 秒は「テストが一件も動いていない時間」ではありません。`worker_occupancy` は TestReport duration の和だけであり、その外側にある lock 待ち、worker idle、scheduler gap、終了処理も混入しています。

## report 外費用の正体

現行 report は [`pytest_runtest_logreport()` の duration を加算するだけです](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/tools/acceptance_shards.py:862>)。対して real-repo lock は [`pytest_runtest_protocol()` が inner pytest protocol へ yield する前に取得します](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/orchestrator/tests/conftest.py:2070>)。したがって lock 待ちは setup/call/teardown report に入りません。

正しい分解対象は次です。

```text
pytest process wall
  = interpreter/plugin/configure
  + worker bootstrap
  + collectionとbootstrapの重なり
  + collectionfinish転送・controller queue
  + controller prewarm
  + scheduler・最初のcommand転送
  + test phaseの時間和集合
  + protocol内だがreport外のlock待ち
  + worker idle
  + session終了・worker teardown
```

単純な `wall - max(worker_occupancy)` はこのうち複数を重ねて含むため、各成分の和にも「global zero-test interval」にもなりません。

## 計測パッチ

計測値は `report.json` に追加せず、shard artifact 内の別ファイルにします。これなら [`_REPORT_FIELDS` の閉じた schema](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/tools/acceptance_shards.py:60>) と [`merge_reports()` の六段 gate](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/tools/acceptance_shards.py:603>) を変えません。

**`tools/acceptance_shards.py`**

- [`InternalSpec` 周辺](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/tools/acceptance_shards.py:112>)に、`timeline-controller.json`、`timeline-gwN.json` の導出 property を追加。
- [process-local state 初期化](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/tools/acceptance_shards.py:798>)に opt-in recorder を追加。
- 次の hook を `IZANAGI_ACCEPTANCE_TIMELINE_V1=full-v1` のときだけ有効化する。

  - `pytest_sessionstart` wrapper: controller の xdist setup 全体を囲う。
  - `pytest_xdist_setupnodes`: 48 node setup の開始。
  - `pytest_configure_node(trylast=True)`: workerinput 構築完了。
  - `pytest_testnodeready`: 各 worker bootstrap 完了。
  - `pytest_collection` wrapper: worker の全 collection 開始と終了。
  - `pytest_collection_finish(tryfirst=True)`: xdist が `collectionfinish` event を送る直前の worker 時刻。
  - `pytest_xdist_node_collection_finished` wrapper: controller 受信時刻と、その通知中の conftest/prewarm 所要。
  - `pytest_runtest_protocol` wrapper: protocol 全体。
  - `pytest_runtest_setup`、`pytest_runtest_call`、`pytest_runtest_teardown` wrapper: report に対応する実 phase。
  - `pytest_sessionfinish`: worker ごとの JSON を create-only で保存。

全 process で `time.monotonic_ns()`、hostname、PID、worker id を保存します。worker/controller は同一計算ノードなので monotonic timestamp を直接比較できます。hostname 不一致は解析拒否にします。

**collection 内部**

[shard collection hook](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/tools/acceptance_shards.py:826>)では次を個別計時します。

- hook 入口。
- `records_from_items()` 完了。
- `allocate()` 完了。
- retained/deselected 分割完了。
- `pytest_deselected` 完了。
- shard state 保存完了。

[conftest の外側 collection wrapper](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/orchestrator/tests/conftest.py:1984>)にも、入口、yield 前、yield 後、suffix/reorder 後を記録します。これにより、

```text
collection start → conftest modifyitems入口
```

を test module import と Item/fixture 構築として取り出せます。

**prewarm**

次をそれぞれ直接囲います。

- [`_prewarm_receipt_memo()`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/orchestrator/tests/conftest.py:770>)
- [`_prewarm_oracle_environment_memo()`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/orchestrator/tests/conftest.py:826>)

現在は [`pytest_xdist_node_collection_finished()`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/orchestrator/tests/conftest.py:2150>)の中で同期実行されます。xdist はこの hook が返った後に collection を scheduler へ登録し、全 worker 分が揃った時点で schedule します。該当順序は [xdist `worker_collectionfinish()`](</home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:274>)です。

**lock 待ち**

[`pytest_runtest_protocol()`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/orchestrator/tests/conftest.py:2070>)で、lock 取得開始、全 lock 取得完了、inner protocol 終了を保存します。

さらに純粋な競合待ちを分けるため、[`_real_repo_flock_until()`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/orchestrator/tests/conftest.py:1141>)で最初の `EAGAIN/EACCES` から取得成功までを resource、mode、legacy/common key 別に加算します。同一 process の `Condition.wait()` は [`_real_repo_lock_path_context()`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/orchestrator/tests/conftest.py:1203>)で別記録します。

これにより path 解決・open・stat と、実際の排他待ちを混同しません。

**pytest process 外縁**

[`_run_internal_acceptance_shard()` の subprocess 呼出し](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/tools/run_tests.py:1527>)を囲い、`launcher-timeline.json` に child spawn 前、return 後、rc を保存します。これで plugin import より前と unconfigure 後も閉じられます。

## 計測用環境の配線

新しい env は現状では compute request に運ばれません。[tests task の env allowlist](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/tools/pegasus/dispatch_compute.py:116>)へ `IZANAGI_ACCEPTANCE_TIMELINE_V1` を追加し、[request 環境の射影](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/tools/pegasus/dispatch_compute.py:3429>)の既存経路で渡します。

計測走を正式受入として誤認させないため、[`acceptance_launcher.py` の起動前検証](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/tools/acceptance_launcher.py:555>)では同 env が設定された走を明示的に拒否します。計測は下記の `tools/run_tests.py` 直起動だけで行います。

`conftest.py` は T-2145 と編集面が衝突しているため、同 wave が land または破棄されるまで、prewarm/lock 用パッチを author してはいけません。`acceptance_shards.py` 側だけ先に用意しても lock の直接分離は完了しません。

## 親が実行する argv

instrumentation tip を固定し、Pegasus login から三走を逐次実行します。同時に複数走を投入しません。

```bash
env -u PYTEST_ADDOPTS -u PYTEST_PLUGINS \
  IZANAGI_ACCEPTANCE_SHARDS=3 \
  IZANAGI_TEST_NPROC=48 \
  IZANAGI_ACCEPTANCE_TIMELINE_V1=full-v1 \
  PYTHONDONTWRITEBYTECODE=1 \
  python3 tools/run_tests.py
```

`IZANAGI_ACCEPTANCE_SHARDS=3` は明示し、D1103 の既定経路と同じ K に固定します。`IZANAGI_TEST_NPROC=48` は値の変更実験ではなく、依頼された 48-worker regime の固定です。

stderr の `IZANAGI_ACCEPTANCE_SHARD_ARTIFACTS_V1` が示す session root から、各 shard の次を保存します。

```text
shard-N/launcher-timeline.json
shard-N/timeline-controller.json
shard-N/timeline-gw0.json ... timeline-gw47.json
shard-N/report.json
shard-N/junit.xml
shard-N/dispatcher.log
login-collection.log
```

各走について、tested tip、K=3、worker 数48、三 shard の `observed_universe` digest、login universe、skip/terminal count が一致しない場合は比較対象から外します。

## timeline の集計方法

各 worker について次を計算します。

```text
bootstrap_i
  = worker collection_start_i - controller setupnodes_start

collection_i
  = worker collection_finish_before_send_i - worker collection_start_i

collection_transport_queue_i
  = controller collection_hook_enter_i
    - worker collection_finish_before_send_i

controller_hook_i
  = collection_hook_exit_i - collection_hook_enter_i

initial_schedule_i
  = first_protocol_start - final_collection_hook_exit

lock_wait_i
  = flock競合待ち + same-process Condition待ち

report_excluded_protocol_i
  = protocol elapsed
    - setup/call/teardown interval union
```

`collection_transport_queue` には execnet 転送だけでなく controller event queue 滞留も含みます。prewarm が controller を止めている場合、この区間と prewarm が時刻上重なるため、総 wall を出す際は interval union で一度だけ数えます。

global な可視化は、全 worker の setup/call/teardown interval を統合し、その補集合を取ります。

- spawn から最初の phase までの prefix。
- phase が一件も active でない中間 gap。
- 最後の phase から child exit までの suffix。
- protocol は active だが report phase が無い区間。
- そのうち real-repo lock 待ちに帰属する区間。

次の恒等式が 100 ms または process wall の 0.1%以内で閉じない場合は、観測漏れとして結論を停止します。

```text
pytest child wall
  = phase interval union
  + zero-phase interval union
```

## collection 短縮候補

**候補 C1: P3 driver 探索の字句 prefilter**

- 変更: [`test_p3_exploration_namespace.py:131-147`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/orchestrator/tests/test_p3_exploration_namespace.py:131>)。
- 実装: 全187ファイルの `read_text()` と `ast.parse()` は残し、source text に `exploration_campaign_layout` が無い場合、または `run_campaign` と `CampaignLayout` が両方無い場合だけ `_is_campaign_root_creator()` の全 AST walk を省く。該当 token を持つのは13ファイルです。
- 不変理由: `_call_name()` が返す対象名が AST に存在するなら、その identifier は必ず source text に存在します。false positive は従来の AST 判定へ流れ、false negative はありません。全ファイルの `ast.parse()` を残すので、非候補ファイルの構文エラーも従来どおり collection error です。明示 `ids` は [parametrize 群](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/orchestrator/tests/test_p3_exploration_namespace.py:574>)のままで、node ID は変わりません。
- 効果: line 70 の setcomp 2.91 秒のうち約 `174/187`、約2.7秒を除ける見込み。collection critical path への期待値は2.5〜3.0秒。
- 反証条件: 48-worker trace で同 module の import/AST 区間が1秒未満、または prefilter 後も `ast.walk` 回数がほぼ変わらない。

**候補 C2: collection hook 内の同一 item 再正規化を除く**

- 変更: [`acceptance_shards.py:832-852`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/tools/acceptance_shards.py:832>)。`_canonical_item()` を item ごとに一度だけ呼び、`records` と identity→nodeid の双方へ再利用する。
- 併せて [`conftest.py:1992`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/orchestrator/tests/conftest.py:1992>)で得た `_real_repo_node_id` を item 属性へ保存し、[suffix strip](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/orchestrator/tests/conftest.py:2055>)でも再利用する。
- 不変理由: 新しい値は作らず、同じ item から最初に計算した既存 `ItemRecord` と node ID を再利用するだけです。選択、sort key、marker、deselect は同じ。
- 効果: collection hook 合計0.375秒と `_real_repo_node_id` 累積0.536秒が上限。期待0.2〜0.6秒。
- 反証条件: timeline で二つの hook 合計が0.2秒未満、または cache 属性の読み書きが削減分を相殺する。

**候補 C3: workerinput の duration ledger を一度だけ圧縮**

- 変更: [`_acceptance_duration_worker_payload()`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/orchestrator/tests/conftest.py:1438>)、[`_acceptance_durations_from_worker_payload()`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/orchestrator/tests/conftest.py:1448>)、[`pytest_configure_node()`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/orchestrator/tests/conftest.py:2117>)。
- 現物は19,519 entry、2,513,728 bytesです。現行 `_acceptance_duration_worker_payload()` は worker ごとに `dict(durations)` を作り、約2.46 MB相当を48回送ります。静的試算では shard あたり約118.2 MBです。
- 実装: controller configure で canonical JSONを一度だけ作り、zlib圧縮、raw length、SHA-256、codec literalを持つ閉じた payload にする。現物の圧縮値は約397 KB、48 workerで約19.0 MBです。worker は16 MiB上限、EOF、trailing data無し、digest一致を確認してから現行 validatorへ渡します。
- 不変理由: 展開後の mapping を現行 `_acceptance_durations_from_worker_payload()` と同じ条件で検証し、reorder に渡す float mappingを byte-for-byte相当の値へ戻します。collection、node ID、skip、sort結果は不変です。
- 効果: 約99 MB/shard の初期通信と48回の大きな dict copyを除去。期待1〜5秒。これは純粋な `perform_collect` ではなく worker bootstrap/xdist 通信の短縮です。
- 反証条件: timeline の `configure_node → testnodeready` が既に1秒未満、または圧縮展開CPUで差が消える。

## prewarm 短縮候補

現行 prewarm は最初の該当 `pytest_xdist_node_collection_finished` 内で同期実行され、その間 controller は他 worker の collectionfinish event を処理できません。

採るなら、最初の該当通知で controller-owned background threadを一度だけ開始し、最後の48件目の collection通知で joinします。例外は保存し、最後の hook が返る前に同じ例外を再送出します。従って xdist の [`sched.schedule()`](</home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:298>)より前に成功が確定し、worker payer無し、fail-closed、consumerより前という契約を維持できます。

効果上限は次です。

```text
min(
  prewarm所要,
  最初の該当collection通知から最後のworker通知までの残り時間
)
```

過去値21.9秒を使えば最大約22秒です。親の37秒仮説をそのまま効果値にしてはいけません。通知のばらつきが小さければ効果は0秒です。

更新対象テストは [`test_real_repo_serialization.py:4434`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/orchestrator/tests/test_real_repo_serialization.py:4434>)と[実 xdist 順序 probe](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/orchestrator/tests/test_real_repo_serialization.py:4750>)です。exactly-once、worker payer無し、最終 barrier前完了、例外再送出、途中終了時joinを固定します。

## P1からP4の判定

| 前提 | 判定 | コード根拠 |
|---|---|---|
| P1: 約60秒の主成分は48 workerの全 universe collection | 一部支持、主成分は未証明 | xdist controller は自分ではcollectせず、各workerがcollectします。[DSession `pytest_collection`](</home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:102>)。各workerは[deselect前に全itemsからrecordsを作る](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/tools/acceptance_shards.py:826>)ため冗長性は実在します。ただし report 外にはlock待ちとidleも入るため、60秒への量的帰属は反証可能なままです。 |
| P2: shard-0固有の約37秒はprewarm | 「shard-0固定」を反証、選択shard固有は支持 | prewarmはconsumerを含むcollection通知だけで起動します。[receipt](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/orchestrator/tests/conftest.py:2175>)、[oracle](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/orchestrator/tests/conftest.py:2191>)。shard index 0 の条件はありません。現tipのallocator結果が0なだけで、item/group重量が変われば移動できます。37秒という量も未測定です。 |
| P3: collection削減分がそのままwallへ乗る | 条件付き支持 | xdistは全worker collection完了後にだけscheduleします。[collection barrier](</home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:274>)。したがって最後のworkerまたはcontroller barrierを短くした分はtest開始を前倒しできます。ただしworker起動とcollectionは重なるため、非critical workerだけの短縮はwallへ乗りません。 |
| P4: bytecode/assert rewrite cache warm化は安全 | 一般命題として反証 | compute childには[`PYTHONDONTWRITEBYTECODE=1`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/tools/pegasus/dispatch_compute.py:1596>)が入り、worker自身はcacheを生成しません。既存pycは読めますが、新しい外部cacheはConfig依存とTOCTOUを閉じられず、[D918](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/docs/decisions.md:33152>)が不採用済みです。 |

## 48 worker collection の設計空間

**controllerで一度collectしてItemをworkerへ配る: 成立しません。**

xdist controllerはcollectionを抑止し、workerがローカルな `session.items` を構築します。schedulerが送るのは整数indexだけで、workerは [`session.items[item_index]`](</home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/remote.py:211>)を実行します。pytest Item、fixture graph、module objectをcontrollerからserializeする標準hookはありません。

**一workerだけ全件collectし、他workerはselectedだけcollectする: 現行schedulerでは成立しません。**

`LoadGroupScheduling` は全workerのcollectionが同一であることを要求します。[collection照合とschedule](</home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/scheduler/loadscope.py:357>)。異なるcollectionを許すにはcustom schedulerが必要ですが、現行コードは exact `LoadGroupScheduling` 型だけを受理します。[acceptance側](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/tools/acceptance_shards.py:897>)、[conftest側](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-overhead/orchestrator/tests/conftest.py:2219>)。D1008の既裁定にも反します。

**共有pyc cache: repo内の有効cacheは既に共有、追加cacheは不採用です。**

pytestは競合書込みをPID付きtempとatomic replaceで守りますが、compute workerはwrite禁止です。外部cache、`PYTHONPYCACHEPREFIX`、`compileall` はD918で閉じています。

**別のfull collectorでinvariantを検査し、48 workerにはselected fileだけcollectさせる: 理論上は可能ですが、現行構造の小変更ではありません。**

同じ強さを維持する最低条件は次です。

- 各shardに独立full collectorを一つ置き、deselect前 `ItemRecord` を生成する。
- 三shardのfull universeとlogin universeを現行どおり一致させる。
- selected worker 48本のcollectionを、allocatorがfull universeから導いたselected集合とexact一致させる。
- full collectorの検証完了まで最後の `pytest_xdist_node_collection_finished` を返さず、testを一件もscheduleしない。
- stale manifest、collector失敗、selected差分はすべてinfra reject。
- file closureが保たれているため、worker側の削減は新規 `pytest_ignore_collect` でfile単位に行う。

ただしselected filesをcollection前に知るため、検証可能な事前manifestが別途必要です。manifest更新、Config依存collection、TOCTOU、extra collectorのCPU競合を新たに扱うことになります。理論上の上限は全collection費用の約3分の2、58.6秒を全てcollectionと仮定した最大約39秒ですが、full collectorとstartupを差し引くと実効0〜30秒です。timelineでcollectionが少なくとも25秒以上のcritical componentと確認されるまではNO-GOです。

## 実装順

1. T-2145との`conftest.py`衝突を解消する。
2. opt-in timelineと非certifying境界だけを実装する。
3. 同一tip、K=3、48 workerで三走し、P1〜P4を再判定する。
4. C1を先に実装する。小差分で効果根拠が直接あります。
5. bootstrap/workerinputが1秒以上ならC3を追加する。
6. prewarmの重畳可能区間が5秒以上ならbackground化する。
7. C2は上記後もcollection hookが0.2秒以上なら実施する。
8. 性能採否はinstrumentationを無効化したbefore/post各三走で行い、universe、selected、finished、skip集合をexact比較する。

今回はread-only静的検査だけで、pytest、受入全走、性能測定は実行していません。

## 総括

- 採る候補: P3字句prefilter 2.5〜3.0秒、ledger圧縮 1〜5秒、prewarm重畳 0〜22秒。
- 採ってはならない: assertion無効化、外部pyc cache、selected-only collection単独導入、custom scheduler、lock緩和。
- 反証: P2の「shard-0固定」、P4の包括的安全性。P1は冗長性のみ支持、量は未証明。
- P3は最後のcollection barrierを短縮できる場合だけ支持される。