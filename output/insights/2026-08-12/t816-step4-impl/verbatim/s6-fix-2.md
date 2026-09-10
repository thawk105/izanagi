2 件とも指定のテストファイル内で修正しました。production、docs、artifact、submodule、git index、commit は変更していません。

| 所見 | 状態 | 対応 |
|---|---|---|
| G1 patched-source hash drift | partial（実装済み・未実走） | historical golden との一致と、現行再計算値との不一致を固定。近傍の自己整合 assert 3 本は維持 |
| G2 stale-baseline フレーク | partial（実装済み・未実走） | note から age・threshold を抽出し、`age >= 1860.0` と設定値との一致を検査 |
| 回帰 | なし | 静的監査では受理集合の拡大、skip/xfail、期待値緩和なし |

G1 の hash は以下です。

- 旧 historical 値: `847d27b07783fcb6bcd0c8f64514bf0292e407549039462f42870b9ac1d16d4b`
- 現行再計算値: `f059834a693142a5d10f3ad315fa7ce7684cbe20457a7fd730f1271c1a013eee`
- 出所:
  - 旧値: 凍結 bundle の campaign-root receipt／raw provenance（`d706650` 期）
  - 新値: `patches/ledger.json` の `base_commit=511c9538…` に patch を適用した `_recompute_patched_source_hashes(entry)`
- `cc/silo/ycsb_silo.cc` の historical 値 `716c4dd2…d68fa3` も同じ独立 golden に含めています。

変更箇所は [test_silo_ladder_rung1_evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-fix2/orchestrator/tests/test_silo_ladder_rung1_evidence.py:84) と [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-fix2/orchestrator/tests/test_campaign.py:6564) です。

指定 nodeid は `run_tests.py` で実行を試みました。

- `orchestrator/tests/test_silo_ladder_rung1_evidence.py::test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head`
- `orchestrator/tests/test_campaign.py::test_pipeline_stale_screening_falls_back_to_verify_first_and_records_trace`

結果は runner `rc=16`、`qstat -Q preflight rc=1` で dispatch infrastructure failure となったため、pytest は未実走です。直接 pytest での迂回はしていません。

静的検査はすべて成功しました。

- `git diff --check`
- Python AST parse
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- 変更範囲確認: 所有内の2ファイルのみ

## 総括

G1・G2 は実装済みですが、計算資源への投入失敗により未実走のため、両所見とも `partial` です。受理集合やproduction挙動は変更していません。