## R1

- **対象:** 棚卸し表の「全 child 起動面」
- **判定:** MISSING
- **重大度:** BLOCKER
- **根拠:** 通常の Codex collaboration child (`spawn_agent`) が表にない。[AGENTS.md:21](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/AGENTS.md:21) は「`task_name` を role 名にした通常の Codex 子」に言及し、[docs/decisions.md:2057](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/docs/decisions.md:2057) も「`spawn_agent` schema には custom profile を明示選択する field がなく、`task_name=auditor` 等は generic child」と確認している。これは X9 の skill 入口とも X1〜X6 の `codex exec` とも別面。model/reasoning の既定・継承挙動は repository 内証拠では未確認。
- **是正案:** X10 として generic `spawn_agent` を追加し、model/reasoning の指定可能性・既定・継承を runtime schema の一次資料で記録する。

## R2

- **対象:** 棚卸し表の網羅性
- **判定:** MISSING
- **重大度:** HIGH
- **根拠:** `tools/codex_reasoning_ab.py` は独立した直接 `codex exec` 起動面である。[tools/codex_reasoning_ab.py:48](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/codex_reasoning_ab.py:48) に `MODEL = "gpt-5.6-sol"`、[同:1806](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/codex_reasoning_ab.py:1806) に argv、[同:1812](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/codex_reasoning_ab.py:1812) に `model_reasoning_effort={arm}`、[同:2031](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/codex_reasoning_ab.py:2031) に実 `subprocess.Popen` がある。`collect-run` は `max|high` の allowlist を持つ（[同:5223](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/codex_reasoning_ab.py:5223)）。
- **是正案:** T-181 専用・非標準面として X11 に追加し、現在は再走待ち／標準 dev-wave 未配線と明記する。

## R3

- **対象:** C6 の `live? = 無人継続時`、A4 の現行 live 経路としての扱い
- **判定:** REFUTED
- **重大度:** HIGH
- **根拠:** 実装自身が [tools/dev_waves/worker.py:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/dev_waves/worker.py:1) で `"Bounded, fake-only child process worker"` と名乗る。D74 も「fake child 限定、real は未開放」（[docs/decisions.md:2955](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/docs/decisions.md:2955)）、「real `claude -p`・課金・network は使わない」（[同:2959](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/docs/decisions.md:2959)）、「real `claude -p` の起動経路は本層に存在しない」（[同:2991](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/docs/decisions.md:2991)）と明記する。
- **是正案:** C6 を `fake-only / runtime inactive` に直す。A4 は「real 開放時の潜在的 validation gap」とし、現在のトークン消費や xhigh fallback への因果を削除する。

## R4

- **対象:** A1「effort 側は2026-07-19承認裁定の未適用分」
- **判定:** REFUTED
- **重大度:** HIGH
- **根拠:** 承認内容が `opus/high` だった点は正しい（[docs/archive/worklog-phase3-0719.md:83](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/docs/archive/worklog-phase3-0719.md:83)、[同:97](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/docs/archive/worklog-phase3-0719.md:97)）。しかし後続の直接観測台帳は `effort=xhigh→high` を `done`、現物 `effortLevel=high` と記録している（[output/insights/2026-07-19_backlog-triage.md:1728](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/output/insights/2026-07-19_backlog-triage.md:1728)、[同:1729](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/output/insights/2026-07-19_backlog-triage.md:1729)）。現在値は再び `xhigh`（[/home/SFC/tanab/.claude/settings.json:10](/home/SFC/tanab/.claude/settings.json:10)）。したがって「未適用」ではなく「一度適用後に再変更された」が静的証拠に合う。
- **是正案:** 「現在は承認値から再ドリフト。再変更の理由・ユーザー裁定は未確認」と直す。

## R5

- **対象:** A1「model 側は適用済み」、および「親の全ターン・全 ad-hoc 子が xhigh」
- **判定:** OVERSTATED
- **重大度:** HIGH
- **根拠:** 承認値は文字どおり `model: "opus"`（[docs/archive/worklog-phase3-0719.md:97](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/docs/archive/worklog-phase3-0719.md:97)）だが、現物は `opus[1m]`（[/home/SFC/tanab/.claude/settings.json:5](/home/SFC/tanab/.claude/settings.json:5)）であり exact 一致ではない。また設定ファイルは既定値の証拠であって、各 live session の override や served effort の証拠ではない。Claude result allowlistにも effort はない（[tools/dev_waves/receipt.py:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/dev_waves/receipt.py:22)）。
- **是正案:** 「user default は `opus[1m]/xhigh`」までに限定し、現在セッションと全 child への実適用は未確認とする。

## R6

- **対象:** A2「Agent tool に effort は存在しない」「常に継承」「唯一の緩和は named role」
- **判定:** OVERSTATED
- **重大度:** MEDIUM
- **根拠:** repository 内では `guard_agent` が「Agent 呼び出し自体に effort パラメータは無い」と記述する（[hooks/guard_agent.py:104](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/hooks/guard_agent.py:104)）。ただしこれは製品 schema の一次資料ではない。さらに `agent()` は effort 明示を扱い（[tools/check_workflow_models.py:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/check_workflow_models.py:22)）、セッション既定を high に戻すことも緩和になるため、「唯一」は per-Agent-call の個別 pin に射程を限定しない限り過大。
- **是正案:** 「repo 内 hook が前提とする Agent schemaでは個別 effort 指定不能。製品 schema は未確認」と書き、緩和策を named role／Workflow／session default に分ける。

## R7

- **対象:** A3 の CLI fail-open、default=xhigh、served effort attest 不在
- **判定:** OVERSTATED
- **重大度:** HIGH
- **根拠:** JSON result の許可 field に effort がない点は確認できる（[tools/dev_waves/receipt.py:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/dev_waves/receipt.py:22)）。S8b も `modelUsage` の opus slug と token は検査するが（[orchestrator/campaign/s8b_prediction_runner.py:1189](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/orchestrator/campaign/s8b_prediction_runner.py:1189)）、effort は検査しない。一方、監査ディレクトリには command・CLI version・stdout・stderr・rc の独立 raw artifact がなく、警告と rc=0 は静的には未確認。まして warning の “default effort” が settings の xhigh を意味する証拠はない。
- **是正案:** 「JSON result に effort field がない」は採用可。fail-open 実測は逐語 artifact を保存し、default の実体は `未確認` とする。

## R8

- **対象:** A4 の model/effort validation 非対称性
- **判定:** CONFIRMED
- **重大度:** MEDIUM
- **根拠:** model は `allowed_models` が空でないこと、選択 model が含まれることを検査する（[tools/dev_waves/daemon.py:222](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/dev_waves/daemon.py:222)）。CLI の allowlist 自体は運用者入力（[tools/dev_waves/cli.py:90](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/dev_waves/cli.py:90)）。effort は非空 ASCII（[tools/dev_waves/daemon.py:226](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/dev_waves/daemon.py:226)）と `_EFFORT_RE` の形だけ（[tools/dev_waves/schema.py:830](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/dev_waves/schema.py:830)）。result field 集合に effort はない（[tools/dev_waves/receipt.py:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/dev_waves/receipt.py:22)）。
- **是正案:** 構造的非対称は残すが、固定 catalog allowlist ではなく「運用者が与える allowlist」、かつ fake-only と明記する。

## R9

- **対象:** A5「DW-S02 reasoning=max は doctrine 適用範囲外で過剰」
- **判定:** OVERSTATED
- **重大度:** HIGH
- **根拠:** 現行契約は段2を明示的に `gpt-5.6-sol/max` とする（[docs/dev-wave/workers.md:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/docs/dev-wave/workers.md:5)）。過去の決定記録も「プラン起草 max」を標準ループとしている（[docs/decisions.md:2645](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/docs/decisions.md:2645)）。T-181 が測ったのは段2ではなく focused review の名指し R-1（[output/insights/2026-07-30_t181-reasoning-ab/README.md:10](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/output/insights/2026-07-30_t181-reasoning-ab/README.md:10)）。全体は10 runで、POS が n=6、NEG が n=4（[同:35](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/output/insights/2026-07-30_t181-reasoning-ab/README.md:35)）。さらに replay 未認証（[同:56](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/output/insights/2026-07-30_t181-reasoning-ab/README.md:56)）で、結果は当該 prompt/snapshot/期間限定（[同:44](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/output/insights/2026-07-30_t181-reasoning-ab/README.md:44)）。
- **是正案:** A5 を real finding ではなく「明示 policy の変更提案」に降格する。T-181 は POS n=6＋NEG n=4、段2への外挿禁止と書く。

## R10

- **対象:** A6「DW-S06-A の実運用は一貫して high」「reasoning 未明記の唯一の子起動段」
- **判定:** REFUTED
- **重大度:** HIGH
- **根拠:** 過去の実運用は段6敵対レビューを `max` と記録している（[docs/decisions.md:2645](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/docs/decisions.md:2645)、[同:2648](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/docs/decisions.md:2648)）。別 wave も「敵対レビュー2 (max)、焦点再レビュー1 (max)」（[output/insights/2026-07-26_t106-t107-parser-authoritative.md:149](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/output/insights/2026-07-26_t106-t107-parser-authoritative.md:149)）。また DW-S06-C の焦点再レビューも reasoning を指定していない（[docs/dev-wave/workers.md:61](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/docs/dev-wave/workers.md:61)）。
- **是正案:** 「S06-A/S06-C とも現行契約では未指定、歴史運用は主に max」と訂正する。high 化は別途裁定事項。

## R11

- **対象:** A7「live `codex_worker_launch.py --reasoning` に許可リストがない」
- **判定:** CONFIRMED
- **重大度:** MEDIUM
- **根拠:** parser は `--reasoning` を required にするだけで choices がない（[tools/codex_worker_launch.py:2474](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/codex_worker_launch.py:2474)）。一方で rollout の model/effort が要求値と一致するかは検査している（[同:772](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/codex_worker_launch.py:772)）。adapter 側の allowlist は存在する（[orchestrator/codex_roles/launcher.py:353](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/orchestrator/codex_roles/launcher.py:353)、[orchestrator/codex_roles/spec.py:608](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/orchestrator/codex_roles/spec.py:608)）。
- **是正案:** 「無検証」ではなく「要求値との一致は検証するが、値域／model×reasoning compatibility は未検証」と精密化する。

## R12

- **対象:** A9「`spec.py` の sol/high 統一は D54 の意図的統一」
- **判定:** REFUTED
- **重大度:** MEDIUM
- **根拠:** D54 の初版統一は3 roleについての履歴であり、同節自身が active 裁定を supersede 済みとする（[docs/decisions.md:2055](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/docs/decisions.md:2055)、[同:2065](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/docs/decisions.md:2065)）。現行 spec は `{sol, terra}` と `{medium, high}` を許し（[orchestrator/codex_roles/spec.py:608](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/orchestrator/codex_roles/spec.py:608)）、verifier を terra/medium に固定する（[同:616](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/orchestrator/codex_roles/spec.py:616)）。全13 runtime blocked は確認できる（[.codex/agents/README.md:12](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/.codex/agents/README.md:12)）。
- **是正案:** 「全13 runtime blocked／official provider cost 0」は残し、「sol/high 統一」は削除して現行段付けを記す。

## R13

- **対象:** A8「変更を要する role なし」、A10「過小方向の不整合は発見しなかった」
- **判定:** OVERSTATED
- **重大度:** MEDIUM
- **根拠:** project role の数と配分自体は確認できる。例えば auditor は opus/high（[.claude/agents/auditor.md:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/.claude/agents/auditor.md:5)）、coder と verifier は sonnet/medium（[.claude/agents/coder.md:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/.claude/agents/coder.md:5)、[.claude/agents/verifier.md:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/.claude/agents/verifier.md:5)）。ただし「変更不要」は前回監査の政策判断であり、今回の頻度・品質再計測ではない。さらに R1/R2 の欠落面があるため「全 surface で過小なし」は導けない。
- **是正案:** 「13 project named role では、既存方針に対する新たな mismatch を静的に観測しなかった」に限定する。

## R14

- **対象:** X5 の表記
- **判定:** REFUTED
- **重大度:** nit
- **根拠:** 表の model 欄が「段5契約を継承 → high」になっているが、`high` は reasoning。段5契約は `reasoning=high`（[docs/dev-wave/workers.md:24](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/docs/dev-wave/workers.md:24)）で、共通起動 command の model は `gpt-5.6-sol`（[docs/dev-wave/operations.md:8](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/docs/dev-wave/operations.md:8)）。
- **是正案:** X5 を `model=gpt-5.6-sol / reasoning=high` に修正する。

## R15

- **対象:** C1「`codex_roles/spec.py` が frontmatter 必須 key を強制」
- **判定:** OVERSTATED
- **重大度:** MEDIUM
- **根拠:** parser が全5 keyを要求すること自体は正しい（[orchestrator/codex_roles/spec.py:45](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/orchestrator/codex_roles/spec.py:45)、[同:297](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/orchestrator/codex_roles/spec.py:297)）。ただしこれは checker/static parity 経路であり Claude Agent 起動時の gate ではない。live hook は model の存在だけを見て許可し（[hooks/guard_agent.py:78](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/hooks/guard_agent.py:78)）、hook 自身も fail-open（[同:116](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-token-hygiene/hooks/guard_agent.py:116)）。
- **是正案:** 検証機構欄を「static checker/testで全keyを強制、Claude launch-time hookはmodelのみ」に分ける。

## 総括

**NO-GO**

- BLOCKER: **1件**
- HIGH: **7件**

主な停止理由は、棚卸しが generic Codex `spawn_agent` と `tools/codex_reasoning_ab.py` を欠くこと、C6 を real/live と誤分類していること、A1 の「未適用」帰属と A6 の「一貫して high」が反証されたこと、A5 が T-181 の射程を段2へ外挿していること。

草案のうち事実として採用してよい主張は次のとおり。

- 現在の user settings の文字列は `opus[1m] / xhigh`。ただし live session の served effort ではない。
- 2026-07-19 の承認内容は `opus / high`。effort は一度適用された記録があり、現在は再ドリフト。
- project named role は13件で、opus/high 10件、sonnet/medium 3件。
- C4 は通常 opus、canary haiku、effort high 固定。
- C5 は selector の opus/high frontmatterを assertし、CLI effort high、served model slugを `modelUsage` で検査する。
- Workflow lint は standalone であり hook 未配線。model欠落はNG、effort欠落はWARN。
- `tools/dev_waves` の model/effort validation は非対称。ただし fake-only・real未開放。
- DW-S02/S03 は sol/max、DW-S05 は reasoning high。DW-S06-A/S06-C は reasoning 未指定。
- `codex_worker_launch.py` は reasoning の値域を検証しないが、rollout記録値との一致は検証する。
- Codex adapter 13件は runtime blocked。現行 spec は sol/terra、medium/high、verifier terra/medium。
- T-181 の記述値は POS n=6、NEG n=4、計10 run。replay未認証・非盲検・限定 promptであり、policyや段2変更の根拠にはできない。
- Claude JSON resultに effort fieldがない。`--effort bogus` の rc=0 と default の実体は、保存済み一次資料がなく未確認。