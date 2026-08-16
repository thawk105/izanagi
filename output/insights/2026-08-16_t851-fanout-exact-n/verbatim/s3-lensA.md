## 総括

判定は **NO-GO**。段 4 で実装を止め、brief / plan を差し戻すべきである。  
`certify` は validator の文面を変えないまま、receipt 前の exact-N 3 走を新たに許すため、運用上の admission 集合を拡大する。  
attestation は測定 cgroup と wrapper 実行を束縛せず、無関係 sleeper・同一 scope の別表記・捏造 sample で receipt を成立させられる。  
さらに identity は HEAD ではなく caller 指定 commit の 2 blob にしか束縛されず、測定証拠は削除され、最終台帳にも admission が残らない。  
「fan-out 不採用」で閉じるか、schema・wrapper・attestation・台帳まで scope を広げるかを裁定パッケージへ返すべきである。

### 1. receipt 前の 3 走が admission gate の別名 bypass になる

**判定: real / stop**

file: [s2-plan.md:47-57](</work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t851-fanout-exact-n/artifacts/s2-plan.md:47>)、[s2-plan.md:87-104](</work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t851-fanout-exact-n/artifacts/s2-plan.md:87>)、[mutation_fanout.py:1537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:1537)

現行 public `run` は receipt validation、bounded scope attestation、reservation の後でだけ wrapper を起動する。提案は public `certify` から private `_certify_repetition` を呼び、同じ exact-N 実行を receipt 無しで3回行う。private 名、親 PID、token は「誰が呼べるか」を狭めるだけで、**receipt 無しの投入である事実を変えない**。

しかも measurement scope の hard cap は未知 peak に対応するため user slice の `memory.max`、すなわち brief 実測では 16 GiB である。保持する `MAX_LOCAL_BUDGET_BYTES` 予約は会計上の 4 GiB であって kernel hard cap ではない。これは「既知 peak + margin の bounded scope」を bootstrap の名で外している。

**成果物影響:** certification report は `3 repetitions/finished`、採否は `fan-out 採用`になりうる一方、最初の18 requestは admission を通らず、最終 merge 台帳には admitted run の6 requestしか残らない。

### 2. 無関係 sleeper だけで通る receipt を具体的に構成できる

**判定: real / stop**

file: [mutation_fanout.py:401-418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:401)、[mutation_fanout.py:477-565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:477)、[mutation_fanout.py:84-96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:84)

次の綴りで、3回の mutation 実行無しに現行 validator を通せる。

1. `MemoryMax=<user slice memory.max>` の scope `S.scope` を1本作り、`sleep` だけを残す。
2. `S.scope/memory.peak` を読み、その値 `p` を sample に書く。`child_returncodes=[0,0]` と期待 `outer_argv` は手書きする。
3. repetition 1〜3 の別 log を作る。cgroup path は例えば以下のように raw string だけ変える。

   ```text
   .../app.slice/S.scope
   .../app.slice/../app.slice/S.scope
   .../app.slice/../app.slice/../app.slice/S.scope
   ```

   `cgroups` の重複検査は raw string 比較だが、attestation は `resolve(strict=True)` 後に読むため、3本とも同じ scopeへ到達する。
4. driver file、指定 commit blob、絶対 path から公開情報で identity object を作り、producer/sampler の両 fieldへコピーする。
5. `certified_peak_bytes = p + max(25%, 128 MiB)` として receipt を作る。

これで `memory.peak == max(samples)`、`memory.max` 一致、`populated 1`、異なる cgroup path 文字列、異なる log path、identity equality が全部成立する。PID、starttime、`cgroup.procs`、wrapper と scope の関係を示す field は存在しない。

攻撃別の判定は次のとおり。

- **peak 押上げ: real。** sleeper scope 内で余分な memory を確保し、その後の kernel peak を sample に写せばよい。採用を不当に高コスト側へ倒せる。
- **peak 抑制: real。** 本物の wrapper を別 scope で走らせるか全く走らせず、低 peak の sleeper scope を receipt に選ぶ。
- **`populated 1` の無関係 sleeper: real。** predicate は process identityを一切見ない。
- **正しい scope を固定したまま log の数値だけ変更: refuted。** log hashとkernel peak完全一致で落ちる。ただし log・receiptを組で差し替える署名防壁はなく、scope差替え攻撃は残る。

**成果物影響:** `certified_peak_bytes` が workload peak ではなく sleeper peakへ変わり、report は3 scopeを独立測定済みと誤記し、台帳の本走は過小 capまたは意図的な過大 capで実行される。

### 3. `memory.peak` を `memory_current_bytes` として書く案は sample 捏造そのもの

**判定: real**

file: [s2-plan.md:91-102](</work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t851-fanout-exact-n/artifacts/s2-plan.md:91>)、[mutation_fanout.py:533-555](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:533)

plan は polling が瞬間 peak を逃した場合、後から読んだ kernel `memory.peak` を、未来の `monotonic_ns` を持つ最後の `memory_current_bytes` sampleとして追加する。だが `memory.peak` はその時刻の `memory.current` ではなく、過去区間の最大値である。

これは schema を変えずに別統計量を同名 fieldへ詰める意味拡張である。正しい解は `kernel_peak_bytes` を独立 fieldにし、`max(memory_current samples) <= kernel_peak_bytes` と kernel 再読を照合する schema v2 である。

**成果物影響:** certified peak の数値自体は保守側でも、measurement log の時系列に存在しない `memory.current` 観測が追加され、report と proof chain が虚偽になる。

### 4. 3 predicate の raw 受理集合と stub 漏出

| 対象 | 判定 | 静的結論 |
|---|---|---|
| `validate_admission_receipt` | **refuted（raw集合） / real（運用集合）** | plan は関数自体を変えないので JSON predicate は拡大しない。ただし issuer 不在で到達不能だった集合を self-issuer が到達可能にし、さらに receiptless 3走を足す。 |
| `_attest_measurement_cgroup` | **refuted（raw集合） / real（帰属欠落）** | predicate は不変だが、現在から同一 scope の lexical alias、任意 sleeper、任意 user cgroupを受理する。新 producer がその穴を実用化する。 |
| `_bounded_scope_cgroup` | **refuted（raw集合） / real（新用途）** | unit/env/property predicate は不変。だが certified peak 用だった機構を、未較正の user-slice-max measurement runへ転用する。 |
| test stub の production 漏出 | **refuted（現行）** | test は callbackを直接注入するが、production `main()` は引数無しで `run_fanout(config)` を呼ぶ。[test_mutation_fanout.py:251-278](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/orchestrator/tests/test_mutation_fanout.py:251)、[mutation_fanout.py:1838-1872](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:1838)。新 CLI flagや bypass引数を足さない限り漏れない。 |

**成果物影響:** raw schemaが不変でも、実際に生成・受理される report/receipt と、receipt無しで生成される request 台帳の集合は拡大する。

### 5. 「固定 HEAD identity」は HEAD 束縛ではない

**判定: real / stop**

file: [mutation_fanout.py:274-337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:274)、[mutation_fanout.py:31-42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:31)、[test_mutation_fanout.py:114-128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/orchestrator/tests/test_mutation_fanout.py:114)

`_resolved_commit` は caller 指定 objectを `rev-parse` するだけで、source repo の `HEAD` と比較しない。identity が pin するのも driver と wrapper の2 blobだけである。

したがって次が受理される。

- certification 後に HEAD が進んでも、2 fileのbytesが同じなら古い `--commit C` で本走できる。
- dirty `mutation_fanout_contract.py`、`login_headroom.py`、import先、同じpathのPython executableは受理される。
- driver worktree Aからsource worktree Bを指定する構成も、Aのdriver bytesとBのcommit blobが一致すれば受理される。
- Aで作った未変更 receiptをBのdriverから直接読む場合だけ、identityの絶対path差で拒否されるため、この狭い攻撃は **refuted**。ただし receiptには署名がなく、identity path自体をBへ書き換えれば再び通る。

特に `mutation_fanout_contract.py` は identity外なのに、split、canonical serializer、merge判定を実行する。certifyと最終runの間にここだけ変われば、receipt bindingが同じでもmerge受理意味を変えられる。

**成果物影響:** reportの `execution_identities` はCを示したまま、実際のplanning/mergeはdirtyまたは別HEADの意味になり、merge台帳の `result_rc`・mutation集合・request集合が変わりうる。

### 6. 親 brief の段1実測7項目はこの範囲までしか言えない

| # | 判定 | 反例条件・file:line | 成果物影響 |
|---|---|---|---|
| 1 producer不在 | **refuted（正規issuer不在） / real（排他推論）** | schema/fieldの全repo検索ではproduction issuerは見つからなかった。一方 identityは署名でなくcopy可能なobjectなので「手書きは構造的に不可能」は偽。[brief.md:17-24](</work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t851-fanout-exact-n/brief.md:17>) | 外部writer製receiptで採否・peak・本走可否が変わる。 |
| 2 exact-N 3回 | **real** | validatorはargv、rcの長さ、scalarしか見ない。plan自身も反証済み。[s2-plan.md:106-118](</work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t851-fanout-exact-n/artifacts/s2-plan.md:106>) | reportが3反復でも、request台帳は0回・1回・decoy実行になりうる。 |
| 3 scope生存 | **real** | `populated 1` は「何かいる」だけでmeasurement workerを意味しない。[mutation_fanout.py:412-418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout.py:412) | reportのscope欄だけ緑になり、peak帰属が変わる。 |
| 4 bounded scope生存 | **refuted（1回の狭い事実） / real（一般化）** | 不正receiptの1回は現行outer `run`のre-execを示すだけ。3本のmeasurement scope、holder保持、異なるcap、親とのhandshakeは未測定。[brief.md:35-38](</work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t851-fanout-exact-n/brief.md:35>) | certify reportが途中`stopped`になり、最終台帳は生成されない条件が残る。 |
| 5 投入枠 | **real** | 08:05の点値。3 scopeを生かす間にcharged memoryが蓄積する、他負荷が増える、1 runが4 GiB見積りを超える条件へ一般化できない。[brief.md:39-42](</work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t851-fanout-exact-n/brief.md:39>) | 同じ入力でもreserve拒否/OOMとなり、採否とreport stateが変わる。 |
| 6 flock | **real（過剰一般化）** | shard checkoutが異なればharness lockは通常別になるが、「真の競合は計算資源だけ」は偽。共有Git registry、admin lock、inode/quotaがあり、plan自身がregistry差でrc2とする。[mutation_harness.py:2090-2111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_harness.py:2090)、[s2-plan.md:188-198](</work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t851-fanout-exact-n/artifacts/s2-plan.md:188>) | reportの`unexpected_worktrees`と`result_rc`が変わり、ledgerが作られない。 |
| 7 pin 0件 | **real（閉包未成立）** | brief/handoffには検索command・全出力がなく、truncate有無は判定不能。私のuntruncated exact-path検索は12 fileを返した。さらにDW-O09はpath hit 0だけの結論を明示禁止し、role/key側検索とdurable manifest分類を要求する。[operations.md:54-64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/docs/dev-wave/operations.md:54) | 未発見pinがあれば実装commitでidentity/trust値が変わり、receipt・report・既存台帳がstaleになる。 |

なお brief の flock 根拠 `mutation_harness.py:430-434` は現在のlock実装位置ではない。これは単独では **nit** だが、「競合は計算資源だけ」という結論は上表のとおり real findingである。

### 7. planの負例は cgroup scalar と wrapper実行数を別々に撃ち、帰属を撃っていない

**判定: real / T-808 M02同型**

file: [s2-plan.md:121-135](</work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t851-fanout-exact-n/artifacts/s2-plan.md:121>)、[test_mutation_fanout.py:442-463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/orchestrator/tests/test_mutation_fanout.py:442)

planは次を別々に検査する。

- fake wrapperが `3N` 回呼ばれた。
- cgroupのpeak/max/populatedが正しい。
- exact duplicate cgroup pathを拒否する。

しかし「その `3N` wrapperが、そのcgroup内で走った」は検査しない。certifier側を次のように変異しても、列挙された負例は赤くならない。

```text
measurement["cgroup_path"] = decoy_holder_scope_alias[repetition]
```

wrapper call数、outer hash、rc、merge、request件数は保ち、attestationもdecoy scopeで通る。exact重複テストはlexical aliasで避けられる。既存 `test_admission_rejects_when_measurement_scope_is_not_live_kernel_evidence` もproduction attestorを呼ばず、明示的な `False` stubを渡すため、`_attest_measurement_cgroup` 自体を壊しても検出しない。

撃つべき実効層は以下である。

- schema: `tools/mutation_fanout.py:84-96` — worker PID/starttime、canonical cgroup、kernel peakを独立field化。
- sampling/launch: `tools/mutation_fanout.py:1588-1611` — child生存中に `/proc/<pid>/cgroup` と対象scopeを照合。
- attestation: `tools/mutation_fanout.py:401-418` — resolved pathで重複排除し、holder PID/starttimeと`cgroup.procs`を束縛。
- run validator: `tools/mutation_fanout.py:477-555` —上記witnessを最終runでも再検証。
- test: sibling scopeでwrapperを走らせ、logged scopeにはsleeperだけを置く負例をpublic経路へ通す。

helper抽出後は、private helperの条件だけでなくpublic `certify/run → validator` の呼出し辺を消す変異も必要である。これはF127型である。

**成果物影響:** 変異matrixが全件KILLEDでも、実際にはdecoy scope receiptが生存し、採否・report peak・台帳実行capが誤ったままになる。

### 8. 全層scopeから execution evidence と durable ledger binding が落ちている

**判定: real / 裁定パッケージ**

file: [s2-plan.md:29-34](</work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t851-fanout-exact-n/artifacts/s2-plan.md:29>)、[s2-plan.md:59-85](</work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t851-fanout-exact-n/artifacts/s2-plan.md:59>)、[mutation_fanout_contract.py:1476-1511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t851-fanout-exact-n/tools/mutation_fanout_contract.py:1476)

計測反復の `GROUP_ROOT` は毎回削除される。そこにあったmerge index、wrapper receipt、attempt、dispatch evidenceも失われ、残るのは同じcertifierが書いたmeasurement log・receipt・reportだけである。さらに最終merge indexには `admission_receipt_sha256`、`certified_peak_bytes`、measurement evidence hash、bounded cgroupのいずれも入らない。

plan内にある層はCLI・planning・sampling・既存attestation呼出し・最終run・driver testまでで、次がscope外である。

- `tools/mutation_worktree.py`: wrapper自身のcgroup membership witness。
- `tools/mutation_fanout_contract.py`: merge indexへのadmission/proof binding。
- merge-index consumerとcontract test。
- issuerとacceptorを同一toolにすることを認めるtrust裁定。
- receipt前measurement runをadmission例外にする資源境界の裁定。

裁定候補は二択である。

1. **推奨:** 現行briefのP4どおり「gateを緩めず構造的不成立」としてfan-out不採用。
2. scopeを広げ、schema v2、独立kernel-peak field、worker membership、各反復のledger/evidence耐久保存、最終merge indexへのreceipt hash束縛、bootstrap実行の明示的認可を一体で実装する。

**成果物影響:** 現planではcertification reportだけが「24 request・3反復」を主張し、durable mutation台帳は最終6 requestとmutation結果しか持たないため、certified採用判断からproof chainを再検証できない。