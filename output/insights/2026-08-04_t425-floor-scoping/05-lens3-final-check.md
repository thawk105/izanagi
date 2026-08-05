| 所見 | 判定 | 根拠 |
|---|---|---|
| ADV-01 | `closed` | estimand を consumer と同じ 1 session-median 周辺 CV に揃え、K 窓 × M sessions の分散成分へ接続した。[v3 §2.1](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:38) |
| ADV-04 | `closed` | 検出力表の行をユーザー選択の設計感度と明記し、scoping/linux 値を K 推薦の根拠から明示的に除外した。[v3 §2.3](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:89) |
| ADV-08 | `partial` | nominal 限定、bootstrap＝診断、実被覆には別較正という区別は閉じた。ただし新しい random-effects estimand と χ² 表の対応が未成立。下記重大所見に該当する。[v3 §2.2](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:69) |
| T425-ADV2-01 | `closed` | insight の 02 は正本 v3 と byte-identical（SHA-256 `ea649d…b2f96`）。03/04 は保存され、README も v3・U-1〜U-7・K=15固定へ整合した。[README](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t425-floor-scoping/output/insights/2026-08-04_t425-floor-scoping/README.md:8) |

## 新規重大所見

### T425-ADV3-01 — random-effects 推定量と χ² 検出力表が不整合

重大度: **must-fix**

v3 は `θ̂ = √(σ̂²_b + σ̂²_w) / μ̂` という二成分の一元配置 random-effects 推定量を定義する一方、UCL と検出力表は単一分散が `χ²_{K−1}` に従うものとして K だけから算出し、「χ²厳密計算」としている。[§2.1](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:45)、[§2.2–2.3](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:55)

random-effects 推定量の分布は窓間・窓内成分の比と M にも依存するため、df=K−1を保守的に選ぶだけでは提示した nominal 5% と検出力値が当該推定量に対応するとはいえない。放置すると、U-1 の K=15推薦と U-5 の compare 適格化が、裏付けのない検出力値により変わりうる。

## 総括

**NO-GO**

ADV-08に直結する推定量と検出力計算の重大な内部不整合が1件残る。