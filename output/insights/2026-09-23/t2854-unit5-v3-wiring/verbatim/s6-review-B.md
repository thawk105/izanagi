### 所見

**RB1 — must-fix：executor 試験の正例も不正な key で赤になる。** [test_campaign.py:7519](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7519) の `district` は、verifier が要求する小文字・偶数桁の hex key ではない。`certified` ケースと witness ケースがともに汚染される。R/W の key を同じ有効な hex 値に直す。親が既に確定した *別の* lost-update 試験の不具合に加え、こちらも修正が必要。**放置時の成果物影響：**段 1 の certified 到達と witness 拒否を示す試験が成立せず、認定経路の実効性を確認できない。

**RB2 — should：拒否理由の説明が新しい受理集合と食い違う。** [pipeline.py:639](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:639) は TPC-C の v2 を `trace-witness-unsupported-workload` で拒否する。一方、[digest.py:1325](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/critic/digest.py:1325) の表示文は「YCSB allowlist 外」と断定する。reason 自体は [s8b_abort_reason_contract.py:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/s8b_abort_reason_contract.py:18) の分類と矛盾せず、WAL consumer も受け取れる。修正案は reason を増やさず、表示文を v2 の TPC-C も含む説明へ更新すること。削除された allowlist コメントも、YCSB 限定のまま戻さず、TPC-C の計数修正の根拠を 1 行で記すのが整合的。**放置時の成果物影響：**台帳の reason 値は変わらないが、critic の拒否説明が TPC-C を常に対象外と誤認させる。

**RB3 — nit：witness の 3 ケースで検査する残存内容が重複している。** [test_campaign.py:7528](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7528) の `tail-loss`・`max-txid-loss`・`thread-file-loss` は、いずれも最終的に `first + second` だけを verifier に渡し、[同:7569](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7569) で同じ診断を繰り返す。裁定が求めた欠落形態の記録は残しつつ、共通 assertion をまとめられる。**放置時の成果物影響：**受理集合・受領証・台帳は変わらない。試験量だけが増える。

## 総括

- 配線先の CLI JSON、pipeline 拒否診断、capability digest はいずれも `result_to_dict_v3` に切り替わっている。
- TPC-C の 4 flag 比較、verifier 後の v3 要求、YCSB の受理維持は plan v2 と一致する。
- v2 の射影は既存 `result_to_dict` を基にしており、差分に既存試験の期待値変更はない。
- 差分は指定の 5 ファイルのみ。production 32 行、試験 220 行、新規 test 関数 5 本で上限内。
- author の行数・本数の申告は差分と一致するが、RB1 のため executor 試験の到達主張は成立しない。
- 親が確定済みの lost-update 試験の赤は再所見に数えていない。
- 本レビューは静的検査であり、試験の実走結果は判断に含めていない。