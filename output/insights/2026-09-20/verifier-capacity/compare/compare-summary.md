# compare 要約 (旧 = base 947fd160a の verifier、新 = 統合後。同一 node・同一復元 trace、旧 → 新の順に別 process)

| label | host | txns / edges (新) | 旧 verdict / anom / workers | 新 verdict / anom / workers | 旧 wall (parse/producer/edge-w/replay/scc) | 新 wall | 旧 node peak / 親 RSS / worker Pdirty GiB | 新 同 | oom 旧/新 | identical rtd / full | stop / rc |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bal10 | bnode025 | 14748197 / 215144539 | serializable / 0 / 8 | serializable / 0 / 16 | 725 (90/174/173/195/76) | 478 (56/161/28/148/77) | 78.7 / 46.2 / 8.31 | 32.4 / 32.4 / 1.39 | 0/0 | True / True | completed / 0 |
| bal6 | bnode080 | 8855503 / 127987677 | serializable / 0 / 16 | serializable / 0 / 16 | 364 (33/102/63/110/45) | 275 (33/95/16/82/45) | 80.2 / 27.6 / 4.9 | 19.5 / 19.5 / 0.85 | 0/0 | True / True | completed / 0 |
| f10-bal3 | bnode083 | 4286776 / 60451583 | serializable / 0 / 16 | serializable / 0 / 16 | 159 (16/49/23/47/20) | 129 (16/46/7/37/20) | 40.3 / 13.5 / 2.68 | 9.5 / 9.5 / 0.32 | 0/0 | True / True | completed / 0 |
| f10-bal6 | bnode082 | 8604257 / 124263686 | serializable / 0 / 16 | serializable / 0 / 16 | 355 (32/99/61/108/44) | 269 (32/92/16/80/44) | 77.8 / 27.0 / 4.72 | 18.8 / 18.8 / 0.76 | 0/0 | True / True | completed / 0 |
| f10-rh3 | bnode035 | 15437721 / 265238797 | serializable / 0 / 16 | serializable / 0 / 16 | 404 (63/27/52/136/116) | 400 (62/53/31/131/115) | 39.6 / 39.6 / 1.87 | 37.3 / 37.3 / 1.45 | 0/0 | True / True | completed / 0 |
| f10-rh6 | bnode019 | 30656095 / 554509023 | serializable / 0 / 16 | serializable / 0 / 16 | 877 (126/54/116/307/254) | 838 (125/98/65/282/250) | 80.0 / 79.9 / 3.52 | 76.2 / 76.1 / 2.76 | 0/0 | True / True | completed / 0 |
| f10-wh3 | bnode023 | 2532560 / 25100961 | serializable / 0 / 16 | serializable / 0 / 16 | 119 (8/50/19/29/9) | 84 (8/42/4/20/9) | 40.0 / 9.5 / 2.78 | 4.7 / 4.8 / 0.21 | 0/0 | True / True | completed / 0 |
| f10-wh6 | bnode011 | 5018742 / 50804713 | serializable / 0 / 16 | serializable / 0 / 16 | 256 (16/106/40/67/19) | 176 (16/86/8/44/19) | 73.9 / 18.8 / 4.63 | 9.3 / 9.3 / 0.51 | 0/0 | True / True | completed / 0 |
| f5-bal3 | bnode042 | 4450058 / 62868744 | serializable / 0 / 16 | serializable / 0 / 16 | 167 (16/51/25/48/21) | 134 (16/48/8/39/21) | 42.3 / 13.9 / 2.72 | 9.8 / 9.8 / 0.43 | 0/0 | True / True | completed / 0 |
| f5-rh3 | bnode024 | 16819316 / 291168798 | serializable / 0 / 16 | serializable / 0 / 16 | 432 (68/31/57/142/125) | 433 (68/58/33/140/126) | 43.2 / 43.1 / 2.04 | 40.8 / 40.8 / 1.56 | 0/0 | True / True | completed / 0 |
| f5-wh6 | bnode021 | 5017504 / 50792622 | serializable / 0 / 16 | serializable / 0 / 16 | 256 (17/107/37/66/20) | 174 (17/85/8/43/19) | 73.9 / 18.8 / 4.63 | 9.3 / 9.3 / 0.46 | 0/0 | True / True | completed / 0 |
| rh6 | bnode083 | 32754846 / 594786279 | serializable / 0 / 16 | serializable / 0 / 16 | 933 (134/57/121/324/275) | 896 (135/106/70/294/273) | 85.7 / 85.6 / 3.66 | 81.2 / 81.0 / 2.95 | 0/0 | True / True | completed / 0 |
| wh10 | bnode044 | 8323838 / 84993314 | serializable / 0 / 8 | serializable / 0 / 16 | 493 (46/176/108/119/33) | 297 (28/145/13/74/33) | 72.4 / 29.0 / 7.71 | 15.2 / 15.2 / 0.89 | 0/0 | True / True | completed / 0 |
| wh3 | bnode016 | 2530609 / 25081301 | serializable / 0 / 16 | serializable / 0 / 16 | 118 (8/55/15/27/9) | 86 (8/42/4/21/9) | 39.7 / 9.7 / 2.53 | 4.9 / 4.9 / 0.25 | 0/0 | True / True | completed / 0 |
