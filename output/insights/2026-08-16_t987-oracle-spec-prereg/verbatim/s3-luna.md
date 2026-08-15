静的確認のみです。pytest は非実走。実測・静的推論・未確認を区別します。

### 1. [refuted] 「entry 511 は lifecycle の素描と 4 候補だけ」

- 主張: 親 brief の「A/B/C だけが付加価値」という整理は、既存成果物との差分を過大評価している。
- 根拠: 先行 `package.md:26-31` は 9 項目の決定者分類と blocker を既に記載。`preregistration-approval-package-draft.md:15-30,71-180` は分類、ccbench、除外理由、binding を既に扱う。`producer-design.md:101-113,185-212,274-301` は 3 状態、producer 手順、block、blocker を既に設計済み。形式化された受理集合 `X` と no-follow namespace は `s2-plan.md:24-72` の実質的な追加。
- 成果物への影響: A の大半、C の分類、ccbench、除外理由、blocker は再掲であり、そのまま新規成果として出すと重複する。
- 推奨: 裁定へ返せ。新規差分を「spec 層の未接続」「受理集合の形式化」「a12 と現行 judge の不整合」に限定せよ。

### 2. [real] 単一 block 契約は spec 承認時には発火しない

- 主張: exact 1 block を要求する設計自体は先行 wave と重複するが、spec loader への接続欠落は実在する。
- 根拠: `validate_reviewed_spec` は `build_schedule` だけを呼ぶ `s8b_oracle_spec.py:123-130`。`build_schedule` は複数 block を受け入れる `s8b_oracle_manifest.py:229-239`。exact 1 件の検査は `_validate_schedule` の `s8b_oracle_manifest.py:302-307` にあり、manifest 構築後段で呼ばれる `s8b_oracle_manifest.py:724`。
- 成果物への影響: 複数 block の spec が spec 承認を通り、manifest 生成で初めて落ちる。承認手番を消費した後に失敗するため、B の実効性を損なう。静的推論であり実走未確認。
- 推奨: 裁定へ返せ。承認前 gate に接続する実装を別 wave として裁定せよ。

### 3. [refuted] a12 から `n=8` または n の上下限を導ける

- 主張: brief の P1/P2 と M4 の「U は J とともに単調増加」「n=8 は q の平坦化点」は承認根拠にならない。
- 根拠: artifact の `false_pass_rule.formula` は `mean - q*sqrt(s/J) > 0`、`claim_scope.value` は `a11_empirical_stress_model_only`、`pilot_ready` は `false`。実測 field でも W1/H は J=9 の `0.0016691623` から J=10 の `0.0016291211` に低下し、W2/G は J=12 の `0.0039004393` から J=13 の `0.0038125182` に低下。現行 judge は median of medians であり、a12 の平均・分散・q 規則ではない `s8b_oracle_judge.py:164-168`。
- 成果物への影響: a12 を n の導出値として提示すると、事前登録の根拠が実験対象と別の規則になる。n=8 は費用見積りと近似的な較正に基づく AI 草案に留まる。
- 推奨: 却下。a12 の n 根拠を承認パッケージから削れ。

### 4. [real] `no-active-ratified-freeze` は先行 blocker だが、唯一の blocker ではない

- 主張: blocker の順序に関する親の主張は正しい。ただし active freeze ができても本走可能とは限らない。
- 根拠: 現物確認では `output/s8b-freeze/` に floor、holdout、selector のみで active pointer/approval 世代はない。live pointer が無ければ `no-active` になる `s8b_ratified_freeze.py:1254-1257`。manifest は spec より先に active freeze を読む `s8b_oracle_manifest.py:1170-1188`。さらに holdout artifact の `floor` と `budget` はともに `null`、driver も `s8b_oracle_driver.py:471-474` で拒否する。
- 成果物への影響: 今ユーザーが 4 値を承認しても、`APPROVED_SPEC_SHA256` は `None` のまま `s8b_oracle_spec.py:21-23` で、spec、manifest、本走のどれにも効かない。最終承認パッケージとして提示する実効性はない。
- 推奨: 却下。今は最終承認ではなく、active v2、floor、budget 後に再提出する保留資料とせよ。

### 5. [real] 7 分類は段階を混ぜている

- 主張: 「ユーザー承認」「validator 固定」「freeze 継承」を現在の spec gate と本走 gate にまたがって一括分類している。

- 根拠:

| 項目 | 実際の code 上の決定者 | 判定 |
|---|---|---|
| `n` | 正整数かだけを検査 `s8b_oracle_manifest.py:226-227` | ユーザー選択は妥当。ただし `8` の導出は未確認 |
| `master_seed` | 非空 identifier のみ `s8b_oracle_manifest.py:228` | ユーザー選択。ISO 形式は未固定 |
| `block_sizes` | 複数 block を builder が受け入れ、exact 1 は後段のみ | 「validator 固定」は spec 承認段階では誤り |
| `campaign_ids` | block との一対一と spec 内重複だけを検査 `s8b_oracle_spec.py:147-158` | ユーザー選択。ただし repo 全体の衝突検査は未確認 |
| `holdout/configuration_ids` | active freeze との一致は manifest 構築時だけ `s8b_oracle_manifest.py:1192-1213` | 現 v1 artifact から直ちに「freeze 継承済み」とは言えない |
| `generator_versions` | canonical path と現 byte hash を検査 `s8b_oracle_manifest.py:53-62,430-470` | ユーザー選択でなく現 source からの機械導出 |
| `binding_identity` | spec では自己 hash と cell 集合だけ `s8b_oracle_spec.py:160-165` | freeze 継承は未接続。実 binding 照合は marker 後 `s8b_oracle_driver.py:1462-1475` |
| run contract | 5 値は固定 `s8b_oracle_manifest.py:396-427`、環境値は runtime lookup `s8b_oracle_driver.py:862-888`、ccbench は binary receipt と照合 `s8b_oracle_driver.py:949-958` | 一つの「validator 固定」欄にまとめてはならない |

- 成果物への影響: ユーザーが承認しても効かない値と、ユーザーが選べない値が同じ承認欄に並ぶ。binding は誤っていても marker 作成後に拒否され得る。実走未確認。
- 推奨: 裁定へ返せ。現時点では `n`、seed、block ID、campaign ID だけを未承認草案として残し、他は確認欄または未導出欄に分けよ。

現状態で AI が未承認値を official spec として流している実測はない。`APPROVED_SPEC_SHA256=None` かつ spec/candidate directory 不在であり、草案値も文書上は未承認である。

### 6. [real] ISO-8601 JST は先例だが、oracle の要件ではない

- 主張: `master_seed` を floor 先例の ISO-8601 JST 文字列にする案は「形の先例」としては正しいが、validator の要求や導出値ではない。
- 根拠: `floor_protocol.json` の `master_seed` は `"2026-07-18T17:16:12+09:00"`、`s8b_approved.py:46` も同値。一方 oracle 側は `master_seed` を identifier として受けるだけ `s8b_oracle_manifest.py:228`。先行案の slug も形式上は通る。
- 成果物への影響: ISO 形式を必須として提示すると、先例を code contract と誤認させる。現在の承認時刻と実値は未確認。
- 推奨: 裁定へ返せ。形式と実値を別判断にし、現在の承認欄からは外せ。

### 7. [real] `ccbench_pin` の二択は排他的な目的選択であり、同時に承認できない

- 主張: floor protocol の `d706650c...` と現 gitlink/`CCBENCH_FULL_SHA` の `511c9538...` は実在する二つの pin だが、単一 spec の二つの選択肢ではない。
- 根拠: `floor_protocol.json` の `ccbench_pin` は `d706650c...`、`s8b_approved.py:65-67` と実測 gitlink は `511c9538...`。両 commit の存在は静的確認済み。manifest は非空文字列しか固定せず、実行時は binary receipt の pin と完全一致させる `s8b_oracle_manifest.py:403-404`, `s8b_oracle_driver.py:949-958`。
- 成果物への影響: 「現 floor と比較」か「現 gitlink で floor を再測定」かを先に決めない限り、ユーザーは一つの exact spec を承認できない。active v2 の binary receipt が未存在のため、どちらが将来通るかは未確認。
- 推奨: 裁定へ返せ。目的を先に択一させ、`ccbench_pin` はその導出値として後段に置け。

### 8. [refuted] floor の 4 件を oracle へそのまま流用できる

- 主張: 形と順序の先例はあるが、意味の継承は成立していない。
- 根拠: floor の 4 件は `floor_protocol.json` の `allowed_excluded_reasons` と `s8b_floor_stats.py:49-55` に固定。一方 oracle validator は非空・重複なしだけ `s8b_oracle_spec.py:171-177`、manifest も同様 `s8b_oracle_manifest.py:736-744`。report も list の形式だけを検査 `s8b_oracle_report.py:386-390`。
- 成果物への影響: oracle 独自の failure event と除外理由の対応を承認せずに流用すると、除外裁量の境界を未承認のまま固定する。
- 推奨: 却下。oracle 固有の理由集合と event 対応表を別裁定にせよ。

### 9. [real] 承認パッケージの一手構成はまだ成立していない

- 主張: 現案は「今決めない値」と「ユーザーが決める値」と「目的依存の択一」を一つの承認手番に混在させる。
- 根拠: 先行案自身が Q1〜Q4 の複数裁定を要求 `package.md:33-99`。現案は 4 項目を「承認可能」としつつ「今決める必要はない」 `preregistration-approval-package-draft.md:15-30,66-69`。`ccbench_pin` は択一でなく記録のみとされる `package.md:88-99`。T987 の成果物形状 `brief.md:90-95` にも、排他的な選択欄や確認欄の実体は未確認。
- 成果物への影響: ユーザーは、現時点で効かない草案を承認するのか、将来の exact spec を承認するのか判断できない。
- 推奨: 却下。後日の一手を「目的の択一」「設計選択 4 項目」「機械導出値の確認」に分離し、現在は最終承認を求めない形へ戻せ。

## 総括

倒した主張: a12 から n=8 を導ける、entry 511 に決定者分類がない、floor の 4 理由を oracle に流用できる、という主張。  
残すべき新規所見: spec 層の単一 block 未接続と、承認が runtime に効かない blocker。  
承認パッケージから削る項目: 今すぐの 4 値、ccbench 二択、current v1 の freeze 値、binding、generator hash、除外理由の承認欄。  
現段階は最終承認ではなく、active v2・floor/budget・trust root 後の再提出とする。