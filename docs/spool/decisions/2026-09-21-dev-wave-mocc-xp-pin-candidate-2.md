---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-21
wave: dev-wave-mocc-xp-pin-candidate
seq: 2
---

## {{D:mocc-xp-candidate-keeps-d297-include-rule}}. mocc の X/P 計装を pin 候補へ載せるときは D297 検査器の include 規則を緩めず、計装側を include 行不変の形へ直す

**決定:** T-2294 (D1686) の X/P 計装を e9e477ca の子 commit として載せる候補は、`cc/mocc/transaction.cc` の include 行列を e9e477ca と同一に保つ
(`#if TRACE` 内にも `#include` を足さない)。`tools/check_trace0_preprocess_identity.py` の受理集合 (mocc の trace.hh 1 行だけを追加として許す) は変えない。
P 検査の容器は、同じ `#if TRACE` 枝で include される `include/trace.hh` が供給する `<unordered_set>` の `std::unordered_multiset<const void*>` を第一案とし、
容器の最終選択と正例・負例の実走経路は次の実装 wave の段 3・段 4 で確定する。T-2294 の patch (`patches/instr-mocc-lock-coverage.patch`)・compute JSON・test は
e9e477ca + patch という旧命題の証拠として bytes 不変で保持する (規律 7)。

**理由:**
- 計装 patch をそのまま commit した候補は D297 検査で rc=1「include 行文字列（順序込み）が不一致」になった (2026-09-21 実測)。原因は `#if TRACE` 内の `#include <set>` の追加である。
- D297 は header を含む差分を拒否し、TRACE=0 正規化前処理出力と include 活性の同一性を保証の中身にする。検査器は mocc の trace.hh 1 行の追加だけを
  機械検証可能な例外として受理する (`_mocc_trace_include_addition_index`、経緯は `output/insights/2026-08-23_t1506-mocc-trace0-unblock.md`)。
  include を足す計装を通すために受理集合を広げるのは、観測者効果の検査 (規律 1) を候補に合わせて緩めることになる。
- 修正は 3 行 (`#include <set>` の削除と宣言の型 2 箇所) で済み、GCC 11.4 / 12.3 の D297 が pass、include 比較は 16 context とも `exact_identity`、既存の負例 patch 4 本も厳密適用で当たった (同日実測)。
- 本決定は Codex の敵対検査 (段 3) を経ていない。検査器を変えないこと自体は規律と D297 から直接従うので先に記録し、容器の選択は検査の後に確定する。

**却下した選択肢:**
- 検査器に `<set>` などの標準 header の追加を許す — 受理集合の拡大であり、規律 1 の防壁を候補に合わせて緩める形になる。
- `#line 17` まで除いた版 — D297 は通るが、負例 patch の early-unlock / hot-update-unlock が先頭 hunk の文脈 (`#line 17`) を失って当たらない (同日実測)。
- T-2294 の compute 実測 (job 979791) を内容同一性で候補へ引き継ぐ — P ブロックの型と include 1 行の bytes が違うので同一内容ではない。候補の上で正例・負例を再走する。
