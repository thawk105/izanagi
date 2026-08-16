## 総括

現時点では投入不可。正本 runbook は Pegasus の kernel 5.15 で `memory.peak` が無いとし、現行 admission 検証はそれを必須にしている。  
3 certify scope を生存させたまま本走する案は、予約 1 件では aggregate memory を拘束できず、OOM kill 時に qsub・worktree・観測記録が孤児化する。  
worktree 差分は path 集合だけで、他 wave の同時変更・同一 path の再束縛を検出できない。  
4 セットは少なくとも 24 request であり、1 回の成功から将来の既定採用までは推論できない。

### 1. `memory.peak` が実機条件と衝突する

- 自己判定: **real**
- 根拠: `tools/mutation_fanout.py:407-418` は `memory.peak` の存在と `max(samples)` との完全一致を要求する。`docs/pegasus-runbook.md:381-404` は、この kernel には `memory.peak` が無いと明記する。段 2 plan の kernel peak checkpoint 案も同じ前提に依存する。
- 成果物影響: `admission.json` を発行できず、`certified_peak_bytes`・certified 選択・本走台帳は未成立になる。

### 2. 3 scope 保持に対して予約が 1 件しかない

- 自己判定: **real**
- 根拠: plan は 3 scope を最終 validation まで保持する一方、測定開始前の予約は `MAX_LOCAL_BUDGET_BYTES` 1 件としている。`login_headroom.py:881-913` の予約は 1 record / 1 scope binding であり、`mutation_worktree.py` には `reserve` / `login_headroom` がない（`rg -n 'reserve|login_headroom|reservation' tools/mutation_worktree.py` は該当なし）。`memory.oom.group=1` は `tools/mutation_fanout.py:1328-1337` で設定される。
- 成果物影響: 3 holder + 最終 run の実メモリを予約台帳が過小計上し、OOM・admission reject・certification report 欠落を起こす。

### 3. OOM kill / SIGKILL で qsub と worktree が孤児化する

- 自己判定: **real**
- 根拠: bounded scope の再 exec は `tools/mutation_fanout.py:1853-1856`。driver が捕捉するのは INT/TERM/HUP 系だけで、SIGKILL/OOM は捕捉不能。`dispatch_compute.py:1458-1462` も SIGKILL を処理しない。親が死ぬと `stop()`、`inspect_or_cancel_owned_requests()`、`_teardown()` は呼ばれない。
- 成果物影響: `driver-report.json` は `running` のまま、6 計測項目の終端値・最終 registry・request 対応が失われ、remote qsub は queue/fair-share を消費し続ける。

### 4. registry 差分は所有権の証明になっていない

- 自己判定: **real**
- 根拠: `_worktree_snapshot()` は worktree root path だけを返す (`tools/mutation_fanout.py:340-352`)。最終判定は `Counter(final_roots) == Counter(initial_roots)` (`:1700-1705`) で、porcelain の HEAD・admin identity は比較しない。別 wave が同じ path を remove/add しても、また実行中に add/remove して最終状態を戻しても検出できない。wrapper の共有木検査 (`mutation_worktree.py:368-389`) も worktree registry 自体を見ていない。
- 成果物影響: `unexpected_worktrees=[]` / `missing_initial_worktrees=[]` が偽に成立し、Git admin burst と最終残渣値が false-green になる。

### 5. 計画中の `GROUP_ROOT` 再帰削除は他 wave を消し得る

- 自己判定: **real（段 2 plan の追加撤去に対して）**
- 根拠: plan は owner marker 後に `shutil.rmtree(GROUP_ROOT)` を行う (`s2-plan.md:74-85`)。一方 `mutation_worktree.py:280-299` の scratch 検査は「registered worktree 外」しか要求せず、他 wave が既存の `GROUP_ROOT` を scratch/output/lock の置場に使うことを防がない。owner marker は root 自身の所有しか示さず、子孫の所有を示さない。
- 成果物影響: 他 wave の lock・dispatch evidence・ledger・resume artifact を削除し、その wave の受入証拠と台帳を破壊する。現行 `run` は root を消さないため、この危険は計画の cleanup 追加で発生する。

### 6. request 全件対応の保証範囲を超えている

- 自己判定: **real**
- 根拠: 完了した `merge_group` には、attempt 完全集合、request ID 一意性、receipt、evidence inventory、総数を検査する強い保証がある (`mutation_fanout_contract.py:716-797`, `:1331-1405`, `:1470-1474`)。しかし `inspect_or_cancel_owned_requests()` は sidecar/evidence に現れた claim だけを走査し、欠落した request ID を発見・回収しない (`mutation_fanout.py:1151-1175`)。
- さらに owner は同一 Unix user、job name は nonce の先頭 10 文字だけ (`dispatch_compute.py:433-436`)、wave ID・source・group token は qstat identity に入っていない。request ID の再利用、claim/receipt の誤束縛、job-name prefix 衝突があれば、他 wave の `izdw-*` を自分のものと誤認し、逆方向にも自分の job を qdel し得る。通常の異なる request ID は照合で防げるが、wave 所有権の保証ではない。
- 成果物影響: `merge-index.requests` は成功 merge に限り完全だが、`remote_jobs` は orphan request を含まない可能性があり、「全 request 対応済み」を certification report に記録できない。

### 7. cancel 経路は cleanup ではない

- 自己判定: **real**
- 根拠: child 非 terminal / registry 異常時、通常は `cancel=False` (`mutation_fanout.py:1710-1718`)。merge reject 時も `cancel=False` (`:1740-1752`)。`cancel=True` でも QUE/HLD、owner、job name が一致する request だけで、RUN は qdel しない (`:1247-1264`; runbook `:1239-1242`)。`cancel_group()` は別 CLI で自動呼出しされない。
- 成果物影響: queue に残った request が他 wave を待たせ、report は `qdel-requested` ではなく report-only / unknown になり、台帳の終了集合が閉じない。

### 8. brief の flock 根拠は refuted

- 自己判定: **refuted（「repo path を鍵にするので衝突しない」という説明）**
- 根拠: `tools/mutation_harness.py:430-434` は repo HEAD/cleanliness の処理で flock 鍵ではない。実際の wrapper lock は `mutation_worktree.py:177-209` の絶対 `--out` に対する `<out>.lock`。通常、別 worktree・別 out なら衝突しないが、同じ resolved `--out`、同じ scratch root、または共有 Git admin の add/remove は別途衝突する。`git worktree` registry 操作を wave 間で直列化する lock はない。
- 成果物影響: 同じ out なら shard が `INFRA_RC` で停止し、共有 admin race なら Git admin burst・registry report の値が不帰属になる。

### 9. 4 セットの queue / fair-share / lease 影響

- 自己判定: **real（待たせる経路）／drop の確率は nit**
- 根拠: A/B・N=2 は 1 セット 6 request、4 セットで 24 request (`s2-plan.md:118`)。各 request は `gen_S` の 1 node・既定 walltime 1 時間 (`dispatch_compute.py:26-29`, `:457-461`)。queue の submit limit は大きくても、runbook は大量投入の fair-share 効果を未計測としている (`docs/pegasus-runbook.md:1107-1115`)。したがって他 wave の受入・変異走行を待たせる経路は real。qsub が必ず落ちるとは静的には言えない。
- 現行 fanout は acceptance lease を直接操作しないので、lease の直接破壊は refuted。ただし lease を certify 開始前に claim すると、queue wait を含む全系列の間 lease を保持し、他 wave を head-of-line block する。TTL 2,400 秒と lease の SIGKILL 限界もある (`docs/pegasus-runbook.md:891-897`, `:1029-1046`)。
- 成果物影響: `queue_wait_s` / fair-share の一系列値は取得できても、将来の既定採用を支持する因果証拠にはならない。lease を先取りした場合は他 wave の acceptance receipt が遅延・失効する。

### 10. 6 項目の観測保全と「1 回で決める」前提

- 自己判定: **real**
- 根拠: OOM/親死亡では次が失われる。

| 失敗 | 失われる値 |
|---|---|
| 親 OOM/SIGKILL | cgroup 3反復の終端、Git admin burst の終端、`df -Pi` 終端 |
| child/dispatch 異常 | request 対応、fair-share receipt、最終 ledger |
| teardown 中断 | 最終 `git worktree list`、container/admin の残渣判定 |
| queue/qstat timeout | request の terminal state と qdel 結果 |

投入順序は、repo 外の durable report に preflight 値を fsync → 各 qsub receipt → child terminal ledger/evidence → request inventory → worktree porcelain/df の cleanup 後値 → 3 measurement log の hash/attestation → 最後に admission receipt → 本走 → 本走後の全値、でなければならない。親と同じ killable scope 内だけで保全する計画では足りず、外部 reaper が必要。
- 1 回で決められる保守的な式は、次の exact-run 判定だけ。

`GO_exact = M ∧ Q ∧ R ∧ W ∧ X ∧ O`

`M`=3 measurement が kernel 検証済み、`Q`=24/24 request が完全対応、`R`=全 scope の aggregate memory が 14 GiB 内、`W`=full porcelain registry が不変、`X`=6項目が保存済み、`O`=OOM/timeout/外部 registry 変更なし。

これは当該走行の GO/NO-GO であり、queue 混雑・他 wave 負荷・node 差・file cache 揺れのない将来を証明しない。全条件成立でも「今後の既定採用」は undecidable。失敗時は stock/variant の選択ではなく `inconclusive` にするべき。
- 成果物影響: 部分成功を certified 選択へ流せず、certification report は `inconclusive`、mutation 台帳は未成立として閉じる。

## 投入直前の中止条件

各行を独立した 1 command として確認し、複合 shell の判定器にしない。

| command | 1 値として必要な結果 |
|---|---|
| `python3.10 -m orchestrator.campaign.queue_state` | `ENA=ENA, STS=ACT`。unknown は停止。rc=0 だけでは不十分 (`queue_state.py:251-270`) |
| `qstat -u <user>` | t851 所有の非 terminal request 数 `0`。wave identity が識別不能なら停止 |
| `rbudgetcheck` | fair-share/budget が利用可能 |
| `check_quota` | 予定する work/inode 使用量を収容可能 |
| `df -Pi -- /work/1/SFC/tanab/dev-wave-jobs` | inode 空きが事前閾値以上 |
| `git -C <repo> rev-parse --verify HEAD` | 実装 commit `C` と完全一致 |
| `git -C <repo> status --porcelain=v1 --untracked-files=all --ignore-submodules=none` | 空 |
| `git -C <repo> worktree list --porcelain` | 保存済み preflight porcelain と byte-identical |
| `stat -- <GROUP_ROOT>` | `ENOENT`。存在・symlink は停止 |
| `python3.10 tools/wave_land_window.py status --lease-dir /work/1/SFC/tanab/dev-wave-jobs/land-lease --wave t851-fanout-exact-n --json` | certify 中に lease を取らないなら `state=free` |
| `/work/SFC/tanab/scripts/memwatch.sh` | memory 値が既定 ceiling 内。headroom / reservation の一値 CLI がない場合は `unknown` 扱いで停止 |

`memory.peak` の実在確認、3 holder + 最終 run の aggregate 予約、foreign wave の registry 変更を 1 command 1 値で確認する既存 leaf はありません。これは nit ではなく、本走 admission の機械的な欠落です。