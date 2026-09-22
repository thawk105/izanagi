fix B1 は**実装済み・未実走**です。所有2ファイルだけを修正し、既存テストの期待値・prompt は変更していません。commit は実行していません。

**1. 変更箇所**

- [tools/b5_llm_round.py:209](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-b/tools/b5_llm_round.py:209)：`RoundTool.knowledge_input()` を完成。
- [orchestrator/tests/test_b5_llm_round.py:65](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-b/orchestrator/tests/test_b5_llm_round.py:65)：`_fixture()` が一時dirへ指定された実物の WAL manifest を書くよう変更。stub なし。

**2. 知識解決**

試走版と同じく、既存 resolver → manifest digest 照合 → 既存 `planner_projection` → `ensure_ascii=False, sort_keys=True, indent=2` の UTF-8 bytes → 照合先の raw bytes 比較、の順です。

差分は manifest の引数化・repo内照合先の使用と、不一致時を `assert` から明示的な `ValueError` にした点です。後者により Python 最適化時も停止します。tool に subprocess の import・呼出しは追加していません。

**3. 静的検査**

- `PYTHONPYCACHEPREFIX=/tmp/t2797-eb-unit-b-pycache python3 -m py_compile tools/b5_llm_round.py orchestrator/tests/test_b5_llm_round.py`：rc=0。
- `git diff --check`：rc=0。
- `git cat-file -t`：指定対象が commit／blob であることを確認、rc=0。
- `git cat-file blob … | sha256sum`、照合先への `sha256sum`：指定hashと一致、rc=0。
- 保存promptを `sed`・`jq` で読み取り：両方の知識payloadが照合先と一致、rc=0。

途中の `jq` は保存されていない単独入力JSONを指定して rc=2。その後、保存prompt内のJSONを読み取り確認しました。

**4. MB2・MB3・MB8 と golden**

全3件が `_fixture()` → `_inputs()` → `cmd_inputs()` → 実物の `knowledge_input()` を通る構造です。

- MB2：`a=3, k=2` で `critic-1` の継承と評価番号を検査。
- MB3：初回の診断不在、次回の両入力への同一6項目診断を検査。
- MB8：生成後のpromptを、保存promptへの既存 `bytes.replace` だけで作る期待値と比較。

本文・入力構築・context・較正定数・JSON整形を静的に追った範囲では、**置換で表せない差は見つかっていません**。実出力のbytes一致は未確認です。

**5. 親の実走候補**

`orchestrator/tests/test_b5_llm_round.py` 全体。優先nodeは以下です。

- `::test_rejected_opportunity_preserves_evaluation_number`
- `::test_initial_and_inherited_inputs`
- `::test_registered_round1_prompt_golden`
- `::test_fixed_knowledge_projection_bytes_and_digest`

## 総括

知識解決の未実装箇所を解消し、実物resolverを通すfixtureを設定しました。構文検査は成功しています。テストの通過・変異検出は未実走のため未判定です。