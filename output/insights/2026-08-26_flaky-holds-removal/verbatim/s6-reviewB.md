## 総括

- 判定は **NO-GO**。must-fix は 3 件。
- 最大 risk は、ignore 規則配下の tracked file 418 件を理由に、現実装が全 snapshot を決定的に失敗させること。
- hold#1 は偽 clock 化が未実装で、3 個の `Event.wait(5)` を含む実時間依存が残る。
- hold#3 の因果順序修理は成立するが、内側 xdist subprocess には起動失敗と無期限待ちの残余 risk がある。
- `output/task-runs/` の shard 間競合は裁定どおり scope 外だが、hold#2 の偽赤経路として残る。
- pytest、焦点走、受入全走は実行していない。以下は静的読解と read-only Git 照会による。

## 1. subprocess コストと並列下の意味

実 repository では literal 規則が 7 個一致する。`git_ignored_output_prefixes()` の process 数は次のとおり。

- `git rev-parse`: 1
- `git config`: 1
- batch `git check-ignore`: 1
- prefix ごとの `git ls-files --cached`: 7
- 最後の `git ls-files -o -i`: 1
- 合計: **11 process**

`git_ignored_output_ancestor_directories()` は `rev-parse`、`config`、`check-ignore` を繰り返すため **3 process**。したがって `_t080_output_snapshot()` 1 回は **14 process**、floor の `_real_output_snapshot()` は **11 process**を直列に起動する。

直接の call expression は全 repository で次の 20 箫所。

- `test_s8b_floor_campaign.py`: prefix 4、ancestor 0
- `test_s8b_oracle_driver.py`: prefix 7、ancestor 4
- `test_real_repo_serialization.py`: prefix 3、ancestor 2
- 合計: prefix **14 箇所**、ancestor **6 箇所**

各 snapshot callerと parameterized node を展開すると、受入全走では prefix helper が約70回、ancestor helperが24回実行される。このうち実 repository 対象は66回と22回で、成功経路なら `66 * 11 + 22 * 3 = 792` process。temp repository の contractを含めると helperだけで約821〜825 process、contract setupの13 Git processも含めると約834〜838 processになる。旧 helper相当は約54 processなので、構造上の増分は約770 processである。

48並列はこの総数を48倍にはしないが、各 workerが14個の短命 processを直列起動し、それが複数 workerと複数 shardから重なる。Git index読取り、process table、metadata I/Oの競合が同時に増える。実測していないため、5分 ceilingへの秒単位の寄与は確定できないが、現状は ceiling内である根拠を持たない。

cacheは存在しない。このため before/afterを跨ぐ stale cacheは無く、状態依存の再導入は起きていない。cacheするなら lifetimeを単一 snapshot 呼出し内に限定する必要がある。`.gitignore`、info exclude、global excludes、index、wildcard配下の実在状態のいずれかを跨いで再利用すると、before/afterで異なる答えを隠す。

問題なし: 各 Git subprocess は読取り専用で、通常の受入が indexを変更しない限りGit lock競合は作らない。

## 2. 撤去 3 node が受入で落ちる経路

### `test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary`

現実装は snapshot 開始時点で決定的に落ちる。`.gitignore:24` の `output/env/pegasus/silo_ladder_rung1/job-staging/` 配下に tracked file が418件あり、`output_snapshot_ignores.py:208-216` がこれを AssertionError にする。親実測の赤と一致する。

`git ls-files output/` は合計12784件。並列・実行時に問題となる主な namespace は次のとおり。

| namespace | tracked数 | ignore | 実行中の変化 |
|---|---:|---|---|
| `output/task-runs/` | 24 | されない | shard runnerが run directory、`task.json`、`events.jsonl`、pilot marker、reportを作成・追記 |
| `output/insights/` | 9362 | されない | 別の dev-waveや証拠生成processが書けばsnapshotに見える |
| `output/env/pegasus/silo_ladder_rung1/job-staging/` | 418 | 規則上はignore | production scriptのruntime root。tracked fileなので正しい修理後も可視にする必要がある |
| `output/pegasus-dispatch/` | 0 | literal ignore | shard dispatch writerの変更は除外対象 |
| `output/runs/` | 0 | literal ignore | launcher artifactは除外対象 |
| `output/campaign-locks/` | 0 | literal ignore | runtime lockは除外対象 |

指定された既知3領域以外では、`output/task-runs/reports` 以外の task-run本体が明確な shard writerである。`tools/run_tests.py:1095-1097` はpytest起動前にrunを開始し、終了時に `events.jsonl` を追記する。別 shardの開始・終了が当該nodeのbefore/after窓へ入れば赤になる。

418件の job-staging は runtime writerを持つが、受入テスト自身が実rootのscriptを起動する経路は見つからなかった。`output/campaigns/` など他のtracked subtreeについても、該当nodeの窓と重なる受入 shard writerは静的検索では見つからなかった。

さらに48並列で Git process生成が `EAGAIN`、file descriptor不足、Git errorになれば、helperはfail-closedで当該nodeを赤にする。

### `test_control_lock_allows_peer_after_pending_hold_is_durably_released`

`poll_interval_s=1` により10秒の決定的な床は約2秒へ縮むが、実 clockと実 `time.sleep` は残っている。段4訂正が要求した threadごとの `_Clock()` と `sleep=clock.sleep` は未実装である。

残る実時間上界は次のとおり。

- `release_qsub.wait(5)`、`qsub_entered.wait(5)`、`second_acquire_entered.wait(5)` の3箇所。
- 48並列でfirstまたはsecond threadのscheduleが5秒を超えると、性質ではなくlatencyで赤になる。
- `second_acquire_entered` 待ちが失敗すると `release_qsub` が設定されず、first thread側の5秒待ちも失敗しうる。
- `first.join(60)` と `second.join(60)` は直列なので、deadlock時には最大約120秒を消費する。
- 同じ修理対象の隣接testは `join(10)` のままで、両方をwatchdogと呼びながら値が一致しない。

control root、artifact root、intent rootはいずれも `tmp_path` 配下なので、別 shardのcontrol lockとの直接競合はない。

### `test_receipt_memo_real_xdist_order_has_no_worker_payer`

既修理の worker hookは `hookwrapper=True, tryfirst=True` かつ `yield` 前記録であり、workerのcollection完了通知より先に記録する因果を持つ。新しいpluggy controlもdecorator削除とpost-yield移動を赤にする。この元flaky経路は静的には解消している。

残る経路は内側 subprocess の実行基盤である。

- 外側worker内でpytest controllerを起動し、さらに `-n 1` workerを起動する。
- process数、memory、PID、file descriptor不足では `subprocess.run()` が例外または非0 rcになり赤になる。
- timeoutが無いため、内側controllerまたはworkerが停止すると外側workerも無期限に待つ。
- 1 full suite当たり本nodeは1回だけで、48倍起動されるわけではない。複数の重複suite/shardが同時に本nodeを含む場合は、その数だけcontrollerとworkerが増える。
- temporary directoryとevent logは `/tmp` 配下で一意なので、repository snapshotとは競合しない。

## 3. 検査どうしの相互作用

新設controlによる repository 汚染は見つからなかった。

- `runs-visible`、`visible-transient-parent`、contract用Git repositoryはすべて各testの `tmp_path` 配下。
- real serialization版の `runs-visible` は `finally` で削除する。oracle版とfloor版はfixture teardownへ委ねるが、repository外である。
- A6の一時作成後削除controlはworker固有の `tmp_path` 内であり、別workerが `ROOT/output` をsnapshotする窓へ入らない。
- pluggy negative controlはmemory内だけで動作する。
- control-lock testのfileとthreadも `tmp_path` 内に閉じる。
- `runs-visible` の出現は今回のcontrolだけで、他のinventory、除外規則、node IDとの衝突は見つからなかった。
- prefix比較は `relative == prefix` または `prefix + "/"` なので、`runs` が `runs-visible` を誤って隠すこともない。

問題なし: A6と `runs-visible` の新設は、同じsuiteの別workerへ共有filesystem副作用を持たない。

## 4. 冪等性と再走

通常終了なら、新設test自身はrepositoryへ何も残さない。helperは読取り専用で、各controlは `tmp_path` または `TemporaryDirectory` 配下である。同じtreeを続けて走らせた場合、test自身の前提は同じになる。

ただし現在のtracked-descendant拒否は毎回同じrepository状態を見て失敗するため、現状の2回目も1回目と同じ赤になる。

外側runnerは別問題である。

- automatic task-runはpytest child起動前にrepository内へ作られ、終了後にeventを追記する。
- 同一runner自身の作成は原則before snapshotより前だが、別 shardの開始・終了はsnapshot窓へ入る。
- kill時は `task.json` の無い incomplete-startを意図的に保存する。次走ではgit-visibleな残骸となり、ledger validationや並行snapshotへ影響しうる。
- report生成中のSIGKILLは `.tmp` を残しうる。
- inner xdist testにはtimeoutやprocess-group cleanupが無いため、外側workerのkill後に内側pytestが残る可能性がある。残るfileは `/tmp` 内で次走とpath衝突しないが、PIDとmemoryを消費し続けうる。

問題なし: gracefulなtest failureでは `TemporaryDirectory` とfixture teardownが働き、新設controlのrepository残骸は生じない。

## 5. 段 3 luna 所見の追跡

1. **wildcard規則の実在依存**: 残っている。`git ls-files` による実在後展開を維持しており、裁定でscope外とされた残余 risk。
2. **exclude sourceとlinked worktree**: 解消した。root `.gitignore`、`git rev-parse --git-path info/exclude`、`git config --get core.excludesFile` を明示的に読む。
3. **`git check-ignore` の3分岐**: 解消した。rc 0、rc 1、その他を分離し、NUL出力と入力候補の部分集合も検査する。
4. **tracked descendantの隠蔽**: 別の形になった。隠蔽はfail-closedへ変わったが、実repositoryに418件ある正当な状態を検査不能にした。裁定訂正後の実装漏れ。
5. **`output/task-runs/` のF136型**: 残っている。writer移設は裁定でscope外。hold#2の偽赤経路として明示的に受容された残余 risk。
6. **台帳closureと再発分類**: 残っている。registryは空になった一方、`docs/failures.md:5099` と `:13317` は登録状態で止まり、F136/F480 closure、F480族定義の訂正、worklogへの6段分類手順が差分に無い。これはscope外裁定ではなく実装漏れ。

## 所見一覧

- **所見 1**: tracked descendantをfail-closedにしたため、実repositoryの全snapshot callerが決定的に失敗する
  - 場所: `orchestrator/tests/output_snapshot_ignores.py:208`; `.gitignore:24`
  - 分類: must-fix
  - なぜ問題か: ignore規則配下にtracked fileが418件ある正当なrepository状態を、line 212-216が無条件に拒否する。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: hold#2を含むsnapshot node群が受理集合から外れ、受入receiptが発行されない。
  - 確度: high — tracked数はread-only Git照会と親実測の両方で418件と一致する。

- **所見 2**: hold#1の偽clock化が未実装で、3個の5秒deadlineが48並列依存を残す
  - 場所: `orchestrator/tests/test_pegasus_dispatch_compute.py:5459`; `orchestrator/tests/test_pegasus_dispatch_compute.py:5472`; `orchestrator/tests/test_pegasus_dispatch_compute.py:5486`
  - 分類: must-fix
  - なぜ問題か: pollを1秒へ短縮しただけで実clockと実sleepを使い、thread scheduleを5秒以内とするassertも残る。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: 高負荷時だけnodeが赤になり、hold撤去後の受理集合とfailure reportが走行負荷で変わる。
  - 確度: medium — 実時間依存は静的に確定するが、注入後の48並列実測は行っていない。

- **所見 3**: registry撤去に対するF136/F480 closureと再発分類手順が記録されていない
  - 場所: `orchestrator/tests/flaky_test_holds.py:200`; `docs/failures.md:5099`; `docs/failures.md:13317`
  - 分類: must-fix
  - なぜ問題か: executable registryは空なのに、正本台帳はnodeを登録した状態で止まり、F480の真因訂正も反映されない。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: 受入では再導入済みなのに台帳はactive holdと読め、再発時の分類が一意に決まらない。
  - 確度: high — current diffの変更fileは7実装fileだけで、該当docsの差分が存在しない。

- **所見 4**: snapshotごとに最大14個のGit processを起動し、全走ではhelperだけで約821〜825 processになる
  - 場所: `orchestrator/tests/output_snapshot_ignores.py:76`; `orchestrator/tests/output_snapshot_ignores.py:144`; `orchestrator/tests/output_snapshot_ignores.py:208`; `orchestrator/tests/output_snapshot_ignores.py:255`
  - 分類: backlog
  - なぜ問題か: source読取りとcheck-ignoreを二重実行し、tracked確認も7 prefix別に起動するため、48並列と複数shardでspawnとmetadata I/Oが集中する。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: suiteが5分 ceilingへ近づき、超過時は受入receiptが発行されない。
  - 確度: medium — process数は静的に数えられるが、秒単位の追加時間は実測していない。

- **所見 5**: `output/task-runs/` の非report部分を含むshard writer競合が残る
  - 場所: `tools/run_tests.py:1064`; `tools/task_runs/generation.py:1131`; `tools/task_runs/ledger.py:911`; `orchestrator/tests/conftest.py:673`
  - 分類: backlog
  - なぜ問題か: snapshot nodeはreal-repo lock inventory外で、別shardがrun directoryやeventを同じGit-visible rootへ書く。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: 正当な台帳記録がhold#2を偽赤にし、受理集合とfailure reportがshard重複時刻で変わる。
  - 確度: high — 親実測とwriter実装が同じ経路を示す。裁定により本waveではscope外。

- **所見 6**: 内側の実xdist subprocessにtimeoutとkill後cleanupが無い
  - 場所: `orchestrator/tests/test_real_repo_serialization.py:3932`
  - 分類: backlog
  - なぜ問題か: 外側48並列中にPID不足や内側worker停止が起きると、即時errorまたは無期限待ちになり、kill後に子processが残りうる。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: 当該nodeが赤または全走がtimeoutし、受入receiptが欠落する。
  - 確度: medium — timeout不在は静的に確定するが、資源枯渇は今回実測していない。

- **所見 7**: hold#1のduration ledgerが修理前の10秒のままである
  - 場所: `orchestrator/tests/acceptance_duration_ledger.json:7663`; `orchestrator/tests/test_pegasus_dispatch_compute.py:5472`
  - 分類: nit
  - なぜ問題か: poll短縮または偽clock化後の実時間とschedulerの見積りが一致せず、48-worker初期配置が不正確になる。
  - もし放置したら成果物 (受入の受理集合・台帳・レポート) の何がどう変わるか: 受理集合自体は変わらないが、load balanceと全走時間reportが実態からずれる。
  - 確度: high — ledger値10.0と現行注入値の不一致は静的に確認できる。