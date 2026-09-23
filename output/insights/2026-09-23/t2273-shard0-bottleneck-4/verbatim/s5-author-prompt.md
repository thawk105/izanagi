単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-acceptance-bottleneck-diag

必読事項の射影:
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/s4-ruling.md — 段 4 裁定。**§1 (C2・C3・C7)、§2、§3 が仕様の正本**。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/s1-brief.md — 親の段 1 brief (背景。裁定と食い違えば裁定が優先)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/codex/s3-consult-out.md — 段 3 相談 (C1〜C7 の根拠)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2817-acceptance-bottleneck-3/probe/t2817_replica_runner.py、t2817_replica_plugin.py、t2817_replica_analyze.py — **出発点** (前回 wave の Codex author 作、計算ノード実機で 1 走完走済み)。これを写して改める。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/verbatim/t2817-jobB-analysis-A.json — 出発点の analyzer の実出力 (形の参照)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe/output/insights/2026-09-19/t2786-base-decomposition-recovery/README.md — 成分名と既知の計器欠陥 (§2・§3・§6)。合成 fixture だけで妥当性を確認して実機で落ちる型を繰り返さないための参照。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe/orchestrator/tests/test_s8b_oracle_driver.py — 観測対象の実体: `_run_git` (400 行付近)、`_run_git_bytes` (794)、`_copy_git_visible_output` (847)、`_T080SharedBases` (920、`get` の flock)、`_t080_join_shared_bases`、`_t080_stub_free_e2e_repo` (995)、`_build_t080_stub_free_e2e_repo` (1437、発行 subprocess 1713 付近)。名前と signature をここで確かめる。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe/tools/run_tests.py、tools/acceptance_shards.py、tools/pegasus/dispatch_compute.py — 受入 shard 子の argv・env・session の作り方 (必要な範囲だけ grep)。読めなければ即停止。

## 役割と所有

あなたは [T-2273] 診断 wave の段 5 実装子 (Codex role=author、workspace-write) である。自分たちの受入 test 基盤の**診断用 probe** (観測 wrapper) の実装で、改善実装ではない。作業 worktree は
`/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe` (branch `author-t2273-probe`)。所有 path はちょうど 3 file で、それ以外は 1 byte も変えない:

- `tools/t2273_replica_runner.py` (python3.10、標準 library だけ)
- `tools/t2273_replica_plugin.py` (標準 library と pytest だけ)
- `tools/t2273_replica_analyze.py` (python3.10、標準 library だけ)

この 3 file は repo に land しない (親が wave 専用 dir へ退避して計算ノードで走らせる)。**docs・テスト・conftest・既存 tools は編集しない。`docs/handoff/` へ file を作らない。`git add` / `git commit` を実行しない。** 差分は worktree に残せばよい。

## 何を足すか (出発点 T-2817 probe からの差分。それ以外の契約は出発点のまま保つ)

名前は `t2817` → `t2273` (module 名、env `T2273_REPLICA_OUT`、job tag、一時 dir 接頭辞) に改める。

1. **TMPDIR を上書きしない (裁定 C7):** runner は `/scr` への付け替えをやめ、dispatch 環境から継承した `TMPDIR` (未設定なら `tempfile.gettempdir()` の値) をそのまま子に渡す。`env-before.json` に継承値、`os.statvfs` と `/proc/mounts` から引いた mount point と filesystem 種別を記録する。smoke は出発点どおり先に走らせ、実行した事実・所要・rc を記録する。
2. **copy 複合区間の分割 (裁定 C2):** `_copy_git_visible_output` の span の内側で、(a) その呼出し中の `_run_git_bytes` 呼出し (git 可視列挙) と (b) その呼出し中の `shutil.copytree` を、親 span id 付きの子 span として記録する (名前 `copy.list` / `copy.copytree`)。出発点が builder 直下で数えている `copytree` / `git` との二重計上を analyzer で排他化する。`_copy_git_visible_output` の戻り値 (可視 path 集合) の件数を `extra` に記録する。
3. **span ごとの CPU 時間 (裁定 C2):** 全 span の begin/end で `resource.getrusage(RUSAGE_SELF)` と `RUSAGE_CHILDREN` の utime/stime を取り、差分を `extra.cpu` に記録する (children は終了済み子 process 分であることを analyzer の注記に書く)。
4. **資源標本 (裁定 C2):** runner が A 走の間だけ 1 Hz の標本 thread (または子 process) を回し、`<out>/A/samples.jsonl` へ 1 行 1 標本で `/proc/stat` の cpu 行 (user/nice/system/idle/iowait/irq/softirq/steal)、`/proc/loadavg` (running/total process 数を含む)、Lustre client の `/proc/fs/lustre/llite/*/stats` と `/proc/fs/lustre/mdc/*/md_stats` の全 counter (読めなければ欠測と記録)、TMPDIR の block device の `/proc/diskstats` 行を書く。標本の失敗は A 走を止めない (欠測として記録)。
5. **analyzer の追加出力 (裁定 C3・§3):**
   - (a) builder 同時本数と `copy.list` / `copy.copytree` 同時本数の時系列 (JUnit timestamp 基準の秒、イベント境界ごと)。
   - (b) **最大占有 worker の item 列の排他分解**: 各 item について「flock 待ち (同 key の builder の区間と対応付ける) / 自分の構築 (copy.list・copy.copytree・copy その他・git・issue・その他) / base→test copytree / verify / 残り (= test の junit time − 上記の和)」。区間の重なりは二重に数えない。同じ分解を L の worker にも出す。各 item の rank・開始・終了・key も載せる。
   - (c) builder の各下位区間 (copy.list、copy.copytree、git、issue) ごとに、区間内の資源標本の平均 (CPU 使用率 = 1 − idle 比、iowait 比、run queue、Lustre の主要 op/秒) と、CPU 時間/壁時間比を表にする。裁定 §3.2 の区分 (≥ 0.8 = CPU 実行が支配、≤ 0.3 = 待ちが支配、間 = 混在) を列として付ける (children を含む比と含まない比を両方)。
   - (d) 出発点の出力 (key 一覧、consumers、shard 層: W・pre・O_max と worker・L と worker・F・post) は保つ。
   - 値は 1 走の観測であり中央値でないと冒頭に書く。
6. 合成入力で analyzer の正例・負例を走らせる (例: 2 key の spans と子 span・samples・小さい junit/report を作り、排他分解が重なりを二重計上しない正例と、子 span が親 span の外にはみ出す入力を拒否または警告する負例)。**加えて出発点と同じく、login で走らせられる範囲 (import・argparse・`--help`・hostname 防壁が rc 3 を返すこと) を実際に走らせる。** pytest plugin は login で `python3 tools/run_tests.py orchestrator/tests/test_s8b_oracle_driver.py -k shared_base_builds_real_builder_once_across_processes -n 2 --dist loadgroup -p no:cacheprovider -p t2273_replica_plugin` を `PYTHONPATH=<worktree>/tools`・`T2273_REPLICA_OUT=<worktree 外でない一時 dir>` で 1 回走らせ、span (copy.list / copy.copytree / cpu を含む) が書かれることを確かめてよい (走らせられなければ「実装済み・未実走」と書く)。この smoke の出力 dir は worktree 内の `tools/.t2273-smoke-out/` とし、報告後に削除してよい。

## 不変条件

- 観測 wrapper は実物へ同じ引数を 1 回渡し、返り値と例外をそのまま返す (DW-O14 の「実物へ委譲する観測 wrapper」)。受理集合・deselect・skip・hold・順序・verifier・台帳に触れない。worker 側で stdout/stderr に書かない。
- 固定値 (HEAD、KEYS、key 件数、T-2817 の path) を焼き込まない。観測した値を記録するだけにする。
- 例外は握りつぶさず記録して伝播する。

## 検査・報告 (DW-S05-C)

- 緑には実走した command と範囲を併記する。子の実走は親の計算ノード走を代替しない。実走できなかったものは「実装済み・未実走」と書く。
- テストを甘くして緑にしない。合成入力の正例・負例は実体 (analyzer の関数) を名指しし、依存先を stub しない。
- 期待値へ揮発値 (epoch、pid、tree hash) を焼き込まない。
- 報告に: 出発点からの変更点一覧 (file ごと)、wrap 対象の現行名と signature の確認結果 (無くなった・改名された関数は明記)、runner の argv / env の組立、analyzer の出力 key 一覧、login で実走した command と結果、残る既知の限界。
- 所有外の file への波及は無いはずなので、`git status --porcelain` の出力を報告に貼って確かめる。

最後に `## 総括` 節を置き、実装状態・実走範囲・親が計算ノードで最初に確かめるべき点を 5 行以内で書け。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。
