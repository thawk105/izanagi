## 所見

### 所見 1 — 既存 A-5 launcher は balanced 成果物を安定して生成できず、純増ゼロではない

**根拠 (file:line)**

- プランは launcher を充足済みとして実装しない: `s2-plan.md:83-94`。
- D1244 の要求は exact workload と mode を固定する launcher: `precheck-ruling.md:42-43`。
- 既存 submitter は workload を選べず、常に `write-heavy` と `balanced` の二本を同じ checkout から投入する: `tools/pegasus/submit_a5_second_boot_backoff_sweep.sh:92-101,169-190`。
- 各 job は共有する submodule repository に scratch worktree を登録する: `tools/pegasus/a5_second_boot_backoff_sweep.sh:363-376,467-484`。終了時には自分以外も対象になる `git worktree prune --expire now` を実行する: 同 `:123-169`。
- 実際に先に終わった write-heavy が balanced の登録を消し、balanced は 8 commit 後に rc=1 になった: `docs/failures.md:8536-8548`、`a5-measured.md:14-24`。そのため balanced の `result.json` は無い: `a5-measured.md:27-29`。

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

正式認可後に既存 submitter をそのまま呼ぶと二本が並行し、先に終わる job の prune が後続 job を壊す。balanced が後なら、全値を取得しても finalizer に到達せず、新 consumer は `producer-artifact-missing` になる。「将来正常終了した A-5 balanced root が入力になる」「launcher は純増ゼロ」という結論が崩れる。

**直し方の方向**

第 2 部品をゼロ扱いせず、balanced 単独かつ worktree ownership を分離した薄い T-1998 launcher を作る。既存 A-5 job/submitter自体を変更する案は A-5 の実行集合を変えるため、`scope 外・裁定パッケージ候補` とする。

既存 A-5 file を変更する場合の `git grep` consumer 閉包は次のとおり。

- job body: submitter `:43,175-177`、`test_a5_second_boot_job_contract.py:10-12,273-371`、`admission_registry.json:10-15`、`test_hooks.py:3034,3111-3115`、`test_official_perf_closure.py:81`、`docs/pegasus-runbook.md:492`。
- submitter: `test_a5_second_boot_job_contract.py:11,177-180,321-371`、`admission_registry.json:304-309`、`test_hooks.py:3083,3405-3410,3942-3943`、`docs/pegasus-runbook.md:542`。
- 特に既存契約テストは global prune 自体を正例として pin している: `test_a5_second_boot_job_contract.py:297-298`。これを消す修正は A-5 の受理集合を変える real change である。

### 所見 2 — consumer の identity 条件は実 field と arm 固有 identity を混同している

**根拠 (file:line)**

- プランは preregistered commit/gitlink/environment digest が「result、reservation、lock、WAL で一致」し、両 arm の source patch identity も一致すると要求する: `s2-plan.md:149-157`。
- `result.json` に environment digest は無い: `tools/pegasus/a5_second_boot_backoff_sweep.sh:770-794`。
- `reservation.json` にも environment digest は無く、repository commit と gitlink だけである: 同 `:434-449`。
- source receipt は `genome_sha256`、`src_token`、`source_bytes_sha256` を genome ごとに持つ: `orchestrator/campaign/source_digest.py:126-156,195-206`。
- 実 balanced WAL では baseline が `src_token=stock`、fixed-5 が `src_token=21def77...` であり、source bytes と genome SHA も異なる: `/work/1/SFC/tanab/a5-second-boot-runs/a5-second-boot-backoff-sweep-20260906T171922Z-31812-balanced/campaigns/backoff-sweep-silo-balanced-sweep-0dd37c05/runs/wal.jsonl:1,16`。

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

正常な future balanced rootを入力しても、environment digest を result/reservation に要求すれば必ず reject になる。逆に「source identity 一致」を `src_token` や source bytes の一致として実装すると、正しい baseline/fixed-5 が必ず `pair-identity-mismatch` になる。

**直し方の方向**

identity を次の別集合に分ける。

- 共通: repository commit、CCBench pin、environment contract、toolchain、tracked patch path/diff。
- arm 固有: canonical genome、genome SHA、`src_token`、`source_bytes_sha256`、variant ID、binary SHA。
- preregistration は arm 固有期待値を別々に渡す。

`test_pair_identity_drift_is_rejected` も、二 arm の source token を同値にした fixtureではなく、実 WAL と同じ非対称な正例から各 arm の期待値を変異させる必要がある: `s2-plan.md:232-238`。

### 所見 3 — `BACKOFF_NOINLINE=0` は計画した入力から証明できない

**根拠 (file:line)**

- プランは genome に key が無く configure override も無いことから effective default 0 を導く: `s2-plan.md:54-61,155,171`。
- A-5 producer の condition gate が検査するのは `BACKOFF_FIXED` だけで、`BACKOFF_NOINLINE` は scope に入っていない: `orchestrator/campaign/backoff_sweep.py:378-392`。
- build command は genome flags と `CCBENCH_TRACE` だけを明示する: `orchestrator/campaign/buildcache.py:1922-1937`。したがって genome に無い noinline は command に現れない。
- default 0 は patch の source にしかない: `patches/silo-backoff-fixed.patch:13-15`。
- persisted `SourceEvidence` は source digestを持つが、effective macro value は持たない: `orchestrator/campaign/source_digest.py:153-156,195-206`。

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

`CCBENCH_BACKOFF_NOINLINE` の default または供給 mapping が 1 の sourceでも、genome と configure command に明示的な `BACKOFF_NOINLINE=1` が無ければ、計画した拒否条件を通る。両 arm が同じ source digest族なら identity比較も通り、診断 throughput を headline 適格と誤判定する。

**直し方の方向**

「1 が記録されていない」を「0」と読まない。commit-bound CMake/source bytesから effective valueを再導出するか、preregistration に arm ごとの期待 source digestを固定する。どちらもできないなら、第 1 部品は schema 拡張不要と結論してはならない。

### 所見 4 — `result.json` と job 成功を同一視しており、failure receipt を見ていない

**根拠 (file:line)**

- failure receipt は `OUTPUT_ROOT + ".failure.json"` に書かれる: `tools/pegasus/a5_second_boot_backoff_sweep.sh:42-101`。
- finalizer は `result.json` を publishする: 同 `:593-817`。
- その後の EXIT cleanup が失敗すると failure receiptを書き、非ゼロ終了する: 同 `:172-186,819`。
- consumer の入力一覧には sibling failure receiptが無い: `s2-plan.md:125-143`。

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

finalizer が `result.json(status=complete)` を作った後、outer worktree cleanup が失敗する入力では、`result.json` と `<root>.failure.json` が同時に存在する。計画した consumer は前者だけを読み、PBS job が rc非ゼロでも `accepted` を返す。

現在の balanced failure receiptも同じ sibling 形式で、`returncode=1`、`last_terminal=commit` を持つ。現在は result欠損が偶然先に止めているだけで、一般の非ゼロ終了を閉じていない。

**直し方の方向**

T-1998 consumer の直接条件として sibling failure receipt の存在を reject にする。正例テストには「result completeとfailure receiptが共存する」ケースを入れる。

### 所見 5 — perf consumer と launcher の登録簿閉包が計画から漏れている

**根拠 (file:line)**

- プランは「記録済み commandを読むだけなので official perf file集合は増えない」とする: `s2-plan.md:260-287`。
- official perf registry は、perfを起動しない記録 consumerも明示的に登録する: `orchestrator/tests/test_official_perf_closure.py:44-92`。
- production 全 fileを走査し、perf名を使う条件分岐または tracked validator callを持つ新規 fileを拾う: 同 `:471-543`。
- 集合完全一致テストは未登録 fileを赤にする: 同 `:546-551,888-905`。
- 第 1 所見どおり launcherを追加するなら、Pegasus file集合、4-field registry、runbook投影も完全一致対象になる: `test_hooks.py:3032-3103,3926-3964`、`docs/pegasus-runbook.md:484-487`。

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

新 consumer が計画どおり `perf_configure_cmd`、`perf_bin_sha256`、trace-disabled条件を分岐で検査すると、`test_outer_perf_file_and_added_guard_inventory_is_exact` が `unreviewed: orchestrator/campaign/t1998_stock_inline_pair.py` で赤になる。安全な launcherを追加すれば、Pegasus registryとrunbook投影も赤になる。

**直し方の方向**

consumer を official recorded-perf consumerとして登録する。launcherを足す場合は `admission_registry.json`、`test_hooks.py`、runbook投影、launcher契約テストを同じ変更単位に含める。「既存テスト期待値は変更しない」という brief の絶対化は撤回が必要である。

追加で検索した語は次のとおり。

`perf_configure_cmd`、`perf_bin_sha256`、`admit_replay_evidence`、`BACKOFF_NOINLINE`、`a5_second_boot_backoff_sweep`、`submit_a5_second_boot_backoff_sweep`、`run_campaign`、`output/insights`、`rglob("*.py")`、`acceptance_duration_ledger`。

### 所見 6 — `admit_replay_evidence()` の追加呼出しは受理集合を狭めない

**根拠 (file:line)**

- `require_admitted_campaign(...CERTIFIED_ACCEPTANCE)` は全 persisted COMMIT を `admit_persisted_certified_commits()` に通す: `orchestrator/campaign/artifact_admission.py:1472-1513`。
- そこで verifier verdict、certified、anomaly zero、serialized receipt、lock、variant、terminal payloadを検証済みである: 同 `:733-834`。
- `admit_replay_evidence()` は同じ exact COMMIT receiptを同じ lock、variant、terminal payloadで再検証する: `orchestrator/verifier/commit_receipt.py:388-438`。
- プラン自身も invalid receipt は先の certified admission が TPS読取り前に拒否するとする: `s2-plan.md:244-246`。

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

receipt不正入力は最初の admissionで既に拒否されるため、二回目の呼出しが追加で拒否する入力はない。一方、viewから取り出した exact `ImmutableWalRecord` でなく再構成 recordを渡す実装では、campaignは適格なのに exact capability要件で偽 rejectになる: `commit_receipt.py:398-405`。

**直し方の方向**

replay capabilityを後続処理へ渡す要件がないなら二回目を削る。receipt IDは admitted COMMITの persisted payloadから返せる。追加呼出しを残すなら、受理条件ではなく capability投影目的だと限定する。

## 親 brief 自身への所見

- `artifact_admission.py:1538` は campaign pathから certified viewを発行する入口ではなく、既に発行済みの exact typeを確認する guardである。実入口は `artifact_admission.py:1459-1513`。brief の `:377,1538` というアンカー表記は役割がずれている: `brief.md:89`。
- `backoff_sweep_report.py:53-80` には不適格性の核心である argmaxもunstable欠落もない。argmaxは `:89`、unstableが届かない旨は `:141-147`。brief のアンカーは主張を支えていない: `brief.md:88`。
- `s1_expected_goldens.py:253-258` は `_BASE and SWEEP_US` という source-layout文字列を pinするだけで、`SWEEP_US` の値を直接 pinしていない。値の直接 pin は `test_s1_known_axes_freeze.py:546-549`。brief の「s1凍結 golden」という説明は過大: `brief.md:93`。
- finalizerアンカー `:769-790` は toolchain、perf preflight、counter statusを含まない。これらは `a5_second_boot_backoff_sweep.sh:791-794` にあるため、brief が後段で列挙する field範囲とアンカーがずれている: `brief.md:59-61,85`。
- 「薄い launcher は既に実在しうる」は call形状だけを実効性へ一般化している: `brief.md:30-33`。同じ経路が二 job fan-outとglobal pruneにより後続 jobを構造的に壊す事実を落としている。
- `P1-d` は一件の write-heavy resultから「consumer の入力 fieldは実環境で到達可能」と一般化している: `brief.md:54-62`。balancedには resultが無く、既存 launcherでは後続 jobが落ちるため、T-1998 の正例到達性は証明されていない。
- `P1-a` は「T-1998へ束縛する別の薄い層が要る」と書きながら launcherを純増ゼロとする: `brief.md:46-48`。consumerと将来のpreregistrationだけでは、exact balanced workloadを安全に起動する第 2 部品を代替していない。

## 純増の判定表

| プランの成果物 | 最も近い既存物 | 受理集合の差 | 純増あり/なし |
|---|---|---|---|
| evidence audit README | `precheck-ruling.md:37-45` | 既存は到達性監査を未完タスクとして残すだけ。新規物は各 evidence を result/reservation/lock/WALへ割り付け、再検証可能・不能を確定する。ただし現プランの noinline 結論は未成立 | あり |
| launcher「なし」 | `submit_a5_second_boot_backoff_sweep.sh` | 既存は二 workload同時 fan-outだけを受理し、後続 jobをglobal pruneで壊す。必要な集合は ownership分離された balanced exact-mode単独起動 | あり |
| `t1998_stock_inline_pair.py` | A-5 heredoc finalizer | 既存は8 commit/0 abort、固定 pair、toolchain/preflight一致を受理するが、preregistered identity、stable、trace/noinline、public admission、failure receiptを条件にしない。差はあるが現プランの identity条件は未定義 | あり |
| `test_t1998_stock_inline_pair.py` | `test_a5_second_boot_job_contract.py` | 既存は二 workload、driver一回、non-screening、8 commit、registryを固定するだけ。新規はfixed-5非置換、identity、diagnostic、trace、stability、sidecar bindingを固定する。ただし実 balanced正例とfailure receipt共存が漏れている | あり |

既存六件の受理集合は次のように分かれる。

- A-5 job body: exact pairを選ぶが全8点完走を要求し、certified view、unstable、noinlineを判定しない: `a5_second_boot_backoff_sweep.sh:649-749`。
- A-5 submitter: balanced単独ではなく二 workload fan-out: `submit_a5_second_boot_backoff_sweep.sh:92-101,169-190`。
- A-5契約テスト: shell形状と現行 registryを固定するだけ: `test_a5_second_boot_job_contract.py:177-213,273-371`。
- `backoff_sweep_report.py`: certified viewは読むがstatic argmaxを採り、unstableを受け取れない: `:58-89,141-158`。
- `backoff_extended_sweep_report.py`: certified、stable、trace-disabledは要求するが31点完全格子からargmax/shapeを判定し、headline適格を明示的に falseにする: `:45-51,85-120,151-159,462-518`。
- `backoff_counterfactual_analysis.py`: prereg hashとexact gridを強く固定するが、入力はdiagnostic traceの3 workload×2 thread×3 policy、最大12 seedであり、stock-inline二点比較ではない: `:15-47,68-89,300-348,557-621`。

## 総括

現プランはそのまま実装できない。blocking は、既存 launcher の構造的失敗、identity field集合の矛盾、noinline offの未証明、failure receipt無視、perf/Pegasus登録簿漏れの五点である。

第 2 部品は純増ゼロではない。第 3 部品には純増があるが、受理集合を field別・arm別に定義し直す必要がある。A-5既存受理集合を変更する修理は別裁定候補とし、T-1998 scope内では安全な薄い launcherと専用 consumerに閉じるべきである。

file変更、commit、test実走は行っていない。