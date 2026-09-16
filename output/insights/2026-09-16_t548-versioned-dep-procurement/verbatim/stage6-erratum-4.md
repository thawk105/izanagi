# 段 6 裁定 追補 4 — 凍結 prereg `protocol-r33.json` の job script binding (D1790 の形へ)

**正本の関係:** `stage6-ruling.md`・追補 1〜3 に続く。衝突したら本書が優先する。

## 発生

受入 attempt 1・2 の両方で `orchestrator/tests/test_s8b_oracle_n_pilot.py::test_r33_protocol_document_loads_from_repository`
が**決定的に赤** (`:291` の `AssertionError`、期待 `566698b3…` ≠ 実測 `3ceaabd1…`)。

- 凍結された事前登録 `output/insights/2026-08-16_t1142-n-pilot-prereg/protocol-r33.json` の
  `source.job_script_sha256` = `566698b3a833224488dd4d0c3be0515dd812b75003f3f08f947e37aebfc50ad9`
  = **変更前 main (`d97c423bd`) の `tools/pegasus/oracle_n_pilot.sh` の bytes**。
- 同 test `:291` は `loaded.job_script_sha256 == sha256(現行 file)` と**live 比較**している。
- 単位 B が同 shell の解決行を付け替えたので現行 bytes は
  `3ceaabd1b8b3759fb24b136f44256e8ae76115dd6d1a283bc205c86de01a0ed1`。
- 後継 prereg `2026-09-09_t2154-n-pilot-prereg-successor/protocol-r33-successor.json` も同じ
  `566698b3…` を記録するが、その test は driver しか live 比較しない (親が確認)。

**本 wave に帰属する。F370 の 4 形目** (凍結 prereg が編集 file を sha256 で pin)。
親が段 6 fix 前に「wave の変更 file 40 本の変更前 sha256 を repo 全体で逆引き」していれば
段 4 追補 5 の `pbs_job` と同時に出ていた。逆引きの結果、live 比較で壊れる箇所は本件 1 つだけ。

## 決定 (D1790 / 規律 7 / D200 の先例)

**凍結 prereg (`protocol-r33.json`、`protocol-r33-successor.json`) は 1 byte も書き換えない。**
test `:291` の根拠を「live bytes と一致」から「**測定時点の版 (prereg が記録する sha) と現行の版
(現行 bytes の明示 pin) を独立した 2 定数で pin**」へ移す。同 test 内で driver が既に
`R33_FROZEN_ARTIFACT_DRIVER_SHA256` / `R33_SUCCESSOR_ANALYSIS_DRIVER_SHA256` の 2 定数でそう扱われている
(commit `02829b79b`、D1790)。

親が算出した値:

| 定数 | 値 | 出所 |
|---|---|---|
| `R33_FROZEN_ARTIFACT_JOB_SCRIPT_SHA256` | `566698b3a833224488dd4d0c3be0515dd812b75003f3f08f947e37aebfc50ad9` | 凍結 prereg の記録値 = `d97c423bd:tools/pegasus/oracle_n_pilot.sh` |
| `EXPECTED_CURRENT_ORACLE_N_PILOT_JOB_SCRIPT_SHA256` | `3ceaabd1b8b3759fb24b136f44256e8ae76115dd6d1a283bc205c86de01a0ed1` | wave tip `a792c92f8` の同 file (親が単位 B の差分を読んで pin) |

要件:

1. `loaded.job_script_sha256 == R33_FROZEN_ARTIFACT_JOB_SCRIPT_SHA256` (prereg の記録は変わらない)。
2. `sha256(ROOT / loaded.job_script_path) == EXPECTED_CURRENT_ORACLE_N_PILOT_JOB_SCRIPT_SHA256`
   (現行 bytes の無断変更は引き続き赤)。
3. `R33_FROZEN_ARTIFACT_JOB_SCRIPT_SHA256 != EXPECTED_CURRENT_ORACLE_N_PILOT_JOB_SCRIPT_SHA256`。
4. **どちらの側も「いずれかを受理」へ緩めない** (D1790)。
5. 定数は既存の `R33_*_DRIVER_SHA256` と同じ場所・同じ書式で置く。
6. 実装子は編集後 file から sha256 を算出して埋めない (D200)。値は本書から逐語で取る。

## 所有

単位 **F5** = `orchestrator/tests/test_s8b_oracle_n_pilot.py` のみ。

## 受入 attempt 2 の他の赤 2 件 (非帰属)

`test_codex_worker_launch.py::test_check_receipt_enforces_v2_wall_clock_admission_boundary[at-bound]` /
`::test_web_search_duplicate_stdout_is_accepted_and_auditable` — 計算ノード bnode042、1 分 load 43.77 での
launcher timeout (`actual rc timeout != expected rc 0`、`receipt_status=missing`)。wave 非接触 file。
時間境界の検査で負荷依存。**非帰属。** 次の受入で再現しなければそのまま、再現すれば
`check_acceptance_reds.py` の経路 (ii)。
