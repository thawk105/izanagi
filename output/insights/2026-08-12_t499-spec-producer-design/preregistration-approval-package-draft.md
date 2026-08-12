# 8b oracle 本走 — 事前登録値と承認パッケージ (草案)

**これは草案であり、承認済みの値ではない。** 本 wave は durable artifact を発行せず、
`APPROVED_SPEC_SHA256` を書かず、contract test の期待値を変えない。
承認判断はユーザー手番であり、本文書はその判断材料である。

- 起点: 2026-08-12 ユーザー裁定 [T-499] Q1 = (b)
- 一次資料: `orchestrator/campaign/s8b_oracle_spec.py`, `orchestrator/campaign/s8b_oracle_manifest.py`,
  `orchestrator/campaign/s8b_ratified_freeze.py`, `orchestrator/campaign/s8b_oracle_driver.py`,
  `output/s8b-freeze/holdout_freeze.json`, `output/s8b-freeze/floor_protocol.json`
- 検証: 段 2 プラン子 + 段 3 敵対 2 本 + 親の独立実測が突き合わせ済み (`verbatim/` 参照)

---

## 1. まず結論 — 今ユーザーが承認できるものは何か

事前登録の 9 項目は、**決定権が誰にあるかで 5 つの階層に分かれる。**
「9 項目を承認してください」という形の承認は成立しない。

| 階層 | 項目 | 誰が決めるか | 現状 |
|---|---|---|---|
| (a) 設計選択 | `n`, `master_seed`, block ID, `campaign_ids` | **ユーザー** (AI が草案) | 草案あり、承認可能 |
| (b) (a) から従属 | `block_sizes` | 機械 | `n` と単一 block 契約から一意 |
| (c) validator が 1 値に固定 | `verify`, `screening`, `bench_max_rounds`, `reps`, `extime` | 機械 (承認済み凍結値) | 選択の余地なし |
| (d) active freeze が強制 | `holdout_ids`, `configuration_ids`, `binding_identity` | 機械 (v1 から継承) | 前 2 者は確定、binding は未導出 |
| (e) 実行時 source / 環境が強制 | `generator_versions`, `env_tag`, `clocks`, `contract_sha256`, `ccbench_pin` | 機械 | source 変更で失効する |

**したがって、今この時点でユーザーが実質的に承認できるのは (a) の 4 項目だけである。**
残りは機械が決めるか、前提 (active ratified freeze v2、floor/budget、prepared binary) が
揃うまで導出できない。

---

## 2. (a) 設計選択 — ユーザーの承認対象

### 2.1 `n` (完全ブロック replicate 数)

**草案: `n = 8`**

- 制約: 正整数、かつ `sum(block_sizes) == n` (`s8b_oracle_manifest.py:226,238`)。
- 総試行数は `n × |holdout| × |configuration|` = `8 × 2 × 6 = 96` 行になる
  (`build_schedule:243-263`)。
- 根拠: `docs/phase3-8b-descriptor-design.md` の `N_oracle=8` は**非拘束の planning prior**であり、
  承認済みの値ではない。したがってこれは AI の提案であって既定値ではない。
- **判断材料:** 1 試行あたり `reps=5` × `extime=5` 秒 = 25 秒の測定時間が下限。
  96 行 × 25 秒 = 2400 秒 (40 分) が純測定時間の下限で、build・起動・検証を含めるとこれを超える。
  `n` を倍にすれば検出力は上がるが測定時間も倍になる。

### 2.2 `master_seed`

**草案: `"s8b-oracle-v2-t499-20260812"`**

- 制約: identifier 形式 (`s8b_oracle_manifest.py:228`)。
- 用途: `derive_seed(master_seed, block_id, replicate_index)` で各 replicate の
  cell 並び順を決定論的に shuffle する (`:252-254`)。
- **重要:** seed は結果を見る前に確定しなければならない。結果を見てから seed を変えることは
  事前登録の意味を失わせる (規律 3)。承認時刻を含む文字列にしてあるのはそのため。

### 2.3 block ID と `campaign_ids`

**草案: block ID = `"b0"`、`campaign_ids = {"b0": "s8b-oracle-v2-b0-20260812"}`**

- 制約: manifest の**単一 block 契約**により block はちょうど 1 件でなければならない
  (`_validate_schedule:303-305`)。よって `block_sizes = {"b0": 8}` は `n` から一意に決まる。
- `campaign_ids` は block と一対一、かつ値が重複しないこと (`s8b_oracle_spec.py:147-158`)。
- **未確認:** repo 全体で過去の campaign ID と衝突しないかの機械検査は行っていない。
  発行前に確認が要る。

---

## 3. (c)(d)(e) — 機械が決める値 (承認ではなく確認の対象)

### 3.1 validator が 1 値に固定する値

| field | 値 | 根拠 |
|---|---|---|
| `verify` | `"legacy+s2"` | `s8b_oracle_manifest.py:399` 完全一致 |
| `screening` | `"off"` | 同 `:401` 完全一致 |
| `bench_max_rounds` | `1` | 同 `:415` 完全一致 (generic pipeline の既定 3 とは別) |
| `reps` | `5` | 同 `:417` / `s8b_experiment_numbers.py:15` |
| `extime` | `5` | 同 `:422` / `s8b_experiment_numbers.py:14` |

**これらに選択の余地はない。承認パッケージでは「確認欄」であって「選択欄」ではない。**

### 3.2 active freeze が強制する値

**`holdout_ids = ["rr20", "rr80"]`、`configuration_ids` = 下記 6 件**

```
backoff_fixed_best, ident_all, p2_2_flag_opt, sort_best, stock_common, system_gate
```

これらは**ユーザーの選択値ではなく、有効な v2 freeze から機械的に継承される値である。**

- v1→g1 の transition 許可 pointer 集合に `/holdouts` は含まれない
  (`s8b_ratified_freeze.py:127-133`)。列挙外の pointer が変化・新設・削除されると
  `_assert_transition` が 1 件でも拒否する (`:658-675`)。
- snapshot 検証も v1 の holdout 集合との一致を要求する (`:1044-1049`)。
- manifest 側は spec の `holdout_ids` が active freeze の全 holdout と sorted 完全一致し、
  各 holdout の構成集合が spec と一致することを要求する (`s8b_oracle_manifest.py:1192-1213`)。
  **部分集合を選ぶことはできない。**
- 現 v1 の実値は `output/s8b-freeze/holdout_freeze.json` の `holdouts` から読み取った
  (親が実測)。

**`binding_identity` (12 件 = 2 holdout × 6 構成) は現時点で導出できない。**
freeze entry と prepared binary から `genome_canonical` / `src_token` / `variant_id` /
`entry_sha256` / `binding_sha256` を materializer が導出する必要があり
(`s8b_materialization.py:98-146`)、active ratified freeze v2 と launch validation が前提。
**推測で埋めてはならない。**

### 3.3 `generator_versions` — 承認が自壊する項目

5 本の production source の実 byte hash を pin する (`s8b_oracle_manifest.py:53-61`)。
loader は毎回、実ファイルの hash と spec の値を比較する (`_validate_generators:430-470`)。

| key | path |
|---|---|
| `materializer` | `orchestrator/campaign/s1_direct_comparison.py` |
| `report` | `orchestrator/campaign/s8b_oracle_report.py` |
| `judge` | `orchestrator/campaign/s8b_oracle_judge.py` |
| `outcome_stage_contract` | `orchestrator/campaign/s8b_outcome_stage_contract.py` |
| `artifacts` | `orchestrator/campaign/s8b_oracle_artifacts.py` |

**この 5 本は直近 30 日で 40 commit の変更を受けている** (5 path のいずれかを触った
一意 commit 数。直近 14 日では一意 17 件、path 別の延べ数では 21 件。
数え方で値が変わるため規則を明記する)。

→ **承認した spec は、この 5 本のいずれかが次に変わった時点で失効する。**
値をここに書かないのは、書いた瞬間から陳腐化するためである。
なお「数日で自壊する」は必然ではない。正確には
**「対象 source の次の変更時に、意図どおり fail-closed になる」**であり、
これは silent drift ではなく安全側の停止である。

### 3.4 `ccbench_pin` — 2 つの正しい値があり、選択規則が必要

- 現 floor protocol は `d706650cdb31e442bef45b9b4216951d4fb40969` を記録している
  (`output/s8b-freeze/floor_protocol.json`)。
- 現在の submodule gitlink と `pin.CURRENT_PIN` は `511c9538e4e8efa54b45cda62e72389ed3b706ec`
  (prefix `511c953`) である。**両者は別 commit で、どちらも submodule 内に実在する。**
- manifest validator は `ccbench_pin` を非空 identifier としか検査しない
  (`s8b_oracle_manifest.py:396-404`)。driver は宣言された pin を隔離 worktree へ checkout する。
- 一方、floor 由来の binary hash は実走前に検査され、不一致なら bench 前に abort する
  (`s8b_oracle_driver.py:927-949`)。

**したがって選択規則は次のとおり。**

- 現在の凍結済み floor と比較する本走 → `d706650...` (floor と同じ ccbench でなければ比較できない)。
- floor を `511c953` で再測定して v2 を作る場合 → `511c953` と新しい binary hash を
  新 freeze / spec へ束縛する。
- **両者を混ぜると binary hash mismatch で本走が止まる。**

### 3.5 `env_tag` / `clocks` / `contract_sha256`

| env_tag | clocks_per_us | contract_sha256 |
|---|---|---|
| `pegasus` | 2100 | `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` |
| `linux-baremetal` | 1800 | `1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7` |

- manifest 層は `contract_sha256` を 64hex の**書式**としか検査しない (`:407`)。
- **実値の完全一致は driver 層が行う** — `run_contract.env_tag` は active freeze の `env_tag` と
  一致、`contract_sha256` と `clocks` は env 契約 lookup 結果と完全一致
  (`s8b_oracle_driver.py:860-889`)。
- つまり `env_tag` は自由選択ではなく、**active ratified freeze の `env_tag` が決める。**

### 3.6 `allowed_excluded_reasons`

floor 側の承認凍結 4 件 (`s8b_floor_stats.py:47-53`) は次のとおり。

```
competing_process, launch_failure, nonfinite_or_partial_output, performance_anomaly
```

**ただし oracle の validator はこの 4 件を強制していない。** 非空・重複なしの文字列 list という
形式検査だけである (`s8b_oracle_spec.py:171-177`, `s8b_oracle_manifest.py:736-744`)。
report 側は `excluded_reason` が承認リストに無ければエラーにする
(`s8b_oracle_report.py:386-390`)。

→ **「floor 由来だから oracle でも正しい」は validator からは導けない。**
oracle の除外理由表は独立に承認され、driver の failure event・trial-result・judge outcome・
report exclusion の対応が 1 行ずつ定義される必要がある。これは別タスク。

### 3.7 `schedule_sha256`

上記が全部決まってから `build_schedule` の出力に対して再計算する導出値。
loader も同じ再計算との完全一致を要求する (`s8b_oracle_spec.py:131-137`)。手で書く値ではない。

---

## 4. 承認しても本走は始まらない — 先行 blocker

**spec を承認すれば manifest candidate → 本走へ進む、という筋書きは成立しない。**

1. **active ratified freeze v2 が存在しない。** live pointer が無ければ `no-active` で拒否される
   (`s8b_ratified_freeze.py:1214-1256`)。`build_approved_manifest` は spec より**先に**
   active freeze を読むため、spec を承認してもここで止まる (`s8b_oracle_manifest.py:1170-1188`)。
2. **floor / budget が null。** driver は floor か budget が null なら v2 実走を拒否する
   (`s8b_oracle_driver.py:469-472`)。
3. **official guard ([T-088]) が未解禁。** pilot 成果物は `eligible_for_refreeze=false` のため
   再凍結に使えない (`docs/phase3.md:118-122`)。
4. **`BUDGET_APPROVAL_SHA256 = None`** (別途 [T-499] (B) の対象)。

→ 現在の先行 blocker は `no-approved-spec` ではなく **`no-active-ratified-freeze`** である。
spec 承認はこの列の最後尾に近い。

---

## 5. 承認パッケージの構成 (最終承認時にこの形で提示する)

最終承認は、以下が**すべて揃った後の 1 回**に限定する。

1. **承認対象と非対象** — 何を承認し、何を承認しないか。本承認は本走開始の許可ではないこと。
2. **設計選択値** — `n` / master seed / block ID / campaign ID。各項に採否欄。
3. **freeze から継承される値** — active generation・pointer・freeze SHA、holdout/構成の全集合、
   12 件の binding identity とその再計算結果。**選択欄ではなく確認欄。**
4. **実行環境契約** — `ccbench_pin` (§3.4 の選択規則を明記)、`env_tag`、`contract_sha256`、
   `clocks`、`reps`、`extime`、`verify` / `screening` / `bench_max_rounds`。
5. **除外理由表** — oracle 独自に承認する閉じた理由集合と、driver event との対応表。
6. **再現性資料** — canonical JSON bytes 全文、その SHA-256、schedule の一覧と schedule SHA、
   generator 5 本の path と hash、strict loader・canonical 化・full validator の静的検査結果。
   **実走していない検査はそう明記する。**
7. **provenance** — 承認 ID、承認者、承認 scope。
   **現行の code pin も receipt も、同じ実装担当がすべて作成できる** ため、
   これだけでは人間承認を機械強制しない。AI が書けない外部 trust root が要る
   (`producer-design.md` §2.1)。
   **T-810 は先例にならない** — その artifact 自身が
   `approval_receipt_trust_root_absent = True` を宣言し、launch には正例が存在しない
   (`orchestrator/campaign/t810_preregistration.py:434-458,798-803`)。
8. **承認後に起きること** — 別タスクで producer / gate を実装 → exact bytes と pin を単一 commit で
   発行 → 関連テスト実測 → manifest candidate 生成 → full verify → そこで初めて本走判断。
9. **誤承認時の故障モード** — `n`・seed の誤りは検出力と事前登録の意味がずれる。軸の誤りは
   `cell-product-mismatch` で停止。binding の誤りは spec loader / launch validation で停止。
   source hash の誤りは generator byte 検査で停止。run contract の誤りは driver が本走前に停止。
   除外理由の誤りは裁量的除外の余地を作る。provenance の誤りは「誰が何を承認したか」を
   証明できなくする。
10. **有効期間と失効条件** — 下記 §6。

---

## 6. 承認の有効期間 (これを書かない承認パッケージは不完全)

承認された spec が有効なのは、**次のすべてが承認時 snapshot と一致している間だけ**である。

- generator 5 source の byte hash
- active ratified freeze の generation と pointer
- floor artifact (と、そこから決まる binary hash)
- 実行環境契約 (`contract_sha256`, `clocks`)
- `ccbench_pin`
- exact spec bytes

**どれか 1 つでも変われば expired** であり、再導出と再承認が要る。
特に generator 5 source の改修速度 (§3.3) を踏まえると、

> **最終承認は「この 5 本の改修が実質的に止まってから」でなければ意味を持たない。**

これは [T-499] Q1 = (b) の判断 (承認手番を今引く) を独立に裏づける事実である。

---

## 7. 本 wave で行っていないこと

- `output/s8b-oracle-spec/` および `output/s8b-oracle-manifest-candidates/` への書込 (0 byte)
- `APPROVED_SPEC_SHA256` の設定 (`None` のまま)
- contract test の変更
- pytest / producer / floor / oracle の実走
- campaign ID の repo 全体での衝突検査 (未実施と明記)
