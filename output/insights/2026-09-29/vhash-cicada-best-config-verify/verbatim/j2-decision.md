# J2 (1M・t48) の投入判断 — 裁定 R4 (2026-09-29 23:1x JST、J2 の結果を見る前)

- 実測単価: 判定器の wall は BEST W3 tuple 200 t48 (trace 14,897,731 行、commit 1,374,444) で 21.4 s (runs/j1-w3 の verifier.wall_seconds)。job Elapse は L0 122 s・120 s、J1-W1 164 s、J1-W3 125 s (build 2〜4 本と run 4〜6 本を含む)。
- 予測: J2 の各 run の trace は、tracing 下の throughput が trace の書き出しで律速されるため 200 tuple t48 と同程度〜数倍 (≤ 5 倍と仮定して ≤ 7,500 万行)。判定器 wall は行数にほぼ比例と仮定して ≤ 約 110 s < 600 s。
- Elapse 積算: 実測 531 s + J1-W2・W4・POS の予測 各 ≤ 250 s (計 ≤ 750 s) + J2 予測 (build 3 本 ≤ 150 s + 8 run × (1 s + 判定器 ≤ 110 s + trace 集計) ≤ 1,200 s) ≈ 2,630 s < 6,000 s。切り分け予備 900 s を足しても 7,200 s 未満。
- 判断: J2 を投入する (cbv-m-l0、walltime 01:00:00)。extime は 1 で md_11 の 3 と違うので、J2 の結果を「md_11 の主比較条件で検査済み」とは書かない (R8)。
