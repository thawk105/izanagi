結論は **NO-GO** です。dev-wave 段3の規律に従い、実装・pytest は行わず静的解析だけで判定しました。

## 受理集合の差分

`V` を schema/raw/意味検査通過、`Bcur` を calibration 以外の driver/policy/runtime が現行 bytes と一致、`X(gN)` を calibration path/SHA/contract hash と gap attestation が世代 N に整合、と置くと、g2 活性化後は次になります。

- 変更前 current verifier: `V ∩ Bcur ∩ X(g2)`
- プランの historical verifier: `V ∩ Bcur ∩ (X(g1) ∪ X(g2))`
- 新規受理: `V ∩ Bcur ∩ X(g1)`
- 新規拒否: 変更前の受理集合内ではなし
- 実 committed g1 evidence: driver/policy/runtime が historical なので `Bcur` を満たさず、変更後も拒否

つまり新たに受理する代表例は「g1 で生成された文書」ではなく、g1 calibration/attestation と g2 時点の非-calibration binding を混ぜた合成文書です。

## 所見

### A-1 — committed evidence 保全という brief と実際の受理集合が一致しない

- severity: **must-fix**
- 根拠: brief は committed evidence の再検証を目的化していますが、プラン自身が literal file は通らないと認め、テストでは非-calibration binding を現行値へ書き換えます（[s1-brief.md:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s1-brief.md:7)、[s2-plan.md:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s2-plan.md:5)、[s2-plan.md:54](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s2-plan.md:54)）。実成果物は driver/policy/runtime の歴史値を意図的に保持しています（[test_silo_ladder_rung1_evidence.py:1235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1235)、[同:1249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1249)）。一方 producer は calibration と attestation の両方を current から作るため、この混成文書は生成不能です（[silo_ladder_rung1.py:1938](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/silo_ladder_rung1.py:1938)、[同:4438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/silo_ladder_rung1.py:4438)）。
- 成果物影響（1行）: literal committed silo report は引き続き拒否される一方、どの producer 世代も出力しなかった hybrid report が新たに受理され、保全対象と実受理対象の参照が逆転します。
- 修正案: 「literal committed bytes の保全」か「contract 軸だけの current-rebinding 文書の受理」かを brief で裁定すること。前者なら driver/policy/runtime も記録 hash から歴史 blob を検証する独立 lane が必要です。後者なら committed 保全という表現を撤回し、literal file の拒否を明示的に pin した上で hybrid を別種の再検証 envelope として扱ってください。

### A-2 — silo の新しい受理集合を固定するテスト行列が不足している

- severity: **must-fix**
- 根拠: 予定されている新規テストは hybrid g1 正例・never-active 負例・collect tripwire だけです（[s2-plan.md:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s2-plan.md:52)）。実コードでは、別 env は全世代 hash 一意性と `expected_env_tag` で拒否され（[env_contract.py:331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/env_contract.py:331)、[同:696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/env_contract.py:696)）、二重記録 hash は semantic gate と raw gate の双方で束縛されています（[silo_ladder_rung1.py:1707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/silo_ladder_rung1.py:1707)、[同:3458](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/silo_ladder_rung1.py:3458)）。しかし historical routing 後もこれらが CLI 受理条件として残ることを直接固定していません。
- 成果物影響（1行）: refactor で main の検査順や resolver 入力がずれた場合、g2 silo report の誤拒否、Linux hash の Pegasus report への混入、binding/attestation 世代不一致の誤受理が検出されません。
- 修正案: `verify-result` 経由で少なくとも、(1) current g2 producer-shaped 正例、(2) binding g1＋attestation g2 負例、(3) g1 hash＋g2 calibration path/SHA 負例、(4) Linux g1 hash＋expected Pegasus 負例、(5) never-active 負例を追加してください。producer/collect が g1 を拒否し g2 を受理する正負対も必要です。

### A-3 — T-660 の単独変異行列が片側しか登録されていない

- severity: **must-fix**
- 根拠: state hash は serial を含む record 全体から算出され（[env_contract_activation.py:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/env_contract_activation.py:130)）、terminal serial と state hash が順に検査されます（[同:406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/env_contract_activation.py:406)）。プランは serial-only と対変異だけを登録しています（[s2-plan.md:163](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s2-plan.md:163)）。指定された production tail-deletion node だけを走らせる場合、**state-hash-only 無効化も serial gate に mask されて SURVIVED** が正解です。全 activation suite なら、同一 serial・異なる state hash の既存 node がそれを KILLED にします（[test_env_contract_activation.py:483](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:483)）。
- 成果物影響（1行）: mutation ledger は serial 側だけの mask を示して対称性を証明せず、対変異 KILLED を「単一理由の実効 head pin」と過大評価します。
- 修正案: tail-deletion node に対し `serial-only=SURVIVED`、`state-hash-only=SURVIVED`、`pair=KILLED` の3件を事前登録してください。state-hash の独立検出力は別走で `test_head_pin_rejects_same_serial_state_hash_mismatch=KILLED` と記録し、node 集合依存の期待を台帳に明記してください。

### A-4 — floor の17-key比較は意味値には十分だが、凍結 bytes の独立 golden になっていない

- severity: **should**
- 根拠: 手順は parsed 値・長さを検査した後、生成物自身の SHA を表示して後続 pin に転記します（[s2-plan.md:263](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s2-plan.md:263)）。builder/post-write 検査も同一 canonicalizer による自己整合です（[s8b_floor_campaign.py:520](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_floor_campaign.py:520)、[同:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_floor_campaign.py:660)）。旧 bytes 中の g1 hash は1回だけで、64-byte の g2 hash へ単純置換した独立期待値は、長さ **774**、SHA-256 **`c0eeed87ab1f449b97c0b7d88654a8c3a5c07fae3565dc90c5724e29f1cb660d`** です。
- 成果物影響（1行）: canonicalization や余分な byte drift が同じ18値・774 bytesに収まると、その出力 SHA が FROZEN_MANIFEST、floor report の `protocol_sha256`、台帳参照へ自己承認されます。
- 修正案: semantic 比較に加え、`old_raw.count(g1_hash)==1`、`new_raw == old_raw.replace(g1_hash, g2_hash, 1)`、上記 SHA の3条件をユーザー手順へ事前登録してください。

### A-5 — 「T126 は影響なし」は admission に限れば正しいが、成果物 identity には反例がある

- severity: **should**
- 根拠: T126 の環境 admission は clocks/numactl/attestation/isolation の比較で、確かに protocol 内の contract hash には依存しません（[t126_driver.py:873](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/qualification/t126_driver.py:873)）。しかし series preimage は superproject commit/tree と code identity を含み（[同:386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/qualification/t126_driver.py:386)）、`env_contract.py` と `env_contract_activation.py` は必須 identity です（[qualification/contract.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/qualification/contract.py:38)）。record directory を直接除外しても commit/tree は変わります。
- 成果物影響（1行）: T126 の protocol 受理集合は不変でも、新規 `qualification_series_id`、series report、attempt ledger の参照値は必ず変わり、旧 series の resume/reuse は同一 identity になりません。
- 修正案: brief を「T126 protocol admission は不変、series identity は回転」に訂正し、旧 series を継続しないことを受入条件へ追加してください。

### A-6 — prediction seal も current-coupled であり「floor live admission だけ」ではない

- severity: **should**
- 根拠: prediction runner は承認定数から current contract を使って protocol bytes を再導出し（[s8b_prediction_runner.py:1457](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_prediction_runner.py:1457)）、指定 `pre_oracle_head` の blob と比較します（[同:1564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_prediction_runner.py:1564)）。したがって g2 活性化＋旧 g1 floor では selector seal も拒否されます。既存 selector の歴史検証は `pre_oracle_head` blob を使う別経路なので安全です（[s8b_ratified_freeze.py:2613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_ratified_freeze.py:2613)）。
- 成果物影響（1行）: floor 再発行前または旧 pre-oracle head を再利用した selector run は、prediction report と journal header を生成できません。
- 修正案: 影響表へ prediction seal を独立 consumer として追加し、「新規 seal は g2 floor commit を基点にする」「既存 selector は ratified historical lane のみで読む」をテストで固定してください。

## 静的に確認できた防壁

- cross-env 取り違えは global hash 一意性＋`expected_env_tag` で閉じています。
- `binding.calibration` と `gap_leg.attestation` の二重 hash は現コードでは semantic/raw の二層で整合検査されています。
- g1→g2 は generation/hash 対の変化、exact `+1`、successor predicate を通るため、遷移述語は確実に発火します（[env_contract_activation.py:274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/env_contract_activation.py:274)、[env_contract.py:417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/env_contract.py:417)）。
- activation テスト表の変更に skip 化や検証削除は見当たりません。valid-suffix/never-active の synthetic head1 化は、g3不在下で同じ述語を保持するための fixture 分離です。
- floor の live pin は `FROZEN_MANIFEST` 1箇所、protocol builder 2箇所、floor e2e 1箇所で、プランの更新一覧は網羅しています。selector journal の旧 SHA は歴史値なので更新不要です。
- holdout-freeze/verdict は env contract を参照せず、execution_guard/pipeline/loop/screening_driver は渡された current authorization を fail-closed に消費します。Pegasus の汎用 loop caller は `allow_resume=False` で既存 campaign artifact を拒否します（[p3_s4_loop_trigger_gating.py:340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/p3_s4_loop_trigger_gating.py:340)）。
- oracle report は記録 hash の historical resolver を既に使用しています（[s8b_oracle_report.py:1640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_oracle_report.py:1640)）。

## 総括

- 判定: **NO-GO**
- must-fix A-1: committed evidence 保全と hybrid 文書受理のどちらが仕様かを裁定する。
- must-fix A-2: g2正例・cross-env・複数hash不一致を含む CLI 受理行列を追加する。
- must-fix A-3: state-hash-only 単独変異を登録し、両単独 SURVIVED／対変異 KILLED を実証する。
- 活性化 chain、g1→g2 遷移述語、00000001 不変方針そのものには静的な correctness 欠陥を認めない。