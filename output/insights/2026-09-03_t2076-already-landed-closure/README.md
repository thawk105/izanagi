# [T-2076] 依頼された設計は既に着地済みだった — 残件は台帳 2 件と現役 docs 1 箇所 — 一次資料

wave branch `worktree-dev-wave-t2076-sort-oracle-ir-design`。着手時 local main `7013ea81f`。

ユーザーは「[T-2076] の設計 wave を起票し、設計文書へ『これは先行実験と別の実験である』ことを
明示的に書け」と依頼した。**着手前の一次資料照合で、その設計と実装が 2026-09-02 に [T-2145] として
既に local main へ着地していることが分かった。** よって新しい設計文書は作らず、依頼の充足を
実物で確認したうえで、同じ着地が終端させた台帳の取りこぼしと、その着地が自ら must-fix と
裁定しながら落とした現役 docs 1 箇所を閉じた。

**この wave は D344 の実験同一性の論点を supersede しない。** 既に着地した [T-2145] の
記録も書き換えていない。歴史記述の遡及改変はしていない。

## 構成

- `s1-brief.md` — 段 1 brief (親)。scope・不変条件・実アンカー表・親の provisional 裁定。
- `s4-adjudication.md` — 段 4 裁定 (親)。real/refuted、採否、scope。
- `verbatim/lens-a.md` — 段 3 敵対検証子 A (充足の検査、`stage=consult`、`lane=sol`)。
- `verbatim/lens-b.md` — 段 3 敵対検証子 B (台帳の検査、`stage=consult`、`lane=luna`)。

## 依頼の 3 要件が landed main で満たされていること (親が現物で照合)

| 依頼の要件 | landed main の実アンカー |
|---|---|
| 設計と実装 | commit `23565ae55`「[T-2145] sort SWO oracle の受理言語を検証済み IR へ縮める」。`git merge-base --is-ancestor 23565ae55 main` が真 |
| 設計文書の実在 | `output/insights/2026-09-02_t2145-sort-oracle-ir/` (README、s1-brief、s4-adjudication、s5-agent-review、s6 裁定 2 本、変異台帳 3 本、verbatim/) |
| 「先行実験と別の実験である」の明示 | `output/insights/2026-09-02_t2145-sort-oracle-ir/README.md:6-8`、`.claude/agents/coder-v4-autonomous-sort.md:93`、`orchestrator/campaign/p3_s4_loop_sort.py:317` |
| 既存の実験同一性の主張を上書きしない | 同 `README.md:64`「D344 を supersede した — していない。実験同一性の論点は生きたままである。」、`.claude/agents/coder-v4-autonomous-sort.md:94`、`p3_s4_loop_sort.py:321`、`s4-adjudication.md:112-114` |
| 規律 2 を緩めない | 受理言語を 79 値の閉じた IR へ**狭める**。行列の出所を候補実行から trusted evaluator へ移し、不一致は `PASS` でなく `UNAVAILABLE` (`sort_swo_oracle.py:2981-2985`、`:3431-3445`) |
| 順序依存の後続の解禁 | 後続は [T-2145] 自身。着地済みで carry から消えている |

## 親が実測した事実

いずれも子の主張を鵜呑みにせず親が現物で確かめたものである。

| # | 事実 | 測り方 |
|---|---|---|
| 1 | `23565ae55` は現行 main の祖先 | `git merge-base --is-ancestor` |
| 2 | worklog entry 1214 は [T-2145] を完了にしたが、`[T-2076]` と `[T-1700]` を素の carry のまま残した | `docs/archive/worklog-phase3-0902-1214.md:64-66,250,360` |
| 3 | [T-2145] の段 6 裁定 F4 は `docs/phase3-s5-sort-runbook.md:190` を「親が段 7 で書く」と分割したが、着地していない | `output/insights/2026-09-02_t2145-sort-oracle-ir/s6-review-adjudication.md:49-55` と、是正前の runbook 本文 |
| 4 | F4 の fix 子担当分 (2 docstring) は着地済み | `orchestrator/campaign/p3_s4_loop_sort.py:47-50`、`orchestrator/campaign/s6_sort_sweep.py:28-32` |
| 5 | IR が確定した経路では compile / run / timeout / 非決定性 / 実 TU 不一致がすべて `UNAVAILABLE` へ行き、`PASS` へ倒れる経路は無い | `sort_swo_oracle.py:2965-2985`、`:3431-3450`、`:446-460` |
| 6 | `docs/phase3-s5-sort-runbook.md` の bytes を pin する台帳・trust root は無い | `git grep -n "phase3-s5-sort-runbook"` の全 hit を分類 (参照・archive・insight のみ) |
| 7 | `[T-2076]` の carry 鎖の実体は entry 1184、`[T-1700]` は entry 956 | `docs/archive/worklog-phase3-0902-1184.md:355-357`、`docs/archive/worklog-phase3-0825-956.md:706` |

## 主張してはいけない

- **[T-2145] の実装が正しいことを再検証した** — していない。本 wave は [T-2145] の記録と
  landed コードの記述の**一致**だけを見た。oracle の挙動そのものは再実測していない。
- **[T-2145] の「766 passed / 変異 11/11 KILLED」を独立に確認した** — していない。
  段 3 レンズ A も同様に認定していない。
- **依頼の全要件を機械が検査した** — していない。要件の充足は親と子 2 本の逐語照合による
  人間可読な判定である。
- **実験同一性の論点を裁定した** — していない。D344 の論点は生きたままで、ユーザー裁定の領域である。

## 三軸語・placeholder の走査

holdout の三軸 conjunction (`rratio` / `skew` / `rmw` の組) は
`orchestrator/campaign/s8b_holdout_freeze.py:699` の `holdout_conjunction_hits` が権威であり、
本 wave の新規・変更 file の主題 (sort comparator の受理言語と worklog carry) には
どの軸の値も現れない。機械的裏づけは受入全走の repo scan invariant 試験群が担う。
`verbatim/` 配下は D205 により placeholder guard・三軸語検査の対象外である。
