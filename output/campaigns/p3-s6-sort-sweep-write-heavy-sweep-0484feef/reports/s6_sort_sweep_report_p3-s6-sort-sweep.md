# s6 sort sweep 偵察レポート — workload=write-heavy trial=p3-s6-sort-sweep

**位置づけ:** 偵察 (preliminary、事前登録外カテゴリ)。断定 verdict なし。
**限定 (必読):** (1) 失敗条件 (c) の判定は出さない (16対1 の非対称比較・空間は coder iter1 後の設計で grid pre-commitment 未充足・random-variation アーム欠落)。(2) floor 0.030 は stock silo 実測の暫定流用の参考線 — high-abort 点 (退化点 + abort 率 stock 比 2.0 倍超) は floor 未較正 = 判定不能。(3) 本 sweep は fairness 偏向 (D41 型15) を検出しない。(4) write-heavy の S2 verify は rr50 固定 (off-workload 被覆)。(5) 段 6 の正式 grid / (c) 判定は本結果を材料流用しない (firewall)。

| 点 | 分類 | median tps | CV% | abort率 | unstable | certified | 備考 |
|---|---|---:|---:|---:|---|---|---|
| s_asc | degenerate | 1,086,932 | 1.69 | 17.72 |  | ✓ | high-abort/未較正: floor 判定不能 |
| sk_ad | full-order | 1,082,402 | 1.17 | 14.42 |  | ✓ |  |
| sp_ad | full-order | 1,081,738 | 1.01 | 15.71 |  | ✓ |  |
| nosort | degenerate | 1,080,707 | 1.70 | 17.62 |  | ✓ | high-abort/未較正: floor 判定不能 |
| sk_dd | full-order | 1,079,988 | 0.92 | 14.55 |  | ✓ |  |
| p_desc | full-order | 1,079,628 | 1.16 | 15.89 |  | ✓ |  |
| k_desc | full-order | 1,074,204 | 0.48 | 13.95 |  | ✓ |  |
| sp_da | full-order | 1,074,189 | 2.93 | 16.88 |  | ✓ |  |
| k_asc | full-order | 1,071,383 | 1.37 | 14.99 |  | ✓ |  |
| s_desc | degenerate | 1,070,902 | 1.52 | 17.38 |  | ✓ | high-abort/未較正: floor 判定不能 |
| sp_dd | full-order | 1,070,401 | 1.86 | 14.81 |  | ✓ |  |
| p_asc | full-order | 1,067,748 | 0.88 | 16.62 |  | ✓ |  |
| sp_aa | full-order | 1,060,847 | 1.70 | 16.94 |  | ✓ |  |
| sk_aa | full-order | 1,060,696 | 2.16 | 15.90 |  | ✓ | coder iter1 同値順序 |
| sk_da | full-order | 1,053,691 | 1.08 | 15.16 |  | ✓ |  |
| stock | stock | 1,045,252 | 0.83 | 15.18 |  | ✓ | 対照 (operator<) |

**valid 全順序点 (stable, n=12):** max=sk_ad 1,082,402 tps / min=sk_da 1,053,691 tps / レンジ +2.72% (選択バイアス無補正の記述統計 — floor との断定比較は cross-run 再測点のみ)
**best vs stock:** sk_ad +3.55% (参考線: 暫定 floor ±3.0%。未再測 = 位置関係は暫定、断定は cross-run 再測後)
**退化点 (別掲、レンジ集計外):** s_asc 1,086,932 tps, s_desc 1,070,902 tps, nosort 1,080,707 tps
**coder 到達点の位置 (記述のみ):** sk_aa (coder iter1 と同値順序) は valid 全順序 12 点中 11 位。coder は iteration 1 (n=1) 中間時点の提案であり最終到達ではない。coder 実測値 (配線規模 t4/100k) とは規模が異なるため直接比較しない (代理 = 本 sweep の sk_aa 点)。
