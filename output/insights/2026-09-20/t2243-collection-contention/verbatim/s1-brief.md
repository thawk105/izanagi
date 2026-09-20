# 段 1 brief — [T-2243] 受入 collection の 48 並列 contention を計算ノードで分解する診断 wave

作成 2026-09-20 (JST)。wave 木 `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2243-collection-diag`、起点 local main `f94b61fc8`。

## 研究前進 (1 行)

受入全走 (dev-wave の land gate) の wall の固定部分 `pre` (session 開始 → 48 worker の collection 終了) は現行 61〜76 秒で、T-2617 が「約 38 秒の配分 (memory 帯域 / Lustre metadata / controller 直列) は決まっていない。決めるには計算ノードで同条件の診断走が要る」と未決のまま残した。本 wave はその配分を計算ノード 1 job・同 checkout・同条件の対照で決め、短縮策の効果量の**見込み**だけを数で置く。完了判定 = 3 仮説 (CPU / Lustre metadata / memory 帯域) の各寄与を同一 job 内の対照で数値化した insight が着地し、実装は 0 行。

## scope

- 計算ノード (gen_S) 1 job (`dispatch_compute.py --task generic -- bash <job dir の script>`) で、独立 process の `python3 -m pytest orchestrator/tests --collect-only -q -p no:cacheprovider` を条件行列で同時起動し、process ごとの wall / user CPU / sys CPU (`/usr/bin/time -f`) と、使えるなら perf stat (`/usr/lib/linux-tools/5.15.0-135-generic/perf stat -e cycles,instructions,cache-misses`、絶対 path、不在なら degrade) と Lustre client stats (`/proc/fs/lustre/llite/*/stats`、`mdc/*/md_stats` の走前後差分、読めなければ degrade) を採る。
- 単独性は job 内で pgrep (自分以外の user process 0 件) と `/proc/loadavg` で確認し、記録する。login では測らない。
- 改善実装は行わない (D1936 項 35)。gate・検査・台帳・一般化の追加は scope 外 (引数)。受入 report の schema には触れない (D1729)。
- 成果物: `output/insights/2026-09-20/t2243-collection-contention/README.md` + `verbatim/` (script の逐語は `.md`、生出力 txt/json)、worklog fragment、専用 handoff。decisions fragment は無し (診断のみ、新しい設計判断を作らない)。

## 確定済みユーザー裁定・既裁定 (純増の境界)

- D1936 項 35: prewarm 等は効果を先に測り、未確認のまま実装しない。
- D1728 / D2003 / D532 / D1729: 自 shard 絞り込み・集合縮小・worker 数変更・report schema 拡張はいずれも本 wave で触れない。
- 既存被覆 (二重に数えない): entry 1218 = 単一 process 内の file 別費用 (1 file が 27%、hook は 5% 未満)。T-2617 = plugin 費用 +1.74 CPU 秒、bytecode 冷/温 (冷は +40 CPU 秒/process)、28 走の `pre` 55〜59 秒。T-2097 / D1420 = 残差 58 秒の 95% が A 区間で collection 51.7 秒、48 同時 87.57 秒 vs 単独 warm 10.23 秒 (計測機不明記)。T-2786 = t080 共有 base 構築の 3 ブロック (発行 65 秒・git 11 秒・copy 配置) — collection とは別量で、collection 前の先行構築 (P) が「変化なし」だった事実だけを重ねて読む。
- 絶対規律 2 は緩めない (本 wave は verifier・gate に一切触れない)。

## brief 前の前提実測 (2026-09-20 夜、repo 外の受入成果物 27 shard、`tmp/read_pre.py`)

- 現行 `pre` = **60.5〜76.1 秒** (universe 26,040 件、T-2617 時点 24,020 件の 55.4〜59.1 秒より増)。`disp` は shard-0 で 0.0 (T-2616 の prewarm 重ね合わせが着地済み)。
- **同時刻に開始した shard 群は別ノードでも全部 72〜76 秒、単独時刻の shard は 61 秒台** (988edc99 の 3 shard、04d049fc の同時 2 shard、e337587c の同時 2 shard)。ノード内の並列度だけでなく**ノード外の共有資源**が `pre` を動かす兆候。本 wave はノード内の並列度を条件にし、ノード間同時性は測らない (記録だけ)。
- gen_S: QUE 28 / RUN 45 / HLD 99 (混雑)。投入は `--queue-wait-timeout 5400 --overall-grace 5400 --walltime 01:00:00`。
- worktree は `.git` と `output` を除き 107 MB + external 15 MB。node-local 複製は現実的。

## 不変条件

- repo の実装面に変更なし。probe (bash + 集計 python) は Codex `role=author` が wave 木の `output/insights/.../verbatim/` 配下でなく **job dir へ退避する前提で wave 木の一時 path** に書き、親が実行前に job dir へ退避して wave 木を clean に戻す (`DW-C01`)。repo へは `.md` の逐語だけ残す。
- 測定走は checkout を汚さない: `PYTHONDONTWRITEBYTECODE=1`、`PYTHONPYCACHEPREFIX` は条件ごとの置き場 (Lustre 条件は Lustre 上の job 専用 dir、local 条件は node-local dir)、`-p no:cacheprovider`、`IZANAGI_TASK_RUN_AUTO_RECORD=0`、`PYTEST_ADDOPTS` / `PYTEST_XDIST_TESTRUNUID` unset。
- 走ごとの scratch は自分のものだけ片付ける。
- 受入の集合・gate・schema・conftest に触れない。

## 測定行列 (親の provisional 設計 — 段 3 の攻撃対象)

- 因子 1: 同時 process 数 N ∈ {1, 4, 12, 24, 48} (独立 process、xdist なし、同時起動して全員の終了を待つ)。
- 因子 2: source の置き場 ∈ {Lustre (wave 木そのもの), node-local (`/scr` があればそこ、無ければ `/tmp`、`rsync -a --exclude .git` の複製)}。pyc prefix も同じ置き場。
- 固定: bytecode 温 (各置き場で最初に書き込み許可の warm-up 1 走で prefix を満たし、以後は読むだけ)、page cache 温 (warm-up が兼ねる)、collection 対象 = 全 `orchestrator/tests`。plugin (`-p tools.acceptance_shards`) は載せない (費用 +1.74 CPU 秒は T-2617 §3.2 が既測、二重に数えない)。
- 反復: 各 cell 2 走、順序は cell を交互 (Lustre→local→local→Lustre のような ABBA) にし、時間交絡を割る。
- 対照 (controller 直列処理の見積もり): Lustre 条件で `python3 -m pytest orchestrator/tests -n 48 -k "zzz_no_such_test_zzz" -q -p no:cacheprovider` (worker 48 が全 collection、controller が nodeid 照合、選択 0 件) を 2 走。「独立 48 process の最大 wall」との差を controller + xdist の取り分の上限と読む。
- 検証: local 複製での collected 件数と nodeid 集合が Lustre と一致することを job 内で確認する。不一致なら local 条件は無効と記録する (差の内訳を出す)。
- 単独性: 各 cell の直前に pgrep で自 user 以外の process と、自分の前走の残骸が 0 件であることを確認し記録。

## 弁別の読み方 (事前に書く。結果を見てから変えない)

- N を上げても process あたり user+sys CPU が一定で wall だけ伸びる → 待ち (I/O / lock)。node-local で消える分 = Lustre metadata、残る分 = node 内の共有 (kernel / page cache lock 等)。
- N を上げると process あたり CPU 時間そのものが伸びる (perf があれば IPC 低下) → memory / cache 帯域競合。node-local でも同じ形なら Lustre ではない。
- N=48 で wall ≈ N=1 の wall → CPU は足りており contention 無し (48 core / 48 process)。
- xdist -n 48 の wall − 独立 48 の最大 wall = controller 直列 + xdist 起動の上限。
- 「効果量の見込み」は上の分解値からの算術 (例: Lustre 取り分 X 秒 → node-local staging の上限 X 秒、bytecode 冷の再発なら T-2617 の +40 CPU 秒/process)。実装しない。

## (P1) 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1-A) 独立 process の同時 `--collect-only` は、受入の xdist worker の collection と同じ費用構造を持つ (worker は execnet 経由で同じ pytest collection を走らせ、差は controller との通信だけ)。
- (P1-B) 3 仮説は上の「弁別の読み方」で分離できる。特に user+sys CPU 一定 ∧ wall 伸長を「待ち」と読んでよい。
- (P1-C) node-local 複製 (`.git` なし) の collection は Lustre と同じ集合を出す。
- (P1-D) 前提実測の「同時開始 shard 群 +12〜15 秒」は本 wave の scope 外 (ノード間同時性) として記録に留めてよい。
- (P1-E) 反復 2 で傾向を言うのに足りる (T-2617 の `pre` のばらつきは 0.3 秒、本日 27 shard でも同条件なら ±1 秒)。

## 並列分割

- 段 2 (plan) は省く (軽量版)。段 3: read-only codex 相談 1 本 (測定設計の交絡・弁別可能性・受入 regime との差のレンズ) を brief に対して走らせ、段 4 で裁定してから実装する。
- 段 5: Codex `role=author` 実装子 1 本 (job script + 集計 script)。所有 path は wave 木の一時 dir 1 つ。
- 段 6: 親が job を投入・回収し insight 草稿を書いた後、read-only codex review 1 本 (結果解釈と数表の検算)。変異 matrix は実装面差分ゼロ (repo) なので免除。
- 受入全走は記録 commit 後の tip で 1 走 (docs のみ)。

## 条件 dispatch の評価 (段 1 brief 前、一括)

- 08 (freeze / oracle gate / proof chain): 不成立 — 診断のみ、repo の実装面に変更なし。
- 09 / 10 (凍結 bytes / producer): 不成立。
- 11 (削除): 不成立。
- 13 (gate・検証の新設): 不成立 — 引数が明示的に scope 外。
- 20 (clean-tree gate): 成立・実行済み rc=0 (`startup-gate.log`)。
- 01 / 02 / 05: codex 起動時に読む。17 / 18 / 23 / 25 / 27 / 28: 該当段で読む。
