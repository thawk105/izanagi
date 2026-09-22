# [T-2847] 段 1 事実要約 (親、main 8fd2a2f5c 時点、worktree は同 commit)

出典: 親の直接照合 + Claude の読み取り子 (sonnet) 3 本の報告。行番号は worktree
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-verifier-detection-design` のもの。
子の報告は要約であり、引用前に file:line を読み直すこと。

## A. trace 形式 (現行 = v2 frame)

- emitter header `external/ccbench/include/trace.hh`: `C <txid> <thid> <epoch> <tid>` (5 field の `emit_commit`)、`R <txid> <key_hex> <ver_epoch> <ver_tid>` (読んだ版を記録、値は記録しない)、`W <txid> <key_hex> <op> <epoch> <tid>` (新版 = commit TID)、`X <txid> <key_hex> <reason>` (lock 被覆違反)。
- silo は独自に 7 field の C 行 (`cc/silo/transaction.cc:601-602` 付近) と `E <txid>` 終端 (`:698`)、`P <reason>` (`:432`)、X (`:628-630`, `:653`, `:674`) を出す。commit 済みの取引だけを出す (abort は出ない)。
- si は `cc/si/transaction.cc:539-552` で `emit_commit` (5 field = v1)、E 終端なし、epoch を 1 に固定、tid = cstamp。
- parser `orchestrator/verifier/parse.py:321-330`: C 行が 5 field なら `trace v1 C record is not supported; expected 7 fields including read/write counts` で ParseError。7 field 以外は malformed。→ 現行 si trace はどの workload でも parse で拒否される。
- 他の record: `I` (write intent 違反)、`A <reason>` (abort 要因の集計、verdict に不関与)。

## B. verdict と integrity

- `model.py:502-515` verdict: n_txns == 0 → indeterminate、巡回あり → non-serializable、巡回なしで integrity 不 clean → indeterminate、他 → serializable。
- `model.py:517-520` certified = n_txns > 0 ∧ serializable ∧ integrity.clean()。
- `model.py:450-467` clean(): orphan_reads / version_dups / dup_txids / genesis_commits / missing_txids / write_version_mismatch / malformed_keys / framing_violations / lock_coverage_violations / write_intent_violations / permutation_violations がすべて 0、proof_surfaces.certification_gate_satisfied()、commit 証人一致。**commit 証人は expected / observed が両方 None でも clean**。
- `core.py:60-73`: expected_commits (trace 外の CCBench counter) と observed = n_txns を比較。pipeline だけが渡す (`orchestrator/campaign/pipeline.py:616` 付近)。`pipeline.py:434-437` は `ycsb_` 以外の binary を `_TraceWitnessUnsupportedWorkload` で拒否 (commit 後に counter を無条件加算すると確認済みなのが YCSB だけ)。
- txid は密連番 (commit 直前に採番)。欠番 → missing_txids → indeterminate。**末尾の欠落は欠番にならず、commit 証人だけが検出する。**
- proof surface: `model.py:37` `_PROOF_SURFACE_PROTOCOLS = {"silo","si","mocc"}`。X/P emitter が source にある protocol だけ certification gate を満たす (論文稿 2026-09-21c: 素の pin の mocc の巡回なし走は indeterminate、si は証明面なし)。

## C. グラフ

- 辺 ww / wr / rw。版順は key ごとの (epoch, tid) 辞書順 (packed `((epoch<<32)|tid)-2**63`、`dsg.py:35-47`)。rw は読んだ版の直後の実版の書き手へ。
- genesis = (1,0) (`model.py:26`)。genesis 判定は producer の有無 (`dsg.py:652-660`)。commit が (1,0) 以下 → genesis_commits (`dsg.py:347-355`)。
- 同一 (key, 版) を別 txid が書く → version_dups。
- 同一 txn 内の多重書き: 版は commit 1 個に畳み込む (`dsg.py:362-367` の `sorted(set(vs))`)。自己辺は作らない。read twice も集合で 1 本。op (U/I/D) はグラフで不使用。
- 分類 `dsg.py:805-824`: rw を含む → G2、wr を含み rw なし → G1c、ww のみ → G0。G0/G1c は「版 = commit スタンプで wr / ww が commit 順前向き」の前提下では出ない (docs/isolation-phenomena.md、fixtures/README.md:44-63)。G1a / G1b は不可視 (abort と中間版が trace に出ない)。
- 報告: `DSG.anomalies` (`dsg.py:826-849`) は SCC を size 昇順に並べ各 SCC の最短巡回を最大 max_report (既定 20、`core.py:29`) 件、total_cycles は全 SCC 数。
- phantom / 述語読み: R 行が出ないので不可視 (fixture `p1_phantom_skew` は certified を固定、D799 と README が限界として明記)。

## D. 既存 fixture (22 件、全部 v2)

- 緑: g1_serial, g2_rmw_chain, g3_readonly, g4_rw_no_cycle, g5_silo_real_prefix (実 Silo、期待値は verifier 自身の出力), g6_silo_serial_1thread (実 Silo 1 thread、serializable が独立に真), g7_mocc_minimal_2thread (patch 付き mocc source でだけ certified), p1_phantom_skew (限界の固定)。
- 赤 (全部 G2): r1_write_skew, r2_lost_update, r3_cycle3, r4_mixed_cycle, r5_nonlatest_transitive, r6_epoch_version_order, r7_epoch_rw_successor, r8_silo_broken_norw (実 broken Silo、G2 ≥ 1 は verifier を使わない raw 監査で独立に確認), r9_dense_cycle4 (長さ 4)。
- indeterminate: integrity_orphan, m1_commit_at_genesis, m2_version_dup, m3_mocc_lock_coverage, m4_mocc_permutation。
- `test_verifier.py:2893` `test_capacity_all_fixture_results_match_frozen_baseline` が 22 件の result sha256 を凍結し、**trace を持つ fixture dir の集合がこの 22 件と一致することも assert** する (fixture を足すと凍結一覧の更新が要る)。
- 欠け: (c) abort 入りの履歴 (形式が commit 済みしか記録しない)、(d) 欠損 trace の fixture dir (inline `_tmp_trace` の 4〜6 test だけ)、(f) 同一 txn 内の二重書き・二重読み (g5 の実データに偶発的にあるだけ)、G0 / G1c の trace fixture (合成 CycleEdge の単体 test だけ)。property-based / 乱数生成の履歴 test は無い。
- D799: 期待結果は「判定が verifier の外で決まる」ものだけが独立根拠。repo 内の第二 checker はユーザー見送り確定。g6 / r8 の対が殺すのは 2 つの定数 verdict 実装だけで、「分類器が常に G2」「版比較が epoch を無視」「長さ 4 以上の巡回を無視」「framing violation を常に 0」「fixture hash で結果を返す」は通す、と明記。

## E. YCSB (CCBench)

- `external/ccbench/include/ycsb.hh:55-80`: 1 取引 `ycsb_max_ope` 個 (既定 10) の操作、key は zipf で重複あり (同一 key 複数操作が自然に起きる)、`ycsb_rratio` で読み比、`ycsb_rmw` 既定 false (blind write)、KEY_SORT で並べ替え。
- 読みは read、書きは update (blind) か read→update (rmw)。

## F. 容量 (既存実測、`output/insights/2026-09-20/verifier-capacity/README.md`、改修版 D2181)

- balanced 10 s: 14.75M txn / 215M edge、478 s、node peak 32.4 GiB。write-heavy 10 s: 8.32M txn / 85M edge、297 s、15.2 GiB。read-heavy 6 s: 32.75M txn / 595M edge、896 s、81.2 GiB。read-heavy 10 s は入力 trace が存在せず未測、隣接構造 (`set`/tuple) を変えない限り 115 GiB 超の見込み (1.2B edge)。
- [T-2351] (P3・設計メモあり): replay / SCC の隣接を bucket 化 set 再生 + CSR、`U ≤ 2N` の txid 直接 index Tarjan などで縮める候補。
- verifier-capacity の実測表の trace は全部 serializable (anomaly 0)。異常が多い trace (si の 3,576 巡回級) での SCC・最短巡回探索の費用は同表に無い (他の記録の有無は未確認)。
