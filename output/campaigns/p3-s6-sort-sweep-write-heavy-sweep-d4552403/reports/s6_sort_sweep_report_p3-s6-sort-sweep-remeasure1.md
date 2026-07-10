# s6 sort sweep 偵察レポート — workload=write-heavy trial=p3-s6-sort-sweep-remeasure1

**位置づけ:** 偵察 (preliminary、事前登録外カテゴリ)。断定 verdict なし。
**限定 (必読):** (1) 失敗条件 (c) の判定は出さない (16対1 の非対称比較・空間は coder iter1 後の設計で grid pre-commitment 未充足・random-variation アーム欠落)。(2) floor 0.030 は stock silo 実測の暫定流用の参考線 — high-abort 点 (退化点 + abort 率 stock 比 2.0 倍超) は floor 未較正 = 判定不能。(3) 本 sweep は fairness 偏向 (D41 型15) を検出しない。(4) write-heavy の S2 verify は rr50 固定 (off-workload 被覆)。(5) 段 6 の正式 grid / (c) 判定は本結果を材料流用しない (firewall)。

| 点 | 分類 | median tps | CV% | abort率 | unstable | certified | 備考 |
|---|---|---:|---:|---:|---|---|---|
| sk_ad | full-order | 1,098,674 | 1.66 | 14.58 |  | ✓ |  |
| sk_aa | full-order | 1,074,352 | 0.90 | 15.90 |  | ✓ | coder iter1 同値順序 |
| stock | stock | 1,055,167 | 1.09 | 16.22 |  | ✓ | 対照 (operator<) |

**valid 全順序点 (stable, n=2):** max=sk_ad 1,098,674 tps / min=sk_aa 1,074,352 tps / レンジ +2.26% (選択バイアス無補正の記述統計 — floor との断定比較は cross-run 再測点のみ)
**best vs stock:** sk_ad +4.12% (参考線: 暫定 floor ±3.0%。未再測 = 位置関係は暫定、断定は cross-run 再測後)
**coder 到達点の位置 (記述のみ):** sk_aa (coder iter1 と同値順序) は valid 全順序 2 点中 2 位。coder は iteration 1 (n=1) 中間時点の提案であり最終到達ではない。coder 実測値 (配線規模 t4/100k) とは規模が異なるため直接比較しない (代理 = 本 sweep の sk_aa 点)。
