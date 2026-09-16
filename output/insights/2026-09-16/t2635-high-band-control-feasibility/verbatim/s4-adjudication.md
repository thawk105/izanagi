# [T-2635] 段 4 裁定 — 所見の裁定・brief の訂正・プラン v2 (probe 実行前に凍結)

2026-09-16。親 (Claude) が段 2 プランと段 3 相談 A (sol) / B (luna) を読んで裁定した。
**本文書の §3 以降は、新しい候補別集計を 1 度も走らせる前に固定する。** 結果を見てから閾値・語彙・境界・
候補集合を変えない。既知情報 (T-2583 の全数値、D2020 / D2021、旧 J1 判定) を読んだ上での固定であり、盲検ではない。

## 1. 所見の裁定

| # | 所見 (要旨) | 判定 | 採否 | scope |
|---|---|---|---|---|
| A1 | brief の「高域へ届く広窓側は必ず別 cell」は証明されていない。正しくは「設定を変える候補は旧登録外」 | real | 採用 (brief 訂正 §2) | 内 |
| A1' | 「J1 の方法を保った新 cell 対は既存事前登録を変えない対照」という読みは文脈上成り立つが、本 wave の新 cell 投入を正当化しない (J1 §6 の cell 名指し + 格子 §4 の固定 + driver の受理集合) | real | 採用 — 実行判断は厳密な登録解釈 | 内 |
| A2 | 登録集合の再走は「設定を変えない基準候補」として表に載せる。ただし本 wave では投入しない (D2044 の「先に確かめ、分かれば新走行」の順序を逆転させる。積極的根拠なし) | real | 採用 | 内 |
| A3 | P3 の境界は数値化済みで `undetermined` は逃げ道でない。ただし「二つの代理計算の一致の要約」であり成立確認ではない。「結果を見る前」= 本 wave の未集計値を見る前 | real | 採用 (§3.6 に束縛文) | 内 |
| A3' | S=100 の「9 本だから構造的に不可能」は条件付き (理想格子 + stock 更新則内)。無条件の主張にしない。優先判定は発動しない | real | 採用 (brief 訂正 §2) | 内 |
| A4 | 裁定パッケージは二択に絞る: A 見送り〔推奨〕 / B 将来 wave で S=25 双子 + 別登録 J1' + driver 登録 | real | 採用 (§6) | 内 |
| A5 | 補助解析 (水準別移動・ACF・窓分位点) と `--selftest` は本題の必須成果物でなく、検査機構を膨らませない | real (部分) | 採用 — 補助解析は最小表に絞る。selftest は probe 自身の算術確認に限り、repo の gate にしない | 内 |
| A6 | brief の断定 3 件は記録済み不成立を設計一般の不可能性へ広げる危険。訂正を本文書に明記、凍結記録は変えない | real | 採用 | 内 |
| B1 | (a) 刻み転写は符号・parity 分岐・更新予算の設定間移植が未検証。「大刻みは平均回帰」は更新則から導けない | real | 採用 — (a) は `simulation_only`、brief の平均回帰仮説は撤回 | 内 |
| B2 | (b) prefix の共通辺は E_b ⊆ E_L の包含で恒真。双子間の共通性を検証する能力がない | real | 採用 — (b) の K は「共通辺」と呼ばず、**K の 3 値判定から (b) を外す** (§3.5) | 内 |
| B3 | (c) の 1899/949/474/37/9 は正しい。`(50,75)` は境界横断。**S=25 の転写最大 300 では主帯域の非自己辺は (75,100)〜(275,300) の 9 本で K_a,high ≤ 9** | real | 採用 — 必要到達水準 `min_reach_for_K_high_ge_10` を候補表に足す (§3.4) | 内 |
| B4 | P(up) 単独は不足 (据置を分ける)。`parity_branch` 件数、水準別の窓統計を足す。平均回帰の因果・到達確率は同定できない | real (部分) | 採用 — up/down/stay + 平均変位、parity_branch、広窓 cell の水準別 `window_commits` 平均/分散 | 内 |
| B5 | selftest は期待値を手で固定すれば恒真でない。150 行は厳しいが検証を削らない。空きメモリは実行時に確認 | real (限界) | 採用 — 目安 200 行へ緩め、生計数・欠測理由・自己検査は削らない | 内 |
| B6 | 模擬値は F29 により裁定根拠に使えない。根拠にできるのは記録済み不到達・保持範囲・登録適合・仮定内の格子制約・未観測部分の存在 | real | 採用 — 結論文 (§6) と JSON の `grounds` / `reference_only` の二分 | 内 |
| B-scope | driver 編集・新計測・新 schema 台帳の混入は無い | 不成立 | — | — |

scope 外の real 所見は無い (A4 の選択肢 B は裁定パッケージの中身であり、本 wave の作業ではない)。

## 2. brief の訂正 (段 3 を受けて)

1. 「広窓側を高域へ置く設定は必ず別 cell になる」→「**設定を変える候補は旧登録外である。設定を変えない再走 (登録集合の
   再走) は旧登録内の唯一の候補だが、記録済み 1 rep の不到達から再走の不到達を確定しない**」。
2. 「S=100 は 9 本 < 10 で K_high >= 10 が構造的に不可能」→「**理想格子 (初期値 0・固定刻み・上限 1000・隣接遷移のみ) と
   stock 更新則の範囲内では**主帯域の非自己遷移辺が 9 本であり、この model 内で K_high >= 10 は成立しない。保存表現を含めた
   無条件の主張にはしない (F718 の表現上端の留保)」。
3. 「同じ登録集合の再走は D2020 の不到達を繰り返す見込みなので取らない」→「**再走は本 wave では投入しない。理由は将来も
   不到達だからではなく、D2044 の条件付き投入許可 (先に確かめ、分かれば新走行) を満たす根拠が記録済み走行に無いから**」。
4. 「刻みが大きいほど符号が決定的になり平均回帰する可能性」(prompt-consult-b の仮説) は撤回。更新則から導けない。
5. 予測子 (a)(b) の一致は成立確認ではない。**本 wave の回答は「現制約と記録済み証拠では成立を確認できない」であって
   「将来も成立しない」ではない。**

## 3. プラン v2 (確定仕様、凍結)

### 3.1 記録済みの登録対照 — 既存 J1 を無改変で呼ぶ (根拠: 記録)

`_load_new_trace` → `_j4_effective_update_interval` → 無改変 `_j1_sign_instability` を順に呼び、戻り値を
`existing_j1_unmodified` に丸ごと保存する。共通辺 12 本を帯域 (主 = 両端 > 50、感度 = max > 50、低域 = max <= 50、
境界横断 = min <= 50 < max) で分類し、`nm-step1-u2560` の `backoff_before` / `backoff_after` の最小・最大を生値で出す。
T-2583 の 5 状態語をそのまま使い、登録対照の判定は `no_high_band_observation` の再現を期待する (期待値は selftest で固定)。

### 3.2 登録・現物 driver への適合 — 実測 (根拠: 現物)

driver `tools/pegasus/probes/t2187_adaptive_const_probe.py` を `spec_from_file_location` で import し (worktree root を
`sys.path[0]` に置く。driver は orchestrator を import する)、候補ごとに次を実測して JSON へ書く。

- `parse_cells(<候補 cell 文字列>)` が例外なく parse できるか (文法適合)。
- `BACKOFF_TRACE_CONTRACTS.get(<候補集合文字列>) is None` か (trace contract 不在 = 現物で投入不能)。
- 登録集合 `NONMONOTONIC_TRACE_CELLS_TEXT` については `BACKOFF_TRACE_CONTRACTS` に**在る**こと、および
  `_validate_backoff_trace_contract` が `rep_index != 0` を拒否する分岐を持つことを、`argparse.Namespace` を組んで
  1 回呼び `ValueError` を得ることで実測する (rep_index=1 の Namespace)。

driver の import に失敗した場合はその項目だけ `measurement_incomplete` とし、`.pbs` 219〜247 行の読解 (逐語は
`verbatim/driver-pbs-trace-mode-219-247.txt`) を代替根拠として `source: "static_reading"` と明記する。
driver の bytes は 1 byte も変えない。driver の関数を module 属性で差し替えない。

候補集合文字列は、登録集合の文字列の中の `nm-step1-u2560:1:1:1000:2560:0:0:0:100:100:0` を
`nm-stepS-u2560:1:S:1000:2560:0:0:0:100:100:0` へ置き換えた 6 cell 集合 (S ∈ {0.5, 2, 25, 100}) と、
S=1 の登録集合そのもの、の 5 本とする。

### 3.3 格子の構造制約 (根拠: 仮定明記の算術) と狭窓側の記録済み在庫 (根拠: 記録)

- 理想格子の主帯域非自己遷移辺数 `U(S) = 1000/S − floor(50/S) − 1` (S=0.5/1/2/25/100 → 1899/949/474/37/9)、
  上端自己辺を含めた本数 (+1)、および仮定 (初期値 0・固定刻み・上限 1000・隣接遷移のみ・stock 更新則) を JSON に書く。
- **K_high >= 10 に必要な最小到達水準** `min_reach_for_K_high_ge_10(S)`: 主帯域の遷移辺を低い方から 10 本
  取ったときの上端 = `(floor(50/S) + 1 + 10) × S` (S=25 → 325、S=100 → 上限超過で `null`、S=2 → 72、S=1 → 61、S=0.5 → 55.5)。
  これは「広窓側が非ゼロ符号を 10 本の異なる主帯域辺に付けるには最低ここまで登る必要がある」という必要条件であり十分条件ではない。
- 記録済み u10 cell (狭窓側候補) ごとに、主帯域の辺表 `[edge, n_plus, n_minus, n_zero]`、全符号の辺種数、
  非ゼロ符号を持つ辺種数、自己辺、境界横断辺、理想格子外の辺の生の計数を出す (T-2583 §4.1 の 307/196/38/10 と照合)。

### 3.4 記録済み広窓 walk の記述 (根拠: 記録、判定境界を変えない)

全 6 cell について、event を帯域で間引かずに:

- 水準 `backoff_before = b` ごとの up / down / stay 件数と平均変位 (`backoff_after − backoff_before`)。
  境界 (0 と 1000) の据置は内点と分けて読めるよう、水準を key にしたまま出す。
- `parity_branch` の値別件数 (生 JSON から取る。loader は落とす)、`gradient_sign == 0` の件数と併記。
- `nm-step1-u2560` だけ: 水準別の `window_commits` の件数・平均・分散、および `gradient_sign` 列 (ゼロ含む) の lag 1〜10 自己相関
  (分散ゼロなら `null`)。他 cell の窓統計は cell 全体の件数・平均・分散・最小・p50・p90・p99・最大に留める。

これらは外挿の仮定に対する反証材料であり、平均回帰の機序・到達確率は同定しない。判定語を変える入力にしない。

### 3.5 代理予測子 (参考のみ、`simulation_only: true`)

- **(a) 刻み転写**: `nm-step1-u2560` の各 event の端点 b を S·b へ写し、event 順序と `gradient_sign` を保存する。
  転写最大値 = 12·S (6 / 12 / 24 / 300 / 1200)。S=100 は上限超過で `applicable: false` (clip しない)。
  転写列から既存部品で非ゼロ符号の辺集合を作り、同 S の記録済み u10 cell の辺集合と交差させた本数を
  `K_a_total` / `K_a_high` として出す (仮定: 刻み単位の歩行・符号・1,170 update 予算の転用。破れ: B1)。
- **(b) 同刻み u10 の走行開始 1,170 update**: `dropped == 0` の cell (`nm-step2` / `nm-step25` / `nm-step100`) だけ適用。
  `seq` の単調性と先頭 seq を確認して開始区間であることを検算し、`sum(window_us)` を prefix 実時間として出す。
  出すのは prefix 内の端点最大値 (到達) と prefix 内の非ゼロ符号辺種数だけ。**「共通辺数」とは呼ばない**
  (E_b ⊆ E_L の包含恒真、B2)。`nm-step0.5` / `nm-step1` は開始 prefix 欠落で `applicable: false`、保持先頭で代用しない。
- (a)(b) の値は JSON の `reference_only` 配下に置き、`grounds` 配下には置かない。

### 3.6 判定語 (実行前に確定、束縛つき)

到達 (候補ごと): 有効な (a)(b) の両方で最大値 > 50 → `reach_predicted`、両方で <= 50 → `reach_not_predicted`、
割れる・一方以上が適用不能 → `reach_undetermined`。到達は端点の**厳密な** > 50。

共通辺 (候補ごと): (b) を K の予測子から外したため、二予測子一致の規則を満たせる候補は存在しない。したがって
**全候補で `K_undetermined` と裁定で定める** (probe は判定語を計算せず、この固定語を書く)。probe が出すのは
`U(S)`、`min_reach_for_K_high_ge_10`、`K_a_total` / `K_a_high` (参考)、狭窓側在庫、の生計数だけである。

**束縛:** これらの判定語は「二つの代理計算の一致の要約」であり、成立確認ではない。`reach_predicted` は D2044 の
「作れると分かれば」を満たさない。判定語・`K_a`・prefix 値は候補採否・新走行選択・再走却下・機序採否の根拠に用いない (F29、B6)。

### 3.7 probe 仕様

- author が worktree 内 `output/insights/2026-09-16/t2635-high-band-control-feasibility/probe_t2635.py` に書く。
  `git add` しない。親が実行前に job dir へ `mv` し、repo には `verbatim/probe_t2635.py.txt` の写しだけ残す。
- Python 3.10、標準ライブラリのみ。引数 `--trace` (絶対 path、必須)、`--analyzer` (絶対 path、既定は worktree の解析器)、
  `--driver` (絶対 path、既定は worktree の driver)、`--repo-root` (sys.path へ挿入、既定は worktree)、`--output` (create-only)、
  `--selftest` (通常出力を書かず、期待値との照合だけ行い不一致なら非 0)。候補集合・N=1170・帯域・閾値は本文で固定し探索引数を設けない。
- 解析器は `spec_from_file_location` で import。bytes を変えず module 属性を書き換えない。
- 生 JSON を 1 度読んで `seq` / `parity_branch` / `window_us` 等の補助要約を取り、解放してから `_load_new_trace` を呼ぶ。
- 目安 200 行 (空行・comment 除く)。収まらなければ §3.4 の他 cell 窓統計 → ACF の順に削り、`omitted` に書く。
  生計数・欠測理由・selftest・`grounds` は削らない。
- JSON: `schema_version: "izanagi-t2635-high-band-control-feasibility/v1"`、`input` (path/bytes/sha256)、`analyzer` (path/sha256/再利用関数)、
  `driver` (path/sha256)、`preregistration` (本文書の絶対 path と sha256、`blinded: false`)、`headline_eligible: false`、
  `throughput_scope: "diagnostic_only"`、`certified: false`、`scope` 文字列、
  `grounds` { `registered_contrast` (§3.1)、`driver_admission` (§3.2)、`lattice` (§3.3)、`narrow_side_inventory` (§3.3)、`wide_walk_descriptives` (§3.4) }、
  `reference_only` { `proxy_a`、`proxy_b` (§3.5) }、`candidates` [ { `S`、`cell_text`、`registered`、`submittable_with_main_artifacts`、
  `reach_verdict`、`k_verdict: "K_undetermined"`、`U_S`、`min_reach_for_K_high_ge_10`、`K_a_total`、`K_a_high`、`proxy_a_max`、`proxy_b_max`、`applicability` } ]、
  `limitations`、`omitted`。
- `--selftest` の固定期待値 (手で固定、helper で生成しない):
  1. `nm-step1-u2560`: events 1170、dropped 0、before/after 最小 0.0 最大 12.0。
  2. 無改変 J1: `common_edge_count` 12、`fixed_weight_sum` 1168、更新間隔 10 側 0.4984、2560 側 0.4583、差 +0.0402 (小数第 4 位で一致)、
     `verdict = not_supported`、qualifiers に `direction_unstable`。
  3. 主帯域の全符号辺種: `nm-step1` 307 / `nm-step2` 196 / `nm-step25` 38 / `nm-step100` 10; `(1000,1000)` の ゼロ件数 `nm-step25` 236 / `nm-step100` 610、正負 0。
  4. 合成列 (5〜8 event): 現在符号を直前辺へ帰属すること、`(50,75)` が主帯域外 (境界横断) であること、ゼロ符号が非ゼロ辺集合に入らないこと。
  5. `U(S)` = 1899/949/474/37/9、`min_reach_for_K_high_ge_10(25)` = 325、S=100 で `null`。
  6. S=100 の (a) が `applicable: false`、`nm-step0.5` / `nm-step1` の (b) が `applicable: false`。
- 入力不正・import 失敗・selftest 不一致・資源不足は `measurement_incomplete` とし、不到達や不可能の証拠にしない。
- 実行は親が login node で `python3 -B` + `/usr/bin/time -v`。実行前に空きメモリを確認する。

### 3.8 主張しないこと (凍結)

- 候補設定での実測値。双子間の再現性。到達確率。平均回帰の因果。計数ノイズの寄与。
- (a)(b) の一致を成立確認と読むこと。`predictor_range` を将来値の上下限と読むこと。
- 旧 J1 `not_supported`、D2020、D2021 の昇格・撤回・射程変更。
- 「将来も成立しない」。

## 4. 変異事前登録 (`DW-M01`)

実装面の repo 差分はゼロ (probe は追跡せず job dir へ退避、解析器・driver・テスト無改変)。`DW-S04` により変異 matrix は免除。
受入全走は免除しない。実 repo を読むテストのうち解析器の consumer test (`orchestrator/tests/test_backoff_nonmonotonicity_analysis.py`) を
記録前に実走する。

## 5. 成果物

- `output/insights/2026-09-16/t2635-high-band-control-feasibility/README.md` + `verbatim/` (s1-brief、s2-plan、s3-consult-a/b、
  本文書、probe_t2635.py.txt、出力 JSON、selftest log)。
- `docs/spool/` fragment: worklog 1 件、decisions 1 件 (裁定パッケージの二択と推奨、および brief の訂正 3 件の記録)。

## 6. 裁定パッケージの形 (「作れない」枝で README §6 に置く)

**結論文 (凍結):** 記録済みの登録対照では広窓側の最大値は 12.0 µs であり高域比較の共通台は成立していない。設定を変える候補は
すべて旧登録外で、main の現物 driver は登録済み 4 cell 集合しか受理しない。候補設定の列は記録の転写または同一記録の部分列であり、
候補設定で観測された走行ではない。本 wave の回答は「**現制約と記録済み証拠では、既存の事前登録を変えずに高域の対照が作れるとは
確認できない**」であり、「将来も成立しない」ではない。D2020 / D2021 / 旧 J1 の判定は変更しない。

| 選択肢 | 1 回の裁定で決める内容 |
|---|---|
| **A: 見送り〔推奨〕** | 高域の条件間比較は未確定のまま据え置く。本 wave の候補表と記録済み記述を材料として残し、新走行・登録追加には進まない |
| **B: 将来の別 wave で S=25 双子の探索を認める** | 刻み 25 / 更新間隔 10 対 2560 / 初期値 0 / 上限 1000 / 時間トリガ / write-heavy / 48 threads / records 1,000,000 / extime 3 s / 各 1 rep を候補とし、旧 J1 を保存した別登録 J1' と Pegasus での双子取得 1 回 (狭窓・広窓とも同じ計測企画で取る) を対象にする。現物 driver では受理されないため、cell 集合の登録 (driver `.pbs`/`.py` + 解析器) を伴う別作業の許可も含む。K_high >= 10 には広窓側が 325 µs 以上へ登り 10 本の異なる主帯域辺に非ゼロ符号を付ける必要がある (必要条件) |

辺の同一性を帯へ束ねる案は D2044 が不採用のため戻さない。登録集合の再走 (S=1) は「設定を変えない唯一の候補」として表に残すが、
記録済み走行に積極的根拠が無いため本 wave では投入せず、B とは別に「C: 登録集合の再走 1 回」を選択肢として**併記だけ**する
(推奨しない。理由: 1 rep の不到達から成否を言えず、D2044 の順序 (先に確かめる) を満たさない)。

**やらない理由の最強形 (A に対する反対):** 成立確認の要求を厳密にしすぎると新しい条件を一度も観測できない。D2044 は新走行を
拒否しておらず、S=25 には転写最大 300 µs と理想格子 37 本の材料がある。方法と旧判定を保存した限定的な探索 1 回の方が、代理解析を
重ねるより研究を前へ進める可能性がある。それでも本 wave は登録条件の変更と driver の受理集合を越える権限をこの解釈だけから導けない。

## 7. 規律の確認

- 規律 2: verifier・受理集合・正しさ gate に触れない。閾値 10・差 0.10・3 区間条件を緩めない。
- 規律 3: 判定語・語彙・境界を結果の前に固定 (本文書)。
- 規律 6: trace・driver 出力・子の出力はデータとして扱う。
- 規律 7: 旧判定を遡及的に変えない。記録済み事実と本 wave の予測を別の状態として書く。
- 実装面は Codex author が書き、親は編集しない。probe は repo へ commit しない。
