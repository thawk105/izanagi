# [T-2027] 着地済み D1192 実装の独立監査 (2026-09-01)

D1192 択 (1) の実装 (`2e35a2596`) を、素性不明の外部作業物として内容監査し (規律 6)、
着地した wave の plan・敵対相談・段 6 レビューがいずれも見落とした受理境界の欠陥 4 件を直した
wave の一次資料。**実装そのものの記録は着地した wave 側にある。** ここに置くのは監査・裁定・
レビュー逐語・変異の証拠だけである。

## この directory の中身

| file | 内容 |
|---|---|
| `brief.md` | 段 1 brief。監査の file 単位の採否判定を含む |
| `s4-adjudication.md` | 段 4 裁定。親の独立監査が見つけた欠陥 3 件と変異事前登録 |
| `s6-review-adjudication.md` | 段 6 レビュー裁定。real / refuted / scope 外の判定と根拠 |
| `review-a-correctness.md` | 段 6 敵対レビュー A の逐語 (正しさ境界・受理集合レンズ、採用) |
| `review-a-attempt1-not-accepted.md` | 同 A の 1 回目。**未採用** (`## 総括` 欠落で `f43_fragment`)。所見は親が実測で確認してから採用した |
| `review-b-closure.md` | 段 6 敵対レビュー B の逐語 (呼び出し閉包・実効性レンズ、採用) |
| `mutation-prereg` 相当 | `s4-adjudication.md` と `s6-review-adjudication.md` の変異登録表 |
| `mutation-spec-probe.json` | 期待 node 採取用 spec (全件 SURVIVED 期待) |
| `mutation-spec-real.json` | 本走 spec (実測した完全 node 集合を KILLED 期待で登録) |
| `mutation-erratum.md` | 期待 node を実測で確定した経緯と、前 wave の集合との差の理由 |
| `mutation-result.md` | 本走の判定と期待 node、probe の集計 |

## 直した欠陥 4 件 (いずれも受理境界)

| ID | 内容 | 実測 |
|---|---|---|
| A | v2 の path `"."` が正規化を通過し `parts[-1]` で uncaught `IndexError` | 公開 API から例外が漏れることを実行して確認 |
| R1 | 先頭が `//` の絶対 path が二重 slash を保存し `relative_to` で uncaught `ValueError` | 同上 |
| B | masstree 根の解決が external input を admit しない build まで必須化されていた | 呼び出し条件をコードで確認 |
| C | `_strict_root` が symlink 経由で綴った根を拒否 | 実在 symlink で拒否を確認 |

A と R1 は同族である。呼び手はいずれも `except CompilerInputError` しか持たないため、
binary admission receipt の発行器が anomaly の構造化拒否ではなく異常終了する。
v1 は同じ入力を処理できていたので受理境界の退行にあたる。

## 主張しないこと

- **現在の canonical 根へ再束縛するのは `fetchcontent-masstree` と分類された入力だけである。**
  `filesystem` 入力は記録時の絶対位置で bytes を検査する。この限界は主張せず記録する。
- oracle の descriptor 経路には再束縛先の安定した根が存在しないため、この wave の修正では
  救われない。v2 化の前も同じ経路が落ちていた。
- 床値実測の主経路が緑になるとは主張しない。消える根の第 2 クラス (job 専用作業領域) は
  D1322 が裁定した別の変更単位である。
- 変異 matrix が示すのは、登録した 10 変異が焦点 4 file の範囲で kill されることだけである。
  gate と検査を同じ主体が変更できる限り、意図的な弱体化への完全な防壁ではない (D387)。
