## 変更点

- [paper_story_a1_paired.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2301-a1-study-id-required/orchestrator/campaign/paper_story_a1_paired.py:3221)
  - 3221行: `run_submit` を `args.study_id` の直接参照へ変更。
  - 8588行: `submit --study-id` を `required=True` へ変更。
  - 8632行のまま。7103行の campaign sink も不変。
  - scope 外の `complete` と `load_policy` は未変更。

- [paper_story_a1_paired.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2301-a1-study-id-required/tools/pegasus/paper_story_a1_paired.sh:37)
  - 旧37行の legacy 既定代入を削除。
  - 現41行の v2 case に `EXPECTED_STUDY_ID="$REQUESTED_STUDY_ID"` を追加。
  - 1347行のまま。

- [test_paper_story_a1_job_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2301-a1-study-id-required/orchestrator/tests/test_paper_story_a1_job_contract.py:1206)
  - 1208〜1209行: 既定代入が存在しないことと case 内代入3件を pin。
  - 1290行: legacy ID の出現数を1件へ更新。
  - 1541〜1552行: study ID 環境変数欠落の負例を追加。
  - 2030〜2477行の17 legacy `run_submit` 呼出しへ `paired.STUDY_ID` を明示。
  - 2844行から2874行へ増加。

- [test_paper_story_a1_paired.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2301-a1-study-id-required/orchestrator/tests/test_paper_story_a1_paired.py:4028)
  - 4028〜4067行: parser 負例、3 study の正例、`run_submit` fail-closed 負例を追加。
  - 4140行から4181行へ増加。

JSON、docs、version control への書込みは行っていません。変更は指定された4ファイルのみです。

## 足した test

- `orchestrator/tests/test_paper_story_a1_job_contract.py::test_production_job_rejects_missing_study_id_before_creating_roots`
  - job body の環境変数欠落を rc=2、`study ID differs`、attempt root 未作成で固定。

- `orchestrator/tests/test_paper_story_a1_paired.py::test_submit_parser_rejects_missing_study_id_M1`
  - M1 を kill。

- `orchestrator/tests/test_paper_story_a1_paired.py::test_submit_parser_accepts_each_explicit_study_id`
  - legacy、v3-pilot、v3-sized の過剰拒否防止正例。単一 test 内で3値を検査するため parameter suffix はありません。

- `orchestrator/tests/test_paper_story_a1_paired.py::test_run_submit_rejects_missing_study_id_attribute_M2`
  - M2 を kill。

M3 は既存の次の node を更新して diagnostic pin としました。

- `orchestrator/tests/test_paper_story_a1_job_contract.py::test_job_body_contains_all_m12_gates_and_no_submitter`

## 実走

- 3 Python file の `ast.parse`: rc=0。
- `bash -n tools/pegasus/paper_story_a1_paired.sh`: 同一 argv を Python subprocess から起動して rc=0。直接の shell 形式は `guard_bash` が構文検査前に遮断しました。
- 追加4 test と更新した source pin 2 test の直接実行: 6件通過。
- 明示 study ID を補った既存 legacy `run_submit` test: 13関数を直接実行し全件通過。
- AST による全 `run_submit(SimpleNamespace(...))` 検査: 意図した M2 負例以外の `study_id` 省略は0件。
- `git diff --check`: rc=0。
- 変異確認:
  - M1: rc=1、`DID NOT RAISE SystemExit`。
  - M2: rc=1、既定へ退避して後段の `PaperStoryError` に到達。
  - M3: rc=1、禁止した既定代入 literal の assertion で赤化。
  - 各変異は検査直後に復元済み。
- full pytest: ログインノード `pegasus02` の提示済み dispatch 制約により、実装済み・未実走。
- policy:
  - v2 SHA256: `83b9c1a1ca4cce1e6394ce3338b491b14663427259eb3e129560fe5b50b99b5b`
  - v3-pilot SHA256: `ed1c942f9d4bc24ab1bc6106caea672262c8634d32b022eca75b125811f7b825`
  - `paper_story_a1_paired.v3-sized.json` は着手前から存在せず、作成していません。

## 波及

- `main` から `run_submit` への経路だけが driver の実 caller。CLI と内部関数の両方が fail-closed になりました。
- job body は3つの case 全てで requested ID を expected ID へコピーします。末尾の driver 呼出しも引き続き `--study-id "$EXPECTED_STUDY_ID"` を明示します。
- `test_ccbench_spawn_sites.py` の7103行 pin は維持されています。
- `test_campaign.py`、`test_hooks.py`、`test_official_perf_closure.py`、admission registry、headline test の参照は path・分類・AST 契約で、今回変更した既定 literal や固定 SHA の追加更新は不要でした。
- 既存 legacy `run_submit` consumer 17箇所は全て所有対象内で明示 ID へ追随済み。v3 consumer は既に明示済みでした。

指定された `rg` の最終結果です。

```text
tools/pegasus/paper_story_a1_paired.sh:40:  paper-story-a1-20260826-sized-v1)
tools/pegasus/paper_story_a1_paired.sh:41:    EXPECTED_STUDY_ID="$REQUESTED_STUDY_ID"
tools/pegasus/paper_story_a1_paired.sh:45:    EXPECTED_STUDY_ID="$REQUESTED_STUDY_ID"
tools/pegasus/paper_story_a1_paired.sh:50:    EXPECTED_STUDY_ID="$REQUESTED_STUDY_ID"
tools/pegasus/paper_story_a1_paired.sh:78:[[ "${IZANAGI_A1_STUDY_ID:-}" == "$EXPECTED_STUDY_ID" ]] || refuse "study ID differs"
tools/pegasus/paper_story_a1_paired.sh:321:    "$REPO_ROOT/$POLICY_RELATIVE" "$EXPECTED_STUDY_ID" <<'PY'
tools/pegasus/paper_story_a1_paired.sh:389:    "$EXPECTED_STUDY_ID" \
tools/pegasus/paper_story_a1_paired.sh:525:    "$EXPECTED_STUDY_ID" "$IZANAGI_EXPECTED_HEAD" "$PBS_JOBID" \
tools/pegasus/paper_story_a1_paired.sh:568:  "$EXPECTED_STUDY_ID" "$IZANAGI_EXPECTED_HEAD" "$PBS_JOBID" \
tools/pegasus/paper_story_a1_paired.sh:928:  "$PYTHON_BIN" - "$TERMINAL_PATH" "$REPO_ROOT" "$EXPECTED_STUDY_ID" \
tools/pegasus/paper_story_a1_paired.sh:1335:  --study-id "$EXPECTED_STUDY_ID" \
orchestrator/tests/test_paper_story_a1_job_contract.py:1208:    assert 'EXPECTED_STUDY_ID="paper-story-a1-20260826-sized-v1"' not in source
orchestrator/tests/test_paper_story_a1_job_contract.py:1209:    assert source.count('EXPECTED_STUDY_ID="$REQUESTED_STUDY_ID"') == 3
orchestrator/tests/test_paper_story_a1_job_contract.py:1224:        '--study-id "$EXPECTED_STUDY_ID"',
orchestrator/tests/test_paper_story_a1_job_contract.py:1290:    assert source.count("paper-story-a1-20260826-sized-v1") == 1
orchestrator/tests/test_paper_story_a1_job_contract.py:1308:    assert 'study_id != "paper-story-a1-20260826-sized-v1"' not in source
orchestrator/campaign/paper_story_a1_paired.py:91:STUDY_ID = "paper-story-a1-20260826-sized-v1"
orchestrator/campaign/paper_story_a1_paired.py:4225:    study_id = getattr(args, "study_id", STUDY_ID)
orchestrator/campaign/paper_story_a1_paired.py:8610:    complete.add_argument("--study-id", default=STUDY_ID)
orchestrator/campaign/wal.py:112:        "paper-story-a1-20260826-sized-v1",
orchestrator/tests/test_p3_exploration_namespace.py:317:        "--study-id", "paper-story-a1-20260826-sized-v1",
orchestrator/tests/test_a1_non_certifying_marker.py:18:    "paper-story-a1-20260826-sized-v1",
orchestrator/tests/test_a1_non_certifying_marker.py:45:        "paper-story-a1-20260826-sized-v1",
orchestrator/tests/test_campaign_lock_codec.py:63:        "study_id": "paper-story-a1-20260826-sized-v1",
orchestrator/campaign/paper_story_a1_paired.v2.json:129:  "study_id": "paper-story-a1-20260826-sized-v1",
orchestrator/tests/test_trial_registry.py:3620:        study_id="paper-story-a1-20260826-sized-v1",
orchestrator/campaign/ident.py:40:        "paper-story-a1-20260826-sized-v1",
orchestrator/tests/test_artifact_admission.py:1813:            "study_id": "paper-story-a1-20260826-sized-v1",
orchestrator/tests/test_artifact_admission.py:1819:        "trial": "paper-story-a1-20260826-sized-v1",
orchestrator/tests/test_artifact_admission.py:1824:        "study_id": "paper-story-a1-20260826-sized-v1",
```

## 総括

`submit` は study ID の明示がなければ argparse で拒否され、内部 caller も属性欠落時に legacy study へ退避しません。legacy、v3-pilot、v3-sized を明示した場合は引き続き受理され、job body の環境変数欠落も attempt root 作成前に拒否されます。

残課題は full pytest の計算ノード実走です。親は `complete --study-id` の既定、`run_complete` の既定退避、`load_policy` の既定がD1619の範囲外として残っている点を報告し、commit 時に provenance 規約どおり Codex author trailer を付与してください。