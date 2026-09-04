## 結論

実装可能な計画である。durable authority も読めたため、WAL、raw cell JSON、tracked authority を照合した。数値と SHA-256 に不一致はない。

ただし実装前に次の点を補正する。

- fixture の stage 件数は brief の値が各 workload WAL 当たりである。全 fixture では `build_start=4`、`build_done=4`、`verify_done=24`、`bench_done=4`、`commit=4` になる。
- `bench_done` は反復ごとに 5 行あるのではなく、1 cell 当たり 1 行の `payload.tps` に 5 標本を持つ。
- raw cell JSON のトップレベルには `workload` や `role` がない。`cell_id`、`variant`、`build_attempt_id` で対応付け、workload と role は `certification.json` から読む。
- `raw-manifest.json.files` は 10 entry で、作図器が実際に読む外部 bytes はそのうち WAL 2 本と raw JSON 4 本である。この区別を provenance に残す。
- D1074 を満たすには、provenance に自己申告 hash を書くだけでは足りない。CLI 経路で tracked authority の既知 SHA-256 を literal pin し、独立なテスト定数でも照合する。
- 図の下段 abort rate は同じ 0〜1 の量なので、workload-local autoscale より共通の 0〜1 軸を推奨する。上段 throughput だけ workload-local とする。
- `results/` は D1013 が直接定めた系列ではなく新系列であるため、同時に README で lifecycle を正本化する必要がある。

静的確認時点では親所有の `docs/paper-story/results/2026-09-04-a2-certification-reject.md` が既に存在する一方、生成器、専用テスト、fig5 三成果物、README の fig5 項目はまだ存在しない。以下では新規ファイルの行番号を実装時の配置目安として示す。

## 生成器の file:line 設計

対象は `tools/plotting/plot_a2_certification.py` のみとし、約 850〜950 行以内に収める。

- `:1-45` — module docstring、利用例、標準ライブラリ、matplotlib/numpy import。入力文字列を shell に渡さないことを明記する。
- `:46-115` — 固定契約。
  - `REPO_ROOT`
  - `PROVENANCE_SCHEMA = "izanagi-a2-certification-figure-provenance/v1"`
  - `CERTIFICATION_SCHEMA = "paper-story-a2-certification-result/v3"`
  - `RAW_MANIFEST_SCHEMA = "paper-story-a2-raw-manifest/v3"`
  - `RAW_CELL_SCHEMA = "paper-story-a2-cell-result/v2"`
  - workload 順 `("rr5", "rr50")`
  - cell 順 `rr5-stock`, `rr5-fixed10`, `rr50-stock`, `rr50-fixed5`
  - canonical certification SHA-256 `f685b40d194c9e4b40eed6337b294f38a7ff4aef731829317fd2e83940fbda40`
  - canonical raw-manifest SHA-256 `12d8be7a9cabd404ab3147301c2df7998a731b310ec51a93f9a99b37705a7c35`
  - `_T975` は `tools/plotting/plot_t2216_backoff_walk.py:83-94` と同じ固定表方式。`ci95()` も同 `:144-156` の索引・範囲外拒否を踏襲する。
- `:116-205` — `FigureDataError`、`FigureLayoutError`、`_fail()`、strict JSON、SHA-256、有限数、整数、path containment。
  - duplicate key、NaN、Infinity、非 object JSON を拒否。
  - repo 入力は repo 外への lexical/symlink escape を拒否。
  - durable path は measurement root からの root-relative path に限定する。雛形は `plot_b10_extended_backoff.py:166-241`。
- `:206-285` — `_parse_cli()` と authority loader。
- `:286-380` — raw-manifest から canonical external path 6 本を組み立て、hash 検証。
- `:381-465` — WAL parser。測定値の consumer 述語を厳密に `record.get("stage") == "bench_done"` とする。
- `:466-570` — raw cell JSON parser、統計量、三者相互検算。
- `:571-645` — caption、artist-series、measurement condition の正規化。
- `:646-750` — 2×2 Figure の生成。
- `:751-825` — `check_figure_layout()`。
- `:826-910` — provenance の構築・意味検査・repo/external closure。
- `:911-980` — sibling temp への保存、provenance-last publish、`main()`。

## CLI 契約

CLI は次とする。

```text
python3 tools/plotting/plot_a2_certification.py \
    [--measurement-root PATH] \
    [--certification PATH] \
    [--raw-manifest PATH] \
    OUT_PREFIX
```

既定値は以下。

- 環境変数: `IZANAGI_A2_CERTIFICATION_MEASUREMENT_ROOT`
- durable root の既定値:
  `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2022-20260828c`
- certification:
  `output/insights/2026-08-24_paper-story-a2-certification/certification.json`
- raw manifest:
  `output/insights/2026-08-24_paper-story-a2-certification/raw-manifest.json`

measurement root の優先順位は CLI option、環境変数、固定既定値の順とする。provenance の再現 argv には defaults 展開後の全 path を明示し、環境変数の暗黙状態へ依存させない。

CLI は certification と raw-manifest の canonical SHA-256 を必ず検査する。合成 fixture 用の期待 hash 注入は Python 関数 API のみに置き、CLI に authority 差し替え用の逃げ道を作らない。

## WAL、raw JSON、authority の読み方

`load_measurements()` は次の順で fail-closed にする。

1. certification と raw-manifest の schema、study、attempt、protocol、current pin を照合する。
2. raw-manifest の `campaign_claims` から workload ごとの campaign id を得る。
3. certification の cell 集合から raw cell path を決める。
4. raw-manifest の 10-entry `files` が policy-sized closure であることを確認する。
5. 実際に開くのは次の 6 本だけとし、各 SHA-256 を `files` と照合する。
   - `jobs/<w>/campaigns/<id>/runs/wal.jsonl` 2 本
   - `jobs/<w>/raw/<cell>.json` 4 本
6. WAL は全行の JSON 構造だけを検査するが、測定値として読むのは `stage == "bench_done"` の行だけとする。他 stage の payload は参照しない。
7. 各 WAL に bench record が exact 2 件あることを要求する。
8. `bench_done.payload.build_attempt_id`、record `variant`、raw JSON の `cell_id`、`variant`、`build_attempt_id` を使って一意に対応付ける。
9. raw JSON の `performance.samples_tps` と WAL の `payload.tps` を順序込みで完全一致させる。
10. genome は raw JSON と certification で完全一致させる。
11. structured workload、trace-disabled、toolchain、campaign identity も raw JSON と certification/manifest の対応範囲で照合する。

raw JSON は WAL から materialize された別経路であり、独立測定とは呼ばない。「hash 束縛された二つの投影の一致」と表現する。

## 統計量と判定の境界

各 cell について以下を WAL の 5 生値から計算する。

- `median_tps = statistics.median(samples)`
- `mean_tps = statistics.fmean(samples)`
- `sample_stdev_tps = statistics.stdev(samples)`
- `ci95_half_tps = _T975[4] * sample_stdev_tps / sqrt(5)`
- `cv = sample_stdev_tps / mean_tps`

`n != 5`、非有限値、bool、0 以下の TPS は拒否する。abort rate は `bench_done.payload.leading_indicators.abort_rate` の有限な 0〜1 の 1 点だけを採り、CI は作らない。

相互検算は次の通り。

- computed median = WAL `payload.median_tps`
- computed median = certification `cells[].performance.median_tps`
- computed CV = WAL `payload.cv`
- WAL samples = raw JSON `performance.samples_tps`
- WAL/raw/certification の build attempt、variant、genome、workload identity が一致
- computed `adopted median / no-backoff median - 1` = certification `effects[workload]`

浮動小数の effect と CV だけ `rel_tol=0`、狭い `abs_tol` を使い、整数由来の sample と median は exact equality とする。

`outer_status` と図中の効果ラベルは計算値ではなく、相互検算後の certification field をそのままコピーする。生成器は status を導出、昇格、書換えしない。

## 図の構成

P2 の 2 列×2 行を維持し、次の形へ明確化する。

- 列:
  - write-heavy、rratio 5、bnode141
  - balanced、rratio 50、bnode064
- 上段:
  - x は `no backoff` と `fixed 10 µs` または `fixed 5 µs`
  - 5 生値を固定 offset で jitter 表示
  - 菱形を標本平均、error bar を t 分布 95% CI
  - 各 arm の median を短い横線で表示
  - no-backoff median をパネル全幅の灰色破線でも表示し、効果の分母を明示
  - adopted median の近傍へ `−46.3902%` / `−65.9080%` を直接表示
  - arm 間を線で結ばない。反復が paired であるとの誤読を避けるため
  - y は 0 始まり、workload ごとに独立
- 下段:
  - 同じ二つの x 位置へ abort rate を 1 点ずつ描く
  - error bar、補間線、機序を示す矢印は付けない
  - 両 workload で共通の 0〜1 軸とする。P2 の全面的な workload-local 軸をここだけ修正し、同じ bounded metric の見かけの差を autoscale で増幅しない
- figure-level text:
  - `outer status: reject`
  - `correctness: all 4 cells certified in separate trace-enabled runs`
  - `correctness is not the performance verdict`
- 色:
  - no backoff は灰色
  - adopted は色覚多様性を考慮した橙または暗赤
  - 成功を連想させる緑は使わない

baseline が raw sample arm と水平線で二重に現れるのは意図的である。前者は分布、後者は protocol が用いる median 分母を示す。

## layout check と atomic publish

`check_figure_layout()` は `plot_t2187_adaptive_consts.py:879-939` と同型にする。

- `fig.canvas.draw()` 後に renderer を得る。
- plot axis が exact 4 面であることを検査。
- 全 visible text が figure bbox 内。
- `gid="direct-label"` と `gid="cell-label"` は owner axis bbox 内。
- 他 panel bbox への侵入が 1 pixel² を超えたら拒否。
- visible text 同士の bbox overlap を拒否。
- `axis.get_tightbbox()` が figure を出ないことを確認。
- layout check は一度以上、最初の `savefig` より前に実行する。
- 保存直前にも input SHA-256 を再計算し、読込後に変化していれば拒否する。

出力は同じディレクトリの sibling temp に PNG、PDF、provenance をすべて構築し、検査完了後に `os.replace()` する。portable filesystem では 3 file 全体を単一 rename transaction にはできないため、provenance を最後の commit marker とする。途中終了で PNG/PDF だけ見えても、provenance 不在または hash 不一致として consumer が拒否できる設計にする。

## provenance schema

トップレベルは次を exact key set とする。

```json
{
  "schema": "izanagi-a2-certification-figure-provenance/v1",
  "generated_utc": "...",
  "generator": {},
  "outputs": [],
  "tracked_inputs": [],
  "external_source_locator": {},
  "external_inputs": [],
  "measurement_conditions": {},
  "cells": [],
  "artist_series": [],
  "outer_status": "reject",
  "effects": {},
  "effect_crosschecks": {},
  "correctness": {},
  "correctness_performance_note": "...",
  "caption": "...",
  "reproduction": {}
}
```

field の内容は以下。

- `generator`: repo-relative `path` と SHA-256。
- `outputs`: PNG/PDF の repo-relative path と SHA-256。
- `tracked_inputs`: certification、raw-manifest の repo-relative path、SHA-256、schema、authority scope。
- `external_source_locator`: `root_at_generation` と `validation_key = "root-relative-path-plus-sha256"`。
- `external_inputs`: 読んだ 6 本だけ。`kind`、workload、campaign/cell、root-relative path、SHA-256。
- `measurement_conditions`:
  - attempt、protocol SHA-256、source commit、CCBench pin
  - threads、records、Zipf skew、rmw、max_ope、extime、reps
  - trace-disabled performance、perf 無し
  - toolchain
  - workload 別 rratio、host、request id、campaign id
- `cells`:
  - workload、role、cell id、variant、build attempt
  - genome
  - samples、median、mean、sample stdev、CI half-width、CV、abort rate
  - raw/certification crosscheck 状態
- `artist_series`: 各 artist の `kind`、`label`、metric、cell id、workload、role、genome、x/y または value、unit。特に水平基準線も label↔value↔genome を持つ。
- `outer_status`: certification から byte-levelに読んだ値。
- `effects`: certification の値。
- `effect_crosschecks`: raw median から再計算した値と authority 一致結果。図のラベルにはこちらでなく `effects` を使う。
- `correctness`: 4 cell の status、legacy/full-scale 反復数、argv observation limit。
- `correctness_performance_note`: 「correctness は別の trace-enabled run の判定であり、trace-disabled 性能の outer verdict を変更しない」という固定注記。
- `caption`: `_caption(data)` が構造化値から決定的に組み立てる正文。
- `reproduction`: `cwd="repository-root"`、展開済み argv、`shlex.join()` した command。

`validate_repo_closure()` は tracked inputs、generator、outputs、caption の README 収録を検査する。`validate_external_sources()` は measurement root が与えられた場合だけ 6 external bytes を再検証する。

## テストファイルの file:line 設計

`orchestrator/tests/test_plot_a2_certification.py` は約 550〜650 行を目安とする。

- `:1-55` — imports、repo path、`skiputil`、独立 SHA-256 pins。
- `:56-220` — production-sized fixture builder。
  - 2 workload
  - workload 当たり 2 arm
  - cell 当たり `bench_done.payload.tps` 5 値
  - abort rate 1 点/cell
  - workload 当たり `build_start=2`, `build_done=2`, `verify_done=12`, `bench_done=2`, `commit=2`
  - raw cell JSON 4 本、certification、10-entry raw-manifest
- `:221-315` — positive parse、統計、identity、artist-series。
- `:316-425` — hash、raw/certification、sample count の負例。
- `:426-510` — 本物の matplotlib Figure、layout、atomic publish。
- `:511-575` — landed fig5 repo closure、caption 一致。
- `:576-640` — canonical durable root の conditional test。

fixture の `verify_done` や `build_done` には故意に巨大な偽 `tps` や abort 値を置き、consumer がそれらを使わないことを観測可能にする。本物の Figure を `make_figure()` で作り、`check_figure_layout()` へ直接通す。

外部 root の判定は `test_plot_b10_extended_backoff.py:42-71` と `test_b10_extended_figure_provenance.py:124-153` の `skiputil` 前例を使う。root が存在して一部だけ欠ける場合は skip でなく failure とする。

## 親が走らせる nodeid

合成 fixture と生成器の focused set:

- `orchestrator/tests/test_plot_a2_certification.py::test_fixture_has_production_shape_and_recomputes_statistics`
- `orchestrator/tests/test_plot_a2_certification.py::test_wal_projection_uses_only_bench_done_records`
- `orchestrator/tests/test_plot_a2_certification.py::test_raw_cell_samples_and_identity_must_match_wal`
- `orchestrator/tests/test_plot_a2_certification.py::test_certification_median_mismatch_is_rejected`
- `orchestrator/tests/test_plot_a2_certification.py::test_certification_effect_mismatch_is_rejected`
- `orchestrator/tests/test_plot_a2_certification.py::test_external_sha256_mismatch_against_manifest_is_rejected`
- `orchestrator/tests/test_plot_a2_certification.py::test_five_samples_are_required_per_cell`
- `orchestrator/tests/test_plot_a2_certification.py::test_outer_status_is_copied_not_recomputed`
- `orchestrator/tests/test_plot_a2_certification.py::test_tracked_authority_bytes_match_independent_pins`
- `orchestrator/tests/test_plot_a2_certification.py::test_caption_distinguishes_correctness_from_performance`
- `orchestrator/tests/test_plot_a2_certification.py::test_real_size_figure_passes_layout_and_artist_contract`
- `orchestrator/tests/test_plot_a2_certification.py::test_layout_checker_rejects_overlapping_text`
- `orchestrator/tests/test_plot_a2_certification.py::test_layout_failure_publishes_no_outputs`
- `orchestrator/tests/test_plot_a2_certification.py::test_cli_writes_png_pdf_and_provenance`

親が docs と三成果物を置いた後に加える integration set:

- `orchestrator/tests/test_plot_a2_certification.py::test_landed_fig5_repo_closure_and_caption`
- `orchestrator/tests/test_plot_a2_certification.py::test_real_external_provenance_when_measurements_exist`

実行は直接 pytest ではなく、例えば次を使う。

```text
python3 tools/run_tests.py orchestrator/tests/test_plot_a2_certification.py
```

描画は production-sized Figure 2 回程度に抑え、他の負例は loader/provenance 関数だけを呼ぶ。外部入力も小さいため、専用ファイル全体を数十秒以内に収められる。

## results 文書の骨格

静的確認時点の親 draft `docs/paper-story/results/2026-09-04-a2-certification-reject.md` は、すでに適切な大枠を持つ。次の対応を維持する。

- `:1-11` — 材料レポートであって投稿本文ではないこと、results 系列、測定追加ゼロ。
- `:13-24` — 位置づけと negative result の区別。
  - status は certification `.status`
  - S' と A-2 の区別は 2026-09-02 版 §9
- `:28-70` — 性能、正しさ、現行環境の三分割。
  - correctness は `cells[].correctness`
  - 現行値は `.effects`、`.median_tps`、WAL `bench_done`
  - campaign 分割は manifest `.campaign_claims`
- `:74-95` — exact 4-cell 表。
  - samples、CV、abort は WAL
  - genome、median、correctness は certification と raw JSON
  - mean/CI は同じ 5 samples から再計算
- `:99-112` — limitation register。
  - argv observation、noise floor、minimality は certification
  - D1257、D1263、A-6 は逐語裁定
  - D1198 未適用は D1198/T-1999 の一次記録を引く
- `:116-123` — fig5 と caption/reproduction。
- `:126-136` — 一次資料と SHA-256。
- `:140-146` —確かめていないこと。

親 draft `:108` の `raw/<cell>.json` に `build_admission_receipt_sha256` があるという参照は修正が必要である。同 field は raw JSON にはなく、WAL の `build_start.payload.build_admission_receipt_sha256` にある。generator は他 stage を読まないため、結果文書でこの receipt を引くなら WAL `build_start` を一次資料として直接示す。

また `:135` の D1258/D1259 は今回の射影にも brief の裁定一覧にもない。必要性と一次資料を親が確認できなければ、出典一覧から外す。

## paper-story README の変更

`docs/paper-story/README.md:135-155` の claim-evidence 系列の後、`:156` の運用ルール前へ `results 系列` を追加する。

規則文案:

- `results/` は版とは別系列の、完走済み個別結果を論文へ渡すための材料レポート置場である。全面的な narrative snapshot ではない。
- append-only とし、書いた後は更新しない。
- 新しい日付の結果を足すときは、対象結果の authority、全 raw input、限定を一体として再導出する。一部だけを直した差分版を置かない。
- 版の履歴へ登録しない。版か結果材料かは directory で判別する。
- 数値、日付、protocol 判定は一次資料のみを出所とし、paper-story の版を数値の出所にしない。
- protocol の status を研究としての成功、失敗、新規性の判定へ拡張しない。
- `tools/check_docs.py` の `LIVING_DOCS` 対象外とする。

表へ次の一行を加える。

```text
| 2026-09-04 | `results/2026-09-04-a2-certification-reject.md` | A-2 exact 4-cell certification の値、outer `reject`、図5、限定 |
```

`README.md:31-33` の最新 snapshot 説明へ、結果材料への一行 pointer を足す。ただし `:53-61` の stale 注記件数には入れない。2026-09-02 版の A-2 結論は stale ではなく、今回増えるのは詳細材料だからである。

## figures README と plotting README

`docs/paper-story/figures/README.md:20` の一覧へ fig5 を追加し、既存 fig4 節の末尾 `:398` 後に fig5 節を置く。

再現コマンド案:

```bash
IZANAGI_A2_CERTIFICATION_MEASUREMENT_ROOT=/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2022-20260828c \
python3 tools/plotting/plot_a2_certification.py \
    docs/paper-story/figures/fig5_a2_certification_reject
```

同節には入力 6 本、tracked authority 2 本、hash pin、軸の意味、proof chain、caption 正文を置く。

`tools/plotting/README.md:70-99` の B-10 節の後、S-1a 節の前へ A-2 節を追加する。これは親 docs ではなく実装単位の所有である。CLI、env var、入力、統計、判定非再計算、3 出力、保存前 layout check を約 25〜35 行で記す。

## キャプション正文案

`_caption(data)` が固定文と正規化済み data から次の正文を組み立てる。status、効果、host、条件、固定 backoff 値は埋込値とし、親は生成済み provenance の `caption` をそのまま figures README へ貼る。

> 図5. A-2 正式 certification の結果 (outer status: reject)。列は write-heavy (rratio=5、Pegasus bnode141) と balanced (rratio=50、Pegasus bnode064) である。上段は各 cell の trace-disabled 性能 run 5 標本を全数表示し、短い横線が median、菱形と誤差棒が標本平均と t 分布による 95% 信頼区間である。灰色の破線は同一 workload の no backoff (`BACK_OFF=0`, `BACKOFF_FIXED=-1`) の median で、効果の分母である。採用静的 backoff の median 効果は write-heavy の fixed 10 µs で −46.3902%、balanced の fixed 5 µs で −65.9080% だった。M tps は毎秒 100 万トランザクションを表す。下段は WAL に記録された abort rate の集約 1 点/cell であり、反復値と信頼区間はない。correctness は別の trace-enabled run で 4 cell とも certified だったが、これは性能の outer verdict ではなく、reject を変更しない。outer status と効果は SHA-256 で束縛した凍結 `certification.json` から読み、生成器は判定を再計算していない。測定条件は 48 スレッド、レコード数 1,000,000、Zipf skew 0.9、read-modify-write 無効、max operations 10、実行時間 3 秒、5 反復、CCBench pin `511c953`、perf 無しである。上段の縦軸は workload ごとに独立なのでパネル間の高さを比較しない。旧 `linux-baremetal` の値は本図の comparator ではなく、符号差の原因は同定していない。

## 変異候補

| # | 位置 | 変異 | 期待する赤の nodeid | 単一理由性 |
|---:|---|---|---|---|
| 1 | `plot_a2_certification.py:_bench_done_rows` | stage predicate を外す | `test_wal_projection_uses_only_bench_done_records` | 非 bench payload の偽値だけが差分 |
| 2 | `plot_a2_certification.py:_summarize_samples` | `len(samples) == 5` を緩める | `test_five_samples_are_required_per_cell` | 標本数だけを 4 にする |
| 3 | `plot_a2_certification.py:_load_external_inputs` | manifest SHA 検査を省く | `test_external_sha256_mismatch_against_manifest_is_rejected` | external 1 file の bytes だけを変更 |
| 4 | `plot_a2_certification.py:_validate_raw_cell` | WAL/raw samples または identity 照合を省く | `test_raw_cell_samples_and_identity_must_match_wal` | raw 側 1 field だけを変更 |
| 5 | `plot_a2_certification.py:_crosscheck_certification` | median 照合を省く | `test_certification_median_mismatch_is_rejected` | certification median だけを変更 |
| 6 | `plot_a2_certification.py:_crosscheck_certification` | effects 照合を省く | `test_certification_effect_mismatch_is_rejected` | certification effect だけを変更 |
| 7 | `plot_a2_certification.py:build_provenance` | status を `"reject"` に固定する | `test_outer_status_is_copied_not_recomputed` | authority status を sentinel にした propagation 専用 fixture |
| 8 | `plot_a2_certification.py:_artist_series` | genome または baseline value を別 cell と結ぶ | `test_real_size_figure_passes_layout_and_artist_contract` | artist↔provenance 対応 1 件だけが不一致 |
| 9 | `plot_a2_certification.py:_caption` | correctness/performance 区別文を落とす | `test_caption_distinguishes_correctness_from_performance` | caption の必須句だけを除去 |
| 10 | `plot_a2_certification.py:_publish_outputs` | layout error を握り潰す、または検査前に publish | `test_layout_failure_publishes_no_outputs` | layout checker だけを意図的に失敗させる |

登録件数は 10 件。いずれも fixture の変更軸を一つに限定できる。

## brief P1〜P6 と実測値の検算

- P1: 新 namespace 案は実現可能。ただし D1013 の自動的な帰結ではない。上記 results 系列規則を同じ変更で正本化する必要がある。
- P2: 2×2 構成は妥当。no-backoff arm の raw points と median 基準線を両方描くことを明示する。下段だけ共通 0〜1 軸へ修正する。
- P3: authority、median、effects、外部 hash の考え方は正しい。D1074 の条件を満たす canonical certification hash の独立 pin が不足していた。
- P4: 性能、正しさ、現行環境の分割と S'/A-2 の区別は妥当。claim-evidence 2026-08-26 §5 は A-2 完走前なので語法の前例にだけ使い、現行事実の出所にはしない。
- P5: stage 件数は workload 当たりの値としては正しいが、全 fixture の総数としては半分である。また反復は 5 bench records ではなく 1 payload 内の 5 samples である。
- P6: caption を provenance から README へ貼り、exact inclusion test を置く案は妥当。生成器の deterministic `_caption(data)` を先に確定し、親が実データ生成後に docs へ転記する順序が必要。

durable authority の 6 file SHA-256 は raw-manifest とすべて一致した。WAL と raw JSON の sample 順、genome、build attempt、median も一致した。

| cell | mean tps | t95 CI 半幅 | median tps | CV | abort rate |
|---|---:|---:|---:|---:|---:|
| rr5-stock | 2,554,948.8 | 119,798.329 | 2,527,542 | 0.0377628245 | 0.7767 |
| rr5-fixed10 | 1,359,769.6 | 20,944.053 | 1,355,011 | 0.0124048442 | 0.1189 |
| rr50-stock | 3,700,807.2 | 136,989.631 | 3,662,448 | 0.0298117278 | 0.6903 |
| rr50-fixed5 | 1,242,560.2 | 32,945.242 | 1,248,603 | 0.0213536032 | 0.2048 |

再計算した effects は rr5 `-0.463901687884909`、rr50 `-0.659079664748824` で、certification の値と一致する。数値上の所見はない。

brief への所見は合計 7 件である。内訳は results lifecycle、baseline 二重表示の曖昧さ、abort 軸、canonical authority pin、manifest 10/consumer 6 の区別、stage 総数、raw JSON の workload/role field 不在である。

## 所有 path と段 5 の分割

実装単位の所有 path は次の 3 本だけとする。

- `tools/plotting/plot_a2_certification.py`
- `orchestrator/tests/test_plot_a2_certification.py`
- `tools/plotting/README.md`

親 docs 単位は次とする。

- `docs/paper-story/results/2026-09-04-a2-certification-reject.md`
- `docs/paper-story/README.md`
- `docs/paper-story/figures/README.md`
- `docs/paper-story/figures/fig5_a2_certification_reject.png`
- `docs/paper-story/figures/fig5_a2_certification_reject.pdf`
- `docs/paper-story/figures/fig5_a2_certification_reject.provenance.json`
- worklog fragment と本 wave の insight

実装子が触ってはならない path:

- 親 docs 単位の全 path
- `output/insights/2026-08-24_paper-story-a2-certification/*`
- `output/insights/2026-08-28_t2022-a2-certification-run/README.md`
- `docs/paper-story/2026-*.md`
- `docs/paper-story/claim-evidence/*`
- 既存 `docs/paper-story/figures/fig*`
- A-2 driver、policy、既存 `paper_story_a2*` テスト
- `FROZEN_MANIFEST`

統合順は、実装子が生成器・合成テスト・plotting README を完成、親が results/README を確定、親が実データで fig5 三成果物を生成、caption を figures README へ byte copy、最後に integration node と全受入を走らせる順とする。

## 総括

- 実装単位の所有 path: 生成器、専用テスト、`tools/plotting/README.md` の 3 本。
- 変異候補: 10 件。
- brief への所見: 7 件。
- 最も割れうる 3 点:
  1. D1074 を満たす certification hash pin と、status を再計算せずコピーする境界。
  2. 10-entry raw-manifest から実際に読む 6 file を選び、WAL は `bench_done` だけを消費する境界。
  3. no-backoff の raw distribution と median 基準線の併記、abort 共通軸、caption の integration 順序。

実装、ファイル変更、pytest 実走は行っていない。