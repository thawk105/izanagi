## 総括

`certify` を「3 回の実 exact-N 計測 → receipt 生成 → `run` 1 回」を同一親 process が完遂する原子的 subcommand とする。receipt-only で終了する形では、生存 scope の所有・解放を安全に閉じられない。  
`derive_split → _shard_documents → _wrapper_argv` を共通 planner へ抽出し、4 走すべての `outer_argv` canonical bytes を完全一致させる。既存 admission schema・validator の受理集合は変更しない。  
現行 validator は実際の child 起動までは証明しないため、P2 の論理的根拠は誤り。ただし producer 実装は実 wrapper・merge 成功からしか rc を生成せず、結論としては実走 3 回を維持する。  
最大の危険は、未知 peak の測定 scope が user slice と同じ `memory.max` を必要とし、より低い aggregate hard cap を置けない点、および固定 HEAD 同一性のため実装 commit 前には本走不能な点である。

## 1. certify 経路の設計

subcommand 名は `certify` とし、単独の receipt producer ではなく「certify-and-run」とする。

```text
python3.10 tools/mutation_fanout.py certify
  --source-repo REPO
  --commit COMMIT
  --parent-spec AB_PARENT_SPEC
  --expected-parent-sha256 SHA256
  --shard-count 2
  --group-root GROUP_ROOT
  --certification-root CERT_ROOT
  [--poll-interval 0.05]
  [--barrier-timeout 120]
  --
  python3.10 tools/run_tests.py --force-dispatch NODEID... -q -rf
```

`--repetitions` は設けず、`MIN_CERTIFICATION_REPETITIONS == 3` を exact 値として使う。反復数を CLI から下げられる面を作らない（[mutation_fanout.py:45-64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:45)）。

出力はすべて repo 外の fresh `CERT_ROOT` とする。

- `measurement-001.json`〜`003.json`: 既存 `MEASUREMENT_SCHEMA` の canonical JSON
- `admission.json`: 既存 `ADMISSION_SCHEMA` の canonical JSON
- `certification-report.json`: 新規の運用 report。各反復、cleanup、scope、request 対応、最終 `run` rc を記録
- `GROUP_ROOT`: 3 計測反復後は毎回消去し、最後の admitted `run` の成果物だけを残す

`tools/mutation_fanout.py:1411-1520` から次を抽出する。

1. `_derive_fanout_plan(config, initial_roots)`  
   commit 解決、固定 HEAD identity、親 bytes、`derive_split`、assignment hash、input binding、`_shard_documents`、`_wrapper_argv`、expected invocation を一つの immutable `FanoutPlan` にする。
2. `_materialize_fanout_plan(plan, ...)`  
   `root.mkdir`、`write_split`、scratch、`group.json`、`driver-report.json` の create-only 生成だけを担当する。
3. `_execute_materialized_fanout(plan, ...)`  
   barrier、exact-N launcher、単一 waiter、registry 検査、`merge_group` を担当する。admission の省略可否を引数にせず、`run_fanout` と private certification worker の二つの厳格な caller だけから呼ぶ。

分割は親 raw bytes と N だけで決まり、shard bytes も canonical 化される（[mutation_fanout_contract.py:506-591](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout_contract.py:506)）。続いて同じ `root` から path 群を作り（[mutation_fanout.py:590-653](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:590)）、同じ `sys.executable`・resolved source・commit・runner argv で wrapper argv を構成する（[mutation_fanout.py:656-688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:656)）。各反復の実行結果には、実際に使った `canonical_json_bytes(outer_argv)` の SHA-256 を入れ、最初の plan と byte 比較する。canonical serializer は唯一の実装を再利用する（[mutation_fanout_contract.py:141-146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout_contract.py:141)）。

`main()` は次の順に分岐する。

1. `_launch`
2. `cancel`
3. private `_certify_repetition`
4. public `certify`
5. `run` のみ既存 bounded-scope re-exec

したがって `certify` 自体は、存在しない receipt を読もうとせず、bounded scope に再 exec しない。3 本の private worker は user-slice `memory.max` の measurement scope に入り、最後に `certify` が新しい subprocess として `run ... --admission-receipt CERT_ROOT/admission.json` を一度だけ起動する。その `run` だけが現行どおり receipt の `certified_peak_bytes` を読み、`_run_in_bounded_scope` へ入る（[mutation_fanout.py:1838-1872](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:1838)）。

なお、certify 実機走行は実装 bytes が `--commit` の blob になった後でなければ不可能である。driver と wrapper の実行 bytes は指定 commit の blob と一致しなければ拒否されるため、実装 commit C を先に作り、C を `--commit` に渡す（[mutation_fanout.py:282-337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:282)）。

## 2. create-only との衝突

状態遷移を次に固定する。

| 時点 | `GROUP_ROOT` | 処置 |
|---|---|---|
| certify 開始 | 不在必須 | registered worktree 外か検証 |
| 反復 1 | create-only 生成 | exact-N、merge、request 監査 |
| 反復 1 後 | 完全撤去 | 不在を再検査 |
| 反復 2・3 | 同じ絶対 path で反復 | 同一 `outer_argv` |
| receipt 作成時 | 不在必須 | admitted run 用 clean state |
| admitted `run` | create-only 生成 | 最終成果物として残す |

現行の `root.mkdir`、`write_split`、`group.json`、report はすべて既存 path を拒む（[mutation_fanout.py:1447-1464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:1447)、[mutation_fanout_contract.py:594-645](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout_contract.py:594)）。したがって「反復ごとに別 root」は outer argv を変えるので不可であり、同じ root の完全撤去が必要になる。

各 measurement materialize の直後に `.certify-owner.json` を create-only で置き、certification token、反復番号、root の `st_dev/st_ino`、source、commit、parent hash、N を束縛する。`_remove_owned_group_root` は以下を全部満たした場合だけ `shutil.rmtree` する。

- N child がすべて 0/1、merge index が生成済み
- `preserved_containers == []`
- measurement 開始前後の worktree registry が一致
- request 対応が完全
- root が symlink でない directory で、現在の inode と owner marker が一致
- root はその時点の全 registered worktree の外

wrapper は terminal ledger のときだけ、自分の container と、自 checkout に backpointer が一致する単一 admin directory を削除する（[mutation_worktree.py:875-933](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_worktree.py:875)、[mutation_worktree.py:1112-1149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_worktree.py:1112)）。certifier はこの後段で group root だけを処理し、`git worktree remove` や `prune` は使わない。

撤去例外、部分撤去、撤去後も `exists()`/`is_symlink()` が真、親 directory の fsync 失敗はすべて `certification-report.json` の `state=stopped`、rc=2 とする。次反復・receipt 作成・admitted run へは進まない。非 terminal や preserved container の場合は証拠を残して停止し、自動撤去しない。

## 3. 測定 scope の生存契約

各反復は private `_certify_repetition` を独立した `systemd-run --user --scope` で起動する。cap は開始時の `login_headroom().memory_max_bytes` とし、既存 `_scope_command` と `_bounded_scope_cgroup` の property 検査を再利用する（[mutation_fanout.py:1313-1383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:1313)）。

worker は次の handshake を行う。

1. 自分の cgroup path、`memory.max`、`memory.swap.max`、`memory.oom.group` を検証し、create-only ready record を書く。
2. 親 certifier が外側から sampler を開始するまで barrier で待つ。
3. exact-N と merge を完遂し、実 child rc と actual outer hash を create-only result に書く。
4. 親 PID/starttime が生きている間、scope 内に idle holder として残る。

親は3本を順次測定するが、完了済み worker を終了させない。3本が `populated 1` のまま receipt を作り、その receipt を渡した最終 `run` が終了するまで保持する。これは「validation 時点まで」を超えて保持する保守側の実装であり、別 invocation 間の orphan protocolを不要にする。終了・例外・signal の全経路で、所有 token が一致する3 unitだけを解放し、process 回収と scope 消滅を report する。

sampler は scope の `memory.current` を単調時刻付きで読み続ける。worker が terminal result を書いて待機状態へ入った後、親が同 scope の kernel `memory.peak` を読む。通常の `memory.current` samples に加え、`monotonic_ns > 前値` としてこの kernel peak を最後の checkpoint に置く。これにより、poll 間に生じた瞬間 peak も `max(samples)` に含まれる。receipt 作成前には現行 `_attest_measurement_cgroup` をそのまま呼び、3 scope の peak、user-slice と同値の `memory.max`、`populated 1` を再検証する（[mutation_fanout.py:401-419](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:401)、[mutation_fanout.py:533-564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:533)）。

これは gate の自己申告化ではない。producer が log に小さい値や任意値を書いても、validation は log の `max(samples)` と、生存中の cgroup から独立に再読した kernel `memory.peak` の完全一致を要求する。大きく偽装しても小さく偽装しても一致しない。scope path の重複、scope 消滅、`memory.max` の変化も同じ既存 gate で落ちる（`mutation_fanout.py:477-555`）。

測定開始前は `login_headroom.reserve(MAX_LOCAL_BUDGET_BYTES)` を一つ保持し、反復は直列にする。観測不能・予約拒否なら scope を一つも起動しない。判定は回収不能量、既存予約、見積り、固定予約を14 GiB天井へ加算する既存式を使う（[login_headroom.py:865-914](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/orchestrator/campaign/login_headroom.py:865)、[login_headroom.py:1200-1245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/orchestrator/campaign/login_headroom.py:1200)）。

## 4. 反復の中身

P2 の「validator が実 exact-N を論理的に要求する」は成立しない。

- measurement schema は `outer_argv` と `child_returncodes` を別々の JSON field として持つだけで、PID、exec identity、child log hash は持たない（[mutation_fanout.py:84-96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:84)）。
- validator は outer argv の値/hashを投入へ束縛するが、rc については「長さ N、各値 0/1」しか検査しない（[mutation_fanout.py:449-461](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:449)、[mutation_fanout.py:526-532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:526)）。
- cgroup attestation も memory 値を証明するだけで、N 個の argv が exec されたことは証明しない。

したがって固定 HEAD producer が意図的に `[0, 0]` を書けば、より安い処理でも構造上は receipt を作れる。しかし、それは実測ではなく証拠捏造なので採らない。

実装は `child_returncodes` を外部入力や sampler callback から受け取らず、共通 `_execute_materialized_fanout` が生成した `Child.rc` だけから作る。全 child は barrier 後に実 wrapper argvへ `execv` され、単一 waiter が実終了値を保存する（[mutation_fanout.py:741-785](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:741)、[mutation_fanout.py:797-823](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:797)）。さらに `merge_group` が terminal wrapper state、ledger、attempt、receipt、request 数を検証してからでなければ measurement log を出さない（[mutation_fanout_contract.py:1286-1307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout_contract.py:1286)、[mutation_fanout_contract.py:1470-1512](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout_contract.py:1470)）。

よって運用上の結論は「実 exact-N 3回 + admitted run 1回」である。既存 A/B が L01/L02 の2変異なら、1セット当たり `input_count + 2N = 2 + 4 = 6 request`、合計24 requestとなる（[mutation_fanout.py:1478-1481](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:1478)）。rc=1 は terminal なので計測反復としては有効だが、rc=125等は無効である。

## 5. テスト設計

既存テストは receipt の手作成と attestation stub、または既存 `run` の失敗を検査している（[test_mutation_fanout.py:131-230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/orchestrator/tests/test_mutation_fanout.py:131)、[test_mutation_fanout.py:394-464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/orchestrator/tests/test_mutation_fanout.py:394)）。その期待値は変えず、次だけを純増する。

- `certify` が存在しない receipt を読まず、最終 `run` だけを bounded-scope re-exec へ送る。private worker の直起動、scope marker 欠落、親 PID/starttime 不一致は child 起動前に拒否する。
- 反復の actual outer hash が一つでも違う場合、measurement log・receipt・最終 run を生成しない。runner argv、N、group root、interpreter path の各 drift を個別に撃つ。
- N child の一つが未起動、非 terminal、または result から欠落した場合、fabricated `[0] * N` へ補完せず停止する。3反復すべてで実 fake wrapper の call 数が `3N` にならない変異を落とす。
- 既存 group root、certification root、measurement log、receipt の pre-create をすべて拒否し、一つも上書きしない。
- 反復1後の撤去失敗、撤去後の残存 path、owner marker/inode 差替えで、反復2へ進まない。他 worktreeやforeign directoryを削除しない。
- holder が receipt validation 前に終了、`populated 0`、重複 cgroup path、`memory.max` 不一致、kernel peak の後進があれば receiptを発行しない。`_CGROUP_ROOT` を一時 fixture rootへ差し替え、stub callbackではなく実 `_attest_measurement_cgroup` の三条件を個別に撃つ。
- log 作成後に kernel peak が増えた場合、最終 `run` が既存 attestation で拒否されることを確認する。producer側の先行検査だけを成功条件にしない。
- `inspect_or_cancel_owned_requests(cancel=False)` が orphan、重複ID、未解決request、authority不一致を返した場合、groupを消さずreceiptを発行しない。既存テストはそれらをreportへ残すところまでなので、certifyの停止接続が純増になる（[test_mutation_fanout.py:740-846](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/orchestrator/tests/test_mutation_fanout.py:740)）。
- 最終 `run` が例外・rc2でも、所有する3 holderを `finally` で解放する。逆に validation より前には一つも解放しない。
- Pegasus限定の実-kernel testを明示 nodeid として追加し、実 scope の一つをvalidation前に失わせてrc2を確認する。通常環境でskipされた結果を「実 kernel 緑」とは数えず、本番 A/B 走をpositive integrationとする。

production CLIには fake executor、attestation bypass、反復数変更を露出させない。テスト用差替えは既存 fixture／monkeypatch側だけに置く。

## 6. 本走の実行計画

まず L01/L02 の mutation object を変更せず一つの親 spec に連結し、repo 外へ凍結する。元の2 specは各1 mutationである（`liveness-shard-a.json:6-23`、`liveness-shard-b.json:6-23`）。runner nodeidも既存の2件を維持する。

実装 commit C の後、次を一度だけ実行する。

```bash
/usr/bin/python3.10 tools/mutation_fanout.py certify \
  --source-repo /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n \
  --commit <implementation-commit-C> \
  --parent-spec /work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t851-fanout-exact-n/t851-ab-parent.json \
  --expected-parent-sha256 <sha256> \
  --shard-count 2 \
  --group-root /work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t851-fanout-exact-n/exact-n-group \
  --certification-root /work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t851-fanout-exact-n/certification \
  --poll-interval 0.05 \
  --barrier-timeout 120 \
  -- /usr/bin/python3.10 tools/run_tests.py --force-dispatch \
  orchestrator/tests/test_mutation_worktree.py::test_scratch_symlink_is_rejected_between_observation_points \
  orchestrator/tests/test_mutation_harness.py::test_cumulative_replacement_uses_the_result_of_the_previous_anchor \
  -q -rf
```

投入前には `python3.10 -m orchestrator.campaign.queue_state`、`qstat -Q`、`check_quota`、`rbudgetcheck` を保存する。queue が停止中なら測定しない（[pegasus-runbook.md:300-316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/docs/pegasus-runbook.md:300)）。

6項目の採取点は次とする。

1. **cgroup `memory.current` 3反復**  
   各 measurement scope の ready 直後から terminal result まで親 sampler が採る。最後に kernel peak checkpointを加え、receipt 作成前と最終 run validation の二度 `_attest_measurement_cgroup` を通す（`mutation_fanout.py:401-419, 477-566`）。

2. **Git admin burst**  
   barrier 作成時刻を起点に、`_shard_documents` が導いた N checkout の `.git` backpointerが共通 `<common>/worktrees` に現れる時刻をread-onlyで監視する。N同時存在数、最初／最後の登録遅延、各 child rc・launcher log、terminal後の自admin消滅をreportする。実 add は [mutation_worktree.py:484-540](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_worktree.py:484)、同時開始点は [mutation_fanout.py:1639-1650](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:1639)。

3. **`df -Pi`**  
   certifier親が各セットの開始前、N admin登録直後、group撤去前、撤去後、最終 run 後に次をcaptureする。

   ```bash
   df -Pi -- \
     /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n \
     /work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t851-fanout-exact-n \
     /tmp
   ```

   `/tmp` はharness lock、`/work` はgroup・checkout・evidenceを含む。quota確認の正規 command は `check_quota`（[pegasus-runbook.md:258-275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/docs/pegasus-runbook.md:258)）。

4. **全 request 対応**  
   各反復は撤去前、最終 run は終了後に `inspect_or_cancel_owned_requests(..., cancel=False)` を呼ぶ。attempt claims、orphan evidence、receipt、job name、owner、qstatを current group authorityへ束縛する（[mutation_fanout.py:1122-1283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:1122)）。さらに merge index の request集合と完全一致させ、A/Bなら各セット6、全体24 requestを要求する。検査中は `qdel` を一度も呼ばない。

5. **fair-share**  
   `rbudgetcheck` を投入前、各計測反復後、最終 run 後に採る。各 dispatch receipt の raw immediate `qstat -f`、`state_history`、`queue_wait_s` をrequest・shard順で保存する（[dispatch_compute.py:1510-1545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/pegasus/dispatch_compute.py:1510)、[dispatch_compute.py:1592-1635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/pegasus/dispatch_compute.py:1592)）。ただしfair-share効果は未確認であり、1回の時系列から因果効果までは主張しない（[pegasus-runbook.md:1107-1115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/docs/pegasus-runbook.md:1107)）。

6. **最終 `git worktree list` 残渣ゼロ**  
   certify直前と全終了後に次を保存し、driver reportの initial/final registryとも照合する。

   ```bash
   git -C /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n \
     worktree list --porcelain
   ```

   current group由来のcheckoutが0件、unexpected/missingが空であることを要求する。現行driverも全体registry差をrc2にする（[mutation_fanout.py:1697-1730](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:1697)）。

他waveへ触れない保証は、全可変成果物をこのwaveのrepo外 `GROUP_ROOT/CERT_ROOT`へ閉じ、wrapperがbackpointerで証明した自adminだけを消し、certifierがowner markerで証明したgroup rootだけを消すことで作る。全request検査は`cancel=False`、`git worktree remove/prune`は不使用とする。7 waveのいずれかが実行中にregistryを変更した場合、現行の全体registry gateが本走をrc2にするが、その差を「修復」するため他waveを削除してはならない。

## 7. 本走が構造的に成立しない可能性

### 実装で解けるもの

- producer CLI不在、planning重複、同一rootのcreate-only衝突、scope holder不在、samplingのpeak取り逃しは、上記の共通planner・原子的certify・所有付き撤去・kernel peak checkpointで解ける。
- request対応の保存は、既存 `inspect_or_cancel_owned_requests` と `merge_group` のrequest indexを計測反復にも接続すれば解ける（`mutation_fanout.py:1122-1283`, `mutation_fanout_contract.py:1380-1405`）。
- 固定HEAD同一性は、実装commit Cを本走より前に作れば解ける。ただし段6受入前にcommitを作らない運用を厳守するなら本走と両立しないため、段4で「code/test commit → 本走 → 記録commit」の境界を明示裁定する必要がある。

### gateを変えずには解けない／外部状態に依存するもの

- measurement scopeの `memory.max` はuser sliceの値そのものを要求するため、未知peakの初回測定を、より低いaggregate hard capで完全に封じることは現行attestationと両立しない（`mutation_fanout.py:401-418`）。予約と監視は事故範囲を減らすが、sampling間の瞬間超過を防ぐkernel hard capではない。
- 3反復後に `certified_peak + margin` が利用可能headroomを超えれば、`reserve` は正しく拒否する。外部負荷が下がるまで待つ以外に実装上の解決はなく、estimateを小さく書くのは不可（`login_headroom.py:881-913`）。
- holder待機中にkernel peakがさらに上がれば、最終validationは一致せず拒否する。そこでlogを書き換える、attestationを緩める、scopeを終了済みでも認める案はすべて却下する。
- queue停止、qsub失敗、非terminal wrapper、dispatch receipt欠落、preserved containerが一つでも出れば、その反復はcertificate材料にならない。自動削除やrcの0/1への丸めはできない（[mutation_worktree.py:1131-1156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_worktree.py:1131)）。
- 他waveが同じ共有Git registryを本走窓内で増減すると、現行global registry gateは自分由来でなくてもrc2にする。quiet windowの確保は運用で解けるが、このwave内で他waveを停止・削除して解くことはできない。
- fair-shareの長期影響は、3計測+1本走の一系列だけでは一般化できない。即時queue waitやpoint差が悪化すれば不採用にできるが、悪化しなかったことから将来も安全とは証明できない。
- 実kernelがlive scopeの`memory.peak`、数値`memory.max`、`populated 1`を同時に提供できない環境なら、fan-out admissionはその環境では構造的に不成立である。gateを緩めず「不採用／実行不能」を結論とする。

以上は静的検査による計画であり、pytest・systemd scope・qsubの実走結果は主張していない。