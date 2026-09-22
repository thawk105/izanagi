単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親の単独走の実測 log (逐語、wave 統合 commit 0b0509d6e = この worktree の HEAD 0470ace93 と同内容で走らせた): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/review/solo-1.log
- 段 5 author の最終報告 (前段の実装子。あなたはその fix を担う): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s5-author-u4r.md
- 段 5 author の prompt (実装子契約。fix はこれを全文継承する): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s5-author-prompt.md
- 段 4 裁定 (R1〜R11、規模上限 R9): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s4-ruling.md

## あなたの役割と権限

あなたは Codex の fix 子である。s5-author-prompt.md の「あなたの役割と権限」「検査と報告の義務」をすべて継承する (編集してよいのは同じ 5 file
だけ、docs・commit・branch 操作はしない、report.py 編集禁止、新 module・test file・fixture dir を作らない、規模上限 R9 を守る)。

## 直すこと

親の単独走 (solo-1.log) で、既存 114 試験を含む 123 件は通り、**新規 v3 試験 9 件が赤**だった:
test_v3_parallel_processes_and_pool_failure_fallback、test_v3_reasons_preserve_ww_wr_rw_identity、test_v3_table_identity_separates_edges、
test_v3_cycle_reports_tables_and_tx_types、test_v3_packed_mapping_and_read_bounds、test_v3_serial_tables_types_and_ops、
test_v3_last_winner_tx_type_in_cycle、test_v3_tuple_and_legacy_fallback_preserve_metadata、test_v3_existence_unverified_and_v2_control。

9 件とも最初の赤は同じ比較 `assert graph.adj == reference_graph.adj` (test_verifier.py の `_v3_paths` 付近、および `DSG(txns).adj == ...`)
で、compact 経路の `DSG.adj` は値が tuple の dict、object 経路は値が set の defaultdict という**既存の表現差** (dsg.py の
`_build_compact_edges` 末尾と `_add`) を、そのまま `==` で比べていることが原因である (`{0: (1,)} != defaultdict(set, {0: {1}})`)。

- 新規試験の比較を表現に依らない形 (例: 辺集合 `{(u, v) for u, ds in adj.items() for v in ds}`) に正規化する。production の `DSG.adj` の
  表現は変えない (既存試験 test_verifier.py:2726, 2885, 2999, 3098 などが tuple 表現を固定している)。
- 正規化の後に同じ 9 試験の後続 assertion (versions・producer・result・result_to_dict_v3 の経路間一致、各試験固有の期待) が赤になったら、
  それが**試験の誤り**か**実装の誤り**かを根拠つきで切り分けてから直す。実装の誤りなら production を直す (段 4 裁定の範囲内で)。
  試験の期待を実装に合わせて緩めない。既存試験 (新規 18 本以外) の行は変更しない。

## 実走の義務

この worktree で次を実際に走らせ、結果 (件数と失敗 nodeid) を報告に逐語で書く。dispatch は sandbox から使えない (前段で qstat が rc=16)
ので、pytest を直接呼んでよい (1 file、数秒):
- `python3 -m pytest -q orchestrator/tests/test_verifier.py -p no:cacheprovider`
- `PYTHONPATH=. python3 orchestrator/tests/test_verifier.py` (素の自走 runner)
両方とも全件緑になるまで直す。緑にできなければ、残った赤と理由を書いて止まる。

## 出力形式

Markdown。「原因」「変更 (file:line と差分行数、R9 の累計)」「実走結果 (逐語)」「切り分けた実装の誤り (あれば)」「変異の位置表 (M1〜M15 の
file:line が前段から動いた分だけ)」「未解決」、最後に `## 総括` (5〜10 行)。
