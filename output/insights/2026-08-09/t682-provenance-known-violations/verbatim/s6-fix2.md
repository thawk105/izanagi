## 総括

| 所見 | 状態 | 根拠 |
|---|---|---|
| F-01 | **partial（実装済み・pytest 未実走）** | 正条件と除外集合を追加：[check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:144)、判定 helper：[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:488)、第3診断：[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:588)、回帰テスト：[test_check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1806)。pytest がインフラで開始できなかったため `closed` にはしていない。 |

可視判定は Unicode category の先頭が `L/N/P/S` であり、明示した default-ignorable 相当 9 文字に含まれない文字を最低1つ要求する方式です。

- U+034F と U+FE0F は `Mn` のため正条件を満たしません。
- U+3164 は `Lo` ですが明示除外集合に含むため満たしません。
- U+115F、U+1160、U+17B4、U+17B5、U+2065、U+FFA0 も明示集合で固定しました。
- 既存の `Cc/Cf/Zl/Zp`・zero-width 拒否判定は削除・縮小せず、新条件より先に維持しています。

直接実行による補助確認では、U+034F／U+FE0F／U+3164 はそれぞれ `rc=2` と `non-descriptive required note`、空 note と禁止文字は既存診断のまま `rc=2` でした。production `_known_violation_registry()` は現行30件を例外なく構築し、必須対象22件の実 note はすべて新条件を通過しました。可視文字 `A` と指定9文字の混在 note も通過しています。

変更は以下の2ファイルだけです。

- `tools/check_ai_provenance.py`: 28行追加
- `orchestrator/tests/test_check_ai_provenance.py`: 80行追加。3負例、production 30件正例、混在正例を追加。既存26件の負例表は無変更
- docs、30件の登録値、禁止対象の定数、既存期待値は変更なし。commit も未実施

pytest 実走要求：

- 焦点6 nodeid（展開予定34ケース）：`tools/run_tests.py` が `qstat -Q preflight rc=1`、`rc=16`。収集前停止、実行0件
- bounded-scope 再試行：user bus が `Operation not permitted`、`rc=16`。実行0件
- 必須の全ファイル `orchestrator/tests/test_check_ai_provenance.py`：同じ dispatch preflight 失敗、`rc=16`。実行0件

したがって pytest の緑は未確認です。受入全走と `python3 tools/check_ai_provenance.py` は指示どおり未実行です。所有外への波及は history 監査時の registry 構築だけで、message-file 経路や finding value 判定には変更ありません。親環境で全ファイル pytest と受入検査が必要です。