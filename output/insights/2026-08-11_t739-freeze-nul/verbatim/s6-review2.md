## 結論

静的レビューの結論は `NO-GO`。親の `231 passed / rc=0` は前提事実として扱い、pytest は実行していない。

### 変異 kill 予測

| 変異 | 静的に赤になる nodeid |
|---|---|
| M1-remove-gate | `test_evidence_contract_hash_rejects_nul_at_every_consumed_path[...]` 全38件、malformed 3件、4つのE2E |
| M2-first-only | 全38件のうち後続36件、`test_prepare_revision_rejects_nul_path_contract_before_create`、`...with_existing_freeze`。legacy E2Eは condition 0 の consumer path が先頭走査で到達するため赤にならない |
| M3-over-reject | `test_evidence_contract_hash_accepts_non_path_nul` |
| M4-order | `test_evidence_contract_hash_preserves_canonicalization_reason_before_nul` |
| M5-nul-to-cr | path NUL 38件、malformed 3件、CR/LF 4件、4つのE2E |

以下は、差分の既存5変異では検出できない実装欠陥である。

- `real / must-fix` — `orchestrator/campaign/s8c_preregistration.py:353`, test側 `:534`
  現在の全NULテストは `"\x00alias"` を末尾に付加するだけで、NULが文字列中間にあるケースを検査しない。
  追加変異 `M6-nul-position`:

  ```python
  # before
  if is_path and isinstance(node, str) and "\x00" in node:

  # after
  if is_path and isinstance(node, str) and node.endswith("\x00alias"):
  ```

  期待する追加 nodeid は `test_evidence_contract_hash_rejects_nul_at_interior_position[/conditions/0/required_evidence/0/path]`。未修正なら中間NUL付き path 契約が freeze・activation まで受理され、certified 選択の受理集合と ledger の `evidence_contract_sha256` / `protected_sha256` が不正契約を含み得る。

- `real / nit` — `orchestrator/tests/test_s8c_preregistration_core.py:636-650`
  `test_current_evidence_contract_hash_is_frozen` と `test_existing_g1_record_pins_are_unchanged` は、登録済み5変異のいずれにも殺されない。hash drift と既存record固定には有用だが、今回の mutation score には寄与しない。未修正でも certified 値・report・ledger の実行時値は変わらず、検出力評価だけが過大になる。

- `real / nit` — `orchestrator/tests/test_s8c_preregistration_core.py:139-143`
  import時の `assert len(cases) == 38` は、path追加を検出するdrift検査としては妥当。ただしpathが1つ増えるだけでmodule全体がcollection errorになる。独立した `test_contract_path_inventory_has_expected_count` へ移し、parametrize自体はcollection可能にするのを推奨する。未修正でも成果物の受理集合やhash値は変わらず、テスト実行可否だけが変わる。

- `refuted / nit` — `orchestrator/tests/test_s8c_preregistration_core.py:33-36, 547-592, 636-648`
  `5203...`、`c4...`、`853...`、CR/LF 4値、非path NUL 1値は、productionのhash関数から期待値を導出しておらず、独立literalとして扱われている。`5203...` はlegacy recordへ注入するだけで、literal自体の旧実装hashをtest内で再検証してはいないが、これは親の実測oracleを信頼する設計上の弱さであり、自己参照ではない。未修正でも成果物値は変わらず、legacy fixtureの証拠力だけが弱くなる。

- `refuted / nit` — `orchestrator/tests/test_s8c_preregistration_core.py:207-226, 736-764, 1218-1263`
  `_install_legacy_nul_bound_g1()` のrecordは、`_record_document()`で全hash・generation・schema keyを埋め、`_load_freeze_record()`のschema条件を静的に満たす。`ruling_reference="D327"` もfixtureの `docs/decisions.md` の `## D327.` と整合する。既存g1ではruling lookup自体は走らないが、対象のNUL検査へ到達することを妨げない。成果物値・受理集合への問題はない。

- `refuted / nit` — `orchestrator/campaign/s8c_preregistration.py:1577-1633, 1696-1747`
  4つのE2Eはいずれも期待検査へ到達する。prepare_revisionの既存freeze分岐では、commit上のg1検証後にworktree evidence hashへ進み、legacy E2Eではrecord schema検証後に対象contract hashへ進む。同一の `evidence-contract-path-nul` を別経路が偶然生成する箇所も静的にはない。成果物への影響はない。

- `refuted / nit` — `orchestrator/tests/test_s8c_preregistration_core.py` 差分全体
  揮発値の焼き込み、fixture弱体化、既存期待値変更、`skip` / `xfail` は確認できない。production差分もhelper追加と呼出し1箇所だけである。成果物値・受理集合・参照への影響はない。

## 総括

1. must-fix

- NUL位置が末尾以外でも拒否されることを追加テストし、`M6-nul-position` を事前登録する。

2. 追加すべき変異

- `M6-nul-position`
  - 置換前: `if is_path and isinstance(node, str) and "\x00" in node:`
  - 置換後: `if is_path and isinstance(node, str) and node.endswith("\x00alias"):`
  - 期待nodeid: `test_evidence_contract_hash_rejects_nul_at_interior_position[...]`

3. 判定

`NO-GO`。5変異は静的には全てkill予測できるが、NUL位置依存のsurviving mutantがあり、land前に追加検査が必要。
