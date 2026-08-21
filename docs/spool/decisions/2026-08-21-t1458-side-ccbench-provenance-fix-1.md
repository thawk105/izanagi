---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: t1458-side-ccbench-provenance-fix
seq: 1
---

## {{D:ccbench-pin-drift-revert-over-cascade}}. 承認pin (CCBENCH_FULL_SHA) が実gitlinkから漂流したら、能動gateの有無を確認してから revert を canary hold / cascade より優先する

**決定:** `orchestrator/campaign/s8b_approved.CCBENCH_FULL_SHA` のような「承認済みpin定数」が
実 gitlink と食い違ったとき、対応方針を選ぶ前に **その pin を検査している全経路を、受動的
canary (test suite 内の複製 assert) と能動的 gate (実際に凍結発行等を行う本番関数内の
fail-closed 検査) に分類する**。能動的 gate が1つでも存在し、かつ今すぐその機能 (今回は
S8b floor campaign の新規凍結発行) を使う具体的な予定が無いなら、canary の hold や
campaign-id golden の連鎖修正より、**pin 前進そのものを revert する方を優先する**。
revert が下流 wave (今回は T-755, MOCC trace hook) に影響しないかを、そのユーザー裁定前に
本人へ確認する。

**理由:**
- 受動的 canary (`test_ccbench_full_sha_matches_real_gitlink`) は既存の
  `freeze_verification_hold.py` パターンで安全に hold できる — 対応する能動 gate
  (`s8b_floor_campaign._assert_sealed_protocol_ccbench_pin`) が既に同じ hold
  (2026-08-12 裁定) の対象であり、hold してもfail-closed側の実防御は変わらないため。
- しかし `build_protocol_document()` の C4-4 検査は **hold機構を経由しない別の能動 gate**
  であり、これは「今すぐ新しい承認済み protocol を、承認されていない ccbench で焼ける」
  状態を防ぐ本物の防御であるため、hold すべきではない。この gate は pin 不一致時に
  無関係な10件のテスト (env_tag 未登録の拒否テスト等) まで巣専える副作用があり、
  「canary だけ hold すれば十分」という早計な判断を誤らせる。
- 一方 CCBENCH_FULL_SHA を pin に合わせて再承認すると、campaign-id が
  `ident.canonical_preimage` の pre-image に pin を含む設計 (`orchestrator/campaign/pin.py`
  の docstring が明記する「正直な content-addressed 挙動」) のため、無関係な
  campaign-id golden 値 (`_CURRENT_POLICY_BOUND_CAMPAIGN_IDS` 等) が50件超連鎖的に
  ズレる。これは正しく計算し直せば解消するが、pin 前進自体が今すぐ必要でないなら
  過剰な作業になる。
- revert は「実際に certified な結果を偽って主張した事象」がまだ発生していない
  (hook は `#if TRACE` で inert、誰も新pinで実測を回していない) 時点でのみ安全に
  選べる。発生後は revert では収拾がつかず (a) の再承認 cascade を選ぶしかない。

**却下した選択肢:**
- **canary hold のみで済ませる**: `build_protocol_document()` の能動 gate を見落とし、
  fleet を完全には解放できない (実測: 10テストが残留)。
- **CCBENCH_FULL_SHA 再承認 + 60件超の golden 連鎖修正を今すぐ仕上げる**:
  当該 pin (MOCC trace hook) を今すぐ使う予定の T-755 自身が「outer gitlink を
  参照しない設計なので revert で無影響」と回答し、緊急性が無いと判明したため、
  fleet 解放を優先し revert を選んだ。将来 T-755 が正式に統合する際は D16 の
  `izanagi-trace` ブランチ経由の正規プロセスで pin 前進をやり直す。
