## must-fix (番号・file:line・成果物影響 1 行・是正案)

1. **凍結説明の経路限定が不完全で、whiteboard 以外の還流も否定している。**
   `.claude/agents/planner-v4.md:52` の「最新測定値ではない」と同ファイル `:55` の「iteration ごとの結果は whiteboard でだけ届く」は無条件の断定。`.claude/agents/coder-v4-autonomous-trigger-gating.md:62` も同様。
   - 手動射影を一律に凍結しないことは段 4 裁定 A2/B3 の明示事項。実例も `output/insights/2026-09-16/t2588-k2-loop-roundtrip/README.md:184` にある。
   - **8c 内でも** `orchestrator/campaign/p3_autonomous_workload_trial.py:4217` は第 2 世代以降に `critic_feedback` を渡す。`:4149` では前世代の `source_metrics` から射影しており、「whiteboard だけ」は反証される。

   **成果物影響:** planner が正規の更新済み手動入力や `critic_feedback` を判断材料から除外し、提案の `direction`・`justification` と後続レポートを変え得る。
   **是正案:** 最新値でないという説明を「8c 自動 trial の当該フィールド」に限定する。「whiteboard でだけ」は削除するか、8c の正規の診断還流も明記する。coder 冒頭も同じ限定を置く。

2. **独立 latency を除去した後も、観測から導けない待ち時間への断定が残る。**
   `.claude/agents/critic.md:26` は throughput 半減・abort_rate 不変だけから「衝突が無くても待つ時間」と帰属する。しかし、この組だけでは cache／IPC 等による低下と区別できない。さらに `external/ccbench/cc/silo/transaction.cc:27`・`:47` の backoff 呼出しは `abort()` 内であり、非衝突時にも待つという挙動の根拠にはならない。

   **成果物影響:** critic の `attribution` に未観測の機序が確定事項として入り、それを根拠に `recommend`・`avoid` が変わる。
   **是正案:** 「abort 率の改善は観測されない。待機コスト等を候補とし、他指標と uncertainty を併記する」とする。独立の待ち時間を測っていない以上、原因を断定しない。

## nit

1. `docs/phase3-s4b-runbook.md:52` の `coder-v4-autonomous*.md` は、未編集の base／sort／k2 まで「改訂した文書」に含めて読める。一方、編集済み `critic-experiment.md` は列挙されない。変更した role 名を明示すると適用版の参照が正確になる。

2. `.claude/agents/critic.md:14`、`.claude/agents/critic-experiment.md:40` の適用版は「改訂以降の走行」とだけ書かれる。他文書と合わせて「改訂以降に**開始する**走行。以前の走行は当時の版」とすると、継続中の走行への適用が曖昧にならない。

3. `src/coder-leakproof-context.md:55` の `default_perf()` 参照は、段 4 裁定表 A4 の「内部関数名を置かない」と plan v2 項 1(e) の明示案が食い違う箇所。実装は後者に従っており、実装違反とは判定しない。裁定側の例外を明記するとよい。

## 検算した事実の一覧 (確認 / 反証)

| 判定 | 検算結果 |
|---|---|
| 確認 | bench の 100,000 records／4 threads／skew 0.9／rr50／rmw false／extime 1／reps 2 は `orchestrator/campaign/p3_s4_loop.py:1565` と一致。calibrator への規模差替え説明も同所と一致。 |
| 確認 | `external/ccbench/include/ycsb.hh:20`・`:22`・`:59`・`:65` より、blind write、既定 10 操作、操作単位の read 確率 50% は正しい。 |
| 確認 | legacy verify の 200 records／4 threads／rmw／5 操作／extime 1／1 rep は `orchestrator/campaign/pipeline.py:147` と一致。S2 の 1m／48／3 は同 `:159`・`:163` と一致。sort `:305`、trigger-gating `:599` は `VERIFY_LEGACY_PLUS_S2` を指定。 |
| 確認 | trace／perf の 2 build は `pipeline.py:2016`。再計測は同 `:1411` と `orchestrator/calibrator/stability.py:58`。throughput 中央値は `orchestrator/calibrator/analyze.py:252` の `statistics.median` で、有効 2 点なら算術平均。 |
| 確認 | latency 恒等式は `external/ccbench/common/result.cc:52` と一致。4 指標の列挙は `orchestrator/critic/digest.py:65` の `INDICATORS` と一致。 |
| 確認 | 初期数値指標は `p3_autonomous_workload_trial.py:146` ですべて `None`。`:4102` で workload ごとに一度射影し、`:2043`・`:2067` は更新済み metrics を使わない。`contention_level` は `:4108` で descriptor 由来。「**数値指標**がすべて null」という限定は正しい。 |
| 反証 | 凍結規則の全経路への一般化、結果が whiteboard だけで届くという断定、および critic の待ち時間への確定帰属。上記 must-fix 参照。 |
| 確認 | 差分に frontmatter・role JSON 例の key・payload schema・`latency_ns` key・代表 rep 選択の変更はない。runbook の `last_delta_pct` 除去は名指しの訂正対象。 |
| 確認 | T-2588 の完了済み K2 走行を非遡及側へ置くことは適切。過去成果物の書換えも差分にない。 |
| 確認 | leakproof の追加部分に勝ち筋値・利得・最適化機序・実験アーム名・裁定番号・命令形はない。role 本文にも内部関数名の追加はない。 |
| 確認 | `tools/check_docs.py:170` が両 runbook を living-doc 検査へ登録。`:6722` 以降に行番号・pin literal・D 番号・path 検査がある。D410／D2104 は `docs/decisions.md:17149`／`:64810` に実在し、追加された具体的 path も実在する。 |
| 確認 | 4 role の現物 SHA-256 は更新後 ledger literal と一致。adapter の変更項目は本文と semantic digest。adapter 完全 parity・checker・pytest は本レビューでは未実走。 |

## 総括

**NO-GO — 凍結・還流説明の経路誤認と、critic の根拠のない機序断定を修正する必要がある。**