単独段 dispatch: stage=plan; sandbox=read-only; parent=/home/SFC/tanab/.claude/jobs/f6bf33bb/brief.md

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/f6bf33bb/brief.md (親の段 1 brief。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f6bf33bb/rulings-verbatim.md (ユーザー裁定・D1639・D2044 項 3・失敗条件 (e)・候補 prereg・床値・A-6 先例 commit message・nodes=5 probe の逐語。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/orchestrator/campaign/paper_story_a2_certification.py (対象 module。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/orchestrator/campaign/paper_story_a2_certification.v2.json (A-2 policy。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/orchestrator/campaign/paper_story_a6_certification.v2.json (A-6 policy。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/tools/pegasus/submit_paper_story_a2_certification.sh (投入器。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/tools/pegasus/paper_story_a2_certification.sh (job body。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/orchestrator/tests/test_paper_story_a2_certification.py (tests。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/orchestrator/tests/test_paper_story_a2_job_contract.py (tests。読めなければ即停止)

repo root は /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression である。上記以外の repo 内 file も必要なら同 root 配下を読んでよい (git 履歴は `git -C` 不可、`git log`/`git show` は同 root で cd なしに実行できる範囲で)。

# 依頼 — 段 2 プラン起草 (read-only、file:line 粒度)

brief の scope A (実装面) について、Codex author が 1 本で実装できる **file:line 粒度の plan** を起草せよ。
scope B (投入・回収) と C (docs) は親が担うので、plan には「親が投入時に確認すべき前提」だけを列挙する。

## plan に必ず含めるもの

1. **新 policy JSON の全文案** (`orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json`)。A-2 v2.json を土台に、brief の指定値で埋める。`_exact_keys` が要求する key 集合 (module の `_POLICY_KEYS` 等) と、`load_policy` の各検証 (`workload identity`, `cell role pairs`, `adopted_backoff_us` と cell genome の整合検査があるか、`tracked_destination` / `durable_measurement_base` の形式検査) を module の該当行で確認し、通る根拠を行番号で示す。
2. **module の変更点** を行番号つきで: `B7_FIXED5_POLICY_PATH` 定数、`canonical_policy_path` の closed set、`_qsub_job_name`、`_qsub_environment_keys`、`policy_shapes`。**それ以外に study 名・policy path・workload 数・cell 数を前提にしている箇所が無いか** module 全体を検索して列挙せよ (例: `collect`/`finish_group`/`_validate_completion_receipt`/`_partial_*`/`materialize`/`exact-qsub` の `-b` nodes 検査/`_protocol_preimage`/`tracked_destination` の書込先検査/`test_token`)。3 workload・6 cell で全 workload 成功した場合に `finish-group` → `collect` が通る経路を行番号で追い、通らない箇所があれば最小変更を示せ。partial 完了 (exact two-workload) は変えない。
3. **submitter の変更点**: `IZANAGI_A2_POLICY_PATH` を渡す条件 (:263 付近) と、他に study 名を前提にする箇所。`finish-group` 側の経路も確認。job body は無変更で通るかを `POLICY_SELECTION` の流れで確認。
4. **tests の変更点**: 既存 test で新 study の追加により赤になるもの (closed set の件数、job 名の集合、param id など) を列挙し、正例 (新 policy が load でき shape (3,6)・job 名・env key が期待どおり) と負例 (新 policy を 1 key 崩すと拒否、非 canonical path 拒否は不変) の最小追加を示す。A-6 追加 commit `60605bec3` のテスト差分を `git show 60605bec3 -- orchestrator/tests/` で参照して同形にせよ。
5. **不変条件の検証法**: A-2 / A-6 policy の bytes・`protocol_sha256` が変わらないことを author 後に親がどう確かめるか (test の sha pin を挙げる)。
6. **親の投入前提の確認項目**: `durable_measurement_base` の dir 作成が必要か (preregister が作るか)、`tracked_destination` の事前存在が拒否されるか、attempt-id の形式、`--policy` に渡す path の形 (repo 相対 / 絶対のどちらが canonical 判定を通るか)、hydrate 先、`scheduler.nodes=5` で `exact-qsub` が `-b 5` を受理するか。
7. **リスク・未確定**: 不明点は推測でなく「未確認」と書く。

## 制約

- sandbox は read-only で pytest を走らせられない。静的検査でよい。テスト実測は親が行う。
- 予算が尽きそうなら途中結論を下記の出力形式どおり書いて終われ (無出力が最悪)。
- 実装面の scope を広げない: 新 gate・partial の一般化・plotter・A-2/A-6 policy の変更・job body の変更は提案しない (必要と判明した場合は「裁定パッケージ候補」として別節に分けて返す)。

## 出力形式

- `## 変更面` (file:line の表)
- `## 新 policy 案` (JSON 全文)
- `## 経路確認` (finish-group / collect / materialize が 3 workload で通る根拠)
- `## tests`
- `## 親の投入前提`
- `## 裁定パッケージ候補` (scope 外だが必要なもの、無ければ「なし」)
- `## 総括` (5 行以内)
