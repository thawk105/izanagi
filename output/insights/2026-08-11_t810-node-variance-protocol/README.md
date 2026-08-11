# [T-810] ノード間性能差 測定 protocol の設計 — wave 逐語 (2026-08-11)

`docs/pegasus-node-variance-protocol.md` を作った dev-wave の逐語控えである。
**設計のみで実走はしていない。**確定した設計の正本は同 docs であり、本 directory は経緯の記録である。

## ファイル

| ファイル | 中身 |
|---|---|
| `brief.md` | 段 1 親 brief。provisional 裁定 (P1)〜(P7) を含む |
| `facts.md` | 段 1〜6 で親が実物から採った実測 F-1〜F-10 (訂正 1 件を含む) |
| `s2-plan.md` | 段 2 起草 (codex `plan`、reasoning=max) |
| `s3-lensA.md` | 段 3 敵対相談 A — 統計的妥当性と識別可能性。NO-GO、blocker 6 |
| `s3-lensB-r3.md` | 段 3 敵対相談 B — 実行可能性と非流入。NO-GO、blocker 8 (3 回目で成功) |
| `s4-adjudication.md` | 段 4 親裁定。real/refuted、採否、scope、プラン v2、ユーザー裁定 Q1〜Q5 |
| `s6-revA.md` | 段 6 敵対レビュー A — 事前固定性。NO-GO、blocker 8 |
| `s6-revB.md` | 段 6 敵対レビュー B — 事実誤りと非流入の穴。NO-GO、blocker 7 |
| `s6-focus.md` | 段 6 焦点再レビュー (1 巡目)。NO-GO、残 blocker 6 (うち 4 件は親の修正が入れた回帰) |
| `s6-focus2.md` | 段 6 最終確認 (2 巡目)。NO-GO、残 blocker 1 + must-fix 3。**すべて修正済み** |

数値計算に使った script は repo 外に置いた
(`/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/` の `verify-s3.py`, `design-nr*.py`)。
**repo へ入れると実装面になり Codex author が要るため、意図的に外に置いている。**
再現に要る条件は docs の protocol 本文に literal で書いてある。

## 親が誤り、子が正した点 (3 件)

1. **段 4 前:** 親 brief (P1) は「T-139 は同一 cluster 内で測るのでノード効果は contrast で相殺する」
   と書いたが、**分母条件には共通加法効果が残る。**段 2 の起草がこれを反証し、親が代数で確認した。
2. **段 6 1 巡目:** 親は「ドリフトは主推定量の分母に入らないので結論の向きを歪めない」と書いたが、
   **推定量は `MS_A − MS_E` の差なので、共通ドリフトはノード差を過小評価させる。**
   推定対象と推定量を混同していた。
3. **段 6 1 巡目:** 親は「成分ごとの上限を掛け合わせる保守的構成」で `τ_U` を定義しながら、
   assurance は κ 単独の F 反転で計算していた。**主区間で測ると 0.80 でなく約 0.62** だった
   (レビュー B が Monte Carlo で実測)。対数尺度の単一式へ変えて整合させた。

## 親が子の所見を退けた点 (2 件)

1. **段 3 レンズ A の「単一 arm は T-139 pilot を支えない」は強すぎる。**共通乗数モデルの下では
   cluster 間分散のうちノード起因の成分に上限を与えられる。識別できないのは loading の形
   (加法か乗法か) であって、上限の計算ではない。目的の削除でなく scope 限定を採った。
2. **段 3 レンズ A の「`CV/√10` は独立性未確認なので SE でない」は機序が違う。**親が計算した
   lag-1 系列相関は両 record ともほぼ 0 (−0.11 / −0.01) で、自己相関は支持されない。
   実在するのは傾き (drift) である。結論 (1.774% を閾値の逆算に使わない) だけ採り、理由を差し替えた。

## 未実施

実走、qsub、build、benchmark。本 wave は設計のみである。
