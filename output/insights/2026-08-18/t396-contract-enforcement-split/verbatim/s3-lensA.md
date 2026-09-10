判定は **NO-GO** です。静的監査のみで、pytest・checker は未実走です。worktree は変更していません。

### 所見 1 — 第 3 bullet の説明配置契約を「完全機械執行」と誤分類している

**判定への影響:** `implementation` 内へ説明を置かず `justification` へ分離する契約が人手監査から落ちます。機械受理集合自体は変わりませんが、契約違反 proposal が certified 選択へ残り、材料レポートの source と justification の帰属が誤る可能性があります。

**根拠:**

- 現行 bullet は delimiter と line splice の禁止に加えて、説明の配置も命じています: `.claude/agents/coder-v4-autonomous-sort.md:87`
- 段 2 は bullet 全体を「完全」としていますが、根拠は delimiter と splice だけです: `s2-plan.md:58`
- 置換案でも説明配置を「機械執行される項目」に入れています: `s2-plan.md:86-91`
- `justification` は optional key で、schema gate は key 集合しか検査しません: `orchestrator/campaign/projection_guard.py:32-33,261-290,325-330`
- loader は欠落した `justification` を空文字列にし、quarantine は `implementation` だけを走査します: `orchestrator/campaign/p3_s4_loop_sort.py:371-379`, `orchestrator/campaign/p3_s4_loop.py:245-246`

**区分:** must-fix

### 所見 2 — 置換案は「内部で処理された例外送出」の禁止を落としている

**判定への影響:** 現行の「例外送出は不可」より policy 上の受理集合が広がります。oracle の外側へ伝播しない例外送出は、置換後の機械項にも residual 項にも属さず、他の gate を通れば build・certification の対象になり得ます。

**根拠:**

- 現行契約は禁止対象を限定せず「例外送出は不可」とします: `.claude/agents/coder-v4-autonomous-sort.md:89`
- 置換案の機械項は「oracle が実際に観測した例外」、residual は「corpus で発火しない条件付き例外」に限定されています: `s2-plan.md:91,98`
- oracle の catch は comparator 呼び出しの外側にあり、外へ伝播した例外だけを exit 72 にします: `orchestrator/campaign/sort_swo_oracle.py:775-793,1051-1061`
- lexical deny table に `throw` 規則はありません: `orchestrator/campaign/coder_effect_gate.py:58-120`
- 段 2 自身も専用 fixture がないと記録しています: `s2-plan.md:62`
- M7 は置換案に書かれた「条件付き例外」の文だけを守るため、既に落ちている分類を検出しません: `s2-plan.md:285-287`

攻撃文字列は構成していません。これは catch 境界による入力クラスの分類です。

**区分:** must-fix

### 所見 3 — 「auditor が拒否する」は現行 auditor 契約へ結線されていない

**判定への影響:** residual の禁止が実際の auditor 入力から落ちたまま、材料レポートには「auditor が拒否」と記録され得ます。機械 gate は schema が整った `pass` をそのまま受け入れるため、certified 選択へ契約違反 variant が残る可能性があります。

**根拠:**

- 置換案は residual 5 項すべてについて auditor 拒否を主張します: `s2-plan.md:93-98`
- しかし段 2 自身が、auditor prompt は loop、非決定性、latent throw を個別列挙しないと認めています: `s2-plan.md:110`
- auditor の必須入力は diff、designated source、abort digest であり、sort closed-region 契約は含まれません: `.claude/agents/auditor.md:21-28`
- auditor は「正しさ違反」だけを reject し、それ以外は nit とします: `.claude/agents/auditor.md:32-36`
- checklist は header・型・macro 等には触れますが、bounded loop、説明配置、内部処理された例外、全非決定性を拒否規則として持ちません: `.claude/agents/auditor.md:66-82`
- runbook の auditor 入力にも closed-region residual はありません: `docs/phase3-s5-sort-runbook.md:94-103`
- 機械 gate は digest・schema・verdict の整合だけを確認し、`pass` なら元の machine-pass を返します: `orchestrator/campaign/auditor_gate.py:190-220`

coder prompt に「auditor が拒否」と書くだけでは、分離された auditor の判定規則にはなりません。

**区分:** must-fix

### 所見 4 — caller 閉包は不完全だが、live coder proposal の build bypass は見つからない

**判定への影響:** 対応表を「全 sort-hole materialization」に一般化すると、S6 の材料レポートへ存在しない SWO oracle 参照が入ります。ただし S6 は固定された信頼中核候補だけであり、現行 live coder proposal の受理集合は変わりません。

**根拠:**

- `p3_s4_loop_sort.py` の entry point は `run_one_iteration:289`、`load_proposal_file:349`、`drive_iteration:383`、`_preview_diff:444`、`main:462` の全 5 個です。
- live build は `_quarantine_and_audit` 後だけ `run_campaign` に進みます: `orchestrator/campaign/p3_s4_loop_sort.py:321-332`
- `--no-build` も同じ gate を通ってから build 前に返ります: 同 `:321-327`
- `--preview-diff` は quarantine だけですが build sink を持ちません: 同 `:444-459`
- default fixture は digest 用 preview 後、改めて `run_one_iteration` を通ります: 同 `:544-569`
- 別の sort build 経路である S6 は固定 `CANDIDATES` のみを選び、設計上 SWO oracle を呼びません: `orchestrator/campaign/s6_sort_sweep.py:24-30,141-157,341-371`
- freeze の `sort_best` は `prepare_cell` で quarantine と SWO oracle を再実行します: `orchestrator/campaign/s1_direct_comparison.py:644-710`
- その materializer は S1 direct comparison のほか、S8b materialization、floor、oracle driver、pilot から再利用されます: `orchestrator/campaign/s8b_materialization.py:125-135`, `s8b_floor_campaign.py:3033-3112`, `s8b_oracle_driver.py:1528-1536`, `s8b_oracle_n_pilot.py:785-836`

production の `quarantine` 直接 call site は合計 15 箇所です:

- backoff: `p3_s4_loop.py:941,949`
- sort: `p3_s4_loop_sort.py:155,455,563`
- trigger loop: `p3_s4_loop_trigger_gating.py:420,889,1006`
- S6 sort: `s6_sort_sweep.py:333,354`
- S8a trigger: `s8a_trigger_sweep.py:434,456`
- freeze/direct comparison: `s1_direct_comparison.py:666`
- trigger calibration: `s1_verify_extime_calibration.py:342`
- autonomous trigger preview: `p3_autonomous_workload_trial.py:1225`

test-only の直接 caller は `test_p3_exploration_namespace.py`、`test_p3_s4_loop.py`、`test_p3_s4_loop_sort.py`、`test_p3_s4_loop_trigger_gating.py`、`test_s1_direct_comparison.py`、`test_s6_sort_sweep.py`、`test_s8a_trigger_sweep.py` に閉じています。

**区分:** should-fix。対応表を「live `CoderProposalSort` build 経路」に明示的に限定すれば安全側に直せます。

### 所見 5 — P3 は現行 sandbox 契約ではなく過去の観測で、親代行は D95 違反になる

**判定への影響:** 親が adapter JSON を書けば author/provenance 契約違反、書かなければ renderer byte parity と adapter 内 pin が不一致になります。adapter は dormant なので既存 certified 値は直接変わりませんが、この wave の commit・材料参照を監査済み成果として land できません。

**根拠:**

- brief は Codex sandbox の恒常制約として親代行を予定します: `s1-brief.md:68-70`
- 過去に `.codex/` 書込が拒否された観測は実在します: `docs/archive/worklog-phase3-0804-188-189.md:297-302`
- しかし現行の段 5 契約は一般的な `sandbox=workspace-write` だけです: `docs/dev-wave/workers.md:18-28`
- launcher も sandbox 値をそのまま渡すだけで、`.codex/` 専用除外を定義しません: `tools/dev_wave_codex.py:210-232`
- D149 決定 6 は production wiring と P1 の話で、親書込権限ではありません: `docs/decisions.md:7323-7328`
- D95 は `.codex/` の非 Markdown を明示的に実装面とし、Codex が書けなければ親が代行せず停止するよう命じます: `docs/decisions.md:4244-4259`
- 代行にはユーザー裁定済み waiver が必要です: `docs/decisions.md:4682-4685`

したがって P3 は「前例としては real、現行 sandbox の一般契約としては未証明」です。今回の read-only 段 3 では書込 probe をしていません。

**区分:** must-fix

### 対応表の確定結果

| 現行 bullet | 現行 main の判定 |
|---|---|
| 1. header・型/関数・macro・global | live coder build 経路では部分執行。header・macro・global の機械分類は支持、型/関数は残余 |
| 2. 生の前処理指令 | live coder build 経路では完全執行を支持 |
| 3. comment delimiter・line splice・説明配置 | delimiter と splice のみ完全。bullet 全体を完全とする判定は反証 |
| 4. 非決定 builtin | 部分執行を支持 |
| 5. API・straight-line・副作用・loop・例外 | 部分執行。残余は段 2 の 5 種より広く、内部処理された例外も含む |

P1 は「insight の残余 5 種が今も存在する」点だけ支持し、対応表の完全性は反証します。P2 の test 5 parameter 丸ごと削除は production を変えず、静的には支持します。Markdown の top-level bullet 数は `.claude/agents/coder-v4-autonomous-sort.md:85-89` の **正確に 5 件**で、数え違いはありません。ただし compound bullet 内の原子的義務を 5 件と同一視したことが所見 1・2の原因です。置換案の SHA-256 と NFC、結合文字 0 件の主張は再計算と一致しました。

## 総括

- **NO-GO**。
- must-fix は **4 件**、should-fix は 1 件です。
- 「機械執行」に置かれた説明配置契約は実際には未執行です。
- 置換案は内部で処理された例外送出の禁止を落としています。
- residual 5 項を auditor が拒否する実行契約は結線されていません。
- caller 閉包には S6 と freeze 再実体化群が欠けていますが、live coder build bypass は未発見です。
- P3 は過去の観測にすぎず、親代行には D95 上の新しいユーザー裁定が必要です。
- pytest・checker はすべて未実走、worktree 変更なしです。