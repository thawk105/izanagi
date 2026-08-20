---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1445-buildcache-toolchain-hit-check
seq: 1
---

## {{D:buildcache-hit-time-toolchain-provenance}}. v2 build cache hit 時にも expected_toolchain_manifest との完全一致を照合する (D602 の恒久対応)

**決定:** `buildcache.py` の v2 build cache completion.json へ、`expected_toolchain_manifest`
付き caller (`complete_toolchain_manifest is not None`) のときだけ full-version toolchain
manifest とその sha256 を条件付きフィールド (`complete_toolchain_manifest`/
`complete_toolchain_manifest_sha256`) として保存し、`_validate_v2_entry` の hit 経路でも
同じ値との完全一致・sha256 一致を要求する。D602 が「次wave scope」として明示的に切り出した
既知の限界 (cache hit 時に toolchain 束縛を検査しない) の恒久対応であり、D602 自体は編集せず
本 D が同 waiver をこの範囲 (expected 付き v2 hit) に限って supersede する。

**設計の核心 (cross-lane 衝突の回避):** 新2 field は `_validate_v2_entry` の既存 `expected_keys`
完全一致集合に**含めない**。`expected_toolchain_manifest`/`declared_use_class` は
`_v2_identity` の preimage に一切含まれず cache digest に無関係なため、同一 digest を
official/非 official caller が両方 hit しうる (段2 codex プラン・段3 敵対相談で実コード
grep により確認済み — pipeline.py の cache_root は既定で共有固定パス、screening_driver.py
は同一 admission のまま expected の有無を切り替え可能)。新2 field は「今回の caller が
要求する場合だけ存在確認+完全一致を要求し、要求しなければ存在有無を問わない」独立 gate
にした。これにより `expected_toolchain_manifest=None` の既存呼び出し (大多数の Phase 3
探索 build) の挙動・completion.json 形状は不変。

**運用影響の訂正:** 段1 brief 時点では「hit 不一致時に campaign 全体が fatal stop する」と
懸念したが、段3 敵対相談レンズBが実コードで反証した。`BuildCacheError` は `RuntimeError`
を継承し `pipeline.py` の `except (RuntimeError, subprocess.SubprocessError)` が捕捉して
`_abort("build-error", ...)` に変換するため、影響は該当 variant 1 件の `build-error` abort
(non-retryable terminal) に留まり、campaign プロセス自体は継続する。ただし同一 campaign
内での自動再評価は無く、cache entry 削除だけでは変異が復旧しない (WAL 側の再評価手段が
別途必要)。この復旧手順の要否は本 D の scope 外とし、裁定パッケージ候補として worklog へ
記録する。

**根拠:**
- D602 (`docs/decisions.md`) が明示的に次wave へ送った「完全な解決」の実装である。
- 段3 敵対相談2レンズが独立に P1-1 (digest 非依存)・P1-3 (cross-lane 衝突の実在性) を実コードで
  確認し、段2 codex プランの結論を追認した。
- 段6 敵対レビュー2本 + fix + 焦点再レビューで real 所見4件 (DW-M01単一理由性の担保・
  expected付き非official経路の網羅・completion assertion・docstring精度) をすべて closed に
  した。変異matrix (2変異事前登録、DW-M01) は 2/2 KILLED・MISMATCH 0・SURVIVED 0。

**却下した選択肢:**
- **新2 field を既存 `expected_keys` へ常時混入する (widen the exact-match set
  unconditionally)** — official が書いた entry を非 official caller が読めなくなる
  (逆方向も同様)、cross-lane 衝突を悪化させるため見送った。
- **cache hit を無効化し常に新規 build する** — D602 が既に却下した選択肢と同じ理由
  (buildcache 全体の cache-first 設計方針を局所的に覆す) で見送った。
- **既存 v2 cache entry を本 wave で一括無効化・再構築する** — 規律5 (段階導入・盛らない)、
  影響範囲の広さ (既存 official 系 campaign 全体) により見送った。fail-closed な hit 時検査を
  追加すれば、旧 entry を実際に hit した時点で個別に検出される。
