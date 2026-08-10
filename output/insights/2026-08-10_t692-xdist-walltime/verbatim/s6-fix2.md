## 総括

- **(1) を採用**しました。並べ替えを `pytest_collection_finish` に移し、cacheprovider の `--ff` / `--nf` post-yield 完了後に適用しています。[conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/conftest.py:262)
- 既存の通常・`--ff`・`--nf` 実 collection 対照は維持しています。[test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:646)
- 指定 runner:
  `python3 tools/run_tests.py orchestrator/tests/test_real_repo_serialization.py -n 0`
  は `qstat -Q preflight rc=1` で未実走（0 passed / 0 failed）。
- 指定 fallback:
  `python3 -m pytest orchestrator/tests/test_real_repo_serialization.py -q`
  は、同ファイルの全11 nodeidを実走して **11 passed / 0 failed**（17.90秒）。
- `--collect-only -q` でも同ファイルの11 nodeidを収集済み。順序検査 node 内では通常・`--ff`・`--nf` の3 collectionが通過しました。
- MT6 / MT7 は、固定 literal と production 定数を最初に比較する assertion で落ちます。[test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:468)
  - MT6: tuple 反転により同 assertion だけが不一致。
  - MT7: 空 tuple により同 assertion だけが不一致。
  - 変異本走は親担当のため、この author 巡では実施していません。
- F1・F2・F4を含む既存検査は削除・緩和していません。production、docs、`tools/**`、禁止対象、commitには触れていません。
- 未解決は runner の `qstat` infrastructure failure と、親によるMT6/MT7本走のみです。実装・fallbackテスト上の未解決 failure はありません。