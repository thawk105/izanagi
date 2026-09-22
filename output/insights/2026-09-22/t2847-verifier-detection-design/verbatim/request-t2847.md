# 依頼の逐語 (ユーザー直接起動の /dev-wave、2026-09-22 08:5x JST)

```
[T-2847] (P1、VLDB P0、D2212) verifier の検出力と容量を計算なしで設計する。期待結果つき小履歴コーパス
  (直列化可能・異常・abort・欠損 trace・初期値・同一キー複数操作) と、意味の異なる CC 変異 20〜40 個の検出期待表を作る。既存の
  patches/broken-*.patch 16 本と verifier の再利用範囲、si の trace が v1 形式で現行 parser に拒否される制約も明記する。大 trace
  の容量評価の計画 (output/insights/2026-09-20/verifier-capacity/README.md、[T-2351] との関係) と、論文用の射程文「certified
  は有限の観測履歴に対する判定で、全実行の証明ではない」も書く。実 trace の取得・変異の実走・parser 改修は含めない。一次資料
  output/insights/2026-09-21/vldb-direction/gap-analysis.md §4 P0。本題だけ、gate・検査・台帳の追加は scope 外。着手直前の local main から
  fresh worktree。
```
