# 変更点

- [s8c_preregistration.py:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-section5-value-check/orchestrator/campaign/s8c_preregistration.py:125) に定数、violation dataclass、validator tableを追加。
- [s8c_preregistration.py:771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-section5-value-check/orchestrator/campaign/s8c_preregistration.py:771) で値違反を集約し、[s8c_preregistration.py:874](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-section5-value-check/orchestrator/campaign/s8c_preregistration.py:874) に制約検証を実装。
- core/invariantテストへ正負例、全件報告、live doc検査を追加。fixture・既存期待値は未変更。

# 実走結果

pytestは未実走。`git diff --check`、3対象ファイルの静的compile、所有ファイル差分を確認済み。commitも未実施。

# 残る懸念

親によるpytest実走と受入検査が必要。violationは仕様どおり `ActivationReport` と `effective` へ影響させていない。

# 波及の静的列挙

`parse_preregistration_markdown`、`parse_preregistration_at`、`parse_preregistration_worktree` の戻り値に新フィールドが波及する。既存のfreeze record、`ActivationReport`、共有の filled fixture、CLI、`DECIDER_VERSION` は変更していない。docs/outputと所有外ファイルも未変更。

## 総括

段4裁定Eに従う実装を完了した。  
制約違反値はFILLEDのままviolationとして報告する。  
pytestは親に委ね、静的確認のみ実施した。  
所有3ファイル以外は変更していない。