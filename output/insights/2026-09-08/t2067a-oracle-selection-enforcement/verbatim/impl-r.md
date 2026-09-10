## 実装

- [s8b_oracle_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2067a-r/orchestrator/campaign/s8b_oracle_report.py:2548): ratified freeze の load 直後、reverify 前に選択 identity 強制を追加。
- `RatifiedFreezeError` は既存 catch 対象で、拒否理由を stderr に出して rc=2 にする構造を確認。
- [test_s8b_oracle_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2067a-r/orchestrator/tests/test_s8b_oracle_report.py:1659): 走査中立な earlier result `b"{}"` と eligibility seam を追加。
- 変更は指定された2ファイルのみ。report の現 SHA-256 は `30fe2b1bcad143f5a85ca32250744522d6049f4c71e9b853618e3af2dd0091c7`。

## テスト

- `test_cli_official_resolves_ratified_freeze_and_verifies`
  - 無変異の実 g1 で実強制を `wraps` し、selection後にreverifyへ到達する順序を固定。
- `test_report_cli_real_g1_rule_mismatch_preserves_selection_reason`
  - earlier eligible result により rc=2、stderrの`floor-selection-rule-mismatch`、出力未作成を検査。
- `test_report_cli_selection_gate_receives_loaded_ratified_and_root`
  - `selection_calls == [(loaded_ratified, root)]`、ratifiedのobject同一性、Path型とroot完全一致を明示。

## 単一帰属の確認

強制行を一時的に削除し、負例nodeを自走harnessで起動しました。しかしテストchild開始前にPegasus dispatchが失敗しました。

- runner rc: `16`
- child: 未開始
- 理由: login-node headroom不足後、`qstat -Q` preflightがsocket作成拒否で失敗

したがって、強制行なしでrc=0へ到達することは未確認です。強制行は直後に復元済みで、単一帰属を確認済みとは扱いません。

## 実走

実装済み・未実走です。

3 nodeの焦点走、collection、強制行除去時の負例走はいずれもテストchild開始前にrc=16となりました。静的にはAST parseと`git diff --check`が成功しています。

## 期待して赤になるもの

単位Pの再pin待ちで、次のnodeは赤になる想定です。

- `orchestrator/tests/test_s8b_oracle_manifest.py::test_reviewed_spec_has_independent_canonical_bytes_and_sha_literal`
- `orchestrator/tests/test_s8b_oracle_manifest.py::test_build_approved_valid_fixture_output_depends_only_on_spec_pin`

## 波及

- report `main()` の既存callerである`test_s8b_oracle_report.py`各CLI testと、`test_s8b_oracle_driver.py::test_transient_prepare_failure_retries_once`。
- `_ratified_cli_manifest`を利用するjudge/verdict test。helperのsignatureと戻り値は変更していません。
- report source hashを束縛するoracle manifestのgenerator pin。
- `test_official_perf_closure.py`、`test_s8b_oracle_manifest_contract.py`、`test_s8b_oracle_artifacts.py`の構造検査。静的には期待集合を変えませんが未実走です。
- legacy report経路は対象外。非g1は強制関数では観測されず、従来どおり後段reverifyが拒否します。

## 総括

production強制と3検査点は実装済みです。  
編集範囲は所有2ファイルのみです。  
強制行は最終状態へ復元済みです。  
実走と単一帰属確認は環境要因で未完了のため、closedとは報告しません。