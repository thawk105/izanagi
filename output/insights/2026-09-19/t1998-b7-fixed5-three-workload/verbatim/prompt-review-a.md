単独段 dispatch: stage=review; sandbox=read-only; parent=/home/SFC/tanab/.claude/jobs/f6bf33bb/ruling-s4.md

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/f6bf33bb/ruling-s4.md (段 4 裁定 = plan v2・所有・変異事前登録。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f6bf33bb/brief.md (段 1 brief。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f6bf33bb/author.patch (author の差分全文 = レビュー対象。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f6bf33bb/author-out.md (author の最終報告。pytest は sandbox の qstat 不在で未実走と申告。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f6bf33bb/tests-focus-1.log (親の実走: 対象 2 test file、307 passed、login bounded local。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f6bf33bb/tests-meta-1.log (親の実走: meta-test 5 file、1071 passed / 6 skipped、計算ノード dispatch。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/orchestrator/campaign/paper_story_a2_certification.py (適用後の module。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json (新 policy。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/tools/pegasus/submit_paper_story_a2_certification.sh (適用後の submitter。読めなければ即停止)

repo root は /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression (HEAD c18a80967 = 実装 commit)。tests・他 file も同 root 配下を読んでよい。

# 依頼 — 段 6 敵対レビュー レンズ A: 正しさ境界・受理集合・pin・テストの検出力

author の差分を守らず攻撃せよ。所見は file:line と具体的な壊れ方を伴う real だけを挙げ、推測は「未確認」に分ける。

## 観点

1. **受理集合**: closed set の拡張が「新 policy 1 path の追加」を超えて緩んでいないか (任意 path・任意 study・任意 shape・非 canonical path の受理)。`canonical_policy_path` / `policy_shapes` / `_qsub_job_name` / `_qsub_environment_keys` / submitter の 2 条件の各変更を行単位で検査。
2. **凍結 pin と既存成果物**: A-2 / A-6 の policy bytes・protocol_sha256・既存 test の期待値・pin が変わっていないか (`git diff 657e1e5a7 c18a80967 --stat` と各 hunk)。既存 test の反転・緩和・skip・削除が無いか。
3. **テストの検出力**: 新テストが実体を名指しているか (実 policy file、実 `load_policy`、実 submitter を wrapper 越しに実行しているか)、fixture が単一理由か、期待値へ揮発 payload を焼いていないか、`_test_token` bypass を使っていないか。特に `test_b7_full_collect_materializes` が本当に 6 cell・3 effects・18 members・COMPLETE.json を機構経路で作っているか、`test_b7_partial_boundary` が exact two-workload 境界を実際に叩いているか、`test_b7_submitter_three_requests` が実 bash submitter の argv/receipt を検証しているか。
4. **変異事前登録 (ruling-s4.md の M1〜M8) の期待 node**: 各変異について、赤になる test nodeid の**完全集合**を静的に導け (author は sandbox で実走できなかった)。単一理由性 (同じ入力を拒否する層が前後に無い) が崩れる変異があれば指摘。M6/M7 (submitter shell 側) を検出する test node を名指しせよ。
5. **3 workload の実行経路**: 適用後の module で finish-group → collect → materialize が 3 workload・6 cell で通ることを、test だけでなく行番号で追って確認 (request_ids 順序、raw manifest 件数、condition receipt 数、fresh destination)。
6. **正しさ gate**: 新 policy の `controlled_define_base` (`CCBENCH_TRACE=0`) / `legacy_correctness` / trace0 argv が A-2 と同値で、anomaly → reject の経路が rr95 でも走ることを確認。

## 制約

- read-only。pytest は走らせられない。静的検査でよい。親の実走 log は上記 2 本。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。
- scope 外の一般化・新 gate は提案せず「裁定パッケージ候補」に分ける。

## 出力形式

- `## must-fix` (番号、file:line、壊れ方、最小 fix)
- `## should-fix` (放置しても成果物の値・受理集合・参照を変えないもの)
- `## refuted` (確認できた正しい点、根拠)
- `## 変異の期待 node` (M1〜M8 ごとの nodeid 完全集合、未確定は理由)
- `## 裁定パッケージ候補` (無ければ「なし」)
- `## 総括` (5 行以内)
