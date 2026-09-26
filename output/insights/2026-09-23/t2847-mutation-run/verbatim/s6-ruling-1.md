# 段 6 裁定 1 巡目 ([T-2847] mutation-run、2026-09-23)

入力: codex/s6-review-a.md (NO-GO)、codex/s6-review-b.md (条件付き GO)、焦点走 focus-1 (request 21149.nqsv、Elapse 193 s、3,219 passed・4 failed・5 skipped、head 58fd15b58)。
統合 snapshot: codex/snapshot-before-fix1.patch (`git diff 65fd1422f..58fd15b58`)。

| ID | 裁定 | fix 単位 |
|---|---|---|
| A01 V18/V35 の helper が Tidword 宣言前 (build 不可) | real must-fix | FA |
| A02 V20 の公開版で tid 巻き戻り (親所見) | real must-fix。公開値を epoch=UINT32_MAX・tid=2^28 にし、1 s 走で通常の C/W が届かない根拠を patch の comment に 1 行 | FA |
| A03 V21 の証人なし verify が証人あり verify の例外で飛ぶ | real must-fix | FD |
| A04 / B03 test 改名 (38→57) | real should。元の名前 `test_module_claim_names_the_exact_38_define_supply_domain` に戻し、本体の数値・docstring は新しい値のまま (受入の所要時間台帳の旧 nodeid と一致させる) | FC |
| B01 test_ccbench_spawn_sites の 14 件個別照合表は既存 assertion と重複 | real should。削る | FC |
| B02 stock 失敗後も同 workload の変異を走らせる | real should。stock の前提が不成立の workload の変異は build・run せず「帰属不能 (stock 前提不成立)」と記録 | FD |
| 焦点走 test_screening_driver::test_screening_condition_requests_cover_exact_define_specs (KeyError: IZANAGI_BREAK_READ_LOCK_CHECK) | real (登録の追随漏れ)。`orchestrator/campaign/screening_driver.py` の `_CONDITION_DEFAULTS` に 14 macro を既存の壊し patch と同じ既定値 0 で足す | FC |
| 焦点走 test_condition_meaning_gate::test_v1_domain_and_claim_boundaries_are_exact | real (件数固定の追随漏れ。ROUTE_CMAKE_CXX_FLAGS 19 → 33 等) | FC |
| 焦点走 test_ccbench_spawn_sites::test_define_sink_cross_product_{classifies_t2155_production_sinks_exactly, t2520_certify_entry_removal} (proven-unreachable 39→53、29→43) | real (件数固定の追随漏れ。新 macro は production の sink から到達しない裸マクロなので proven-unreachable が 14 増えるのが正しい) | FC |

期待値の扱い: 件数固定の更新は「登録を 14 件足したことの直接の帰結」だけを許す (各件数が +14 になる根拠を報告)。それ以外の既存 test の期待値の変更・緩和・skip・削除は禁止。

fix 単位 (所有は素集合):
- FA (worktree t2847mr-ua、branch dev-wave-t2847mr-ua-fix1): patches/broken-silo-no-write-tid-max.patch、patches/broken-silo-no-read-tid-max.patch、patches/broken-silo-published-version-mismatch.patch
- FC (worktree t2847mr-uc、branch dev-wave-t2847mr-uc-fix1、base = wave HEAD 58fd15b58): orchestrator/campaign/screening_driver.py、orchestrator/tests/test_condition_meaning_gate.py、orchestrator/tests/test_ccbench_spawn_sites.py
- FD (worktree t2847mr-ud、branch dev-wave-t2847mr-ud-fix1): .t2847-launcher/launch_mutation_run.py (repo 外へ退避、commit しない)
