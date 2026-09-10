## 現在地の確認

単独段 `stage=plan; sandbox=read-only` として、射影された6資料をすべて読み、指定されたコードを静的に追跡した。書き込み、pytest、受入全走は実行していない。

本プランの `full wall` は、親の解析と同じく各 full 走の

\[
W_r=\max_s(\text{shard }s\text{ の junit testsuite@time})
\]

とする。launcher 起動、PBS queue 待ち、artifact 回収まで含む waiter の端から端の wall ではない。後者を成果物にするなら、現状の dispatcher artifact では queue 待ちが支配し得るため別の定義が必要である。

## 同定の定義

「wall を決めている単体処理」は pytest nodeid ではなく、次を満たすコード単位の処理と定義する。

- fixture setup、test call、teardown、process-local cache の first miss など、開始と終了をコードへ帰属できる。
- 同一 tip、同一 K、同一 worker 数、同一 collection universe で、その処理だけを x 秒短縮する介入を考えたとき、full wall の中央値が概ね x 秒短くなる。
- 事前判定式は後述するが、「概ね x」は `0.9 <= ΔW / ΔU <= 1.1` とする。
- D357 に従い、`ΔW / median(W_before) < 0.10` は変化なしとする。

fixture 所要は最初の consumer node の setup に課金されるため、「最長 node」をそのまま単体処理と呼ばない。例えば `test_candidate_freeze_matches...` の 119 秒には、test body だけでなく module fixture の fresh-index commit 生成が含まれ得る。

並列 plateau により単一処理が存在しない場合は、次を同定結果とする。

- 「D357 の解像度で単一処理なし」という負結果。
- 先頭を短縮すると次に wall を取る処理を並べた critical frontier。
- frontier を、コード routine、fixture、loadgroup、worker、shard の各粒度で示す。
- 70〜77 秒が単一 routine に帰属しなければ、「startup/collection/scheduling の合成区間」であり、単体処理とは認定しない。

各走で critical worker の終了時刻と次点 worker の終了時刻の差、critical shard と次点 shard の wall 差を取り、その小さい方を単体短縮の slack とする。slack が full wall の10%未満なら、単一処理を10%以上短縮しても別 worker または shard が wall を引き継ぐので、D357 解像度の単一支配処理ではない。

## 段取り (file:line 粒度)

1. 走の同値性を先に固定する。

   - report の closed schema は [tools/acceptance_shards.py:50-66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/acceptance_shards.py:50)。
   - 各 worker の全 collection digest は [tools/acceptance_shards.py:533-540](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/acceptance_shards.py:533)。
   - shard 間 universe と login collect の一致は [tools/acceptance_shards.py:655-670](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/acceptance_shards.py:655)。
   - 走間については gate がないため、tested tip、K、worker 数、全 shard の collection digest tuple が同一の走だけを比較する。異なる corpus は混ぜない。

2. launcher と pytest session を分離する。

   - launcher は tested-main の runner blob を読み、別 Python で実行する [tools/acceptance_launcher.py:555-635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/acceptance_launcher.py:555)。これは JUnit session wall の外側。
   - shard child は `python -m pytest`、JUnit、shard plugin、`no:cacheprovider` を組み立てる [tools/run_tests.py:1460-1533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/run_tests.py:1460)。
   - `-n` と `--dist loadgroup` は [tools/run_tests.py:550-572](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/run_tests.py:550)。worker 数は [tools/run_tests.py:385-399](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/run_tests.py:385) で環境と割当から解決される。48 は固定 literal ではないが、既存 dispatcher stdout の `created: 48/48 workers` で実測できる。

3. session 開始から最初の call までを次の区間に分ける。

| 区間 | 実行コード | 現 artifact で分かること | 必要な追加観測 |
|---|---|---|---|
| Controller session start と48 worker 起動 | pytest command は [tools/run_tests.py:1495-1508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/run_tests.py:1495)。実 spawn は xdist 側 | stdout から worker 数のみ。所要なし | `pytest_sessionstart`、各 `pytest_testnodeready` の controller 時刻 |
| conftest/plugin import と configure | conftest の import は [orchestrator/tests/conftest.py:30-145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/conftest.py:30)、configure は [orchestrator/tests/conftest.py:2502-2512](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/conftest.py:2502)。shard plugin configure は [tools/acceptance_shards.py:806-822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/acceptance_shards.py:806) | なし | worker process 内の configure 完了時刻 |
| `workerinput` 配布 | memo nonce と duration ledger を配る [orchestrator/tests/conftest.py:2115-2145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/conftest.py:2115) | payload の内容も配布所要も report にない | `pytest_configure_node` の開始、終了、worker id |
| 全 test module の import/collection | 各 worker が全 items を持った後、conftest が全 item を走査する [orchestrator/tests/conftest.py:1983-2053](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/conftest.py:1983) | `observed_universe` と48個の同一 digest は、各 worker が全 universe を見たことを証明する | worker の collection 開始、`pytest_collection_modifyitems` 入口、module collector ごとの開始、終了 |
| shard 割付けと deselect | 全 items から records、allocate、retained/deselected を作る [tools/acceptance_shards.py:825-852](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/acceptance_shards.py:825) | observed、selected、finished の集合のみ | hook 入口、allocate 完了、deselect 完了の時刻 |
| hold、suffix、duration reorder | hold marker は [orchestrator/tests/conftest.py:1991-2036](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/conftest.py:1991)、deselect 後の suffix strip/reorder は [orchestrator/tests/conftest.py:2053-2065](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/conftest.py:2053) | 結果の item 順は report にない | wrapper の yield 前後を計時 |
| collection barrier の prewarm | receipt memo は [orchestrator/tests/conftest.py:2174-2189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/conftest.py:2174)、oracle environment は [orchestrator/tests/conftest.py:2191-2207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/conftest.py:2191) | なし | 各 prewarm の開始、終了、cache hit/miss |
| scheduler barrier から最初の setup/call | xdist collection 完了 hook は [orchestrator/tests/conftest.py:2148-2215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/conftest.py:2148) | なし | 全48 worker collection 完了、最初の setup start、最初の call start |
| fixture setup と test call | real-repo lock は test protocol 全体を包む [orchestrator/tests/conftest.py:2068-2085](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/conftest.py:2068) | JUnit testcase time は setup/call/teardown の合計。phase 境界なし | TestReport の setup/call/teardown start/stop |

重要なのは、real-repo lock の取得が `yield` より外側の [orchestrator/tests/conftest.py:2083-2085](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/conftest.py:2083) にある点である。lock 待ちが TestReport phase の外なら `worker_occupancy` に入らず、`wall - max_occ` へ混入する。

また module fixture setup は「最初の test call より前」ではあるが、他 worker がすでに test を実行中の場合がある。したがって 70〜77 秒を「全 worker が1本も test を走らせていない連続時間」とは呼べない。

4. 現 artifact と追加観測から以下を別々に計算する。

   - prefix: session start から全 worker 中最初の setup start。
   - no-call prefix: session start から最初の call start。fixture setup を含む。
   - zero-active interval: 全 worker の setup/call/teardown interval の和集合の補集合。
   - critical-worker idle: critical worker の phase interval 間の空白。
   - suffix: 最後の teardown stop から session finish。
   - collection/import、deselect、prewarm、initial scheduling は上記 milestone の差分。

`worker_occupancy` は TestReport duration を node ごとに加算する [tools/acceptance_shards.py:862-872](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/acceptance_shards.py:862) だけである。従って `wall - max_occ` は上記すべての混合値であり、「テストを1本も走らせていない時間」の下限でもない。

## 観測の穴とその塞ぎ方 (費用と波及範囲)

最小変更は report を v2 にし、1フィールド `node_execution` を追加することである。

```json
"node_execution": {
  "<normalized nodeid>": {
    "worker": "gw46",
    "setup": [start_epoch_s, stop_epoch_s],
    "call": [start_epoch_s, stop_epoch_s],
    "teardown": [start_epoch_s, stop_epoch_s]
  }
}
```

skip/error で存在しない phase は `null` とする。これだけで nodeid → worker、node 全体の開始、終了、fixture setup と call の境界を残せる。

変更位置は次のとおり。

- schema を v2 へ上げ、field を追加する: [tools/acceptance_shards.py:50-66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/acceptance_shards.py:50)。
- process-local state を追加、初期化する: [tools/acceptance_shards.py:798-822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/acceptance_shards.py:798)。
- 既存 `_REPORT_WORKERS` と TestReport の `when/start/stop` を phase entry へ畳む: [tools/acceptance_shards.py:862-874](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/acceptance_shards.py:862)。
- loadgroup suffix を正規化して report へ出す: [tools/acceptance_shards.py:965-1023](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/acceptance_shards.py:965)。
- 検証を追加する: [tools/acceptance_shards.py:518-600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/acceptance_shards.py:518)。

検証条件は次に限定する。

- key 集合が `selected` と完全一致。
- worker が `worker_occupancy` の key に存在する。
- phase は closed key、有限数、`start <= stop`、setup → call → teardown の順。
- node を worker 別に数え直した件数が `worker_occupancy[*].items` と一致。
- loadgroup node の worker が `group_to_workers` と一致。
- 同じ node の phase 間で worker が変わった場合は report-invalid。

費用は TestReport 1件あたり定数時間、保存量は selected item 数と最大3 phase に比例する。現状の約6,300 selected/shard なら phase record は最大約18,900/shard。test body や受理集合には触れないが、report の書き出し量と final validation は増える。

70〜77秒の分解まで恒久 artifact に残す場合は、同じ v2 に `session_milestones` を追加し、以下も計時する。

- controller `sessionstart`、`testnodeready`、`xdist_node_collection_finished`。
- worker collection と shard deselect。
- conftest prewarm。
- controller `sessionfinish`。

worker 側 collection milestone は現在の `_worker_payload` と `_controller_state` [tools/acceptance_shards.py:913-952](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/acceptance_shards.py:913) に載せる必要がある。prewarm 内訳まで分けるなら [orchestrator/tests/conftest.py:769-870](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/conftest.py:769) に計時を置く。

波及する test は主に次である。

- report fixture: [test_run_tests_shards.py:79-110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_run_tests_shards.py:79)。
- selected を変更する補助: [test_run_tests_shards.py:131-152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_run_tests_shards.py:131)。
- report evidence の positive/negative controls: [test_run_tests_shards.py:892-937](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_run_tests_shards.py:892)。
- artifact 書き出し fixture: [test_run_tests_shards.py:1246-1262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_run_tests_shards.py:1246)。
- workerinput/prewarm milestone も変更する場合: [test_real_repo_serialization.py:3100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_real_repo_serialization.py:3100)、[同:3193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_real_repo_serialization.py:3193)、[同:4294](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_real_repo_serialization.py:4294)、[同:4401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_real_repo_serialization.py:4401)、[同:4707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_real_repo_serialization.py:4707)。

受入 receipt への波及は、report-only 変更ならない。receipt は report を埋め込まず、scheduler と log hash だけを持つ [tools/acceptance_launcher.py:495-527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/acceptance_launcher.py:495)。land 側の exact fields も [tools/dev_wave_land.py:94-130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/dev_wave_land.py:94) のままでよい。

report digest や telemetry を receipt に証明対象として追加するのは最小変更ではない。その場合は launcher completion [tools/acceptance_launcher.py:402-429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/acceptance_launcher.py:402)、waiter completion [tools/dev_wave_wait.py:3124-3136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/dev_wave_wait.py:3124)、land receipt fields、`test_acceptance_launcher.py`、`test_dev_wave_wait.py`、`test_dev_wave_land.py` 全体へ schema bump が波及するため避ける。

既存の凍結 report は v1 のまま保存し、変更しない。事後解析 reader だけが v1/v2 の双方を扱う。

## 100〜200 秒 node の中身

### `s8c-preregistration-candidate`

loadgroup marker は [test_s8c_preregistration_invariant.py:30-31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_s8c_preregistration_invariant.py:30)。

共有 module fixture は [同:362-385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_s8c_preregistration_invariant.py:362) で、主要処理は次である。

- fresh index を作る。
- `read-tree HEAD`。
- pathspec なしの `git add -A --`。
- `write-tree`。
- `commit-tree -p HEAD`。

実装は [同:191-215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_s8c_preregistration_invariant.py:191)、問題の全 checkout 対象 `git add -A` は line 205。

その後、同じ worker 上の5 node が以下を行う。

- freeze/history validation: [同:388-425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_s8c_preregistration_invariant.py:388)。
- `_batch_oids` を含む再 validation: [同:428-445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_s8c_preregistration_invariant.py:428)。
- activation report と generation/decider binding: [同:448-479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_s8c_preregistration_invariant.py:448)。
- predicate report assertion: [同:602-616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_s8c_preregistration_invariant.py:602)。
- 全 repository file enumeration と holdout scan: [同:619-642](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_s8c_preregistration_invariant.py:619)。

既存 `c575a368.../shard-0/junit.xml` では5 node が 119.372 / 1.182 / 16.764 / 0.001 / 10.834 秒で、group 合計は約148秒だった。ただし119.372秒を fresh-index、validation、fixture lock に分解する情報はない。

`growth_test_holds.py` の主張は [growth_test_holds.py:84-90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/growth_test_holds.py:84)、5 node への対応は [同:205-247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/growth_test_holds.py:205)。コード上の対応先は確かに `_candidate_commit` の line 205 だが、次は未証明である。

- tracked file 数に対する増加率。
- 119秒中 `git add -A` が占める秒数。
- 現 tip、48 worker 競合下の単独所要。

`_hold` は `measured_seconds=None` を設定する [growth_test_holds.py:47-61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/growth_test_holds.py:47)。従って hold 理由文は測定 record ではない。phase timing と subprocess 単位の追加観測が必要である。

また現在の5 node は hold registry にあり、opt-in なしでは conftest が skip marker を付ける [orchestrator/tests/conftest.py:2020-2030](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/conftest.py:2020)。historical artifact の loadgroup criticalityを、そのまま現行 default tip の処理と扱えない。

### ungrouped C06 predicate node

`test_repository_candidate_uses_real_s8c_budget_module` は別機構である。

- function fixture が fresh index を作るが、`git add` は4 path に限定される [test_s8c_preregistration_predicates.py:3916-3962](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_s8c_preregistration_predicates.py:3916)。
- test body は C06 evaluator を呼ぶ [同:3965-3985](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_s8c_preregistration_predicates.py:3965)。
- evaluator は budget module、ratified loader、supervisor を読み、call graph を探索する [s8c_preregistration_evidence.py:3504-3579](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/campaign/s8c_preregistration_evidence.py:3504)。
- module 解決は `.py` と `__init__.py` を probe する [同:850-858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/campaign/s8c_preregistration_evidence.py:850)。
- 各 committed blob の存在確認と読取は Git subprocess を使う [同:682-705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/campaign/s8c_preregistration_evidence.py:682)。
- bounded graph traversal は [同:1341-1468](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/campaign/s8c_preregistration_evidence.py:1341)。

直近 artifact の126.6秒を、path-limited `git add` と reachability traversal のどちらが何秒使ったかは現 artifact から分からない。これは `s8c-preregistration-candidate` loadgroup とは別の ungrouped work unit である。

### T-080 stub-free e2e

対象11 node の exact inventory は test 自身が固定している [test_s8b_oracle_driver.py:930-1006](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_s8b_oracle_driver.py:930)。

各 node は概ね次を行う。

- process-local key ごとに base repo を1回構築し、その後各 test 用に実体 copytree する [同:890-927](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_s8b_oracle_driver.py:890)。
- `orchestrator/` 全体と Git-visible `output/` をコピーする [同:1022-1028](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_s8b_oracle_driver.py:1022)。
- visible output 列挙と copytree の実装は [同:808-887](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_s8b_oracle_driver.py:808)。
- historical source closure を復元し、ccbench を submodule add/checkout、`git add -A`、basis commit を作る [同:1043-1097](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_s8b_oracle_driver.py:1043)。
- isolated child Python で current runtime modules を import し、各 source を Git blob と比較する [同:1108-1204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_s8b_oracle_driver.py:1108)。
- draft、validate、finalize、commit、receipt verify、public gate を実行する [同:1206-1254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_s8b_oracle_driver.py:1206)。
- defect node は artifact/submodule を変異させ、複数回 verify する [同:1462-1557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_s8b_oracle_driver.py:1462)。
- draft/finalize positive node は verify、17 observation の独立 Git hash、release verify、public gate、history inspect を行う [同:1371-1459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_s8b_oracle_driver.py:1371)。

source comment の「base 構築15〜22秒」は過去の限定実測 [同:895-903](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/test_s8b_oracle_driver.py:895)。48 worker 競合下の100〜190秒をその内訳へ比例配分してはならない。

これらは ungrouped なので process-local cache が worker をまたがない。現 report に nodeid → worker がないため、同じ worker に何 node 載ったかも現在は確定できない。

`real_repo_ratified_memo.py` はこの stub-free 11 node の base builder ではない。同 memo は実 repo active generation 解決の39 Git subprocess、過去実測4.4秒を記録する [real_repo_ratified_memo.py:2-10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/real_repo_ratified_memo.py:2)。対象は conftest の exact 4 process-memo node [orchestrator/tests/conftest.py:567-574](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/orchestrator/tests/conftest.py:567) で、stub-free e2e definitions には `patch_ratified_loader` がない。

## 最小の測定計画と事前判定式

最小計画は適応的に3走または6走とする。

### A. 観測付き baseline: full K=3 を3走

同一 instrumentation tip、同一条件で逐次3走する。他 job は同時に走らせない。各 full 走には3 shard が含まれるが、D357 上の「1走」は full acceptance invocation 1回と数える。

各走で次を保存する。

- `W_r = max(shard wall)`。
- critical shard と次点 shard の差。
- 各 worker の node/phase timeline、終了時刻、idle。
- critical worker と次点 worker の終了差。
- 各候補 routine の setup/call 所要。
- collection、deselect、prewarm、initial schedule、suffix。
- tested tip、K、worker 数、collection digest。

候補 u の baseline slack を

\[
S_u=\operatorname{median}_r\left(
\min(\text{critical-worker lead},\text{critical-shard lead})
\right)
\]

とし、u が critical chain 上にない走では0とする。baseline wall は `M0 = median(W_r)`。

事前判定は次のとおり。

- 全候補で `S_u / M0 < 0.10` なら、3走で停止し「D357 解像度の単一処理なし」。これが最小3走の負結果。
- 複数候補が `S_u / M0 >= 0.10`、または critical unit が3走で入れ替わるなら、単一同定せず critical frontier。
- exactly one のコード routine が3走すべてで critical chain にあり、`S_u / M0 >= 0.10` なら「構造上の単一候補」。ただし親の x-for-x 因果定義を確定するには B が必要。

70〜77秒については、3走それぞれで

\[
W=\text{prefix}+\text{phase interval union}+\text{zero-active gaps}+\text{suffix}
\]

を閉じる。合計が JUnit wall と timer 精度内で一致しなければ、観測漏れとして同定を停止する。

### B. 因果確認: candidate-local before/after を各3走

A で exactly one が出た場合だけ、別 follow-up でその routine の自然な所要だけを短縮する、受理集合不変の介入を作る。本 wave の成果物には実装を含めない。

A の3走を before として再利用し、固定 post tip で full K=3 を3走する。合計は最小6 full 走。focus 走は証拠に数えない。

\[
\Delta W=M_0-M_1
\]

\[
\Delta U=\operatorname{median}(U_{\text{before}})
-\operatorname{median}(U_{\text{after}})
\]

事前判定式は次のとおり。

- `ΔW / M0 < 0.10`: D357 により変化なし。単一支配処理の同定を棄却。
- `ΔU <= 0`: 介入不成立。
- `ΔW / M0 >= 0.10` かつ `0.9 <= ΔW / ΔU <= 1.1`: x-for-x の単一支配処理と同定。
- `0 < ΔW / ΔU < 0.9`: 次の worker/node が wall を引き継いだ。単一ではなく frontier。
- target 外の node/collection/startup が10%以上変動、collection digest 不一致、worker 数不一致: 交絡として結論を出さない。

## 親の (P1) への反証・補強

- **P1a:** 470/484 は corpus の強い記述統計として補強される。ただし allocator は node 数重みの file/group LPT [tools/acceptance_shards.py:377-442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1933-wall-unit/tools/acceptance_shards.py:377) で、時間による shard-0 固定規則ではない。fixed-tip の不変条件にはできない。

- **P1b:** `wall` と max occupancy の相関は補強材料だが、「固定床」は反証される。K=3 recent の slope 1.540、intercept -0.5 は `wall = 75 + occupancy` と整合しない。さらに occupancy は report phase duration の和にすぎず、worker idle、real-repo lock 待ち、collection、prewarm、scheduler、suffix を除外する。`wall - max_occ` は global no-test time ではない。

- **P1c:** 「少数 node と最長 node が大半」は中央値として補強される。しかし2〜5本は普遍でなく、提供出力にも29/31/54本の走がある。ungrouped critical worker の構成は node mapping がない以上未確定。

- **P1d:** 「2系統」は粗すぎる。コード機構として少なくとも、historical candidate module fixture loadgroup、ungrouped C06 reachability evaluator、ungrouped T-080 e2e builder/verify の3つがある。さらに candidate exact five は現在 hold 対象なので、mixed-tip corpus から現 tip の criticalityを主張できない。

- **P1e 前半:** 100〜130秒帯の plateau は「単一 node を短くしても次が取る」という仮説を補強する。しかし node → worker と終了 margin がないため未証明。3走の slack 判定が必要。

- **P1e 後半:** 「残る単体処理は約75秒の process 起動/import/collection」は反証される。70〜77秒は単一処理でも連続 prefix でもなく、occupancy に入らない全時間の差分である。内訳測定前に「最大の単一項」とは認定できない。

## 残る不確実性

- mixed-tip corpus のため、historical candidate group と現 default hold 状態が混在している。
- 問いの18,954 items は対象 tip の値であり、item 数自体が走間同値性の代用にはならない。digest と tested tip を固定する必要がある。
- TestReport の `start/stop` が対象 pytest-xdist 経路で欠落なく controller へ転送されることは、実走前に unit test で固定する必要がある。
- worker 同士は同一 compute node だが、epoch clock の逆転や欠損を report validation で拒否する必要がある。
- xdist は動的 scheduler なので、観測上の slack は固定割付け counterfactualである。親の x-for-x 定義を最終確定するには paired full 3+3 が必要。
- end-to-end waiter wall を対象とする場合、PBS queue latency と artifact 回収を含めた別の milestone schema が必要になる。

## 総括

現 artifact だけからは、wall を決める単一処理は同定できない。現在確定できるのは、ungrouped C06 evaluator、T-080 stub-free e2e 群、historical candidate fixture 群からなる critical frontier の候補までである。

特に `wall - max_occ` 約70〜77秒を「テストが1本も走っていない固定床」とする解釈は成立しない。最小の穴埋めは report v2 に node → worker と phase start/stop を追加し、同一 tip の full K=3 を3走すること。そこで単一候補がなければ3走で負結果、候補が1つ出て x-for-x 因果まで確定するなら paired post 3走を加え、合計6 full 走とする。