# 段 6 fix2 裁定 (2026-09-29 16:4x JST、wave HEAD 06071df01 = fix1 統合)

- 対象: F6 だけ (s6-fix1-ruling.md)。fix1 後も `orchestrator/tests/test_vhash_cicada_vlife.py::test_readonly_figure_full_campaign_layout` が `ValueError: figure text overlaps` で赤 (焦点走 35531.nqsv、focus-2.log 185〜195 行)。
- 親の診断 (repo 外 script `/work/1/SFC/tanab/tmp/vhash-readonly-share-2026-09-29/diag_layout.py`、出力 `diag_layout.out`): 重なりは 1 種類で、tick label「100」と tick label「−20」の組が 12 回 (同じ図の中)。図の text 数は 190・190・91・47 (大きさ 2400×1500、2400×1500、2400×1500、2400×900)。どの図・パネルかは未特定。
- 推定 (攻撃してよい): x 軸が ro 指定率 0〜100 のパネルの右端目盛「100」と、隣のパネルの y 軸目盛「−20」(自動余白で負側に伸びた軸、または負値をとる差の軸) が近接している。
- fix の方針: 作図の配置 (パネル間隔、軸の範囲、目盛の位置) を直す。**layout 検査 (`_layout` の拒否条件) は緩めない**。負になりえない量 (率・件数・年齢) の軸は下限 0 に固定してよいが、負をとりうる量 (D-F の差) の軸を 0 で切ってはいけない。
- 変異の追加登録: なし (既存 test が赤→緑になることが検証)。
