## 所見対応表

| 項目 | 状態 | 根拠 |
|---|---|---|
| F1 | closed | 部分閉包と展開理由を保持し、交差→不完全/未消費→非交差の順に判定。[checker:938](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2539-fix1/tools/check_silo_validation_isolation.py:938)、[checker:1447](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2539-fix1/tools/check_silo_validation_isolation.py:1447)、[test:272](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2539-fix1/orchestrator/tests/test_silo_validation_isolation.py:272) |
| F2 | closed | default argument の最小 arity を解析。解決不能な first-party arity 変更は不完全閉包。[checker:564](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2539-fix1/tools/check_silo_validation_isolation.py:564)、[checker:865](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2539-fix1/tools/check_silo_validation_isolation.py:865)、[test:303](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2539-fix1/orchestrator/tests/test_silo_validation_isolation.py:303) |
| F3 | closed | full pre/post image からコメント・literal を除去後、conditional directive span を検証。[checker:1183](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2539-fix1/tools/check_silo_validation_isolation.py:1183)、[checker:1220](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2539-fix1/tools/check_silo_validation_isolation.py:1220)、[test:328](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2539-fix1/orchestrator/tests/test_silo_validation_isolation.py:328) |
| F4 | closed | early-unlock の rc=0、`writePhase/0`、write/writeback・serializability 非保証を固定。[test:461](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2539-fix1/orchestrator/tests/test_silo_validation_isolation.py:461) |
| F5 | closed | `claim_boundary` の完全 dict equality と exact key set を固定。[test:477](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2539-fix1/orchestrator/tests/test_silo_validation_isolation.py:477) |
| F6 | closed | runtime policy 非強制、外部 evidence 必須、implicit constructor/destructor edge 非モデル化を明記。[checker:41](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2539-fix1/tools/check_silo_validation_isolation.py:41)、[test:501](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2539-fix1/orchestrator/tests/test_silo_validation_isolation.py:501) |

## 実走結果

自走 harness:

```text
command:
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 orchestrator/tests/test_silo_validation_isolation.py

rc=0
19 nodes PASS; failures=0
```

追加 node は以下を含み、すべて PASS です。

```text
test_known_root_edits_win_over_incomplete_closure_expansion
test_known_root_edit_wins_over_unconsumed_edit
test_default_argument_callee_edit_is_not_reported_as_no_intersection
test_comment_directive_text_does_not_create_macro_intersection
test_early_unlock_is_outside_closure_and_claims_no_correctness
test_claim_boundary_records_every_required_non_guarantee
test_claim_boundary_requires_external_runtime_anomaly_evidence
test_claim_boundary_records_unmodeled_implicit_lifetime_edges
```

実測 1 — checker を各 patch に直接実行:

```text
permutation-erase    rc=1 INTERSECTION root@0 expansion=UNKNOWN_EDITED_CALLEE×2
permutation-swap     rc=1 INTERSECTION root@0 expansion=UNKNOWN_EDITED_CALLEE×1
write-intent-erase   rc=1 INTERSECTION root@0 expansion=UNKNOWN_EDITED_CALLEE×2
write-intent-forge   rc=1 INTERSECTION root@0 expansion=UNKNOWN_EDITED_CALLEE×2
write-intent-opswap  rc=1 INTERSECTION root@0 expansion=UNKNOWN_EDITED_CALLEE×1
write-intent-ptrswap rc=1 INTERSECTION root@0 expansion=UNKNOWN_EDITED_CALLEE×1
sort-nonswo          rc=1 INTERSECTION root@0 function×2 + macro×1
```

実測 2 —実体 source から tmpdir patch を生成:

```text
default-arg:
  rc=1 STATIC_VALIDATION_CLOSURE_INTERSECTION
  ReadElement::get_tidword/1 depth=1

arity-unchanged control:
  rc=1 STATIC_VALIDATION_CLOSURE_INTERSECTION
  ReadElement::get_tidword/0 depth=1

required-arg mismatch:
  rc=2 ERROR / INCOMPLETE_CLOSURE_EXPANSION
  reason=FIRST_PARTY_ARITY_MISMATCH
```

実測 3:

```text
comment-directive:
  rc=2 ERROR / UNCONSUMED_EDITS
  conditional_macros=[]
  intersections=[]
```

実測 4 と正例:

```text
broken-silo-early-unlock-validation.patch:
  rc=0 NO_STATIC_VALIDATION_CLOSURE_INTERSECTION
  target=TxExecutor::writePhase/0
  write/writeback covered=false
  serializability listed in does_not_prove

silo-backoff-fixed.patch:
  rc=0 NO_STATIC_VALIDATION_CLOSURE_INTERSECTION
  expansion_errors=[] intersections=[] unconsumed=0
```

`tools/run_tests.py` と pytest は指示どおり未使用です。指定された harness と実測 1〜4 はすべて実走済みです。

## 波及可能性

- repository 内の所有外 caller/consumer は検索上ありません。接続面は standalone `main() → analyze()` と同 test の直接 import のみです。
- 出力へ `closure_expansion_errors` と claim boundary 3 field が増えました。外部に exact-schema consumer があれば追随が必要ですが、repository 内には存在しません。
- 共有 fixture は同 test 内の `_invoke` と tmpdir patch generator のみです。生成 patch はすべて現物 source から `difflib` で構築しています。
- `silo-backoff-fixed.patch` の guard span は、厳格な macro-inspection と区別して `compile-time-requirement` に分類されます。

## 総括

F1〜F6 はすべて closed、19/19 test が緑です。  
正例 rc=0、既知 root 編集 7 件 rc=1、early-unlock の境界 rc=0 を確認しました。  
変更は指定 2 file のみ、commit なし、結合文字なしです。