## must-fix

1. **[real][恒真ゲート][テスト代表性] fixture 配線検査が lock mode を識別できません。**  
   共通 scope は `access_mode` を lock helper へ転送しますが（[test_p3_b4_raw_record_producer.py:1281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1281)）、実体検査は read/write の両方へ同じ `LOCK_EX|LOCK_NB` を当てています（[同:1496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1496)）。SH も EX も競合 EX を拒むため、`access_mode=access_mode` を恒常的な `"write"` に変えても追加9検査はすべて緑のまま、17 consumer の直列鎖が復活します。逆に `"read"` 固定でも writer の排他欠落をこの検査は検出しません。wrapper AST も外側 fixture の literal しか確認せず、共通 scope から lock scope への転送は見ていません（[同:1634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1634)）。

   また、NB 検査は共通 `_certified_evidence_fixture_scope` そのものを使っており再実装ではありませんが、decorated fixture（[同:1319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1319)、[同:1330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1330)）の `yield` nesting は未検査です。fixture 引数を増やさず、既存実体検査で reader は競合 SH 成功、writer は競合 SH 失敗を確認し、AST で mode 転送と両 wrapper の yield nesting を固定できます。

   **放置すると成果物が変わる点:** T-2298 の受入証拠が緑でも、全17 consumer が再直列化、または M17/M18 が reader と同時に共有 evidence を破壊できる実装を許します。

## nit

- **[refuted][writer 閉包 AST]** 恒真・恒偽の問題は現行入力ではありません。期待 map は検出結果から生成せず17本を明示列挙（[同:1591](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1591)）、両 fixture が taint 起点（[同:1610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1610)）です。`Path` と `with_name` だけを伝播するため `_publish` / `_assert_write` の返値は非 taint（[同:1667](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1667)）。代入 fixed-point（[同:1697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1697)）は M18 の `Path(...) → with_name → rename/symlink_to/unlink`（[同:2154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:2154)）を捕捉します。reader の `Path(write.artifact_path).write_bytes` は `write` が非 taint なので誤検出されません。検査名・docstring も直接 mutation 限定を明記しています（[同:1588](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1588)）。

- **[refuted][F649]** helper-level正負例は実 `fixture.lock` を開いて実 `flock` を競合させています（[同:1341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1341)、[同:1398](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1398)）。実 evidence の NB 例も共通 scope を直接 enter しており、別実装への置換ではありません。残る endpoint 配線不足は must-fix のとおりです。

- **[refuted][揮発 payload]** 新規期待値に絶対 path、working-tree hash、時刻、pid はありません。atomic metadata 検査の固定値は `iteration/on_root/off_root` の論理値だけです（[同:1558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1558)）。fixture metadata の絶対 path は実行時生成値で、期待値への焼込みではありません。

- **[refuted][メタテスト波及]** `test_mutation_node_mapping_is_complete_and_one_to_one` は M01〜M18 の map と callable 性だけを pin し（[同:832](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:832)）、新規検査は M 番号を名乗りません。M17/M18 の関数名も不変なので赤化要因はありません。実際の追加数は「6〜8」ではなく、条件付き変異 g の検査を含む **9 node** です。

- **[real][台帳・焦点走への波及、修正不要]** file 単位 shard では既存 file と同じ shard に9 nodeが追加され割付先は変わらず、loadgroup 順序では各 node が台帳 key 不在（[conftest.py:1512](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/conftest.py:1512)）のため96番目相当の fallback costで並び、同値間は元の collection 順を保ちます（[同:1587](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/conftest.py:1587)）。

## consumer 17 本の hunk 照合表

逐語 diff の consumer 変更は [stage5-diff.patch:598](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/artifacts/stage5-diff.patch:598) の1 hunkだけです。

| consumer | 現物 file:line | hunk 判定 |
|---|---:|---|
| M01 assembly precursor | `test_p3_b4_raw_record_producer.py:1804` | hunk なし、不変 |
| M02 planned path | `test_p3_b4_raw_record_producer.py:1823` | hunk なし、不変 |
| M03 assignment timestamp | `test_p3_b4_raw_record_producer.py:1836` | hunk なし、不変 |
| M04 pair IDs | `test_p3_b4_raw_record_producer.py:1855` | hunk なし、不変 |
| M05 lock buffer | `test_p3_b4_raw_record_producer.py:1878` | hunk なし、不変 |
| M06 WAL commit | `test_p3_b4_raw_record_producer.py:1909` | hunk なし、不変 |
| M07 decimal lexeme | `test_p3_b4_raw_record_producer.py:1919` | hunk なし、不変 |
| M08 tuple reuse | `test_p3_b4_raw_record_producer.py:1929` | hunk なし、不変 |
| M10 off digest | `test_p3_b4_raw_record_producer.py:1954` | hunk なし、不変 |
| M12 ratio rejection | `test_p3_b4_raw_record_producer.py:2002` | hunk なし、不変 |
| M13 integer reference | `test_p3_b4_raw_record_producer.py:2038` | hunk なし、不変 |
| M16 judgment fields | `test_p3_b4_raw_record_producer.py:2087` | hunk なし、不変 |
| M17 receipt replacement | `test_p3_b4_raw_record_producer.py:2104` | fixture 引数名と全同名参照だけを writer 名へ変更。長名による改行のみ。assertion、`_publication(tmp_path)`、`P._snapshot_regular` monkeypatch は不変 |
| M18 symlink evidence | `test_p3_b4_raw_record_producer.py:2134` | fixture 引数名と全同名参照だけを変更。request の改行のみ。control/attack/role-attack root、`on_terminal_receipt_path`、assertion は不変 |
| assembly judgments | `test_p3_b4_raw_record_producer.py:2169` | hunk なし、不変 |
| manifest driver | `test_p3_b4_raw_record_producer.py:2285` | hunk なし、不変 |
| non-guarantees | `test_p3_b4_raw_record_producer.py:2295` | hunk なし、不変 |

関数名、parametrize、decorator の変更は17本すべてゼロで、既存 node id は不変です。

## 総括

**changes requested: must-fix 1件。** 実装本体、17 consumer の期待値、writer taint 閉包、atomic metadata、既存メタテストとの整合は静的には契約どおりです。一方、実 fixture 配線検査が SH/EX を区別しないため、旧直列鎖を復活させても緑になる反例があります。

再発攻撃面の判定は、`[恒真ゲート]=real`、`[テスト代表性]=real`、`[誤前提]=「追加6〜8 node」は refuted（実数9）`です。指定どおり pytest は再実行していません。