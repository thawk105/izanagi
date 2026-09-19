単独段 dispatch: stage=consult; sandbox=read-only; parent=/home/SFC/tanab/.claude/jobs/f6bf33bb/brief.md

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/f6bf33bb/brief.md (親の段 1 brief。**攻撃対象に含む**。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f6bf33bb/rulings-verbatim.md (ユーザー裁定・D1639・D2044 項 3・失敗条件 (e)・候補 prereg・床値・A-6 先例・nodes=5 probe の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f6bf33bb/plan-out.md (段 2 の plan。攻撃対象。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/orchestrator/campaign/paper_story_a2_certification.py (読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/orchestrator/campaign/paper_story_a2_certification.v2.json (読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/orchestrator/campaign/paper_story_a6_certification.v2.json (読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/tools/pegasus/submit_paper_story_a2_certification.sh (読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/tools/pegasus/paper_story_a2_certification.sh (読めなければ即停止)

repo root は /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression。他の repo 内 file (tests、docs、output/insights) も必要なら同 root 配下を読んでよい。

# 依頼 — 段 3 敵対相談 レンズ A: 正しさ境界・受理集合・凍結 pin・整合

plan を守らず検査せよ。**親 brief 自身も検査対象である。** 反論は file:line と具体的な壊れ方を伴う real だけを挙げ、
推測は「未確認」と分けて書け。

## 攻撃の観点

1. **受理集合**: 新 study を closed set に足す変更が、任意 path・任意 shape・任意 study を受理する方向へ緩んでいないか。
   `canonical_policy_path` / `policy_shapes` / `_qsub_job_name` / `_qsub_environment_keys` の 4 箇所以外に、
   3 workload・6 cell・新 study 名を通すために**黙って緩む**箇所が plan に無いか。逆に、plan が見落として
   3 workload で fail-closed に落ちる箇所 (finish-group、collect、materialize、completion receipt の検証、
   `_validate_*`、request_ids の順序、raw manifest の cell 数、condition-gate receipt の workload 数、
   exact-qsub の `-b` 検査、`tracked_destination` の書込先検査) が無いか、module を実際に追って行番号で示せ。
2. **凍結 pin**: A-2 / A-6 の policy bytes・`protocol_sha256`・既存 attempt 成果物 (`output/insights/2026-09-07_t2364-*`、
   `2026-09-08_t2411-*`) が 1 byte も変わらないことは plan でどう担保されるか。tests の sha pin と
   `tools/plotting/plot_a2_certification.py` の pin が新 policy 追加で壊れないか。
3. **正しさ gate**: 新 policy で `legacy_correctness` / `controlled_define_base` (`CCBENCH_TRACE=0` 等) / `trace0_cmake_argv` を
   A-2 と同値にすることで、verifier (trace-enabled 別 build) → anomaly → reject の経路が rr95 でも A-6 と同じに走るか。
   規律 1 (性能値は trace-disabled) と規律 2 (anomaly = 即 reject) が新 policy で弱まる余地が無いか。
4. **identity**: 「同一 build」(brief P1) を成果物から検証できるか — 3 workload の adopted cell の `src_token` /
   `source_bytes_sha256` / configure argv が成果物 (raw cell JSON、campaign WAL の build_start、certification.json の cells[])
   のどこに現れ、親が事後に一致を確かめられるか。T-1998 prereg の target source digest (`678b7203…`) と一致する
   保証があるか、無いなら稿に何と書くべきか。
5. **A-6 先例との差**: `60605bec3` が変えた 8 file (`git show --stat 60605bec3`) のうち plan が触らないもの
   (`admission_registry.json`、`test_hooks.py`、job body) について、今回も無変更で通る根拠があるか。
6. **親 brief の実測値と一般化**: brief が書く行番号・sha・床値の全桁・A-6 の所要 (73 分)・t2489 の 12 分・「partial は exact two-workload」
   の各主張を現物で照合し、誤りや一般化しすぎを挙げよ。

## 制約

- sandbox read-only。pytest は走らせられない。静的検査でよい。テスト実測は親が行う。
- 予算が尽きそうなら途中結論を下記の出力形式どおり書いて終われ (無出力が最悪)。
- scope 外の一般化・新 gate は提案せず、必要なら「裁定パッケージ候補」に分けて返す。

## 出力形式

- `## real` (番号、file:line、壊れ方、最小修正)
- `## refuted` (plan / brief の主張で正しいと確認できたもの、根拠 file:line)
- `## 未確認` (静的に決められないもの、親の実測で確かめる方法)
- `## 裁定パッケージ候補` (無ければ「なし」)
- `## 総括` (5 行以内)
