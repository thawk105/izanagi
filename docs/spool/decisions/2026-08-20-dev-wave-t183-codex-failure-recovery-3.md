---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t183-codex-failure-recovery
seq: 3
---

## {{D:codex-failure-classification}}. codex 子の異常終了を seal 時不変な観測値だけから分類し、safety-filter 等の未観測原因を断定しない

**決定:** `tools/codex_worker_launch.py` の `_classify_failure()` は `codex_exit_code` /
`output_bytes` / validator の失敗理由リストという、`_seal_attempt()` 完了後に変化しない
入力だけから `failure_class` (`None` / `f43_fragment` / `f45_missing_output` / `other`)
を導出する純粋関数とする。`accepted` や `limit_trigger` のような後続処理
(`_latch_final_job_limit()` 等) で変わりうる field には一切依存しない。

**理由:**
- `accepted` は seal 後の複数箇所 (受入直前の最終 limit 再latch・receipt 監査・staging 後)
  で `False` へ後置反転しうる。分類をこれらの可変 field から導出すると、後置反転の前後で
  `failure_class` が矛盾した値になりうる。
- `f45_missing_output` という値名は「非ゼロ終了かつ成果物欠落」という構造的特徴だけを表し、
  「upstream safety-filter による kill」という原因を断定しない。launcher はプロセスの
  終了理由を判別する手段を持たず (grep で safety-filter 固有のマーカー文字列を探索したが
  repo 内に既存の検出ロジックは無かった)、原因を断定する名前を付けると未検証の主張を
  構造化データとして残すことになる。

**却下した選択肢:**
- `f45_safety_filter` という値名 — 原因を断定しており、構造的特徴だけを扱う設計と衝突する。
- 旧 schema (`failure_class` field 無し) の receipt を再検証時に受理する互換 shim — 呼び手が
  ゼロの経路 (`check-receipt` は repo 内に自動呼び出し元が無い) への投資は規律5 に反する。
  旧 receipt が新 exact-field-set で構造検査に落ちるのは、権威対象が実際に増えたことの
  正確な反映であり隠さない。
