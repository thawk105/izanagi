### `declared_use_class` 採用は T-318/T-337 の既裁定を無断で上書きしている

- 深刻度: blocker
- 根拠: `output/insights/2026-08-05_t337-qualification-authority/s2-plan.md:25,40-43,176`、`docs/archive/worklog-phase3-0802-113-116.md:937-940,955-957`、`docs/archive/worklog-phase3-0802-117-121.md:1367-1370,1407-1409`
- なぜ既存裁定と矛盾するか、または誰も呼ばないと言えるか: T-318 と T-337 はともに literal に `artifact_role` を採用している。「概念名だった」と読み替える根拠は一次裁定にない。既存の文書種別 `artifact_role` との衝突自体は実在するが、それは既裁定を設計者が改名してよい根拠ではなく、新事実を添えた再裁定理由である。実測では `declared_use_class` の production hit/caller は 0 件、T-318 軸の実装も 0 件。一方、既存 `artifact_role` は production 8 hit・CLI producer 1 経路ある。
- 成果物影響: 将来 T-318 gate が既裁定どおり `artifact_role` を要求すると RF receipt の `declared_use_class` は未分類として拒否され、certified 選択・材料レポートへ qualification 参照が一件も入らない。

### 「適格性 field の consumer は 0 件」は事実ではなく、0 件なのは promotion consumer だけである

- 深刻度: must-fix
- 根拠: `output/insights/2026-08-05_t337-qualification-authority/brief.md:27-29,56-59`、`orchestrator/campaign/silo_ladder_rung1_contract.py:538-564`、`orchestrator/campaign/silo_ladder_rung1.py:1241-1246,1556-1560,3755-3761,4042-4048,4820-4835`
- なぜ既存裁定と矛盾するか、または誰も呼ばないと言えるか: ledger の三 field は contract に読まれ、二つの実 driver 経路で不一致なら計測を停止する。evidence 側の二 field も `_validate_schema()` が読み、`verify-result` を rc=1 にする。したがって production の判断 caller は、ledger contract が2 call site、evidence validator が collect/verify の2 call siteある。これらは新 artifact を正に昇格させる権威ではないが、既存 rung に対する authoritative な負制約であり、「歴史的宣言にすぎない」は広すぎる。
- 成果物影響: 値を変えると試行台帳の receipt が生成されないか既存 evidence 参照が無効になる。certified 受理集合は増えないが、材料レポートが参照可能な既存負例が変わる。

### P4 は D126(4) を一般化しすぎ、裁定済みの代替 X 再走まで禁止している

- 深刻度: must-fix
- 根拠: `output/insights/2026-08-05_t337-qualification-authority/brief.md:62-64`、`docs/decisions.md:6191-6194,6216-6219`、`docs/archive/worklog-phase3-0803-124.md:15-18,35-37`
- なぜ既存裁定と矛盾するか、または誰も呼ばないと言えるか: D126(4) が禁じたのは、結果後に同じ probe の条件を変えることと、W1 のみに縮めること。後続ユーザー裁定は、O(1) stripe と cache-line padding を備えた代替 Xについて、Q1〜Q5 に従う新しい事前登録済み probe の再走を明示承認している。「代替 X を作れば事後調整」は誤りである。本 wave で作らない結論は scope と実経路不在から導けばよい。
- 成果物影響: この一般化を D に残すと、裁定済みの次試行が台帳へ登録されず、正例・RF 材料参照・certified 候補が永続的に空のままになる。

### `eligibility_status` の閉表は Q9 の裁定済み状態を表現できない

- 深刻度: must-fix
- 根拠: `output/insights/2026-08-05_t337-qualification-authority/s2-plan.md:13,99,102-111`、`docs/archive/worklog-phase3-0803-138-139.md:364-366`、`output/insights/2026-08-03_t338-rf-statistical-design/package.md:257-267`
- なぜ既存裁定と矛盾するか、または誰も呼ばないと言えるか: 案は decision の閉集合を `eligible / ineligible / not_certifiable / invalid_receipt` とする一方、Q9 が状態名として固定した `weak_denominator_not_certifiable` を含めていない。これを `reasons[]` に落とすだけでは「状態名を置く」という裁定を満たさない。また「少なくとも〜の閉集合」は閉表を将来拡張可能にする表現で、D126(4) の事前固定とも噛み合わない。
- 成果物影響: 弱い分母の材料レポート値が generic `not_certifiable` に潰れるか schema reject となり、受理集合は同じ非受理でも状態値と証拠参照が変わる。

### 新しい `trial_id` は既存 8c の同名 ID と異なる実体を指し、結合規則がない

- 深刻度: must-fix
- 根拠: `output/insights/2026-08-05_t337-qualification-authority/s2-plan.md:87-90,102-105,134`、`orchestrator/campaign/trial_registry.py:41-55,78-113,263-289`
- なぜ既存裁定と矛盾するか、または誰も呼ばないと言えるか: 既存 `trial_id` は H1/H2 × `on/off/swapped` の exact 6 cell の各一試行で、`arm/holdout/campaign_id` に束縛される。案の RF `trial_id` は candidate・workload・contrast と複数 cluster/三 arm を束ねる study 側 IDであり、さらに別 `rf_trial_registry.py` に隔離するとしている。production では既存 `trial_id` が3 module・73 hitある一方、RF schema/class/caller は全て0件で、両 ID の foreign-key 規則がない。`rf_trial_id` 等へ分けるか、同一実体だと証明する binding が必要である。
- 成果物影響: 材料レポートが RF decision を別の 8c trial へ結合し、certified 選択の候補参照や試行台帳の再現参照を取り違えうる。

### T-126 receipt は repo 外ではなく `$REPO_ROOT/output` に書かれる

- 深刻度: nit
- 根拠: `output/insights/2026-08-05_t337-qualification-authority/brief.md:39-40`、`output/insights/2026-08-05_t337-qualification-authority/s2-plan.md:54`、`tools/pegasus/t126_qualification.sh:56-61`、`tools/pegasus/submit_t126_qualification.sh:28-33`
- なぜ既存裁定と矛盾するか、または誰も呼ばないと言えるか: producer は `output/env/pegasus/qualification/t126` を repo root 配下に作る。したがって tracked inventory 0 件だけでは実 receipt の不在確認にならない。本レビューでは filesystem も確認し、現 worktreeでは実ファイル0件だったため DW-G04 結論は変わらない。
- 成果物影響: 現在値への影響はないが、この所在誤認を残すと別 worktreeの未追跡 T-126 receipt を試行台帳・移行 inventory から落とす。

## 総括

- (i) **NO-GO** — identifier の既裁定違反が blocker、ほか4件が land 前修正必須。
- (ii) **独立 DW-G04 判定は docs-only** — 唯一の3-arm path `877859` は W2/全体不成立かつ J=1、T-126 は二者・no-promotion、現行 Layer3 は qualification lineage を拒否し、RF consumer/caller は0件。
- (iii) **段4の択一:** T-318/T-337を明示 supersedeして軸名を全体で `declared_use_class` へ改めるか、literal `artifact_role` を維持して既存 oracle の文書種別名を改めるか。
- 推奨は前者。ただし段4が独断で確定せず、新事実付きでユーザー再裁定へ戻すこと。