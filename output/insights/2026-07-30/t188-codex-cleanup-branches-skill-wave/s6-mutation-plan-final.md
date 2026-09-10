# T-173 段6 mutation 最終 plan

## anchor

- integrated implementation commit: `85e9a73a9dfce526a2468c495fb2f35f5b43bece`
- Skill SHA-256: `cc3eff8cc6ebebe07b5014c79b2a24aee4a67ab4a55f391e38a9ac82d68ed116`
- command SHA-256: `9b2c0dac6cf1e8cfcd49a18840d62b6b3dcd2cdf322d1594266b5a4a71af43c7`
- metadata SHA-256: `f9f8fd23a4ee240125914fff6fce895a20f0850e9eb5e75ebe7fe54eab1be660`
- checker SHA-256: `2b7318c4a39e5f96efa8538e15563cdc2c4fbb580e8e73d9c7bdb2ac9a6ff9bb`

各 tracked mutation は `apply_patch` で単一変更を注入し、`git diff --stat` と実 diff で注入実在を
確認してから `pytest -q -rf <node>` を単独実行する。失敗 node を記録後、`git checkout -- <exact-file>`
で復元し、上記 SHA-256 と `git diff --exit-code HEAD -- <exact-file>` を照合する。並列実行しない。

## stage 4 plan v2 からの erratum

round 3 で clause/literal parser を whole-file digest へ置換したため、V1〜V7 の旧注入位置は消滅した。
旧結果は未実施として保持し、同じ成果物影響を最終 gate へ次のように再照準する。

| ID | 単一変異 | 期待する失敗 node / 理由 |
|---|---|---|
| V1 | Skill digest gate の `expected_sha256 is not None` を false にする | `test_cleanup_skill_one_byte_change_is_rejected` — mutated synthetic Skill が rc=0 になる |
| V2 | command digest gate の `cleanup_text is not None` を false にする | `test_cleanup_command_one_byte_change_is_rejected` — mutated synthetic command が rc=0 になる |
| V3 | real Skill末尾へ unsafe live lineを1行追加 | `test_real_repo_clean` — Skill whole-file digest finding |
| V4 | real command末尾へ unsafe live H2を追加 | `test_real_repo_clean` — command whole-file digest finding |
| V5 | metadata policyを `false` から `true` へ変更 | `test_real_repo_clean` — exact generated interface finding |
| V6 | checkerのSkill digest literalを1 nibble変更 | `test_codex_cleanup_branches_skill_contract_pins_exact_surface` — 独立literal不一致 |
| V7 | 変更なしで独立surface pin nodeを実行 | diagnostic sensitivity pin（kill数に含めない） |
| V8 | 変更なしで `test_real_repo_clean` を実行 | positive survivor。承認済みexact surfaceを過剰拒否しない |

V3 / V4 の追加文は placeholder や他のgeneric forbidden tokenを含めず、digestだけを赤理由にする。
V5 はSkill本文を触らずmetadata exact guardだけを赤理由にする。hang変異はなく、timeout対象外。
