## 所見

### 1. real — 五 probe の成功が、非 `invalid` 結末への到達を保証していない

- **主張:** プランに明記された受入条件では、全 cohort を `invalid` にする回帰を排除できない。これは実装済み欠陥の指摘ではなく、検査計画の不足である。
- **根拠:** `04-plan.md:138–209` の五 probe は、設定の消費、整数保存、出所、五本の発行、mode 一致を確認する。一方、`analyze_cohort` は同 `:25`、解析テストは同 `:129` に挙がるだけで、**異なる三 workload の完全な入力から期待する非 `invalid` verdict を得る正例**が明記されていない。親 brief の完了判定は五 probe の成功である。
- **壊れ方:** 五条件を満たす記録を発行する実装に、解析結果を常に `invalid` にする変異を加える。明記された五 probe の確認項目は依然満たせるのに、正常 cohort の結末が失われる。workload 座標まで三 job 同一性に含める T-2500 型の変異も、この不足を突く。
- **深刻度:** **must-fix**。
- **必要な修正:** production writer・admission・loader・`analyze_cohort`・materializer を結んだ完全な三 campaign の試験入力を用意し、期待 verdict を literal で検査する。同じ入力に workload 同一化要求を加える変異、または常時 `invalid` 変異が、確実に落ちることを確認する。

### 2. real — 親の実測記述に、最初の cell の値を走全体へ広げた表現がある

- **主張:** 主要三前提は正しいが、数値と型の記述は修正が必要。
- **根拠:** `02-measured-premises.md:27–32` は `tps` を「浮動小数」、abort 率を「この走では 0.6869」、正しさ counter を「この走では 630878 / 240566」と記す。balanced の実 WAL では、五 cell の代表 abort 率は **`[0.6869, 0.0404, 0.211, 0.0145, 0.0268]`**。最初の throughput 配列は **`[3958382,3752160,3727702,3692363,3695293]`** と整数表記で保存されている。正しさ counter も cell ごとに異なる。
- **壊れ方:** この説明を型契約として転記し、throughput に exact float を要求すると、実在する正常な整数表記の throughput が拒否される。ただし、現在のプランは正値・有限性を要求しており、この誤実装を指定してはいない。
- **深刻度:** **nit**。

## 正常な走行が到達できる結末の確認

**非 `invalid` に到達する完全な実成果物は、今回の入力からは示せない。到達不能と判明したわけでもない。**

確認できた部分は次のとおり。

- 探索三 lock の workload/read ratio は、それぞれ `balanced/50`、`read-heavy/95`、`write-heavy/5`。一方、CCBench commit は共通の `511c953`、環境契約 digest も共通の `e576e9cd…e242c01`。**workload が異なり、共有条件が一致する組は実在する。** ただし、これだけで本走の全同一性 field の充足は証明できない。
- `certified=true`、`verdict="serializable"`、`anomalies=0`、`workload={"tag":"legacy"}` の verify 記録は実在する。プラン `:34` は権威を正しく選んでおり、report の `certified=false` による全件拒否という攻撃は **refuted**。
- `pipeline.py:2151–2156` は指定回数を逐次実行し、失敗時に即 return する。`:2406` は反復数分の receipt tag を保持する。プランはこの機構を五反復へ配線するため、反復数を減らす設計という攻撃は **refuted**。
- 保存 stdout `output/env/pegasus/t139-r4-env-probe/0:896504.nqsv/run-R01.log:13–21` には、整数 counter `24435129 / 2270481`、印字率 `0.9150`、throughput `756827` が実在する。整数 parser が要求する字句形式は到達可能である。
- 丸め値 fallback は、プラン `:51–55,98,160–163` が専用 parser・整数比・印字率変更への不変性で明示的に排除する。既存 `benchparse.abort_rate()` を解析へ再利用する計画という攻撃は **refuted**。

数学的には、全 cell で同じ正の整数比を五回観測し、throughput も一定なら、CV gate を通り、正値・分散ゼロの規則から `indeterminate-in-region` に到達できる。ただし、これは**構成例**であり、完全な formal campaign の実在証明ではない。所見1の試験で、その差を埋める必要がある。

## 既存 3 系列が不変である証人

**受理集合・成果物・値の完全な不変性は、現段階では示せない。** 次の既存テストは、範囲を限定した証人になる。今回は実行していない。

| テスト名 | 証明する範囲 |
|---|---|
| `test_mu1_extended_grid_semantic_golden_except_registered_upper_endpoint` | extended 格子の意味対応 |
| `test_mu2_grid_upper_endpoint_matches_adaptive_range` | 格子上端 |
| `test_t2266_grid_is_exact_eight_points_with_physical_1000_encoded_as_3000` | t2266 の点集合・符号化 |
| `test_t2418_exact_grid_identity_order_and_disclosure_are_literal_pinned` | t2418 の格子・identity・順序・開示値 |
| `test_t2418_v2_discovery_does_not_select_v1` | v1/v2 discovery の分離 |
| `test_t2418_frozen_campaign_is_rejected_by_existing_t2266_consumer` | 系列を取り違えた入力の拒否 |
| `test_t2266_real_rep_capture_flows_through_wal_consumer_for_every_rep` | runner/parser/capture と report 値の対応 |
| `test_t2418_frozen_wal_view_flows_through_capture_loader_and_reports` | t2418 の rep 値・report schema・開示 |
| `test_measure_point_wrapper_preserves_value_exception_and_out_parameters` | 通常 runner の値・例外・出力引数 |

最後から三つ目・二つ目の限界は明確である。`test_backoff_extended_sweep.py:294–359` などで、verify・bench・commit 記録と admission decision を手組みしている。**実 `_run_bench` の発行値と admission 全体まで通した証人ではない。**

実呼出し経路は、既存 driver `backoff_extended_sweep.py:1446` → `run_campaign` → `evaluate` → `_run_bench` → `measure_point`。t2266/t2418 はさらに capture を挟む。したがって共有 file の変更は既存系列の値へ届く。

ただし、プランどおり非既定時だけ引数・sink・整数 parser を追加し、旧 `abort_rate()` を維持すれば、**指定された変更に旧値を変える必然性はない**。受入時には key 集合だけでなく、この旧経路の発行値も確認すべきである。

## 親 brief と実測前提への反証

主要三点への反証は**無し**。

balanced 実 WAL は25行、各 stage 五本、各 variant の verify は一本、mode はすべて `{"tag":"legacy"}`。探索 root の73 file に `abort_counts_` / `commit_counts_` の検索一致は無かった。

補足・訂正は以下。

- 数値と throughput 型の一般化は所見2のとおり。
- JSON 行全体の key は `env_tag,payload,stage,ts,variant` の五つ。「四つ」は payload を除いた envelope の意味に限定すれば正しい。
- counter を含む保存 stdout を探索 root から供給できるという前提は成立しない。ただし、検索結果だけから「stdout 類が一切存在しない」とまで一般化しない。
- manual-build 在庫の一般化へのプランの反論は正しい。`test_p3_build_authority_cli.py:1217–1223` は `--build` を含む file を抽出している。
- runner の片側アンカーという反論も正しい。通常 `measure_point` は `runner.py:1064` 以降に別実装がある。
- 同居関係文書は `docs/test-environment-coincidence-ledger.md:326–329` に明記された過去 wave の先送り一覧であり、常設登録簿ではない。
- 五 probe は投入前条件の実装経路を示す。実投入時の環境条件・時間枠・cohort 完備性まで充足した証拠にはならない。

## 総括

正しさ五反復、anomaly 即 reject、認証の権威、整数由来の解析を緩める明示的設計は見つからなかった。  
T-2500 型の到達不能を検出する、完全な三 campaign の非 `invalid` 正例が受入計画に不足している。  
既存テストには有効な部分証人があるが、三系列全体の不変性を一括して証明するものではない。  
規律7に反して過去測定を現行コードとの差だけで無効化する指定は見つからず、事前登録・resume の束縛も維持されている。  
実装前に所見1を受入条件へ追加すべきである。静的レビューのみ実施し、編集・commit・テスト実行は行っていない。