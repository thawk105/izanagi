結論は **NO-GO** です。指定ファイルはすべて読取可能でした。静的検査のみで、編集・git 操作・pytest 実走はしていません。

数値検算では、`u_K`、判定境界・倍率、χ²検出力表はいずれも提示値と一致しました。5分/窓を未丸めで使えば K=15 ≈1.25→1.3 node-hours も整合します。

## ADV-01〜10 対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| ADV-01 | `partial` | K・M・窓代表値は定義されたが、θ は「5 session-median の中央値」のCV。一方、現行 compare 用 floor の測定単位は「1 session-median」であり、consumer と estimand が未接続のまま。平滑化により floor を過小評価し、偽 faster 側へ受理集合を動かしうる。[v2 §2.1](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:40)、[stability.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t425-floor-scoping/orchestrator/calibrator/stability.py:102) |
| ADV-02 | `closed` | 効果量別の検出力表と K=8/15/25 の operating point が追加され、K の選択をユーザー裁定へ返している。表の全数値も再計算と一致。[v2 §2.3](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:69) |
| ADV-03 | `closed` | U-7 が generic scalar と official 8b/8c per-pair 義務を明確に分離し、置換時は再凍結・別裁定と規定した。[v2 U-7](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:150) |
| ADV-04 | `partial` | 非転移は明記されたが、同じ文書が rr5/Linux由来の1.3〜1.5倍帯を「尤もらしい」として K=15 推奨に使用する。H1/H2へ転移しないという留保と標本数推薦の根拠が矛盾する。[v2 §2.3](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:83)、[v2 U-1/U-4](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:104) |
| ADV-05 | `closed` | √2 の同分散・独立条件と限界を明記し、正式な構成対は official RSS に残した。[v2 §2.2](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:61) |
| ADV-06 | `closed` | 境界 1.180/1.453/1.611%、倍率1.50/1.85/2.05は正しい。時間成分0.878%は丸めた `u=1.80` による値で、精密値は0.881%だが結論を変えない。[v2 §2.2](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:56) |
| ADV-07 | `closed` | Kを事前固定し、中間値による停止・増補を明示的に禁止した。[v2 U-3](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:117) |
| ADV-08 | `partial` | model-based近似との留保は追加されたが、直前では依然「5%保証」、検出力表では「χ²厳密計算」と無条件に表現する。bootstrapとの大小比較だけではCVに対する95%被覆は較正されない。[v2 §2.2–2.3](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:54) |
| ADV-09 | `closed` | 387秒の実測、build・rep数・署名数から約5分/窓へ外挿する前提が示され、K別費用も丸め込みで整合する。[v2 §2.4](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:90) |
| ADV-10 | `closed` | abort率がwithin代表rep由来であることと、「独立session」が時間窓独立性を意味しないことを明記した。[v2 §1](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:23) |

集計: **closed 7 / partial 3 / regressed 0**。

## 新規所見

### T425-ADV2-01 — v1 が既に insight に凍結されており、v2 の状態宣言と矛盾する

重大度: **must-fix**

v2 は「v1 は insight に凍結せず、本 v2 のみを凍結写し」と宣言していますが、現行 insight には旧 `02-ruling-package.md` が存在し、README も「U-1〜U-6」「K=8推奨＋途中増補」を案内しています。[v2の宣言](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:3)、[insight README](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t425-floor-scoping/output/insights/2026-08-04_t425-floor-scoping/README.md:12)、[旧パッケージ](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t425-floor-scoping/output/insights/2026-08-04_t425-floor-scoping/02-ruling-package.md:42)。

放置すると、裁定者や後続台帳が、v2で撤回した optional stopping と K=8推薦を正本候補として参照します。

## 総括

**NO-GO**

最小修正は次の4点です。

1. ADV-01: θを現行consumerと同じ「1 session-medianの周辺CV」に戻してcluster推定するか、compare側も必ずmedian-of-5を消費する契約として原子的に束縛する。
2. ADV-04: rr5/Linuxの「尤もらしさ」をH1/H2のK推薦から除き、1.5%・2.0%をユーザーが選ぶ設計感度と目標検出力として明示する。
3. ADV-08: 5%を「i.i.d.正規SDモデル内のnominal値」と限定する。実被覆を保証するなら、別途較正済み手続きを規定する。
4. T425-ADV2-01: insightの旧パッケージとREADMEをv2へ同期し、旧K=8・増補記述を残さない。