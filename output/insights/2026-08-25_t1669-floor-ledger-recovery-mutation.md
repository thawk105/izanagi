# [T-1669] 床値 ledger 復旧と次 ordinal 認可 — 変異 matrix の逐語

- wave: `dev-wave-t1669-floor-ledger-recovery`
- 本走 spec: `mutation-spec-final.json`
  (sha256 `b3b485c1d82f18ebfba68a5a5b6012b16c8bda59c548652786d7cc7b83941916`)
- 本走 repo_head: `d54637c46b19ca3d3b88a32261ea2f8bd513823a`
- runner: `python3 tools/run_tests.py --force-dispatch
  orchestrator/tests/test_s8b_holdout_admission.py
  orchestrator/tests/test_s8b_floor_campaign.py -q -rf`
- 本走結果: **baseline PASSED (565 passed / 2 skipped)、KILLED 9 / 9、SURVIVED 0、
  MISMATCH 0、TIMEOUT 0、PARSE_ERROR 0**

## 本走の内訳

| ID | 撃つ不変条件 | 期待 node |
|---|---|---|
| MUT-T1669-RECOVERY-CANDIDATE-COUNT | 同じ trigger start を主張する recovery を計数から消させない | `test_registry_recovery_counts_corrupt_extra_candidate_before_replay` |
| MUT-T1669-AUTHORITY-PIN | 候補 bytes が自分の trust root を選べない | `test_registry_recovery_authority_is_empty_and_fail_closed` |
| MUT-T1669-RETRY-PREFIX | retry ordinal は連続 prefix である | `test_inspection_rejects_registry_recovery_nonprefix_or_reused_trigger[ordinals0]`, `test_verified_registry_recovery_rejects_non_next_or_multiple_retry_ordinals[ordinals0]` |
| MUT-T1669-RETRY-LATEST | consume は最新 ordinal しか開けない | `test_verified_registry_recovery_rejects_nonlatest_retry_start` |
| MUT-T1669-TRIGGER-UNIQUE | 1 つの trigger が開ける retry start は 1 つ | `test_registry_recovery_rejects_two_starts_when_target_is_first` |
| MUT-T1669-RETRY-XOR | 失敗 session と検証済み recovery の排他 (候補は絞る前に数える) | `test_legacy_retry_rejects_extra_completion_for_same_trigger` |
| MUT-T1669-TRIGGER-FORWARD | recovery が指す attempt を trigger へ転送する | `test_resume_runner_produces_one_retry_from_admission_selected_recovery` |
| MUT-T1669-ONE-ORDINAL | 1 つの検証済み recovery が開けるのは次の 1 ordinal だけ | `test_verified_recovery_emits_only_one_invalid_retry_ordinal` |
| MUT-T1669-CUT6-ADMISSION | runner は truthy な非 bool を証拠として扱わない | `test_cut6_replay_rejects_truthy_non_bool_verdict` |

## erratum — probe 相で 3 件が生存した

`DW-M02` に従い初回結果を消さずに残す。

- probe spec: `mutation-spec-probe.json`
  (sha256 `e4a2631dc6e78f3d76fc866f14007b7d8a48d9be6fd5bd2554d4b4e78eef5ab0`)
- probe repo_head: `07d04397c4b9b72cb41758ce2ea00f03e1ebbea1`
- probe 結果: baseline PASSED、KILLED 6、**SURVIVED 3**

生存したのは `MUT-T1669-RECOVERY-CANDIDATE-COUNT`、`MUT-T1669-TRIGGER-UNIQUE`、
`MUT-T1669-CUT6-ADMISSION` の 3 件である。

**等価変異ではなくテストの穴だった。** 3 件とも注入の実在を確認している
(`anchor_counts` は 1 箇所、`injection_diff_sha256` は互いに相異、`rc=0`、`failed_nodes` は空)。

生存の型はそれぞれ次のとおりで、いずれも「その gate だけで落ちる入力」がテストに無かった。

- **CANDIDATE-COUNT**: 同じ trigger start を指す recovery が 2 件あり、片方の slot 座標が
  壊れている履歴が無かった。候補を 1 件へ切り詰めると正規行だけが残り、authority・exact
  candidate・consume marker の全検査を通って認可されてしまう。
- **TRIGGER-UNIQUE**: 直後の `recovery_starts[0] is not retry_start` が mask していた。
  件数検査だけが拒否理由になるのは「2 件あり、かつ検査対象が先頭である」場合に限られる。
- **CUT6-ADMISSION**: 再開判定の query が truthy な非 bool を返す負例が無かった。
  exact-bool 検査を外すとその値が真として扱われ、再開が通る。

実装は 1 byte も変えず、負例 3 関数を足して閉じた (commit `d54637c4`)。
「前後の層に吸収されて固有の力を持たない gate は登録を取り下げる」という `DW-M01` の要求は、
段 6 のレビューが現物で判定した 7 件 (A1 / A3 / A4 / A5 / A7 / A8 / B6) に対して既に適用し、
実効 gate へ再照準している。本走の 9 件はその再照準後の集合である。
