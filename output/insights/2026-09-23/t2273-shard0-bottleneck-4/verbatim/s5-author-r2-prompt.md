単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-acceptance-bottleneck-diag

必読事項の射影:
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/s4-ruling.md — 段 4 裁定。**「追補 1」の「R2 の事前登録」が仕様の正本**。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/codex/s5-author-out.md — あなた (前巡) の実装報告。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe/tools/t2273_replica_runner.py、t2273_replica_plugin.py、t2273_replica_analyze.py — 前巡の実装 (計算ノードで R1 を 1 走完走済み。R1 の出力は /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/job-out-r1/ と analysis/r1.json)。これを改める。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe/orchestrator/tests/test_s8b_oracle_driver.py — `_copy_git_visible_output` (847 行付近) と、それが source_root に対して行う git 呼出し (`_run_git_bytes`、ls-files の引数)・ignore 関数・copytree。staged root で同じ可視集合になる条件をここで確かめる。読めなければ即停止。

## 役割と所有

[T-2273] 診断 wave の段 5 実装子 (Codex role=author、workspace-write)、R2 用の追加実装。作業 worktree は `/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe` (branch `author-t2273-probe-r2`、前巡の commit の上)。所有 path は前巡と同じ 3 file (`tools/t2273_replica_runner.py` / `tools/t2273_replica_plugin.py` / `tools/t2273_replica_analyze.py`) だけで、他は 1 byte も変えない。docs・テスト・conftest・既存 tools は編集しない。`docs/handoff/` へ file を作らない。`git add` / `git commit` をしない。

## 何を足すか (R2 の事前登録どおり。R1 用の既存の挙動は壊さない)

1. **runner に `pair` mode を足す** (既存の `run` mode はそのまま残す): 同一 job 内で smoke → A2 → staging → X を順に行う。A2 と X はどちらも R1 の A 走と同じ argv・env (受入 shard-0 相当、`acceptance_shards.create_session(repo, 3)` で別 session を 1 つずつ) で、出力は `<out>/A2/` と `<out>/X/`。各走の前後に単独性・loadavg・clean を記録。smoke 失敗・clean でない・A2 の rc≠0 なら X へ進まず `incomplete.json`。資源標本は A2 と X の両方で取る。walltime 00:50:00 に対し alarm は 2900 秒。
2. **staging (A2 の後、X の前):** `$TMPDIR` (継承値) 配下に staged repo を作る。実 repo の git admin (shared `.git`) に worktree を登録しない・実 repo へ一切書かない。方法は例えば `git clone --no-local --no-checkout <repo root> <staged>` (または `--shared` を使わない local clone) + `git -C <staged> checkout <repo の HEAD SHA> -- output` 相当で、**staged root で `_copy_git_visible_output` が返す可視 path 集合が実 repo root で返す集合と同一になること**を目標にする。実 repo の `output/` に untracked の可視 file (ls-files --others --exclude-standard) が 1 件でもあれば staging 後に同じ bytes で写すか、写さずに X を無効として止める (どちらかを選び理由を報告)。`.gitignore` 系の規則が staged 側で同じになるかをコードで確かめる。staging の開始・終了・壁時間・file 数・使った command を `<out>/staging.json` に記録。
3. **plugin の対照差し替え:** env `T2273_LOCAL_OUTPUT_SOURCE=<staged root>` があるときだけ、`_copy_git_visible_output(source_root, destination)` の呼出しで `source_root` が実 repo root (resolve して比較) のときに限り、**実関数を** `(staged_root, destination)` で呼ぶ。それ以外の呼出しは実引数のまま。span の `extra` に `substituted: true/false`・元の source_root・staged root を記録。A2 ではこの env を渡さない。差し替えは「対照用の差し替えであり観測 wrapper ではない」と plugin の docstring とspan に明記。受理集合・deselect・skip・hold・順序・verifier・台帳には触れない。
4. **可視集合の同一性:** plugin は `_copy_git_visible_output` の戻り値 (可視 path 集合) の件数と、sorted 集合の sha256 を span の `extra` に記録する。analyzer が A2 と X の全 builder でこれが一致するかを判定する。
5. **analyzer に対比較を足す:** `--pair-dir <out>` (A2 と X と staging.json を読む) で、事前登録の判定量 — W_0 / O_max (worker) / L (worker) / pre / post の A2・X・差 (A2 − X)、builder ごとの build・copy・copy.list・copy.copytree・git・issue の A2・X・差、最大占有 worker の排他分解 (A2 と X)、X での最大占有 worker と最大成分、staging の壁時間、ΔW_0 と ΔW_0/W_0(A2)、D357 の 1 走比較の区分 (10 % 以上 / 未満)、有効性 (rc・outcome 集合一致・可視集合 digest 一致・clean・others・record-error) — を markdown と json に出す。既存の単走 analyze (`--run-dir`) は保つ。
6. 合成入力で対比較の正例 (A2・X の小さい run dir を作り差が期待どおり) と負例 (可視集合 digest 不一致で X 無効、outcome 集合不一致で無効) を走らせる。login で走らせられる範囲 (`--help`、hostname 防壁 rc 3、staging の関数を小さい一時 git repo に対して走らせて可視集合が一致すること) を実際に走らせる。

## 不変条件・検査・報告 (DW-S05-C)

- 固定値 (HEAD、件数 29,885、R1 の path) を焼き込まない。観測値を記録するだけ。例外は記録して伝播。
- 緑には実走した command と範囲を併記。子の実走は親の計算ノード走を代替しない。実走できなかったものは「実装済み・未実走」。
- テストを甘くしない。合成正例・負例は analyzer の実関数を名指しし依存先を stub しない。
- 報告に: 変更点一覧 (file ごと)、staging の方法と「同一可視集合」になる根拠 (コードの行)、pair mode の argv/env、analyzer の追加出力 key、login で実走した command と結果、`git status --porcelain`、残る限界 (X が後走の warm を受ける偏り等)。

最後に `## 総括` 節で、実装状態・実走範囲・親が計算ノードで最初に確かめるべき点を 5 行以内で書け。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。
