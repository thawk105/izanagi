## MF-1 — `_gate_check_core` の token-only 化は採るべきでない

**所見:** 変更後に新たに拒否される入力は存在するが、実在する安定した production CLI 入力ではない。拒否集合は次の二つである。

- private core を直接呼び、正常な v2 `freeze_path` を self-load させる入力。現行は `:459` で `VerifiedFreeze`、`:496` で raw `RatifiedFreeze` を取得し、`:503` の SHA 一致だけで先へ進める。
- `verified=<v2>` と SHA が一致する raw `ratified=` を `_gate_check_core` へ直接注入する入力。現行は `:490-503` で authority として使える。

いずれも、床値選択規則を満たす raw freeze まで「`LaunchValidatedFreeze` token がない」という形式だけで拒否する。逆に、選択規則を破る raw freeze も現行 private core なら通り得るため、変更は一部の仮想呼出しには正しさを強めるが、除外集合全体については単なる fail-closed 拡大である。`LaunchValidatedFreeze` は選択規則だけでなく current contract・closure・live scan まで含む型であることも、[D1370:43664](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/docs/decisions.md:43664) の「狭い選択 API と full launch validation を分ける」理由と一致する。

**根拠: production caller の全閉包**

- CLI `main` の唯一の `gate_check` 呼出しは [s8b_oracle_driver.py:2055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:2055)。
- `gate_check` から core への全呼出しは `:619`, `:632`, `:646`, `:655`, `:677`。
  - 通常 v2 は `:644` で raw freeze を取得し、`:664` で `launch_validate`、`:677-683` で exact token を渡す。
  - v1 は `:632`。
  - active 解決失敗は `:646/:655` から既に refusal。
  - 問題とされたものは初回 loader 失敗時の `:619` だけ。
- `run_block` は [同:1335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:1335) → `launch_validate:1351` → `_gate_check_validated:1407` → core `:702` で、常に exact token を渡す。
- production の他 module から `gate_check`、`_gate_check_core`、`_gate_check_validated` を呼ぶ箇所は静的走査上 0 件。

CLI で `:615` の初回 load が失敗し `:459` の直後の再読込だけ成功するには、二読の間で path の可読性または bytes が変化する必要がある。loader は同じ path を read・strict parseする決定的処理であり（[s8b_freeze_io.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_freeze_io.py:41)）、両読の間に driver 自身の更新処理はない。固定された実入力で成立せず、外部競合・一過性 I/O・mock が必要な状態遷移である。

**根拠: 既存テスト caller と壊れる node**

静的には壊れる既存 node は **0 件**。

- core の直接 caller は [test_gate_check_core_rejects_reverified_freeze_token:2462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_oracle_driver.py:2462) の 1 nodeだけで、現在も不正 token の拒否を期待している。
- v2 public gate caller は [test_spec_matching_gate…:2654](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_oracle_driver.py:2654)、[test_gate_check_rebinds…:2726](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_oracle_driver.py:2726)、[test_v2_standalone…:5436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_oracle_driver.py:5436)。すべて `launch_validate` を通る。`:5496` の `ratified=` 注入も `launch_validate` に渡されるため維持される。
- v1または既拒否経路の caller は `test_t080_stub_free_e2e_exact_consumers_and_nodeids_b5:908`（埋込み call `:1219`）、`test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5:1349`、`test_real_freeze_gate_lists_floor_and_budget_null:3074`、`test_t080_gate_hermetic_primary_states_exact:3142`、`test_tampered_freeze_fails_source_verification:4259`、`test_never_issued_generator_tamper_reaches_public_driver_gate_g7:4375`。
- 他 test module の唯一の caller は [test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal:300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_binding_driftguards.py:300) で、もともと refusal を期待する。
- `run_block` 経由の全 test は production の一つの token 済み choke point に畳まれる。[test_private_validated_gate_has_only_run_block_as_production_caller:5503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_oracle_driver.py:5503) もこの閉包を固定している。

本段では pytest は実走しておらず、以上は現行 source と AST による静的判定である。段2が提案する「初回失敗→二回目成功」の新規 node は、既存入力の回帰を固定するものではなく、mock で仮想状態遷移を新設するものになる。

**成果物への影響:** `s8b_oracle_driver.py` と driver test の変更案をプランから外し、fallback は「構造上の callsite だが安定した production 入力で発火不能」と記録する。

**区分:** **must-fix（MF-1）**

## MF-2 — (b) の「3群」は stale だが、再監査の意図まで stale と断定してはいけない

**所見:** 「load-only consumer 3群」という数は stale である。一方、1345 が (a) 着地後に母集合を再監査対象として再開した、と読む余地はある。ただし、それでも現在の未強制 production consumer が3群になる根拠はない。

**根拠（逐語比較）**

- 1202 の (b) は「`load-only consumer 3群` という母集合の再確定」であり、まだ過少計上の疑いを述べる段階だった。[1202:354](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/docs/archive/worklog-phase3-0902-1202.md:354)
- 1236 は「(b) の母集合は4群」と明記し、report / judge / verdict / C06 を列挙した。[1236:333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/docs/archive/worklog-phase3-0903-1236.md:333)
- 1345 は (a) の3 CLIを実装済みにした一方、carry では再び旧表現「3群」を使った。[1345:311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/docs/archive/worklog-phase3-0908-1345-1347.md:311)
- (a) 着地後、1236 の4群中3群は [report:2548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_report.py:2548)、[judge:750](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_judge.py:750)、[verdict:829](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_verdict.py:829) で強制済みになった。残る実在未強制 consumer は C06 だけである。

letter の意味もずれている。特に (c) は、1202では旧 public builder/writer、1236ではその private 化を完了、1345では同じ letter に別物の `verify_manifest` library chain を載せ直している。(d) は同じ意味のまま、1345側に再開を裏付ける新事実がない。

したがって判定は、「3群という具体数は stale」が real、「1345が母集合の再監査自体を意図していない」までは未証明、である。

**成果物への影響:** carry は「(b) を再監査した結果、実在未強制は C06 1群。`:496` は仮想遷移として別記」に訂正し、letter の意味の変化も注記する。

**区分:** **must-fix（MF-2）**

## (c) — 1236で閉じた狭い課題は real、1345の library 到達は production では refuted

**所見:** 元の (c)「公開 builder/writer の迂回口」は現在も閉じている。残る `verify_manifest` 非対称から library 関数を手動連結する経路はコード上構成可能だが、repo 内 production 到達経路は存在しない。

**根拠:**

- 現定義は `_build_manifest` / `_build_manifest_from_ratified` という private 名だけ。[s8b_oracle_manifest.py:818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_manifest.py:818)
- 旧3名を attribute 解決不能とする負例も現存する。[test_s8b_oracle_manifest.py:1248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_oracle_manifest.py:1248)
- `verify_manifest` の production direct caller の exact set は driver / report / judge / verdict の4 fileで固定されている。[test_s8b_oracle_manifest_contract.py:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_oracle_manifest_contract.py:31)、equality assertion は [同:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_oracle_manifest_contract.py:99)。
- 実 callsite は driver `:543/:1397`、report `:2553`、judge `:753`、verdict `:832`。動的 `getattr` / import による production caller も静的検索ではなかった。
- official artifact continuation は3 CLIだけで、いずれも先に選択強制する。
  - report: `assert:2548` → `verify_manifest:2553` → `build_observations:2561` → write `:2565`
  - judge: `assert:750` → `verify_manifest:753` → `judge_oracle:761`
  - verdict: `assert:829` → `verify_manifest:832` → `verify_oracle_verdict:857` → `judge_combined:864` → write `:867`
- driver は通常 v2 なら `launch_validate:664/:1351` を先に通す。

`build_observations` が token を要求せず、`reverified_freeze` も optional なのは [s8b_oracle_report.py:2312](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_report.py:2312) のとおりであり、外部 library caller に対する非対称自体は実在する。しかし repo 内 production continuation がないため、今回の must-fix にはできない。

**実測と読解の区別:** 本段の実走は0。caller set は現行 source/AST の静的確認、1236・1345の passed/mutation 数値は過去 worklog の記録であり本段で再実測していない。

**成果物への影響:** original (c) は完了維持。library 非対称は「repo 内 production 到達なしの閉じていない範囲」とだけ記録し、gateを追加しない。

**区分:** **nit**

## (d) — genuine 正負4 node による閉鎖は real

**所見:** 4 node は D1504 が却下した「loader と選択 assert の両方を stub」ではない。実 loader、実 admission 導出、実 launch/consumer calleeを通る。

**根拠:**

- helper は実 admission の `reserve`、`finalize`、`inspect` を [test_s8b_ratified_verify.py:858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_ratified_verify.py:858) から呼び、実 `result.json` / manifest / journal / ledgerを設置する。
- 4 node は [同:1031](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_ratified_verify.py:1031)、`:1046`、`:1060`、`:1075`。各 node は `load_ratified_freeze` で取り直し、`launch_validate` または `assert_g1_floor_selection_identity` を直接呼ぶ。4関数内に monkeypatch はない。
- 対照的に旧 stub 版は `:1002-1006` / `:1019-1023` で `_derive_floor_selection_eligibility` を明示的に monkeypatchしており、genuine 4 nodeとは明確に別物。
- 実導出は [s8b_holdout_freeze.py:1851](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_holdout_freeze.py:1851) → `_derive_floor_selection_eligibility:1867` → admission inspection `:1903`。launch側は [s8b_ratified_freeze.py:3322](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_ratified_freeze.py:3322)、狭い consumer API側は `:3657` から同じ選択本体へ入る。
- D1504自身も genuine 正負例を機構証明とし、両方stubを却下している。[D1504:46861](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/docs/decisions.md:46861)

**成果物への影響:** (d) は完了維持。テスト追加・作り直しを行わない。

**区分:** **nit**

## D1371 — P1-1 の C06 帰属は real、再評価条件は未成立

**所見:** D1371 の不実装対象は C06だけではなく3件だが、P1-1が参照する C06選択強制は明確にその第1項の射程内である。C05着地による再評価条件も、現 consumerでは満たされていない。

**根拠:**

D1371が実装しないとした対象は [decisions.md:43686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/docs/decisions.md:43686) の次の3件。

1. s8c C06予算経路への選択強制。C05実装着地時に再評価。
2. 起動証明書の実時間性。
3. s8c production final claim配線。

現行 C06 production 経路は [p3_autonomous_workload_trial.py:4957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/p3_autonomous_workload_trial.py:4957) で raw `RatifiedFreeze` を読み、`:4958` から budget inputを準備する。しかし schedule authority resolver は [同:2074](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/p3_autonomous_workload_trial.py:2074) で `root` を捨て、無条件に `AutonomousTrialError` を送出する。`reserve_all_cells:4964` には到達しない。

`s8c_schedule.py` という leaf moduleは存在するが、C06の `_load_s8c_schedule_authority` へ結線されていない。したがって D1371 が定めた「C05実装が着地した時点」は、少なくともこの production consumerの意味では未成立である。選択 gateを追加しても C05 errorとの順序だけが変わり、成果物・受理集合は変わらないという D1371 の前提が現在も成立する。

**成果物への影響:** C06は「実在 callsiteだがD1371により不実装・再評価未発火」と分類し、コード変更しない。

**区分:** **nit**

## 総括

プランの `_gate_check_core` token-only 化は採るべきでない。安定した production CLI 入力の穴ではなく、private直呼びまたは「初回load失敗→即時再読成功」という外部状態遷移だけを閉じる仮想リスク対応である。

4は **real（3群という数は stale。ただし再監査意図はあり得る）**、5は **real（original (c) は閉鎖）／production library 到達は refuted**、6は **real**、7は **real（D1371射程内、C05再評価未発火）**。

must-fix は **2件**。MF-1はコード変更案の撤回、MF-2は母集合を「実在未強制 C06 1群＋仮想 fallback別記」へ訂正すること。