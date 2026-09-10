F1〜F3 をテスト側だけで修正しました。production、docs、既存期待値は変更せず、commit も作成していません。

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | closed | `_campaign_file` が `M.ROOT` 配下の絶対 Path を返すよう修正 |
| F2 | closed | `generate()` の全収集関数と metadata 取得を hermetic mock 化 |
| F3 | closed | `static_gate_adapter` から実 `_verify_known_schema` へ到達する意味負例を追加 |

- F1: [test_s1_known_axes_freeze.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s1_known_axes_freeze.py:51)
  - 検査呼び出しを削除すると `relative_to(M.ROOT)` が成功し、mock 済み source 構築を経て `_trigger_entries()` が正常 return します。
  - したがって負例は「期待した `FreezeError` が発生しない」という正しい理由で赤くなり、`ValueError` による偽 kill はありません。

- F2: [test_s1_known_axes_freeze.py:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s1_known_axes_freeze.py:165)
  - `_backoff_entry`、`_sort_entry`、Git/hash 取得を追加で mock し、provenance/path mock は全 workload の呼び出しに応答します。
  - gate/ident の flags は同一、predicate は相違するため pairing を通過します。検査削除変異では `generate()` が非正準 doc を実際に書き、`pytest.raises` が「例外なし」で赤くなります。

- F3: [test_s8b_oracle_driver.py:1043](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s8b_oracle_driver.py:1043)
  - 到達済み: `static_gate_adapter` → `_verify_known_schema` → `_validate_schema`。
  - `known_axes.artifact_bytes` と `known_axes.schema ...正準集合外` の拒否集合を完全一致で固定しました。schema 配線または検査を削除すると schema refusal が消えるため、正しい理由で赤くなります。
  - 未到達: 公開 `driver.gate_check()` end-to-end。改竄 raw bytes は adapter 前の legacy pin 検査で拒否されるためです。SHA 定数の monkeypatch はしていません。

波及可能性は次のとおりです。

- 共有 fixture は変更せず、F3 は既存 receipt helper と凍結 artifact を読み取り利用するだけです。
- conftest の real-repo allowlist 追加は不要です。新テストは repo 状態を変更しません。
- S1 の plain-runner meta-test は新規 `tmp_path` node を既存機構で収集できます。
- 独立 golden と frozen manifest は未変更で、既存の六述語 exact 固定も維持されています。
- 既存 G7 是正とその refusal 期待値は変更していません。

静的確認として、両テストファイルの `py_compile`、`git diff --check`、mock 対象の実在、adapter の呼び出し順、known/holdout artifact と固定 SHA-256 の一致を確認しました。

## 総括

修正の骨子: repo 内絶対 Path、完走可能な `generate()` mock、実 adapter schema refusal の3点で偽 killを除去しました。

実走状況: 実装済み・pytest 未実走です。構文検査と差分検査のみ完了しています。

親が実測すべき node: F1 の2負例、`test_generate_rejects_noncanonical_predicate_before_writing`、`test_t080_static_adapter_rejects_noncanonical_known_predicate_as_schema` の計4 nodeです。