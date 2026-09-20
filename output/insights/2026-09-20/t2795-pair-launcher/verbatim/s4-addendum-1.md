# 段 4 裁定 追補 1 — stock source の build admission (author の未了報告への裁定)

親 (Claude、2026-09-20 13:49 JST)。入力 = codex/s5-author.md「未了・懸念」、`orchestrator/campaign/build_admission.py:660–705`
(`derive_build_admission`)、`orchestrator/campaign/pin.py:28` (`CURRENT_PIN = "511c953"`)、`orchestrator/campaign/pipeline.py:1795–1860`
(evidence 解決 → `capability_resolver` → `derive_build_admission`)、既存 driver の先例 `backoff_extended_sweep.py:1373–1382`、
`backoff_sweep.py:420–425`、`b10_backoff_static_tail_formal.py:746–747` (いずれも `attest_generator_output(build_context, evidence, generator_input_sha256=...)`
を `capability_resolver` で渡し、`GeneratorId.BACKOFF_SWEEP` の generator receipt で source を admission する)。

## 事実 (real)

- `derive_build_admission` の STOCK_BASELINE 分岐は `source.src_token == STOCK and source.tracked_clean is True and source.ccbench_commit == CURRENT_PIN`
  の exact 比較。S4 の `PIN` は full SHA (`511c9538e4e8…`)、`CURRENT_PIN` は短縮 `511c953` なので stock source でもこの分岐に入らない。
- 続く分岐は review receipt / generator receipt / coder authority。stock 経路は coder authority を持たない (裁定 §2-1 項 2・3) ので、
  resolver 無しでは「source evidence は stock/review/generator/coder のどれも支持しない」→ `_prebuild_abort("admission-error")` になる。
- 既存 driver で stock genome を同じ `GeneratorId.BACKOFF_SWEEP` の build context から評価するものは、`capability_resolver` で generator receipt を
  発行して admission を通している (上記先例)。これは既存 admission class (MACHINE_GENERATED) の正規 seam であり、gate の受理集合は変えない。

## 裁定

1. **採用:** stock 経路 (`_run_stock_control_resolved` の `run_campaign` 呼出し) に限り `capability_resolver` を渡す。
   `resolver(evidence)` は `evidence.src_token == source_digest.STOCK` のときだけ
   `attest_generator_output(build_context, evidence, generator_input_sha256=hashlib.sha256(f"p3-s4-loop-stock-control/v1|{evidence.genome_sha256}".encode("utf-8")).hexdigest())`
   を返し、**それ以外 (非 STOCK) は `None` を返す** (→ pipeline が admission-error で abort。fail-closed)。候補経路 (`_run_one_iteration_resolved`) は
   従来どおり resolver 無し (coder authority の CODER_AUTHORED)。
2. 裁定 §2-1 項 7 の成功条件 (`variant == variant_id(genome)` かつ BUILD_START `src_token == STOCK`) は**そのまま残す** (二重ではなく層が違う: resolver は
   admission 時、成功条件は WAL 記録時)。
3. admission class は `machine-generated` (generator `backoff-sweep`) として WAL / admission receipt に残る。stock-baseline class にならない事実を insight に
   記録する (source の STOCK 性は src_token で保証され、class 名は admission の経路を表す)。`build_admission.py` の pin 比較の正規化 (full / short) は
   admission gate の変更 = 規律 2 の防壁側なので本 wave では行わず、裁定パッケージ候補として §5 へ記録する。
4. 失敗している `test_stock_digest_refresh_keeps_checkpoint` は実 pipeline の admission を通す形で緑にする (fixture を緩めない)。
5. 変異を追加登録: **M16** = resolver が非 STOCK evidence にも receipt を返す (`if evidence.src_token == STOCK` を外す) → 新 test
   `test_stock_resolver_refuses_non_stock_evidence` (実 `_run_stock_control_resolved` を呼び、非 STOCK evidence を返す `source_digest.resolve_evidence`
   の境界 stub で pipeline 実 admission が abort し `outcome=aborted`、WAL ABORT reason `admission-error`) で kill。
   **M17** = stock 経路が resolver を渡さない → `test_stock_digest_refresh_keeps_checkpoint` (実 pipeline admission で abort する) で kill。

## 手順の差 (DW-O12)

裁定 §2-1 項 5 の順序に「`run_campaign(..., capability_resolver=_stock_capability_resolver(build_context))`」を足す。他は不変。
