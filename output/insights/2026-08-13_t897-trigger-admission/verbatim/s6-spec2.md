作成しました: [mutation-spec.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/output/insights/2026-08-13_t897-trigger-admission/mutation/mutation-spec.json)

各 anchor と完全集合の根拠:

- M1: caller 前後を含む逐語 anchor が HEAD で1件。負例21件 + read-once + 診断順序 + AST = 24 node。
- M2: `_source_map(expected_source)` 前後の anchor が1件。runtime recheck + AST = 2 node。
- M3: hole membership 節が1件。実 fixture probe で空白3 parameterだけを受理し、runtime recheck・診断順序と合わせて5 node。
- M5: `for mask in range(32)` が1件。mask-31 と同 mask を使う runtime recheckの2 node。
- M6-prime: 同 anchor が1件。mask-0のみ1 node。
- M7: frame/hole 検査全体の anchor が1件。実 parametrize bytes probeで N01/N02/N05/N09/N10/N11/N14 の7件だけを受理。
- M8: `except OSError` 節が1件。non-ENOENTをno-op化し、該当 read-failure nodeのみ1件。
- M9: marker不在・骨格token節が1件。N04/N08のみ2 node。
- M10: marker pair条件が1件。一意性だけを外すとN13/N15のみ2 node。
- M11: pristine fast-pathが1件。pristine正例のみ1 node、categoryは`positive`。

M4-primeは冗長gateとして未登録、`test_campaign.py`の12 nodeも対象外です。推測箇所はありません。

検証結果:

- 指定されたJSON load command: rc=0
- 固定HEAD `01d17293b90bbd6f66475d8578e384618fe686b9` に対するregistration preflight: 10件すべてanchor count=1
- 各変異後sourceのメモリ上compile: 成功
- UTF-8 NFC・最終改行: 確認済み
- 変更範囲: 指定成果物1ファイルのみ
- commit・Web検索・変異本走: 未実施
- SHA-256: `1bcfa41df19517884f86dbd47674cdba6453c9d81e6e1f85f803f835cb5c7619`

## 総括

T-897の段6変異specを、指定された10変異・期待node完全集合・runner見積りでrepo内に作成し、固定HEAD逐語性とJSON妥当性まで確認しました。