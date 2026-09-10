# 段 4 裁定 — [T-2408] B-10 限定受理の identity を campaign lock の記録値から取る (D1771)

段 2 プランを基に、段 3 の 2 レンズ (sol = 受理集合の拡大、luna = 実効性と先例整合) の所見を裁定した。
**プラン v1 は採用しない。下記 R1〜R7 と N1〜N3 を織り込んだプラン v2 を実装する。**

## 採用する所見 (must-fix)

### R1. lock を歴史 decoder に通しただけでは identity の真正性に届かない (sol-1 + luna-1、両レンズ独立に検出)

**成果物影響:** 4 投影だけの検査では、record 135 件を正規のまま残して `search_tag` / `trial` /
`ccbench_commit` / authority を改変した lock で report を発行でき、report が参照する測定時 identity が変わる。

report 専用入口で次を足す。

1. **D1653 が必須とする 24 blob 照合を行う。** 新機構は作らない。既存の
   `orchestrator/campaign/contract_loader_binding.verify_committed_contract_loader_blobs(
   authority.contract_loader_commit, authority.contract_loader_blob_sha256s,
   authority.recorded_contract_loader_relative_paths)` を再利用する。
   これは `artifact_admission._verify_committed_loader_binding` が pre-T733 grammar に対して
   実際に使っている経路と同じ関数である。
2. **identity の残り field を module 由来の導出値と exact 比較する。新しい不透明 literal は 1 つも増やさない。**
   - `identity["search_tag"] == "formal"`
   - `identity["ccbench_commit"] == PIN`
   - `identity["trial"] == f"{TRIAL}-{<その系列 binding literal の spec_sha256>[:16]}"`
   - `identity["spec_content"]` は `config_for()` が組み立てる文字列を系列名から同じ式で導出して一致比較
   - `identity["search_config"]["workload"]` == 系列名
   - `identity["search_config"]["preregistration_path"] == PREREG_REL`
3. campaign_id は既存どおり系列 literal と一致させる (現行の validator の検査を残す)。

**不採用の代替:** `artifact_admission.require_admitted_campaign(purpose=HISTORICAL_RAW)` を使う案。
実測で `orchestrator/campaign/legacy_admission_overlay_v1.json` に B-10 の formal campaign ID は
1 件も無い。採ると overlay ledger への登録という別問題を開く。D1653 が要求するのは blob 照合であり、
それは上記 1 の helper 再利用で満たせる。

### R2. calibration も lock 記録値から復元する (luna-2)

**成果物影響:** 現状の案では `load_calibration()` が live registry を読むため、report が停止するか、
歴史 campaign と異なる calibration path / SHA / records を report へ記録する。

report では `load_calibration()` を呼ばず、3 lock の `search_config.calibration` を exact 共通比較して
`CalibrationSelection` を復元する。`CalibrationSelection` は 11 個の scalar だけを持つ frozen dataclass で
`as_dict() = dict(vars(self))` なので、**exact key 集合検査 + `CalibrationSelection(**locked)` で復元できる**
(`b10_backoff_shape_sweep.py:525-540` で確認済み)。`validate_runtime_physical_residual` と writer には
この復元値を渡す。

**「live を読んで exact 比較する」案は不採用。** 一致しなければ止まる形は、D1771 が治した病
(現行の live 成果物と一致しないと過去の測定が読めない) を calibration 側で再発させる。

### R3. report 分岐を patch / applied-tree より前へ出す (luna-3)

**成果物影響:** 現状の案では、歴史 patch SHA を渡せば SHA 不一致で report は発行不能のまま、
current patch と比較すれば無関係な live C++ tree の変化で再び止まる。

report phase では `validate_patch_bytes` / `patchharness.checkout` / `applied` / `validate_applied_tree` を
実行しない。report 分岐を `checkout` より前へ出す。現行解析側の evidence は
**clean tree・HEAD・`ANALYSIS_REL` blob 一致だけ**に限る。

### R4. writer は測定時 identity と現行解析 identity を分けて書く (luna-4)

**成果物影響:** 判定値が locked v4 spec 由来でも、report が `space_version` を現行 v3、formula を現行値として
表示すると、測定 identity の参照が矛盾する。現物 3 lock は `space_version = "b10-backoff-shape/v2"`、
formula `5b3d8dee…` を記録している。

provenance の measurement identity 欄へ lock の `space_version` / formula / patch / 3 系列 binding / 共通 spec を置き、
現行情報は `report_analyzer` 欄 (source commit と module SHA) へ分離する。Markdown も同じ区別にする。
**provenance schema は v2 → v3 へ上げる。** 消費者は module 自身と test 1 行 (`test_b10_backoff_shape_sweep.py:2730`)
だけであることを実測済み。単一 binding 前提が崩れる以上、版を据え置いて意味を変えるほうが悪い。

### R5. `run_formal(phase="report")` に到達する orchestration test を足す (luna-6)

**成果物影響:** helper の単体テストが全部緑でも `run_formal` に `load_preregistration()` が残れば
report は `prereg-blob` で止まったままになる。

`load_preregistration` / `load_calibration` / patch 系を fail stub にしたうえで `run_formal(phase="report")` を呼び、
3 lock の収集から `_write_reports` まで到達することを固定する。

### R6. 現物 3 本の lock を hermetic fixture として持つ (luna-7 + 親 B4)

**成果物影響:** 合成 fixture だけでは、現物の outer bytes・authority map・系列固有 identity のどれかを
実装が拒否しても緑のままになり、report が発行不能のまま残る。
親も同型の穴を独立に見つけている — 既存 `test_report_lock_binding_reads_the_real_campaign_lock_codec`
(`:2463`) は `schema_version` を持たない v1 形式を書いており、`decode_campaign_lock` は
`schema_version` が無ければ authority 検査を一切しない (`campaign_lock.py:540` 以降)。現物を再現していない。

3 本の raw lock (各約 16 KB) を `orchestrator/tests/fixtures/` 配下へ snapshot として置き、
decoder と report identity 入口へ raw bytes のまま通す。
`orchestrator/tests/fixtures/` は既に 2.9 MB の fixture 木を持つので前例の範囲内。
**fixture は byte 互換性だけを保証し、外部 evidence tree の不変性や対応する record / receipt / WAL までは
保証しない**とコメントへ明記する。既存の v1 正例 test は exact-24 正例 + v1 負例へ置換する。

### R7. report の submission receipt も歴史 commit で作る (luna-10)

`load_submission_identity()` は `prereg_commit` を receipt と突き合わせる (`:672-673`)。
report では歴史値 `77b33e37d2d63b1f83d10652792c3c93eba9fe8f` で一致することを要求し、正例 test を足す。
CLI syntax と job argv は変えない (`--prereg-commit` は全 phase で必須のまま)。

## 採用する小さい是正 (nit)

- **N1 (sol-2):** 3 系列の `preregistration_path` 相互比較は、各系列で `PREREG_REL` と比較した後では恒真になる。
  入れない。spec の相互比較を残すなら「診断用の整合確認」と明記し、変異保護の件数に数えない。
- **N2 (sol-3):** binding の module literal 比較の帰属変異には `analysis_code_sha256` の変更または
  系列 binding の交換を使う。`spec_sha256` の変異は locked spec digest gate に食われるので使わない。
- **N3 (sol-5):** brief の言い方を直す。B2 は「lock gate を除いたデータフロー上は」、
  M6 は「D1771 が裁定した唯一の採用 authority」とする (git blob 自体は今も読める)。
- **luna-9 の後段:** clean tree / HEAD / analysis blob の検査は、`load_preregistration` と report 入口の
  二重実装にせず小さい private helper へ抜いて双方から呼ぶ。

## refuted / 不採用

- **sol-4:** binding の key 欠落・系列交換・record 改変は、プラン v1 の設計でも通らない。追加不要。
- **luna-8:** 通常 decoder への歴史 grammar 漏れは無い。分離をそのまま保つ。
- **luna-9 前段:** `load_preregistration` / patch 検査は非 report phase で生き続けるので死なない。
- **luna-5 (live campaign identity の回転):** real だがコード変更はしない。
  この file 自身が `ANALYSIS_REL` なので、**編集すれば live binding の `analysis_code_sha256` は必ず変わる。**
  実測: 現に走っている B-10 campaign は無い (official campaigns の最終更新は 2026-09-05、3 日前)。
  drain も resume 放棄の裁定も不要。事実として worklog / insight へ記録する。
  同じ性質は同 file を編集する並行 wave (T-2409) にも等しく当てはまる。
- **luna-11:** 段 5 は 1 単位。所有集合を
  `{orchestrator/campaign/b10_backoff_shape_sweep.py, orchestrator/tests/test_b10_backoff_shape_sweep.py,
  orchestrator/tests/fixtures/<本 wave で足す lock snapshot>}` と明記する。

## 並行 wave との境界 (親の約束、実装子は必ず守る)

T-2409 (D1772) が同じ file の WAL 読取側を並行実装中。相手は
`_verification_source_disclosure` の `verify_done` ループ内 (起点 `cc9bba523` の `:3408` 付近) だけを触る。

- `_collect_report_inputs` の中の `_verification_source_disclosure` 呼出しと戻り値の受け 2 行は
  **現在の位置・現在の呼び方のまま残す** (親が相手へ約束済み)。
- `_verification_source_disclosure` (`:3359-3438`) と `_verification_completeness` の本体には触らない
  (`_verification_completeness` は引数型の変更だけ許す)。
- 新しい test は `orchestrator/tests/test_b10_backoff_shape_sweep.py` の 2463〜2670 付近へ置く。
  2850 行以降は相手の領域なので空ける。

## 構造 pin (壊さない)

- `_collect_report_inputs` は module 直下の FunctionDef のまま。
- その中に `_validate_legacy_balanced_records` / `_validate_legacy_read_heavy_records` への
  **Name 呼び出し**が在り、`expected_record_digests` を keyword で渡さない
  (`test_b10_backoff_shape_sweep.py` の 2023 行付近と 2257 行付近が AST で固定している)。
- `orchestrator/tests/test_official_perf_closure.py` の membership 一覧は現状のまま (perf 起動を足さない)。
- `orchestrator/tests/test_ccbench_spawn_sites.py` が関数別の subprocess 呼出し箇所数を pin している。
  `load_preregistration` の `_git` は 1 箇所。report 入口で `_git` を使うなら、その関数の期待値を
  同じ commit で更新する。

## 不変条件 (緩めない)

1. 135 個の record digest literal を 1 byte も変えない。3 つの digest 集合比較も変えない。
2. lock 記録値と module literal の exact 一致比較を残す。「lock に書いてあるから受理」にしない。
3. 系列別 literal の分離を保つ (3 つを 1 本に共通化しない)。
4. 歴史 lock の読み取りは report 専用入口に閉じ、通常 decoder を union にしない。
5. 凍結成果物 (現物の lock / block record / receipt) の bytes を書き換えない。

## 変異事前登録 (DW-M01、実装前に登録)

各変異は「同じ入力を拒否する層が前後にも内側にも無く、赤理由が一つに絞れること」を実装後に確認する。

| # | 変異 | 赤になるべき test | 単一理由性の根拠 |
|---|---|---|---|
| M1 | report 入口の歴史 decoder を通常 decoder へ戻す | exact-24 現物 fixture の正例 | 他層は grammar を見ない |
| M2 | authority の 24 blob 照合呼び出しを削除 | 偽 authority (commit と digest を差し替え) の負例 | 他の gate は authority を一切見ない |
| M3 | binding の module literal 比較を削除 | `analysis_code_sha256` を変えた負例 | N2 のとおり spec digest gate に食われない値を選ぶ |
| M4 | 系列 binding を交換 (write-heavy 入口へ balanced literal) | 系列交換の負例 | workload 比較とは別 field |
| M5 | locked calibration の復元をやめ `load_calibration()` に戻す | orchestration test の live-stub 正例 | stub された live 経路を呼ぶのはこの変異だけ |
| M6 | report 分岐で `load_preregistration()` を呼び直す | live parser fail-stub の正例 | 同上 |
| M7 | locked spec digest (`9c594114…`) の検査を削除 | spec drift の負例 | binding literal は spec 本体を見ない |

受理集合を縮小する wave なので、**承認外の過剰拒否の正例**も登録する: 現物 3 本の raw lock は
そのまま受理されること (M1〜M7 のどれを入れても、この正例が巻き添えで赤にならないことを確認する)。
