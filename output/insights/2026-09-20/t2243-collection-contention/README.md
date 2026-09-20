# [T-2243] 受入 collection の 48 並列を計算ノードで分解した — bytecode 温なら 48 並列でも 18.4 秒 (Lustre の取り分 4.7 秒)、冷なら 84.6 秒。受入の `pre` 61 秒との差 約 43 秒は異条件の差であり内訳は未測定 (2026-09-20)

wave `dev-wave-t2243-collection-diag`。依頼の逐語は `verbatim/T-2243-origin.md`。
一言でいうと「受入 1 shard の 48 worker が同時に払う全 collection を、計算ノード 1 job・同一 checkout・同一 node で条件を割って測った」診断で、**改善の実装は 1 行もしていない** (D1936 項 35: 効果を先に測る)。

## 結論 (最初に読む)

計算ノード bnode008 (48 core、HT 無効)、request `13599.nqsv`、checkout `25334c9b7` (投入直前の local main)、単独 (他 user の process 0、自分の残骸 0)、30 cell、Elapse 744 秒。数値は `aggregate.md` / `aggregate.json` (機械集計) と `raw/<cell>/` (生記録) にある。

| 腕 (置き場・bytecode) | N=1 の wall | N=48 の wall | N=48 / N=1 (wall) | N=48 / N=1 (CPU 時間) | 事前登録の判定 |
|---|---|---|---|---|---|
| L: Lustre・温 | 9.8 秒 | **18.4 秒** | 1.87 | 1.02 (一定) | `wait-dominant` |
| C: node-local (NVMe)・温 | 8.8 秒 | **13.7 秒** | 1.56 | 0.91 | `wait-dominant` |
| R: Lustre・冷側 (wave 木に pyc 4 個だけ存在、その有効性は未確認、書かない) | 50.1 秒 | **84.6 秒** | 1.69 | 1.49 | `cpu-time-inflation` |

(wall は process median、前半 (a)・後半 (b) 2 走の平均。R/L/C の対応する cell の process median の前後差は 0.5 秒未満 (R48 の cohort wall は 0.51 秒差、X48 は 7.0 秒差)。参照腕 L48 の job 前後差は −0.5 秒。)

1. **bytecode cache が温なら、48 process の同時 collection は Lustre 上でも 18.4 秒で終わる。** 単独 9.8 秒からの伸びは 8.6 秒で、CPU 時間は伸びない (待ちが増えるだけ)。node-local に source と pyc を置くと 13.7 秒 (伸び 4.9 秒)。**Lustre の取り分 (配置効果 Δplace) は N=48 で 4.7 秒、N=1 で 1.0 秒。** source と pyc を node-local に置いても残る待ち 4.9 秒は帰属していない (§4.4)。
2. **冷 (pyc なし) は桁が違う。** 単独でも 50.1 秒 (温の 5.1 倍)、48 並列で 84.6 秒。CPU 時間が 55.5 → 82.6 秒に伸び (1.49 倍)、IPC は 2.11 → 1.41、instruction あたり cache-miss は 4.1 倍。**Δbc(48) = R48 − L48 = 66.1 秒、Δbc(1) = 40.2 秒。** 事前登録の仮説 H (差 10〜15 秒) の閾値からは外れ、機械判定は `H-inconclusive`。独立 process の冷/温対照としては「冷は温より大幅に遅い」という向きが出たが、受入の双峰 (§2b) の原因を確定したものではない (§4.3)。
3. **受入の `pre` (session 開始 → collection 終了) は現行 61 秒 (2 回目以降の受入)。本 job の温 48 並列 collection は 18.4 秒。差 約 43 秒は checkout・plugin・xdist・cache 配置・計時区間がすべて異なる観測値の引き算であり、受入の内訳でも削減可能量でもない (未測定)。** 本 job は T-2617 §3.3 の帰属 (「残る約 38 秒は 48 重の並列実行そのもの」) を検証する同条件対照ではない。言えるのは「本 job の条件では、温の 48 並列 collection そのものは 38 秒も伸びない」までである (§6)。
4. **短縮策の効果量の見込み (§5、実装しない):** (a) fresh worktree の初回受入で冷 collection を避ける策は、受入で観測された群間差 (約 8〜18 秒、観測された関連は初回受入の shard に限られる) からの**仮説**で、正味利得・適用範囲・適用条件は未確定。(b) node-local staging は利得 4.7 秒/shard に対し今回の構築手順の費用 (clone 13.4 + rsync 1.0 + warm-up 46.6 秒) が上回り、1 回利用なら負。(c) 約 43 秒の差の内訳は本 wave では測っていない (次の一手として起票)。

## 1. 何を測ったか

- 投入: `python3 tools/pegasus/dispatch_compute.py --task generic --walltime 01:00:00 --queue-wait-timeout 5400 --overall-grace 5400 -- bash <wave dir>/t2243_collection_contention_probe.sh` (launcher の逐語 `verbatim/run-probe-1.sh.txt`、dispatch log `verbatim/run-probe-1.log`)。21:38:09 投入、即 RUN、22:01:56 終了 (JST)。cwd は dispatcher が wave 木 (`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2243-collection-diag`) に固定。
- 各 cell: `python3 -m pytest orchestrator/tests --collect-only -q -p no:cacheprovider` を N 本同時に起動し全員の終了を待つ。process ごとに `/usr/bin/time -f "%e %U %S %M %F %R %w %c"` (wall・user・sys・maxrss・major/minor fault・voluntary/involuntary context switch) と `perf stat -e cycles,instructions,cache-misses` (絶対 path の 5.15.0-135 版、計算ノードで動作確認済み) を付け、cell 前後に Lustre client stats (`/proc/fs/lustre/llite/*/stats`、`mdc/*/md_stats`)、`/proc/loadavg`、MemAvailable、cell 中盤に CPU MHz を採る。stdout/stderr は node-local (`/scr`) に書き、job 末尾で wave 専用 dir へ回収した。
- 共通環境: `PYTHONDONTWRITEBYTECODE=1`、`IZANAGI_TASK_RUN_AUTO_RECORD=0`、`PYTEST_ADDOPTS` / `PYTEST_XDIST_TESTRUNUID` / `IZANAGI_TASK_RUN_SIDECAR` unset、`TMPDIR` は node-local、`LC_ALL=C` (Python は UTF-8 mode で stdout utf-8)。shard plugin (`-p tools.acceptance_shards`) は載せない (費用 +1.74 CPU 秒は T-2617 §3.2 が既測、二重に数えない)。
- 腕:
  - **R** (現行 checkout・冷): cwd = wave 木、pyc prefix 未設定。wave 木の `orchestrator` / `tools` 配下の pyc は job 開始時 4 個 (2 dir)、終了時も 4 個 (`raw/pycache-wave-before.txt` / `-after.txt`)。この 4 個は job 開始時刻 21:49:23 に計算ノード側の dispatcher (`_job_run`、PBS 環境で書込み禁止なし) が import した `orchestrator/scheduler_nqsv`、`orchestrator/campaign/{__init__,mutation_attempt_marker,site_policy}` のものと推定する (時刻と module 集合から。書込みは追跡していない)。対照として warm-L 後の別 prefix には pyc が 1,528 個ある。**wave 木の 4 個が collection で実際に読まれ有効だったかは確認しておらず、「完全な冷」とは書かない。** probe の機械判定は `R_cache=warm` (0 でないため) と記録している。
  - **L** (Lustre・温): cwd = wave 木、`PYTHONPYCACHEPREFIX=<wave dir>/job-out/pycache-L` (Lustre 上)。warm-L (書込み許可、1 走 53.0 秒) で prefix を満たした後に測る。prefix には pyc 1,528 個、うち pytest assertion-rewrite 462 個 (`raw/pycache-L-count.txt`)。pytest 9.1.1 の rewrite cache は `sys.pycache_prefix` に従う (login で `get_cache_dir` を確認)。
  - **C** (node-local・温): `/scr/tanab/t2243-<pid>/repo` へ `git clone --depth 1 --no-local file://<wave 木>` (13.4 秒) + `rsync -a --exclude .git <wave 木>/external/` (1.0 秒)、1,090 MB。HEAD は wave 木と一致。warm-C (46.6 秒) の nodeid 集合 (26,152 行) と rc (0) が warm-L と完全一致 (`raw/setcheck.txt`、diff 0 行)。cwd = 複製、prefix も node-local。
  - **X** (xdist 較正): cwd = wave 木、prefix L、`-n 48 -k zzz_no_such_test_zzz`。事前登録の期待 rc=5 を満たさず **rc=4** (§3.3)。
- 順序 (30 走): R1-a, R48-a, warm-L, (clone/rsync), warm-C, ref-L48-pre, [L1 C1 L4 C4 L12 C12 L24 C24 L48 C48], X48-a, [C48 L48 C24 L24 C12 L12 C4 L4 C1 L1], X48-b, R48-b, R1-b, ref-L48-post。前半は N 昇順で L→C、後半は N 降順で C→L。
- 全 cell の rc は 0 (X48 の 2 走だけ 4)。

## 2. 単独性と環境の記録

`raw/env.txt` の逐語 (要点): bnode008、kernel 5.15.0-173-generic、nproc 48、Mem 124 GiB (available 118)、`/scr` は `/dev/md0` xfs 5.4 TB、`/work` は Lustre、Python 3.10.12、pytest 9.1.1、`perf=/usr/lib/linux-tools/5.15.0-135-generic/perf`、`lustre_stats=readable`、HEAD `25334c9b7bf5a36da20f285a80d4b9e1b847abd7`、`git status --porcelain` 0 行、`others=0` (自 user 以外の非 system user の process 0)、`stale_pytest=0`。各 cell の直前にも同じ単独性検査を行い、全 cell で `others=0`、`stale_pytest=0` (`raw/<cell>/cell.txt`)。cpuset は `0-47`。

job 前の loadavg (1 分) は 0.89、job 中は自分の走行で上がり、記録された最大は 91.90 (C24-b の直後、`raw/C24-b/loadavg-after.txt`)。

## 2b. brief 前の前提実測 — 現行 `pre` の双峰は走行元 worktree の受入回数と login collection の完了時刻で分かれる (login の read-only 観測、2026-09-20 夜。原因は仮説で、反例 1 件を含む)

一次資料は repo 外の受入成果物 `/work/1/SFC/tanab/.izanagi-acceptance-shards/<digest>/` (直近 23 session、69 shard = 初回 33 + 2 回目以降 36、読み取り script は `verbatim/read_pre_v2.py.txt` (親が書いた read-only の整形、repo 外に置いた)、出力は `verbatim/pre-recent-v2.txt`)。`pre` = `collection_finished_epoch_s − junit の timestamp`。shard-0 の `request.json` の `repo_root` から走行元 worktree を取り、同じ木の受入を時系列で数えた (ordinal)。

- **ordinal ≥ 2 (その木で 2 回目以降の受入) の 36 shard は `pre` が 58.9〜62.8 秒、例外は 9ef5b469 shard-1 の 66.2 秒の 1 件。**
- **68.8〜78.8 秒の 14 shard はすべて ordinal = 1 (fresh worktree の初回受入) の session にあり、初回群 33 shard の残り 19 は 60.5〜61.9 秒。** 同一 session 内では最初に開始した shard 群が高く、遅れて開始した shard は 61 秒台になる例が多い (d4eafc90: shard-1 19:17:54 → 76.1、38 秒後の shard-2 19:18:32 → 61.0、16 分後の shard-0 → 61.2; b2b19375: shard-2 17:05:39 → 78.8、6 分後の shard-1 / 7 分後の shard-0 → 61.2 / 61.4)。
- 受入は login 側の独立 collection (`tools/run_tests.py` の `_collect_login_universe`、D711 gate 3) を compute shard と**並行に**走らせる。その環境は `os.environ.copy()` ベースで `PYTHONDONTWRITEBYTECODE` を付けないため、login の collection が走行元 worktree の `orchestrator/tests/__pycache__` に pyc を書くと読める。計算ノードの worker は dispatch 既定の `PYTHONDONTWRITEBYTECODE=1` で書かずに読むだけ (code 読み。書込み時刻を直接記録したのではない)。
- `login-collection.log` の完了時刻 (mtime、`verbatim/login-collection-mtimes.txt`、観測 22:24) と shard 開始時刻の関係: 完了が開始より**後**の shard は高い (988edc99: 完了 20:28:28、3 shard 開始 20:27:52 → 74.3 / 75.1 / 73.9; caa3bb01: 完了 19:03:49、開始 19:03:22 → 70.2 / 70.7 / 70.9; e337587c: 完了 19:23:21、shard-0/2 開始 19:22:53 → 72.2 / 73.6; b2b19375 shard-2: 完了 17:06:13、開始 17:05:39 → 78.8)、完了が開始より**前**の shard は 61 秒台 (d4eafc90 shard-2: 完了 19:18:25、開始 19:18:32 → 61.0; 04d049fc shard-1: 完了 19:39:20、開始 19:55:55 → 61.5)。**反例が 1 件ある:** 6b5e8983 shard-0 は完了 20:48:15 の約 5.6 分後 (20:53:51) に開始して 68.8 秒。**境界例が 1 件ある:** edc9df7c shard-0 は完了の 3 秒前 (19:53:49) に開始して 61.9 秒 (開始時点で一部の pyc が利用可能だった可能性はあるが、その時点の pyc 件数・書込み進捗・読み出し有効性は未測定)。
- login で `find` した現物 (`verbatim/pycache-counts-wave-worktrees.txt`、観測 22:25、14 木): `orchestrator/tests/__pycache__` の pyc が 394〜396 個 (うち pytest assertion-rewrite 366〜368 個、source は 394 file) の木が 5 本、0 個の木が 5 本、1〜15 個の木が 4 本。どの木が受入を通ったかは観測 file に無く、親が wave 名から「394 個以上の木は受入済み、0 個の木は受入前 (本 wave の木を含む)」と推定した (保存した session 出力で `repo_root` を照合できるのは t2700 だけで、他の木の根拠は保存していない。全称ではない)。21:1x に見たときは 394〜397 / 366〜369 だった (その値は保存していない)。

**仮説 H (段 4 で登録した文言): 現行 `pre` の双峰 (61 / 70〜76) は shard 開始時点の bytecode cache の有無で決まり、差は約 10〜15 秒。** (登録時は 27 shard の値で書いた。69 shard では初回群の高い値は 68.8〜78.8 で群間差は約 8〜18 秒。) 本 job の R/L 対照 (§3・§4) は独立 process の冷/温差 66 秒を出したが、受入の双峰の原因を確定したものではない (§4.3)。ordinal と login 完了時刻による説明は反例 1 件・境界例 1 件を含む仮説である。

親の最初の一般化「同時刻に開始した shard 群は別ノードでも全部 72〜76 秒」は段 3 相談 (所見 5) が提示データ (8d490116: 3 shard が 2.3 秒以内に開始し全部 61 秒台) で反証した。撤回し、上の ordinal / login-collection 完了時刻による説明に置き換えた。

## 3. 数表 (機械集計 `aggregate.md` から。process median、秒)

### 3.1 cell 表 (前半 a / 後半 b)

| cell | cohort wall | wall median | user | sys | CPU (u+s) | maxrss MiB | vol. cs | invol. cs | IPC | cache-miss / instr | pytest 報告 collected in | MHz (8 core sample) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R1-a / R1-b | 50.42 / 49.93 | 50.29 / 49.84 | 54.71 / 54.61 | 0.90 / 0.78 | 55.61 / 55.39 | 366 | 6145 / 4258 | 1613 / 1569 | 2.112 / 2.114 | 0.00113 / 0.00114 | 48.42 / 47.96 | 2101 |
| R48-a / R48-b | 84.73 / 85.23 | 84.31 / 84.79 | 80.47 / 80.98 | 1.69 / 1.77 | 82.31 / 82.89 | 366 | 5379 / 5323 | 8994 / 10124 | 1.416 / 1.410 | 0.00465 / 0.00465 | 80.12 / 80.59 | 3100 |
| warm-L (書込み許可) | 53.03 | 52.94 | 51.36 | 1.36 | 52.72 | 365 | 18863 | 1555 | 2.094 | 0.00105 | 49.80 | 2101 |
| warm-C (書込み許可) | 46.62 | 46.49 | 51.87 | 0.48 | 52.35 | 366 | 1671 | 1791 | 2.095 | 0.00105 | 44.14 | 2101 |
| L1-a / L1-b | 9.92 / 9.96 | 9.83 / 9.84 | 14.60 / 14.55 | 0.73 / 0.76 | 15.33 / 15.31 | 333 / 332 | 4791 / 4788 | 1186 / 1502 | 1.425 / 1.426 | 0.00116 / 0.00113 | 8.26 / 8.24 | 2101 |
| L4-a / L4-b | 11.28 / 11.30 | 11.14 / 11.21 | 11.75 / 11.82 | 0.80 / 0.79 | 12.56 / 12.62 | 332 | 4574 / 4592 | 1986 / 1080 | 1.552 / 1.544 | 0.00275 | 8.75 / 8.80 | 2101 |
| L12-a / L12-b | 12.39 / 12.31 | 12.19 / 12.16 | 11.71 / 11.52 | 0.91 / 0.95 | 12.59 / 12.43 | 333 / 332 | 4884 / 4809 | 1812 / 1482 | 1.516 / 1.528 | 0.00328 / 0.00332 | 9.38 / 9.36 | 2101 |
| L24-a / L24-b | 13.96 / 13.76 | 13.70 / 13.52 | 12.25 / 12.38 | 1.05 / 1.06 | 13.28 / 13.45 | 333 / 332 | 5887 / 5659 | 1598 / 1900 | 1.448 / 1.436 | 0.00349 / 0.00348 | 10.37 / 10.30 | 3098 / 3099 |
| L48-a / L48-b | 18.96 / 18.91 | 18.43 / 18.41 | 13.39 / 13.52 | 2.07 / 2.22 | 15.40 / 15.75 | 332 | 6824 / 6682 | 8609 / 8318 | 1.257 / 1.235 | 0.00376 / 0.00375 | 14.11 / 14.11 | 2596 / 2101 |
| ref-L48-pre / -post | 18.91 / 18.42 | 18.41 / 17.88 | 13.18 / 13.50 | 2.15 / 2.08 | 15.47 / 15.55 | 332 | 6748 / 6560 | 7840 / 8292 | 1.255 / 1.250 | 0.00377 / 0.00374 | 14.04 / 13.70 | 2595 / 3098 |
| C1-a / C1-b | 8.93 / 8.84 | 8.84 / 8.75 | 14.46 / 14.42 | 0.36 / 0.31 | 14.82 / 14.73 | 332 | 760 / 743 | 154 / 110 | 1.439 / 1.444 | 0.00111 / 0.00113 | 7.37 / 7.31 | 2101 |
| C4-a / C4-b | 10.25 / 10.18 | 10.16 / 10.09 | 11.57 / 11.47 | 0.32 / 0.34 | 11.88 / 11.82 | 332 | 736 / 732 | 288 / 290 | 1.592 / 1.598 | 0.00279 / 0.00280 | 7.87 / 7.80 | 2101 |
| C12-a / C12-b | 10.96 / 10.93 | 10.82 / 10.82 | 11.21 / 11.01 | 0.34 / 0.33 | 11.54 / 11.34 | 332 | 749 / 736 | 285 / 256 | 1.596 / 1.610 | 0.00341 / 0.00343 | 8.19 / 8.18 | 2101 |
| C24-a / C24-b | 11.58 / 11.70 | 11.35 / 11.50 | 11.20 / 11.46 | 0.34 / 0.33 | 11.55 / 11.76 | 332 | 752 / 782 | 222 / 291 | 1.571 / 1.553 | 0.00366 | 8.50 / 8.63 | 2600 / 3100 |
| C48-a / C48-b | 14.07 / 14.07 | 13.73 / 13.73 | 12.92 / 12.97 | 0.50 / 0.49 | 13.42 / 13.48 | 332 | 859 / 868 | 684 / 642 | 1.378 / 1.372 | 0.00404 / 0.00406 | 10.10 / 10.09 | 3100 |
| X48-a / X48-b (rc 4、欠測) | 28.73 / 21.70 | 28.64 / 21.61 | 766.35 / 737.25 | 49.56 / 68.31 | 815.91 / 805.56 | 332 (controller) | 376597 / 303793 | 283452 / 436322 | 1.233 / 1.219 | 0.00363 / 0.00383 | (no tests ran in 28.24 / 21.26) | 3100 / 3099 |

表の maxrss は a/b の median を MiB で丸めたもので、L1 / L12 / L24 は a が 333、b が 332 (331.9〜332.4)。major fault (median) は R/L/C の全 cell で 0〜8 (最大は C の 8)、X48 は 21 (a) / 62 (b)。minor fault は温で約 13.4〜13.5 万、冷で約 18 万 (cell ごとの値は `aggregate.json`)。MHz は 8 core の無作為 sample なので N が小さい cell では busy core を捉えていない (idle core の 2101 MHz が出る)。

### 3.2 導出表

| 量 | N=1 | N=4 | N=12 | N=24 | N=48 |
|---|---|---|---|---|---|
| L: wall(N)/wall(1) | 1 | 1.136 | 1.238 | 1.383 | **1.873** |
| L: CPU(N)/CPU(1) | 1 | 0.822 | 0.816 | 0.873 | **1.017** |
| C: wall(N)/wall(1) | 1 | 1.151 | 1.230 | 1.299 | **1.561** |
| C: CPU(N)/CPU(1) | 1 | 0.802 | 0.774 | 0.789 | **0.910** |
| R: wall(N)/wall(1) | 1 | — | — | — | **1.689** |
| R: CPU(N)/CPU(1) | 1 | — | — | — | **1.488** |
| Δplace(N) = L − C (wall median、a/b 平均) | 1.04 | 1.05 | 1.36 | 2.18 | **4.69** |
| Δplace(N) (cohort wall) | 1.05 | 1.08 | 1.40 | 2.22 | **4.86** |
| Δbc(N) = R − L (wall median) | **40.23** | — | — | — | **66.13** |

- 参照腕 (時間変動): ref-L48-post − ref-L48-pre = −0.49 秒 (cohort) / −0.53 秒 (median)。L48 の値は job の前後で動いていない (他の cell の条件が不変であることの証明ではない、§8)。
- 較正 X48 − L48: 機械集計では **n/a** (X の rc が期待 5 でなく 4)。生値は wall 28.6 秒 (a) / 21.6 秒 (b)、48 worker + controller の CPU 合計 815.9 / 805.6 秒 (worker 1 本あたり約 16 秒で温の単独 collection と同じ)。
- residual 行 (事前登録の式): C の wait = C48 − C1 − max(0, ΔCPU) = 4.89 / 4.98 秒、`placement_explained` = min(wait, Δplace48) = 4.70 / 4.69、`unexplained` = 0.20 / 0.30。**この `placement_explained` は式の定義どおり min を取っただけで、node-local 腕の待ちが Lustre 配置で説明されるという因果ではない (§4.4)。**

### 3.3 Lustre client stats (cell 前後の差分、`aggregate.json` の `lustre_delta`)

client id は `md_stats` の path に出る 3 種 (`…e752d800`、`…dfe9a000`、`…c4166000`)。主列は wave 木のある `/work` を担う `MDT0000-mdc-…e752d800`。「主列以外」は同 client の MDT0001 分と他 2 client (別 mount) の MDT0000 / MDT0001 分の intent_lock の合計で、mount 別には分けていない。

| cell | 主列 MDT0000-…e752d800: intent_lock | close | read_page | 主列以外の intent_lock 合計 (うち同 client の MDT0001 分) |
|---|---|---|---|---|
| L1-a | 104,958 | 2,016 | 142 | 5,321 (492) |
| L48-a | **5,032,315** | 91,001 | 6,722 | 254,428 (23,616) |
| R48-a | 4,954,877 | 58,007 | 6,722 | 336,930 (23,616) |
| C48-a | **1** | 0 | 0 | 229,410 (0) |
| X48-a | 5,040,904 | 96,162 | 6,746 | 256,600 (23,669) |

温の 1 process の collection は主列に約 10.5 万回の intent_lock (metadata op) を出し、48 並列は 503 万回 (48 × 104,958 = 5,037,984 に対し 5,032,315、比 47.9)。これが 18.4 秒の wall に収まる。node-local 腕では主列の op がほぼ消え (1 回)、主列以外 (他 client 由来) の op 約 4,780/process が残る (L48 でも同程度で両腕共通)。**これは当該 client (bnode008) の観測であり、MDS の負荷や他ノードの同時性を証明しない。**

## 4. 弁別 — 事前に書いた読み方 (段 4 裁定 §4) をそのまま当てる

読み方 v2 (結果を見る前に固定、`verbatim/s4-ruling.md` §4) と機械適用の label (`aggregate.md` の「判定」):

### 4.1 並列度応答

- **L48: wall 1.87 倍、CPU 1.02 倍 → `wait-dominant`。** CPU 時間は増えず、wall だけ増える。voluntary cs は 4.8k → 6.8k、involuntary cs は 1.2k → 8.6k、sys 時間は 0.7 → 2.1 秒 (kernel 側で 1.4 秒増)。
- **C48: wall 1.56 倍、CPU 0.91 倍 → `wait-dominant`。** node-local でも 48 並列で wall が 4.9 秒伸びる。voluntary cs は 750〜860 で L の 1/8、sys 0.3 → 0.5 秒。
- **R48: wall 1.69 倍、CPU 1.49 倍 → `cpu-time-inflation`。** 冷 (compile あり) の 48 並列では CPU 時間そのものが 27 秒伸びる。IPC 2.11 → 1.41、cache-miss/instr 0.00113 → 0.00465 (4.1 倍)、minor fault 18 万で温の 1.35 倍。事前登録どおり「帯域競合と断定しない」— IPC と cache-miss は共有 cache / memory 側の stall の兆候だが、周波数 (単独時の sample は idle core を見ており比較不能) と kernel 競合を分離していない。
- 温の N=4〜24 で CPU(N)/CPU(1) が 0.77〜0.87 と**単独より小さい**。IPC も 1.43 → 1.55〜1.61 と上がる。周波数 sample が N≤12 では idle core を見ているので理由は特定できない (単独時の低 IPC が memory 待ち・clock・両方のどれかは未識別)。数値だけ記録する。

### 4.2 配置効果 (Lustre の取り分)

Δplace(48) = **4.7 秒** (a 4.70 / b 4.69、cohort 4.89 / 4.83)、Δplace(1) = 1.0 秒、N に対して単調増加 (1.0 → 1.05 → 1.36 → 2.18 → 4.69)。当該 N・当該 cache 条件 (温、page cache 温) での配置差であり、上限でも下限でもない。sys 時間差 (L48 2.1 秒 vs C48 0.5 秒) と voluntary cs 差 (6.8k vs 0.86k) が対応する。

### 4.3 bytecode 効果

Δbc(48) = **66.1 秒**、Δbc(1) = **40.2 秒**。機械判定は `H-inconclusive` (事前登録の閾値 10〜15 秒の外、5 秒以上)。**独立 process の冷/温対照としては「冷は温より大幅に遅い」という向きが出た。受入の双峰差 (約 8〜18 秒) とは量が一致せず、受入の双峰の原因は本 job では確定していない。** 一致しない理由の候補 (以下はすべて解釈であり、本 wave では検証していない):

- 受入では login 側の collection が並行して pyc を書き続けるので、shard の worker は「開始時点は冷、途中から温」の混合になりうる。R 腕は wave 木の pyc 4 個 (有効性未確認) 以外に cache が無い状態のまま (書かずに) 走らせた。
- 受入の worker 48 本は xdist の起動順で数秒ずれて import を始めるので、先行 worker が読めなかった pyc を後続が読める余地がある。本 job の 48 process は同時起動。
- 単独の冷/温差は user CPU で +40.1 秒 (R1 user 54.71 / 54.61 − L1 user 14.60 / 14.55)。T-2617 §3.1 の login 実測は user CPU で +39.8 秒 (同 README `output/insights/2026-09-16_t2617-acceptance-collection-cost/README.md` §3.1 の表の #4 56.37 秒 − #3 16.54 秒。原測定 log は同 insight に無く、表の記載値からの算術)。同じ指標で見て、条件 (機体・checkout・負荷) の異なる 2 観測が概ね同規模だった。再確認した量であって新しい利得ではない。

### 4.4 未識別

C48 − C1 = 4.9 秒 (a 4.89 / b 4.98) は、CPU 時間の伸長では説明されず、source と pyc を node-local に置いた後も残る待ちである。候補は runnable のままの scheduler 待ち、page cache / dentry の lock、主列以外の Lustre client への op (約 4,780/process、両腕共通)、48 本同時の Python 起動と site-packages 読み込みだが、本 wave はこれを分けていない (CPU 時間が増えないことは CPU 資源不足の否定にならない — 段 4 裁定 §4 も scheduler 待ちを「待ち」に含めている)。事前登録の式が出す `placement_explained` 4.7 秒は「min(wait_C, Δplace)」の算術結果であって、C 腕の待ちの原因を Lustre に帰属するものではない。機械出力の `unexplained` = 0.25 秒 (式の残り) と、解釈上まだ帰属していない待ち = 4.9 秒 (C 腕、N=48) を別の名で併記する。**本文で「未識別」と呼ぶのは後者である。**

### 4.5 xdist 較正 (X)

事前登録の期待 rc=5 (no tests ran) に対し **rc=4**。`no tests ran in 28.24s` の後、conftest の flaky-test hold 完全性検査が `ERROR: flaky-test hold keys missing from complete collection: [...]` を出した (`raw/X48-a/procs.txt` の proc-0.err)。`-k` で全 deselect したため hold 対象が collection から消え、UsageError になった — 段 3 相談の所見 3 が「完全 collection の hold 検査も `-k` により経路が変わる」と予告したとおりで、事前登録の expected_rc を満たさない cell として機械集計から外した。生値 (wall 28.6 / 21.6 秒、2 走で 7 秒の幅) は「xdist 起動 + 48 worker collection + deselect + hold 検査 error」までの所要であり、受入 controller 費用の上限とは読まない。

## 5. 短縮策の効果量の見込み (実装しない、D1936 項 35)

| 策 | 本 wave の分解値からの見込み | 費用・前提 | 見込みの判定 |
|---|---|---|---|
| (a) fresh worktree の初回受入で冷 collection を避ける (login collection の完了を shard 投入の前に置く、または pyc を事前に用意する) | 受入で観測された群間差 = **初回受入の shard で約 8〜18 秒** (§2b、反例 1 件を含む)。本 job の冷側対照の差 66 秒は独立 process の対照値で、受入への転用はしない | 段 4 裁定 §4 は「Δbc(48) が受入の双峰差と整合すれば」を見込み提示の条件にしていたが、実測は `H-inconclusive` で整合していない。順序の入れ替えは `run_tests.py` の受入経路の変更 (実装面) で、順序を変えた場合に増える待ち時間は未測定。pyc の事前用意は T-2617 §4 の「条件つき」策で、本 wave は初回受入の shard に高い `pre` が集まるという関連を観測した (受入開始時の cache 状態は直接観測していない) | **仮説 (未確定)。** 観測された群間差からの見込みで、原因・正味利得・適用範囲・適用条件は未確定 (観測された関連は初回受入の shard に限られる) |
| (b) node-local staging (source と pyc を `/scr` へ) | 利得 **4.7 秒/shard** (温、N=48、独立 process の配置差) | 今回の構築手順の費用 = clone 13.4 + rsync 1.0 + warm-up 46.6 秒 (temp pyc を作る走) = 61.1 秒 + 回収。`/scr` は job 終了で消えるので node ごとに毎 job 払う | **今回の構築手順を 1 回の独立 collection に使う場合は負** (61.1 秒 > 4.7 秒)。再利用回数 (同 node で複数 shard / 複数走)、pyc を Lustre から持ち込んで warm-up を省く形 (それでも clone 13.4 秒 > 4.7 秒)、受入 shard への移植可能性 (受入 worker の配置差は未測定) は条件として別 |
| (c) 48 並列 collection そのものを減らす (worker 数) | L24 = 13.6 秒、L48 = 18.4 秒 (差 4.8 秒) | D532 が worker 数・配布順の変更を「提案しない」と明記 | **提案しない** (数値の記録のみ) |
| (d) 受入 `pre` 61 秒と本 job の 18.4 秒の差 (約 43 秒) の内訳 | 本 wave では測れない (異条件の差であり、独立 process には plugin・ledger・xdist 照合・prewarm が無く、計時区間も違う) | 同 checkout・同 job で「独立 48 → xdist 48 (hold 検査を壊さない全 deselect の形を先に設計) → plugin 有り → ledger 有り」と段階的に載せる診断が要る。conftest / gate の改変で代用しない | **未測定。** 削減可能量は書かない。次の一手として起票 (新規 T) |
| (e) T-2242 (prefilter、単一 process で最大 2.7 秒)・T-2244 (ledger 圧縮)・T-2245 (prewarm 重ね合わせ) | 本 wave の対照の外 | 既存資料の値を引用するだけ | 新しい見込みは書かない |

## 6. 既存被覆との関係 (二重に数えない)

- **entry 1218** (単一 process 内の file 別費用、1 file が 27%): 本 wave は file 別を測っていない。重ならない。
- **T-2617** §3.1 の冷 = user CPU +39.8 秒 (login、56.37 − 16.54) と本 job の R1 − L1 = user CPU +40.1 秒 (計算ノード) は、同じ指標で条件の異なる観測が概ね同規模だったという再確認であり、新しい量ではない。§3.2 の plugin +1.74 user CPU 秒 (user+sys では +3.46 秒) は本 wave が plugin を載せない根拠。**§3.3 の「残る約 38 秒は 48 重の並列実行そのもの」について、本 job は同条件対照ではない** (checkout・plugin・xdist・cache 配置・計時区間が違う)。本 job で言えるのは「この条件では温の 48 並列 collection そのものは 8.6 秒しか伸びず、38 秒の伸びは出ない」までで、T-2617 §3.3 自身が禁じた「同条件でない引き算の成分配分」を本 wave も行わない。§9 が求めた「計算ノードで同条件の診断走」のうち並列度・配置・bytecode に答え、受入 regime の側 (plugin・ledger・xdist 照合・prewarm・計時区間) は答えていない。
- **T-2097 / D1420**: 残差 58 秒の 95% が A 区間 (collection 51.7 秒) という測点は「controller が 48 worker の collection 完了通知を受け取る時刻」まで。本 wave の 18.4 秒は worker 相当の独立 process の collection wall で、A 区間に入る他の処理 (worker 起動 3.2 秒、plugin、ledger、通知) を含まない。T-2097 の「48 プロセス同時 87.57 秒 vs 単独 warm 10.23 秒」は計測機の記載が無く条件不明なので比較しない。
- **T-2786** (t080 共有 base 構築の 3 ブロック、collection 前の先行構築 P は変化なし): collection と別量で重ならない。本 wave は base 構築を測っていない。

## 7. 段 3 相談・段 6 レビューの所見と裁定

- 段 3 (codex gpt-6-astra / medium / read-only、lane sol、`verbatim/s3-consult-out.md`): 所見 9 件 (高 3・中 6)、**全件 real・採用、refuted 0**。高 3 件 = (1) `.git` 除外の複製は module 直下の `git rev-parse` (3 file) で collection に失敗する → `git clone --depth 1` に変更、実際に集合が一致した; (2) 3 仮説を一意に数値分解できない → 完了判定を「配置効果・並列度応答・未識別の定量化」に変更; (3) 全 deselect の xdist 走は受入の上限にならない → 較正に限定 (実際に rc=4 で欠測になった)。裁定の逐語は `verbatim/s4-ruling.md`。
- 段 5 (codex author、`verbatim/s5-author-out.md`): probe と集計の 2 file、合成入力で判定 label の正例・負例 PASS。親が計算ノードで実走した (この README)。
- 段 6 (codex gpt-6-astra / medium / read-only、2 レンズを 1 本、`verbatim/s6-review-out.md`): 数表 381 件を照合し 376 件一致、不一致 5 件。所見 11 件 = **must-fix 6 / should 5、NO-GO → 全件 real・反映 → 焦点再レビュー (`verbatim/s6-review2-out.md`)**。must-fix: (1) 「約 43 秒は受入 regime の追加処理」という帰属は異条件の差の成分配分で成立しない → 題・結論・§5 (d)・§6・fragment・新規 T から確定的な帰属を除き「異条件の差、内訳は未測定」に統一; (2) §5 (a) の「正・最大 9〜15 秒」は事前登録の条件 (Δbc が受入の差と整合したとき) を満たしていない → 仮説 (未確定) へ; (3) 前提実測の件数・全称に反例 (23 session、9ef5b469 の 66.2、edc9df7c は完了が開始の後、初回群に 78.8 と 68.8) → 数と範囲を訂正し反例・境界例を明記; (4) 「前後差は全 cell で 0.5 秒未満」「major fault 0〜21」に X48 の反例 → R/L/C の process median に限定; (5) Lustre 表の C48-a は 0 でなく 1、「別 mount」に同 client の MDT0001 分が混在 → MDT × client で集計し直し; (6) residual の「CPU 不足ではなく Lustre でもない」は根拠不足 → 「CPU 時間の伸長では説明されず local 配置後も残る待ち」に改め、式の `unexplained` 0.25 と未帰属の 4.9 を別名で併記。should: 冷腕の代表値を a/b 平均に統一 (50.1 / 84.6)、T-2617 との比較を同じ user CPU 指標で、staging の償却条件、出所未保存の観測 (login 完了 mtime・pyc 件数) を時刻付きで保存、load 最大 91.9、fragment 本文の README 再掲を縮約。
- 焦点再レビュー 2 巡目 (`verbatim/s6-review2-out.md`): 対応表 closed 5 / partial 6 / regressed 0、新規 3 件 (must-fix 1 = fragment が再レビュー完了を先取り、should 1 = 「4 個が温」の断定、nit 1 = 5.5 分 → 5.6 分)。残る must-fix は #2 (§5 (a) の適用範囲・§2b 見出しの断定)、#4 (§3.2 の「条件は動いていない」) と新規 #1 の 3 件、NO-GO。全件反映 (§2b 見出しを「受入回数と login 完了時刻で分かれる (原因は仮説)」へ、§5 (a) の適用範囲を未確定へ、§3.2 の参照腕の言い切りを削除、「4 個が温」を「pyc 4 個存在・有効性未確認」へ全箇所統一、§2b の pyc 件数の全称を木の分類 (5 / 5 / 4 本) と親の読みに分離、表本体の maxrss を a/b 別に、T-2617 値の出所 (表の記載値からの算術) を明記、fragment の先取りを削除し再掲を縮約) → 3 巡目 (`verbatim/s6-review3-out.md`)。
- 焦点再レビュー 3 巡目 (上限): 対象 9 件のうち closed 6 / partial 3 (#2: §5 (a) の表の 3〜4 列目に「本 wave が冷の発生を観測した」「効くとしても初回受入 1 走の shard だけ」が残存 = 親の 2 巡目の直し漏れ; #10: fragment の事故欄で dispatcher が「書いた」と確定表現、§2b の受入済み 5 木の根拠は t2700 以外未保存; #11: fragment の前提実測段落が README の再掲)、新規 3 件 (should 2 = §7 の要約が §5 (a) の実体と不一致、境界例から「大半の pyc」は導けない; nit 1 = 工数の和が 5 本)。raw の 30 cell・554 process の集計、Lustre 表、未帰属待ち 4.935 秒と式の残差 0.245 秒、staging 費用 61.118 秒は一致。**`DW-O16` の 3 巡上限に達したので、残る 6 件は親が裁定した: 全件 real、全件反映** (§5 (a) の表から原因・適用範囲の断定を除去、§2b の境界例を「一部の pyc が利用可能だった可能性、件数・有効性は未測定」へ、受入済み 5 木の根拠を「wave 名からの推定、t2700 以外未保存」へ、fragment の事故欄を「書いたと推定」へ、fragment の前提実測段落を参照だけに、工数 5 本)。refuted 0。4 巡目は行わない。

## 8. 限界・言わないこと

- **1 node (bnode008)・1 job・1 checkout (`25334c9b7`) の実測である。** 前半/後半の 2 走は順序反転で時間変動を検出するためのもので、統計的誤差の推定ではない。参照腕の前後差 −0.5 秒は「この job の 12 分で L48 の値が動かなかった」ことを示すだけで、他の cell の条件が動かなかったことの証明ではない。
- **受入の `pre` を分解したのではない。** 独立 process の collection は受入 worker と費用構造が同じではない (段 3 所見 3): shard plugin の正規化・割付・digest、duration ledger の配送・検証、xdist の起動・照合、prewarm、`pre` の測り方 (junit timestamp 起点、worker 時刻の最大) を含まない。**§結論 3 の約 43 秒は checkout・plugin・xdist・cache 配置・計時区間がすべて異なる観測値の差で、条件差と相互作用を含む。受入の内訳・削減可能量ではない。**
- **3 成分 (CPU / Lustre metadata / memory 帯域) への一意な配分はしていない。** 書けたのは「温では待ち優勢で CPU 時間は伸びない」「Lustre の取り分は N=48 で 4.7 秒」「冷では CPU 時間が 1.48 倍に伸び IPC が落ちる」「node-local でも 4.9 秒の待ちが残る (未識別)」まで。IPC 低下・cache-miss 増を memory 帯域の飽和と断定しない。
- R 腕の wave 木には pyc が 4 個存在し (warm-L 後の別 prefix は 1,528 個)、完全な冷とは書かない。4 個の帰属 (計算ノード側 dispatcher が job 開始時に書いた) は時刻と module 集合からの推定で、書込みを追跡したのではない (`verbatim/pycache-wave-after-job.txt`)。4 個の読み出し有効性 (source と整合して実際に読まれたか) は確認していない。保存した件数は「存在する数」であって「有効に読まれた温 cache の数」ではない。
- X48 は事前登録の期待 rc を満たさず欠測。xdist 経路の較正値は得られていない。X48 の 2 走は wall が 7.0 秒違い、major fault も 21 / 62 と揃っていない。
- Lustre client stats は当該 client の観測で、MDS 負荷・他ノードの同時性・login 並行 collection の影響は測っていない。仮説 H の「量の不一致」の理由 (§4.3) は候補であって検証していない。
- 前提実測 (§2b) は同日 23 session の観測で、「今後もそうである」とは言えない。login collection が pyc を書くことは code (`_collect_login_universe`) と現物 (`__pycache__` の有無) から読んだもので、書込み時刻を直接記録したのではない。ordinal と login 完了時刻による説明は反例 1 件 (6b5e8983 shard-0) と境界例 1 件 (edc9df7c shard-0) を含む。
- MHz は 8 core の無作為 sample で、N が小さい cell の busy core を捉えていない。温の N=4〜24 で CPU 時間が単独より減る理由は未識別。
- 改善は実装していない。§5 は算術の見込みで、実装した場合の受入 wall の変化は測っていない。§5 (a) は仮説、(b) は今回の構築手順 1 回利用の条件付き、(d) は未測定。

## 9. この dir の中身

- `README.md` — 本文。
- `aggregate.md` / `aggregate.json` — 集計 script (`verbatim/t2243_collection_contention_aggregate.py.txt`) の出力。cell 表・並列度応答表・配置効果表・bytecode 効果表・較正表・判定・欠測・実行付帯記録。
- `raw/` — job の生記録 (原本は wave 専用 dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2243-collection-diag/job-out/`、repo 外)。`env.txt`、`setcheck.txt` (`set.diff` は 0 byte で、`.diff` を実装面と判定する checker に掛かるので置かない)、`stage-C.txt`、`pycache-*.txt`、`lustre-initial.txt`、`perf-check.txt`、`probe.done`、`singleton-before.txt`、`process-args-before.txt`、`clone.err`、`rsync.err`、各 `<cell>/` に `cell.txt`、`procs.txt` (process ごとの `time` / `rc` / `perf` / `err` を逐語連結、整形は `verbatim/concat_procs.py.txt`)、`lustre-before.txt` / `lustre-after.txt`、`loadavg-*.txt`、`mem-*.txt`、`cpufreq.txt`、`singleton-before.txt`、`process-args-before.txt`。**除外したもの:** `proc-*.out` (nodeid 出力、合計 1.6 GB)、`set-L.txt` / `set-C.txt` (nodeid 一覧 26,152 行、`setcheck.txt` に一致の要約)、`pycache-L/` (59 MB)、`clone.out` / `rsync.out` (空)。
- `verbatim/` — `T-2243-origin.md` (依頼)、`s1-brief.md`、`s3-consult-prompt.md` / `s3-consult-out.md`、`s4-ruling.md`、`s5-author-prompt.md` / `s5-author-out.md`、`t2243_collection_contention_probe.sh.txt` (sha256 `d5542ab55040c68b7a0eca38b3a49f351715b20bbce8c4054cc3069e96d6cae0`)、`t2243_collection_contention_aggregate.py.txt` (sha256 `2fe44b7741225708d77cdb6e02f133a17c354a5173a4f1f3c1eede965d66198e`)、`run-probe-1.sh.txt` (親の投入 launcher)、`run-probe-1.log` (dispatch の stdout/stderr)、`run-probe-1.times`、`read_pre_v2.py.txt` / `pre-recent-v2.txt` (前提実測)、`login-collection-mtimes.txt` (§2b で引用した session の `login-collection.log` の mtime、観測 22:24)、`pycache-counts-wave-worktrees.txt` (稼働 wave 木の pyc 件数、観測 22:25)、`pycache-wave-after-job.txt` (job 終了直後の wave 木の pyc 4 個の一覧、観測 22:03)、`concat_procs.py.txt`、`startup-gate.log`、`s6-review-prompt.md` / `s6-review-out.md` (段 6 レビュー)、`s6-review2-prompt.md` / `s6-review2-out.md` (焦点再レビュー 2 巡目)、`s6-review3-prompt.md` / `s6-review3-out.md` (3 巡目)。probe と集計は Codex `role=author` の子 branch `author-t2243-probe` (commit `58f95933e`) に実体があり、repo には逐語 (`.txt`) だけを置く。

## 10. 再現手順

1. local main から fresh worktree を切り、submodule を初期化し、`orchestrator` / `tools` 配下の `__pycache__` を全部消す (`.gitignore` 対象、tree は汚れない)。login で python tool を走らせるときは `PYTHONDONTWRITEBYTECODE=1` を付ける (付けないと R 腕が温まる)。
2. `verbatim/t2243_collection_contention_probe.sh.txt` を repo 外の dir に `.sh` として置く (既定の出力先は script 冒頭 `OUT_ROOT` の定数。変えるなら `T2243_OUT` … ただし generic は clean env なので定数を書き換える)。
3. worktree を cwd にして `python3 tools/pegasus/dispatch_compute.py --task generic --walltime 01:00:00 --queue-wait-timeout 5400 --overall-grace 5400 -- bash <repo 外>/t2243_collection_contention_probe.sh`。`--walltime` は `HH:MM:SS`。
4. `<OUT_ROOT>/probe.done` が `rc=0` になったら `python3 <repo 外>/t2243_collection_contention_aggregate.py <OUT_ROOT> --markdown out.md --json out.json`。
5. 前提実測 (§2b) は `python3 verbatim/read_pre_v2.py.txt` を `.py` として login で走らせる (read-only、受入成果物 dir を読む)。
