# [T-2486] 遠隔検査の ssh session は rank 側と別の cgroup object に入る — per-job の cgroup 境界はどちらの側にも無い

- 日付: 2026-09-09
- request: `986762.nqsv` (`-b 3`、queue `gen_S`、elapstim 00:10:00、Elapse 52 秒)
- 割当: `bnode004(4) bnode015(15) bnode007(7)` (head = `bnode004`)
- 統治する裁定: D1810 (認証の正しさ検査を単一 multi-node request 内の ssh で分割する)
- 先行: `output/insights/2026-09-09_t2457-a6-fanout-live/README.md` §8-2 が
  「rank 終了後の ssh session が job の cgroup / cpuset に属するかは測っていない」と主張の上限を
  明記していた。**本稿はその 1 点だけを埋める。**

A-6 認証は 1 つの NQSV request を `-b 5` で取り、job 番号 0 の rank (head) だけが本体を走らせる。
job 番号が 0 でない rank は 1 行の診断を出して即 `exit 0` する (D1842)。head はその後、割当ノードの
兄弟へ**素の ssh** で入り、直列性検査の worker を走らせる
(`orchestrator/campaign/pipeline.py` の `_default_verify_fanout_launcher`)。
測ったのは、その ssh session が rank process と同じ資源文脈にいるのかどうかである。

## 1. 答え — 3 対とも別の cgroup object

同一ホスト・同一 `boot_id`・同一 namespace の下で比べた。

| ホスト | rank 側の cgroup | `st_dev:st_ino` | ssh 側の cgroup | `st_dev:st_ino` | 判定 |
|---|---|---|---|---|---|
| `bnode004` (head, rank 生存中) | `/system.slice/nqs-lchd.service` | `29:4565` | `/user.slice/user-31609.slice/session-101130.scope` | `29:375447` | 別 object |
| `bnode015` (rank 1, **終了済み**) | `/system.slice/nqs-jsv.service` | `29:4565` | `/user.slice/user-31609.slice/session-78829.scope` | `29:326039` | 別 object |
| `bnode007` (rank 2, 生存中) | `/system.slice/nqs-jsv.service` | `29:4565` | `/user.slice/user-31609.slice/session-26809.scope` | `29:116166` | 別 object |

各対で `cgroup` / `mnt` / `pid` / `user` の namespace が rank 側と ssh 側で一致している
(`cgroup:[4026531835]`、`mnt:[4026531841]`、`pid:[4026531836]`、`user:[4026531837]`)。
したがってこれは path 文字列だけの比較ではなく、**同一ホスト・同一 boot 内の
`st_dev:st_ino` 非同一**である。

**別ホスト間で inode を比べてはいけない。** 3 ノードの service cgroup はいずれも `ino=4565` だが、
`boot_id` が違うので別物である。段 3 の敵対相談がこの罠を事前に指摘し、実データで現れた。

## 2. rank の終了は、この差の必要条件ではなかった

生死は bytes で立証した。

| ssh 観測 | 対象 shell | `present` | `same_starttime` | `comm` |
|---|---|---|---|---|
| `ssh-rank1.after-exit` | rank 1 の shell (pid 1635668) | **false** | false | — |
| `ssh-rank2.alive` | rank 2 の shell (pid 2772750) | true | true | `user_script` |
| `ssh-head.loopback` | head の shell (pid 3801574) | true | true | `user_script` |

**rank が生きているノードへの ssh でも、head 自身への折り返しでも、同じく別 cgroup object だった。**
よって**本 request では、rank の終了は観測された membership 差の必要条件ではない。**

production の worker (`verify_fanout_worker`) についても同じになるだろうという見込みは持てるが、
それは**非 PTY で同型に起動していることからの推測**である。本 probe が実際に起動したのは
`observe.py` であって production の worker ではない。

## 3. per-job の cgroup 境界は、rank 側にも無い

| | rank 側 (`nqs-jsv.service`) | ssh 側 (`session-N.scope`) |
|---|---|---|
| `cpuset.cpus.effective` | `0-47` | 自階層は `ABSENT`、祖先 `user.slice` で `0-47` |
| `sched_getaffinity` | 48 個 (`0`〜`47`) | 48 個 (`0`〜`47`) |
| `Cpus_allowed_list` | `0-47` | `0-47` |
| `/sys/devices/system/cpu/online` | `0-47` | `0-47` |
| `cgroup.controllers` | `cpuset cpu io memory pids` | `memory pids` |
| `memory.max` | `123480309760` (≈115.0 GiB) | `max` (leaf から `user.slice` まで) |
| `pids.max` | `152831` | leaf は `max`、`user-31609.slice` で `336230` |

**rank が入っているのは per-job cgroup ではなく、そのノードの NQSV service を job 間で共有する
cgroup である。** 両側とも cpuset は全 48 CPU で、task affinity も 48 個である。

**言えることの範囲を狭く書く。** 観測できたのは
**per-job の cgroup membership・cpuset の絞り込み・task affinity の絞り込みが、どちらの側にも
無かった**ことである。`cpu.max` / `cpu.weight` のような CPU controller の制限値は本 probe が
採取していないので、「CPU 資源境界が一切無い」とは言えない。
また scheduler 側には per-job の表示が実在する — `qstat -f` は
`(Per-Job) CPU Number = Max: 48`、`(Per-Job) Memory Size = Max: UNLIMITED` を返す。
cgroup の境界と scheduler の会計上の境界は別の層である。

**memory と pids の上限文脈は非対称である。** rank 側は共有 service cgroup の
`memory.max = 123480309760` の下にあるが、ssh 側は leaf から `user.slice` まで有限値を持たない。
`pids.max` は逆に ssh 側の `user-31609.slice` が `336230`、rank 側の service が `152831` である。
root (`/sys/fs/cgroup`) の `memory.max` と `pids.max` はどちらの側でも `ABSENT` で、`max` ではない。

## 4. 既存実測との関係

`docs/pegasus-runbook.md` §7.0 に 2026-08-13 の実測がある — 「計算ノードには per-job cgroup も
cgroup delegation も無く (`/proc/self/cgroup` が `0::/system.slice/nqs-jsv.service` の 1 行だけで
あることを 2 ノードで確認)」。

- **非 head rank の membership はこれを再現した。** 新発見ではない。
- **delegation は本 probe では再測定していない。** `cgroup.subtree_control`・owner/mode・書込み可否を
  採っていないので、delegation 不在まで「再現した」とは書けない。
- **新しく分かったのは次の 3 点。**
  1. ssh 側は systemd の login session scope (`/user.slice/user-<uid>.slice/session-<N>.scope`) に入る。
  2. memory と pids の上限文脈が rank 側と ssh 側で非対称である。
  3. head (job 番号 0) は `nqs-lchd.service`、非 head rank は `nqs-jsv.service` と別の service cgroup に入る。

## 5. 採取した PBS 変数は ssh session に継承されない

3 本の ssh すべてで、production と同じ `env PBS_JOBID=` を被せる**前**の値
(`PRE_PBS_JOBID`) が `ABSENT` だった。`PBS_JSVNO` と `PBS_NODEFILE` も `ABSENT` である。
**採取した PBS 変数は 1 つも渡っていない** (採取したのは `observe.py` が列挙する 8 変数だけで、
環境全体を調べたわけではない)。

`pipeline.py` の launcher が `env PBS_JOBID=<値>` を明示的に載せ、`verify_fanout_worker` が
無ければ `ValueError` で止まるのは、この事実に対する正しい設計である。
`SSH_TTY = ABSENT`、`stdin_isatty = false` で、production と同じ非 PTY 経路であることも確かめた。

## 6. 何が変わり、何が変わらないか (規律 7)

**変わらないもの:**

- **17 分 37 秒は変わらない。** あれは request `986046.nqsv` の実測 elapsed である。本 probe は
  **別 request・別時刻・別ノード**であり、先行 attempt の観測ではない。所要を無効化しない。
- **A-6 の正しさ結論も変わらない。** D1810 決定 3 は遠隔結果の権威を head 生成の 32 byte secret に
  よる HMAC に置いており、資源保証には置いていない。決定 7 により欠落・不一致・ssh 非 0 は
  `verify-remote-unavailable` (indeterminate) で pass に化けない。
  **規律 2 は本 wave で一切緩めていない。correctness gate は 1 行も変えていない。**
- **兄弟側 worker の競合検査もそのままである。** worker は自分で競合 ccbench を探し、見つければ
  `verify-competing-tenant` で reject する (`orchestrator/campaign/verify_fanout_worker.py` の
  `competing_bench_pids` 経路)。これはその時点の観測であって、scheduler の資源所有の証明ではない
  — だが元から所有の証明を名乗ってはいない。

**弱まるもの:**

- 「兄弟側の検査は割当の資源保証の下で走った」という解釈は、**cgroup の層では支持されない**。
  ただし同じ理由で **head 側の計測も同じ立場にある** — head の rank も per-job cgroup を持たない。
  ssh 側が rank 側と違うのは membership object と、memory / pids の上限文脈である。

## 7. 観測の完全性

- **記録された rc はすべて 0。** `*.client` 3 本の ssh rc、`rank-*.commands` の 73 件、
  `qstat-f.rc` と `qstat-list.rc` のいずれも 0 で、非 0 は 1 件も無い。
- **予定した観測点 7 つはすべて採れた。** JSON 中の `ABSENT` は 178 件あるが、これは
  「v2 上に v1-only の file が無い」「root に当該 file が無い」「非 ssh 観測に
  `liveness_check` が無い」「継承されなかった環境変数」などの**期待どおりの不在**である。
  `UNREADABLE` と `UNRESOLVED` は 0 件。
- **記録に残らなかったものが 3 つある。** 中核結論は壊さないが、欠落として明記する。
  1. **ssh の remote stdout を捨てている** (`/dev/null` へ)。client 記録には stderr だけが残る。
  2. **`qstat` の採取時刻を記録していない。** stdout / stderr / rc は全文残っているが時刻が無い。
  3. **投入前の `qstat -Q` が durable な記録に残っていない。** 親は投入前にログインノードで
     キューが `ENA ACT` であることを確認したが、その出力を job dir へ保存しなかった。

## 8. 主張の上限 (明記する)

1. **1 request・1 回きり・3 ノードである。** A-6 の 5 ノード実走そのものの観測ではない。
2. **ノード専有はこの probe では確かめられない。** `gen_S` は `Exclusive submit = OFF` であり
   専有はスケジューラの保証ではない (`docs/pegasus-runbook.md` §1)。同居 job の有無は測っていない。
3. **これは実行場所分類 (admission registry の class) の実測ではない。** runbook §7.0 は
   「AI セッション・子エージェント・自動化は実行場所分類の実測を自分で行わない」と定めるが、
   本 probe が測るのは scheduler の資源文脈であって実行体の memory 使用量ではない。
   **得られた値を `tools/pegasus/admission_registry.json` の class 根拠に使ってはならない。**
4. **遠隔検査の受理条件は変えていない。総 timeout も入れていない** ([T-2487] は別項)。
5. `nqs-lchd.service` と `nqs-jsv.service` の役割の違いは NQSV の内部であり、本 probe は
   **cgroup 名を観測しただけ**でその意味を確かめていない。
6. **CPU controller の制限値 (`cpu.max` / `cpu.weight`) と cgroup delegation は採取していない。**

## 9. 裁定パッケージ候補 (本 wave では実装しない)

1. **遠隔検査の受理条件に資源文脈の同値性を含めるか。** 観測した 3 経路はいずれも exact な
   membership 同値性を満たさなかった。これを受理条件にするかは裁定待ちである
   (先行 insight §9 と同じ問い)。
2. **遠隔実行へ walltime より短い総 timeout を入れるか** ([T-2487])。
3. **遠隔 worker が memory 上限の外にいることを扱うか。** rank 側は共有 service cgroup の
   115 GiB 上限の下、ssh 側は有限値を持たない。本 wave は測っただけで対処を提案しない。

## 10. 再現条件

| 項目 | 値 |
|---|---|
| 投入 | `qsub -A SFC -q gen_S -b 3 -N t2486cg -l elapstim_req=00:10:00 -o <probe>/job.stdout -e <probe>/job.stderr <probe>/probe.sh` |
| 投入元 | `pegasus02` のログインノード (repo の worktree からではなく wave job dir から) |
| probe | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2486-ssh-cgroup-equivalence/probe-cgroup/` (repo 外の使い捨て。`observe.py` と `probe.sh` の 2 本) |
| 生記録 | 同 `out/` — 観測 JSON 7 本、`*.client` 3 本、`rank-*.commands` 3 本、`rank-*.self` 3 本、`qstat-f.stdout`、`qstat-list.stdout` |
| 時刻 | Created 08:28:33 / Started 08:41:26 / Ended 08:42:14 JST |
| 段 3 相談・段 6 レビュー・裁定 | 同 wave job dir の `consult-a.md`、`s6-review.md`、`s4-ruling.md`、`s6-ruling.md` |
