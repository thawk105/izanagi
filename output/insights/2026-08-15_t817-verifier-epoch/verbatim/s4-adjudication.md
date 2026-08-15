# 段 4 裁定 — [T-817] verifier epoch 実装 wave

2026-08-14 01:55 JST / base = main `849d3d59` (wave 中に `43ac2d67` から ff 取り込み済み)

## 0. 結論

**実装へ進む (段 5)。** Q1・Q2・Q3・Q4 をすべて本 wave で満たす。
段 2 プランの「Q4 は凍結再発行が必要なので段 4 で停止」は、**親の実測で refuted**。
ただしレンズ A の blocker 1 (verifier 実装が epoch の束縛外) は **real** であり、
その完全な解消は scope 外として裁定パッケージへ返す。

## 1. 所見の裁定表

| # | 所見 (出所) | 判定 | 採否 | scope |
|---|---|---|---|---|
| F1 | 8-path authority に **verifier 実装 (`orchestrator/verifier/*`) が入っていない**。同じ epoch のまま `VerifyResult.certified` を常時真へ倒せる (レンズ A blocker 1) | **real** | 部分採用 | 名称・記述の正直化は scope 内。closure 拡張は **scope 外** → 裁定パッケージ |
| F2 | `purpose` は自己申告であり、history view を certified 選択へ戻せる (レンズ A blocker 2) | **real** | 採用 | scope 内。**非互換な 2 型**に分離する |
| F3 | consumer 集合がプランの 10 経路より広い — `s6_sort_sweep` / `s8a_trigger_sweep` / `backoff_sweep_report` / `autonomous_trial_completeness` / p3 loop 群 / `tools/plotting/plot_backoff.py` (レンズ A 所見 4、レンズ B 所見 1・2・4・5) | **real** | 採用 | scope 内。全件を分類して purpose を通す |
| F4 | 「E0 = 30/30」は**ラベル数**であり、純減は 21 件 (3 件 overlay deny + 6 件 legacy trigger は既に拒否) (レンズ A 所見 5) | **real** | 採用 | scope 内。epoch 判定は**既存 admission の後段**に置き、既存 9 件の拒否理由・overlay 参照を保存する |
| F5 | `E1-stale` 判定が live bytes 依存で、作業ツリーの 1 byte 編集が受理集合を変える (レンズ A 所見 6) | **real** | 採用 | scope 内。**certified 側は dirty/取得不能を fail-closed**、歴史表示は**記録 epoch のみ**で決定的にする |
| F6 | 保存済み certifying report に epoch が残らず、後から世代を監査できない (レンズ A 所見 7) | **real** | 採用 (限定) | scope 内。**certifying な出力にだけ** epoch を必須化。既存 `as_receipt()` の exact schema は変えない |
| F7 | S8b は report/judge/artifacts が bytes pin されており凍結再発行が要る → 停止 (段 2 プラン §4、レンズ A blocker 3、レンズ B) | **refuted (コスト面)** | 不採用 | 下記 §2 の実測による |
| F8 | S8b には未 pin の共通入口が無く、report/judge 本体を編集するしかない (レンズ B) | **real** | 採用 | scope 内。編集面を report/judge/artifacts に確定する |

## 2. F7 を refuted とした実測 (親が独立に測定)

段 2 プランとレンズ 2 本は「pin されている = 凍結再発行が要る」と等置したが、**pin の実体を測ると
成立しない**。

- `orchestrator/campaign/s8b_oracle_spec.py:23` = `APPROVED_SPEC_SHA256: Optional[str] = None`
  (「approval 不在で常に fail-closed」とコメント自身が明記)。approved spec による公式検証は
  **現時点で production では発火しない**。テストは monkeypatch で合成 approval を注入している
  (`test_s8b_oracle_report.py:261` 他)。
- `output/s8b-oracle-spec/reviewed_spec.json` は**存在しない** (ls で不在)。
- `orchestrator/tests/test_frozen_artifacts.py:41-89` の `FROZEN_MANIFEST` (23 件) に
  s8b oracle manifest / reviewed spec は**含まれない**。含まれるのは
  `output/s1-freeze/*`・`output/s8b-freeze/*`・2026-07-16 の insights だけである。
- `output/s8b-freeze/*` と `output/s1-freeze/*` は `s8b_oracle_report.py` /
  `s1_direct_comparison.py` を**参照していない** (grep 0 件)。
- **決定的証拠**: 本 wave 進行中に main へ入った [T-971] (`80caf743`) が、同じ
  `_GENERATOR_SOURCES` の pin 対象 `orchestrator/campaign/s1_direct_comparison.py` を編集し、
  `test_s8b_oracle_manifest.py` の golden literal (`PIN_GATE_SPEC_SHA256` /
  `PIN_GATE_SPEC_RAW`) を**機械的に貼り直して land 済み**。凍結再発行の裁定は取っていない。

→ S8b の編集コストは**テスト golden 1 箇所の再 pin**であって、凍結成果物の再発行ではない。
`FROZEN_MANIFEST` の 23 件の bytes は 1 bit も変わらない。よって **Q4 は本 wave に収まる**。

## 3. F1 の裁定 (最も重い所見)

**実測で確認した (親)**: 正しさ判定の実体は `orchestrator/verifier/{core,dsg,model,parse}.py` にあり
(`pipeline.py:29` が `verify_trace_dir` を import)、これらは
`campaign_lock.py:29-38` の exact 8 path に**含まれない**。したがって v2 authority へ束縛した epoch は
「verifier 実装の同一性」を保証しない。

- **scope 内 (本 wave で行う)**: epoch が束縛するものを**過大に名乗らせない**。
  epoch の導出・表示・診断は「enforcement source closure (8 path、witness gate 本体 `pipeline.py` を
  含む) の同一性」であることを、コードの docstring・構造化診断・report field で明示する。
  E0 の意味は「**この closure の下で検証されていない記録**」に限定して記述する。
- **scope 外 (裁定パッケージへ返す)**: `CONTRACT_LOADER_RELATIVE_PATHS` へ verifier source closure を
  加えて実際に束縛を広げること。理由 = (a) authority の**契約自体の変更**であり、裁定 Q3 (a) の
  「既存 authority へ束縛する」を超える、(b) 並走中の別タスクが manifest schema を触っている、
  (c) 実 corpus に v2 lock が 0 件なので緊急性は無い (壊れる既存成果物が無い代わりに、
  今すぐ入れる利得も将来 run にしか及ばない)。
- 名称は裁定文が固定した `campaign_verifier_epoch` を使う (親が独断で改名しない)。
  名称と束縛範囲の乖離は、上記の明示と裁定パッケージで扱う。

## 4. 確定した設計 (プラン v2)

1. **epoch 導出** — `artifact_admission.py` 内。v2 authority の
   `contract_loader_blob_sha256s` (exact 8 path map) から導出。新 module・新 JSON artifact・
   新 lock field を作らない。`IDENTITY_KEYS` / `AUTHORITY_KEYS` / `V2_KEYS` /
   `CONTRACT_LOADER_RELATIVE_PATHS` / `search_config` は不変。
   - `E0` = `authority is None` (v1 lock)
   - `E1` = v2 authority が記録 commit に対して有効、かつ記録 map == 現在 map
   - `E1-stale` = v2 だが記録 map != 現在 map、**または現在 map を取得できない**
     (理由 code を `current-closure-unavailable` として区別する)
2. **除外の適用点** — 中央 1 箇所。`require_admitted_campaign` に `purpose` を**既定値なしの必須
   keyword** で追加する。F2 のため、返り値を**非互換な 2 型**に分ける:
   - `CertifiedCampaignView` (purpose=`CERTIFIED_ACCEPTANCE` のときだけ返る。E0 / E1-stale は拒否)
   - `HistoricalCampaignView` (purpose=`HISTORICAL_RAW`。拒否せず epoch を保持)
   certified consumer は `CertifiedCampaignView` **型でしか**受け取れないようにし、
   自己申告だけで history を certified 選択へ流せないようにする。
   既存 `AdmittedCampaign` 型名は互換のため残してよいが、certified 判定は新型で行う。
3. **順序 (F4)** — epoch 判定は**既存 admission 判定の後段**に置く。overlay deny 3 件と
   legacy trigger 6 件は従来どおりの理由・overlay 参照で拒否し、epoch 理由へ書き換えない。
4. **決定性 (F5)** — 歴史側の表示は**記録 epoch のみ**から決まる。現在 closure との比較は
   certified 側の判定にだけ使い、取得不能・dirty は certified を fail-closed で拒否する。
5. **S1 (プラン §2 の lock-only API)** — `s1_report.py` は WAL 破損行も構造化証拠として集める
   必要があるため、WAL 全体を先に拒否する経路へは載せない。同じ中央条件式を使う lock-only API を
   使い、適用点は二重化しない。
6. **S8b (Q4)** — `s8b_oracle_report.py` が実 `output_root` を解決した直後に epoch を検査し、
   observations へ epoch と拒否状態を投影する。`s8b_oracle_judge.py` は E1 以外を eligible に
   しない。`s8b_oracle_artifacts.py` の observations schema を対応させ、
   `test_s8b_oracle_manifest.py` の golden literal を再 pin する。
   **`FROZEN_MANIFEST` の 23 件と `output/s8b-freeze/*` の bytes は変えない。**
7. **certifying 出力の epoch (F6)** — `layer3_report` の accepted report など certifying な出力に
   epoch を必須化する。既存 `CampaignAdmissionDecision.as_receipt()` の exact schema は変えず、
   既存の保存済み文書は optional として読めるままにする。
8. **plot_backoff (F3)** — 中央 API 経由へ移す。`HISTORICAL_RAW` で読み、図の provenance へ
   epoch を出す。certified を名乗る winner 表記をしない。

## 5. consumer 分類 (確定)

| consumer | 分類 | 根拠 |
|---|---|---|
| `replay.load_landscape` / `assert_complete` | **certified 受理集合** | `certified` 全件 true を要求する |
| `guided` | certified (replay 継承) | replay gate より前へ進めない |
| `search_baselines` | certified (replay 継承) | `assert_complete` 経由 |
| `s1_report` | **certified 受理集合** | certified sample を hard gate へ入れる |
| `layer3_report.build_accepted_report` | **certified 受理集合** | certifying 入力 |
| `layer3_report.build_report` | 歴史生値 | `certifying_input=false` の歴史射影 |
| `s8b_oracle_report` / `s8b_oracle_judge` | **certified 受理集合** | official observations / verdict |
| `s6_sort_sweep` / `s8a_trigger_sweep` | **certified 受理集合** | best / rank / backstop を出す |
| `backoff_sweep_report` | **certified 受理集合** | `best_static` と sweet-spot verdict を出す |
| `autonomous_trial_completeness` | **certified 受理集合** | 台帳の完了判定に admission receipt を渡す |
| p3 loop 群 (`p3_s4_loop` 他) | **certified 受理集合** | 次 iteration の選択入力 |
| `p2_2_report` | 歴史生値 | `certified` を見ず committed + median で winner を出す (歴史解析) |
| `critic/digest` (P2 既定経路) | 歴史生値 | committed throughput の歴史解析 |
| `critic/digest` (Phase 3 `--campaign-dir`) | **certified 受理集合** | 選択入力 |
| `s1_known_axes_freeze` | 歴史生値 (**編集しない**) | 凍結 producer。bytes pin のため不変 |
| `tools/plotting/plot_backoff.py` | 歴史生値 | 図の材料。epoch 表示を付ける |

## 6. 事前登録変異 (DW-M01 / B-057)

実装前に登録する。各変異は「同じ入力を拒否する層が前後に無い」「無効化時の赤理由が一つ」を
実装後に確認してから本走する (DW-M07)。**期待 node の完全集合は fix 後に再導出する。**

| ID | 位置 | 変異内容 (wave 前の実コードの形を含む) | 期待 |
|---|---|---|---|
| MUT-1 | 中央 gate (`artifact_admission.py`) | certified purpose での epoch 拒否を**削除**し、wave 前と同じく epoch 検査なしで view を返す | KILLED — 実在 E0 負例 |
| MUT-2 | epoch 比較 | 記録 map と現在 map の **exact equality を key 集合比較へ緩める** | KILLED — E1-stale fixture |
| MUT-3 | 型分離 | certified consumer が `HistoricalCampaignView` も受け取れるよう型検査を外す | KILLED — 型分離テスト |
| MUT-4 | 中央 gate | **全 purpose で無条件拒否** (過剰拒否) | KILLED — E1 正例 + 歴史生値の非拒否 |
| MUT-5 | 順序 (F4) | epoch 判定を既存 admission の**前段**へ移す | KILLED — overlay deny 3 件の理由保存テスト |
| MUT-6 | S8b judge | E1 以外を eligible から外す条件を削除 | KILLED — s8b oracle judge テスト |
| MUT-7 | 決定性 (F5) | 歴史表示を現在 closure 依存にする | KILLED — 歴史表示の決定性テスト |

**正例 (過剰拒否検出)**: 合成 v2 lock の E1 fixture が certified を通ること、実在 E0 が
`HISTORICAL_RAW` では通り epoch が表示されること。

**発火の実在 (恒真でないこと)**: 負例は合成でなく**実在 artifact**
`output/campaigns/p2-2-silo-read-heavy-enumerate-5ffcabad` (v1 lock、現行 admission を通る) を使う。
これにより「既存 admission を通る記録が、新 gate だけで落ちる」ことを示す。

## 7. 実装単位 (段 5、所有は素集合)

| 単位 | 所有ファイル | 順序 |
|---|---|---|
| **A** | `orchestrator/campaign/artifact_admission.py`、`orchestrator/tests/test_artifact_admission.py` | 先行 (API 確定) |
| **B** | `replay.py`、`guided.py`、`search_baselines.py`、`p2_2_report.py`、`critic/digest.py`、`backoff_sweep_report.py`、`s6_sort_sweep.py`、`s8a_trigger_sweep.py` と対応 test | A の後、並列 |
| **C** | `s1_report.py`、`layer3_report.py`、`layer3_schema.json` と対応 test | A の後、並列 |
| **D** | `s8b_oracle_report.py`、`s8b_oracle_judge.py`、`s8b_oracle_artifacts.py`、`test_s8b_oracle_*.py` | A の後、並列 |
| **E** | `p3_s4_loop*.py`、`p3_autonomous_workload_trial.py`、`autonomous_trial_completeness.py`、`tools/plotting/plot_backoff.py` と対応 test | A の後、並列 |

**編集しない**: `campaign_lock.py`、`ident.py`、`s1_known_axes_freeze.py`、
`output/s1-freeze/*`、`output/s8b-freeze/*`、`external/ccbench`、既存 WAL。

## 8. 裁定パッケージへ返す項目 (scope 外の real 所見)

1. **F1**: `CONTRACT_LOADER_RELATIVE_PATHS` に verifier source closure
   (`orchestrator/verifier/{core,dsg,model,parse}.py`) を加え、epoch が実際に verifier 実装を
   束縛するようにするか。現状は「enforcement closure の同一性」までしか保証しない。
   実 corpus に v2 lock が 0 件のため、壊れる既存成果物は無い。
2. **T-834 の残余**: 本 wave で 16 経路を分類したので、[T-834] は本 wave の分類表で閉じられる
   見込み (段 7 で記帳)。
