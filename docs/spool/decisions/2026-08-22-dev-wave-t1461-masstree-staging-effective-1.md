---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-22
wave: dev-wave-t1461-masstree-staging-effective
seq: 1
---

## {{D:t1461-masstree-staged-transport-design}}. floor masstree staged FetchContentの独立検証設計

**決定:**
1. 独立 expected hash (config.h / archive の sha256) は `tools/pegasus/policy.json` の
   凍結 pin closure (`third_party_sources`) ではなく、新規
   `tools/pegasus/policies/floor_masstree_payload_v1.json` へ配置する。
2. staged FetchContent の base dir 引数 (`fetchcontent_base_dir`) を
   `REFREEZE_DISQUALIFYING_SEAM_NAMES` へ登録し、明示的に staged payload を指定した
   pilot run を refreeze 対象外とする。

**理由:**
- (1) `policy.json` の `third_party_sources` は既存の凍結 pin closure に属する。同じ file へ
  独立 hash を追記すると、独立検証 (pin 自体が改ざんされていないことを pin とは別経路で
  検証する) という目的が pin closure との結合によって損なわれる。別 file へ分離することで
  payload policy 自体の bytes も binding へ束縛でき (postflight で再検証)、pin closure とは
  独立した監査対象として扱える。
- (2) refreeze (再凍結による official 昇格) は official 実行と完全に同一条件の pilot 実行を
  要求する。staged FetchContent (network 非依存 transport) はデフォルトの network 経由
  FetchContent と異なる依存解決経路であり、この経路差自体が実行条件の同一性を破るため、
  refreeze 対象から除外する。

**却下した選択肢:**
- 独立 hash を `policy.json` へ直接追記する — 凍結 pin closure との結合により独立性が
  損なわれるため不採用。
- `fetchcontent_base_dir` を `REFREEZE_DISQUALIFYING_SEAM_NAMES` へ登録しない
  (staged/非staged を区別しない) — official/pilot の実行条件同一性という既存の不変条件を
  壊すため不採用。
