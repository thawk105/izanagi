## 検査項目 1〜10 の結果

1. **裁定との一致:** ほぼ一致。`_match_key` は最初の `::` で path と test 名を分け、接尾辞除去を test 名側だけへ適用しています。[mutation_harness.py:1237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:1237)、[mutation_fanout_contract.py:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_fanout_contract.py:297)。両 `_normalize_node` と `tools/mutation_fanout.py` は未変更で、複数段 `@` の除去もありません。ただし fanout の重複検査に MINOR 1 件あります。

2. **受理集合:** group 接尾辞以外の新たな吸収は見つかりません。path、大文字小文字、class 階層、parametrize ID は保持されます。[test_mutation_harness.py:1017](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:1017)、[test_mutation_harness.py:1051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:1051)、[test_mutation_harness.py:1095](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:1095)。

3. **異なるテストの key 衝突:** 現行 pytest node 形式について、意図しない具体的な衝突対は見つかりませんでした。base 表記と一段の group 接尾辞表記だけが同じ key になります。

4. **F71:** 3 契約とも維持されています。

   - dispatch job stdout 全文を読む処理: [mutation_harness.py:1509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:1509)、[mutation_harness.py:1598](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:1598)。fanout も relocated stdout と台帳内容を一致検査します。[mutation_fanout_contract.py:1396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_fanout_contract.py:1396)
   - ` - ` 無しは行末まで: [mutation_harness.py:1246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:1246)、[mutation_fanout_contract.py:306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_fanout_contract.py:306)
   - `rc != 0` かつ抽出 0 件は `PARSE_ERROR`: [mutation_harness.py:2011](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:2011)、[mutation_fanout_contract.py:351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_fanout_contract.py:351)

   接尾辞除去は抽出後の key 化であり、抽出結果を空にする新経路はありません。

5. **`KILLED` 完全一致:** harness は `failed_keys == expected_keys`、fanout も同じです。[mutation_harness.py:2019](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:2019)、[mutation_fanout_contract.py:358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_fanout_contract.py:358)。strict superset 負例もあります。[test_mutation_harness.py:970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:970)、[test_mutation_fanout_contract.py:669](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_fanout_contract.py:669)

6. **記録の忠実性:** `collected_nodes` は抽出値をそのまま保存し、`failed_nodes` も `_match_key` へ置換せず保存しています。[mutation_harness.py:1488](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:1488)、[mutation_harness.py:2192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:2192)。registration と spec の表記一致も fanout が検査します。[mutation_fanout_contract.py:867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_fanout_contract.py:867)

7. **expected-node 空非空契約:** harness と fanout の双方で維持されています。[mutation_harness.py:593](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:593)、[mutation_fanout_contract.py:486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_fanout_contract.py:486)

8. **flaky hold:** expected 側と hold registry 側を同じ key にしているため、base／接尾辞付きの双方が拒否されます。[mutation_harness.py:1310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:1310)、[test_flaky_test_holds_contract.py:722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_flaky_test_holds_contract.py:722)

9. **既存テスト:** harness の既存テストは削除・反転・skip・xfail されていません。strict superset/subset は [test_mutation_harness.py:957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:957) と [test_mutation_harness.py:986](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:986)、path/class/case 負例は [test_mutation_harness.py:1002](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:1002) 以降に残っています。

10. **scope:** 差分は裁定された 2 production file と 3 test file の計 5 本だけです。新 module、registry、台帳、互換層、汎用 framework、文書変更はありません。

## 所見一覧 (BLOCKER / MAJOR / MINOR、file:line 付き)

- **MINOR — fanout spec の重複検査が対象 checkout ではなく contract 自身の checkout を repo root に使っています。** [mutation_fanout_contract.py:500](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_fanout_contract.py:500)

  `--source-repo /B` に対し別 checkout `/A` の driver を実行し、expected node を `/B/tests/test_gate.py::test_m1` と書くと、`Path(__file__).resolve().parents[1]` は `/A` なので `/B/` が除去されず、絶対 path として [mutation_fanout_contract.py:291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_fanout_contract.py:291) で拒否されます。fanout は対象 repo を独立した `--source-repo` として受け取り、[mutation_fanout.py:1438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_fanout.py:1438) で解決しているため、両 root が異なる経路は構造上到達可能です。

  **変異 matrix への影響:** 偽 `KILLED`／偽 `SURVIVED` にはならず fail-closed で開始前停止しますが、従来 harness が受理できる有効な絶対 node 表記の fanout matrix を生成できません。偽結論ではないため MINOR としました。

BLOCKER、MAJOR はありません。

## 裁定と実装の差分

プラン v2 の 1〜7、test 名部分だけの除去、両 `_normalize_node` の据え置き、`tools/mutation_fanout.py` の無編集、一段のみの `@` 除去、fanout の正規化後重複拒否は実装されています。

差分は上記 MINOR のみです。プラン v2 #6 の重複拒否自体はありますが、その比較 key を作る repo root が実際の対象 checkout に束縛されていません。

M1〜M13 に対応する正例・負例も静的には配置されています。[test_mutation_harness.py:868](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:868)、[test_mutation_harness.py:1051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_harness.py:1051)、[test_mutation_fanout_contract.py:547](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_fanout_contract.py:547)、[test_mutation_fanout_contract.py:604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_mutation_fanout_contract.py:604)。

## 問題を見つけられなかった箇所

- group 接尾辞による偽 `KILLED`
- path、case、class、parametrize ID、空白の新たな吸収
- 異なる通常 pytest test の key 衝突
- F71 の三契約の弱体化
- raw node 記録の書換え
- expected-node 空非空契約の弱体化
- flaky hold の接尾辞による迂回
- 既存負例の緩和・削除
- 許可 5 ファイル外の変更

## 総括

**BLOCKER 0、MAJOR 0、MINOR 1。** 裁定の本体と正しさ防壁は保たれており、`KILLED` の完全一致や F71 の fail-closed 契約にも弱体化は見つかりませんでした。

テストは実走しておらず、緑とは判定していません。