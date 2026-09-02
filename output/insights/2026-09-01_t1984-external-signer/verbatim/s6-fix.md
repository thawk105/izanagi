## 直したもの

- must-fix 1 — [tools/acceptance_receipt_signature.py:39](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1984-author/tools/acceptance_receipt_signature.py:39)、[同:289](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1984-author/tools/acceptance_receipt_signature.py:289)、[同:378](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1984-author/tools/acceptance_receipt_signature.py:378): production の固定 path を維持し、loader と高水準 API を `load_configured_public_key()` / `verify_configured_key_signed_receipt()` に改称。
- must-fix 1 — [orchestrator/tests/test_external_acceptance_signing.py:169](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1984-author/orchestrator/tests/test_external_acceptance_signing.py:169)、[同:334](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1984-author/orchestrator/tests/test_external_acceptance_signing.py:334): test PEM A/B を固定 test path に配置し、高水準 API の正例、B 署名、環境差し替え、path 欠落、壊れた PEM、非 Ed25519 PEM を実呼出しで検査。test-key control であり production signed-v6 control は unmet と明記。
- must-fix 2 — [tools/acceptance_receipt_signature.py:9](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1984-author/tools/acceptance_receipt_signature.py:9)、[同:98](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1984-author/tools/acceptance_receipt_signature.py:98)、[同:245](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1984-author/tools/acceptance_receipt_signature.py:245): `trusted` / `trust root` を API、型、例外文から除去し、「固定された設定済み公開鍵」の保証範囲に限定。
- must-fix 2 — [tools/acceptance_issuer_reference.py:9](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1984-author/tools/acceptance_issuer_reference.py:9)、[同:336](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1984-author/tools/acceptance_issuer_reference.py:336)、[同:447](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1984-author/tools/acceptance_issuer_reference.py:447): provenance を caller-bound、issuer-derived expectation、未再導出 claim の3群へ分離。特定 issuer の実行や全 claim の再導出を示す文言を削除。
- production fixture は未編集で、SHA-256 は `e4026458e2de2cd1173d214b7cdd1f000eafdc7ef328533efa440c571fd763d4` のままです。

## 実走結果

- `python3 orchestrator/tests/test_external_acceptance_signing.py`: rc=0、16 passed。

  - `test_external_acceptance_signing.py::test_configured_key_boundary_accepts_test_key_A`
  - `test_external_acceptance_signing.py::test_configured_key_boundary_rejects_attacker_key_B_signature`
  - `test_external_acceptance_signing.py::test_configured_key_boundary_rejects_malformed_pem`
  - `test_external_acceptance_signing.py::test_configured_key_boundary_rejects_missing_fixed_path`
  - `test_external_acceptance_signing.py::test_configured_key_boundary_rejects_non_ed25519_pem`
  - `test_external_acceptance_signing.py::test_configured_key_loader_ignores_environment_substitution`
  - `test_external_acceptance_signing.py::test_different_public_key_is_rejected`
  - `test_external_acceptance_signing.py::test_missing_issuer_signature_is_rejected`
  - `test_external_acceptance_signing.py::test_recorded_production_v5_receipt_passes_canonical_projection`
  - `test_external_acceptance_signing.py::test_recorded_projection_rejects_missing_v5_root_field`
  - `test_external_acceptance_signing.py::test_reference_issuer_parses_recorded_canonical_v5_fixture`
  - `test_external_acceptance_signing.py::test_signed_receipt_replay_into_other_context_is_rejected`
  - `test_external_acceptance_signing.py::test_signed_receipt_replay_to_other_tested_tip_context_is_rejected`
  - `test_external_acceptance_signing.py::test_signed_v6_signature_covers_every_root_field_except_itself`
  - `test_external_acceptance_signing.py::test_unsigned_tested_tip_tamper_is_rejected`
  - `test_external_acceptance_signing.py::test_valid_test_signature_and_exact_context_pass`

- `python3 orchestrator/tests/test_plain_runner_coverage.py`: rc=0、3 passed、0 skipped。

  - `test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries`
  - `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
  - `test_plain_runner_coverage.py::test_this_metatest_is_itself_self_runnable`

## 負例の単一理由性

- 攻撃者鍵 B: receipt の key ID は A に合わせ、schema/context も有効にしたため、赤の理由は Ed25519 署名不一致だけです。単一理由。
- 環境差し替え: loader の実呼出しが A の key ID を返すことを先に検査します。環境由来 B を読む変異ではこの一点で赤になります。単一理由。
- 固定 path 欠落: 正常な A 署名 receipt を使い、`configured public key is unavailable` の exact message を要求。単一理由。
- 壊れた PEM: 存在する通常ファイルを使い、PEM decode の `configured public key format is invalid` だけを要求。単一理由。
- 非 Ed25519 PEM: parse 可能な RSA public PEMを使い、鍵種別の `configured public key is not Ed25519` だけを要求。単一理由。
- 高水準検証迂回と環境選択 loader をプロセス内変異として注入し、上記5 control がすべて赤になることを確認しました（mutation audit rc=0）。
- 既存の「署名なし」負例は従来どおり exact-schema gate で先に赤になる冗長 gateであり、Ed25519 検証の証拠には数えません。

## 総括

must-fix 1/2 のみを、指定された3ファイル内で修正しました。  
固定された production 公開鍵 path と production の受理集合は変更していません。  
禁止ファイルおよび production fixture は未編集です。  
自走 harness は16/16、plain-runner coverage は3/3で緑です。  
これは test-key control であり、production signed-v6 positive control と D906 enforcement は unmet のままです。  
commit、add、stash は実行していません。