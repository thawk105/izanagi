## 所見

### RB-1

- **区分**: BLOCKER
- **主張**: direct CLI だけが `orchestrator.campaign.t080_freeze_migration` を絶対 import するため、`campaign.*` と `orchestrator.campaign.*` の二重 module/class identity を発生させ、既存 import invariant に違反する。
- **根拠**:

  `orchestrator/campaign/s8b_holdout_freeze.py:869-875`

  ```python
  if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
      if str(ROOT) not in sys.path:
          sys.path.insert(0, str(ROOT))
      from orchestrator.campaign import t080_freeze_migration
  else:
      from . import t080_freeze_migration
  ```

  `orchestrator/tests/test_campaign_import_invariant.py:1231-1233`

  ```python
  def test_real_campaign_package_uses_relative_sibling_imports(repository_scan):
      _assert_rule_ledger_matches(repository_scan, RELATIVE_RULE)
  ```

  `orchestrator/tests/README.md:72-74`

  ```text
  patch 先はテストが import する module object = campaign.s8b_oracle_driver。
  orchestrator.campaign.s8b_oracle_driver は同一ファイルでも別 object
  ```

- **成果物への影響**: import invariant が赤くなり、direct CLI と既存 `campaign.*` consumer 間で `MigrationError`・`ReceiptResolution` 等の型 identity、patch 対象、例外捕捉が不一致になる。

### RB-2

- **区分**: MUST
- **主張**: 追加された正例は package-import 経路の `M.main()` しか検証せず、問題の direct CLI import 経路を通っていない。
- **根拠**:

  `orchestrator/tests/test_s8b_holdout_freeze.py:481-485`

  ```python
  def test_verify_cli_accepts_active_t080_receipt_exact_match(capsys):
      assert M.main(["verify"]) == 0
      captured = capsys.readouterr()
      assert f"verified: {M.FREEZE_PATH}" in captured.out
      assert captured.err == ""
  ```

  `stage4-ruling.md:87-88`

  ```text
  通る正例 (1 件): 現行 repo の ... holdout_freeze.json に対する
  verify が rc=0 を返すこと
  ```

- **成果物への影響**: 新規テストが緑でも、実際の `python3 orchestrator/campaign/s8b_holdout_freeze.py verify` だけが別 namespace を読み、既存 CLI/consumer で壊れる退行を検出できない。

### RB-3

- **区分**: MUST
- **主張**: 非 canonical path 負例の fixture は canonical known_axes を用意しておらず、path 検査を削除しても意図した adapter 経路ではなく後段のファイル欠落で失敗する。
- **根拠**:

  `orchestrator/tests/test_s8b_holdout_freeze.py:507-523`

  ```python
  root = tmp_path / "repo"
  alternate = root / "alternate" / "holdout_freeze.json"
  alternate.parent.mkdir(parents=True)
  alternate.write_bytes(M.FREEZE_PATH.read_bytes())
  ...
  with pytest.raises(M.FreezeError, match="canonical active path でない"):
      M.verify_cli_with_t080_receipt(alternate, root=root)
  ```

  `orchestrator/campaign/s8b_holdout_freeze.py:934-936`

  ```python
  known_raw = _read_regular_nofollow(root / migration.KNOWN_AXES_REL)
  try:
      adapted = migration.static_gate_adapter(
  ```

- **成果物への影響**: MU-2 の単一理由性が崩れ、path exact 検査ではなく known_axes 不在による偶発的失敗を検証するテストになる。

### RB-4

- **区分**: SHOULD
- **主張**: receipt 検証と adapter の `except Exception` が想定外の実装エラーを generic `FreezeError` に変換し、構造化された原因分類を失わせる。
- **根拠**:

  `orchestrator/campaign/s8b_holdout_freeze.py:896-902`

  ```python
  except Exception as exc:
      raise FreezeError(f"T-080 receipt 検証失敗: {type(exc).__name__}: {exc}") from exc
  ```

  `orchestrator/campaign/s8b_holdout_freeze.py:935-946`

  ```python
  except Exception as exc:
      raise FreezeError(f"T-080 adapter 検証失敗: {type(exc).__name__}: {exc}") from exc
  ```

  `orchestrator/campaign/s8b_holdout_freeze.py:986-989`

  ```python
  except FreezeError as exc:
      print(f"fails-closed: {exc}", file=sys.stderr)
      return 1
  ```

- **成果物への影響**: fail-closed 自体は維持されるが、内部バグ・型不整合・I/O 障害が同じ CLI refusal に見え、原因特定と既存 failure taxonomy への接続を遅らせる。

### RB-5

- **区分**: SHOULD
- **主張**: direct CLI 分岐が `sys.path` に repository root を永続挿入し、同一 process 内の後続 import 解決順を変更する。
- **根拠**:

  `orchestrator/campaign/s8b_holdout_freeze.py:869-872`

  ```python
  if str(ROOT) not in sys.path:
      sys.path.insert(0, str(ROOT))
  from orchestrator.campaign import t080_freeze_migration
  ```

- **成果物への影響**: embedded caller や同一 process の後続処理で `campaign.*` と `orchestrator.campaign.*` の解決が変わり、patch や exact 型検査の対象を汚染する。

## 総括

**NO-GO**。少なくとも RB-1 の import invariant 違反は commit 前に修正必須であり、RB-2 により新規正例も direct CLI の安全性を証明していません。`verify()` 本体・freeze bytes・serialization manifest への直接変更は見当たりませんが、import 波及のため既存 consumer 整合性は未確認です。

親が実走すべき最小 nodeid:

- `orchestrator/tests/test_campaign_import_invariant.py::test_real_campaign_package_uses_relative_sibling_imports`
- `orchestrator/tests/test_s8b_holdout_freeze.py::test_verify_cli_accepts_active_t080_receipt_exact_match`
- `orchestrator/tests/test_s8b_holdout_freeze.py::test_verify_cli_active_receipt_hash_mismatch_is_immediate_red`
- `orchestrator/tests/test_s8b_holdout_freeze.py::test_verify_cli_same_bytes_at_noncanonical_path_are_rejected`
- `orchestrator/tests/test_s8b_holdout_freeze.py::test_verify_cli_rejects_bytes_changed_while_receipt_is_verified`
- `orchestrator/tests/test_s8b_holdout_freeze.py::test_verify_cli_never_issued_delegates_to_legacy_verify_and_keeps_drift_red`
- `orchestrator/tests/test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control`
- `orchestrator/tests/test_frozen_artifacts.py::test_frozen_artifacts_match_manifest`
- `orchestrator/tests/test_t080_freeze_migration.py::test_state_never_issued_and_present_invalid`
- `orchestrator/tests/test_t080_freeze_migration.py::test_state_active_valid_after_schema_topology_and_all_independent_gates`
- `orchestrator/tests/test_s8b_oracle_driver.py::test_real_freeze_gate_lists_floor_and_budget_null`
- `orchestrator/tests/test_s8b_oracle_driver.py::test_cli_subprocess_returns_rc_2_on_gate_refused`

テストは実走していません。