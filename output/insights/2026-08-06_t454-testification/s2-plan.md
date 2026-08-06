## 総括

- 推奨: S1・S2を実装し、S3へ候補 (d) の strict-superset test も追加する。S4の削除は実施しない。
- 最大の risk: S1で「状態公開・producer lock・`.done` 公開」の順序を誤り、死と完了の境界に TOCTOU を作ること。
- 親前提反証1: (d) の既存testは期待集合と実集合が互いに別の場合だけで、期待集合を包含する余分な失敗を固定していない。
- 親前提反証2: 新toolは段5 U1で初めて実装されるため、同waveの段3およびU1自身ではdogfood不能。段5もU1→U2へ直列化が必要。
- 親前提反証3: 旧L2監査で唯一「発火なし」だった `DW-O10` は2026-08-06に実発火済み。現行の削除候補はゼロ、回収可能量も0 bytes。

## S1 — dev-wave 子起動・待機の機械強制 tool

### 変更面と CLI

新規 `tools/dev_wave_codex.py` と新規 `orchestrator/tests/test_dev_wave_codex.py` を追加する。両方とも現在は存在しないため、架空の line 番号は付けず、以下では予定 symbol と既存実装の根拠行を示す。`tools/codex_worker_launch.py` は変更しない。

公開 CLI は二つに固定する。

```text
python3 tools/dev_wave_codex.py launch \
  --job-dir ABS \
  --prompt-file ABS \
  --output-file ABS \
  --log-file ABS \
  --cwd ABS \
  --sandbox {read-only,workspace-write} \
  --reasoning {low,medium,high,xhigh,max} \
  [--model gpt-5.6-sol] \
  [--codex-bin codex]

python3 tools/dev_wave_codex.py wait \
  --job-dir ABS \
  [--poll-interval-ms 100]
```

`--reasoning` は `tools/dev_waves/effort_levels.py:19-25` の既存語彙をimportする。`<log-file>.done`、`launch.json`、`started.json`、`.producer.lock`、`.wait.lock` は `--job-dir` から導出し、任意path引数にはしない。

終了codeは次の意味に固定する。

| command | rc | 意味 |
|---|---:|---|
| `launch` | 0 | detached producer がlockを保持し、開始stateを公開した |
| `launch` | 2 | CLI・path・prompt・既存artifact等のpreflight拒否 |
| `launch` | 3 | state予約後のdetach／開始handshake失敗。job-dirは再利用しない |
| `wait` | 0 | 正規 `.done` を読み、Codex exit codeが0 |
| `wait` | 1 | 正規 `.done` を読み、Codex exit codeが非0。正確な値は `.done` とstdoutへ出す |
| `wait` | 2 | state、lock、`.done` が不正・不確定 |
| `wait` | 3 | 同一条件の既存waiterが生存中 |
| `wait` | 4 | producerが正規 `.done` を公開せず死亡 |

### 実装ブロック

- `_preflight_launch()`:

  - promptはabsolute、symlinkでないUTF-8 regular file、raw bytesが1 byte以上であることを、artifact作成・spawnより前に検査する。既存類似実装は `tools/codex_worker_launch.py:1519-1545`。
  - `job-dir` とartifact pathをcanonical化し、全artifactが専用directory配下であることを要求する。これは `docs/dev-wave/operations.md:14-19` の `DW-O02` を機械化する。
  - `.done`、`launch.json`、`started.json`、log、outputのいずれも、dangling symlinkを含め `lstat()` で存在したら拒否する。既存output不在契約は `tools/codex_worker_launch.py:1549-1558`。
  - preflight失敗時は `.done` を書かず、既存物を削除・切詰め・置換しない。

- `_reserve_launch()`:

  - `launch.json` をcreate-only・atomicに公開する。内容はcanonical `job_dir`、各artifact path、random nonce、`condition_id`、model/reasoning/sandbox/cwd、prompt SHA-256。
  - `condition_id = SHA-256(canonical job-dir + canonical done path + launch nonce)` とする。一つのjob-dirを一世代だけに限定し、完了後も同じdirへ再投入させない。
  - 一時fileはjob-dir内に置き、fsync後にno-replaceで公開する。外部の書込可能tmpへ依存しない。

- `_spawn_detached_producer()`:

  - shell文字列を組まず、argvとして `nohup setsid python3 tools/dev_wave_codex.py _produce ...` を起動する。stdinは`DEVNULL`、stdout/stderrはlogへ結合する。
  - 内部 `_produce` は次のCodex argvを構築する。既存の同型argvは `tools/codex_worker_launch.py:1105-1112`、安全な`Popen`形は同`:1161-1169`。

    ```text
    codex exec -m MODEL
      -c model_reasoning_effort="REASONING"
      -s SANDBOX -C CWD -o OUTPUT PROMPT_TEXT
    ```

  - producerが`.producer.lock`を `LOCK_EX` で保持してから `started.json` をatomic公開する。`launch` はこのhandshakeまで待ってrc=0を返す。
  - Codex終了後、負の`Popen.returncode`はshell互換の`128 + signal`へ変換し、正規10進数一行を`.done`へcreate-only・atomic公開する。その後にproducer lockを解放する。

- `_wait_job()`:

  - `launch.json` と `started.json` のclosed schema、nonce、condition IDを照合する。
  - condition固有の`.wait.lock`を `LOCK_EX|LOCK_NB` で全待機期間保持する。競合時はrc=3。
  - loopは必ず「`.done`を読む → producer lockをshared/nonblocking probe → 死を観測したら`.done`を再読」の順にする。
  - `.done` はsymlinkでないregular file、`0..255`のcanonical decimal一行だけを受理する。不正な`.done`は成功待ちを続けずrc=2にする。

### 5要件のfail-closed化

1. prompt非空は `_preflight_launch()` がspawn前に拒否する。`DW-O01` の根拠は `docs/dev-wave/operations.md:8-9`。
2. 既存`.done`は種類を問わず拒否し、削除しない。予約stateも残っていれば新世代を開始しない。
3. 同一条件はimmutable `condition_id` で定義し、`.wait.lock`のnonblocking排他で二本目をrc=3にする。
4. producerの生死はPIDでなく、producer自身が保持する`.producer.lock`で判定する。process終了時はkernelがfile descriptorを閉じるため、正常終了・異常終了・SIGKILLのすべてが同じ観測になる。
5. 成功・失敗を含む「完了」は正規`.done`とそこに記録されたexit codeだけで決める。log文字列、outputの存在、通知、producer死亡は成功条件にしない。

### race、PID再利用、自己一致、複数wave

- producer lock取得前には`started.json`を公開しないため、waiterが「未取得lock＝死亡」と早判定する窓を作らない。
- producerは`.done`をatomic公開してからlockを解放する。waiterも死亡観測後に`.done`を再読するため、「公開直後のprocess exit」をrc=4へ誤分類しない。
- PIDは診断fieldとして記録しても権威にしない。PID再利用で新processを旧producerと誤認しない。
- `pgrep`やcommand line scanを行わないので、waiter自身への自己一致が構造的に存在しない。
- 異なるwaveはcanonical job-dirとnonceが異なるためlockを共有しない。同じjob-dirを誤って再利用した場合はstate予約で拒否する。
- 最初のwaiterが死亡すればkernelが`.wait.lock`を解放し、新waiterは再開できる。通知のたびに同時waiterを増殖させることはできない。

### `DW-O01`との互換性

`docs/dev-wave/operations.md:8-12` が要求する次の四点を維持する。

- detachは実際に`nohup setsid`で行う。
- stdinは`/dev/null`相当。
- 成果物はCodex `-o`の最終メッセージであり、logから抽出しない。
- `wait` rc=0後も採用は別段階とし、既存 `tools/check_codex_output.py` のrc=0を必須にする。同checkerの判定は `tools/check_codex_output.py:67-115,142-152` に既に固定されている。

旧手順で作ったartifactは読替え・削除しない。新toolの`wait`はproducer lock/stateを持たない旧jobへ後付け適用せず、旧jobは従来の `DW-O01` で処理する。これが `親 brief:56-62` の既存artifact非破壊条件を守る境界である。

### 本waveでのdogfood可否

`親 brief:42` の「段3/5/6すべて」は不可能である。状態機械では段3が実装段5より先である（`.claude/commands/dev-wave.md:45-51`）。また段5 U1自身もtoolをまだ持たない。

plan v2では次の順に改める。

1. 段3と段5 U1は既存 `DW-O01` で起動。
2. U1を親が統合。
3. 段5 U2を新toolで起動して最初のdogfoodとする。
4. 段6のレビュー・fix子を、それぞれ別job-dirで新toolから起動する。

したがって `親 brief:90-91` のU1/U2並列は直列化が必要になる。

## S2 — mutation harness の生死 probe

### CLIと終了code

既存実走CLIは一切変えず、先頭tokenが`probe-running`の場合だけ別parserへdispatchする。

```text
python3 tools/mutation_harness.py probe-running --repo ABS
```

- rc=0: canonical repoのexclusive harness lock所有者が、その観測時点で存在する。
- rc=1: lock file不在、またはshared probe lockを取得・即解放できた。観測時点で所有者なし。
- rc=2: repo、lock path、open、flockの状態を安全に判定できない。

これはpoint-in-time probeであり、rc=0後の継続生存やrc=1後に新runが始まらないことまでは保証しない。

### file:line実装案

- `tools/mutation_harness.py:105-114`:

  - `HarnessLockBusy(HarnessError)` を追加し、正常なlock競合と、open/flock自体の故障を区別する。

- `tools/mutation_harness.py:1814-1835`:

  - `_lock_path_for()` のcanonical repo hashと既存pathを維持する。
  - `_lock_for(repo)` の既定動作は現在どおり `O_CREAT|O_RDWR|O_APPEND|O_NOFOLLOW` と `LOCK_EX|LOCK_NB`。
  - probe用modeでは同じpathを`O_RDONLY|O_NOFOLLOW`、no-create、`LOCK_SH|LOCK_NB`で開く。lock file不在は「未走行」として扱い、probe自身はtmpにfileを作らない。
  - `EACCES/EAGAIN`相当の競合だけを`HarnessLockBusy`とし、その他の`OSError`はrc=2相当の`HarnessError`にする。

- `tools/mutation_harness.py:1857-1878`:

  - 現在の実走parserは変更しない。隣に`_probe_parser()`を置き、`--repo`以外を受け付けない。
  - subparser化で既存 `--repo --spec ... -- command` を壊さず、`main()`の先頭token dispatchだけを追加する。

- `tools/mutation_harness.py:1881-1918`:

  - `probe-running`は`resolve(strict=True)`後、`_repo_head()`でworktree rootそのものか確認する。既存確認は同`:344-357`。
  - 実走側はexclusive取得がshared probeだけに阻まれた場合、短いbounded retryを行う。shared取得も失敗する場合だけ「別のexclusive harness」と判定する。
  - これによりprobeのshared lockは本走を一時的に遅らせても、「別harness」と誤認させて拒否しない。二本の本走はどちらもexclusiveなので、現行の一走限定を維持する。

- `tools/mutation_harness.py:1919-2090`:

  - lock取得後のHEAD固定、clean検査、collection、baseline、mutation、ledger、finally closeは変更しない。

### 既存fail-closed経路との相互作用

- 通常走行: exclusive lockは現在と同じ全期間保持される。既存 `test_flock_rejects_a_competing_harness_for_the_same_repo`（`orchestrator/tests/test_mutation_harness.py:698-704`）を壊さない。
- `--resume`: lock取得後に既存ledgerを検証する順序（`tools/mutation_harness.py:1928-1948`）を維持する。resume中もprobeはrc=0。
- `--plan-only`: 現状はlock取得後に `tools/mutation_harness.py:1965-1966` で戻るため、その短い期間もrc=0と定義する。
- SIGINT/SIGTERM: handler設置・復元は同`:2006-2008,2084-2085` のまま。probeはsignal handlerやsource復元へ触れない。
- active mutation:既存の復元finallyと検査を変更しない。関連testは `test_signal_arriving_during_restore_is_deferred_until_all_targets_verified`（`:746-779`）と `test_sigterm_handler_stops_child_and_restores_active_mutation`（`:815-856`）。
- SIGKILL: kernelはlockを解放するためprobeはrc=1になるが、「台帳完了」「repo clean」を意味しない。既存testはSIGKILL後に変異sourceが残り得ることを示す（`:782-812`）。再開時はclean検査 `tools/mutation_harness.py:1920-1923` が止める。
- lock fileの存在は生死に使わない。process死亡後もfileが残ってよく、flockの取得可否だけを権威にする。
- PID、process名、`pgrep -f`は一切使用しないため、PID再利用とprobe自身への文字列一致は射程外になる。

## S3 — 機械検査をpinするpytest

`pytest.ini:12-14` により新規fileも `orchestrator/tests/` 配下で自動収集される。

### 新規 `orchestrator/tests/test_dev_wave_codex.py`

現行lineは存在しない。追加するnodeは次のとおり。

- `test_launch_rejects_empty_prompt_before_any_artifact_or_spawn`
- `test_launch_rejects_existing_done_without_mutation_or_spawn`
- `test_launch_uses_nohup_setsid_and_dw_o01_codex_argv`
- `test_same_condition_rejects_second_waiter`
- `test_distinct_job_conditions_do_not_contend`
- `test_wait_returns_producer_dead_after_lock_release_without_done`
- `test_wait_rechecks_done_after_producer_release_race`
- `test_wait_completion_matrix_is_done_and_exit_code_only`
- `test_wait_does_not_treat_self_or_reused_pid_as_liveness`

最後の三nodeでは、valid output、log内の終了語、通知相当fileが存在しても`.done`なしでは成功しないこと、rc=0/非0、malformed `.done`、`.done`公開直後のproducer終了をtable-drivenに固定する。

fake Codex executableとjob artifactはpytest管理directory内だけに作り、networkを使用しない。detach testは必ずtimeoutと`finally` cleanupを持たせ、失敗時にprocessを残さない。

### `orchestrator/tests/test_mutation_harness.py`

`orchestrator/tests/test_mutation_harness.py:698-704` のlock test近傍へ追加する。

- `test_probe_running_then_not_running_after_lock_owner_process_exit`
- `test_probe_shared_observation_never_causes_run_lock_rejection`
- `test_probe_absent_lock_returns_one_without_creating_lock_file`
- `test_probe_canonical_repo_alias_uses_same_lock_identity`
- `test_probe_unsafe_lock_error_is_indeterminate`

process間同期はsleep推測でなくpipe/event handshakeを使う。最初のnodeは子processがexclusive lock取得済みと通知してからrc=0を確認し、子終了後rc=1へ変わることを固定する。

### 候補 (d) の純増test

`orchestrator/tests/test_mutation_harness.py:341-350` の直後へ、次を追加する。

```text
test_extra_failed_node_is_mismatch_even_when_all_expected_nodes_fail
```

入力は `expected={one}`、`failed={one,two}`、pytest rc=1とし、`MISMATCH`を要求する。

親の「純増検出力ゼロ」は反証される。既存 `test_parameter_suffix_is_matched_exactly` は `expected={one}`、`failed={two}`で互いに素である（`:341-349`）。実装を `expected_keys <= failed_keys` に変異しても既存testは引き続き`MISMATCH`になり、変異をkillできない。新nodeだけがその変異を`KILLED`誤判定として検出する。実際に「期待nodeをすべて含む上位集合が赤になった」履歴も `docs/worklog.md:2746-2751` にある。

productionの完全一致自体は `tools/mutation_harness.py:1191-1193` に既にあるため、(d)についてproduction変更は不要である。

### 重複になるため追加しないnode

- 期待nodeのcollection不存在: `test_expected_node_must_exist_in_pytest_collection`（`orchestrator/tests/test_mutation_harness.py:330-338`）が既にpin済み。
- parameter suffixが別nodeになる場合: `test_parameter_suffix_is_matched_exactly`（`:341-350`）が既にpin済み。
- 同repoのexclusive二重走行: `test_flock_rejects_a_competing_harness_for_the_same_repo`（`:698-704`）が既にpin済み。
- resumeのHEAD/spec/ledger整合:既存node群 `:421-586` がpin済み。
- output checkerの正常・小片・見出し・非regular等: `orchestrator/tests/test_check_codex_output.py:25-55,68-115` がpin済み。S1側で同じvalidator仕様を複製しない。
- `tools/codex_reasoning_ab.py` の`.done`は、事前に空fileを作って後からJSONで上書きする別protocol（`:1950-1955,2112-2120`）なので、S1の既存`.done`拒否をpinする既存nodeとは数えない。

段4の変異事前登録には最低限、次を入れる。

- S1: prompt guard除去、既存done拒否除去、wait lockのnonblocking除去、producer-death分岐除去、log終了語を成功にする変異。
- S2: probeをsharedからexclusiveへ変える変異、lock file存在だけでrunningとする変異。
- (d): `failed_keys == expected_keys` を `expected_keys <= failed_keys` へ変える変異。

## S4 — `docs/dev-wave/**` 削除候補

### 現行L2外延

L2の定義は `docs/dev-wave/core.md:5-9`、段・条件dispatchは `.claude/commands/dev-wave.md:56-75,80-105`。

現行ではL1が `O01/O02/O03/O05/O13/O23`、L2は次の13節、合計5,081 bytesである。`DW-O15` は既にT-450で削除済み（`tools/check_docs.py:352-355`）。

| 節 | 現行範囲 | bytes |
|---|---|---:|
| O04 | `docs/dev-wave/operations.md:26-30` | 200 |
| O06 | `:36-40` | 210 |
| O08 | `:41-45` | 183 |
| O09 | `:46-58` | 935 |
| O10 | `:59-63` | 261 |
| O11 | `:64-68` | 223 |
| O12 | `:69-73` | 195 |
| O14 | `:78-82` | 200 |
| O16 | `:83-88` | 367 |
| O17 | `:89-97` | 702 |
| O18 | `:98-104` | 441 |
| O19 | `:105-113` | 675 |
| O20 | `:114-120` | 489 |

### 発火実績の反証検索

repo全体検索は `rg -n -uuu '<語>' . --glob '!.git/**'` とし、`docs/archive/**`、`output/insights/**`を除外しない。O04とO11は文書への記録有無だけでなく、実commit message・削除履歴も検索する。

| 節 | 反証検索語 | 発火反証 |
|---|---|---|
| O04 | `防護パス.*commit`, `output/campaigns`, `git commit -F` | 実commit messageで発火済み。`output/insights/2026-08-04_t412-l2-pruning/README.md:112-120` |
| O06 | `submodule.*偽赤`, `sandbox 由来`, `index lock` | 親環境での独立再現が実施済み。同`:145-148` |
| O08 | `submodule update --init`, `未初期化.*停止` | T-207等で発火済み。同`:149-151` |
| O09 | `FROZEN_MANIFEST`, `pin 閉包`, `review ledger` | F27/F30/F39/F78を含め頻発。同`:152` |
| O10 | `producer.*書き出し面`, `全ファイル種`, `DW-O10` | 旧監査後に実発火。`output/insights/2026-08-06_t419-u2-recalibration/s4-adjudication.md:88-105,215-221` |
| O11 | `git add -A`, `未 stage 削除`, `git log --diff-filter=D` | commit `72e3800` の実削除で発火済み。T412 README`:83-90` |
| O12 | `DW-O12 訂正`, `裁定.*未実装`, `実際に実行` | 手順訂正実績あり。同`:153-154` |
| O14 | `正規注入 seam`, `monkeypatch.*最後`, `current_head` | 正規seam非等価確認で発火済み。同`:155` |
| O16 | `closed.*partial.*regressed`, `NO-GO`, `3 巡` | T-287等で発火済み。同`:156-157` |
| O17 | `AI-Agent:`, `--dry-run -F`, `--no-edit` | 実commitとF25/F37で発火済み。同`:158` |
| O18 | `単独再走`, `差分.*到達しえない`, `測った checkout` | 親受入実走で発火済み。同`:156-157` |
| O19 | `git diff --stat`, `git checkout --`, `mutation-ledger` | tracked変異・復元で発火済み。同`:156-157` |
| O20 | `check_wave_startup.py`, `external-handoff`, `clean-tree` | F48/F49/F50とT-412自身で発火済み。同`:159` |

特に旧監査はO10だけを「発火実績なし」としていた（T412 README`:135-143`）が、上記T-419の実測によって現在はその条件も成立しない。

### 機械代替とbyte結論

全13節が「発火実績なし」を満たさないため、三条件の積集合は空である。したがって節ごとの削除候補はなく、回収可能量は **0 bytes**。

なお `tools/check_docs.py` は全節の一意存在を `:376-394,3577-3595`、dispatch写像を `:3822-3855` で固定しているが、これは義務本文の代替ではない。`docs/skill-self-improvement.md:83-84` も、同checkerの担保範囲をbyte・構造に限定している。旧O10についてもproducerの全書出し種を検査する機械検査は存在しないとの実測がある（T412 README`:135-141`）。

よって親へ返すS4裁定パッケージは「削除候補なし・0 bytes・削除未実施」とする。`docs/dev-wave/**`、その他のMarkdown本文、`tools/check_docs.py` は本waveで変更しない。