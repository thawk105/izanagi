## 実装

- [s8b_oracle_judge.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2067a-j/orchestrator/campaign/s8b_oracle_judge.py:750): ratified freeze の load 直後、reverify 前に選択 identity 強制を追加。
- 既存の `RatifiedFreezeError` catch を確認済み。拒否文字列を stderr に出し rc=2 とする構造です。
- 従来受理可能だった選択規則違反 g1 のみ新たに拒否します。非 g1 は後段 reverify の `certificate-generation-scope` 拒否のままです。
- [test_s8b_oracle_judge.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2067a-j/orchestrator/tests/test_s8b_oracle_judge.py:728): 実 g1 fixture、走査中立な earlier result helper、3テストを追加。
- 変更は指定された2 fileのみです。

## テスト

- `orchestrator/tests/test_s8b_oracle_judge.py::test_judge_cli_real_g1_rule_mismatch_preserves_selection_reason`
  - earlier `result.json` を `b"{}"` として追加。
  - eligibility 導出のみ True にし、実強制が rc=2、stderr に `floor-selection-rule-mismatch` と規則名を残すことを固定。
- `orchestrator/tests/test_s8b_oracle_judge.py::test_judge_cli_valid_real_g1_reaches_reverify_after_actual_selection_gate`
  - 無変異の実 g1 と実強制を使用。
  - `wraps` spy で selection、reverify の順に到達し rc=0 となることを固定。
- `orchestrator/tests/test_s8b_oracle_judge.py::test_judge_cli_selection_gate_receives_loaded_ratified_and_root`
  - 実 loader と実強制を通す記録 wrapper を使用。
  - `selection_calls == [(loaded_ratified, root)]`、object identity、root の exact `Path` と完全一致を固定。

## 単一帰属の確認

未確認です。通常状態の3 node実走を先に試みましたが、harness がテスト子を起動する前に `qstat -Q preflight rc=1`、dispatch infrastructure failure、rc=16 で停止しました。

`queue_state` も `ENA/STS=不明`、local admission は sandbox から予約台帳を更新できず不成立でした。このため強制行を一時除去した実走もできず、裁定どおり負例を単一帰属確認済みとは扱いません。強制行は削除しておらず、実装位置に残っています。

## 実走

実装済み・未実走です。

試行範囲:

- 追加した3 nodeの焦点走: rc=16、`child_started=false`
- judge file の collect-only: rc=16、`child_started=false`

読み取り検査では両 file の AST parse と `git diff --check` が成功しました。

## 期待して赤になるもの

単位 P の再 pin 待ち:

- `orchestrator/tests/test_s8b_oracle_manifest.py::test_reviewed_spec_has_independent_canonical_bytes_and_sha_literal`
- `orchestrator/tests/test_s8b_oracle_manifest.py::test_build_approved_valid_fixture_output_depends_only_on_spec_pin`

`test_s8b_oracle_report.py` 側で静的に赤を予想する nodeはありません。次の既存 caller は実 g1 を使うため通過する想定ですが未実走です。

- `orchestrator/tests/test_s8b_oracle_report.py::test_judge_cli_reverifies_official_manifest_and_legacy_cannot_reach_verdict`

## 波及

- `test_s8b_oracle_report.py` と既存 judge CLI schema テストが `judge.main()` の callerです。
- 共有 `_ratified_cli_manifest` と `build_production_emitter_g1` を読み取り利用していますが、変更していません。
- judge source hash が変わるため manifest golden の再 pin が必要です。
- loader・manifest verifier の consumer集合、schema、公開 signatureは変更していません。
- library 経路の選択未強制は残件 (c) のままです。

## 総括

judge の公式 CLI に指定どおり選択 identity 強制を追加しました。  
実 g1の負例・正例・引数同一性テストを3本追加しました。  
構文と差分検査は成功しています。  
実走と単一帰属確認は Pegasus infrastructure failureにより未完です。