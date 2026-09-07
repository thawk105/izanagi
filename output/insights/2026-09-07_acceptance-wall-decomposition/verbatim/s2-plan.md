## 総括

read-only の段 2 として調査し、ファイルは変更していない。

結論は次のとおり。

- 親の「147 回 collection」は訂正が必要である。xdist controller は collection せず、全量 collection は `3 shard × 48 worker + login collector = 145 回`。controller が worker payload を集約する実装は [`tools/acceptance_shards.py:928-952`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:928)、145 回という既測定は [`output/insights/2026-09-02_acceptance-collection-internals/README.md:45-50`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/output/insights/2026-09-02_acceptance-collection-internals/README.md:45)。
- collection は重要だが、模型残差 140 秒全体の主因とまではまだ言えない。既裁定 D1420 は旧 tip の同型測定で、worker 起動約 3.2 秒、collection 約 51.7 秒、終端約 2.9 秒を確定している。[`docs/decisions.md:45015-45034`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/docs/decisions.md:45015)。したがって現在の 140 秒は、同じ走ごとに「実 worker 裾」と「test report 外区間」へ分け直す必要がある。
- 各 worker を担当 file だけ collect させる案は採らない。現在は各 worker の全 universe digest を検査しており、担当外 file の collection 異常を検出できなくなる。各 host に別の全量 collector を置いても、全 worker の独立観測という検出力は戻らない。
- L1 は全 worker の全 collection を維持したまま、重複する item 正規化、2.5 MB の duration ledger の worker ごとの転送、同期 prewarm を短縮する。
- L2 の本命は t080 である。11 node が11 workerに散り、各 worker が base を構築することが実測済みである。[`output/insights/2026-09-04_t2298-t2273-shard0-critical-path/measurements.md:107-133`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/output/insights/2026-09-04_t2298-t2273-shard0-critical-path/measurements.md:107)。host 共有の二段 cacheを実装する価値がある。
- `_clone_committed_head_with_ccbench` は direct consumer が1 nodeだけなので、host cache は 0.0 秒しか短縮しない。ここには共有化を実装しない。
- L4 では、明確に同じ入力と assertion を持つ5 nodeを削除できる。うち snapshot 3 nodeは実装を共有 helperへ一本化し、残す側の3 testで検出力を維持することが前提である。
- L3 は現時点では採らない。11.6 秒は反実仮想模型値であり、L1/L2後には t080 の重みと均衡点が変わる。

## 残差 140 秒の切り分け設計

### 1. 既存75走だけで行う分解

追加実走より先に、各 session、各 shardについて次を同じ走から計算する。

```text
T = JUnit testsuite time
W = report.json worker_occupancy.duration_s の総和
O = worker_occupancy.duration_s の最大
M = 親と同じ方法で当該走から求めた max(C, W/48)

模型残差       R_model    = T - M
実 worker 裾   R_worker   = O - M
report外区間   R_outside  = T - O

R_model = R_worker + R_outside
```

`worker_occupancy` は report の生成時に TestReport duration を worker別に集計している。[`tools/acceptance_shards.py:973-1019`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:973)。過去の同じ再計算方法は [`output/insights/2026-09-02_t2097-residual-breakdown/measurements.md:9-24`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/output/insights/2026-09-02_t2097-residual-breakdown/measurements.md:9)。

再現 command は、既存 probe を現行 artifact rootへ向ける。

```bash
python3 <repo外probe>/_t2097_residual_probe.py recompute-archive \
  --root /work/1/SFC/tanab/.izanagi-acceptance-shards \
  --out <repo外出力>.json
```

元の command 契約は [`output/insights/2026-09-02_t2097-residual-breakdown/measurements.md:194-210`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/output/insights/2026-09-02_t2097-residual-breakdown/measurements.md:194)。

判定は次のとおり。

- `R_worker` が大きい場合、collection ではなく実 worker の不均衡、LPT の裾、t080 などの重量 unitが模型との差を作っている。
- `R_outside` が大きい場合だけ、worker起動、collection、prewarm、finalizationの計装へ進む。
- 中央値同士を引かず、必ず各走の差を作ってから中央値を取る。

### 2. 受入全走は計装付き1回だけ

`tools/acceptance_shards.py` に opt-in の timeline を追加する。ただし14 fieldの `report.json` には一切加えず、shard artifact内の別ファイルへ create-only で保存する。`_REPORT_FIELDS` は [`tools/acceptance_shards.py:61-66`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:61) のままとする。

計測点は以下に限定し、testごとの追加 hookは置かない。

- controller: session start、gateway生成完了、worker ready、各 worker collection受信、最初と最後の report、session finish。
- worker: collection開始・終了、`resource.getrusage()`、`/proc/self/io` 差分、hostname、PID、worker ID。
- 既存の `_REPORT_WORKERS` と `_REPORT_DURATIONS` を timeline終了時に投影し、追加の test report hookを増やさない。
- `time.monotonic_ns()` を使用し、全 workerのhostname不一致は解析拒否とする。

実行 commandは1回だけである。

```bash
IZANAGI_ACCEPTANCE_SHARDS=3 \
IZANAGI_ACCEPTANCE_TIMELINE_V1=full-v1 \
python3 tools/run_tests.py --force-dispatch
```

同じ走で次を分離する。

```text
critical bootstrap =
  最後に collection を終えた worker の collection start - session start

critical collection =
  同 worker の collection end - collection start

controller barrier/prewarm =
  最初の test report start - 最後の collection end

test frontier =
  最後の test report stop - 最初の test report start

finalization =
  pytest wall end - 最後の test report stop
```

collectionを模型残差の主因と呼べる条件は、同じ走の `critical collection` が `R_model` 内で最大の相互排他的成分で、かつ `R_model` の50%以上を占めることとする。満たさなければ「collectionは主因」ではなく「共通費用の一成分」と記録する。

### 3. 他候補の排除

- worker起動: `session start → critical worker collection start` で直接測る。過去値約3.2秒は [`docs/decisions.md:45028-45030`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/docs/decisions.md:45028)。現行値が残差の最大成分でなければ排除する。
- LPTの裾: `O-M`、最大 workerと2位の差、最大 workerの item数を既存 reportから出す。過去には最大 workerがt080の2 itemであった。[`output/insights/2026-09-04_t2298-t2273-shard0-critical-path/measurements.md:42-52`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/output/insights/2026-09-04_t2298-t2273-shard0-critical-path/measurements.md:42)。
- finalization: timelineの最後の report stopからsession wall終点までを測る。過去値は2.913秒である。[`output/insights/2026-09-02_t2097-residual-breakdown/measurements.md:98-118`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/output/insights/2026-09-02_t2097-residual-breakdown/measurements.md:98)。
- 共有filesystem競合: critical collectionの `wall - user CPU - system CPU`、read syscall数、major faultを確認する。off-CPU時間が大きい場合だけ、同じ計算node内で次の非受入 collect-only対を行う。

```bash
/usr/bin/time -v python3 tools/run_tests.py \
  -n 0 --collect-only -q -p no:cacheprovider

/usr/bin/time -v python3 tools/run_tests.py \
  -n 48 --collect-only -q -p no:cacheprovider
```

これは受入全走ではなく、testを実行しないcollection較正である。48 worker側だけ1 processあたりのcollection wallが増え、CPU時間では説明できず、repoのfilesystem種別がLustreなら共有filesystem競合を支持する。差が無ければLustre競合を主因候補から外す。

CPU hotspotは同じ計算nodeで次を使う。

```bash
python3 -m cProfile -o /tmp/izanagi-collect.pstats \
  tools/run_tests.py -n 0 --collect-only -q -p no:cacheprovider
```

なお、既測定で最重量だった `test_p3_exploration_namespace.py` の走査には、すでにNFKC字句prefilterが入っている。[`orchestrator/tests/test_p3_exploration_namespace.py:133-159`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_p3_exploration_namespace.py:133)、同値性testは [`orchestrator/tests/test_p3_exploration_namespace.py:526-586`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_p3_exploration_namespace.py:526)。これを未実装案として再提案しない。

## L1 案と閉包 gate 論証

### 現行gateの検出対象

- `assignment_closure_gate`: selectedの重複と欠落を拒否し、file、`xdist_group`、real-repo conflict edgeが単一shardへ閉じることをallocatorとは独立に再検査する。[`tools/acceptance_shards.py:445-474`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:445)。
- `observed_universe`: 全shardのdeselect前 `ItemRecord` 列が完全一致することを検査する。[`tools/acceptance_shards.py:487-492`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:487)、発火箇所は [`tools/acceptance_shards.py:651-663`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:651)。loginの独立collectionとのCounter一致も別gateである。
- `_finished_gate`: `pytest_runtest_logfinish` で観測したnode multisetとselected multisetを完全一致させ、未実行、重複実行、別node実行を拒否する。[`tools/acceptance_shards.py:499-500`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:499)、発火箇所は [`tools/acceptance_shards.py:672-677`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:672)。
- `validate_report_evidence`: 全workerのcollection digest、worker occupancyの型とitem総数、group集合とworker集合、JUnit path、terminal countの閉包をproducerと独立に再計算する。[`tools/acceptance_shards.py:518-600`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:518)。

### L1-A: `_canonical_item` の二重評価除去

変更点:

- [`tools/acceptance_shards.py:771-775`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:771) で各 itemから `ItemRecord` と `id(item) → nodeid` を一度に作る内部helperを設ける。
- [`tools/acceptance_shards.py:832-843`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:832) の二度目の `_canonical_item()` を、その保存済み対応表で置換する。
- `_canonical_item` の呼出し回数が `len(items)` ちょうどであり、旧実装とrecords、selected、loadsが完全一致するtestを `test_run_tests_shards.py` に追加する。

gate論証:

- 新しい値やauthorityを作らず、同じ `_canonical_item` の初回結果を再利用するだけである。
- `records`、allocation、selected、deselect、reportの全bytesが同じなので、四gateの入力も検出力も変わらない。

### L1-B: duration ledger workerinputの圧縮

変更点:

- [`orchestrator/tests/conftest.py:1442-1449`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/conftest.py:1442) でmappingを一度だけcanonical JSON化し、zlib圧縮する。
- payloadは `schema_version`、`codec`、非圧縮長、SHA-256、圧縮bytesの閉じた集合にする。
- [`orchestrator/tests/conftest.py:1452-1477`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/conftest.py:1452) で16 MiB上限、EOF、trailing data無し、digest一致、duplicate JSON key無しを確認してから現行の型・有限値検査へ渡す。
- [`orchestrator/tests/conftest.py:2132-2141`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/conftest.py:2132) は全workerへ同じimmutable bytesを渡し、workerごとの `dict(durations)` を除く。
- 展開mappingと現行mapping、最終reorder結果のidentity列が完全一致するtestを追加する。

gate論証:

- 全workerは従来どおり全testをcollectする。
- duration ledgerはcollection集合やshard allocationではなく、shard内の送出順だけに使われる。[`orchestrator/tests/conftest.py:1571-1620`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/conftest.py:1571)。
- 展開後mappingと順序の完全一致を要求するため、assignment、observed universe、finished、report evidenceのいずれも弱まらない。
- 破損payloadは空ledgerへfallbackせず `pytest.UsageError` で停止する。

### L1-C: controller prewarmの重畳

これはtimelineで重畳可能区間が3秒以上ある場合だけ実装する。

- [`orchestrator/tests/conftest.py:2179-2212`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/conftest.py:2179) で最初の該当collection通知からcontroller-owned threadを1本だけ起動する。
- 全workerのcollection通知が揃った時点でjoinし、成功確認後に最後のhookを返す。例外は保存し、schedulerがtestを配る前に同じ例外を再送出する。
- exactly-once、worker payer無し、最後のcollection barrier前完了、例外伝播、途中終了時joinを固定する。

gate論証:

- collection、allocation、report生成は変更しない。
- prewarm完了をscheduler開始より前に維持するため、testが未完成memoを読む経路を作らない。
- failureを握り潰さないので受理集合を広げない。
- 既存のcontroller-only、lazy、例外伝播testは [`orchestrator/tests/test_real_repo_serialization.py:4437-4547`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_real_repo_serialization.py:4437)。

### 採らないL1案

workerを担当fileだけに絞る案は採らない。

現行の各workerは全records digestを返し、全digestがfull universe digestと一致しなければ拒否される。[`tools/acceptance_shards.py:913-952`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:913)、[`tools/acceptance_shards.py:533-540`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:533)。selected-onlyにすると、担当外fileのworker固有collection欠落を検出できない。

さらに次の既裁定と直接衝突する。

- D634: controller-onlyとmanifest共有を不採用。[`docs/decisions.md:25364-25415`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/docs/decisions.md:25364)。
- D711: suite root全量collection、決定的再導出、manifest無しを要求。[`docs/decisions.md:27929-27970`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/docs/decisions.md:27929)。

この案を採るには両裁定の明示的supersedeと、xdistのworker-local `Item` 構築を置換する独立設計が必要である。本waveでは採らない。

## L2 案と安全境界の証明方針

### t080 host共有cache

現行は [`orchestrator/tests/test_s8b_oracle_driver.py:893-930`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_s8b_oracle_driver.py:893) のprocess-local cacheである。48 workerに11 nodeが分散するため、受入では11 workerがそれぞれbaseを構築することが実測済みである。

実装は二段に分ける。

1. `_build_t080_stub_free_e2e_repo` を、pre-receipt basis生成とreceipt発行へ分割する。

   - basis生成: [`test_s8b_oracle_driver.py:1012-1104`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_s8b_oracle_driver.py:1012)。
   - receipt発行: [`test_s8b_oracle_driver.py:1105-1273`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_s8b_oracle_driver.py:1105)。
   - basis keyは `distinct_basis_blob`、final keyは現行と同じ `(r_trailer, extra_r_path, issue_receipt, distinct_basis_blob)` とする。

2. 新規 `orchestrator/tests/host_tree_cache.py` にtest専用cacheを置く。

   - xdist時は `tmp_path` の祖先にある `popen-${PYTEST_XDIST_WORKER}` の親を共通rootとする。該当祖先が無ければfail-closed。
   - serial時は現在のprocess-local cacheを維持する。
   - keyごとの `fcntl.flock`、同じfilesystem内のstaging directory、`os.rename` によるatomic publishを使う。
   - cache pathはtestへ返さない。testへ返すのは毎回 `shutil.copytree(..., symlinks=True)` した独立treeだけとする。
   - hardlink、共有working tree、共有document objectは禁止する。
   - documentは現行どおり `copy.deepcopy` する。
   - cache rootはpytestのsession temp tree配下なので、別pytest sessionや別worktreeと共有しない。

現行11 nodeのkey内訳は、default 7 node、`distinct_basis_blob=True` 1 node、bad trailer 1 node、extra path 1 node、`issue_receipt=False` 1 nodeである。host共有後はfinal baseが5個、basisは `distinct_basis_blob` の2個まで減る。nodeid、入力変異、assertionは変更しない。

### 変異で殺せるpositive control

T-1933が欠いていた安全境界は、次をすべて証明すれば足りる。

- 同時に7 processがdefault keyを要求してもbasis builder呼出しが1回、final builder呼出しが1回である。
- 返却rootは7個すべて異なり、代表regular fileのinodeも異なる。
- copy Aでregular file追記、receipt削除、Git commit追加、submodule HEAD変更を行っても、copy Bとcache baseのbytes、Git HEAD、submodule HEADが変わらない。
- copy Aへ返したdocumentのnested fieldを書き換えてもcopy Bのdocumentが変わらない。
- bad trailer、extra path、issue false、distinct basisを同じkeyへ畳む変異が拒否される。
- builder途中でprocessをkillした後、次processはpartial treeを読まず再構築できる。
- publish済みbase pathを返す変異、hardlink copyへ変える変異、`deepcopy` を外す変異、lockを外す変異、keyから各fieldを1個ずつ落とす変異が、それぞれ専用testを赤にする。
- positive controlの期待値はcache manifest自身から導出せず、literal sentinel bytes、`git rev-parse`、`git status --porcelain`、pathとinodeの独立観測から作る。

同一uidの悪意あるtestが予測可能なcache pathを直接探して改変することまでは隔離できない。この限界は明記し、process隔離や権限制御を主張しない。

### floor clone

[`orchestrator/tests/test_s8b_floor_campaign.py:1934-1972`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_s8b_floor_campaign.py:1934) のdirect consumerは [`orchestrator/tests/test_s8b_floor_campaign.py:11116-11119`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_s8b_floor_campaign.py:11116) の1 nodeだけである。host共有によるhitは0件なので、共有cache化は採らない。内部の2 clone並列化も、同一host対測定とatomic stagingの安全証拠が無いため今回の計画には入れない。

## L3 の採否

現時点では採らない。

- D1020の再検討条件成立は認める。
- ただし親briefの反実仮想利得は中央値11.6秒で、D1019が観測した同一tipの走間差32.27秒より小さい。[親brief:33-36](/home/SFC/tanab/.claude/jobs/98cb6669/tmp/s1-brief.md:33)、[D1019:24-29](/home/SFC/tanab/.claude/jobs/98cb6669/tmp/rulings-d1019-d1020.md:24)。
- t080共有化後は重量nodeのdurationとshard負荷が変わるため、現在のcounterfactualを使い回せない。
- L1/L2後の完全JUnitから走ごとに `C`、`W`、実worker occupancyを再計算する。過去ledgerを将来走の `W` に使わない。
- それでもduration割付の予測中央値が残り、同一branch・同一host blockのcount対duration A/Bで短縮が確認できる場合だけ、段4へ再裁定を返す。D531は配布順変更の採否を同一branch A/Bに限定している。[`rulings-d531-d532.md:3-6`](/home/SFC/tanab/.claude/jobs/98cb6669/tmp/rulings-d531-d532.md:3)。
- 採る場合は `_components()` の `weight` [`tools/acceptance_shards.py:321-357`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:321) と `allocate()` [`tools/acceptance_shards.py:377-442`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:377) だけを先に変えてはならない。ledger provenance、未知node処理、実際に発火したallocation modeの証拠まで同じ変更単位にする。

## L4 の冗長テスト一覧

次の5 nodeは削除可能である。

1. 同一helper、同一入力、同一assertion。

   - 削除: `orchestrator/tests/test_autonomous_trial_completeness.py::test_pre_raw_failure_allows_missing_raw_response_pointer`
   - 残す: `orchestrator/tests/test_autonomous_trial_completeness.py::test_p3_role_invalid_partial_passes`
   - 両方とも `_role_invalid_trial(tmp_path)` の結果を `_verify(run, report)` へ渡すだけで、bodyが同一。[`test_autonomous_trial_completeness.py:2019-2021`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_autonomous_trial_completeness.py:2019)、[`test_autonomous_trial_completeness.py:2274-2276`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_autonomous_trial_completeness.py:2274)。

2. 同一文字列、同一decision、同一scorer、同一assertion。

   - 削除: `orchestrator/tests/test_codex_reasoning_ab.py::test_f176_preserves_decision_mentions[go_condition]`
   - 残す: `orchestrator/tests/test_codex_reasoning_ab.py::test_f176_preserves_legitimate_opposite_mentions[go_condition_not_met]`
   - 入力は双方とも `("NO-GO。GOの条件を満たさない。", "NO-GO")`。[`test_codex_reasoning_ab.py:13236-13254`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_codex_reasoning_ab.py:13236)、[`test_codex_reasoning_ab.py:13257-13317`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_codex_reasoning_ab.py:13257)。distinct input集合は縮まらない。

3. snapshot helperを `output_snapshot_ignores.py` へ一本化したうえで、oracle側の次の3 nodeを削除し、real-repo側を残す。

   - `orchestrator/tests/test_s8b_oracle_driver.py::test_t080_output_snapshot_detects_git_visible_real_output_changes`
   - `orchestrator/tests/test_s8b_oracle_driver.py::test_t080_output_snapshot_excludes_git_ignored_real_output_changes`
   - `orchestrator/tests/test_s8b_oracle_driver.py::test_t080_output_snapshot_observes_git_visible_create_and_delete`

   oracle側は [`test_s8b_oracle_driver.py:598-653`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_s8b_oracle_driver.py:598)、残す側は [`test_real_repo_serialization.py:752-815`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_real_repo_serialization.py:752)。入力tree、書くrelative pathとbytes、assertionは同じであり、real-repo側にcleanupが追加されているだけである。

   `_t080_output_snapshot` 自体も両fileで同一実装である。[`test_s8b_oracle_driver.py:565-595`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_s8b_oracle_driver.py:565)、[`test_real_repo_serialization.py:719-749`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_real_repo_serialization.py:719)。共通helperへ寄せず片方のtestだけ消す案は、独立実装の片側を未検査にするため採らない。

これ以外のAST body重複候補は、別module、別authority、別parameter集合、別production関数を検査しており削除しない。

## pin 閉包

### L1 runner、report、gate

- `SCHEMA` と14 field exact: [`tools/acceptance_shards.py:49-66`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:49)。
- synthetic report全field: [`orchestrator/tests/test_run_tests_shards.py:79-110`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_run_tests_shards.py:79)。
- observed、closure、finished、login、report evidenceのmutation controls: [`test_run_tests_shards.py:774-937`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_run_tests_shards.py:774)。
- hook属性pin: [`test_run_tests_shards.py:48-59`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_run_tests_shards.py:48)。
- default suite root pin: [`test_run_tests_shards.py:301-356`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_run_tests_shards.py:301)。
- manifestとbarrierの禁止pin: [`test_run_tests_shards.py:1385-1393`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_run_tests_shards.py:1385)。
- 全dispatch開始とlogin collectionの順序pin: [`test_run_tests_shards.py:1403-1423`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_run_tests_shards.py:1403)。
- real-repo shard stateはfull recordsを要求: [`orchestrator/tests/conftest.py:1917-1946`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/conftest.py:1917)。
- 実collectionからclosureを再検査するpin: [`test_real_repo_serialization.py:1650-1732`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_real_repo_serialization.py:1650)。
- group名exactとconflict edge exact: [`test_real_repo_serialization.py:249-257`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_real_repo_serialization.py:249)、[`test_real_repo_serialization.py:319-328`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_real_repo_serialization.py:319)。
- 追跡下consumerの14 field、worker digest 48本、selected partition: [`output/insights/2026-08-24_t1618-xdist-controller-cost/prepare_inputs.py:501-558`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/output/insights/2026-08-24_t1618-xdist-controller-cost/prepare_inputs.py:501)。

brief外で追加確認したpinは、manifest禁止test、default suite root test、`_validate_real_repo_shard_state`、実collection closure test、D634、D711である。

### L1 duration ledger

- file path、16 MiB上限、workerinput key `izanagi_acceptance_duration_ledger_v1`: [`orchestrator/tests/conftest.py:893-909`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/conftest.py:893)。
- controller payload exact: [`test_acceptance_schedule_order.py:1084-1123`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_acceptance_schedule_order.py:1084)。
- payload欠落、型破損、workerのfile再読禁止: [`test_acceptance_schedule_order.py:1128-1164`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_acceptance_schedule_order.py:1128)。
- ledger schemaと有限値: [`test_update_acceptance_duration_ledger.py:306-326`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_update_acceptance_duration_ledger.py:306)。
- collection coverage 90% gate: [`test_acceptance_schedule_order.py:660-717`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_acceptance_schedule_order.py:660)。

### L2 t080

- helper direct consumer 6 function、11 node exact: [`test_s8b_oracle_driver.py:933-1009`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_s8b_oracle_driver.py:933)。
- 11 canonical nodeid、skip/xfail/deselect無し、setup到達: [`test_real_repo_serialization.py:1112-1154`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_real_repo_serialization.py:1112)。
- ledgerのt080 node keys: [`acceptance_duration_ledger.json:14280`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/acceptance_duration_ledger.json:14280)、[`acceptance_duration_ledger.json:14325-14344`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/acceptance_duration_ledger.json:14325)。
- source、metadata、receiptのgoldenは [`test_s8b_oracle_driver.py:149-278`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_s8b_oracle_driver.py:149)。cache refactorで値を更新してはならない。
- floor nodeはreal-repo inventoryと独立goldenの双方にpinされる。[`orchestrator/tests/conftest.py:376-377`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/conftest.py:376)、[`test_real_repo_serialization.py:149-150`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_real_repo_serialization.py:149)。

brief外で追加確認したpinは、11 nodeのdefault実行をsubprocessで検査する `test_stub_free_receipt_nodes_are_selected_and_reach_setup_by_default` と、floor nodeの二重inventoryである。

### L4

削除対象のledger keys:

- autonomous 2 node: [`acceptance_duration_ledger.json:2568-2579`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/acceptance_duration_ledger.json:2568)。
- F176 2 node: [`acceptance_duration_ledger.json:5767-5768`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/acceptance_duration_ledger.json:5767)。
- snapshot 3 node: [`acceptance_duration_ledger.json:14333-14335`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/acceptance_duration_ledger.json:14333)。

削除する5 keyと `nodeid_count` を同じ変更で更新する。新しい安全境界testのdurationを合成してledgerへ加えてはならない。

`test_real_repo_serialization.py` はadd-only frozen suiteである。[`tools/update_acceptance_duration_ledger.py:21-38`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/update_acceptance_duration_ledger.py:21)、suite node set pinは [`test_update_acceptance_duration_ledger.py:360-387`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_update_acceptance_duration_ledger.py:360)。したがってsnapshot testはreal-repo側を残し、oracle側を削る。

共通snapshot helperはD1063からD1065の意味論を保存する。特にignored prefix祖先だけmetadataを正規化し、それ以外の一時作成後削除を検出する条件は [`docs/decisions.md:36625-36649`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/docs/decisions.md:36625)。

## 段 5 の実装分割

### 単位A: L1 collectionとbootstrap

所有file:

- `tools/acceptance_shards.py`
- `orchestrator/tests/test_run_tests_shards.py`
- `orchestrator/tests/conftest.py`
- `orchestrator/tests/test_acceptance_schedule_order.py`

内容:

- opt-in timeline。
- `_canonical_item` の一回化。
- duration ledger workerinput圧縮。
- report schemaと全量collectionは不変。

### 単位B: L2 t080とL4

所有file:

- `orchestrator/tests/host_tree_cache.py` 新規
- `orchestrator/tests/test_host_tree_cache.py` 新規
- `orchestrator/tests/test_s8b_oracle_driver.py`
- `orchestrator/tests/output_snapshot_ignores.py`
- `orchestrator/tests/test_real_repo_serialization.py`
- `orchestrator/tests/test_autonomous_trial_completeness.py`
- `orchestrator/tests/test_codex_reasoning_ab.py`
- `orchestrator/tests/acceptance_duration_ledger.json`

内容:

- t080の二段host cacheと隔離positive controls。
- snapshot helper一本化とoracle側3 node削除。
- autonomous 1 node、F176 1 node削除。
- ledgerから削除対象5 keyを除去。

単位AとBの所有fileは重ならないため並列実装できる。

### 単位C: 条件付きprewarm重畳

所有file:

- `orchestrator/tests/conftest.py`
- `orchestrator/tests/test_real_repo_serialization.py`

単位A、Bの双方と所有fileが重なる。timelineで重畳可能区間が3秒以上と確認された場合だけ、AとBの統合後に直列実装する。

L3を後日実装する場合は `tools/acceptance_shards.py`、`conftest.py`、ledgerと重なるため、AからCと並列にしてはならない。

各単位のfocused確認は必ずrunner経由で行う。

```bash
python3 tools/run_tests.py orchestrator/tests/test_run_tests_shards.py
python3 tools/run_tests.py orchestrator/tests/test_acceptance_schedule_order.py
python3 tools/run_tests.py orchestrator/tests/test_host_tree_cache.py
python3 tools/run_tests.py orchestrator/tests/test_s8b_oracle_driver.py \
  -k 't080_stub_free or never_issued_generator'
python3 tools/run_tests.py orchestrator/tests/test_real_repo_serialization.py
python3 tools/run_tests.py orchestrator/tests/test_autonomous_trial_completeness.py
python3 tools/run_tests.py orchestrator/tests/test_codex_reasoning_ab.py -k f176
```

D1184により、`tools/acceptance_shards.py` 自身を変更する単位Aは、その変更後gateだけで自己認証できない。この限界を記録し、既存mutation controls、独立review、変更bytes着地後の受入を別証拠とする。

## 予測効果と根拠

| 案 | pytest wall予測 | 根拠 |
|---|---:|---|
| L1-A `_canonical_item` 一回化 | 予測不能 | 旧測定ではcollection hook全体0.375秒、関連重複を含む上限0.2から0.6秒だったが、現行21,005 nodeの対測定ではない。[`acceptance-collection-internals/README.md:51-62`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/output/insights/2026-09-02_acceptance-collection-internals/README.md:51) |
| L1-B ledger圧縮 | 予測不能 | 旧現物では2,513,728 bytesを48回、約118 MB/shardから約19 MB/shardへ縮められるが、wall効果は未測定。[`acceptance-collection-internals/README.md:174-176`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/output/insights/2026-09-02_acceptance-collection-internals/README.md:174) |
| L1-C prewarm重畳 | 条件付き4.17から4.97秒、現行予測は不能 | 過去の同一node計装で最初から最後のcollection通知幅が4.17、4.97、4.86、4.31秒。[`t2097 measurements.md:128-158`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/output/insights/2026-09-02_t2097-residual-breakdown/measurements.md:128)。prewarmがこの幅より長い場合の上限である |
| selected-file collection | 不採用 | 理論上の短縮値を出さない。workerごとのfull-universe検出力を失う |
| L2 t080 host cache | 予測不能 | isolated base構築60から77秒、受入並列時は各node132から155秒だが、5 key並行時の競合量は未測定。[`shard0 measurements.md:107-133`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/output/insights/2026-09-04_t2298-t2273-shard0-critical-path/measurements.md:107)。削除できる重複basis構築は11回から2回、final構築は11回から5回 |
| floor host cache | 0.0秒 | direct consumerが1 nodeだけなのでcache hitが存在しない |
| L4 autonomous重複削除 | 予測不能 | ledger hintは削除側0.99秒、残す側0.72秒。[`acceptance_duration_ledger.json:2568-2579`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/acceptance_duration_ledger.json:2568)。ledgerはwall予測authorityではない |
| L4 F176重複削除 | 予測不能 | ledger hintは削除側0.001秒。[`acceptance_duration_ledger.json:5767-5768`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/acceptance_duration_ledger.json:5767) |
| L4 snapshot 3 node削除 | 予測不能 | ledger hintの直列work合計は21 + 50 + 23 = 94秒。[`acceptance_duration_ledger.json:14333-14335`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/acceptance_duration_ledger.json:14333)。並列wallへの寄与は未測定 |
| L3 duration割付 | 模型中央値11.6秒、実測短縮は不明 | 親brief 33から36行。L1/L2後は再計算必須 |
| 全体 | 予測不能 | t080のhost共有後のcontentionとfrontier変化が未測定であり、各候補の秒を足せない |

現行の単一collection 36.83秒は親brief 23行、wall中央値324.3秒と模型184.6秒は18行および37行が出所である。ただし36.83秒を145倍した値や、そのままwall短縮値へ読み替えてはならない。

## 未解決・要親裁定

- selected-file collection案を再開するにはD634とD711の明示的supersedeが必要である。推奨は「再開しない」。
- L1-C prewarm重畳は、現行timelineで重畳可能区間が3秒未満なら実装しない。
- t080 host cacheは安全境界のmutation controlsを全件killできなければ採らない。特にhardlink、共有Git metadata、document共有のいずれかが生存したら不採用とする。
- floor clone共有は効果0.0秒なので実装しない。内部clone並列化を別案として追うには、単独nodeの同一host A/Bが先に必要である。
- L3はL1/L2後の均衡点を見て再裁定する。現時点では不採用。
- 最終的な中央値短縮は予測不能である。実装後の採否は、同一branch、同じK=3、48 worker、growth hold状態とcollection digestを揃えたbefore/post blockで測る。計装1回による原因分解と、最終性能A/Bは別目的として混同しない。