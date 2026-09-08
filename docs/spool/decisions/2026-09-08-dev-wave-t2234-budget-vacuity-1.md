---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t2234-budget-vacuity
seq: 1
---

## {{D:budget-normative-limits-exact}}. 8c 予算 consumer は規範の「対称」「一致」を厳密一致で検査し、許容差を発明しない

**決定 (1): arm 上限の対称性と holdout 上限の和 = 総上限は、浮動小数の厳密一致 (`!=` / `==`) で
判定する。** `math.isclose` も `_TOLERANCE` も使わない。事前登録の規範
(`docs/phase3-8c-preregistration.md` の「累積ベンチ実時間の上限」の項) は「対称」「一致」としか
書いておらず、許容差の値はどこにも権威を持たない。

**決定 (2): arm 上限と holdout 上限は正値を要求する。総上限の正値は検査しない。**
holdout 上限が正で、その和が総上限に厳密一致するなら、総上限は必ず正である。冗長な検査は
等価変異を増やし、変異 matrix の証拠力を下げる。

**決定 (3): 予約値が 0 の cell が 1 つでもあれば `held` にせず `insufficient` にする。**
新しい state も新しい gate も足さず、既存の `symmetric_indeterminate` が実走前に 6 cell を
対称停止させる経路へ載せる。

**決定 (4): 規範に反する上限は `BudgetError` で拒否する。** `insufficient` にしない。
これは予算の不足ではなく入力が規範に反する状態であり、`insufficient` にすると supervisor が
`budget-insufficient` という誤った理由で報告する。

**理由:**
- 許容差を置くと、保証が別の形で恒真化する。段 3 の敵対レンズが、総上限 0.0・arm 上限
  `{0.0, 5e-10, 1e-9}`・holdout 上限 `{5e-10, 0.0}`・各 cell の予約 `5e-324` という入力が
  許容差版の 3 検査を**すべて通り**、総予算 0 のまま `held` になることを示した。
- 許容差の値を実装が決めることは、先行 insight
  (`output/insights/2026-09-02_t2159-c05-schedule-authority/README.md` §4.1 の R3) が
  「権威のない仕様を実装が決める」構図として却下した型そのものである。
- 厳密一致にしても既存の 3 層別 witness は保てる。層別比較が持つ `_TOLERANCE` の帯を使えば
  「総上限層だけが不足」する数値 witness を構成できることを実測した。
- ULP 級の差 (`math.nextafter(8.0, 9.0)` など) は厳密一致では拒否され `abs_tol=1e-9` では受理
  されるので、許容差を入れ直す変異を殺す負例になる。

**却下した選択肢:**
- 既存の ledger 再集計規約 (`math.isclose(rel_tol=0.0, abs_tol=_TOLERANCE)`) を流用する —
  上記の regime で保証が恒真化する。
- 予約 0 を `BudgetError` にする — 予約 0 は型として不正ではなく予算が足りない状態であり、
  既存の対称停止経路 (`insufficient` → `symmetric_indeterminate` → 全 cell 判定不能) が
  そのまま意味的に正しい。新しい失敗経路を作る理由がない。
- 総上限にも正値検査を足す — 決定 (2) の導出で不要。冗長な検査は単独では殺せない等価変異になる。
- 最低予約量を定める — 規範に無い。実装が決めれば決定 (1) が避けたのと同じ構図になるため、
  裁定へ返す。

**残る限界:** 上限も予約も `_TOLERANCE` 未満という極小正値 regime は依然 `held` になる。
これを閉じるには最低予約量か正式 workload の事前コスト計画との結合が要り、どちらも本決定の外である。
また `ReservationCell` は `_finite_nonnegative` の戻り値を field へ保存しないため、比較を上書きした
`float` subclass に対して予約の正値検査は健全でない。公開経路では JSON 読み戻しで
`BudgetError` になるため不整合な台帳は残らないが、この限界は主張せず記録する。
