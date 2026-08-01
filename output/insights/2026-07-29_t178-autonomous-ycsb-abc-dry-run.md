# T-178 autonomous workload-conditioned YCSB A/B/C dry-run

**判定:** bounded 8c MVP の operational wiring は成立。正式な workload-conditioned synthesis
主張は未成立。全 run は `--no-build` であり、correctness / performance evidence ではない。

## 1. 固定した pilot 条件

- axis: `silo-backoff-trigger-gating`
- workloads:
  - YCSB A = skew 0.9 / rr50 / rmw0
  - YCSB B = skew 0.9 / rr95 / rmw0
  - YCSB C = skew 0.9 / rr100 / rmw0
- scale: 100,000 records / 4 threads
- generation budget: 1 per workload
- roles: planner → coder → auditor → existing harness → critic
- provider: headless Claude、fresh 1 turn、runtime tools=[]、empty MCP
- attempts: role/cell ごと1回、retryなし
- stop: fixed generation budget。performance early stop なし
- report label: `scientific_claim=false`, `exploratory wiring pilot`

## 2. Fixture

決定論 fixture で A/B/C の 3 cell が全て `dry-pass`。descriptor projection、role parser、
diff preview、auditor digest、既存 driver、critic、journal、terminal report の配線を確認した。

## 3. 実 Claude trial と fail-closed 発火

### v1 — schema failure を保存して停止

- trial: `claude-abc-g1`
- status: `partial`
- planner/coder: 6/6 valid
- auditor: 0/3 valid
- 原因: source auditor contract が `list[dict]` を要求する一方、mediated output 例が element
  schema を明記せず、モデルが `nits` / `proposed_tests` を `list[str]` で返した
- 動作: parser が 3 cell とも拒否。retryせず各 cell を `role-invalid` で停止。他 cell は続行
- report SHA-256:
  `09cd0e2fafa85c039fd085e19f01cde2e2ed7d08bb51b752055a8a7cd3ba2f3d`
- attempt journal SHA-256:
  `3657fe91945133de3b8b37a3fd00d9930e98b75dbdfb08917c087ceb7d9d96ad`

これは「invalid を都合よく再試行して成功だけ残す」のでなく、境界違反を first-class result として
保存する gate の発火実証。

### v2 — auditor schema 明確化後の完走

- trial: `claude-abc-g1-v2`
- status: `complete`
- role attempts: 12/12 valid
- cells: 3/3 `dry-pass`
- stop: 3/3 `fixed-generation-budget`
- report SHA-256:
  `e1aa2c041550006f3e3f3c462a37bb3e543f13f971a8b7c66b5223e33594b49d`
- attempt journal SHA-256:
  `bf7fd93e7ab965e95cc5d8982274faa21f9e9fb8ee38e825974531a12dbf450d`

ただし出力監査で、planner justification が具体的 gate mechanism を述べ、それを coder payload へ
そのまま転送しうる causal contamination を検出した。この run は provider/harness 完走実証には使えるが、
planner/coder の独立推理 evidence には使わない。

### v3 — planner mechanism を coder から構造遮断した後の完走

- trial: `claude-abc-g1-v3`
- status: `complete`
- role attempts: 12/12 valid
- cells: 3/3 `dry-pass`
- stop: 3/3 `fixed-generation-budget`
- report SHA-256:
  `31c52341a81daf919e7ff62f1e8d30fb511e510f2ee1a76217560f440c5d8f3c`
- attempt journal SHA-256:
  `0d1373568c0650e308939ac6200d61263697b9f8a20c06c775bbdf838fc8e2cb`

planner→coder はこの run から `axis/direction/magnitude` の3 field だけ。justification と uncertainty
は report には残すが coder 入力へ流さない。

| workload | descriptor rr | planner | coder proposal (要約) | auditor | critic reverse |
|---|---:|---|---|---|---|
| A | 50 | explore_both / medium | node/insert/scan/update-absent 以外で gate pass | pass | false |
| B | 95 | explore_both / medium | A と同一 | pass | false |
| C | 100 | increase / large | unset/lock-conflict/read-locked で gate pass | pass | false |

各 proposal は `kUnset=true` fail-safe を満たし、diff quarantine、禁止識別子 gate、auditor digest
照合を通った。`dry-pass` なので build、legacy/S2 verify、bench は行っていない。

## 4. 科学的な読み方

観測できたのは次だけ:

1. Python が人間セッションなしで A/B/C の descriptor を proposal 前に4 roleへ運べる
2. role output / prompt / payload / descriptor / envelope を hash で束縛して全件報告できる
3. invalid schema を retryせず partial result にできる
4. planner の自然文 mechanism を coder 入力から構造的に落とせる
5. A/B と C で abstract direction / coder proposal が分岐する1例が得られた

観測していないもの:

- proposal が compile するか
- legacy+S2 correctness
- throughput / abort / latency / IPC / cache miss
- descriptor が proposal差を**因果的に**生んだか
- descriptor-on が off/swapped より良いか

A/B の coder proposal は同一であり、C の差も1 sample の on-only output。rationale の workload
言及や出力差を「workload-aware synthesis 成立」と数えない。

## 5. Evidence の耐久性

上記3 live run の raw payload/envelope/report は `/tmp/izanagi-t178-live*` の local operational
artifact で、正式 freeze ではない。本 insight は status と SHA を残す compact receipt であり、
raw bundle の durable formal evidence を代替しない。論文・正式判定へ転用しない。

正式 run は default `output/autonomous-trials/<trial-id>/` または承認済み durable root に保存し、
H1/H2 arm freeze と同じ証拠鎖へ束縛する。

## 6. 次の順序

1. current commit 上で A/B/C × 1 generation の single-tenant live
   build → legacy+S2 → bench を operational pilot として走らせる
2. H1 rr80 / H2 rr20 × descriptor on/off/swapped、同一 generation budget、固定 stop、
   全 attempt 報告を実装・freeze
3. formal run の前に bench 実時間 budget accounting と crash resume の扱いを固定

Runbook: `docs/phase3-s8c-autonomous-trial-runbook.md`。設計裁定: D106。

### Live preflight の結果

commit `436a3af` 後に login host で T-235 を開始したが、CCBench は d706650 pinned-clean、
競合 `ycsb_*.exe` は無しである一方、`numactl` が未導入だった。trigger driver の legacy+S2
経路は `numactl --interleave=all` を correctness/measurement contract として要求するため、
空 command へ差し替えず実計測を停止した。T-235 は Pegasus または同契約を満たす NUMA 計測
host で再開する。

### 取り込み時の採番訂正 (2026-08-01、[T-207])

本 insight は `codex/p3-autonomous-trial` (tip `402086d`) 上で 2026-07-29 に書かれ、
2026-08-01 に main へ取り込まれた。分岐中に main が同じ番号を別内容へ使ったため、
取り込み時に次を機械的に振り替えた。**内容・数値・SHA は 1 文字も変えていない。**

- 設計裁定 `D99` → `D106`。main の `D99` は `[T-143] RuleOps v1` である
- live build pilot の task ID `T-179` → `T-235` (本節 2 箇所)。main の `T-179` は
  `worker 資源台帳` (完了済み) である
- runbook path は取り込み時に `docs/phase3-8c-…` → `docs/phase3-s8c-…` へ改名した
  (`tools/check_docs.py` の段 runbook lint glob `phase3-s*-runbook.md` へ編入するため)
