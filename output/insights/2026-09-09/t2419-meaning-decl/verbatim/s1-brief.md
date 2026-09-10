# 段 1 brief — [T-2419] 非負 BACKOFF_FIXED に production の意味宣言を渡す

base main = cbcdb6c91 / branch = worktree-dev-wave-t2419-meaning-decl / 2026-09-09 JST

## 研究前進

論文の backoff 軸 (静的 backoff を要求する測定系列) は、「要求した µs でほんとうに走ったか」を
production 経路で保証できていない。非負 `BACKOFF_FIXED` の意味の節は常に `unestablished` のまま
admission され、その事実だけが成果物へ持ち越される。F718 (格子上端の生値 1000 が合成枝の符号化
境界と衝突し、実質 0 µs を測って成果物へ記録された) は、この宣言が無いために production では
捕まらない。**完了判定** = 静的 backoff を要求する driver 族の meaning 節が実 source の観測で
green になり、F718 と同型の要求 (生値 1000 を 1000 µs のつもりで出す) が build 前に止まること。

## scope

- **in**: `orchestrator/campaign/backoff_sweep.py` の `_require_backoff_condition_gate`
  (88-169 行) が、非負 `BACKOFF_FIXED` にも `MeaningWitnessDeclaration` を渡す。
- **in**: 正例 (生値 3000 の宣言 1000.0 が実 source の観測と一致して green) と
  負例 (生値 1000 を 1000.0 と宣言すると観測 0.0 と食い違って赤) の 2 本。
- **out**: `screening_driver.py` の別経路 gate (`test_screening_driver.py:200` が
  `("BACKOFF_FIXED", "unestablished")` を pin)、`b10_backoff_shape_sweep.py` の乱択 shape、
  新しい gate・検査・台帳・一般化、凍結成果物の再発行。

## 不変条件

1. **規律 2 を緩めない。** 受理集合は狭まる方向だけ動く (`unestablished` → `green` または `red`)。
   green へ転じるのは、実 source を compile した pointwise witness が宣言と一致した場合だけ。
2. `BACKOFF_FIXED = -1` の stock branch witness (`MeaningCase(-1, None, STOCK_ADAPTIVE_BRANCH)`)
   は現行のまま。supply 節・admission の既存契約も変えない。
3. 凍結成果物の bytes を変えない。`output/s1-freeze/known_axes_freeze.json` は
   `backoff_sweep.py` の sha256 = `4e7fa96e…` を記録するが、現行 file は `1b64f897…` で**既に乖離**
   している。現行 file との一致を要求する consumer は無い (あれば受入が既に赤)。再発行しない。
4. **恒真化の禁止。** 宣言は「driver が要求した意味」を述べ、判定器は「実 source を compile して
   観測した値」を返す。両者を同じ式から導かない (F718 のタグは [恒真ゲート])。
5. 新 test file を作らない (既存 `orchestrator/tests/test_backoff_sweep.py` へ追加)。

## 実アンカー

| 対象 | 位置 |
|---|---|
| 結線点 | `orchestrator/campaign/backoff_sweep.py:133-155` (`declaration=` の三項) |
| 判定器入口 | `orchestrator/campaign/condition_meaning_gate.py:3287` |
| 宣言型 | 同 `:406` `MeaningCase` / `:614` `MeaningWitnessDeclaration` |
| 非負値の検査 | 同 `:741` `_validate_define_value` (非負のみ) |
| C++ の意味 | `patches/silo-backoff-fixed.patch` の `EVOLVE-BLOCK` 合成枝 |
| 静的 codec | `orchestrator/campaign/backoff_extended_sweep.py:64,71` |
| helper の consumer | backoff_sweep / backoff_extended_sweep / backoff_profile / backoff_requested_us / backoff_repro / backoff_overthrottle の 6 本 |
| 追加先 test | `orchestrator/tests/test_backoff_sweep.py:148,172` の近傍 |

C++ 側の意味 (q = 生値 / 1000): q==0 → 生値、q==1 / q==2 → 乱択、q>=3 → 生値 - 2000。
したがって生値 3000 → 1000.0、生値 1000 → 0.0。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1) 宣言値の出所。** 親 = 生値から静的 codec で物理 µs を導き、その float64 を宣言する。
  生値 1000〜2999 (乱択帯) は静的 wire domain の外として build 前に拒否する。
  攻撃点 = (a) C++ の式を Python で書き直しただけで恒真ではないか、
  (b) 乱択帯を要求する正当な driver を将来塞がないか。
  対案 A = driver が物理 µs を明示的に渡す (6 driver の呼び出し面が広がる)。
  対案 B = 乱択帯は `unestablished` 据え置き (F718 型が production で捕まらないまま残る)。
- **(P2) codec の置き場所。** `decode_static_backoff_us` は `backoff_extended_sweep.py` にあり、
  同 module は `backoff_sweep` を import する。逆輸入は循環になる。
  親 = 静的意味の関数を `backoff_sweep.py` 側へ置き、extended は再輸出で互換を保つ。
- **(P3) 期待 bits の 2 文脈。** `CONTEXT_STARTS = (1, 2)`。静的域は `start` に依存しないので
  両文脈同値でよい。

## 成果物と分割

コード差分 + テスト + insight README + worklog fragment。実装面は 1 単位
(`backoff_sweep.py` + `test_backoff_sweep.py` + 循環回避に必要なら `backoff_extended_sweep.py`)。
Codex author 1 本。正しさ防壁に触り受理集合が変わるので、段 2・3 と段 6 の敵対レビュー 2 本は省かない。
実測環境は login node の python テストのみ (計算ノード投入なし)。
