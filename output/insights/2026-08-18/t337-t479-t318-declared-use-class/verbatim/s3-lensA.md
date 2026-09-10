実施範囲: 必読資料と指定ソースを静的確認。pytest、編集、commit、ネットワークは未実施。`test_check_docs.py` は未読。

### 1. 必須引数化だけでは恒真防壁になる（real）

- 判定: `real`
- 根拠:
  - 現状の通る正例は `orchestrator/tests/test_campaign.py:8408-8425`。引数省略が `orchestrator/campaign/loop.py:132` の `official` 既定値で通り、同 `:168-180` で official root が作られる。
  - 計画後に同じ省略を落とす負例は妥当だが、未実施である。
  - 呼出し側が `DECLARED_USE_CLASS = "official"` を機械的に渡せば必須引数は満たす。計画も定数を registry/meta に置くと明記している (`s2-plan.md:9-15`)。
  - `test_p3_exploration_namespace.py:223-381` は `run_campaign` を monkeypatch しており、実 sink の検査ではない。同 `:430-465` も AST 検査だけである。
- 成果物影響: 宣言なしの直接呼出しだけは落ちるが、未登録 producer の official 自己申告は通り、受理集合と official 材料レポートへの到達可能性が広がる。
- 推奨: 裁定へ

### 2. `official` 自己申告が受理集合を広げる（real）

- 判定: `real`
- 根拠:
  - `loop.py:162-180` は class の由来を検証せず、`official` なら `campaign_layout` を選ぶ。
  - D162 は caller の自己申告を semantic gate としない (`docs/decisions.md:8010-8016`)。
  - D123 は official root に marker が無くても受理する穴を残す (`docs/decisions.md:6008-6010`)。
  - よって exploration 相当の新 producer が `"official"` を宣言すれば、official output へ入れる。`qualification` と `dry` の拒否はこの経路を防がない。
- 成果物影響: official root に出た未検証出力が downstream の certified selection、材料レポート、proof chain の入力候補になり、受理集合が広がる。
- 推奨: 裁定へ

### 3. 旧 `campaign_namespace` を残すと宣言を迂回できる（real）

- 判定: `real`
- 根拠:
  - 現行 API は `campaign_namespace` を受け付ける (`loop.py:123-167`)。
  - 新しい `declared_use_class` と旧 selector を同時に残す実装なら、`declared_use_class="exploration", campaign_namespace="official"` のような不一致を旧 selector が決める。
  - 既存の official 省略経路は `test_campaign.py:8408-8425` に固定されている。
- 成果物影響: 宣言値と実際の output namespace が乖離し、探索出力を official 材料へ送ることで proof chain と受理集合が変わる。
- 推奨: 採用（旧 selector の削除と不一致拒否をプランに明記）

### 4. `qualification` / `dry` の直接受理拡大は計画上は反証される（refuted）

- 判定: `refuted`
- 根拠:
  - `s2-plan.md:21-32` は official/exploration だけを sink に許し、qualification/dry を layout と cid の前に拒否する。
  - D162 は qualification を「qualification へ提出する意図」とし、合格を意味しない (`docs/decisions.md:8010-8016`)。
  - D500 も dry を qsub 免除にしない (`docs/decisions.md:20738-20742`)。
  - ただし、実装時には `ValueError` だけでなく cid、directory、report が未生成であることを負例にする必要がある。
- 成果物影響: この拒否が実装されれば certified selection と材料レポートの受理値は不変で、漏れれば二つの追加 namespace が受理集合を広げる。
- 推奨: 採用

### 5. path は概ね不変だが、source freeze が proof chain を止める（real）

- 判定: `real`
- 根拠:
  - 既存の公式 root は `layout.py:168-225`、探索 root は同 `:430-487` に固定されている。
  - 5 producer の既存呼出しは `p3_kickoff.py:111-121`、`p3_s4_loop.py:958-962`、`p3_s4_red.py:168-181`、`p3_s4_loop_sort.py:328-332`、`p3_s4_loop_trigger_gating.py:640-648` にある。
  - `s1_known_axes_freeze.py` の glob/join は `:338-340`、`:373-375`、`:426-430`、`:459-462`、`:527-530`。path の探索規則自体は新 namespace を見ない。
  - `output/campaigns` は Python 194 hit、16 file。16 file は guard、plotting、freeze、layout、`s1_expected_goldens.py`、`test_campaign.py`、layer3、artifact admission、Pegasus、critic 等を全て確認した。`output/exploration` は6 file、35 hit。
  - しかし凍結3 artifact は `p3_s4_loop_sort.py` の path と SHA を保持する (`output/s1-freeze/known_axes_freeze.json:205-207`, `measurement_freeze.json:232-234`, `output/s8b-freeze/holdout_freeze.json:191-193`)。検証は `s1_known_axes_freeze.py:842-856` で source bytes を SHA 比較する。
  - 記録値 `9b64f34...67dbf4` に対し、現 checkout の同ファイルは `9a27a97...89e3c` だった。これは既存の不一致だが、計画通り同ファイルを編集すれば source pin はさらに不変ではなくなる。
- 成果物影響: output bytes が変わらなくても freeze verifier が停止し、proof chain と certified selection の受理が失敗する。
- 推奨: 裁定へ

### 6. campaign-id への宣言漏洩は静的には無い（refuted）

- 判定: `refuted`
- 根拠:
  - canonical preimage は `ident.py:151-179` の spec、commit、search config、trial だけで、id は同 `:187-190` から導かれる。
  - `CampaignConfig` に declaration field は無い (`model.py:66-84`)。
  - 同一 cfg の official/exploration で id が同じことを固定する既存検査が `test_campaign.py:8499-8521` にある。
- 成果物影響: この分離を維持すれば歴史 campaign の id、proof chain、既存 certified selection は不変である。
- 推奨: 採用

### 7. 族の切離しは未達で、5個と6個の集合がずれている（real）

- 判定: `real`
- 根拠:
  - D123 の族は5つの `run_campaign` producer だけでなく、`p3_autonomous_workload_trial.py` を含む6 driver である (`docs/decisions.md:5991-5996`)。
  - テストの `_DRIVERS` は手書き tuple のままで、`_CAMPAIGN_DRIVERS = _DRIVERS[:-1]` という位置依存除外である (`test_p3_exploration_namespace.py:39-47`)。
  - autonomous driver は直接 exploration layout と output を使う (`p3_autonomous_workload_trial.py:2831`, `:3446-3456`, `:3768`, `:3789-3792`)。これは `run_campaign` 必須引数化の対象外である。
- 成果物影響: tuple 外または直接 layout を使う新 producer は namespace gate を通らず、official 相当の path と受理集合を得る余地が残る。
- 推奨: 裁定へ

### 8. 親 brief の数値は分母を明記しないと結論が変わる（real）

- 判定: `real`
- 根拠:
  - raw `run_campaign(` は 199 hit、18 file。定義2件 (`loop.py:123`, `s8b_floor_campaign.py:5585`) と test helper 定義2件を除くと、計画の195件 = production 16、test 179になる。
  - 実際に `orchestrator.campaign.loop.run_campaign` を AST で数える移行対象は production 15、test 30であり、195件全てを一括変更する話ではない。
  - production Python の `declared_use_class` hit は0だが、schema には既存 field と4値 enum がある (`output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:1225-1248`)。
  - 「既存被覆0」は新しい omission-fail の被覆が0という意味なら正しいが、現状には省略を official として固定する正例 (`test_campaign.py:8408-8425`) がある。
  - 「production 5 driver」は `run_campaign` 呼出し数としては正しいが、D123 の族は6である。
- 成果物影響: 移行対象を15+30と認識し損ねると未変更 caller が TypeError または official fallback になり、受理集合と完了証拠が変わる。
- 推奨: 採用（測定値を分母付きで修正）

### 9. 9層には別プロトコルの実体があるが、RF実体ではない（real）

| 層 | 再測した実体 | 判定 |
|---|---|---|
| measurement producer | `campaign/pipeline.py:592-616,1237-1311`、`qualification/collector.py:1118-1138,1314-1355`。campaign evaluation と T126 receipt | `real`、RFではない |
| attempt registry | `qualification/attempt_ledger.py:312-373`、floor の private retry ordinal `s8b_floor_campaign.py:4592-4615` | `real`、T126/floor用 |
| schedule validator | `s8b_oracle_manifest.py:278-318`、呼出し `s8b_oracle_driver.py:325-344` | `real`、oracle用 |
| RF calculator | `qualification/contract.py:1-6,332-353`、series FSM | `real`、T126 relative calculator |
| eligibility authority | `s8b_floor_stats.py:682-706` は live admission を保証しない。oracle judge は `s8b_oracle_judge.py:465-505,680-710` | `real`、RF authorityではない |
| layer3 next version | `layer3_report.py:46-48,576-580`。certified-selection consumer は無い | `real`、future fail-closed |
| selector consumer | `s8b_selector_input.py:102-136` と oracle judge | `real`、RF selectorではない |
| material report consumer | `layer3_report.py:430-436,500-517`。qualification lineage を拒否 | `real`、RF material consumerではない |
| bijection / mutation | `layer3_report.py:217-234`、`test_layer3_report.py:1605-1629`、`test_s8b_oracle_report.py:2829-2840,3033-3042` | `real`、別protocolの検査 |

- 成果物影響: これらをRF被覆と誤認すると certified selection、材料レポート、proof chain の完成値を過大報告するが、D500どおりこのwaveの受理値は変えてはならない。
- 推奨: 裁定へ

## 総括

必須引数化は省略を落とすが、producer の official 自己申告は防がない。  
旧 selector の残置、monkeypatch runtime test、手書き tuple が恒真性の主穴である。  
path の実装は概ね維持されるが、`p3_s4_loop_sort.py` の凍結 source pin は不変主張を破る。  
campaign-id の preimage 分離は守られている。  
D123 の6 driverと計画の5 producerには外延差がある。  
9層は別protocolとして実在するが、D500のRF実装ではない。  
land 前に自己申告の信頼境界、freeze repin、autonomous の扱いを裁定すべきである。