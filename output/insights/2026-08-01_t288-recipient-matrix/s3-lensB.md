NO-GO。必読ファイルは全件取得済み。以下は静的レビューのみで、pytest・編集・commit は行っていない。

### B-01

- 判定: blocker
- 主張: role payload の値の意味と critic の key 集合を変えるのに、プランは report だけを v2 化し、role input／attempt journal の `SCHEMA_VERSION` を v1 のまま再利用している。同じ v1 が `abort_rate_pct=0.079` と `7.9`、critic の `abort_rate_pct` と `abort_rate` の双方を意味する破壊的 drift になる。
- 根拠: [p3_autonomous_workload_trial.py:88](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:88)、[p3_autonomous_workload_trial.py:605](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:605)、[p3_autonomous_workload_trial.py:1028](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:1028)、[s2-plan.md:74](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s2-plan.md:74)、[s2-plan.md:98](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s2-plan.md:98)、[s2-plan.md:114](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s2-plan.md:114)
- 成果物影響: v1 payload の SHA・role 応答・attempt journal を旧実走と意味比較できなくなり、受理 variant と proof-chain 参照が曖昧になる。

### B-02

- 判定: blocker
- 主張: P5 は成立していない。単位だけなら既存例示と合うが、今回追認する recipient matrix は live producer と role source の field 契約が食い違ったままであり、D116 に「不一致あり」と書くだけでは実際に role が読む prompt を直せない。
- 根拠:
  - coder の例示 `baseline` は 2 key だけだが、現行・計画とも 5 key を渡す: [coder-v4-autonomous-trigger-gating.md:50](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/.claude/agents/coder-v4-autonomous-trigger-gating.md:50)、[p3_autonomous_workload_trial.py:796](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:796)、[p3_autonomous_workload_trial.py:858](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:858)、[s2-plan.md:56](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s2-plan.md:56)
  - role 例示は `planner_direction.justification` を要求するが、実装は意図的に転送しない: [coder-v4-autonomous-trigger-gating.md:44](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/.claude/agents/coder-v4-autonomous-trigger-gating.md:44)、[p3_autonomous_workload_trial.py:851](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:851)
  - 「入力は 5 field のみ」に反し `**common` の 9 field も渡る: [coder-v4-autonomous-trigger-gating.md:57](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/.claude/agents/coder-v4-autonomous-trigger-gating.md:57)、[p3_autonomous_workload_trial.py:601](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:601)、[p3_autonomous_workload_trial.py:843](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:843)
  - planner は同じ LLC 値を `current_perf.llc_miss_rate=0.124` と `leading_indicators.cache_miss_rate_pct=12.4` の二単位で同時に読む計画だが、source は後者しか説明しない: [planner-v4.md:32](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/.claude/agents/planner-v4.md:32)、[s2-plan.md:58](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s2-plan.md:58)
  - プラン自身も矛盾を認識して放置している: [s2-plan.md:138](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s2-plan.md:138)、[s2-plan.md:146](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s2-plan.md:146)
- pin 閉包:
  - role 本文を直すと `SOURCE_FILE_SHA256` の coder/planner が赤: [review_ledger.py:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/codex_roles/review_ledger.py:22)、[review_ledger.py:25](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/codex_roles/review_ledger.py:25)、検出点 [spec.py:582](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/codex_roles/spec.py:582)。
  - description も直すなら `DESCRIPTION_SHA256` も赤: [review_ledger.py:62](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/codex_roles/review_ledger.py:62)、[review_ledger.py:65](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/codex_roles/review_ledger.py:65)。
  - ledger 更新後も adapter を再生成しなければ byte parity が赤: [check_codex_agents.py:241](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/tools/check_codex_agents.py:241)、現行 pin [coder adapter:165](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/.codex/role-adapters/coder-v4-autonomous-trigger-gating.json:165)、[planner adapter:124](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/.codex/role-adapters/planner-v4.json:124)。
  - `planner_direction.justification` を source から落とすと、manifest がなお required のため source example parity も赤: [manifest.json:876](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/codex_roles/manifest.json:876)、[check_codex_agents.py:195](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/tools/check_codex_agents.py:195)。この場合は `SCHEMA_SHA256` と `ROLE_MANIFEST_SHA256` も更新対象: [review_ledger.py:99](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/codex_roles/review_ledger.py:99)、[review_ledger.py:41](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/codex_roles/review_ledger.py:41)。
  - 逆に `baseline` 内の key 差は schema が open object のため parity が見逃す: [manifest.json:873](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/codex_roles/manifest.json:873)、[check_codex_agents.py:168](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/tools/check_codex_agents.py:168)。
- no-role-md の成立条件: [claude_projected_provider.py:128](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/claude_projected_provider.py:128) の優先 mediated contract に exact field・単位・source 例との差を明記し、producer parity をテストする場合だけ救える。現行 `ROLE_CONTRACTS` はそこまで規定していない。
- 成果物影響: coder/planner が未文書化の値や重複単位を解釈して proposal を変え、受理 variant／certified 集合と「何を見せたか」の台帳が食い違う。

### B-03

- 判定: blocker
- 主張: `nan`/`inf` を `_metric_projection()` で `None` にしても、raw `outcome` は `generation_record["harness"]` に残る。最終 report は `allow_nan=False` なので書込みが失敗し、しかも `run-finish` は report 書込みより先に journal へ記録される。
- 根拠: [p3_autonomous_workload_trial.py:536](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:536)、[p3_autonomous_workload_trial.py:951](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:951)、[p3_autonomous_workload_trial.py:751](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:751)、[p3_autonomous_workload_trial.py:757](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:757)、[s2-plan.md:25](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s2-plan.md:25)
- 具体入力: `fitness_tps=float("nan")`、`leading_indicators.abort_rate=float("inf")`、`latency_ns=float("-inf")`。射影値だけは `None` になるが raw harness のため report は生成不能。
- 成果物影響: journal が「run-finish/report path」を指すのに report が存在しない破断台帳となり、certified 結果の再現・参照が失われる。

### B-04

- 判定: must-fix
- 主張: 異常値を欠損へ黙って畳む契約は不正である。`None` は role contract 上「未観測」を意味する一方、プランは有限な負 throughput／latency／IPC をそのまま受理し、異常な率だけを `None` に偽装する。
- 根拠: [s2-plan.md:23](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s2-plan.md:23)、[s2-plan.md:42](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s2-plan.md:42)、[p3_autonomous_workload_trial.py:116](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:116)、[p3_autonomous_workload_trial.py:127](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:127)
- 具体入力:
  - `None`、`False`、`True`: `None` 化は妥当。
  - ratio `0.0` / `1.0`: `0.0%` / `100.0%` として妥当。
  - ratio `-0.001` / `1.0000000000000002`: 「異常」でなく「未観測」に化ける。
  - `throughput=-1.0`、`latency_ns=-5.0`、`ipc=-0.1`: finite 判定だけなので role へ通る。
- 成果物影響: critic/planner/coder が計測異常を欠損または実値と誤認し、提案方向・受理 variant と report の normalized/raw 値が分裂する。

### B-05

- 判定: must-fix
- 主張: 提案された 5 テストは全部が恒真ではないが、全 recipient と generation-1 境界を固定していない。特に初期 `None`、critic 配線、input schema version の一行変異が緑のまま残る。
- 根拠: [s2-plan.md:154](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s2-plan.md:154)、[s2-plan.md:175](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s2-plan.md:175)、現行 recorder [test_p3_autonomous_workload_trial.py:66](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:66)

各案の歯は次のとおり。

| テスト案 | 壊す一行 | 判定 |
|---|---|---|
| ratio key/unit | 現行 [p3_autonomous_workload_trial.py:523](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:523) の abort source を LLC source にする | `.079 != .124` で落とせる |
| invalid numbers | 新 helper の `math.isfinite` または bool/range guard を削る | 列挙値を個別 assert すれば落とせる。ただし `10**400` の overflow はテスト表に無い |
| percent conversion | `ratio * 100.0` を `ratio` にする | 7.9/12.4 literal で落とせる |
| unobserved None | `None` 分岐を `0.0` にする | helper 単体では落とせる |
| second generation | planner [line 818](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:818) または coder [line 858](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:858) を internal dict 直渡しにする | 明示 7.9 assert なら落とせる |

生き残る変異:

- 初期 `abort_rate=None` を `0.0` にする一行: [p3_autonomous_workload_trial.py:798](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:798)。helper 単体と generation-2 assert は通るため、generation-1 の実 payload assert が必要。
- critic の `dict(current_metrics)` を `dict(perf_payload)` にする一行: [p3_autonomous_workload_trial.py:963](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:963)。提案テストは critic payload を一度も断言しない。
- `SCHEMA_VERSION` を v1 のままにする一行: report v2 assert とは独立なので通る。
- `disk report is v2` を `A.REPORT_SCHEMA_VERSION` と比較する形は恒真候補。現行の `on_disk == report` も同じ生成物同士の比較であるため、literal `"p3-autonomous-workload-trial-report/v2"` を要求すべき: [test_p3_autonomous_workload_trial.py:201](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:201)。
- [s2-plan.md:156](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s2-plan.md:156) は「report/internal は ratio のまま」と「report 側で ×100」を同じ行で主張しており、期待値自体が矛盾している。

現行 hash の fixture 焼き込みは計画上見当たらない。問題は hash ではなく、未観測経路と critic consumer が未 assert なことにある。

- 成果物影響: generation 1 に偽の 0 が入り現在の proposal を変える、または critic だけ percent payload を読む変異が、テスト緑のまま report／将来の選択へ入る。

### B-06

- 判定: must-fix
- 主張: 「機械構築は 8c のみ」は Python producer に限れば真だが、role-facing 経路全体では偽である。段4b・段5 runbook はメインセッションに `_pct` field を手作業で射影させるのに、WAL/calibrator の ratio を `×100` する規約が無い。
- 根拠: [phase3-s4b-runbook.md:41](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/docs/phase3-s4b-runbook.md:41)、[phase3-s4b-runbook.md:54](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/docs/phase3-s4b-runbook.md:54)、[phase3-s5-sort-runbook.md:40](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/docs/phase3-s5-sort-runbook.md:40)、[phase3-s5-sort-runbook.md:56](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/docs/phase3-s5-sort-runbook.md:56)、ratio 契約 [model.py:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/calibrator/model.py:38)、[benchparse.py:66](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/calibrator/benchparse.py:66)
- 成果物影響: 手動駆動の planner/coder は引き続き 0.079 を 0.079% と読めるため、別 campaign の受理 variant／certified 集合が 100 倍ずれのまま残る。

### B-07

- 判定: must-fix
- 主張: 親 brief の「planner/coder が誤単位を読み certified 選択が変わる」は現行承認範囲について過大表現である。上限 1 generation では両 role は全 `None` を読むだけで、有限値を受けるのは評価後の critic だけである。
- 根拠: [p3_autonomous_workload_trial.py:91](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:91)、[p3_autonomous_workload_trial.py:189](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:189)、[p3_autonomous_workload_trial.py:796](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:796)、評価後の更新 [p3_autonomous_workload_trial.py:951](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:951)、critic [p3_autonomous_workload_trial.py:957](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:957)、親主張 [brief.md:47](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/brief.md:47)
- 成果物影響: 現行 1-generation artifact では変わるのは critic attribution／role 台帳であり、planner/coder 起因の受理集合変更は multi-generation 開放後に限定される。

### B-08

- 判定: nit
- 主張: 「8c live artifact 0 件」は偽で、追跡済み report に加えて attempt journal も存在する。`FROZEN_MANIFEST` は `output/` 全体ではなく exact 23 path だけであり、両 artifact は対象外である。
- 根拠: [control report:211](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/output/insights/2026-08-01_t241-compute-llm-transport/evidence/control-876813-report.json:211)、[control attempts:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/output/insights/2026-08-01_t241-compute-llm-transport/evidence/control-876813-attempts.jsonl:1)、[test_frozen_artifacts.py:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_frozen_artifacts.py:38)、[test_frozen_artifacts.py:141](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_frozen_artifacts.py:141)
- 成果物影響: unit key の過去互換結論は変わらないが、artifact inventory から journal schema／report hash 参照を落とすと proof-chain の列挙が不完全になる。

### B-09

- 判定: must-fix
- 主張: `generation_record["metrics"]` と report v2 は、単位換装に必要な修正ではなく独立した durable schema 拡張である。誤った P3 前提を訂正した後に新 field を足すなら、単位修正へ黙って抱き合わせず別裁定に分離すべきである。
- 根拠: 現行 report は raw `harness` を既に保持 [p3_autonomous_workload_trial.py:951](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:951)、追加案 [s2-plan.md:89](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s2-plan.md:89)、schema bump [s2-plan.md:114](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s2-plan.md:114)、現行 live report generation shape [control report:32](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/output/insights/2026-08-01_t241-compute-llm-transport/evidence/control-876813-report.json:32)
- 成果物影響: exact-key consumer の受理集合と report 参照 version が変わる一方、certified 判定ロジック自体は変わらない。

### B-10

- 判定: backlog
- 主張: scope 外だが real。multi-generation で bench 未到達の reject/dry outcome が来ると、直近の有効測定を全 `None` で無条件上書きし、role 文書の「直近実測 baseline」と一致しなくなる。
- 根拠: 欠損 outcome の射影 [p3_autonomous_workload_trial.py:505](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:505)、無条件上書き [p3_autonomous_workload_trial.py:953](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:953)、role 契約 [coder-v4-autonomous-trigger-gating.md:57](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/.claude/agents/coder-v4-autonomous-trigger-gating.md:57)
- 成果物影響: reject 後世代の planner/coder が既知 baseline を失い、次の proposal と最終受理 variant が変わる。
- 裁定パッケージ候補: 「直前 outcome の metrics」と「last valid measured baseline」のどちらを recipient matrix に載せるかを別 ID で決める。

### B-11

- 判定: backlog
- 主張: scope 外だが real。`ratio * 100.0` の丸め・表示精度契約がなく、`pytest.approx` だけでは role が実際に読む JSON 数値表現を固定できない。
- 根拠: 無丸め乗算 [s2-plan.md:32](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s2-plan.md:32)、approx 案 [s2-plan.md:158](/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/s2-plan.md:158)、canonical JSON [s8b_prediction_runner.py:214](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/s8b_prediction_runner.py:214)
- 具体値: `0.29 * 100` は `28.999999999999996`、`0.07 * 100` は `7.000000000000001`、`-0.0` は `-0.0` として直列化されうる。
- 成果物影響: role input の字面と payload SHA が不要に変わり、LLM proposal と台帳参照が安定しない。
- 裁定パッケージ候補: 「無丸め binary float」「固定桁 round」「decimal 文字列」のどれを role 契約にするかを別 ID で決める。

## 親実測 4 点の独立検証

| 主張 | 判定 |
|---|---|
| 対象 test file の 6 token が grep 0 | 真。各 token 0 件。ただしこれは lexical evidence であり coverage 計測そのものではない |
| `FROZEN_MANIFEST` は本件非対象 | exact 23 path について真。`output/` 全体を freeze するものではない |
| 8c live artifact は 0 件 | 偽。追跡済み report と attempt journal の少なくとも 2 ファイル |
| 機械構築は 8c のみ | Python producer に限れば真。運用上の手動 role 投影は段4b・段5 runbook に残る |

## 総括

**NO-GO。blocker 3 件。**

止める理由は、input schema v1 の意味再利用、P5 が放置する live/source recipient 契約不一致、非有限値で terminal report が消える三点。これらを解消し、generation-1・critic・schema literal を実配線テストで固定するまで実装へ進めてはならない。pytest は実走していない。