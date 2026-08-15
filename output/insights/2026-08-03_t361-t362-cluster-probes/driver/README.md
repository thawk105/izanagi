# T-361 / T-362 login-side controller

`run_probes.py` は、この wave の 4 leg を login node から投入・監督・回収する唯一の入口である。
PBS script を直接 `qsub` してはならない。controller は安全判定を印字して済ませず、各 command の
argv、rc、stdout、stderr、marker、会計、job 出力、判定に使った連言を raw evidence と一緒に保存する。

## 実行前提と実行方法

次の 1 command だけを実行する。controller 自身が初回 4 request を直列投入し、初回 4 本の
`rbudgetcheck` 減少が 20 point 以下と機械確認できた場合に限り、無効だった leg だけを request 上限 6、
requested node-min 上限 40 の範囲で最大 2 本再試行する。成功済み leg は再投入しない。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 output/insights/2026-08-03_t361-t362-cluster-probes/driver/run_probes.py run
```

T-402 の flock leg だけを追加投入するときは、通常の `run` や signal 用 flag ではなく次を使う。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 output/insights/2026-08-03_t361-t362-cluster-probes/driver/run_probes.py run --flock-leg-only
```

`--flock-leg-only` は `t361-flock` だけを対象にする one-shot であり、初回 4 request の point gate、
request 上限 6、requested node-min 上限 40 を迂回しない。予約は qsub 前に wave-state の
`flock_one_shot_submission_count` へ永続化され、失敗・中断・`dangerous:null` でも消費は戻らない。
後続 session と通常 `run` も 2 本目の flock を投入しない。`--signal-legs-only` は T-362 の
mitigation / split-warning 専用で用途が異なり、両 flag は同時指定できない。

## 中断 session の回収

controller が request 投入後に異常終了し、`_controller/sessions/` と未完の wave state が残った場合だけ、
次を login node で先に実行する。`resolve` 自身は `qsub` / `qdel` を呼ばず、新しい request を投入しない。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 output/insights/2026-08-03_t361-t362-cluster-probes/driver/run_probes.py resolve
```

`resolve` は singleton lock を取って未解決 session と attempt を列挙し、全 submitted attempt について
現在の `qstat -J -f` が rc=0 で request 不在を示すことを共通の前提にする。そのうえで終端は次の 3 経路の
論理和で実証し、成立した経路を `terminal-proof.json` の `termination_evidence_paths` に残す。

1. `resolve` が取得した `qwait` raw が leg 固有の期待 rc と raw 条件を満たす。
2. `resolve` が実際に取得した `racctjob -I <request>` または `racctreq -I <request>` raw の少なくとも一方が、
   exact request ID と Started / Ended / Elapse の条件を満たす。取得失敗や不完全な会計は証拠にしない。
3. scheduler dir に収集済みの `.e` の NQSV 会計 block が exact `Request ID` と `Ended Request Time` を持ち、
   同時に上記の現在 `qstat` 不在が成立する。`.e` 単独では終端証拠にしない。

**1 attempt でも `qstat` 不在と上記論理和を実証できなければ、どの attempt も解決済みにせず
fail-closed で止まる。** request がまだ見える場合、権限・一時エラー、3 経路すべての欠測も同じ扱いであり、
走行中かもしれない job を閉じない。

全 attempt の終端を実証した後だけ、投入時 preflight・qsub raw・compute marker・probe / observer raw・
job output・会計を通常 `run` と同じ validity conjunction で再検査する。T-361 の Execution Host は現在の
`qstat -J -f` raw、そこで取得不能なら hash 照合済みの保存済み `qstat -J -f` raw だけを使う。host の
一対一照合を含む連言を確定できない attempt は `admissible:false`、`dangerous:null` の無効 attempt として
解決し、後付けの安全判定へ倒さない。T-362 も observer rc=0 と全 acceptance condition の論理積を保ち、
未観測 signal は `UNKNOWN` のまま扱う。

解決は既存 wave-state の request 行を完了化するだけで、予約済み request 数と requested node-min の累積を
減算・削除しない。最初の admissible attempt だけを authoritative に保つため、成功済み leg はその後の
`run` で再投入されない。`resolve` が rc=0 で session を回収した後、必要なら通常の `run` command を再実行する。

controller は `qsub` の直前に毎回、次を fail-closed で検査して `controller/preflight.json` に残す。

- `PATH`、`qsub` / `qstat` / `qdel` / `qwait` / `racctjob` / `racctreq` / `rbudgetcheck` / `git`
  の実在と実行可能 path
- driver 全 12 file の SHA-256 と size
- Git top-level、source HEAD、driver 全 file が `git ls-files` の追跡対象であること
- `tools/pegasus/dispatch_compute.py` の interpreter 候補・選択 loop・PATH 行と、各 PBS / shell
  の該当 byte の一致
- fresh な `/work` / `/home` attempt root、その 0700 mode、symlink 不在、read-after-write 一致
- leg が参照する全 `T361_*` / `T362_*` が `qsub -v` に含まれること
- request / subjob ごとの `-o` / `-e` template を含む完全な `qsub` argv

さらに `/work/.../probe-runs/_controller/controller.lock` を non-blocking `flock` し、別 controller の
同時起動を拒否する。session 外の `_controller/wave-state.json` は request の予約時点で完全 argv、
request 数、累積 requested node-min を atomic に永続化し、完了後に admissible と最初の authoritative
attempt を同じ台帳へ固定する。controller 再起動後もこの台帳から 6 / 40 と attempt ordinal を復元し、
既に authoritative な leg は再投入しない。前回の unresolved session、未完予約、または qsub rc=0 の
終端未証明 attempt が 1 件でもあれば、新規投入を始めない。

`run_probes.py` は投入時に次の root を新規作成し、既存 root を再利用しない。

```text
/work/1/SFC/tanab/izanagi-jobs/3a7f810a/probe-runs/<leg>/<attempt-id>/
/home/SFC/tanab/.izanagi-t361/probe-runs/<leg>/<attempt-id>/
```

実際の `/home` prefix は実行 uid の passwd entry から得る。`$HOME` は信用しない。`attempt-id` は UTC
時刻、leg、attempt ordinal、暗号乱数からなる。

## 直列 transaction

各 attempt は次の順を変えない。

1. fresh な `/work` / `/home` root を作る。
2. preflight と `rbudgetcheck` before を raw 保存する。
3. request 数と累積 requested node-min を**投入前**に予約し、6 / 40 を超える argv を拒否する。
4. 完全な `qsub -v ... -o ... -e ...` argv を保存して投入し、request ID と request 台帳を永続化する。
5. `qwait` を直ちに起動する。T-362 は login-side observer も直ちに起動・監督する。
6. `qstat -J -f` を bounded retry で採取する。権限系エラーは全体を恒久停止し、一時系・未知の非 0 は
   当該 attempt を無効にする。QUE 3600 秒後の再確認でも RUN でなければ controller だけが bounded
   `qdel` を実行し receipt を残す。RUN 初観測から requested walltime + 300 秒を execution deadline
   とする。
7. compute marker の schema・request ID・mode / nonce・host を検査する。T-361 は raw
    `qstat -J -f` の対象 `Request ID:` block 2 件から得た `Batch Job Number` → `Execution Host`
    写像と 2 marker の PBS job number / host を一対一照合し、
   probe の provisional `flock-result.json` と合流した `controller/t361-finalized-result.json` を生成する。
   host 照合または probe 自己検査が不成立なら final 側も `valid_for_safety_conclusion:false` / 
   `dangerous:null` のままにする。T-362 は `t362-signal-marker/v2` と controller の attempt-id を
   `T362_RUN_NONCE` / `T362_ATTEMPT_ID` の同値として producer・observer・controller の全層で照合する。
8. `qwait`、`racctjob -I`、`racctreq -I` を回収する。会計は exact request ID と Started / Ended /
   Elapse の連言を要求する。T-362 は qwait rc=9 と raw の ELAPSE limit 表記も要求するが、これを
   signal 種別の証拠には使わない。
9. NQSV job の `.o` / `.e` を `.stdout.raw` / `.stderr.raw` へ改名し、元名、hash、size、改名後 path
   を `job-output-manifest.json` に保存する。強制終了時に file が戻らない可能性は欠測として残す。
10. `/work` / `/home` tree を repo の
    `output/insights/2026-08-03_t361-t362-cluster-probes/evidence/<session-id>/` へ byte 同一で copy する。
    全 file に `git check-ignore`、`git add`、`git ls-files --error-unmatch` を通した後に限り、元の
    attempt root を撤去する。qwait と Ended 会計の連言で終端を証明できない attempt は、追跡確認後でも
    外部 root を保持し、同じ永続台帳に terminal-unproven と記録して次回投入も拒否する。controller は
    commit しない。

## 判定表

controller の `admissible` は「その観測を読んでよい」という有効性であり、安全判定ではない。
安全・危険は staged raw observation から次表で復元する。

| 対象 | raw 観測と自己検査 | 扱い |
|---|---|---|
| T-361 | authority・全自己検査・marker・会計・Execution Host 照合が通り、`localflock` がなく、controller が raw 各 6 件を全 `BLOCKED` と再導出 | `BLOCKED_EXPECTED`; exact host pair / kernel / effective mount に限って排他を観測 |
| T-361 | 上記有効性が通り、contender が `ACQUIRED` | `ACQUIRED_SILENT_FAIL_OPEN`; **危険** |
| T-361 | 上記有効性が通り、いずれかの mount に `localflock` がある | 観測無効へ畳まず `dangerous:true`; **危険** |
| T-361 | `ENOSYS` / `EOPNOTSUPP` 等を raw errno で観測 | 明示的非対応。fail-open と同一視せず、別の排他機構が必要 |
| T-361 | control / mount / backing object / marker / host / accounting / cleanup のどれか不成立 | `INVALID_CONTROL` / `INFRA_ERROR`; `dangerous` は `null` 相当で安全結論を出さない |
| T-362 | observer rc=0 かつ walltime 会計、非 RUN 終端、全必須層、parse error なし、TERM→約5秒 timeout→KILL→wait→restore→byte 検証の順が成立 | 有効。受信 signal と継続 heartbeat の raw 時刻から grace を復元する |
| T-362 | ready 未確認、権限 / active / 会計 / parse / cleanup error、grandchild 早期停止 | 無効。成功 rc や安全そうな値へ畳まない |
| T-362 | signal 記録なし | `UNKNOWN`。mitigation leg で配送経路が実証されるまで `SIGKILL` と断定しない |
| T-362 | mitigation だけで SIGTERM と十分な grace を観測 | 構成依存の緩和候補。十分性の閾値は **約 10 秒 + 復元所要** |

controller の `attempt-result.json` は `validity_conjunction` の全値が literal `true` の場合だけ
`admissible: true` にする。attempt envelope の `dangerous` は常に `null` だが、T-361 の
`t361-finalized-result.json` は observation と外部 root 終端、host 束縛、自己検査を単一の
authority receipt で束縛した場合だけ final な boolean を持つ。安全側の `false` にはさらに
`localflock` 不在と raw 各 6 件の全 `BLOCKED` を要求する。無効時は必ず
`dangerous:null` である。authoritative attempt は wave 永続台帳上の各 leg の**最初の admissible
attempt**だけで、session を跨いでも後続の都合のよい結果へ差し替えない。全 attempt は evidence に残る。

## 出力

正常終了時は次が残る。

```text
output/insights/2026-08-03_t361-t362-cluster-probes/evidence/<session-id>/
  attempts/<leg>/<attempt-id>/
    work/                       # compute marker、raw events、observer、scheduler/accounting raw
    home/                       # /home 側 lock / inventory / 残存物の byte copy
    source-tree-inventory.json
    tracking-receipt.json
  controller/
    request-ledger.jsonl        # request ID、leg、attempt、node-min、累積、完全 argv、時刻
    attempts.jsonl
    controller/raw/             # wave 前後の rbudgetcheck 等
    session-summary.json
    tracking-receipt.json
```

session evidence とは別に `/work/.../probe-runs/_controller/wave-state.json` が wave 完了後も残り、
全 session の request 予約、累積 node-min、完了状態、first-admissible 選択を保持する。各 session の
`controller/wave-state-snapshot.json` は、その session 終了時点の byte snapshot である。

正常時の外部残存物は次のとおり。

- `/work/.../probe-runs/<leg>/<attempt-id>/`: なし。追跡確認後に controller が撤去する。
- `/home/.../.izanagi-t361/probe-runs/<leg>/<attempt-id>/`: なし。同上。
- `/work/.../probe-runs/_controller/sessions/<session-id>/`: なし。session evidence の追跡確認後に撤去する。
- `/work/.../probe-runs/_controller/controller.lock`: 空の singleton lock inode が残る。attempt evidence
  ではなく、次回 controller が同じ inode を再利用する。
- `/work/.../probe-runs/_controller/wave-state.json`: session 間の上限と authoritative 選択を固定する
  永続台帳。wave を新規にやり直すという別のユーザー裁定なしに削除しない。
- repo: evidence file が index に stage 済みで残る。commit / push は人間が行う。

異常停止時は fail-closed のため、次が残りうる。

- fresh attempt の `/work` root 全体。bootstrap stderr、未改名 `.o` / `.e`、marker、raw command、
  accounting、inventory の一部を含みうる。
- 対応する `/home` root。control / cross / long-hold lock、inventory、read-write probe が残りうる。
- `_controller/sessions/<session-id>/` の request ledger と root 作成記録。
- repo evidence の partial copy。`git check-ignore` / `git ls-files` が一件でも不成立なら外部 root は
  故意に残る。

これらは固有 attempt-id のため後続 attempt から再利用されない。

## cleanup

正常 transaction の cleanup は上記 step 10 で完結し、人手で `rm` しない。異常停止時は、まず
`_controller/sessions/<session-id>/request-ledger.jsonl` の request ID と保存済み qwait / qstat /
accounting raw から全 request の非 RUN 終端を確認する。active、権限エラー、会計未確認の request が
一つでもあれば削除せずユーザー裁定へ返す。

非 RUN 終端を確認できた残骸だけについて、次の順を守る。

1. `.o` / `.e` があれば元名・hash・size を manifest に記録して `.stdout.raw` / `.stderr.raw` へ改名する。
2. `/work` と `/home` の directory scan を採り、全 regular file の path / SHA-256 / size と空 directory
   を inventory に固定する。symlink や特殊 file があれば停止する。
3. fresh な repo evidence path へ copy し、copy 後 inventory が byte 一致することを確認する。
4. **全 file ごとに** `git check-ignore` が非 ignored、`git add` が成功、
   `git ls-files --error-unmatch` が成功したことを receipt に残す。
5. ここまで全て成立して初めて、manifest に記録された exact attempt root だけを撤去する。base root、glob、
   未解決変数を削除対象にしない。

この異常時手順で evidence 集合や request 終端を一意に確定できない場合、値を補完したり成功扱いにせず、
残骸を保持してユーザー裁定へ返す。
