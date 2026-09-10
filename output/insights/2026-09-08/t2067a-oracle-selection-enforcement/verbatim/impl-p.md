## 再 pin

- report: `f7ef6259f8feb3a6ccd7812d85132f19bc36e10fa4cd10cea28ecd145769c93b` → `30fe2b1bcad143f5a85ca32250744522d6049f4c71e9b853618e3af2dd0091c7`
- judge: `0e6276ddcb6cde6e38f781bdbb8df1289520cfcce9653330d2c83a1db20784d3` → `f3e2fbec0d9dc353dae987aa2f31afeafe178d75e544313fe1af84c06ec1ab3b`
- 外側 hash: `58190f7b402ea5a72d19e86e38d63ef2941e3281d1617a4a8ff986c2e4769f8e` → `63cd82787ebe361e4fc6c4335c542bf76ee10083f419fd0b47f09b97e3d64202`

変更先: [test_s8b_oracle_manifest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2067a-p/orchestrator/tests/test_s8b_oracle_manifest.py:63)

## 照合

編集後 source を AST parse し、`ast.literal_eval` で `PIN_GATE_SPEC_RAW` を抽出して検証しました。

- report / judge の JSON 内 hash と実 file SHA-256: 両方一致
- `sha256(PIN_GATE_SPEC_RAW)` と `PIN_GATE_SPEC_SHA256`: 一致
- compact・sort 済み JSON: 維持
- 末尾 LF なし: 維持
- 差分: 指定された 3 literal のみ、`git diff --check` 成功

波及先は pin を検証する指定 2 nodeです。production caller、共有 fixture、他 consumer の変更はありません。

## 変わっていない pin

実 file SHA-256 と既存 literal の一致を確認しました。

- materializer: `049642ca067d93b046df66b14ddfdda3782bb06c830f2803c71e0e60e42f316d`
- artifacts: `576ce3cf83f4f3f693d47b6fecd219816f49ed7bfabc665458044e3c5c307c1d`
- outcome_stage_contract: `f8a0bb2237dcaf3c643a78c04ca6b8cea2a8f83e3d306d85c781716b165c73af`

## 実走

次の 2 node を `tools/run_tests.py` 経由で起動しましたが、テスト本体は未起動です。

- `test_reviewed_spec_has_independent_canonical_bytes_and_sha_literal`
- `test_build_approved_valid_fixture_output_depends_only_on_spec_pin`

runner が local headroom 不足から dispatch を選択後、`qstat -Q` が `EACCTAUTH Unknown user-id` で失敗し rc=16 となりました。したがって、実装済み・未実走です。

## 総括

所有ファイルの 3 literal だけを再 pin しました。  
独立照合はすべて一致しています。  
テストは基盤認証エラーにより未実走です。  
commit・push は行っていません。