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

## 再発

### F945

- **再発: 2026-09-17** — [T-2710] 調査 wave (docs と計測成果物のみ、post-claim merge 後の tip `06ad393af`) の受入 attempt 1
  (session `93bc7244…`、同時受入は投入時 2 本・他 session 合計 3 本) で 4 setup error (24,755 passed / 67 skipped)。全件
  `test_s8c_preregistration_predicates.py::test_current_repository_*` の module fixture の `archive` 呼び出し (orchestrator/campaign
  約 80 file) が 10 秒 TimeoutExpired。本 wave の差分は到達不能。同 tip・同 file の単独再走 (`run_tests.py --force-dispatch`、
  request 4213.nqsv) は 218 passed / 92.29 秒 / rc=0 で非再現。attempt 2 (tip `b82d12ac7`、session `c8faa7f0…`、投入時 leader 2 本) は
  33 error (t1259 の worktree に対する 30 秒 TimeoutExpired 29 件 + s8c の 10 秒 timeout 4 件、24,726 passed)、同 tip の 2 file 単独再走
  (request 4300.nqsv) は 269 passed / 99.10 秒 / rc=0 で非再現。恒久対応は既報のまま変えず、timeout 拡大・stub 化・除外・gate 新設は
  していない。attempt 3 は投入条件を leader ≤ 1・load1 < 15 に絞って投げた。
