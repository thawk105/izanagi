## 実装したもの

- [acceptance_receipt_signature.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1984-author/tools/acceptance_receipt_signature.py:1)
  - v5 の exact 27 field から signed-v6 payload を構築。
  - `issuer_signature` を除く全 30 root field を launcher 同等の canonical JSON にして署名対象化。
  - `lease_generation` は `[0-9a-f]{64}` の検証だけで、production lease には未配線。
  - 固定外部 PEM path の trust-root loader、Ed25519 検証、wave/main/tip/lease context 束縛を実装。
  - `cryptography` の既存利用・依存宣言がなかったことと、import failure が fail-closed になることを docstring に明記。

- [acceptance_issuer_reference.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1984-author/tools/acceptance_issuer_reference.py:1)
  - `tested_main` の launcher blob を自ら読み、実行して v5 receipt を取得。
  - main/tip の実在、launcher/waiter/runner/checker blob bytes、log hash を再導出して照合。
  - 固定外部秘密鍵で signed-v6 を発行。秘密鍵 bytes はログ・例外文・戻り値に出さない。
  - 独立再導出 field と待ち手自己申告 field を docstring の2表に分離。
  - production waiter/land からの caller は追加していない。

- [test_external_acceptance_signing.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1984-author/orchestrator/tests/test_external_acceptance_signing.py:1)
  - 自走 harness、production projection control、署名なし・鍵違い・改竄・別 context の負例を実装。
  - test key の正例は production control として扱わない旨を明記。

- [production-acceptance-receipt-v5.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1984-author/orchestrator/tests/fixtures/production-acceptance-receipt-v5.json:1)
  - 射影された production sample と byte-for-byte 同一。`cmp` rc=0。
  - 禁止された `git add` はしていないため、親が追跡対象へ追加する前の untracked 状態。

production の現行挙動は不変です。有効な unsigned-v5 は従来どおり受理され、不正な field/context/blob/verdict は拒否されます。signed-v6 はまだ production land に配線されておらず、現行 land では extra field/schema mismatch として拒否されます。

## 実走結果

自走 harness `python3 orchestrator/tests/test_external_acceptance_signing.py` は rc=0、11 passedです。実走 nodeid は以下です。

- `test_external_acceptance_signing.py::test_recorded_production_v5_receipt_passes_canonical_projection`
- `test_external_acceptance_signing.py::test_recorded_projection_rejects_missing_v5_root_field`
- `test_external_acceptance_signing.py::test_reference_issuer_parses_recorded_canonical_v5_fixture`
- `test_external_acceptance_signing.py::test_valid_test_signature_and_exact_context_pass`
- `test_external_acceptance_signing.py::test_missing_issuer_signature_is_rejected`
- `test_external_acceptance_signing.py::test_different_public_key_is_rejected`
- `test_external_acceptance_signing.py::test_unsigned_tested_tip_tamper_is_rejected`
- `test_external_acceptance_signing.py::test_signed_receipt_replay_into_other_context_is_rejected`
- `test_external_acceptance_signing.py::test_signed_receipt_replay_to_other_tested_tip_context_is_rejected`
- `test_external_acceptance_signing.py::test_signed_v6_signature_covers_every_root_field_except_itself`
- `test_external_acceptance_signing.py::test_trust_root_path_is_fixed_and_environment_independent`

`python3 orchestrator/tests/test_plain_runner_coverage.py` は rc=0、3 passed、0 skippedです。

- `test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries`
- `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
- `test_plain_runner_coverage.py::test_this_metatest_is_itself_self_runnable`

`tools/run_tests.py` 経由の上記2 file 走は rc=16でした。Pegasus の `qstat -Q` preflight failure で child は起動していないため、pytest 走は「実装済み・未実走」であり、緑には数えていません。親の全走も未実走です。

`git diff --check`、行長検査、fixture 同一性検査、issuer CLI import/help は rc=0でした。

## 恒真化の自己検査

D431 の退化型はありません。

- production fixture と projected canonical payload の SHA-256・byte lengthを、test source 内の独立 literal と照合。
- 同じ projection へ root field 欠落入力を渡す反対クラスを置き、双方受理なら test が失敗する構造。
- 鍵違い負例は、receipt の key ID を別 public key に合わせた上で署名検証を失敗させており、key-ID 比較だけの偽緑ではない。
- 改竄負例は expected tip も改竄値に合わせ、context gate ではなく署名 coverage が拒否することを確認。
- 正しい署名を別 lease generation と別 tested tip の双方へ再送し、context 比較が拒否することを確認。
- 各負例は「例外が起きなければ test 自体が失敗する」`_assert_rejected` を通過。

人手 issuer による production signed-v6 positive control は未充足です。runtime test key の正例を production control と呼んでいません。

## 波及

既存 caller はありません。後続 activation wave が production waiter/land、実 lease generation、外部 operational issuer・鍵配置を同時に接続する必要があります。`cryptography` がない環境では新 module import が例外で停止しますが、production 経路は新 moduleを importしていません。

共有 fixture は新規専有 fileのみで、既存 fixtureは未変更です。consumer testへの静的波及は pytest discovery と plain-runner inventoryへの新 test file追加だけで、plain-runner meta-testは実走済みです。

禁止 file は個別 SHA-256 を開始時と最終時に比較し、すべて不変でした。

- `orchestrator/tests/test_dev_wave_land.py`
- `tools/dev_wave_land.py`
- `tools/dev_wave_wait.py`
- `tools/acceptance_launcher.py`
- `tools/wave_land_window.py`
- `hooks/guard_write.py`
- `hooks/guard_bash.py`
- `orchestrator/campaign/artifact_admission.py`
- `orchestrator/campaign/campaign_lock.py`
- `orchestrator/campaign/contract_loader_binding.py`

`docs/` 配下にも変更はありません。Git-visible な変更は指定された4新規 fileだけです。commit/add/stash/push/branch/merge は実行していません。

## 総括

【機構追加・未強制】署名 library、reference issuer、production fixture、負例付き testを追加しました。  
production land の署名必須化と lease generation 配線は行っていません。  
既存 unsigned-v5 の受理集合は1 bitも変更していません。  
自走 harnessは11/11、plain-runner meta-testは3/3で成功しました。  
公式 runnerはchild未起動のrc=16であり、pytest範囲は実装済み・未実走です。  
production signed-v6 controlとD906 enforcementは未閉鎖です。