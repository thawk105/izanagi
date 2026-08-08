結論は **NO-GO** です。必読 5 文書はすべて読めました。本番コードの編集・テスト実行はしていません。

### A-01 — exact 2-path への一般化は DW-G03 を満たさず、実行意味論を束縛しない

- **区分:** real
- **根拠:** 親 brief は「silo / qualification の独立 2 実装」を DW-G03 の根拠にしていますが、DW-G03 が要求するのは「異なる producer/consumer で再現した同型欠陥 2 件」です。[s1-brief.md:22](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s1-brief.md:22)、[s1-brief.md:35](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s1-brief.md:35)、[core.md:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/docs/dev-wave/core.md:55)
- **反例:** silo は activation JSON、execution guard、calibrator、全 verifier 等を含む広い集合を束縛します。[silo_ladder_rung1.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/silo_ladder_rung1.py:254) qualification も pipeline、build admission、guard、site policy 等を含む広い exact set です。[contract.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/qualification/contract.py:38) これを R-A1 の env loader 2 本だけへ縮約する根拠はありません。[s2-plan.md:48](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:48)、[s2-plan.md:63](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:63)
- **未検証 bytes:** authority を解釈する `execution_guard.py`、COMMIT を書く `pipeline.py`、admission/WAL validator 自身が dirty でも、lock は full `source_commit` に由来したように見えます。
- **成果物影響:** dirty な guard/pipeline semantics が、clean な loader 2 本と full commit を名乗る certified COMMIT・レポート・台帳を生成できる。
- **判定:** **must-fix**

### A-02 — live file 検査は、実際にロード済みの Python bytes を証明しない

- **区分:** real（静的反例）
- **根拠:** R-A1 は capture 時点の live file と Git blob を比較するだけです。[s2-plan.md:63](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:63) しかし loader/guard は campaign 起動時に既に import 済みです。[loop.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/loop.py:20)、[execution_guard.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/execution_guard.py:22) 現行 preflight も `module.__file__` を後から再読しているだけです。[certified_writer_preflight.py:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/certified_writer_preflight.py:85)
- **反例:** A を import → checkout/file replacement で B に変更 → B の commit/blob と live file を照合 → メモリ上では A を実行、という順序で gate が通ります。同一プロセス verifier 改竄を仮定しなくても成立します。
- **成果物影響:** lock は loader B を証明する一方、certified 選択は loader A の意味論で生成され、proof chain が異なる bytes を結ぶ。
- **判定:** **must-fix**

### A-03 — 全案で、提案 gate を実際に発火させる artifact / measurement が不足している

- **区分:** real
- **根拠:** DW-G04 は既存 artifact path または measurement ID を brief に要求します。[core.md:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/docs/dev-wave/core.md:60)
- **案別監査:**
  - **R-A1 / R-A2:** 引用テストは floor preflight で `certified_writer_admission.py` を変異させるものです。[test_campaign.py:2696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/tests/test_campaign.py:2696)、[certified_writer_fixtures.py:279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/tests/certified_writer_fixtures.py:279) exact 2-path generic gate、layout 前拒否、offline admission のどれも発火しません。プラン自身も generic integration 不在を認めています。[s2-plan.md:233](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:233)
  - **R-A3:** artifact は silo 固有 gate の発火例で、generic 配線の発火例ではありません。[s2-plan.md:235](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:235)
  - **R-A4:** artifact/measurement は「なし」です。[s2-plan.md:236](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:236)
  - **R-B1 / R-B2:** 引用された t530 テストは Linux g1 と Pegasus g1 の別環境比較で、g1→g2、lock、WAL、resume を一切作りません。`t530@9f60471b:orchestrator/tests/test_p3_s4_loop_trigger_gating.py:590-620`
  - **R-B3 / R-B4:** プラン自身が positive rejection / two-root selector measurement 不在を認めています。[s2-plan.md:239](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:239)
- **成果物影響:** dead wiring のままでもテストが緑になり、authority を持たない COMMIT・レポートを「gate 済み」と誤認できる。
- **判定:** **must-fix** — 現状は設計メモに留める条件です。

### A-04 — 「15 caller + direct sink 4 箇所」の閉集合検査は恒真ではない

- **区分:** real
- **根拠:** プランは既存テストを閉集合の根拠にしています。[s2-plan.md:74](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:74) 実際のテストは固定ファイル辞書だけを走査し、`ast.Name(id="run_campaign")` だけを数えます。[test_campaign.py:2513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/tests/test_campaign.py:2513)、[test_campaign.py:2522](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/tests/test_campaign.py:2522) 新規ファイル、alias、attribute call は検出しません。
- **追加穴:** direct sink は全 call でなく、authority keyword を持つ call が `any(...)` で 1 本あれば通ります。[test_campaign.py:2538](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/tests/test_campaign.py:2538)、[test_campaign.py:2553](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/tests/test_campaign.py:2553)
- **成果物影響:** 新規または別形態の writer が authority なし WAL/COMMIT を生成しても、caller inventory は緑のまま残る。
- **判定:** **must-fix**

### A-05 — v2 authority を v1 へ降格して消せる

- **区分:** real（設計上の静的反例）
- **根拠:** v2 の campaign ID は inner `identity` だけを hash し、v1 lane を残します。[s2-plan.md:30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:30)、[s2-plan.md:69](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:69)、[s2-plan.md:72](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:72)
- **反例経路:** v2 lock の外側 envelope を除去して inner identity を現行 v1 lock とし、全 COMMIT から `certified_authority_sha256` を除去する。ID は変わりません。
- **現行受理:** `build_admission` を持つ v1 は post-policy lane へ入り、non-trigger は directory ID 再導出すら行わず受理されます。[artifact_admission.py:487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/artifact_admission.py:487)、[artifact_admission.py:637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/artifact_admission.py:637)、[artifact_admission.py:699](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/artifact_admission.py:699) fixture も v1 post-policy と arbitrary layout の受理を固定しています。[test_artifact_admission.py:700](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/tests/test_artifact_admission.py:700)、[test_artifact_admission.py:729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/tests/test_artifact_admission.py:729)
- **成果物影響:** v2 で証明されるはずの loader/environment authority を削除した WAL・レポートが、同じ campaign ID の v1 として再受理される。
- **判定:** **must-fix** — v1 を許す根拠を trusted frozen ledger 等に限定する anti-downgrade 規則が必要です。

### A-06 — freeze / offline report の raw readers が proof chain を迂回する

- **区分:** real
- **根拠:** `s1_known_axes_freeze` は WAL JSON を直接読み、COMMIT の fitness だけで選びます。[s1_known_axes_freeze.py:221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/s1_known_axes_freeze.py:221)、[s1_known_axes_freeze.py:263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/s1_known_axes_freeze.py:263) `s1_report` と `s8b_oracle_report` も raw `read_records_collected` を使います。[s1_report.py:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/s1_report.py:329)、[s8b_oracle_report.py:1275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/s8b_oracle_report.py:1275)
- **scope 衝突:** t530 裁定はこれらを「既存受理集合を変えるため裁定送り」と明記し、全経路閉鎖を名乗らないとしています。[s4-adjudication.md:39](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s4-adjudication.md:39)、[s4-adjudication.md:101](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s4-adjudication.md:101) 今回の plan は `wal.py` の “read admission” とだけ書き、各 consumer と受理集合裁定を scope に戻していません。[s2-plan.md:71](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:71)
- **成果物影響:** online writer/admission を閉じても、freeze 選択と offline 材料レポートは authority のない COMMIT を certified 材料として採用できる。
- **判定:** **must-fix** — raw readers 一式は明示的な裁定パッケージ候補です。

### A-07 — S8b private lock は v2 authority schema と接続されていない

- **区分:** real
- **根拠:** S8b は `{manifest_sha256, block_id, campaign_id}` だけの private lock を独自に atomic acquire します。[s8b_oracle_driver.py:979](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/s8b_oracle_driver.py:979)、[s8b_oracle_driver.py:989](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/s8b_oracle_driver.py:989) その後、同じ layout に certified pipeline COMMIT を書きます。[s8b_oracle_driver.py:1356](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/s8b_oracle_driver.py:1356)
- **scope 穴:** plan は「S8b sink へ authority 伝播」とだけ書き、private lock の v2 化、validator dispatch、offline report 照合を定義していません。[s2-plan.md:74](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:74) t530 裁定では private lock/report は独立 wave と明記されています。[s4-adjudication.md:41](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s4-adjudication.md:41)
- **成果物影響:** S8b を validator から除外すれば oracle COMMIT が未束縛のまま残り、含めれば既存 private-lock campaign/report の受理が壊れる。
- **判定:** **must-fix** — S8b private lock + offline report を裁定パッケージ化する必要があります。

### A-08 — 分裂条件に「unfinished」は不要で、順序一般化も誤っている

- **区分:** real
- **根拠:** brief と plan は `t530 land ∧ g1 H-bound unfinished ∧ g2 resume` を必要条件としています。[s1-brief.md:27](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s1-brief.md:27)、[s2-plan.md:261](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:261)
- **反例:** t530 loop は current H を config に入れ、旧 root を探索する前に ID/layout を確定します。`t530@9f60471b:orchestrator/campaign/loop.py:130-136`、`t530@9f60471b:orchestrator/campaign/ident.py:52-74,155-203`。したがって g1 campaign が完全 terminal でも、g2 で同じ論理入力を再実行すれば空の g2 root が作られます。
- **順序反例:** `g2 activation → t530 land` でも、land 前の unbound root と land 後の H-bound root が両方 WAL を持てば 2-hit です。Explore B の「分裂なし、断絶のみ」は成果物形として区別できません。[s1-explore-b.md:49](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s1-explore-b.md:49) reader は 2 root で停止します。`t530@9f60471b:orchestrator/campaign/replay.py:89-107`
- **成果物影響:** 完了済み g1 certified set も g2 で再生成・二重化され、report/replay が ambiguous になる。
- **判定:** **must-fix**

### A-09 — authority は global activation state を記録するのに、boundary は H しか比較しない

- **区分:** real
- **根拠:** v2 authority は H に加えて `activation_serial` と `activation_state_sha256` を記録します。[s2-plan.md:42](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:42) 一方、resume 前 gate は pinned H だけを比較します。[s2-plan.md:153](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:153)
- **反例:** activation state hash は全 env の `active_contracts` を覆います。[env_contract_activation.py:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/env_contract_activation.py:130) 実 fixture では Pegasus が g2 へ進む一方、Linux は g1 のままです。`t530@9f60471b:orchestrator/tests/test_env_contract_activation.py:1467-1475`
- **帰結:** Linux resume は H 一致で早期 gate を通るが、full authority digest は不一致です。後段照合なら layout/repair/recovery 後に失敗し、full state を早期比較すれば「対象 env は不変」でも既存 resume 受理集合が狭まります。
- **成果物影響:** 他環境だけの activation 更新で、既存 trial が副作用後に拒否されるか、古い activation state を名乗る COMMITが受理される。
- **判定:** **must-fix**

### A-10 — 推奨順序には authority-free v1 を生成できる無保護期間がある

- **区分:** real
- **根拠:** 推奨順序は g2 activation を R-A1/R-B2 より先に置きます。[s2-plan.md:248](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:248) A を activation 前提へ昇格する条件は「producer 無稼働を機械保証できない場合」ですが、その保証 artifact/gate は示されていません。[s2-plan.md:265](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:265)
- **反例 artifact:** 現行 generic campaign の [campaign.lock:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/campaign.lock:1)、[wal.jsonl:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/runs/wal.jsonl:6)、[layer3_report.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/reports/layer3_report.json:1) は loader authority を持ちません。A の穴は g2 固有ではなく g1 でも発火します。
- **成果物影響:** activation 後から R-A1 land までに生成された v1 COMMIT/report が未束縛のまま固定され、互換 lane に残る。
- **判定:** **must-fix**

### A-11 — R-B3 の lineage pre-scan は並行起動で破れる

- **区分:** 推測（反証可能な静的 race）
- **根拠:** R-B3 は lineage を scan してから current-H layout を作ります。[s2-plan.md:180](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:180) 既存 atomic lock は渡された個別 layout 内だけです。[ident.py:216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/ident.py:216)、[ident.py:245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/ident.py:245)
- **反例 schedule:** g1 を保持した process A と activation 後の g2 process B がともに scan 0-hit → H の異なる別 layout を各々 atomic acquire。lineage 全体の lock/registry がないため、双方成功します。
- **計測不足:** plan 自身も positive rejection measurement 不在を認めています。[s2-plan.md:239](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:239)
- **成果物影響:** fallback gate を実装しても、競合時には g1/g2 の certified WAL・report root が二重生成される。
- **判定:** **must-fix（R-B3 を fallback として残す場合）**

### A-12 — Layer3 の authority source-ref 形式と独立再導出が未定義

- **区分:** real
- **根拠:** plan は authority source ref を追加するとだけ書きます。[s2-plan.md:73](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s2-plan.md:73) 現行 `_report_primary_refs` は WAL/whiteboard だけを再導出し、`source_refs` との exact bijection を要求します。[layer3_report.py:161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/layer3_report.py:161)、[layer3_report.py:178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/layer3_report.py:178) schema も `wal|wb` だけです。[layer3_schema.json:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/layer3_schema.json:21)
- **成果物影響:** authority ref は現行 schema で拒否されるか、meta 内の独立検証されない digest として残る。
- **判定:** **nit** — v4 設計時に canonical ref domain と再導出元を明記すべきです。

所有越境については、R-A1/R-B2 の environment/source authority 自体は T-184 の stage policy matrix や T-189 の served-model/model-routing 所有へ踏み込んでいません。[phase3.md:726](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/docs/phase3.md:726)、[phase3.md:733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/docs/phase3.md:733) また「既存 campaign 30 本、H/build_admission なし」という実測値そのものは反証できませんでした。問題はそこから導いた将来の分裂条件と受理集合の一般化です。

## 総括

**NO-GO — must-fix 11 件、nit 1 件。**

must-fix は以下です。

- A-01: exact 2-path 一般化と未束縛実行意味論
- A-02: loaded-code / live-file TOCTOU
- A-03: 全案の実発火 artifact・measurement 不足
- A-04: 恒真な caller inventory
- A-05: v2→v1 authority 降格
- A-06: raw reader / freeze / offline report の迂回
- A-07: S8b private lock の proof-chain 外残留
- A-08: `unfinished` を含む分裂条件の誤り
- A-09: H と global activation authority の不整合
- A-10: 推奨順序の authority-free write 窓
- A-11: R-B3 lineage scan の並行 race（同案を残す場合）