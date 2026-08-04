判定は不受理です。must-fix 8 件、親 brief の refuted 候補 1 件を構成しました。必読入力は全件読了済みです。`pegasus02` 上の段3 read-only 検査なので、pytest・checker は実走していません。型タグは [docs/failures.md:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/docs/failures.md:17) に従います。

### B-1 — S8A 直接 materializer 2 経路が未被覆 `[手順漏れ]`

- 対象: [plan:132-146](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:132)、[plan:258](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:258)、[brief:17](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s1-brief.md:17)
- 根拠: 閉じた registry は `s8a_trigger_coverage._build` を admitted gateway として明記していますが、プランの materializer 表にありません。[materializer_admission.py:31-51](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/materializer_admission.py:31)。同 `_build` は trigger patch 適用後の source evidence と旧 admission を作り、`buildcache` を経ず直接 CMake を起動します。[s8a_trigger_coverage.py:106-162](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8a_trigger_coverage.py:106)。`s8a_trigger_freq` も同じ `_build` を再利用します。[s8a_trigger_freq.py:143-149](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8a_trigger_freq.py:143)
- 成果物影響 (DW-G05): SourceEvidence v2 導入後は characterization build が全停止するか、互換逃げを置けば文法外 trigger source が直接 materialize されます。
- 提案: **must-fix**。`s8a_trigger_coverage.py`、`s8a_trigger_freq.py`、registry と対応テストを scope 内へ追加し、実 source 検査後の receipt を direct admission と出力 provenance に束縛すること。

### B-2 — 共通 artifact reader が旧 trigger WAL を再検査せず admitted 扱いする `[恒真ゲート] [手順漏れ]`

- 対象: [plan:173-184](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:173)、[brief:51-52](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s1-brief.md:51)
- 根拠: `CampaignAdmissionDecision.admitted` は `legacy-unclassified` 以外を真とします。[artifact_admission.py:94-96](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/artifact_admission.py:94)。receiptless pre-policy branch は git snapshot の byte 一致だけで `historical-not-reclassified` を返し、grammar・receipt topology を検査しません。[artifact_admission.py:497-529](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/artifact_admission.py:497)。WAL topology 検査は後続の post-policy branch だけです。[artifact_admission.py:531-541](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/artifact_admission.py:531)。その view は Layer3、critic、replay、S8A report 等へ供給されます。[layer3_report.py:46-50](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/layer3_report.py:46)、[replay.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/replay.py:107)、[s8a_trigger_sweep.py:524-528](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8a_trigger_sweep.py:524)
- 成果物影響 (DW-G05): gate 導入前の trigger campaign が「admitted」のまま Layer3・critic・replay に入り、新 gate 済み材料として再包装されます。
- 提案: **must-fix**。`artifact_admission.py` を所有面へ追加し、旧 trigger campaign は source 再検査済み migration receipt がある場合だけ view を発行すること。単に `wal.py` を強化してもこの分岐には届きません。

### B-3 — S8B binding の consumer schema 閉包が不足 `[手順漏れ] [ドリフト]`

- 対象: [plan:186-203](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:186)、[plan:291-293](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:291)、[plan:311](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:311)
- 根拠: plan は trigger binding に 2 field を足しますが、次の exact-key consumer が scope 外です。
  - Oracle manifest: [_BINDING_KEYS と再hash:54-57,480-509](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8b_oracle_manifest.py:54)
  - Oracle report: [exact schema と再hash:866-901](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8b_oracle_report.py:866)
  - Ratified freeze: [portable binding keyset:181-188](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8b_ratified_freeze.py:181)、[exact検査:1668-1688](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8b_ratified_freeze.py:1668)
  - Oracle driver 自身も exact 5 fields ですが、これは plan 所有に含まれています。[s8b_oracle_driver.py:64-67](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8b_oracle_driver.py:64)
- 成果物影響 (DW-G05): fresh trigger binding は manifest 検証段で拒否され、legacy branch まで届きません。迂回して keyset を緩めれば未検査 binding が report/freeze に入ります。
- 提案: **must-fix**。manifest・report・ratified-freeze と全対応テストを scope 内に入れ、trigger/non-trigger 二形態と legacy 再検査を同じ versioned schema で閉じること。

### B-4 — P3 の「同じ materialization recipe で再構成」が実装可能な形に落ちていない `[手順漏れ]`

- 対象: [plan:154-160](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:154)、[plan:182-184](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:182)、[brief:51-52](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s1-brief.md:51)
- 根拠: 旧 SourceEvidence は絶対 `source_root` と digest 群だけで、source bytes／implementation／再構成 recipe を保持しません。[source_digest.py:108-160](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/source_digest.py:108)。trigger loop の provenance も `proposal_path`、diff digest、variant、outcome だけです。[p3_s4_loop_trigger_gating.py:655-660](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/p3_s4_loop_trigger_gating.py:655)。generic loop は migration 前に WAL terminal を replay/skip しますが producer recipe を持ちません。[loop.py:136-165](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/loop.py:136)
- 成果物影響 (DW-G05): transient worktree や proposal file が消えた既存 trial は一括 reject され比較母集団が変わる一方、誤った recipe 再構成は別 implementation を旧測定へ結び付けます。
- 提案: **must-fix**。producer 別の migration registry、必要入力、旧→新 record 射影、再構成不能時の分類を file:line まで定めること。再構成不能な既存 artifact の扱いは **scope 外裁定候補**として件数・材料影響を添えて返すこと。

### B-5 — 「pin は3本のみ」は現物に反する `[恒真ゲート] [手順漏れ]`

- 対象: [brief:21-24](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s1-brief.md:21)、[plan:348-350](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:348)
- 根拠:
  - `known_axes_freeze.json` は generator 自身に加え、`genome.py`、backoff、sort、外部 Options/CMakeLists、phase doc 等を pin しています。[known_axes_freeze.json:5-7](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/output/s1-freeze/known_axes_freeze.json:5)、[:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/output/s1-freeze/known_axes_freeze.json:107)、[:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/output/s1-freeze/known_axes_freeze.json:152)、[:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/output/s1-freeze/known_axes_freeze.json:200)、[:220](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/output/s1-freeze/known_axes_freeze.json:220)
  - verifier は `sources` を再帰列挙して全件 live SHA を照合します。[s1_known_axes_freeze.py:682-742](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s1_known_axes_freeze.py:682)
  - measurement freeze はさらに 3 implementation hash を持ちます。[s1_measurement_freeze.py:252-258](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s1_measurement_freeze.py:252)
  - `FROZEN_MANIFEST` は 23 artifact を固定します。[test_frozen_artifacts.py:38-85](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/tests/test_frozen_artifacts.py:38)
  - plan が変える `s1_direct_comparison.py` は S8B oracle の generator SHA pin 対象で、reader は live bytes と再照合します。[s8b_oracle_manifest.py:44-52](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8b_oracle_manifest.py:44)、[:411-450](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8b_oracle_manifest.py:411)
- 成果物影響 (DW-G05): no-touch 3 SHA だけ緑でも、既存 oracle manifest や凍結 proof chain が planned producer change で拒否され得ます。F30 と同型です。[failures.md:485](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/docs/failures.md:485)
- 提案: **must-fix**。変更予定 path→全 pin consumer の inventory を作り、「更新する pin／不変を要求する pin／legacy migration」を分離すること。[T-442] は live-freeze 回帰テストの所有であり、この pin inventory を送る理由にはなりません。

### B-6 — role 変更が brief に記録された承認範囲を超える `[ドリフト]`

- 対象: [brief:15](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s1-brief.md:15)、[plan:207-217](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:207)
- 根拠: brief が明記する承認は「数値 literal を入れない契約への変更」です。plan はそれに加えて bare `!`、alternative token、ternary、comma、member access、再代入などを producer prose で新たに禁止し、defense-chain 記述も変更します。現行 role は「enum + compile-time constants」「1行・副作用なし」までです。[role md:82-115](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/.claude/agents/coder-v4-autonomous-trigger-gating.md:82)。D51 が許すのは裸 member 名であり、member 別説明や順位ではありません。[decisions.md:1957-1962](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/docs/decisions.md:1957)
- 成果物影響 (DW-G05): producer の提案分布と候補成功率が数値禁止以外の理由でも変わり、旧 role と同じ synthesis 試行として比較できなくなります。
- 提案: **must-fix**。role diff を既承認部分に限定するか、文法 v1 全体への producer 契約縮小を変更項目ごとに明示して再承認を得ること。裸名列挙や plan の defense-chain 文言から勝ち筋リーク自体は構成できませんでした。

### B-7 — B-6 report boundary は v4 schema と非trigger形が未定義 `[恒真ゲート] [ドリフト]`

- 対象: [plan:235-249](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:235)、[plan:295](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:295)
- 根拠: 現行 generator は v3 と単一 legacy v2 だけを扱います。[layer3_report.py:39-40](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/layer3_report.py:39)、[:190-200](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/layer3_report.py:190)。schema は `additionalProperties:false` かつ required 全体が固定です。[layer3_schema.json:5-9](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/layer3_schema.json:5)。plan は trigger の固定値しか定めず、v4 の非trigger値、条件付き required、v2/v3 reader の選択規則を定めていません。既存の別テストも v3 を pin していますが test list から漏れています。[test_t126_qualification_artifacts.py:322-326](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/tests/test_t126_qualification_artifacts.py:322)
- 成果物影響 (DW-G05): field を全体 required にすれば非trigger report が壊れ、optional にすれば trigger report が boundary 欠落のまま schema green になります。
- 提案: **must-fix**。v4 の trigger/non-trigger 両形、必須条件、historical v2/v3 reader、`test_t126_qualification_artifacts.py` の追随を明記し、`claim_boundaries` 削除変異が赤になるテストを置くこと。

### B-8 — A→B の依存 patch handoff が段5手順から欠落 `[手順漏れ]`

- 対象: [plan:302-316](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:302)、[brief:41-45](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s1-brief.md:41)
- 根拠: A/B の所有ファイル自体は素集合ですが、B は A の新 API を import します。plan は「A→Aテスト→B」としか書かず、別 worktree の B へ A の成果をどう渡すかがありません。DW-S05-A は、依存単位を先に完了した後、所有 path 限定の staged patch を次単位へ展開することを要求します。[workers.md:19-24](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/docs/dev-wave/workers.md:19)
- 成果物影響 (DW-G05): B worktree で import/test が成立しないか、B が A 所有ファイルを再作成・修正して author provenance と所有分離を壊します。
- 提案: **must-fix**。A の2 pathだけから ownership-limited patch を作り B worktreeへ適用する具体手順を段5へ追加すること。共有 fixture・conftest・import cycleは検査したが構成できませんでした。

### B-9 — P2 の「既存 issued flag 様式」は現物と違う `[ドリフト]`

- 対象: [brief:49-50](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s1-brief.md:49)、[plan:63-107](/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/s2-plan.md:63)
- 根拠: 既存 `GeneratorReceipt`／`ReviewReceipt` は private `_SEAL` と canonical body を使い、永続 body に `issued` field はありません。[build_admission.py:181-210](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/build_admission.py:181)、[_GENERATOR_KEYS等:339-349](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/build_admission.py:339)。同モジュールは in-process issuer の認証ではないとも明記しています。[build_admission.py:2-13](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/build_admission.py:2)
- 成果物影響 (DW-G05): 永続 `"issued":true` を権威として扱う実装へドリフトすると、raw body の再生が runtime 発行を代替します。
- 提案: **refuted 候補**は P2 の「既存 issued-flag 様式」という一般化です。plan:107 の exact runtime token 要求を維持し、`{"issued":true,...}` の raw mapping が代替不能な境界テストを置けば、これ単独は追加 must-fix に数えません。混乱を避けるなら永続 `issued` field 自体を削除してください。

## must-fix 8件の closure 検収

| README §5 | Bレンズ判定 |
|---|---|
| A2-1 | plan 上は閉じる。レンズAの recognizer 正しさ判定は行っていない |
| A2-5 | plan 上は閉じる |
| A2-8 | plan 上は閉じる |
| A2-15 / B-1 | **未閉鎖** — 本回答 B-1、B-2 |
| B-2 | **未閉鎖** — B-2、B-3、B-4、B-5 |
| B-4 | 数値禁止はあるが role 承認射程が **partial** — B-6 |
| B-6 | **未閉鎖** — B-7 |
| B-10 | SHA 更新単位は整合。role 承認問題だけ B-6 に残る |

検査したが構成できなかった面:

- P1 の二つの named field は、現物上どちらも hole へ逐語で渡る同一概念です。[p3_s4_loop_trigger_gating.py:102-107](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/p3_s4_loop_trigger_gating.py:102)、[s1_verify_extime_calibration.py:329-338](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s1_verify_extime_calibration.py:329)。ただし P1 は B-1 の無名/direct 経路を列挙しません。
- D51 の旧 blacklist 併存、D96 の新 D＋境界テスト手続、D127 の materializer 寄せという方向自体には衝突を構成できませんでした。D127 の実閉包不足は B-1/B-2 です。
- role source→manifest→review ledger→adapter の SHA 更新集合は機械的には正しいです。[review_ledger.py:15-47](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/codex_roles/review_ledger.py:15)、[check_codex_agents.py:216-263](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/tools/check_codex_agents.py:216)。ただし差分後の実走なしに「緑」とは認定しません。
- [T-441]/[T-410] への実装滲出は構成できませんでした。generic quarantine の既存 backoff/sort positive controlsもあります。[test_p3_s4_loop.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/tests/test_p3_s4_loop.py:108)、[test_p3_s4_loop_sort.py:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/tests/test_p3_s4_loop_sort.py:91)
- [T-442] へ送るのは checked-in freeze 対 live-source 回帰テストだけ、という境界は妥当です。B-5 の pin inventory は本 wave の受入責務です。

## 総括

- must-fix は **8件**。
- 最重要所見は B-2: 共通 artifact admission が旧 trigger WAL を未再検査のまま admitted view にすること。
- consumer 閉包は S8A direct build、artifact reader、S8B exact-key consumer の三層で不足。
- 親は既存 trigger campaign 全件について classification、source bytes/recipe の生存、移行可能件数を実測すべき。
- S8B manifest・resume・ratified artifact の実在 keysetと `s1_direct_comparison.py` generator pin を棚卸しすべき。
- role は数値禁止を超える全 producer 文言差分について承認範囲を再確認すべき。
- 計算ノードで関連＋全テスト、変異 matrix、cross-axis positive controlsを実走すること。
- 差分後に `check_codex_agents.py`、`check_docs.py`、全 pin/no-touch hash、commit 後 provenance を確認すること。