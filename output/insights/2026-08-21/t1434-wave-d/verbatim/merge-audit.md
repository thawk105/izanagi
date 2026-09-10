## 検証結果

### [orchestrator/tests/conftest.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/t1434-wave-d/orchestrator/tests/conftest.py:386>) — `safe-union`

- 自 wave は `@@ -385,0 +386 @@` の1行追加のみ。
- main 側の hunk は旧座標で `343-367` の削除、追加位置 `403, 507, 516, 572, 739, 761, 787, 981, 984, 995, 1429`、および `1389-1395` の置換であり、旧座標385とは重複しない。
- 新座標では自 waveの `+386` と main側の `+379,31` が数値上重なるが、main側の24行削除による行番号移動であり、共通親上のhunk衝突ではない。
- 自 waveは既存の `frozenset` へ完全な文字列リテラルを1行追加するだけ。main側の24 node削除、別 `ORACLE_ENVIRONMENT_CONSUMER_NODES` 定義、補助関数追加もブロック単位で完結しており、union後のPython構造は妥当。
- 自 waveのnodeは `test_codex_reasoning_ab.py::test_validate_schedule_legacy_different_arm_same_model_pair_remains_valid`。main側24 nodeはすべて `test_sort_swo_oracle.py::...` で、重複しない。

### [orchestrator/tests/test_real_repo_serialization.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/t1434-wave-d/orchestrator/tests/test_real_repo_serialization.py:126>) — `safe-union`

- 自 waveは `@@ -125,0 +126 @@` の1行追加のみ。
- main 側の旧座標hunkは `9`、`15`、削除範囲 `84-107`、追加位置 `146`、`1342`、`1948`。自 waveの旧座標125とは重複しない。
- 新座標では自 waveの `+126` と main側の `+126,30` が重なるように見えるが、main側の24行削除後の座標であり、共通親上の変更位置は別。
- main側の `_REAL_REPO_SERIAL_NODES_GOLDEN` から24 nodeを除去し、`ORACLE_ENVIRONMENT_CONSUMERS_GOLDEN` に同じ24 nodeを追加する。自 waveは別ファイルnodeをgoldenへ1件追加するだけで、frozenset構文は壊れない。
- main側の追加テスト・helper hunkも自 waveのgolden追加位置とは独立しており、diff内容からPython構文上の未閉鎖ブロックや行内衝突は見当たらない。

## 総括

両commitは同じ共通親からの差分である。  
hunkの旧座標を比較すると、両ファイルとも変更位置は重複しない。  
新座標の見かけ上の重複は、main側の24行削除による行番号再計算で説明できる。  
自 waveは同じcodex reasoning nodeをregistryとgoldenへ1件追加する。  
main側はsort-SWOの24 nodeを別のfrozensetへ移設する。  
node名の接頭辞も異なり、相互の集合重複はない。  
差分内容から推論したunionのPython構文も妥当である。  

結論: union は安全です。