## 実装結果

S1〜S12を一体で実装しました。変更対象は次の5ファイルだけです。

- [attempt_registry_core.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-a2alpha-author/orchestrator/campaign/attempt_registry_core.py)
- [s8b_attempt_profile.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-a2alpha-author/orchestrator/campaign/s8b_attempt_profile.py)
- [s8b_attempt_registry.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-a2alpha-author/orchestrator/campaign/s8b_attempt_registry.py)
- [test_attempt_registry_core_s8b_profile.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-a2alpha-author/orchestrator/tests/test_attempt_registry_core_s8b_profile.py)
- [test_s8b_attempt_registry.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-a2alpha-author/orchestrator/tests/test_s8b_attempt_registry.py)

commit、stage、branch/remote 操作はしていません。docs、launcher、`output/` の凍結成果物、`external/`、`FROZEN_MANIFEST` は変更していません。runner が自動生成した4組の dispatch 診断ファイルは、今回生成された exact path だけ削除済みです。

## 変更前後の受理・拒否

変更前は canonical v1 lifecycle、1段 path、claim v2、legacy consumed marker が受理される一方、v2 profile は `_assert_profile()` の5入口で v1 factory と比較され、path 処理前に拒否されていました。handle は1段 pathを再計算し、reserve/resume に capability marker 引数はありませんでした。

変更後は次の状態です。

- v1: default、1段 path、claim v2、legacy marker、公開戻り型を維持。
- v2: schema exact gateを通過し、protocol別2段 generation pathを使用。
- v2 create: generation directoryを含む create-only publish。
- v2 reserve/resume: current-generation marker必須。
- v2 claim: full bindingを持つ v3。
- v2 terminal: core validatorとlegacy adapter入口の二層で、指定署名により無条件拒否。
- v2 retryable reasons:空集合のまま。
- E1、E2、sealed terminal API 2本、launcher carrier:未実装のまま。

既存の空集合 pin は1 byteも変更しておらず、diffはそのテスト終了後の追加だけです。既存 `test_v2_profile_is_rejected_by_public_mutation_but_slot_lookup_is_five_axis` の拒否期待も維持し、対象を validator を除去した forged v2 profile に限定しました。

## S1〜S12

| 項目 | 状況 |
|---|---|
| S1 | keyword-only default 2 fieldを追加 |
| S2 | classification equality、null matrixの後に terminal validatorを実行 |
| S3 | policy false時は retryable terminalから次 ordinalを開かない |
| S4 | schema identity dispatchと `_assert_exact_profile()` を実装。新2 fieldもexact比較 |
| S5 | v2 terminal fail-closed validatorを実装 |
| S6 | legacy terminal 2入口でv2を明示拒否 |
| S7 | `_entry_paths()` の全11呼出しをprotocol-aware化。handle保存pathも再照合 |
| S8 | generation create-only publisherを実装 |
| S9 | v3 address/schema/key set/reader/writerを実装 |
| S10 | legacy marker validatorをrenameし、v2をcapability経路へ分岐 |
| S11 | marker-owned atomic updateとlive-lock guardを実装。prelock hookはlock前1回 |
| S12 | reserve/resumeにoptional markerを追加。v2必須、v1 default None |

## 検査結果

pytest は規定の `tools/run_tests.py` 経由で4回試しましたが、すべて `qstat -Q preflight rc=1`、runner `rc=16` となり、compute childは開始されませんでした。したがって、pytestとして実走したnodeidは0です。

試行範囲は以下です。

- `test_attempt_registry_core_s8b_profile.py` 全体
- `test_s8b_attempt_registry.py` 全体
- `test_profile_extension_fields_are_keyword_only_and_preserve_legacy_defaults`
- `test_terminal_validator_direct_replay_and_producer_mapping_keep_v1_positive`
- `test_v2_marker_claim_v3_resume_and_legacy_terminal_fail_closed`

pytestの代替緑とは数えていませんが、新設test関数を通常Pythonから直接診断し、core validator/order、S8C defaults、v1 terminal、generation publish、実 admission capabilityを使ったv2 create/reserve/claim v3/resume/observation/legacy-terminal拒否を通過させました。

以下は実走成功です。

- `py_compile`: 変更したproduction/test 5ファイル
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- `git diff --check`
- consumer module import
- S8C profile差分診断

`ruff` は環境にmoduleがなく実行できませんでした。

## 変異16件

| 変異 | 期待 | 対応検査 |
|---|---|---|
| M1 | KILLED | `test_v2_profile_opens_generation_create_and_read`、`test_v2_marker_claim_v3_resume_and_legacy_terminal_fail_closed` |
| M2 | KILLED | `test_v2_profile_exact_gate_rejects_both_new_field_mutations`、既存v2 forged-profile node |
| M3 | KILLED | `test_v2_profile_exact_gate_rejects_both_new_field_mutations` |
| M4a | SURVIVED | kill検査は意図的になし。v2 terminal検査はcore側の同署名拒否でも通る |
| M4b | KILLED | `test_terminal_validator_direct_replay_and_producer_mapping_keep_v1_positive`、v2 lifecycle node |
| M5 | KILLED | v2 lifecycle nodeのhandle classify/observe経路 |
| M6 | KILLED | `test_generation_publish_direct_barriers_adapter_mapping_and_positive` |
| M7a | SURVIVED | kill検査は意図的になし。残るsymlink層で同じ検査が通る |
| M7b | KILLED | `test_unchecked_generation_symlink_would_double_count_one_registry_budget`、generation publish direct barrier |
| M8 | KILLED | `test_v3_claim_address_separates_measurement_ordinals` |
| M9 | KILLED | v2 lifecycle node内のprotocol tamper |
| M10a | SURVIVED | kill検査は意図的になし。marker.use/admission再検査が残る |
| M10b | KILLED | v2 lifecycle内live-lock差し替え、既存 `test_floor_marker_capability_requires_live_caller_held_lock` と durable-evidence再検査 |
| M11 | KILLED | v2 lifecycleのcurrent-generation resume正例 |
| M12 | KILLED | v2 lifecycleのprelock回数、既存 locked-update seam/rendezvous検査 |
| M13 | KILLED | v2 lifecycle内のmarkerなしreserve拒否 |

全KILLED期待変異に検査名があります。M4a/M7a/M10aは裁定どおり単層SURVIVEDを維持しています。ただしmutation harness自体は未実走です。

## 波及可能性

静的に確認した所有外consumerは次のとおりです。

- `trial_registry.py`: S8Cの `DomainProfile` / `TransitionPolicy` constructorとcore terminal consumer。defaultによりtext変更なし。関連225 nodeはpytest未実走。
- `s8b_holdout_admission.py`: v1 full replay、current-generation claim/marker、三層lock再検査。関連72 nodeは未実走。
- `s8b_scheduler_accounting.py`: registry loader/binding consumer。関連1 nodeは未実走。
- `s8b_floor_attempt_launcher.py`: v1 reserve callerはdefault `consumption_marker=None` で不変。v2 marker handoffは単位C待ち。
- `test_trial_registry.py`: 225 node未実走。
- `test_s8b_holdout_admission.py`: marker capability群未実走。ただし同fixtureを使った直接診断は成功。
- core equivalence 16 node、launcher 12 node、campaign recovery helper 1 nodeも未実走。

## 残る赤

- 期待赤: 観測なし。A2β面はscope外としてテストを追加していません。
- 回帰赤: 不明。pytest childが1件も開始されていないため、回帰なしとは申告できません。
- infrastructure: `qstat -Q` preflight失敗による `rc=16`。
- 新規test fileは作っておらず、既存testのrenameも最終差分にはありません。そのため plain-runner file列挙meta-testの追加対象はありません。

## 総括

- S1〜S12: 実装済み。ただしpytest未実走のため、変更単位全体のclosureは「部分」。
- 実走したpytest nodeid: 0。指定2ファイル全体と3 exact nodeidは、compute child開始前にrunner `rc=16`。
- 残る赤: 期待赤0件、回帰は未判定、infra failureあり。
- 16変異: KILLED期待13件すべてに検査実在。SURVIVED期待3件はmask構造を維持。
- 波及可能性: trial、holdout、scheduler、launcher、関連consumer test 487-node閉包を静的確認。pytest未実走。
- 読めなかった資料: なし。射影6資料を全文読了。
- 確かめられなかった事実: pytest実結果、mutation実走結果、consumer 487-node全走、ruff結果。