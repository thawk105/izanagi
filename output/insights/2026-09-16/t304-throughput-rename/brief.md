# [T-304] / [T-305] 段 1 brief — `throughput_ops_sec` を実体名へ改め、旧名成果物の読み方を同じ単位で決める

- 基準: local main `9d52ef1459fdae5bc97050155b28fce0601d259f`
- wave worktree: `.claude/worktrees/dev-wave-t304-throughput-rename`

## 研究前進

論文の実験節・図表は planner / coder へ渡した入力を `throughput_ops_sec` と記す。producer の源値は
`outcome["fitness_tps"]`、CCBench 側は `common/result.cc` の `throughput[tps]` で、実体は
transactions/sec である。YCSB 既定 `ycsb_max_ope=10` (`include/ycsb.hh`) の下で読者が名前どおり
operations/sec と読むと **10 倍に取り違える**。値は正しく名前だけが誤りである。
完了判定 = live role 定義・producer・runbook・spec の名が実体と一致し、旧名で書かれた既存成果物の
読み方が同じ変更単位で決まっていること。

## 確定済みユーザー裁定

- worklog entry (109) (`docs/archive/worklog-phase3-0802-106-110.md` L881-919):
  **[T-304] は択 (a) rename**、**[T-305] は択 (a) 直す**、両者は同一 wave。
- 起票本文は同 file entry (106) L263-274。設計の原典は `docs/decisions.md` D118 の「残余 (a)/(b)」。

## 不変条件

- 規律 2 を緩めない。正しさゲート・identity ゲート・性能ゲートの定義・順序・閾値を変えない。
- 値を変えない。改名は名前だけで、`fitness_tps` からの写しも換算規約 (D118 決定 2) も不変。
- `screening` / `fitness` / `stop` 判定 / 凍結成果物へ到達しない (D118 決定 4 の射程を維持)。
- 記録された過去の測定は無効化しない (規律 7)。旧名の成果物は書き換えない。

## 親の provisional 裁定 (攻撃対象)

- **(P1) [T-305] を scope に含める。** `docs/phase3.md` L1529 は [T-305] を D205 (2026-08-06、
  裁定 (109) より後) で active 除外と記録し、現行 worklog から消えている。[T-304] は現行 worklog
  L122 / L927 に carry として残る。**除外は「同一 file を触る wave への相乗り」で解ける型** (T-1008
  と同じ扱い) であり、本 wave が [T-305] と同一 file・同一 pin 閉包を触る以上、相乗り条件は成立する。
  ユーザー引数も同一 wave を明示している。
- **(P2) 新しい名前は `throughput_tps`。** producer の源 field が `fitness_tps`、CCBench の出力名が
  `throughput[tps]` であり、単位の曖昧さが残らない。対抗案 `throughput_txn_sec` は `latency_ns` と
  並びが揃うが、源の字面から離れる。
- **(P3) 旧名成果物の読み方は「schema 版で分ける」。** `SCHEMA_VERSION` を
  `p3-autonomous-workload-trial/v3` → `v4` へ上げ、`autonomous_trial_completeness.py` の
  独立定数 `_ROLE_SCHEMA_VERSION` も同じ単位で上げる。**v3 以前の record は `throughput_ops_sec` を
  持ち、その値は同一の transactions/sec である**ことを decisions へ 1 行残す。
  **読み手側に別名受理 (alias) を足さない** — 旧 record を跨いで読む consumer の実在は段 2 で実測し、
  実在しなければ機構を足さない (ユーザー指定の scope 外)。
- **(P4) 変異事前登録は「両コピー同時」を突く。** `s8c_generation_projection.py` の `_PERF_KEYS` と
  `autonomous_trial_completeness.py` の `_PERF_KEYS` は D118 決定 4 により**意図的な独立二重定義**で
  ある。片方だけ改名する変異が生存しないことを確かめる。

## 成果物影響 (DW-G05)

放置すると、論文の実験節と runbook が role へ渡した入力を 10 倍の単位名で記し続け、
`.codex/role-adapters/*.json` の live prompt もその名で固定される。**受理集合が動く面**である
(D118 が [T-305] について同じ判定をしている) ため、軽量版は使わず段 2・3 と段 6 レビュー子を置く。

## 編集面 (実アンカー)

| 種別 | path | 件数 |
|---|---|---|
| producer | `orchestrator/campaign/p3_autonomous_workload_trial.py` L147/2005/2021 | 3 |
| producer | `orchestrator/campaign/s8c_generation_projection.py` L59/78 | 2 |
| 独立再計算 | `orchestrator/campaign/autonomous_trial_completeness.py` L436 | 1 |
| live role | `.claude/agents/{planner-v4,coder-v4-autonomous,coder-v4-autonomous-k2,coder-v4-autonomous-sort,coder-v4-autonomous-trigger-gating}.md` | 各 1 |
| 生成 adapter | `.codex/role-adapters/` 同 5 file | 各 1 |
| test | `test_p3_autonomous_workload_trial.py` 23 / `test_s8c_generation_projection.py` 8 / `test_codex_agents.py` 1 / `test_s8c_preregistration_predicates.py` 1 / `test_s8c_schedule.py` 1 | 34 |
| docs | `docs/phase3-s4b-runbook.md` 2 / `docs/phase3-s5-sort-runbook.md` 2 / `src/coder-spec.md` 2 | 6 |
| 所要台帳 | `orchestrator/tests/acceptance_duration_ledger.json` L12019-12020 (test node ID に field 名が入る) | 2 |

**pin 閉包 (path 検索に出ない、F30 型):** `orchestrator/codex_roles/review_ledger.py` の
`SOURCE_FILE_SHA256` が **role 名を key に** `.claude/agents/*.md` の exact SHA を pin する。
検査は `orchestrator/codex_roles/spec.py` L587 と `tools/check_codex_agents.py`。
role 定義を 1 byte でも変えたら ledger の明示更新と adapter 再生成が要る。

**分類保留 (F39):** `test_codex_agents.py` L619 の `throughput_ops_sec` は **calibrator の正規入力**の
例であり、role payload の field とは別物の可能性がある。段 2 で live copy / 独立 golden /
歴史記録のどれかを判定する。

## 編集面の重複検査 (起動時、実測)

全 worktree を対象 path に絞って走査した。**未 commit の実質衝突は 1 件**:
`.codex/worktrees/t2293-impl` (`impl-dev-wave-t2293-origin-producer`) が
`p3_autonomous_workload_trial.py` と `test_p3_autonomous_workload_trial.py` を編集中。
ただし **その差分に `throughput_ops_sec` は 0 件**で、行は競合しない。他の 7 worktree の未 commit は
`acceptance_duration_ledger.json` だけで、これは land が扱う add-only 台帳である。
B-7 の wave (`dev-wave-t2670-b7-three-run-materials`) は対象面に未 commit 変更を持たない。

## 成果物の形

- コード・test の改名差分 (Codex author が書く)。
- `.codex/role-adapters/*.json` の再生成 (親が integrator として render — 子は `.codex/**` へ書けない)。
- `review_ledger.SOURCE_FILE_SHA256` の明示更新。
- decisions 1 件 (新名・schema 版・旧名 record の読み方)、worklog 1 エントリ、本 insight。

## 並列分割方針

段 2 は codex plan 子 1 本。段 3 は異なるレンズ 2 本 (lens-a = pin 閉包と受理集合の漏れ、
lens-b = 改名の射程過大・scope 外機構の混入)。段 5 は実装子 1 本 (編集面が 1 つの改名で密結合のため
分割は競合を増やす)。段 6 はレビュー 2 本 + 変異 matrix。
