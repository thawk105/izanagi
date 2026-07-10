# s6 sort sweep 偵察レポート — workload=balanced trial=p3-s6-sort-sweep

**位置づけ:** 偵察 (preliminary、事前登録外カテゴリ)。断定 verdict なし。
**限定 (必読):** (1) 失敗条件 (c) の判定は出さない (16対1 の非対称比較・空間は coder iter1 後の設計で grid pre-commitment 未充足・random-variation アーム欠落)。(2) floor 0.030 は stock silo 実測の暫定流用の参考線 — high-abort 点 (退化点 + abort 率 stock 比 2.0 倍超) は floor 未較正 = 判定不能。(3) 本 sweep は fairness 偏向 (D41 型15) を検出しない。(4) write-heavy の S2 verify は rr50 固定 (off-workload 被覆)。(5) 段 6 の正式 grid / (c) 判定は本結果を材料流用しない (firewall)。

| 点 | 分類 | median tps | CV% | abort率 | unstable | certified | 備考 |
|---|---|---:|---:|---:|---|---|---|
| s_asc | degenerate | 950,095 | 0.76 | 19.79 |  | ✓ | high-abort/未較正: floor 判定不能 |
| s_desc | degenerate | 941,580 | 2.15 | 19.86 |  | ✓ | high-abort/未較正: floor 判定不能 |
| sp_dd | full-order | 928,214 | 1.75 | 20.04 |  | ✓ |  |
| k_desc | full-order | 925,963 | 1.16 | 19.58 |  | ✓ |  |
| sp_ad | full-order | 925,294 | 0.96 | 19.86 |  | ✓ |  |
| sp_aa | full-order | 923,622 | 2.61 | 19.90 |  | ✓ |  |
| p_asc | full-order | 920,115 | 1.12 | 20.01 |  | ✓ |  |
| p_desc | full-order | 919,181 | 2.20 | 19.95 |  | ✓ |  |
| sk_da | full-order | 916,805 | 1.26 | 20.34 |  | ✓ |  |
| sk_dd | full-order | 915,754 | 1.51 | 19.46 |  | ✓ |  |
| nosort | degenerate | 915,734 | 2.12 | 19.10 |  | ✓ | high-abort/未較正: floor 判定不能 |
| stock | stock | 913,843 | 0.80 | 19.99 |  | ✓ | 対照 (operator<) |
| sp_da | full-order | 912,962 | 1.68 | 19.93 |  | ✓ |  |
| sk_aa | full-order | 910,253 | 1.19 | 20.40 |  | ✓ | coder iter1 同値順序 |
| k_asc | full-order | 907,817 | 1.53 | 19.83 |  | ✓ |  |
| sk_ad | full-order | 905,956 | 4.04 | 18.94 |  | ✓ |  |

**valid 全順序点 (stable, n=12):** max=sp_dd 928,214 tps / min=sk_ad 905,956 tps / レンジ +2.46% (選択バイアス無補正の記述統計 — floor との断定比較は cross-run 再測点のみ)
**best vs stock:** sp_dd +1.57% (参考線: 暫定 floor ±3.0%。未再測 = 位置関係は暫定、断定は cross-run 再測後)
**退化点 (別掲、レンジ集計外):** s_asc 950,095 tps, s_desc 941,580 tps, nosort 915,734 tps
**coder 到達点の位置 (記述のみ):** sk_aa (coder iter1 と同値順序) は valid 全順序 12 点中 10 位。coder は iteration 1 (n=1) 中間時点の提案であり最終到達ではない。coder 実測値 (配線規模 t4/100k) とは規模が異なるため直接比較しない (代理 = 本 sweep の sk_aa 点)。
