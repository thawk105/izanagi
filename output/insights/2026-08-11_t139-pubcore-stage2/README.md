# [T-139] 公表 core 段階 2 — 成果物

worklog 404 の裁定 **C-1〜C-5 (全問 (a))** を実行した wave の成果物。
**実装差分ゼロ (docs-only)。**3 文書はいずれも `authority: none` であり、凍結されていない。

## 読む順

| ファイル | 何か |
|---|---|
| `package.md` | **裁定パッケージ。まずここを読む。**凍結承認 (Q5〜Q7) と、裁定時点で未見だった新事実 4 件 (Q1〜Q4) |
| `publication-core-v2.md` | 公表手続きの新 core の**承認候補**。段階 1 版からの変更は 5 行だけ |
| `addendum-b-v2.md` | 追補 B の**再発行版**。`b03` の縮小 1 点のみ。`b01`・`b02` は初版の逐語 |
| `addendum-p-draft.md` | 追補 P の**草案**。従属先 commit が未確定のため凍結対象ではない |
| `verbatim/` | 段 2〜段 6 の子出力の逐語凍結 |

## 前段からの位置づけ

- 段階 1 = `output/insights/2026-08-10_t139-publication-core/` (land 済み)。
  新 core の草案と、C-1〜C-5 の裁定パッケージ。
- 追補 B 初版 = `output/insights/2026-08-09_t139-addendum-b/` (land 済み)。**不変のまま残す。**
- source study の凍結 core = `output/insights/2026-08-07_t139-mainrun-design/preregistration.md`。
  追補 A = `output/insights/2026-08-08_t139-addendum-a/`。**いずれも 1 byte も触れていない。**

## この wave が確定したこと

1. **`b03` の正本は本 wave が持つ。**land 2 側 (`output/insights/2026-08-11_t139-manifest-land1/package.md`
   の §S7 表 7 行目) は「記録要件が未凍結」という要件の指し先で、定義を持たない。
   機械執行は C-5 (a) により producer 実装 wave。**定義 / 要件 / 執行に分かれ、二重定義は生じない。**
2. **新 core v2 の変更は 5 行だけ** (104, 105, 569, 570, 571)。行数は不変。
   §8.1 の「どちらが正本か未確定」という一節を、C-2b (a) の結論へ差し替えた。追補 B を参照しない。
3. **追補 B v2 の変更は `b03` の縮小 1 点だけ。**落とした 5 項目は `addendum-b-v2.md` の
   末尾節で逐語に列挙した。`fields` が `{b01, b02, b03}` を過不足なく解決することを
   repo の実装で機械確認した。
4. **追補 P は凍結できない。**従属先 `core_ref.commit` は先例では「承認決定を canonical 台帳へ
   fold した commit」であり、それは承認の後にしか存在しない。草案のまま置いた。

## 機械確認したこと

| 検査 | 結果 |
|---|---|
| envelope の exact-key (`orchestrator/preregistration/addendum_envelope.py`) | 追補 B v2 = `{b01,b02,b03}` / 追補 P = `{p01,p02,p03}` / 初版 B = `{b01,b02,b03}`。3 件とも OK |
| 新 core v2 の差分行 | 5 行 (104, 105, 569, 570, 571)。総行数 698 で不変 |
| 凍結 core・追補 A の bytes | 変更 0。pin は `orchestrator/tests/test_t139_preregistration_binding.py` の 2 件のみで、本 wave は触れていない |
| C-1 の数値 | 親が前 wave の probe で再現し、段 3 のレンズ A が別経路で独立再検算 |

## 主張しないこと

- **凍結された、とは主張しない。**3 文書とも `authority: none`。発効は承認決定の fold 以後。
- **本走・pilot が投入可能になった、とは主張しない。**B8 (a) により依然不可。
- **公表表が生成できる、とは主張しない。**公表層の実装は 1 byte も存在しない。
- **`b03` の縮小が受理集合を狭める方向だけに働く、とは主張しない。**投入前 admission を 1 つ失う。
  `package.md` の Q1 でユーザー裁定へ返した。
