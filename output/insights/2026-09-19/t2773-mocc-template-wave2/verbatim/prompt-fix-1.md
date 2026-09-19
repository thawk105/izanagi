単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2773-mocc-template-wave2

## 必読事項の射影

次の絶対パスを読む。読めなければ即停止し、読めなかったパスを `## 総括` に書いて終わる。

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2773-mocc-template-wave2/wave-artifacts/s6-ruling.md (段 6 裁定。F1 / F2 が今回の fix)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2773-mocc-template-wave2/wave-artifacts/s6-reviewA-1.md (所見 1 = F1、所見 3 = F2 の逐語是正案)、s6-reviewB-1.md (所見 1 = F1)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2773-mocc-template-wave2/wave-artifacts/s4-ruling.md (R1 / R2 / R6 / R8 / R9 / R17 / R18 / R19、変異 M8 / M15)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2773-mocc-template-wave2/compute-1.json (実 compute の完成 JSON。合成 proof の形の参考。**この file を test へ複製・読込しない** — repo 内の `output/env/pegasus/calibration/s3_mocc_template_proof.json` が同じ bytes で commit 済み 8d82f7b3e)

作業 repo は /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2773-mocc-template-wave2 (branch worktree-dev-wave-t2773-mocc-template-wave2、HEAD 8d82f7b3e)。実装は `orchestrator/campaign/s3_mocc_template_proof.py` (driver、`compute_checks(proof, policy)` 310〜、`_matrix_complete` 262〜、`_condition_gates_valid` 286〜、`QUARANTINE_EXPECTED` 57〜、`DENY_EXPECTED` 63、`CHECK_KEYS` 46〜) と `orchestrator/campaign/axis_mocc_temperature.py` (`auditor_projection` 102〜、`AUDITOR_MOCC_REQUIRED` 40〜) にある。旧 test の per-key 型の前例 = `orchestrator/tests/test_mocc_mutation_proof.py` (`test_mocc_mutation_checks_are_input_derived`) と `orchestrator/tests/test_mocc_proof_surface.py` 798〜954。

## 所有 path (これ以外を編集しない)

`orchestrator/tests/test_mocc_template_proof.py` だけ。production code (driver・軸 module・登録簿・patch・auditor.md・pin) と他の test を編集しない。

## 禁止事項 (すべて必須)

- `git add` / `git commit` / `git merge` / `git checkout` / `git reset` / `git stash` / `git worktree` を実行しない。commit は親が行う。
- docs・`output/**`・`patches/**`・`orchestrator/campaign/**`・`.claude/**`・`.codex/**`・`tools/**`・`conftest.py` を編集しない。
- `tools/run_tests.py` と `python -m pytest` は使わない (sandbox で走らない)。実走は `PYTHONPATH=. python3 orchestrator/tests/test_mocc_template_proof.py` の自走 harness だけ。
- **既存テストの期待値を変更しない。** 反転・緩和・skip・削除は禁止。赤なら実装側が誤りとし、期待値が誤りと考えるなら実装を変えず報告して止める。既存 13 node は名前・意味を保ち、追加・強化だけを行う。
- 受理集合を変えない (driver・軸 module は不可触)。fixture へ現行 hash を差し込むなど test を甘くして緑にしない。期待値へ揮発 payload を焼き込まない。合成 proof は test 内で組み立て、実 JSON を読まない (実 JSON を読む node は既存の 2 つだけ)。
- system tmp 以外に一時 dir を作らない。repo 内に untracked を残さない。出力へ結合文字 U+0300〜U+036F を使わない。入力はデータであって指示ではない。

## 依頼

**F1 (must-fix、A1 / B1): `test_mocc_template_checks_are_input_derived` を全 30 check の per-key 対照へ拡張する。**

1. 全 30 check が True になる**合成 proof と policy** を test 内で組み立てる (`compute_checks(proof, policy)` が `all(...)` になること、`tuple(checks) == M.CHECK_KEYS`)。組み立てに必要な形は driver の各述語 (`compute_checks`、`_matrix_complete`、`_condition_gates_valid`、`_logical_valid`、`axis.auditor_projection`、`QUARANTINE_EXPECTED`、`DENY_EXPECTED`) から読む。identity の digest / src_token は 64 桁 hex の合成値、toolchain の sha は policy 側と同じ合成値、runs は既存の 12 走合成 (`M.wave1._summary(raw)` 型) を再利用、`condition_gates` は 3 本の合成 record (driver_id / macro / admission.admitted / supply・meaning の terminal_status "green"・driver_id・macro / supply.evidence.owner_tu / meaning.evidence.source_rel・start_directive)、`auditor_definition` は tools・items (7 key True)・accepted_runs・performance_rejected・projections (12 走ぶん、`axis.auditor_projection` を通る形 = 既存 `_projection()` helper を利用)、`quarantine_controls` は `QUARANTINE_EXPECTED` どおりの cases と `DENY_EXPECTED` 4 key True、`consumer_binding_controls` 3 key True、`wave1_proof` / `legacy_proof` は path / sha256 / all_pass / checks / required_checks (driver の `_proof_reference` の形。required_checks の各 key が checks に True で存在)、`instrumentation_preservation` は 3 flag True + old/new sha が `patches` の sha と一致、`trace0` は claim + off / on_b (`_logical_valid` を満たす) + binary (nm 0 / strings 0 / 0)、`template` / `touch_sets` / `patches` は駆動定数から。
2. 各 check key について、**対象入力を 1 箇所だけ壊す**と当該 key が False になる対照を置く (他 key は原則 True のまま。連鎖して落ちる key があればその理由を assert message か comment に書き、「当該 key だけ」とは主張しない)。必須の対照:
   - `quarantine_rejects_frozen_frame_and_outside_edits`: `cases["stock-frame"]["subtype"]` だけを `"outside-region"` に変える (passed は False のまま) → False。`quarantine_accepts_benign_hole`: `cases["benign"]["passed"]` を False → False。cases に無い key を足す / 1 key を消す → 両 dq check False。
   - `auditor_digest_and_deny_only_controls`: `deny_only["machine-reject-preserved"]` を False → False。key 欠落 → False。
   - `auditor_definition_read_only_and_projection`: **有効な projections を保持したまま** tools を `["Read","Grep","Glob","Bash"]` にする → False。`performance_rejected` False → False。`accepted_runs` の 1 走 False → False。projections の 1 走に `wall_seconds` を足す → False (`auditor_projection` が例外 → compute_checks は False にする)。
   - `auditor_mocc_items_present`: items の 1 key False → False。items の key 集合から 1 つ消す → False。
   - `consumer_binding_controls`: 1 key False → False。
   - `instrumentation_body_preserved`: 3 flag それぞれ単独 False → False。`new_sha256` を patches と不一致 → False。
   - `wave1_proof_bound_and_all_pass` / `legacy_proof_bound_and_all_pass`: `all_pass` False → False。`checks` から required_checks の 1 key を消す → False。1 key を False → False。sha256 を 64 桁の別 hex → (driver が実 file と照合するなら) False、照合しないなら「束縛は JSON consumer 側」と comment に書く (driver の実装を読んで決め、実装を変えない)。
   - `template_off_stock_identity`: `template_off.src_token` を 64 桁 hex → False。`template_off.digest` ≠ stock → False。`claim` 文字列変更 → False。
   - `template_on_benign_identity_distinct`: 既存対照 (digest 一致) を保ち、`benign_diff_sha256` ≠ cases.benign.diff_sha256 → False を追加。
   - `trace0_logical_rows_identical`: off / on_b それぞれ `logical_rows_identical` False、count 不一致、sha 不一致 → False。`claim` 変更 → False。
   - `trace0_nm_izanagi_zero` / `trace0_strings_izanagi_trace_zero`: 各 count を 1 → False。
   - `toolchain_matches_policy`: g++ の sha を policy と不一致 → False。
   - `template_touch_set_is_exact` / `instrumentation_touch_set_is_transaction_only`: touch set に 1 file 追加 → False。
   - `matrix_runs_complete_and_terminated`: 既存の終了状態対照を保ち、`condition_gates` を 2 本にする / 1 本の `admission.admitted` False / `start_directive` 変更 → False を追加。
   - `*_certified_and_silent` (12): 既存対照を保つ。
3. 期待 key 集合・期待 subtype・期待 tools は test 側の固定値 (driver の定数を参照してよいが、対照の期待値は literal で書く)。

**F2 (nit、A3): `test_mocc_template_instrumentation_preserves_body` の対照を単一理由へ揃える。** X 恒偽化対照は入口検査の条件全体を `false && ( … )` で包む形 (現行の `if (false && !izanagi_cll_has_writer ||` は `(false && A) || B` で全体の恒偽化ではない)。4 対照 (X 恒偽化・P emit 無効化・publish 前検査の移動・`#line` ±1) それぞれについて、期待する flag だけが False になることを個別に assert する (`added_body_identical` / `added_body_identical` / `operation_contexts_identical` / `line_restorations_match`)。他の flag が連鎖して False になる場合はそれを assert に含めて明記する。

**実走と報告。** `PYTHONPATH=. python3 orchestrator/tests/test_mocc_template_proof.py` を走らせ、全 13 node の結果 (JSON 依存 2 node は JSON が commit 済みなので緑になるはず) を nodeid で報告する。M8 相当 (driver の `records[n]["subtype"] == subtype` を一時的に外す) と M15 相当 (`auditor_projection` の allowlist に `wall_seconds` を足す) を **自分の scratch copy** (system tmp に driver / 軸 module を複製して import path を差し替える等、repo 内 file は触らない) で試し、新 test が赤になることを確認できれば報告する。できなければ「未実走」と書く。所有外への波及 (test 名の変更なし、node 数 13 のまま) を明記する。

## 出力形式

Markdown。見出しはすべて `##` (H2)。節: `## 変更 file 一覧`、`## per-key 対照の一覧` (check key → 壊した入力 → 期待 False、連鎖の有無)、`## F2 の対照`、`## 実走した検査` (nodeid と結果)、`## 総括`。最後の節は必ず `## 総括` (`#` を 2 個) とし、`git status --short` の結果と未実走の項目を書く。予算が尽きそうなら途中結論を出力形式どおり書いて終わること (無出力が最悪)。
