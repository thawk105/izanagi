# 段 5 (i) probe 結果 (親が login pegasus02 で実行、2026-09-19 22:12:43〜22:13:43 JST、rc=0)

- probe: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-6/t2153_witness_candidates_probe.py` (sha256 `09ed5c865864d564…`、Codex author の巡 1 が書き親が job dir へ退避)。selftest PASS (正例・負例 2・固有 import・正準不変)。
- 入力: `probe-sidecar.json` (repo_root = wave worktree at 657e1e5a7、g++-11、cmake 3.22、official 同形 4 引数 = `-DFETCHCONTENT_BASE_DIR=<scratch>` + `-DFETCHCONTENT_SOURCE_DIR_{MASSTREE,MIMALLOC,GOOGLETEST}=<cache>`、env `CMAKE_PREFIX_PATH=<gflags-install>:<glog-install>`)。原本 gate sha256 `19173d8ad57ad25c…`、shadow `e0d222cdf52b70c2…`。
- 出力: `probe-out/cells.json` (977,781 bytes、canonical JSON、全 record)。

| cell | supply | meaning | admitted / 未確立 | 観測 (要求 / 既定) |
|---|---|---|---|---|
| sort-base (正準) | green `requested-default-preprocess-different` | unestablished `meaning-witness-undeclared` | True / [SORT_VARIANT] | — |
| **sort-shadow** | green 同上 | **green `declared-compile-time-branch-selection-observed`** | True / [] | (1,1) / (0,1) |
| rung1-report-base (正準) | green 同上 (別 root: requested / default) | unestablished | True / [IZANAGI_SILO_LADDER_RUNG1_REPORT] | — |
| **rung1-report-shadow** | green 同上 (共有 root: requested / requested)。前処理 digest `a14dc4657a72` / `2775e7dc9e93`、bytes 4,479,871 / 4,479,486 は base と**完全一致** | **green** | True / [] | (1,1) / (0,1) |
| ss2pl-lock-impl-shadow | red `dependency-closure-drift` | green (1,1)/(0,1) | False / [] | 観測可能だが採用しない (ruling P3) |
| ss2pl-wfg-diag-shadow | red `dependency-closure-drift` | green (1,1)/(0,1) | False / [] | 同上 |
| ss2pl-dlr-shadow | red `compile-command-drift` | **red `compile-command-drift`** ("requested/default owner compile commands differ beyond the tested define") | False / [] | 既存機構では届かない (ruling P4、予測どおり) |

## 確定集合 (ruling.md plan v2 の条件 (a)(b) を満たす)
- `SORT_VARIANT` → `("cc/silo/transaction.cc", "#if SORT_VARIANT")`
- `IZANAGI_SILO_LADDER_RUNG1_REPORT` → `("cc/silo/ycsb_silo.cc", "#if IZANAGI_SILO_LADDER_RUNG1 && IZANAGI_SILO_LADDER_RUNG1_REPORT")`

SS2PL 3 件は足さない (LOCK_IMPL / WFG_DIAG = 観測可能だが代表選択は scope 外 + supply 拒否、DLR = meaning arm も argv drift、LOCK_KIND = 所有 TU に directive なしで宣言不能)。
