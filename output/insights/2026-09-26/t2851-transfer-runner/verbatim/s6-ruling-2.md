# 段 6 裁定 (2 巡目) — 2026-09-23 22:00 JST、対象 commit f28284c14、焦点再レビュー codex/s6-focus1.md (NO-GO)

派生値の照合: M = 18 (wh の 9 cell × R1・R2) と、候補が R1 と同 identity のとき M = 9 は焦点レビューが原データから再計算して一致。

| ID | 判定 | 採否 | 内容 |
|---|---|---|---|
| R-A4 partial / F-1 | real | 採用 | run-job / verify の実行前に、凍結記録の入力 field から `freeze_candidates` を再実行し、派生 field (`jobs`・`comparisons`・`m_by_family`・`sha256`) を含む出力全体が渡された凍結記録と完全一致することを要求する |
| R-A6 partial / F-2 | real | 採用 | cohort 2 の run-job は、凍結記録の cohort 1 の全 job key (同じ段・protocol・cell) について記録があることを要求し、end_utc は `datetime` に parse して UTC の最大値を取る。対象 key の hostname は、その key の採用 (32 block 完走・単独性成立) 記録から取る |
| R-A5 partial / F-4 | real | 採用 | `attempt` 番号は trace_runner の呼び出しを開始した場合だけ付ける。一時 dir 作成失敗などの前段失敗は `attempt: null` |
| R-B3 partial | refuted | — | `trace_c_lines` は件数 (≥ 0) なので `> 0` は pipeline.py の `ncommit == 0` 拒否と同値。変更不要 |
| 未使用 `sys` (test) | real | 採用 | 削除 |
| F-3 TPC-C 認定経路 | refuted (scope 外) | 不採用 | 認定経路 (T-2854/T-2855) は未着地で、発火条件を満たす既存成果物を名指しできない (DW-G04)。未着地の間は indeterminate・attempt null が TPC-C 版 §6 と整合。接続は経路の着地後の別単位として insight に記録 |
| P-4 (親) clocks_per_us / numactl | real | 採用 | 凍結記録の入力に `environment = {"env_tag": str, "clocks_per_us": 正整数, "numactl": [str, ...]}` を必須で置き (hash 対象)、run-job は `run_once` の gflags に `-clocks_per_us=<値>` を明示して渡し numactl も渡す、verify は同じ値を `_run_trace` に渡す。job・verify の記録に環境値を写す。既定値 (CCBench の 2100) への暗黙依存を無くす。smoke は Pegasus の値 (`env_tag="pegasus"`、2100、numactl なし。出所 `orchestrator/campaign/env_contract.py` の pegasus entry と `between_run_floor._measurement_profile`) を渡す |

fix 後に焦点再レビューを 1 本 (2 巡目)。上限 3 巡 (DW-O16)。
