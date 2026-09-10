# 段 6 裁定 (親の初回実測後) — dev-wave-t2327-s1-sort-contract-binding

統合 commit 1 = `50cfcb6832be7e56fcc5afc0a89e0b624e70467f` (author patch そのまま)。
親の焦点走 (10 file、計算ノード dispatch、`focus-1.log`): 3 failed / 686 passed / 6 skipped。

## 親が見つけた所見 (レビュー前、すべて real・must-fix)

- **F-P1 (派生 pin、本 wave 起因)** `orchestrator/tests/test_s8b_oracle_manifest.py:63` の `PIN_GATE_SPEC_SHA256` は
  `PIN_GATE_SPEC_RAW` bytes の sha256 であり、L89 の materializer sha を書き換えると変わる。author prompt の
  「他の literal は触らない」が原因。赤 = `test_build_approved_valid_fixture_output_depends_only_on_spec_pin`、
  `test_reviewed_spec_has_independent_canonical_bytes_and_sha_literal`。成果物影響: 無し (test golden の整合のみ)。
  対応: `hashlib.sha256(PIN_GATE_SPEC_RAW).hexdigest()` で再計算して置換。値の複製は repo に無い (値検索で 1 件のみ)。
- **F-P2 (consumer test の double 取り残し)** `orchestrator/tests/test_sort_swo_oracle.py::test_s1_sort_best_runs_same_oracle_before_source_materializer`
  は `direct.source_digest.resolve` だけを double にして順序 `oracle → resolve` を期待する。sort_best は
  `resolve_evidence` を呼ぶようになったので実 `resolve_evidence` に落ちて `git status rc=128`。対応: 同テストの
  double を `resolve_evidence` にも張り (kwargs に `sort_oracle_contract_id=ORACLE_CONTRACT_ID` を要求)、
  順序の期待は「oracle が source resolve より先」のまま維持する。期待値の緩和ではなく代役の追随。
- **F-P3 (consumer 取り残し・production)** `orchestrator/campaign/s8b_oracle_driver.py` は s1 の `prepare_cell` で
  materialize した後、L1731 で `PreparedCell` を作り直して `sort_oracle_contract_id` を落とし、L1760/L1788 で
  契約 ID 無しに `pipeline.evaluate(src_token=<束縛済み token>)` を呼ぶ。`pipeline.evaluate` L1178 が
  `src_token != evidence.src_token` で fail-closed するため、**s8b oracle campaign の sort_best cell は全件 abort する。**
  成果物影響: s8b の sort_best 判定が出なくなる (受理集合の縮小、本 wave 起因)。
  対応: `prepared_for_eval` に `sort_oracle_contract_id=prepared.sort_oracle_contract_id` を写し、非 None の
  ときだけ `evaluate_kwargs["sort_oracle_contract_id"]` を足す (s1 `run_role` と同型)。
- **F-P4 (consumer 取り残し・production)** `orchestrator/campaign/s8b_floor_campaign.py` L4383 は prepare 後に
  契約 ID 無しで `source_digest.resolve_evidence(...)` を呼び、L4497 `_invoke_build(... source_evidence=evidence,
  src_token=prepared.src_token ...)` → `buildcache.build_v2` が src_token と evidence の不一致を拒否する。
  成果物影響: floor campaign の sort_best cell が build admission で全件失敗する (本 wave 起因)。
  対応: `prepared.sort_oracle_contract_id` が非 None のときだけ `resolve_evidence(..., sort_oracle_contract_id=...)`
  とし、同じ値を `build_kwargs["sort_oracle_contract_id"]` へ入れて `_invoke_build` → `build_v2` (既存 keyword、
  L2984) へ渡す。L4388-4405 の「不一致なら receipt identity を evidence 側へ正規化」は据え置く。

F-P3 / F-P4 は「gate の新設」ではなく、s1 materializer の consumer が同じ sort 軸の束縛値を転送するだけの
consumer 整合である。D1548 の「sort 軸へ局所適用」の範囲内で、他軸・他 driver への一般化はしない。
scope 外の一般化 (s8b 側に独自の契約 gate を置く、`_require_sort_oracle_contract` を s8b から呼ぶ) は採らない。

## レビュー A (identity/cache 意味論) の裁定 — 07:34 JST

- **A-1 (must-fix 申告、`source_digest._resolved_src_token` の stock 短絡が binder より先)** → **refuted・scope 外。**
  comparator が stock と同一 bytes に materialize される sort_best では、契約を改版しても token が `STOCK` のまま。
  これは D1630 が binder に定めた規約そのもの (loop 側の sort producer も同じ) で、bytes が stock と同一なら
  build 結果も stock binary であり、契約 ID の改版が binary を変えない以上 cache の再利用は stale build ではない。
  変更先は `source_digest.py` (本 wave の編集面外、D1630 の設計)。実装せず、設計観察として裁定パッケージに載せる。
- refuted 7 件 (宣言と oracle 値の不一致経路、prepare/evaluate 不整合、受理集合拡大、非 sort 漏れ、追加 consumer、
  D1630 違反、旧 freeze binding の黙認) は親の裁定と一致。追加 consumer 取り残しは無し。

## レビュー B (テスト検出力 / pin 閉包) の裁定 — 07:35 JST

- must-fix なし。nit 2 件は採用 (記録のみ、実装変更なし):
  - binder の preimage 計算は s1 のテストでは double に置換される。D1630 側のテストに委ねる (親の裁定と一致)。
  - M3 は prepare 側の 1 node だけが production 変異を殺す (run_role 側は独自 double で契約 ID を作るため緑のまま)。
    s4 の M3 期待「run_role 側も赤」は誤りで、期待 node は prepare 側 1 node に訂正する。
- 変異対応表: M1〜M4 は新規検出力。**M5 と M6 は既存テスト (`test_run_role_available_perf_keeps_evaluate_call_shape_exact`、
  `test_prepare_cell_passes_site_cxx_to_source_digest`) でも落ちる → 冗長 gate と明記し、新規検出力に数えない (DW-M03)。**
  本走の期待 node には既存 node も含めて完全集合を probe から取る。
- refuted 6 件 (sort_best cell は freeze fixture に 3 個で正例は恒真でない、zip の順序、非 PASS 後の非呼出、
  既存 assertion の弱化なし、第三 pin なし、揮発値なし) は親の裁定と一致。

## 焦点再レビュー C (fix 後) の裁定 — 08:02 JST

- 対応表: F-P1〜F-P4 すべて closed (partial / regressed なし)。must-fix なし。
- nit 1 件 (s8b 側 fixture の token は契約 ID を反映しない → binder preimage は s1 と D1630 側テストの担当) は
  レビュー B の nit と同じ整理で採用 (記録のみ)。
- refuted 3 件: floor の正規化分岐 (L4396) へ sort_best が入るのは drift / 注入 seam のみで既定 `build_v2` が拒否する、
  `prepared_for_eval` が `oracle_attempt` を写さないのは fix 前からで evaluate / binding 比較に使われない、
  fixture signature 変更に退行なし。親の裁定と一致。
- 変異対応表: M7〜M11 はすべて明示 assertion で殺せ、冗長 gate なし。
- fix2 (テスト側の key 名 `configuration_id` への修正 2 行) は commit 3 として取り込む。fix 巡は 2 回で DW-O16 の上限 3 内。

## 変異事前登録の追加 (DW-M01、fix 前)

| # | 位置 | 変異 | 期待して赤になるもの |
|---|---|---|---|
| M7 | s8b_oracle_driver `prepared_for_eval` | `sort_oracle_contract_id` の写しを落とす | driver の正例: sort_best row の evaluate_fn kwargs に契約 ID がある |
| M8 | s8b_oracle_driver evaluate kwargs | 転送の None 判定を落とし常に渡す | driver の負例: 非 sort_best row の kwargs に key が無い |
| M9 | s8b_floor_campaign L4383 | `resolve_evidence` への契約 ID を落とす | floor の正例: sort_best cell で `resolve_evidence` が契約 ID 付きで呼ばれる |
| M10 | s8b_floor_campaign build_kwargs | `build_kwargs["sort_oracle_contract_id"]` を落とす | floor の正例: sort_best cell の build_fn kwargs に契約 ID がある |
| M11 | s8b_floor_campaign | 非 sort_best にも契約 ID を渡す (None 判定を落とす) | floor の負例: 非 sort_best cell の resolve_evidence / build_fn kwargs に key が無い |
