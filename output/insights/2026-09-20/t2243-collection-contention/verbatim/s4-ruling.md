# 段 4 裁定 — [T-2243] (2026-09-20、親)

段 3 相談 (codex gpt-6-astra / medium / read-only、lane sol、11 分、出力 `codex/s3-consult-out.md`) の所見 9 件を現物で検証した。

## 1. 所見の裁定 (real / refuted、採否)

| # | 所見 | 判定 | 採否・処置 |
|---|---|---|---|
| 1 | `.git` 除外の node-local 複製は collection に失敗する (module 直下の `git rev-parse HEAD` check=True が 3 file) | **real** (現物: `test_t1998_stock_inline_pair.py:63`、`test_codex_worker_launch.py:36`、`test_t1259_qsub_env_delivery_probe.py:53`) | 採用。複製は `git clone --depth 1 --no-local file://<wave 木> <local>/repo` (node-local に自己完結の `.git`、HEAD は同一 commit) + `rsync -a --exclude .git <wave 木>/external/ <local>/repo/external/` (submodule の source bytes を重ねる)。warm-up C の rc と nodeid 集合を warm-up L と比較し、不一致なら C 腕の反復へ進まず差分の内訳を記録する。テスト除外・git 偽装はしない |
| 2 | 3 仮説を一意に数値分解できない (配置差には metadata 以外も混ざる、CPU 増は帯域以外でも起きる、wall−CPU には runnable の scheduler 待ちも入る) | **real** | 採用。完了判定を「配置効果 (Lustre − node-local、同 N・同 cache 条件) と並列度応答 (wall・CPU の N 依存) と未識別部分の定量化」に変更する。3 成分への強制配分はしない。既存走に context switch (`%w %c`)・page fault (`%F %R`)・利用可能 CPU (`nproc`、`taskset -pc`)・CPU MHz サンプル・perf (あれば) を付随記録 |
| 3 | 全 deselect の xdist 走は受入の「controller 直列 + xdist 起動」の上限にならない (plugin の正規化・割付・digest、ledger 配送 (loadgroup 条件)、prewarm、非空 nodeid の照合が欠ける) | **real** (現物: `acceptance_shards.py:895`、`conftest.py:1862`、`:2314`、`:2567`; `pre` 終端は worker 時刻の最大 `acceptance_shards.py:1092`) | 採用。xdist 対照 2 走は残すが「別 workload (xdist 起動 + worker collection + 空 ids) の較正」に限定し、「上限」の解釈を削除。受入 `pre` との直接比較はしない。(P1-A) 撤回 |
| 4 | 温 prefix の新設は現行受入の cache 状態を再現しない。warm-up は `PYTHONDONTWRITEBYTECODE` を **unset** (文字列 "0" は禁止指定になる)。assertion rewrite cache が prefix に従うかは未確認 | **real** | 採用。(a) warm-up は unset。(b) 現行 checkout cache のままの腕 **R** (wave 木、prefix 未設定、`PYTHONDONTWRITEBYTECODE=1` = 受入 worker と同じ、wave 木は現在 pyc 0 個 = **冷**) を N=1 と N=48 で各 2 走追加。(c) warm-up 後に prefix 配下の `*.pyc` と `*-pytest-*.pyc` の件数を記録 (rewrite cache が prefix に従うかの実測) |
| 5 | 「同時開始 shard 群は全部 72〜76 秒」は提示データ (8d490116: 3 shard が 2.3 秒以内に開始し 61 秒台) と矛盾。反復 2 の根拠 (T-2617 の 0.3 秒) は反復誤差ではない。file は 27 行でなく 29 行 | **real** | 採用。(P1-D)(P1-E) 撤回。前提実測を v2 で再走した結果、**代替仮説が立った (§2)**。N の順序は前半昇順・後半降順、参照腕 L48 を job 前後に置く。client stats は当該 client の観測であり MDS 負荷の証明でないと明記 |
| 6 | wall の区間と出力負荷が不統一 (`-q` の nodeid 出力を Lustre のログへ出すと読取り競合に書込みが混ざる、process 別最大 ≠ cohort の開始→終了) | **real** | 採用。stdout/stderr は node-local の個別 file、cohort の開始/終了 epoch を採る、pytest の `collected ... in X.XXs` も採る、nodeid 集合比較は warm-up 出力を使う |
| 7 | generic は clean env・cwd 固定なので環境設定と腕ごとの `cd` は compute 側 script に明記。「clean tree」と「checkout 配下への書込みゼロ」は別 | **real** (現物: `dispatch_compute.py:155-161`、`:1841`、`:1853`) | 採用。script 内で export / cd。job の書込み先は node-local と wave 専用 dir だけ。job 前後に wave 木の `__pycache__` が 0 のままであることを記録 |
| 8 | `read_pre.py` は universe を取れず (`observed_universe` は list)、first-start 欠測を黙って除外 | **real** | 採用。v2 で修正・再走 (`verbatim/pre-recent-v2.txt`)。first_missing は全 shard 0 |
| 9 | 配置差を staging 上限へ転用する算術には条件が欠ける | **real** | 採用。「当該 N・当該 cache 条件での配置差」として報告、複製 (clone/rsync) と warm-up の所要を別記、償却は受入 3 shard × 走数の条件付き。T-2617 の 38 秒へ足し込まない |

refuted 0。scope 外の real 所見なし (全件が測定設計の是正で、gate・台帳・一般化を足さない)。

## 2. 前提実測 v2 が立てた新事実 (brief の (P1-D) を置き換える)

直近 24 session (69 shard、`verbatim/pre-recent-v2.txt`、`read_pre.py` v2) を走行元 worktree ごとの受入回数 (ordinal) で分けると:

- **ordinal ≥ 2 の session は `pre` が全部 58.9〜62.8 秒 (例外 66.2 が 1 shard)。**
- **70〜76 秒は ordinal = 1 (fresh worktree の初回受入) の session でだけ出る**。しかも同一 session 内で「最初に開始した shard 群」だけが高く、後から開始した shard は 61 秒台 (d4eafc90: shard-1 19:17:54 → 76.1、38 秒後の shard-2 → 61.0)。
- 受入は login 側 collection (D711 gate 3、`login-collection.log`、`PYTHONDONTWRITEBYTECODE` 無し) を shard 投入と並行に走らせており、その完了時刻が shard 開始より**後**なら高い (988edc99: 完了 20:28:28 vs 開始 20:27:52 → 74〜75)、**前**なら 61 秒台 (edc9df7c: 完了 19:53:52 vs 開始 19:53:49、d4eafc90 shard-2: 完了 19:18:25 vs 開始 19:18:32)。
- 受入を通った wave 木は `orchestrator/tests/__pycache__` に pyc 394〜397 + pytest rewrite 366〜369 を持ち、受入前の木は 0 (login で `find` 実測)。計算ノードの worker は `PYTHONDONTWRITEBYTECODE=1` (dispatch 既定) で書かないので、**pyc を書いているのは login 側 collection**。

**仮説 H (job 内で検証する): 現行 `pre` の双峰 (61 / 70〜76) は shard 開始時点の bytecode cache の有無で決まり、差は約 10〜15 秒。** 本 job の R 腕 (冷) と L 腕 (温) の N=48 対照がこれを同一 node・同一 checkout で確定する。T-2617 §9「冷が実測された時点で見直す」の実測回答になる。改善 (login collection の完了を shard 投入の前に置く等) は実装しない — 効果量の見込みとしてだけ書く。

## 3. 測定行列 v2 (実装子への確定仕様)

計算ノード 1 job (`dispatch_compute.py --task generic --walltime 01:00:00 --queue-wait-timeout 5400 --overall-grace 5400 -- bash <job dir>/t2243_collection_contention_probe.sh`)。cwd = wave 木 (dispatch が固定)。script は環境変数を自分で export し、腕ごとに `cd` する。

腕:
- **R** (現行 checkout・冷): cwd = wave 木、`PYTHONDONTWRITEBYTECODE=1`、`PYTHONPYCACHEPREFIX` 未設定。wave 木の `__pycache__` は 0 個 (job 冒頭と末尾で `find` して記録、0 でなければ R は「温」と記録)。
- **L** (Lustre・温): cwd = wave 木、`PYTHONDONTWRITEBYTECODE=1`、`PYTHONPYCACHEPREFIX=<wave 専用 dir (Lustre)>/pycache-L`。warm-up L は `PYTHONDONTWRITEBYTECODE` を unset して 1 走し prefix を満たす。
- **C** (node-local・温): `LOCAL=/scr/$USER/t2243-$$` (`/scr` が無ければ `/tmp/t2243-$$`)。`git clone --depth 1 --no-local file://<wave 木> $LOCAL/repo` + `rsync -a --exclude .git <wave 木>/external/ $LOCAL/repo/external/`。cwd = `$LOCAL/repo`、prefix `$LOCAL/pycache-C`。warm-up C は unset で 1 走。clone / rsync の所要と `du -sm` を記録。
- **X** (xdist 較正、Lustre): cwd = wave 木、prefix = L のもの、`python3 -m pytest orchestrator/tests -n 48 -k "zzz_no_such_test_zzz" -q -p no:cacheprovider`。

共通: `python3 -m pytest orchestrator/tests --collect-only -q -p no:cacheprovider`、`IZANAGI_TASK_RUN_AUTO_RECORD=0`、`PYTEST_ADDOPTS` / `PYTEST_XDIST_TESTRUNUID` unset、`TMPDIR=<node-local scratch>`。各 process は `/usr/bin/time -f "%e %U %S %M %F %R %w %c" -o <cell>/proc-<i>.time` で包み、stdout/stderr は `<cell>/proc-<i>.out` / `.err` (node-local)。perf は `/usr/lib/linux-tools/5.15.0-135-generic/perf` が実行可能なら `perf stat -x, -e cycles,instructions,cache-misses -o <cell>/proc-<i>.perf --` で最外側に付け、不能なら付けずに `perf=absent` を記録。Lustre client stats は `/proc/fs/lustre/llite/*/stats` と `/proc/fs/lustre/mdc/*/md_stats` を cell 前後で snapshot (読めなければ `lustre_stats=unreadable`)。cell ごとに `/proc/loadavg`、`/proc/meminfo` (MemAvailable)、`/proc/cpuinfo` の MHz を cell 中盤に 1 回、`nproc`、`taskset -pc $$`、単独性 (`ps -eo user,pid,comm --no-headers` で自 user 以外の非 system user process の一覧・件数、自 user の pytest 残骸 0 件)。cohort の開始 epoch (全 process 起動直前) と終了 epoch (全 wait 後) を記録。

順序 (走数 30):
0. env 採取 (hostname, nproc, free, df, mount の Lustre/local 種別, python/pytest version, perf 可否, lustre stats 可読性)、単独性、wave 木 `__pycache__` = 0 の記録、page cache warm (`find orchestrator tools -name '*.py' -exec cat {} + >/dev/null`)。
1. R1、R48 (前半)。
2. warm-up L (unset、prefix 満たし)。prefix の `*.pyc` / `*-pytest-*.pyc` 件数を記録。
3. C 複製 (clone + rsync)、warm-up C (unset)。集合比較: warm-up L と warm-up C の `--collect-only -q` 出力から nodeid 行 (`::` を含む行) を sort して diff、rc も比較。不一致なら C 腕は以後 skip し、差分の行数・先頭 20 行を記録。
4. 参照 L48 (前)。
5. 前半 N = 1, 4, 12, 24, 48 の順に、各 N で L → C。
6. X (前半)。
7. 後半 N = 48, 24, 12, 4, 1 の順に、各 N で C → L。
8. X (後半)。
9. R48、R1 (後半)。
10. 参照 L48 (後)。
11. 末尾: wave 木 `__pycache__` = 0 の再確認、`$LOCAL` の結果 dir を wave 専用 dir へ rsync、`$LOCAL` を削除、`.done` に rc。

概算所要: N=48 走 ≈ 90 秒 × 8、N=24 ≈ 60 × 4、他 ≈ 20〜40 × 14、X ≈ 60 × 2、clone ≈ 60〜120 秒、cat ≈ 20 秒 → 約 28 分。walltime 01:00:00。

## 4. 弁別の読み方 v2 (結果を見る前に固定)

- 並列度応答: cell ごとに process wall の median/max、user+sys の median、cohort wall。`wall(N)/wall(1)`、`CPU(N)/CPU(1)` を L と C で別々に出す。
  - CPU(N) ≈ CPU(1) ∧ wall(N) > wall(1): 「待ち」(I/O・lock・runnable のまま scheduler 待ちを含む。`%w %c` と faults で補助)。
  - CPU(N) > CPU(1): 「CPU 時間の伸長」(stall・kernel 競合・周波数低下を含む。perf の IPC・MHz で補助。帯域と断定しない)。
  - wall(48) ≈ wall(1): contention なし。
- 配置効果 Δplace(N) = L(N) − C(N) (cohort wall と process median の両方)。当該 N・当該 cache 条件での差。Lustre の寄与の観測値であって上限でも下限でもない。
- bytecode 効果 Δbc(N) = R(N) − L(N)。同 checkout・同置き場での冷/温差。§2 の仮説 H は Δbc(48) が 10〜15 秒付近なら支持、5 秒未満なら不支持。
- 未識別 = C(48) − C(1) のうち CPU 伸長でも待ちでも説明のつかない残り (数値として出す)。
- X は「xdist 起動 + worker collection + 空 ids」の較正値。独立 L48 との差は「xdist 経路の追加費用の観測値」と書き、受入 controller 費用の上限とは書かない。
- 効果量の見込み (実装しない): (a) 初回受入の bytecode 冷: Δbc(48) が `pre` 双峰差 (約 13 秒) と整合すれば「login collection の完了を shard 投入前に置く、または pyc を事前配布する」策の見込み = Δbc(48) /初回受入 1 回。(b) node-local staging: Δplace(48) − (clone + rsync + warm-up の所要) を 3 shard × 走数で償却する条件付き。(c) T-2242 prefilter / T-2244 ledger 圧縮 / T-2245 prewarm 重ね合わせは本 wave の対照の外なので、既存資料の値を引用するだけで新しい見込みは書かない。

## 5. (P1) の裁定

- (P1-A) 撤回 (所見 3)。(P1-B) 撤回 → 読み方 v2 (所見 2)。(P1-C) 撤回 → clone (所見 1)。(P1-D) 撤回 → 仮説 H に置換 (所見 5 + 前提実測 v2)。(P1-E) 撤回 → 反復 2 は「前半/後半の順序反転 + 参照腕」で時間変動を検出する設計に変更、統計的誤差の主張はしない。

## 6. 変異 matrix・受入・record

- repo の実装面差分ゼロ (probe は wave 専用 dir に置き、repo には `.md` 逐語のみ) → 変異 matrix 免除 (DW-S04)。受入全走は免除せず、記録 commit 後の tip で 1 走。
- 実装子: Codex role=author 1 本、workspace-write、所有 path = `tools/t2243_collection_contention_probe.sh`、`tools/t2243_collection_contention_aggregate.py` (子 worktree に commit させ、親が wave 専用 dir へ複製し、wave 木には apply しない)。
- 投入直前に local main を wave 木へ `--ff-only` で取り込む (peer 通知: main は 799d38b97 まで進んだ。conftest の pairing 既定 on を含む。現行の collection を測るため取り込む)。取り込み後 `git submodule update --init --recursive`、clean 確認、tip SHA を記録してから投入。
- 段 6: 親が job を回収し README を書いた後、read-only review 1 本 (2 レンズを 1 本で: 数表の検算・読み方 v2 の適用の正しさ / 既裁定・scope・言い過ぎ)。

## 7. 裁定 inbox の再走査

- local main: f94b61fc8 → 799d38b97 (peer `dev-wave-t2766-pairing-adopt` の landed 通知 91ecb61ba、その後 paper-intro-ja の land)。wave 木 HEAD は main の祖先。本 wave の所有 path (新規 insight dir、worklog fragment) と競合なし。
- `docs/handoff/` は README と 2026-08-28 の中断品のみ。新しい裁定なし。
