# T-173 段6 mutation receipt

## 結果

- anchor: `85e9a73a9dfce526a2468c495fb2f35f5b43bece`
- destructive mutations: **6/6 KILLED**
- SURVIVED: **0**
- diagnostic sensitivity pin: **1/1 green**
- positive survivor: **1/1 green**
- hang / timeout: 対象なし

| ID | 注入実在 | pytest `-rf` の失敗 node | 判定 |
|---|---|---|---|
| V1 | `tools/check_docs.py` Skill digest gateへ `and False` 1行 | `orchestrator/tests/test_check_docs.py::test_cleanup_skill_one_byte_change_is_rejected` | KILLED。mutated Skillがchecker rc=0となることをnodeが検出 |
| V2 | `tools/check_docs.py` command digest gateへ `and False` 1行 | `orchestrator/tests/test_check_docs.py::test_cleanup_command_one_byte_change_is_rejected` | KILLED。mutated commandがchecker rc=0となることをnodeが検出 |
| V3 | real Skill末尾へunsafe live lineを追加 | `orchestrator/tests/test_check_docs.py::test_real_repo_clean` | KILLED。findingはSkill whole-file digest 1件 |
| V4b | real commandの `## 4. 事後検査` を `## 4. 先に削除` へ置換 | `orchestrator/tests/test_check_docs.py::test_real_repo_clean` | KILLED。findingはcommand whole-file digest 1件 |
| V5 | metadata policyを `false` から `true` へ置換 | `orchestrator/tests/test_check_docs.py::test_real_repo_clean` | KILLED。findingはgenerated Skill interface exact mismatch 1件 |
| V6 | checkerのSkill digest literal末尾を `6` から `7` へ置換 | `orchestrator/tests/test_check_docs.py::test_codex_cleanup_branches_skill_contract_pins_exact_surface` | KILLED。checker/test独立literal assertionが検出 |

`FAILED ` 後から ` - ` 手前までの上表nodeをpytest出力から採取した。V1 / V2 は診断文字列ではなく、
変異済みsurfaceをcheckerが受理してしまう挙動を恒久nodeが検出した。V3〜V5は実repoの受理集合が
rc=0からrc=1へ変わり、期待する単一findingを確認した。V6は構造化surface pinのため、
受理集合killではなく独立pinの破損検出であるが、事前登録どおりdestructive mutationに数える。

## erratum

V4初回はreal command末尾へ4行を追加し、`test_real_repo_clean` が失敗した。しかし
command byte budget と whole-file digest の2 findingが同時発火して過剰決定だったため、killから除外した。
復元後、budget内で既存見出しだけを安全意味からunsafe意味へ置換するV4bへ再照準し、digest 1理由の
KILLEDを得た。初回結果は削除せず本erratumに保持する。

## positive / diagnostic controls

- V7:
  `test_codex_cleanup_branches_skill_contract_pins_exact_surface` — PASS
- V8:
  `test_real_repo_clean` — PASS
- combined command:
  `pytest -q -rf <V7-node> <V8-node>` — `2 passed in 0.49s`

## 復元証拠

各変異前に `git diff --stat HEAD -- <exact-file>` と実diffで単一entryを確認し、各実走後に
`git checkout -- <exact-file>` で復元した。最終 byte は次のanchorと一致し、
`git diff --exit-code HEAD --` はrc=0だった。

- Skill: `cc3eff8cc6ebebe07b5014c79b2a24aee4a67ab4a55f391e38a9ac82d68ed116`
- metadata: `f9f8fd23a4ee240125914fff6fce895a20f0850e9eb5e75ebe7fe54eab1be660`
- command: `9b2c0dac6cf1e8cfcd49a18840d62b6b3dcd2cdf322d1594266b5a4a71af43c7`
- checker: `2b7318c4a39e5f96efa8538e15563cdc2c4fbb580e8e73d9c7bdb2ac9a6ff9bb`
