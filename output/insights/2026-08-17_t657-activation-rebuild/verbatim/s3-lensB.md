## 調査境界

必読の brief と段 2 plan は読めた。`orchestrator/**/*.py`、`tools/**/*.py`、関連 JSON / shell、全 213 test Python file、worklog、phase、decisions、spool、旧 branch の成果物を静的に探索した。`s8b_floor_campaign.py` は定数、resolver、preflight、reseal 周辺だけを対象にし、全読はしていない。

pytest、受入全走、mutation、provenance checker は実行していない。以下は緑判定ではなく、静的所見である。

### 1. [real] 派生 runtime binding が fallout 一覧から漏れている

根拠: [`silo_ladder_rung1.py:274`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/silo_ladder_rung1.py:274>) は activation record の全 JSON を `runtime_modules` に含め、[`silo_ladder_rung1.py:4475`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/silo_ladder_rung1.py:4475>) と [`silo_ladder_rung1.py:4599`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/silo_ladder_rung1.py:4599>) が binding と digest を成果物へ入れる。検証側は [`silo_ladder_rung1.py:3562`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/silo_ladder_rung1.py:3562>) で完全一致を要求する。

test 側の期待集合は [`test_silo_ladder_rung1_driver.py:937`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_silo_ladder_rung1_driver.py:937>) で動的 glob なので、テスト literal の置換は不要だが、現行 evidence の再生成は必要である。

無視時の破壊: `binding.runtime_modules` と `runtime_modules_sha256` が旧値のまま残り、`current runtime module binding mismatch` で現行 Silo evidence が拒否される。

### 2. [real] T-419 実行成果物の calibration pin が未列挙

根拠: [`t419_probe_causality.py:3395`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/tools/pegasus/probes/t419_probe_causality.py:3395>) は常に現行 `lookup("pegasus")` を使い、[`t419_probe_causality.py:3407`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/tools/pegasus/probes/t419_probe_causality.py:3407>) から submission の期待 hash と実 bytes を比較する。実行結果の再検証でも [`t419_probe_causality.py:3730`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/tools/pegasus/probes/t419_probe_causality.py:3730>) が submission pin を再利用する。

段 2 の [`s2-plan.md:112`](</work/1/SFC/tanab/dev-wave-jobs/t657-activation-rebuild/artifacts/s2-plan.md:112>) は dirty-scope test の record 1/2 対応だけで、既存 submission の g1 calibration pin を historical lane へ隔離する条件を成果物一覧に含めていない。

無視時の破壊: g1 pin を持つ T-419 submission は g2 activation 後に `pin_verified=false`、`matched=false` となる。

### 3. [refuted] alias や旧 hash を一括置換すべきという読み

根拠: [`pegasus_floor_scoping.py:25`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/pegasus_floor_scoping.py:25>) の `lookup` は関数 alias であり、[`pegasus_floor_scoping.py:78`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/pegasus_floor_scoping.py:78>) で現行契約から calibration path を導出する。固定 g1 pin ではない。

一方、[`test_s1_direct_comparison.py:124`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_s1_direct_comparison.py:124>) や [`test_s1_report.py:52`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_s1_report.py:52>) の旧 pin は歴史成果物の pin である。

無視時の破壊: 旧 lane の pin を g2 へ置換すると、historical replay の期待 hash と過去成果物の束縛が壊れる。

### 4. [refuted] 「旧 A/B/C の三択は全て失効した」

根拠: D444 は変更可能 field を `contract_sha256` と `ccbench_pin` に限定し、既存 bytes の上書きを禁じる ([`decisions.md:18634`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/decisions.md:18634>)、[`decisions.md:18640`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/decisions.md:18640>)。履歴不変条件、freeze hold、human seal、23 key は変更しない ([`decisions.md:18666`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/decisions.md:18666>)。supersede も Q2 の binding retarget に限定され、Q3 は残る ([`decisions.md:18703`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/decisions.md:18703>)。

したがって B は依然として不許可だが、A は未失効、C も自動承認されたわけではないが将来の別設計として残る。

無視時の破壊: A/C を不要と誤認すると再設計の選択肢を失い、B を採ると `history-mutated` の拒否層を壊す。

### 5. [real] 21 件の hold 対象に履歴不変条件は入っていない

根拠: [`freeze_verification_hold.py:16`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/freeze_verification_hold.py:16>) から [`freeze_verification_hold.py:39`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/freeze_verification_hold.py:39>) の 21 ID に `history-mutated` や `_immutable_introductions` はない。

ただしこれは免除ではない。検査の条件は [`s8b_ratified_freeze.py:475`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_ratified_freeze.py:475>) にあり、実際に [`s8b_ratified_freeze.py:999`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_ratified_freeze.py:999>) で呼ばれる。

無視時の破壊: hold の 21 件だけを見て legacy anchor の書換えを進めると、ratified freeze が `history-mutated` で止まる。

### 6. [refuted] 「追加のみなら履歴不変条件に触れない」は無条件には真でない

根拠: `_immutable_introductions` は全履歴で `absent` または期待 OID だけを許し、別 bytes を一度でも見つけると拒否する ([`s8b_ratified_freeze.py:475`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_ratified_freeze.py:475>)、[`s8b_ratified_freeze.py:482`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_ratified_freeze.py:482>))。

新しい versioned path を absent から一度だけ追加する場合はこの条件と両立する。しかし旧 branch は legacy `floor_protocol.json` を再発行し、実在赤 4 件の `history-mutated` を記録している (`worktree-dev-wave-t657-t660-g2-activation:output/insights/2026-08-09_t657-t660-g2-activation/package.md:86`)。

無視時の破壊: legacy anchor を新 bytes へ置換すると、既存凍結 bytes と履歴 OID が不一致になり、受入全走で少なくとも 4 件の実赤を再現する。

### 7. [real] P1 の「第 4 世代は env contract 世代でない」は正しい

根拠: env contract の Pegasus catalog は g1 と g2 だけ ([`env_contract.py:253`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/env_contract.py:253>)、[`env_contract.py:270`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/env_contract.py:270>))。一方 T-1289 の `GIT_TIMEOUT_CAP_SECONDS` は S8c の generation 条件 ([`s8c_preregistration.py:115`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8c_preregistration.py:115>)) である。

ただし T-1289 自体は消えていない。allocator では別の `[T-1213]` として残っている ([`FOLDED.md:1358`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/spool/FOLDED.md:1358>))。

無視時の破壊: 「第 4 世代」を env g4 と誤解すると未登録 successor を作り `lookup` / activation admission が失敗し、逆に S8c full run の cap 問題を T657 の成果として誤って緑扱いする。

### 8. [refuted] D471 が S1 activation record を直接禁止する、は誤読

根拠: D471 の対象は床値 protocol の発行と resolver であり ([`decisions.md:19572`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/decisions.md:19572>)、[`decisions.md:19589`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/decisions.md:19589>))、S1 activation record は本文の対象になっていない。

無視時の破壊: D471 の直接射程を S1 まで拡張すると、`00000002.json` の準備自体を不必要に禁止し、S1/S2 の順序と所有境界を混同する。

### 9. [real] ただし S1 だけを land するのは構造的に失敗する

根拠: resolver は現行 contract に一致する protocol を exact 1 件要求する ([`s8b_floor_campaign.py:882`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:882>)、[`s8b_floor_campaign.py:896`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:896>))。g2 activation 後に g2 protocol が無ければ count=0 となり、admission は [`certified_writer_admission.py:201`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/certified_writer_admission.py:201>) から拒否される。D471 も配線前の実発行は受理集合を空にすると明記する ([`decisions.md:19631`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/decisions.md:19631>))。

無視時の破壊: S1 だけを main に入れると floor submit、pilot result、report、trial ledger の新規生成が止まる。

### 10. [real] 所有境界はこの wave の外にある

根拠: T-419 の (3) は shell / driver / fixed-path consumer wiring ([`worklog-phase3-0817-611.md:169`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/archive/worklog-phase3-0817-611.md:169>))、T-1255 はその後の実凍結 ([`worklog-phase3-0817-611.md:565`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/archive/worklog-phase3-0817-611.md:565>)) と明記されている。allocator でも consumer wiring は T-1214、reissue は T-1255 に割り当てられている ([`FOLDED.md:1361`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/spool/FOLDED.md:1361>)、[`FOLDED.md:1403`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/spool/FOLDED.md:1403>)。

実際に `worktree-dev-wave-t1255-floor-freeze` は locked worktree として存在する。T-419 の別 worktree は見えないが、所有 allocation は残っている。

無視時の破壊: この wave が consumer wiring や実 protocol 発行を先取りすると、固定 legacy path と versioned resolver が二重 authority になり、count=0/2 または provenance の所有不一致で land が止まる。

### 11. [refuted] D471 後の解除裁定は見つからない

根拠: D472 以降の最新 entry は D479 で ([`decisions.md:19885`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/decisions.md:19885>)、8c allocation evidence の裁定であり、D471 の floor issuance blocker を変更していない。D471 自身も hold と履歴不変条件を維持している ([`decisions.md:19591`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/decisions.md:19591>))。

無視時の破壊: D471 が解除されたと誤認して発行を先行すると、floor resolver が count=2 または count=0 となり、受入成果物が一つも生成されない。

### 12. [real] 旧 branch はコードを捨てても、検出力実証と E2E 分割は捨ててはいけない

根拠: 旧 package は T-660 の mutation 5/5 検出を記録している (`worktree-dev-wave-t657-t660-g2-activation:output/insights/2026-08-09_t657-t660-g2-activation/package.md:12`)。また historical lane と current refusal lane の E2E 分割も記録している (`.../package.md:26`)。現行 archive もこれらを再利用対象として明記する ([`worklog-phase3-0810-356.md:405`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/archive/worklog-phase3-0810-356.md:405>))。

legacy anchor の書換えや旧 test code の丸ごと移植は不安全だが、mutation ledger、期待判定、2 lane の構造は現行 wave の設計資産である。

無視時の破壊: branch ref だけを削除すると、T-660 の検出力値と E2E lane の受入定義が消え、同じ mutation / historical replay を再取得する費用が発生する。

### 13. [refuted] versioned protocol を FROZEN_MANIFEST へ追加する必要はない

根拠: D471 は versioned artifact を 23 key の `FROZEN_MANIFEST` へ登録しないと明記する ([`decisions.md:19585`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/decisions.md:19585>))。

無視時の破壊: manifest を変更すると凍結台帳の key 数と replay bytes が変わり、既存 freeze artifact の hash が一斉に失効する。

### 14. [real] fold / clean tree / provenance が land の構造的関門になる

根拠: 現在の worktree には `?? output/insights/2026-08-17_t657-activation-rebuild/` が残っている。clean-tree gate は clean branch を要求する ([`operations.md:134`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/dev-wave/operations.md:134>))。

記録 fragment を追加する場合、frontmatter と filename の byte 一致、LF、末尾 newline、placeholder 規則が必要 ([`spool/README.md:28`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/spool/README.md:28>)、[`spool/README.md:48`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/spool/README.md:48>)、[`spool/README.md:53`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/spool/README.md:53>)。worklog は `## 本文` と `## 次の一手差分` の 2 H2 が必須 ([`spool/worklog/README.md:5`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/spool/worklog/README.md:5>))。実装 commit には Codex author trailer が必要 ([`ai-provenance.md:48`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/ai-provenance.md:48>))。

docs/dev-wave の予算検査は [`check_docs.py:4175`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/tools/check_docs.py:4175>) と provenance family の [`check_docs.py:4607`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/tools/check_docs.py:4607>) にある。今回はその検査を実行していないため、予算緑とは報告しない。

無視時の破壊: untracked artifact、壊れた spool、欠落 trailer のいずれかが残ると、fold または clean-tree / provenance land gate が止まり、コードが正しくても `landed` にならない。

## 総括

最も見落とされやすいのは、`00000002.json` の追加が `runtime_modules_sha256` まで変える派生 binding である。  
D471 は S1 を直接禁止しないが、S1 単独 land は floor resolver count=0 で成果物を生成できない。  
旧 branch はコードでなく、T-660 の検出力と historical/current E2E 分割を保存してから破棄すべきである。