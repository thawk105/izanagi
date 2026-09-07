## 総括

4件の赤をすべて閉じた。  
対象 prefix のみを正当な `fig<N>_` 形式へ変更した。  
実装側は M3 検証時に一時変異したが、検証後に完全復元しており、恒久変更はない。  
未変異の全62 test が通過した。

## 変更点

- [orchestrator/tests/test_plot_a2_certification.py:710](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-pin/orchestrator/tests/test_plot_a2_certification.py:710): `fig5_missing_pin`
- [orchestrator/tests/test_plot_a2_certification.py:741](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-pin/orchestrator/tests/test_plot_a2_certification.py:741): `fig5_rejected_pin`
- [orchestrator/tests/test_plot_a2_certification.py:940](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-pin/orchestrator/tests/test_plot_a2_certification.py:940): `fig5_changed_certification`
- [orchestrator/tests/test_plot_a2_certification.py:949](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-pin/orchestrator/tests/test_plot_a2_certification.py:949): `fig5_changed_manifest`

## 変異 M3 の期待 node

一時適用した変異は、CLI が指定した certification/raw-manifest 自身の SHA-256 を期待値として `load_measurements` に渡し、repository-owned pin table を迂回するもの。

赤になった node の完全集合は4件で、事前登録の2件から増えた。

- `test_cli_rejects_exact_bytes_at_certification_path_missing_from_pin_table`
- `test_current_cli_reads_repository_owned_pin_table`
- `test_m11_whitespace_changed_certification_fails_cli_with_zero_outputs`
- `test_m12_whitespace_changed_raw_manifest_fails_cli_with_zero_outputs`

結果: `4 failed, 58 passed`。変異は除去済み。

## 実走した検査

- 対象4 node: `4 passed`
- 未変異のファイル全体: `62 passed in 9.63s`
- M11/M12 の zero-output assertion: 両方通過
- `git diff --check`: 通過
- 指示どおり `PYTHONPATH=.` のインライン自走 harness を使用

## 所有外への波及

恒久変更は test file の上記4行だけ。実装 file、凍結成果物、docs、その他の file は変更していない。commit・`git add` も実施していない。

## 未了・申し送り

M3 の期待 node 集合は4件へ張り直しが必要。その他の未了事項なし。