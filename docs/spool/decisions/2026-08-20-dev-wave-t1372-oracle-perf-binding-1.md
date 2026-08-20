---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1372-oracle-perf-binding
seq: 1
---

## {{D:oracle-holdout-perf-binding}}. oracle 側の holdout perf 束縛は module 表との canonical bytes 比較に限定し、producer 側の arm resolver digest chain は複製しない

**決定:** `s8b_oracle_driver._perf_for_holdout` が freeze 文書から取り出す `records`/`threads`/
`ycsb`/`candidate_id` を、静的単一権威 `s8b_holdout_freeze.HOLDOUTS[holdout_id]` の同一4-key
projection と canonical bytes (`_canonical_bytes`、sort_keys=True の JSON 直列化) で比較し、
不一致・未知 holdout_id は fail-closed で拒否する。producer 側の同型実装
(`p3_autonomous_workload_trial._assert_formal_entry_binding`) が追加で行う arm resolver の
descriptor digest chain・legacy freeze 照合は oracle 側では複製しない。

**理由:**
- 段階導入規律5 (盛らない) — oracle 側が今回埋める穴は「freeze 文書の値が module 表と一致するか」
  だけであり、producer 側の arm resolver 整合は別の懸念 (どの arm が選ばれたか) を守るための
  別レイヤーで、oracle の実走直前の役割には不要。
- 段3敵対相談 (整合・実効性レンズ) が「producer と oracle は同一構造 (module 表束縛) だが
  信頼境界の強度は異なる」と指摘し、DW-G03 の独立2例は「同じ保証の二重化」ではなく
  「同一パターンの異なる強度での独立適用」として成立すると確認した。
- 既存の関連3層 (`RatifiedFreeze.holdouts` property の candidate_id のみ束縛、
  `s8b_holdout_freeze.verify_document()` の全field束縛だが `gate-check` CLI 限定、
  `_verify_snapshot_layer1` の holdout 集合+unknownness hash のみ) はいずれも
  `run_block`→`_perf_for_holdout` の実走経路を保護しておらず、既存機構の拡張より
  自己完結の新規検査を追加する方が変更面が小さく検証しやすい。

**却下した選択肢:**
- `RatifiedFreeze.holdouts` property を records/threads/ycsb まで拡張し `run_block` 側もそれを
  経由させる案 — 変更面が `run_block` や他の `.document` consumer にも波及し、本 wave の scope
  (2ファイルの narrow な追加) を超えるため不採用。
- producer 側と同じ arm resolver digest chain 照合まで複製する案 — oracle は「選ばれた arm が
  何か」を判定する層ではなく、既に選ばれた holdout の perf 条件を実走直前に検証する層であるため、
  同じ検証をもう一層持つ理由がない。
