---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-t2710-t080-series-inquiry
seq: 3
---

## 新規

### {{F:probe-identifier-rewrite-breaks-ledger-lookup}}. 仮想割付 probe で nodeid を書き換え、台帳 lookup が既定値に落ちた偽の均等化を敵対相談の材料に載せた [計測汚染] [手順漏れ]

- 事象: T-2710 の親 probe が「成分粒度を node にした場合」を `tools/acceptance_shards.py::allocate()` で仮想計算する際、
  `test_s8b_oracle_driver.py` の group 無し node の **nodeid 自体**を仮想 file 名へ書き換えた。allocate は nodeid で
  `acceptance_duration_ledger.json` を引き、未登録 node を 1 秒に置くため、147 node 中 141 node が 1 秒になり
  「M を含んでも 3 shard が 5,165 秒で均等化」という偽の結果が出た。親はそれを段 3 レンズ B の prompt に「T-2750 が land すれば
  別系列化なしでも床が同程度まで下がるか」の材料として載せた。レンズ B が `allocate` の lookup (`AS:397,404`) を読んで検出し、
  nodeid を保った再計算で 6,052.7×3 (M は 0/6/5、240 秒 node が残る) に訂正した。near miss (裁定前に訂正)。
- 根本原因: (1) 仮想計算で「成分の鍵」(file) と「重みの鍵」(nodeid) を同じ文字列で扱い、片方だけ変えるべきところを両方変えた。
  (2) probe の出力に台帳 hit 数・fallback 数を含めず、全 node 1 秒という異常が数値 (負荷総和が 18,158 → 15,495 秒へ減る) からしか
  見えなかった。(3) 現行割付の再現 (保存済み loads と一致) は確かめたが、仮想変更後の「重みの総和が不変」という保存則を確かめなかった。
- 恒久対応: memory `virtual-allocation-probe-keeps-identifiers-and-checks-weight-conservation` — 仮想割付 probe は識別子 (nodeid) を
  保ち、変えるのは成分の鍵だけにする。出力に台帳 hit / fallback 数と重み総和を含め、母集合が同じ仮想変更では総和不変を assert する。
  修正済み probe の出力は `output/insights/2026-09-17/t2710-t080-series-inquiry/probe-outputs/probe_shard_wall.895f300a.v2.txt`。
- 再発検知: 段 3 レンズが親 probe の source を読む (本件で機能した)。probe 側は重み総和の保存則 assert。
