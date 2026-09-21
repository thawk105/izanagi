単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/brief.md — 親 brief (13:45 の追補を含む最新版)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/codex/s2-plan.md — 段 2 のプラン (攻撃対象)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/verbatim/T-2830-origin.md — 依頼の逐語 (「本題だけ。gate・検査・台帳の追加は scope 外」)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/verbatim/d2199.md — D2199 の逐語。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/verbatim/insight-6-3.md — 試走の所要実測。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/verbatim/insight-8.md — 裁定パッケージ (§8.4 項 6 が cache 公開競合)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/tools/pegasus/p3_s4_loop_pegasus.sh — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/tools/pegasus/b5_contrast_launch.py — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/tests/test_p3_s4_loop_job_contract.py — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/tests/test_b5_contrast_launch.py — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/campaign/p3_s4_loop.py — cache root の決定 (`isolate_worktree` 分岐)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/campaign/buildcache.py — `_acquire_v2_claim` と公開経路。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/campaign/b5_generator_contrast.py — 系列開始 stock の build 順序。読めなければ即停止

## レンズ B: 過剰・削除 (研究前進に要る最小か)

プランを守らせず検査する。**親 brief 自身も検査対象**である。依頼は「本題だけ。gate・検査・台帳の追加は scope 外」。
研究前進 (B-5 本走を認可後すぐ投入できる状態にする) に要らないものを削り、局所修正で足りるものを指摘する。
**親自身の実測値とその一般化**を疑う。各項目を real (過剰・誤り) / refuted (必要) で判定し、根拠 (file:line) を示す。

1. **(P2) の根拠:** brief は「node-local lock で build の同時性が上がるため、検査だけでは本走が fail-closed で落ちる」と言う。
   build は bench lock の外で走るか。試走の 4 job はほぼ同時に始まった (insight §6.1) — それでも落ちなかった機序は何か
   (系列開始 stock build の claim が衝突しなかったのは時刻差か、cache hit か)。lock を node-local にすると build の同時性は本当に上がるか。
   上がらないなら、job ごとの submit-tree は本走に必要か、それとも D2199 の「一般保証ではない」だけが根拠か。
   必要と判定する場合も、その根拠を brief の一般化から実コードの機序へ差し替えて示す。
2. **新しい検査の混入:** プランは `validate_submit_tree` に `previous_trees` (path 重複・common repo 不一致の拒否) を足す。
   これは依頼の「検査の追加は scope 外」に当たるか。「job ごとの submit-tree」を成立させる最小条件 (同じ path を 4 回渡されたら
   共有に戻る) として必要か。common repo 不一致の拒否は本題に要るか。要らないなら削除案を示す。
3. **test の重複:** プランは既存の argv 完全一致比較に加えて、NUL 区切り bytes を別 file に記録して比較する。既存比較で
   「argv・bytes 不変」は既に固定されているか。追加は冗長か。
4. **継承値の test:** `test_job_preserves_or_overrides_inherited_bench_lock` (非 B-5 は入力の `IZANAGI_BENCH_LOCK` を保持) は必要か。
   launcher は `qsub -v` で env を明示列挙する — 継承経路は実在するか。
5. **CLI 形:** `--repo-root-<arm>` 4 本必須と、単一 `--repo-root` fallback 無し。既存の試走手順 (insight §6.1、job dir の
   `submit_pilot.py` が API を import した) と `tools/pegasus/README.md` の記載との整合で、より小さい変更はあるか。
6. **削れる変更:** プラン全体で、B-5 本走の実行可能性に寄与しない変更 (互換層・一般化・防御的検査) を列挙し、削除案を示す。

## 制約

- sandbox は read-only で書込可能な tmp が無い。**静的検査だけでよい。** テスト実走は親が行う。実走していないことを「確認した」と書かない。
- 新しい gate・検査・台帳を提案する場合は、依頼の scope 外であることを明記し、裁定パッケージ候補として分けて返す。
- 予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終える。

## 出力形式

項目 1〜6 を見出しで分け、各項目に判定 (real / refuted) と根拠を書く。削除・縮小案は「残す最小の差分」として具体的に書く。
最後に `## 総括` を置く。
