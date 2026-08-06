## 判定

このプランは現状のままでは land 不可です。must-fix は 7 件あります。

本レビューは静的検査のみです。pytest その他のテストは実行しておらず、テスト結果は主張しません。また `env_contract_activation.py` と activation record はまだ存在せず、以下の新規検査はすべてプラン上の予定です。

## 保証と検査の対応表

| 主張する保証 | 支える検査 | 検査が見ていない状態 | 判定 |
|---|---|---|---|
| record の exact schema・canonical bytes | 関数名未定の decoder、`load_activation_state()`。`s2-plan.md:80-87` | issuer、commit 済みか、record 集合の suffix 削除 | 部分的 |
| serial の単調性・rollback 防止 | `load_activation_state()` の filename/serial/hash-chain 検査。`s2-plan.md:70-73,84-86` | trusted latest head がないため、末尾 record の削除・chain 全交換 | must-fix |
| inactive generation は current にならない | `validate_generations()`、`load_activation_state()`、`test_registered_but_inactive_g2_does_not_change_registry`。`s2-plan.md:130-151,224-229` | `_ACTIVATION_STATE` / `REGISTRY` の再束縛、valid active g2 を成功させる正例 | must-fix |
| record だけでは未publish g2を活性化できない | `verify_activation_evidence()` の7条件。`s2-plan.md:89-108` | publisher provenance、契約との env/clock/policy 照合、receipt の外部裏取り | must-fix |
| 全入口が最初の write 前に同じ状態を検査 | `issue_receipt()` / `assert_current_receipt()` と wrapper の `admit_current()` / `assert_current_activation()`。`s2-plan.md:80-87,155-182` | import 後の disk 変更、別 checkout、別 process、未列挙 writer | must-fix |
| sealed receipt は偽造・stale を拒否 | `test_forged_stale_or_cross_env_receipt_is_rejected`。`s2-plan.md:543` | seal の生成・秘匿方法、module global の再束縛、実 state の再読込 | must-fix |
| 既存 contract hash は不変 | `test_contract_sha256_matches_independent_reference`、linux/Pegasus golden。`test_env_contract.py:1109-1138` | 特段なし | 支持あり |
| 現状の受理集合は不変 | `test_g1_activation_preserves_current_lookup_acceptance_set`。`s2-plan.md:196-212` | 各入口、import 条件、committed artifact corpus、historical verifier | must-fix |
| 旧 proof chain は再検証可能 | `_CONTRACT_SHA256_INDEX` / `resolve_by_contract_sha256()`。`env_contract.py:329-380` | production verifier は依然 `lookup()` を使用 | must-fix |
| 既存 artifact bytes/schema は不変 | 案Cで永続化しない。`s2-plan.md:362-373` | run と activation serial/state の事後対応 | bytes は支持、監査保証は欠落 |

## must-fix

### 1. `AcquisitionReceipt` は publish provenance を証明せず、P3 の「非偽造性」は成立しない

**根拠 file:line**

- 7条件は path/hash/schema/status の検査に限られる: [s2-plan.md:89](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-authority/s2-plan.md:89)
- `AcquisitionReceipt` の各 field は型・形式だけを検査する: [schema_v2.py:345](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/calibrator/schema_v2.py:345)
- accepted 時の照合も同じ JSON 内の値同士である: [schema_v2.py:521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/calibrator/schema_v2.py:521)
- candidate writer も入力 dict を dataclass 化するだけである: [make_acquisition_receipt.py:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/tools/pegasus/make_acquisition_receipt.py:36)
- actual binary の hash や probe を独立取得するのは calibrator CLI 実行時だけ: [cli.py:677](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/calibrator/cli.py:677)

自己申告値と独立検証値の内訳は次のとおりです。

| receipt 項目 | activation 時に検証されるもの | 独立に検証されないもの |
|---|---|---|
| `qsub` / `allocation` | 型、ID相互一致、正整数 | scheduler の実記録、実割当 host、実 cpuset、実 HT 状態 |
| `toolchain` | 非空文字列・list | 実 compiler/module bytes |
| `ccbench` | SHA形式、`pinned_clean=True`、argv | 実 HEAD、clean tree、argv を使った build、実 binary |
| `job_script_sha256` | hex64 | job script の実 bytes |
| `walltime` | 正数、内部的な大小関係 | scheduler request、実経過時間 |
| `known_values_check` | 固定 source 文字列、`passed=True`、同一JSON内 profile との一部照合 | runbook 正本、実 CPU model |
| `quality.status` | `"accepted"` という値 | publisher が算出した verdict であること、統計量の再計算 |

さらに7条件は、現行 production loader が行う `calibration.env_tag == contract.env_tag`、clock、current tolerance の照合も含みません。[env_attestation.py:1091](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_attestation.py:1091)

**成立条件:** `registered/...` に schema 内部では整合するが、正規 publisher 以外に由来する bytes が存在し、その SHA を参照する generation と record が存在する状態。7条件をすべて通る。

**成果物影響:** 誤った較正を current とした certified 選択、report、ledger が「正規 publish 証拠あり」と誤表示される。

**判定:** real。

**代案:** Git のレビュー済み commit を authority と明示して全入口で clean committed identity を検査するか、publisher/maintainer の detached signature と repo 外の trust root を用いる必要がある。schema validity と issuance authority は別保証に分けるべきです。

---

### 2. hash-chain には trusted head がなく、suffix rollback を検出できない

**根拠 file:line**

- プランは連番 record と predecessor hash だけで rollback を防ぐとしている: [s2-plan.md:13](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-authority/s2-plan.md:13)
- `O_EXCL` は issuer 実行時の上書きだけを防ぐ: [s2-plan.md:66](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-authority/s2-plan.md:66)
- chain 検査候補 M03: [s2-plan.md:534](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-authority/s2-plan.md:534)

**成立条件:** 最新 record を除いた valid prefix、または全 record を再計算した自己整合 chain が deployment に現れ、外部に期待 latest serial/hash が存在しない状態。残った chain は gap も predecessor 不一致も持たない。

**成果物影響:** current contract を旧世代へ戻した後の run が正常扱いされ、台帳上は rollback が観測不能になる。

**判定:** real。

`test_chain_rejects_gap_rollback_and_bad_predecessor` が malformed chain を拒否しても、valid suffix deletion は殺せません。Git commit/review を trust anchor とするか、repo 外の monotonic serial floor／署名済み head が必要です。

---

### 3. sealed receipt と `_ACTIVATION_STATE` は D176 が否定した module-local authority と同型である

**根拠 file:line**

- D176 は public dataclass の型が生成権限を証明しないとする: [decisions.md:8680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/docs/decisions.md:8680)
- module 属性の逆引き index も再束縛可能なので authority ではない: [decisions.md:8691](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/docs/decisions.md:8691)
- 案Cは module-level `_ACTIVATION_STATE` と非直列化 `_seal` に依存する: [s2-plan.md:132](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-authority/s2-plan.md:132)、[s2-plan.md:182](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-authority/s2-plan.md:182)

**成立条件:** `_ACTIVATION_STATE`、`REGISTRY`、assert 関数のいずれかが process 内で再束縛される状態。または record/calibration bytes が import 後に変わり、pre-write assert が import 時の cached state だけを再照合する状態。

**成果物影響:** stale・再束縛された contract で最初の write が許され、receipt の serial/hash は実 disk state を表さない。

**判定:** real。`_seal` の具体的な複製可能性だけは実装未定なので疑いだが、module global の再束縛と cached recheck はプラン上確定している。

`assert_current_activation()` が `_ACTIVATION_STATE` の field を再比較するだけなら、freshness 検査ではなく構造的な自己一致です。少なくとも threat model から in-process mutation を除外する裁定か、pre-write 時の trusted state/evidence 再取得が必要です。

---

### 4. 案Cでは「全入口が同じ activation state を使った」ことを成果物から検証できない

**根拠 file:line**

- 案Cは durable evidence がないことを明記する: [s2-plan.md:362](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-authority/s2-plan.md:362)
- silo は `gap-job` と `collect` を別 writer として扱う: [s2-plan.md:321](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-authority/s2-plan.md:321)
- brief は全入口で同じ状態 hash を検査することを要求する: [brief.md:8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-authority/brief.md:8)

**成立条件:** submission・measurement・collect、または別入口が異なる process／checkout／activation head で実行され、それぞれの local current check は成功する状態。

**成果物影響:** report・ledger・certified selection から、どの `activation_serial` / `activation_state_sha256` が測定を支えたか復元できず、複数入口の同一状態性を監査できない。

**判定:** real。

P4 の exact-key 互換要求自体は正しい一方、案Cが保証できるのは「現行 source の制御フローが assert を呼んだ」までです。既存 bytes を保存したまま新規 run を versioned schema／manifest-bound sidecar にする選択肢は残っています。親は durable proof を要求するか、保証を process-local gate に縮めるか裁定が必要です。

---

### 5. g2 活性化後、既存 g1 proof chain の read-only 再検証が current lookup により拒否される

**根拠 file:line**

- committed floor protocol は g1 contract hash を固定している: [floor_protocol.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/output/s8b-freeze/floor_protocol.json:1)
- floor protocol validator は artifact hash を current lookup の hash と比較する: [s8b_floor_contract.py:138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_floor_contract.py:138)
- ratified freeze の journal／run-command 再検証も current lookup を使う: [s8b_ratified_freeze.py:1795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_ratified_freeze.py:1795)、[s8b_ratified_freeze.py:2285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_ratified_freeze.py:2285)
- oracle report も manifest の contract hash を current と比較する: [s8b_oracle_report.py:1189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_oracle_report.py:1189)
- D176 自身が historical resolver の production consumer 不在を明記する: [decisions.md:8696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/docs/decisions.md:8696)

**成立条件:** Pegasus g2 が current になった後、g1 hash を持つ既存 floor/oracle artifact を再検証する状態。

**成果物影響:** committed floor evidence、oracle report、そこから導出する certified selection が「過去には有効だったが current でない」という理由だけで拒否され、proof chain が解決不能になる。

**判定:** real。

read-only verifier は artifact に記録された hash を `resolve_by_contract_sha256(..., expected_env_tag=...)` で解決し、世代別 predicate を dispatch する必要があります。current gate は新規 producer／resume admission に限定すべきです。

---

### 6. 「全入口」の閉包がなく、現行 certified writer に activation bypass が残る

**根拠 file:line**

- 共通 `loop._authorize_measurement()` は `env_contract is None` なら無検査で返る: [loop.py:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/loop.py:62)
- その直後に `layout.ensure()` が書込みを開始する: [loop.py:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/loop.py:139)
- certified outcome を作る `s8a_trigger_sweep` は `env_contract` を渡さない: [s8a_trigger_sweep.py:457](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8a_trigger_sweep.py:457)
- `p3_s4_loop` は `run_campaign()` より前に `layout.ensure()` を実行する: [p3_s4_loop.py:878](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/p3_s4_loop.py:878)
- これらは段2の編集対象一覧にない: [s2-plan.md:505](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-authority/s2-plan.md:505)
- 「silo 昇格」consumer は未同定で、対象ファイルは ability probe にすぎない: [s2-plan.md:309](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-authority/s2-plan.md:309)

**成立条件:** `loop.run_campaign()` の default `env_contract=None` caller、または `p3_s4_loop` の既存経路が実行される状態。

**成果物影響:** activation を経ない WAL、fitness、`certified=True` の結果が残り、選択・材料 report が旧手書き環境値を取り込める。

**判定:** real。

低位の共通 writer を gate するか、各 legacy caller が非production・非certifiedであることを機械的に閉じない限り、「6入口すべて」は主張できません。また真の silo promotion consumer がないまま ability probe を結線しても、昇格入口の保証にはなりません。

---

### 7. positive control が valid active g2 を一度も成功させず、「永久 fuse」実装でも通り得る

**根拠 file:line**

- 現状保持 test は「全世代長が1」と g1 lookup だけを見る: [s2-plan.md:196](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-authority/s2-plan.md:196)
- g2 正例は inactive のまま current が変わらない検査だけ: [s2-plan.md:224](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-authority/s2-plan.md:224)
- serial2、rollback、evidence の候補はすべて拒否側 mutation: [s2-plan.md:528](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-authority/s2-plan.md:528)

**成立条件:** loader が `generation > 1` または `activation_serial > 1` を無条件拒否する一方、g1 initial record と malformed g2 を期待どおり処理する状態。

**成果物影響:** テストが通っても較正の再取得・g2活性化は依然不能で、T-529 の目的自体が名ばかりになる。

**判定:** real。

必要な非恒真性証拠は、valid な2-record chain、正規 evidence を持つ active g2、そして `lookup()` がその g2 を返す成功ケースです。入口側にも refusal test だけでなく、valid g2 receipt が既存 writer の正常経路を通る正例が必要です。

### 受理集合の実変化

| 変化 | 箇所 | 評価 |
|---|---|---|
| 複数 generation の構造受理 | 現行 fuse `env_contract.py:321-326` → `s2-plan.md:130` | 意図した拡大 |
| valid g2 を record で current 化 | `s2-plan.md:147-151` | 意図した拡大 |
| 手製でも schema-consistent な「publish evidence」 | `s2-plan.md:89-108` | 未承認の拡大、must-fix 1 |
| import が全 active env の record/calibration bytes に依存 | `s2-plan.md:132-143` | 新しい全体 fail-closed 縮小。lookup positive control は未検査 |
| required-mode の canonical registered path と accepted status | `s2-plan.md:95-99` | correctness 強化だが、現行 loader より狭い |
| legacy を exact contract hash のみに限定 | `s2-plan.md:116-124` | 親裁定待ちの縮小 |
| g2後の historical artifact 再検証 | `s8b_floor_contract.py:138-150` 等 | 未承認の縮小、must-fix 5 |

初期 record が両 g1を選ぶ限り、静的には linux legacy bytes と Pegasus v2 accepted artifact が存在するため、直ちに落ちる committed artifact は断定できません。[legacy calibration:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json:1)、[Pegasus calibration:1599](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1599)。ただし corpus 再検証の positive control は計画されておらず、g2 活性化後の g1 artifact 拒否は静的に確定します。

## should-fix

### 8. legacy exact-contract-hash 例外は現状には必要十分だが、既存 loader より狭い

**根拠 file:line**

- 現行 loader は `mode=none` と exact calibration SHA だけを見る: [env_attestation.py:1119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_attestation.py:1119)
- プランは linux g1 の exact contract hash に限定する: [s2-plan.md:116](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-authority/s2-plan.md:116)
- contract hash は全 field と calibration ref を束縛する: [env_contract.py:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_contract.py:145)
- 全世代 hash 一意性も検査される: [env_contract.py:302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_contract.py:302)

**成立条件:** current linux g1 以外の `mode=none` contract が、同じ grandfathered bytes を参照する状態。現 loader は受理し得るが、新 gate は拒否する。

**成果物影響:** 現在の committed linux g1は維持できる一方、mode-none の将来 contract／API fixture の受理集合は狭まる。

**判定:** real。ただし現行 registry に対しては広すぎず、必要十分な狭さである。

親はこの exact contract hash を明示的な trust root として grandfather するか、detached evidence を作るか裁定すべきです。

---

### 9. 親実測の floor/oracle 限定は「非実在 path」に限れば正しいが、publish/quality まで一般化できない

**根拠 file:line**

- floor は calibration bytes を line 2762 で読み、最初の claim は line 2881: [s8b_floor_campaign.py:2758](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_floor_campaign.py:2758)
- oracle は line 781 で読み、claim は line 1193: [s8b_oracle_driver.py:781](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/s8b_oracle_driver.py:781)
- missing path は `resolve(strict=True)` で拒否される: [env_attestation.py:1072](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_attestation.py:1072)
- loader 自体は `quality.status == accepted` を要求しない: [env_attestation.py:1091](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/campaign/env_attestation.py:1091)

**成立条件:** g2 path は実在し hash/schema/profile が整合するが、artifact が rejected または正規 publisher に由来しない状態。

**成果物影響:** 現行 floor/oracle preflight を publish authority と誤認すると、claim前の検査があるにもかかわらず不正な calibration を実行 receipt へ進め得る。

**判定:** real。

したがって段1実測の命題「指定した非実在 g2 は floor/oracle では write 前に落ちる」は正しいです。一方、「両入口は既に正規 publish を検証する」まで広げるのは誤りです。

---

### 10. 「valid calibration」が historical accepted status か current predicate pass か未定義

**根拠 file:line**

- 現在の Pegasus artifact は `quality.status="accepted"`: [calibration:1599](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1599)
- しかし既存 test はこの calibration を既知の effective-clock self-inconsistent 例外として固定する: [test_env_contract.py:840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority/orchestrator/tests/test_env_contract.py:840)

**成立条件:** activation gate が status の歴史的 verdict だけでなく current predicate を再評価する設計へ強化される状態。

**成果物影響:** 追加 grandfather がなければ Pegasus g1 の initial record が拒否され、全 env_contract import が停止する。

**判定:** real。現プランは status だけを見るため直ちには発火しないが、「有効な calibration」という表現の射程が曖昧である。

## nit

### P2 の命名修正には欠陥を認めない

`activation_serial` / `activation_state_sha256` / `previous_activation_state_sha256` は、既存の time epoch、migration、bundle と区別できています。`s2-plan.md:448-471`。成果物完全性への追加指摘はありません。

## 総括

最も重い所見は次の3点です。

- `AcquisitionReceipt` は自己申告値の schema であり、正規 publisher の実行を証明しない。P3 の非偽造性は名ばかりになる。
- hash-chain、sealed receipt、`_ACTIVATION_STATE` は trusted external head を持たず、rollback・cached state・module再束縛を検出しない。
- g2 活性化後も read-only verifier が current `lookup()` を使うため、既存 g1 proof chain が再検証不能になる。

親が裁定すべき択一は次です。

- authority を「レビュー済み Git commit」と定義して全入口で committed identity を検査するか、外部 trust root を持つ署名済み activation/publisher receipt にするか。
- 案Cを process-local control-flow gate として保証を縮めるか、activation state を新規 run の versioned identity／durable evidence に残すか。
- fuse を外す前に historical resolver + versioned predicate dispatch を consumer へ配線するか、g2後の旧 artifact 拒否を明示的な受理縮小として承認するか。
- linux g1 exact-contract-hash grandfather を採るか、detached acquisition evidence を要求するか。
- generic `loop.run_campaign` を含む全 certified writer を対象にするか、legacy producer を機械的に非production化するか。
- silo ability probe を対象と呼ぶか、真の promotion consumer が同定されるまで「silo 昇格入口は未実装」とするか。

プランのまま実装すると、次が名ばかりの保証になります。

- 「record／receipt は非偽造」
- 「hash-chain は rollback を検出」
- 「pre-write assert は最新 state を再検査」
- 「全入口が同じ activation state を使用」
- 「g2を実際に活性化できる」
- 「既存 committed proof chain の受理集合は不変」