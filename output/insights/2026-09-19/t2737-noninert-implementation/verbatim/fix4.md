## 総括

**実装済み・未実走。** 所有ファイルのみ12行追加・1行削除。`git diff --check` は成功しました。

修正前は、新規 guard を除外し、値付き既定値・変更ファイルの guard は候補に残す一方、escape.hh 型の `#if X + 0` からも X が落ちていました（静的確認・focus3実測）。

| 所見 | 状態 | 結果 |
|---|---|---|
| 除外射程の修正 | partial | `include_guards[start + first]` の1行に限定。(a)(b)(c)は不変。実走待ち |
| escape.hh 負例 | partial | 既存unit test内に追加し、Xが `patch_sources` に残るassertを追加。依存先stubなし |
| 既存条件・所有制約 | closed | `guard.hh` 正例、`default.hh`・`changed.hh` 負例、全既存期待値を保持。docs・production・patches変更、stage・commitなし |

静的波及確認：所有外caller・consumer testから当該関数への参照は見つかりません。同ファイルの目録照合・sink cross-product検査が利用します。共有fixtureは既存 `tmp_path` と `conftest.py` のままです。

指定の `python3 tools/run_tests.py orchestrator/tests/test_ccbench_spawn_sites.py` を**1回**実行しましたが、`qstat -Q` 事前確認失敗で **rc=16、child_started=false**。実走nodeidはなく、同ファイル全体が未実走です。親docs由来の期待赤はありません。親の焦点走・変異検査・受入全走も未実施です。