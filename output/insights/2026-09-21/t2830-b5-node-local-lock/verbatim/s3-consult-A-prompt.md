単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/brief.md — 親 brief (13:45 の追補を含む最新版)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/codex/s2-plan.md — 段 2 のプラン (攻撃対象)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/verbatim/T-2830-origin.md — 依頼の逐語。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/verbatim/d2199.md — D2199 の逐語。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/verbatim/d2205.md — D2205 の逐語。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/tools/pegasus/p3_s4_loop_pegasus.sh — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/tools/pegasus/b5_contrast_launch.py — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/tests/test_p3_s4_loop_job_contract.py — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/tests/test_b5_contrast_launch.py — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/campaign/lock.py — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/campaign/pipeline.py — bench_lock の取得箇所。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/campaign/verify_fanout_worker.py — `IZANAGI_BENCH_LOCK` を一時的に書き換える箇所。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/campaign/b5_generator_contrast.py — B-5 driver。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/docs/failures.md の F3 (見出し「F3. 計測前の単独性未確認」) — 読めなければ即停止

## レンズ A: 正しさ境界・整合・実効性

プランを守らせず検査する。**親 brief 自身も検査対象**である。brief の file:line、前提、所有範囲、変異の帰属不成立、
**親自身の実測値とその一般化**を疑う。次を必ず検査し、各項目を real (欠陥あり) / refuted (欠陥なし) で判定して根拠 (file:line) を示す。

1. **lock の被覆:** B-5 driver 直前の export だけで、B-5 mode の全 bench lock 取得 (performance verify pass 5 rep と bench) を覆うか。
   `b5_generator_contrast.py` が p3_s4_loop を subprocess で起動する経路で環境が伝わるか。`verify_fanout_worker.py` が lock path を
   上書きする経路は B-5 で通るか、通るならその上書きが node-local 化を無効にしないか。親の実測「bench lock は driver 内部でだけ取る」は正しいか。
2. **規律 2 (正しさゲートを緩めない):** lock の所在変更が correctness verify (trace 走行 + verifier) の排他や判定に影響しないか。
   performance tag の verify pass が lock 下で回る構造は保たれるか。
3. **F3 [計測汚染] の型:** `$TMPDIR/bench.lock` は job ごとの path で、同一ノードの別 job とは排他しない。brief の前提
   (gen_S は 48/48 割当てで自分の request が同居しない、専有はスケジューラ保証外) で、node-local 化が計測汚染を新たに生むか。
   B-10 / A-5 の先例との差はあるか。home 共有 lock は試走で別ノードの job を直列化していた — その直列化に正しさ上の意味があったか
   (あったなら node-local 化は計測の独立性を壊す)。
4. **既存 3 経路の不変の実効性:** プランが「既に全 argv の順序付き比較がある」と言う test (`test_default_job_invokes_driver_once`、
   `test_pair_job_invokes_one_driver_with_both_modes`、`test_complete_k2_environment_reaches_actual_job_driver_argv`) は本当に
   3 経路それぞれで driver argv の完全一致を検査しているか (部分一致・`in` 検査で終わっていないか)。行番号を示す。
5. **launcher の実効性:** `runner(argv, cwd=tree.repo)` と相対 `JOB_BODY` の組で、各 job が自分の tree の job body を投入するか。
   `IZANAGI_S4_REPO_ROOT` と qsub の cwd が食い違う経路はないか。4 本の tree が同じ HEAD でも、CCBench submodule・cache root・
   `patchharness.checkout` の base が tree ごとに分かれるか。
6. **D2205 の維持:** pair mode・認可 session・結合検査に触れていないか。
7. **[恒真ゲート] / [テスト代表性]:** プランの test と変異候補 (§6) は、欠陥があるとき実際に落ちるか。fake driver の harness は
   実 flock を検査しない — その限界の下で「node-local lock が効く」ことを test が主張しすぎていないか。変異の帰属 (どの test が殺すか) が
   成立しない候補はどれか。

## 制約

- sandbox は read-only で書込可能な tmp が無い。**静的検査だけでよい。** テスト実走は親が行う。実走していないことを「確認した」と書かない。
- 新しい gate・検査・台帳を提案する場合は、依頼の scope 外であることを明記し、裁定パッケージ候補として分けて返す。
- 予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終える。

## 出力形式

項目 1〜7 を見出しで分け、各項目に判定 (real / refuted) と根拠を書く。real には must-fix / nit の別と、放置時に成果物
(B-5 本走の台帳・score・certified 判定) がどう変わるかを 1 行で添える。最後に `## 総括` を置く。
