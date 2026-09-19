単独段 dispatch: stage=author; sandbox=workspace-write; parent=/home/SFC/tanab/.claude/jobs/f6bf33bb/ruling-s4.md

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/f6bf33bb/ruling-s4.md (段 4 裁定 = plan v2・所有・変異事前登録。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f6bf33bb/plan-out.md (段 2 plan。変更面・新 policy 全文・tests の設計。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f6bf33bb/brief.md (段 1 brief。scope・不変条件。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f6bf33bb/consult-a-out.md (段 3 レンズ A。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/f6bf33bb/consult-b-out.md (段 3 レンズ B。読めなければ即停止)

**作業する repo root は /work/1/SFC/tanab/izanagi/.codex/worktrees/t1998-author である** (branch `impl-dev-wave-t1998-three-workload-regression`、HEAD = local main 657e1e5a7)。この root の外へ書かない。

# 依頼 — 段 5 実装 (Codex author、1 本)

ruling-s4.md の「plan v2」と plan-out.md の「変更面」「新 policy 案」「tests」を実装せよ。

## 所有 (これ以外の path を編集しない)

- `orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json` (新規。plan-out.md の JSON 全文をそのまま使う)
- `orchestrator/campaign/paper_story_a2_certification.py`
- `tools/pegasus/submit_paper_story_a2_certification.sh`
- `orchestrator/tests/test_paper_story_a2_certification.py`
- `orchestrator/tests/test_paper_story_a2_job_contract.py`

所有外 (触らない): `tools/pegasus/paper_story_a2_certification.sh` (job body)、`paper_story_a2_certification.v2.json`、`paper_story_a6_certification.v2.json`、`tools/pegasus/admission_registry.json`、`tools/plotting/*`、`docs/**`、他の tests。docs 編集・commit をしない (commit は親)。

## 変更点 (plan-out.md の表を正とし、次を加える)

1. module: `B7_FIXED5_POLICY_PATH` 定数、`canonical_policy_path` の closed set、`_qsub_job_name` (`paper-b7-fixed5`)、`_qsub_environment_keys` (新 study も `IZANAGI_A2_POLICY_PATH` を要する側)、`policy_shapes` (`(3, 6)`)。`canonical_policy_path` の docstring と `--policy` の help の「two」→「three」(文言のみ)。**それ以外の関数・partial 境界 (exact two-workload) は変えない。**
2. submitter: **`S:273` と `S:365` の 2 箇所**とも新 study で `IZANAGI_A2_POLICY_PATH` を渡す (片方だけでは submission receipt 検証が落ちる)。
3. tests: plan-out.md「tests」の 1〜7 (新 fixture `_b7_fixed5_policy`、policy literal 正例 (shape/順序/label/rratio/adopted 5/6 cell/scheduler/2 destination/job 名/env 集合 9 key)、closed set・CLI 正例、負例 (adopted genome 不整合・未知 key・shape 不足・非 canonical path 拒否)、全件 finish→collect→materialize (6 cell・3 effects・18 raw manifest members・COMPLETE.json、`_test_token` 不使用、全 arm 正常と `adopted_gain < 1` の両 param)、partial 不変 (B7 の 1/2 成功で manifest null・exact two-workload 拒否)、submitter 3 request 契約 (`-b 5`/12h/`paper-b7-fixed5`/POLICY_PATH env/同じ `--policy` の伝播)、study ごとの重複検出)。既存 test の期待値・既存 pin (A-2 `f8a7780600766e6c8e0248ae0e3aff70a2e1c28150f8932842cdbf67f988472c`、A-6 `682e0f4ed980b74d509426d8f074f51f5b8062a1ca7cf82cd8dbbaae93c4446a`、protocol `d99f08bc…` / `21427e71…`) は変えない。新 policy の bytes sha を pin するなら literal を 1 箇所に置く (A-6 と同形)。
4. 受理集合は「新 policy の 1 path を closed set へ足す」以外に変えない。任意 path・任意 shape・任意 study を受理する方向の変更は禁止。scope 前の現行挙動 (A-2 既定、A-6 明示、他 path 拒否) を報告に明記する。

## 検査・報告 (必ず全部)

- `python3 tools/run_tests.py orchestrator/tests/test_paper_story_a2_certification.py orchestrator/tests/test_paper_story_a2_job_contract.py` を実走し、緑には実走 nodeid・件数を併記する (子の実走は親の全走を代替しない。実走不能なら `closed` でなく「実装済み・未実走」と書く)。
- テスト新設・改名は親の名指しを網羅と見なさず、制約 meta-test (例: `test_hooks.py`、`test_ccbench_spawn_sites.py` の call 数 pin、`test_official_perf_closure.py`) を自ら洗い出して走らせる。新しい spawn/subprocess 呼出しを module に足さないこと。
- fixture への現行 hash 差し込み等、テストを甘くして緑にしない。正例・負例は実体 (実 policy file、実 `load_policy`、実 submitter wrapper) を名指しし、依存先を stub しない。
- 期待値へ揮発 payload (tree hash、tmp path 等) を焼き込まない。
- 報告に所有外 caller・共有 fixture・consumer test への波及を静的列挙する (例: `tools/plotting/plot_a2_certification.py`、`test_plot_a2_certification.py` は無変更で緑か)。
- 変異事前登録 (ruling-s4.md の M1〜M8) について、各変異を**手元で一時適用→当該 test を実走→復元**し、赤になる nodeid の完全集合を報告せよ (これが親の変異 matrix の期待 node になる)。M6/M7 (submitter の shell 側) が test から検出できない場合はその旨を書く。適用後は必ず元に戻し、`git diff` に変異が残っていないことを確認する。
- 最後に `git status --short` と `git diff --stat` を報告に貼る。

## 出力形式

- `## 変更面` (file:line、何をどう変えたか)
- `## 受理集合` (scope 前の挙動と scope 後の挙動、緩めていないことの根拠)
- `## テスト実走` (command、nodeid、件数、赤があれば内訳と帰属)
- `## 変異の実測` (M1〜M8 ごとの赤 nodeid 完全集合、SURVIVED は理由)
- `## 波及` (所有外への静的列挙)
- `## git status / diff --stat`
- `## 総括` (5 行以内)
