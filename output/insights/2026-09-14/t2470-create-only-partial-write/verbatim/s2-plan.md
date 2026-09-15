## 方針と確認結果

`orchestrator/campaign/trial_registry.py` の `_write_create_only` に、**排他的な作成成功後の失敗だけを対象とする unlink** を追加する。変更先は同ファイルと `orchestrator/tests/test_trial_registry.py` のみ。以下の行番号は現行コードを静的に確認したもの。

指定された必読資料はすべて読み取り可能だった。編集・commit・pytest 実行はしていない。

親 brief の caller 列挙は正しい。ただし、**P2 の「分類受領証 reader は 0 件」は誤り**。`trial_registry.py:2311` の `_assert_attempt_classification_receipts` が、`:2327` で実ファイルを読み、`:2332` 以降で digest・改行・canonical JSON 等を検証している。呼び出し元は `_assert_attempt_registry_rows` の `:2304`。書き込み失敗時は分類行追加より前に止まるため、本件の再試行阻害という説明は成立するが、reader 不在を根拠にはできない。

## caller の独立列挙と挙動差分

`trial_registry.py` 内の `_write_create_only(` は、定義 1 件、呼び出し **2 件**だった。

| 関数・定義行 | writer 呼び出し・gate | 書き込み先（repository root 相対） | production 入口 |
|---|---|---|---|
| `create_attempt_registry_genesis` `:2471` | `:2530`、`attempt-registry-genesis` | `output/s8c-preregistration/attempt-registry.jsonl`。定数 `:61`、canonical path 強制 `:2425` | 同ファイル `main` `:6502` → `genesis` 分岐 `:6544` → `:6559` |
| `classify_attempt` `:3254` | `:3288`、`attempt-classification-receipt` | `output/s8c-trial-registry/classification-receipts/<receipt_digest>.json`。layout `:2187`、digest・path 構築 `:3282` | `p3_autonomous_workload_trial.py` の `run_trial` `:4614` → `:4876` |

`classify_attempt_failure = classify_attempt`（`:3336`）は別名であり、第 3 の writer caller ではない。別名を呼ぶ production 箇所は検索で見つからなかった。親の caller 名・行番号・gate・path に漏れや誤りはない。

| caller | 修正後に通るようになる再試行 | 修正前後で変わらない入力・結果 |
|---|---|---|
| genesis | 有効な引数で初回作成後に write/fsync が失敗し、撤去が成功した後の**同じ引数**による再試行 | 初回正常作成の bytes、既存ファイルがある場合の拒否、不正な generation・slot・path 等の拒否 |
| 分類受領証 | 有効な capability と分類引数で writer が失敗し、撤去が成功した後の**同じ capability・同じ引数**による再試行 | 正常時の受領証 bytes・分類行追加、既存受領証への拒否、不正入力の拒否 |

分類経路では writer の後に分類行追加（`:3322`）と capability 更新（`:3327`）がある。今回の注入失敗ではこれらに到達しない。既に残っている旧残骸の自動回収や、writer 成功後の分類行追加失敗からの復旧は対象にしない。

## 実装プラン

修正位置は `trial_registry.py:2451–2461`。`os.open` と `FileExistsError` 処理（`:2447–2450`）を cleanup の対象外に保ち、既存の内側 `try` に `except BaseException` を追加する。

```python
# O_EXCL による作成が成功した後だけ到達する
try:
    # 現行の memoryview、write loop、
    # fsync(fd)、fsync(parent_fd) をそのまま残す
    ...
except BaseException:
    try:
        os.unlink(relative_path.name, dir_fd=parent_fd)
    except OSError:
        pass
    raise
finally:
    os.close(fd)
```

- **所有 flag は追加しない。** `os.open` 成功後だけこの `try` に入る構造自体を所有条件とする。staging/publish がないため、先例の `published` flag は不要。
- `:2452–2459` の bytes 処理、短い write の反復、進捗なしの拒否、`fsync(fd)` → `fsync(parent_fd)` の順序は変更しない。
- cleanup は `relative_path.name` と既に開いた `parent_fd` を使う。絶対パスでの unlink や `Path.unlink()` に置き換えない。
- unlink の `OSError` は元例外を置き換えず、最後の裸の `raise` で元例外を再送出する。unlink 自体が失敗した場合、残骸撤去・再試行成功までは保証できない。
- `BaseException` を拾う。write/fsync 中の `KeyboardInterrupt` 等でも、作成済みファイルを残す問題は同じだからである。cleanup 後はその例外をそのまま送出し、`TrialRegistryError` に変換しない。
- cleanup → `os.close(fd)` → 外側の例外処理 → `os.close(parent_fd)` の順になる。親 fd を閉じてから unlink しない。

既存の外側三段構えとの関係は次のとおり。

| 現行処理 | 修正後 |
|---|---|
| `:2462` `except TrialRegistryError: raise` | 維持。`FileExistsError` 由来の既存パス拒否もここを通る。unlink には到達しない |
| `:2464` `except OSError as exc` | 維持。cleanup 後に元の write/fsync エラーを既存メッセージの `TrialRegistryError` に変換し、`__cause__` に保持 |
| `:2466` `finally: os.close(parent_fd)` | 維持。cleanup 中は親 fd が有効 |

通常の fd close 処理は変更しない。close 自体の障害対応や cleanup 後の追加 fsync は本プランへ広げない。

先例 `tools/issue_env_contract_activation.py:108` の `BaseException` cleanup は参考になる。一方、`:130–134` の cleanup エラーによる例外置換は今回の不変条件と異なるため採用しない。staging・hard-link publish も採用しない。

## 正例テストの設計

追加先はすべて `orchestrator/tests/test_trial_registry.py`。正規の I/O 失敗注入 seam は確認できなかった。writer は `os.write`・`os.fsync` を直接呼び、引数にも注入機構がないため、`monkeypatch.context()` を使う。

`:6801` の `_genesis_cli_fixture` 後を追加位置とし、次のテストを作る。

`test_attempt_create_only_failure_removes_residue_and_allows_retry`

明示的な parameter ID を付け、次の 6 nodeid にする。

| caller | failure point |
|---|---|
| `genesis` | `write`、`file_fsync`、`directory_fsync` |
| `classification` | `write`、`file_fsync`、`directory_fsync` |

例：`test_attempt_create_only_failure_removes_residue_and_allows_retry[classification-directory_fsync]`。

各 nodeid 内で、**失敗注入 → 対象ファイル不在 → 同じ引数で再試行成功**まで完結させる。

1. genesis は `_genesis_cli_fixture`（`:6772`）で未作成の正規入力を準備し、generation 2 を含む固定 kwargs で公開 API を呼ぶ。
2. 分類は `_attempt_fixture`（`:6117` 付近）と `_reserve_attempt` を使い、既存テスト `:7158–7165` と同じ有効な分類引数を固定する。注入前に fixture・予約を完了する。
3. 期待 bytes は genesis の正規 row、または `_attempt_receipt_payload` による受領証から組み立てる。受領証の対象 path はその bytes の SHA-256 から求める。
4. `write` は最初の呼び出しで本物の `os.write(fd, raw[:1])` を実行し、次の呼び出しで固定の `OSError` インスタンスを送出する。失敗直前に実際の部分 bytes を確認する。
5. fsync は `os.fstat(fd)` で通常ファイル／ディレクトリを識別し、指定種類で一度だけ失敗させる。他の呼び出しは本物へ委譲する。
6. `TrialRegistryError` の gate・失敗メッセージと、`__cause__ is injected_error` を確認する。
7. patch を解除し、対象 path が不在であることを確認する。分類の場合は台帳 bytes と capability の分類状態も注入前のままであることを確認する。
8. 固定した同じ引数で再試行し、対象 bytes が期待 bytes と完全一致することを確認する。分類では追加された分類行と受領証 digest の対応も確認する。

先例 `test_env_contract_activation.py:2586–2628` の構造を使うが、先例が再試行時に payload を変えている点は踏襲しない。

同じ追加位置に、不変条件を直接検証する次の小さな writer テストも置く。

| 新規 nodeid | 検証 |
|---|---|
| `test_create_only_unlink_failure_preserves_original_error` | 部分 write 失敗に加え unlink を `OSError` にする。送出される `TrialRegistryError.__cause__` は元 write エラーのまま |
| `test_create_only_interrupt_removes_residue_and_allows_retry` | 部分 write 後に `KeyboardInterrupt`。同じ例外の伝播、対象不在、注入解除後の同一 payload 再試行成功 |
| `test_create_only_success_preserves_bytes_and_fsync_order` | 本物の短い write を繰り返し、最終 bytes と fsync の順序 `[file, directory]` を確認 |

正例の unlink wrapper は本物へ委譲しつつ、basename と `dir_fd` が指定され、その fd が期待する親ディレクトリを指すことも確認する。これで相対撤去の契約を検証する。

## 負例テストと既存期待値

| 既存 nodeid | 現在の担保 | 今回の扱い |
|---|---|---|
| `test_attempt_registry_genesis_is_closed_before_first_performance_observation`（`:6750`） | 2 回目の公開 API が `TrialRegistryError`。その後に台帳を読める。完全な bytes 比較はない | `:6754` 前に bytes を保存し、`:6762` 後に完全一致を追加。新しい重複 nodeid は作らない |
| `test_genesis_cli_rejects_second_creation_without_changing_bytes`（`:6833`） | CLI 2 回目の終了コード 2、既存パス拒否メッセージ、`:6849` で bytes 完全保持 | 変更せず焦点走に含める |
| `test_attempt_registry_classification_receipt_is_create_only`（`:7157`） | 2 回目の分類が既存パス拒否。受領証の残存・bytes は未確認 | 現状維持。欠けている保持保証だけ新規 nodeid にする |

`:7169` 後に `test_attempt_registry_classification_rejection_preserves_receipt_bytes` を追加する。

既存テストと同じ手順で正常分類を一度行い、完成した受領証の path と bytes を保存する。同じ capability・kwargs で再度呼び、`TrialRegistryError` と `create-only path already exists` を確認した後、同じ path の `read_bytes()` が保存値と完全一致することを確認する。これは削除も 1 bit の変更も検出する。

genesis の既存 nodeid への追加 assertion と分類の新規 nodeid により、両公開 API で「既存完成物を消さない」を直接検証する。

**既存の期待値変更は不要。** 静的確認で、本修正のために期待値を変更すべき既存テストは見つからなかった。既存パス拒否・bytes 同値の期待が通らなくなった場合は実装を見直す。

## 波及の静的列挙と焦点走

worktree 内で `_write_create_only`、公開 caller 名、module import、テスト間参照を検索した。対象 writer を直接呼ぶ既存テストはなく、公開 API 経由だった。

| 段 | 実際の参照 | 焦点走への判断 |
|---|---|---|
| writer → 公開 API | `trial_registry.py:2530,3288` | `test_trial_registry.py` 全体 |
| 公開 API → 等価性テスト | `test_attempt_registry_core_equivalence.py:392,414`。`:447` のテストで core・facade の event/receipt bytes を比較 | 含める |
| genesis → production fixture | `test_p3_autonomous_workload_trial.py:7070`、`_t325_prepare_effective_binding`（`:7050`） | 含める |
| genesis → origin fixture | `test_reflux_origin_binding.py:339` | 含める |
| 上記テスト fixture → 別テスト | `test_reflux_originless_compatibility.py:13` が p3 テストを import、`:48,133` で fixture 利用、`:72,136` で production 実行 | 含める。テスト間参照も 2 段確認済み |
| production module → completeness テスト | `test_autonomous_trial_completeness.py:25,931,983` | 含める |
| facade → 静的契約検査 | `test_attempt_registry_core_s8b_profile.py:2049` の facade rebinding 検査 | 含める |
| production source → preregistration evidence → テスト | `s8c_preregistration_evidence.py:1636` の genesis 名参照等 → `test_s8c_preregistration_predicates.py:24`、`test_s8c_preregistration_core.py:3235` 以降、invariant の source mapping | 3 ファイルを含める |

したがって焦点走の提案集合は、`orchestrator/tests/` 配下の次の 10 ファイル。

- `test_trial_registry.py`
- `test_attempt_registry_core_equivalence.py`
- `test_p3_autonomous_workload_trial.py`
- `test_reflux_origin_binding.py`
- `test_reflux_originless_compatibility.py`
- `test_autonomous_trial_completeness.py`
- `test_attempt_registry_core_s8b_profile.py`
- `test_s8c_preregistration_predicates.py`
- `test_s8c_preregistration_core.py`
- `test_s8c_preregistration_invariant.py`

追加の module 名・source path 参照として、`test_p3_s4_loop.py`、`test_p3_s4_loop_trigger_gating.py`、`test_role_session_isolation.py`、`test_reflux_formal_consumer.py`、`test_campaign.py`、`test_t671_source_binding.py`、`test_layer3_report.py`、`test_layer3_admission_diagnosis.py`、`test_claude_transport.py`、`test_s8c_arm_inputs.py`、`test_p3_build_authority_cli.py`、`test_p3_exploration_namespace.py`、`test_holdout_observation.py`、`test_artifact_admission.py`、`test_s8c_budget.py` が検索に掛かった。これらは今回の 2 caller への直接参照とは区別し、親の受入全走で扱う。

同名 `_write_create_only` の別実装は、campaign の `backoff_overthrottle`、`backoff_requested_us`、`mocc_trace_pair`、`mocc_trace_pair_anchor`、`s8b_oracle_report`、`s8b_oracle_judge`、`s8b_verdict`、tools の `issue_env_contract_activation`、`pegasus/t810_coordinator`、`pegasus/run_probe`、`pegasus/probes/t293_perf_site_probe`、テストの `reflux_origin_fixture_builder` に存在する。その参照テスト `test_backoff_overthrottle.py`、`test_backoff_requested_us.py`、`test_env_contract_activation.py`、`test_pegasus_tools.py` は対象 writer の consumer ではない。

`s8b_attempt_registry` と `attempt_registry_core` の同名公開 API も別実装であり、それだけを理由に横展開や焦点走追加はしない。上記は実行候補の静的整理で、成功結果ではない。

## 変異事前登録の候補

以下の nodeid はすべて `orchestrator/tests/test_trial_registry.py::` を接頭辞とする。新規行番号は未確定のため現行行の挿入位置で指定する。

| # | 変異箇所・書き換え | 赤になるべき nodeid と理由 |
|---|---|---|
| 1 | `:2460` 前に追加する cleanup の `os.unlink(...)` を削除 | `test_attempt_create_only_failure_removes_residue_and_allows_retry[genesis-write]`。残骸不在 assertion が失敗 |
| 2 | `:2449` の `FileExistsError` handler にも unlink を追加 | `test_attempt_registry_classification_rejection_preserves_receipt_bytes`、強化後の `test_attempt_registry_genesis_is_closed_before_first_performance_observation`、既存 CLI 負例。完成物が消えて失敗 |
| 3 | `:2459` の `fsync(parent_fd)` を cleanup 対象の `try` の外へ移す | `test_attempt_create_only_failure_removes_residue_and_allows_retry[classification-directory_fsync]`。親 fsync 失敗の残骸が残る |
| 4 | 新規 unlink を `os.unlink(repository_root / relative_path)` に変更 | `test_attempt_create_only_failure_removes_residue_and_allows_retry[genesis-file_fsync]`。unlink wrapper の basename・親 fd assertion が失敗 |
| 5 | 新規 `except OSError: pass` を `except OSError: raise` に変更 | `test_create_only_unlink_failure_preserves_original_error`。`__cause__` が cleanup エラーに変わる |
| 6 | 新規 `except BaseException` を `except Exception` に変更 | `test_create_only_interrupt_removes_residue_and_allows_retry`。割り込み後に残骸が残る |
| 7 | 新規 cleanup 末尾の裸の `raise` を削除 | `test_attempt_create_only_failure_removes_residue_and_allows_retry[genesis-write]`。期待する `TrialRegistryError` が送出されない |
| 8 | `:2458–2459` の fsync 順序を逆転 | `test_create_only_success_preserves_bytes_and_fsync_order`。順序 assertion が失敗 |

特に変異 2 は、例外が出ることだけでは殺せない。既存 path の bytes を**拒否後に再読込する負例**で検出する。

## 総括

修正は、O_EXCL 成功後の内側 `try` に cleanup を加える最小差分とする。両 caller の 3 注入点で同一引数の再試行を検証し、既存完成物の完全保持・元例外保持・相対 unlink・fsync 順序も確認する。

親 brief の caller 列挙は確認できたが、受領証 reader 不在という P2 は訂正が必要。実装・テスト実走・変異実走は未実施であり、緑の主張はしない。