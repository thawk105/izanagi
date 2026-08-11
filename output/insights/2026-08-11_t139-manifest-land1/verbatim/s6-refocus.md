## 判定

**NO-GO。凍結前に少なくとも 2 件の文書欠陥を直す必要があります。**

略記: `R`=`record-items-v2.md`、`S`=`receipt-schema-v1.json`、`E`=`erratum...v2.md`、`P`=`package.md`。

## (1) 対応表

| 出所 | 所見の要旨 | 判定 | 根拠 |
|---|---|---|---|
| C-1.1 [blocker] | `position=1 ⇒ predecessor_arm=START` が schema にない | **partial** | `R:338` は同値を要求するが、`S:687-696` は `START ⇒ position=1` のみ。実際に `position=1, predecessor_arm=stock` は schema ACCEPT |
| C-1.2 [blocker] | compile flags と argv/CMakeCache の照合 | **closed** | `R:237-239,594-602,763` |
| C-1.3 [blocker] | qsub returncode を受理入力に使う consumer の否定検査 | **closed** | `R:68-69,781-783` |
| C-1.4 [blocker] | submission intent の create-only | **closed** | `R:464-470,767` |
| C-1.5 [blocker] | job-side preflight reject collector | **closed** | `R:468-469` |
| C-1.6 [blocker] | performance marker の create-only | **closed** | `R:466-467,767` |
| C-1.7 [blocker] | `#FLAGS_` / `ShowOptParameters()` exact 照合 | **closed** | `R:612-615,764` |
| C-1.8 [blocker] | `J` 導出 receipt の必須性 | **closed** | `R:429-430,749,770` |
| C-1.9 [blocker] | `q` 導出 receipt の必須性 | **closed** | `R:429-430,749,770` |
| C-1.10 [blocker] | simulation receipt の必須性 | **closed** | `R:427-428,749` |
| C-1.11 [blocker] | alpha reservation evidence の必須性 | **closed** | `R:425-426,748` |
| C-1.12 [blocker] | actual argv と計画 argv の exact 比較 | **closed** | `R:612-613,764` |
| C-1.13 [blocker] | schema digest の `PreregBinding` pin | **closed** | `R:164-167,770` |
| C-1.14 [blocker] | `binary_rehash` の到達点条件 | **closed** | `R:293-298,757` |
| C-1.15 [blocker] | `liveness` enum の旧閉集合 | **closed** | `R:402,409-413,747` |
| C-1.16 [blocker] | `calibration_simulation` の改名 | **partial** | `R:68,419,427-428` は erratum 承認を前提とする。`E:94-127` は候補だが未承認 |
| C-2 [blocker] | pilot 288 run を schema が拒否 | **closed** | `R:41,336-337,754`、`S:729-733` は `minItems:36` のみ |
| C-3 [blocker] | stage 粒度・main slot・verification allocation の矛盾 | **closed** | `R:47-53,577-590,673-677` |
| C-4 [blocker] | 成功 verification attempt の表現不能 | **closed** | `R:43-45,510-516` |
| C-5 [blocker] | verification に性能 phase/rehash を強制 | **closed** | `R:281-298,695-702`、`S:471-535` |
| C-6 [blocker] | schema と要件文書の不一致 10 系統 | **closed** | `R:733-771` が 20 項目の semantic 責務を列挙 |
| C-7 [blocker] | 承認済み文書から一意に導けない predicate | **partial** | `R:819-834` が 8 件を明示しただけで、`P:100-110` の人間裁定が未了 |
| C-8 [blocker] | trace/correctness を自己申告で代替可能 | **closed** | `R:594-603,762-763`。ただし validator 実装は未実装 |
| C-9 [blocker] | erratum の置換内容が pin されない | **closed** | `E:130-151,206-212`。候補値の検査は成立。ただし外部 manifest pin が必須 |
| D-1 [blocker] | pilot 288 run の schema 拒否 | **closed** | `R:41,336-337`、`S:729-733` |
| D-2 [blocker] | verification-only receipt を記録不能 | **partial** | terminal receipt 方針は `R:43-45,515` で解消。ただし `R:747-749` の無条件「6 件」が失敗 stage 条件と矛盾 |
| D-3 [blocker] | preflight `a03` failure と rehash の衝突 | **closed** | `R:293-298,525-541,757` |
| D-4 [blocker] | `fallback_build_inside` が記録不能 | **refuted** | `A:357-360` が fallback binary と verification artifact の一致を要求。`R:212-214` は正しい |
| D-5 [must-fix] | qsub failure・中間状態を terminal receipt にできない | **closed** | 中間状態を receipt に載せない契約が `R:43-45`、qsub failure row は `R:453,575-576` |
| D-6 [must-fix] | `malformed_reason` の優先順位未定義 | **closed** | `R:495-504` |
| D-7 [must-fix] | schedule の block index が曖昧 | **closed** | `R:327,635-640` |
| D-8 [must-fix] | valid-shaped counter による第三分岐偽装 | **closed** | `R:793-802` が残余として明示 |
| D-9 [suspicion] | pilot/main slot identity の曖昧さ | **closed** | `R:47-49,673-677` |
| D-10 [must-fix] | 時間予算と phase mapping の不整合 | **closed** | `R:680-707`。ただし package の旧算術誤記は残存 |
| D-11 [must-fix] | 既存 driver が必要証拠を取得しない | **partial** | `P:180-186` が land 2 scope 外として残している。実測・certified 出力には未解決 |
| D-12 [must-fix] | package の「exact 1:1」「承認可能」過大主張 | **closed** | `P:24-26` で semantic validator との分離を明記 |
| D-13 [nit] | `2340` 算術誤記 | **partial** | `P:194-196` に依然として残る。正値は `2640` |

## (2) fix が持ち込んだ新しい欠陥

### 1. correctness/liveness の条件付き件数が semantic 一覧で無条件化されている `[blocker]`

現物には次の三つが併存します。

- completed verification は evidence 6 件、liveness 6 件: `R:515`
- failed verification は得られた件数のみ、0 件も可: `R:388-390,410-411`
- しかし §7.1 は無条件に correctness 6 件・liveness 6 件を要求: `R:746-749`

そのため semantic validator が §7.1 を字義通り実装すると、verification failure の正当な 0〜5 件 receipt を拒否します。

影響: failed verification の受理集合と試行台帳が変わる。§7.1 を「completed verification の場合のみ」に修正すべきです。

### 2. `consumed_cluster_slots` の stage 別制約は本文では閉じている `[closed / 要確認]`

schema 単体では main stage の `[]`、重複、未整列も通りますが、本文の semantic 責務は明記されています。

- pilot は exact `[1..8]`: `R:673-674`
- main は昇順・重複なしの 1..13 部分集合、要素数 `J`: `R:675`
- runs 件数は `36 × |consumed_cluster_slots|`: `R:754`

実測 schema では main の緩い形も ACCEPT しますが、schema は形だけと明記されています (`R:733-734`)。仕様上は closed、schema-only consumer は不適格です。

### 3. role 別 phase enum `[closed]`

`performance_cluster` に verification phase、`verification` に performance phase を入れた例は schema REJECT になりました。

- performance: `preflight` 等のみ: `S:471-505`
- verification: `staging` 等のみ: `S:506-536`

### 4. `correctness_evidence` 0〜6 `[partial]`

schema の 0〜6 は failed verification を表すため必要ですが、上記 §7.1 の無条件記述が残っており、semantic 側で 6 件必須が実質的に落ちる余地があります。

### 5. `binary_rehash` 到達点 `[closed]`

`R:293-298` と `R:757` に到達点条件が明記されています。0〜9 は「到達した点だけ」の意味であり、10 件は schema REJECT でした。

### 6. `runs` の上限削除 `[closed]`

schema は `minItems:36` のみ (`S:729-733`)、exact 件数は `R:754` の semantic validator に移管されています。37 件以上を schema が通すこと自体は文書契約違反ではありません。

### 7. erratum の自己参照・循環と反例

循環はありません。`new_sha256` は `new_text` の hash、`expected_composed_sha256` は合成後 core の hash であり、erratum 自身をハッシュしていません。

候補値の独立検査結果:

- 第1 `new_sha256`: 一致
- 第2 `new_sha256`: 一致
- 合成 digest: 一致
- 適用順序反転: 一致
- 置換後 `較正`: 0 件

レンズ C の反例をそのまま使うと、canonical hash を維持した場合は検査 8 で拒否されます。しかし攻撃者が `new_sha256` と `expected_composed_sha256` も差し替えると、検査 8〜12 は自己整合だけなので通り得ます。

したがって、検査 8〜12だけでは完全な pin ではありません。`approval_manifest` が erratum blob の digest を事前に固定し、その blob digest を resolver が必ず照合することが必要です。これは `R:162-163` の authority 契約が実装されることを前提にした `[suspicion]` です。

## (3) 独立再計算

独立再計算は **7/7 一致**でした。

- `92fd7175…`: 一致
- `b8741cc9…`: 一致
- `expected_composed_sha256`: 一致
- 適用順序非依存: 一致
- 置換後 `較正` 件数: 0
- `Draft7Validator.check_schema`: rc=0
- object schema 51 件、`additionalProperties:false` 欠落 0 件

schema の追加静的検査:

- `position=1, predecessor_arm=stock`: schema は ACCEPT
- role 不整合 phase: REJECT
- `runs=35`: REJECT、`runs=36/37`: schema ACCEPT
- `binary_rehash=10`: REJECT

## (4) 残余の裁定材料

### 凍結してよい残余

- producer が preflight raw を作って未実行に見せる経路: `R:793-803`。候補自身が明示的に引き受けています。
- semantic validator 未実装: `P:177-179`。land 1 が要件文書凍結だけなら scope 内です。
- driver/collector 未実装: `P:180-186`。ただし実測開始・certified 化の前には必須です。
- §10 の8件の閉包は技術欠陥ではなく、明示的な人間裁定事項です。

### 凍結前に直すべき欠陥

1. **§7.1 の correctness/liveness 件数を completed verification に条件付ける。**  
   失敗 verification の 0〜5 件 receipt の受理集合が変わります。

2. **package の `2340` を `2640` に修正する。**  
   受理集合は変わりませんが、walltime・contingency・材料レポートの算術参照が変わります。

3. **erratum blob の approval-manifest pin を機械的必須条件として確認する。**  
   未確認のままなら、別 hash を自己申告した erratum が検査 8〜12 を通る余地があります。

実測 driver が未実装のため、現時点で certified 選択・材料レポート・試行台帳の値は生成可能な状態ではありません。

## 実行した検査

- `rg` / `sed` / `nl` による指定文書の読取り: rc=0
- SHA-256 独立再計算: rc=0
- `Draft7Validator.check_schema`: rc=0
- object schema 閉包検査: rc=0
- role/phase、runs、rehash、plannedRun の静的反例検査: rc=0
- `git diff --check`: rc=0
- `git status --short`: rc=0（開始前からの既存変更を確認）
- pytest: **未実行**
- PBS: **未実行**

## 総括

GO/NO-GO: **NO-GO**  
closed 件数 / partial 件数 / regressed 件数: **30 / 6 / 0**（refuted 1 件）  
凍結前に直すべき残り欠陥の件数: **3 件**  
独立再計算の一致件数: **7/7**