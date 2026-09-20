# verifier の容量 — trace-enabled 10 s 走の未完走 2 型の原因同定と、producer / versions の packed 配列化 + 配列だけを読む edge worker による省メモリ化 (2026-09-20)

wave `dev-wave-verifier-capacity` (branch `worktree-dev-wave-verifier-capacity`、base local main `947fd160a`)。
job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verifier-capacity/` (brief `s1-brief.md`、裁定 `s4-ruling.md`、plan / consult / review の生出力 `codex/`、profile `run/profile/`、compare `run/compare/`、変異 `mutation/`)。
決定は {{D:verifier-packed-producer-array-workers}}。失敗型は {{F:broken-pool-hangs-when-sigterm-ignored}}。

## 1. 一行で

trace-enabled 10 s 走を現行 verifier が完走できなかった 2 型 (balanced 14.7M commit で SIGKILL、write-heavy 8.3M commit で 3600 s timeout) は、**どちらも fork した edge worker 16 本が親の Python object graph (producer dict の key tuple / value int、versions list の版 tuple) に refcount で触って copy-on-write で page を複製し node memory 128 GiB を使い切る OOM kill**であった (balanced は親が殺され rc −9、write-heavy は worker が殺され pool 破綻 → 残 15 worker が SIGTERM 無視環境で shutdown 待ちのまま停滞)。producer / versions を鍵単位の packed 配列 (`(epoch<<32)|tid` の `array("q")` + producer txid 配列 + file ごとの token→key_id 配列) にし、edge worker が配列だけを読むようにした改修で、**balanced 10 s は 478 s / node peak 32.4 GiB、write-heavy 10 s は 297 s / 15.2 GiB で完走し、判定 (`result_to_dict` の bytes と `VerifyResult` 全 field) は旧 verifier と同一**。fixture 全件 (22) と完走済み校正 trace でも同一。read-heavy 10 s は入力 (保全 trace) が存在せず対象外。

## 2. 未完走 2 型の原因 (段 1 実測、現行 verifier `947fd160a`、Pegasus gen_S、probe `probe/verifier_profile_probe.py` v1 sha `bc86ca22…`)

probe は保全 trace (`zstd`、sha256 照合) を `/scr` へ復元し、verifier を子 process で走らせて phase marker (parse / producer / edges-workers / adjacency-replay / scc) を採り、親 process が 2 s ごとに process tree の `/proc/<pid>/smaps_rollup` (Pss / Private_Dirty)、`/proc/meminfo`、`/proc/vmstat` (`oom_kill` / `pswpout`) を記録する。

| run | node | txns / reads / writes | phase wall s (parse / producer / edge-workers / replay / scc) | 親 RSS peak | node used peak | worker Private_Dirty 最大 | 結末 |
|---|---|---|---|---|---|---|---|
| bal10 (fixed-5 balanced 10 s) | bnode029 | 14.75M / 73.1M / 73.4M | 55 / 173 / (fork +80 s で kill) | 20.7 GiB | 113.6 GiB | 6.1 GiB | **t≈308 s に OOM kill (`vmstat oom_kill` 0→1、全 process 消滅)**。前 wave の 303 s / rc −9 / 21.2 GiB と一致 |
| wh10 (fixed-5 write-heavy 10 s) | bnode018 | 8.32M / 4.1M / 78.4M | 28 / 175 / (fork +65 s で worker kill) | 17.5 GiB | 119.2 GiB | 7.2 GiB | **t≈270 s に worker 1 本が OOM kill (oom_kill=1)、残 15 worker は state S のまま 2400 s 以上、node 114 GiB 不変、親は `shutdown(wait=True)` から戻らず hard timeout 2700 s** (= 前 wave の 3600 s timeout・親 CPU 低の正体) |
| bal6 (完走参照) | bnode040 | 8.86M / 43.9M / 44.1M | 33 / 101 / 62 / 112 / 45 | 27.7 GiB | 80.4 GiB | 4.8 GiB | 完走 serializable。完走する 6 s でも edge-workers 段の node peak は 80 GiB |
| bal6gf (= bal6 + fork 前 `gc.freeze()`) | bnode026 | 同上 | 33 / 102 / 34 / 85 / 46 | 27.5 GiB | 78.9 GiB | 4.7 GiB | 完走。**freeze 単独は CoW をほぼ減らさない** → refcount 書込みが主因 |
| rh6 (read-heavy 6 s) | bnode042 | 32.75M / 308.3M / 16.4M | 135 / 57 / 122 / 322 / 277 | 85.6 GiB | 86.0 GiB | 3.7 GiB | 完走 (594.8M edge)。replay + scc が所要の 55%、親 RSS は `set`/tuple 隣接が支配 |
| wh3 (write-heavy 3 s) | bnode017 | 2.53M / 1.25M / 23.8M | 8 / 53 / 15 / 27 / 9 | 9.6 GiB | 39.9 GiB | 2.5 GiB | 完走 |
| bal10w8 / bal10w4 / wh10w8 (`--workers 8 / 4 / 8`) | bnode103 / 019 / 083 | — | 746 / 882 / 500 (total) | 46.4 / 46.0 / 29.1 GiB | 78.9 / 52.4 / 71.7 GiB | 8.3 / 8.9 / 7.7 GiB | 現行でも worker を減らせば完走するが、**worker 1 本の Private_Dirty はむしろ増える** (CoW は task 範囲でなく親の object graph に比例)。既定 16 は変えない (D1553) |

- 仮説 (P3) の判定: (a) 主 process の記憶量は producer / versions 構築で writes に比例 (bal10: 4.0 → 19.1 GiB、約 220 B/write)、replay で edges に比例 (bal6: 13.6 → 25.5 GiB、約 100 B/edge)。(b) fork した worker の Private_Dirty は fork 後 15 s で 3〜4 GiB、最大 6〜7 GiB (worker 自身の出力は数百 MB) で node MemAvailable の減少と一致。`gc.freeze()` 単独では減らないので refcount 書込みが主因。**対照比較で補強した同定であり、page 単位の帰属 (どの object の page か) までは測っていない。** (c) parse 段 (16 worker の Txn object) は node peak 18 GiB で支配項ではない。swap (24 GiB) は使われていない。
- 計算ノードの事実: job 配下の子 process は SIGTERM を無視する ([T-2778] 実測) ので、壊れた pool の worker は `Process.terminate()` では消えない。`/proc/vmstat` の `oom_kill` が読める。

## 3. 改修 (統合 commit `11f0f1972` 単位 1、`f29ef5ec1` 単位 2。Codex `role=author`、gpt-6-astra / medium)

- `orchestrator/verifier/dsg.py` `_build_compact`: 全 write の epoch / tid が 32 bit 非負なら `_build_compact_packed` — writer を持つ鍵だけに初出順 id、file ごとの `token_id → key_id` 配列 (`array("i")`、writer 無しは −1)、版を `((epoch << 32) | tid) − 2**63` で flat `array("q")` に、producer txid を並走 `array("q")` に、鍵ごとに版昇順・同版は出現順の安定整列で最初の writer を残す。診断 (genesis note、`version dup` note) は元の rank / write 順で再生。範囲外なら従来の tuple builder (`_build_compact_tuple`) をそのまま使う (partial な integrity を残さない)。
- `_edge_candidates_for_task`: packed 経路は配列と `bisect` (lo / hi 付き) だけで wr / rw / ww を生成し、親の dict / list / str / tuple object を読まない。run の順序 (source 初出順、宛先は add 呼出し順) は不変。`producer` / `versions` は既存消費者 (`_reasons`、`core.py` の `len(versions)`、test の `_EdgeWorkerState` 直接構築) が使う Mapping 操作だけを持つ薄い view。
- 単位 2: `parse.py` に `_kill_pool_workers` (SIGKILL)。edge / parse とも worker 例外時に残 worker を殺してから shutdown し、Future / executor / 部分結果の参照を解放してから全件を親で逐次再計算 (D1552 の fallback は不変)。
- test (`orchestrator/tests/test_verifier.py`、+8): fixture 22 件の旧版 `result_to_dict` sha256 一覧との一致 (workers 1 / 2)、packed の境界 (同版重複・genesis・範囲外の退避)、last-wins の辺集合、worker が配列だけを読む機構検査 (Mapping 操作を拒否する代役)、workers 1 / 2 / 16 / 既定の一致、pool 破綻の終端 (SIGTERM 無視 + worker `os._exit`、子 process + 120 s timeout、fix 前は timeout)、fallback 前の解放。既存期待値は不変。焦点走 (計算ノード) 302 passed。
- 採らなかった案 (裁定 D-5): CSR 隣接 / txid 直接 index の Tarjan / 「全辺が前向きなら非巡回」の前判定。未完走 2 件は edge-workers 段で死んでおり replay / SCC に到達していない。read-heavy 10 s (見込み 1.2B edge、現行形の replay で 100 GiB 超) を扱う将来 wave の候補として §7 に残す。`gc.freeze()` は不採用 (効果なし)。

## 4. 改修版の実測 (compare、同一 node・同一復元 trace で旧 `947fd160a` → 新を別 process で順に、probe v2 sha `17ad243e…` の `compare`)

| trace | node | txns / edges | 旧 (workers) wall s: total (parse / producer / edge-w / replay / scc) | 新 (16) wall s | 旧 node peak / 親 RSS / worker Pdirty 最大 GiB | 新 同 | verdict (旧 = 新) | `result_to_dict` / 全 field 同一 |
|---|---|---|---|---|---|---|---|---|
| fixed-5 write-heavy 10 s | bnode044 | 8,323,838 / 84,993,314 | (8) 493 (46 / 176 / 108 / 119 / 33) | 297 (28 / 145 / 13 / 74 / 33) | 72.4 / 29.0 / 7.71 | 15.2 / 15.2 / 0.89 | serializable / anomaly 0 = serializable / 0 | True / True |
| fixed-5 balanced 10 s | bnode025 | 14,748,197 / 215,144,539 | (8) 725 (90 / 174 / 173 / 195 / 76) | 478 (56 / 161 / 28 / 148 / 77) | 78.7 / 46.2 / 8.31 | 32.4 / 32.4 / 1.39 | serializable / anomaly 0 = serializable / 0 | True / True |
| fixed-5 write-heavy 3 s | bnode016 | 2,530,609 / 25,081,301 | (16) 118 (8 / 55 / 15 / 27 / 9) | 86 (8 / 42 / 4 / 21 / 9) | 39.7 / 9.7 / 2.53 | 4.9 / 4.9 / 0.25 | serializable / anomaly 0 = serializable / 0 | True / True |
| fixed-5 write-heavy 6 s | bnode021 | 5,017,504 / 50,792,622 | (16) 256 (17 / 107 / 37 / 66 / 20) | 174 (17 / 85 / 8 / 43 / 19) | 73.9 / 18.8 / 4.63 | 9.3 / 9.3 / 0.46 | serializable / anomaly 0 = serializable / 0 | True / True |
| fixed-5 balanced 3 s | bnode042 | 4,450,058 / 62,868,744 | (16) 167 (16 / 51 / 25 / 48 / 21) | 134 (16 / 48 / 8 / 39 / 21) | 42.3 / 13.9 / 2.72 | 9.8 / 9.8 / 0.43 | serializable / anomaly 0 = serializable / 0 | True / True |
| fixed-5 balanced 6 s | bnode080 | 8,855,503 / 127,987,677 | (16) 364 (33 / 102 / 63 / 110 / 45) | 275 (33 / 95 / 16 / 82 / 45) | 80.2 / 27.6 / 4.90 | 19.5 / 19.5 / 0.85 | serializable / anomaly 0 = serializable / 0 | True / True |
| fixed-5 read-heavy 3 s | bnode024 | 16,819,316 / 291,168,798 | (16) 432 (68 / 31 / 57 / 142 / 125) | 433 (68 / 58 / 33 / 140 / 126) | 43.2 / 43.1 / 2.04 | 40.8 / 40.8 / 1.56 | serializable / anomaly 0 = serializable / 0 | True / True |
| fixed-5 read-heavy 6 s | bnode083 | 32,754,846 / 594,786,279 | (16) 933 (134 / 57 / 121 / 324 / 275) | 896 (135 / 106 / 70 / 294 / 273) | 85.7 / 85.6 / 3.66 | 81.2 / 81.0 / 2.95 | serializable / anomaly 0 = serializable / 0 | True / True |
| fixed-10 write-heavy 3 s | bnode023 | 2,532,560 / 25,100,961 | (16) 119 (8 / 50 / 19 / 29 / 9) | 84 (8 / 42 / 4 / 20 / 9) | 40.0 / 9.5 / 2.78 | 4.7 / 4.8 / 0.21 | serializable / anomaly 0 = serializable / 0 | True / True |
| fixed-10 write-heavy 6 s | bnode011 | 5,018,742 / 50,804,713 | (16) 256 (16 / 106 / 40 / 67 / 19) | 176 (16 / 86 / 8 / 44 / 19) | 73.9 / 18.8 / 4.63 | 9.3 / 9.3 / 0.51 | serializable / anomaly 0 = serializable / 0 | True / True |
| fixed-10 balanced 3 s | bnode083 | 4,286,776 / 60,451,583 | (16) 159 (16 / 49 / 23 / 47 / 20) | 129 (16 / 46 / 7 / 37 / 20) | 40.3 / 13.5 / 2.68 | 9.5 / 9.5 / 0.32 | serializable / anomaly 0 = serializable / 0 | True / True |
| fixed-10 balanced 6 s | bnode082 | 8,604,257 / 124,263,686 | (16) 355 (32 / 99 / 61 / 108 / 44) | 269 (32 / 92 / 16 / 80 / 44) | 77.8 / 27.0 / 4.72 | 18.8 / 18.8 / 0.76 | serializable / anomaly 0 = serializable / 0 | True / True |
| fixed-10 read-heavy 3 s | bnode035 | 15,437,721 / 265,238,797 | (16) 404 (63 / 27 / 52 / 136 / 116) | 400 (62 / 53 / 31 / 131 / 115) | 39.6 / 39.6 / 1.87 | 37.3 / 37.3 / 1.45 | serializable / anomaly 0 = serializable / 0 | True / True |
| fixed-10 read-heavy 6 s | bnode019 | 30,656,095 / 554,509,023 | (16) 877 (126 / 54 / 116 / 307 / 254) | 838 (125 / 98 / 65 / 282 / 250) | 80.0 / 79.9 / 3.52 | 76.2 / 76.1 / 2.76 | serializable / anomaly 0 = serializable / 0 | True / True |

- 判定同一性: `result_to_dict` の canonical JSON (`trace_dir` を置換) の sha256 と、`dataclasses.asdict(VerifyResult)` (非 wire の `expected_commits` / `observed_commits` / `proof_surfaces` を含む) の sha256 の両方が旧新で一致。
- 完了条件 (裁定 D-1): bal10 / wh10 が ≤ 115 GiB・≤ 3600 s で完走し旧版 (8 worker) と同一 → **充足**。600 s の校正規則は目標にしていない (wh10 297 s、bal10 478 s は結果として 600 s 内だが、校正規則の再適用は裁定事項)。

## 5. 変異 matrix

変異 harness `tools/mutation_worktree.py` (固定 commit `f29ef5ec1` の使い捨て worktree、runner `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_verifier.py -q -rf`、計算ノード dispatch)。spec は `mutation/mutation-spec-final.json` (sha256 `ba1bd790a47e…`)、結果は `mutation/final-results.json`。probe 走 (全件 SURVIVED 期待、`mutation-spec-probe.json` / `probe-results.json`) で観測 node を採り、本走は完全集合を KILLED 期待で登録した (DW-M08)。baseline: PASSED ()。

| 変異 | 位置 (`orchestrator/verifier/dsg.py`) | 期待 | 結果 | 殺した node 数 / 代表 |
|---|---|---|---|---|
| M0-equivalent-counts-init | `counts = array("Q")` → `array("Q", [])` (等価、harness の SURVIVED 検出の正例) | SURVIVED | **SURVIVED** | 0 / — |
| M1-dup-version-keeps-last-writer | 同版重複で最後の writer を採る | KILLED | **KILLED** | 3 / test_capacity_all_fixture_results_match_frozen_baseline, test_capacity_packed_versions_preserve_bounds_duplicates_and_notes, test_version_dup_keeps_first_writer_note_and_edge |
| M2-rw-successor-bisect-left | rw の直後版を `bisect_left` (同版) にする | KILLED | **KILLED** | 28 / test_broken_silo_norw_fixture_contract, test_broken_silo_norw_structured_report_is_exact, test_capacity_all_fixture_results_match_frozen_baseline … |
| M3-wr-writer-without-exact-match | wr の producer を完全一致なしで採る | KILLED | **KILLED** | 13 / test_broken_silo_norw_fixture_contract, test_broken_silo_norw_structured_report_is_exact, test_capacity_all_fixture_results_match_frozen_baseline … |
| M4-out-of-range-guard-removed | 範囲外 (epoch/tid ≥ 2**32) の退避 guard を外す | KILLED | **KILLED** | 1 / test_capacity_packed_versions_preserve_bounds_duplicates_and_notes |
| M5-worker-uses-mapping-path | worker の配列経路を無効化し Mapping 経路へ落とす | KILLED | **KILLED** | 1 / test_capacity_edge_worker_reads_only_arrays |
| M6-broken-pool-no-kill | pool 破綻時の残 worker SIGKILL を外す | KILLED | **KILLED** | 1 / test_capacity_broken_pool_terminates_workers_and_falls_back |
| M7-partial-results-not-released | fallback 前の部分結果解放を外す | KILLED | **KILLED** | 1 / test_capacity_partial_outcomes_are_released_before_full_fallback |
| M8-ww-drops-last-pair | ww の最後の隣接対を落とす | KILLED | **KILLED** | 8 / test_capacity_all_fixture_results_match_frozen_baseline, test_capacity_edge_worker_reads_only_arrays, test_capacity_packed_versions_preserve_bounds_duplicates_and_notes … |

- 単一理由の kill: M4 / M5 / M6 / M7 は本 wave の新 test 1 本だけが殺す (`test_capacity_packed_versions_preserve_bounds_duplicates_and_notes` / `test_capacity_edge_worker_reads_only_arrays` / `test_capacity_broken_pool_terminates_workers_and_falls_back` / `test_capacity_partial_outcomes_are_released_before_full_fallback`)。M1 / M2 / M3 / M8 は既存 test (fixture の exact pin、g2 / r7 等) と新 test (凍結一覧) の両方が殺す = 冗長 gate (DW-M03、新規検出力には数えない)。
- wrapper (`mutation_worktree.py`) の事後検査は本走で `共有木の観測 bytes が変化した` (rc=125) で不成立。走行中に別 session の land が 3 件あり (15:16 / 15:36 / 15:44、`.codex/worktrees/` の増減)、親は wave worktree へ書いていない (`git status` clean)。変異結果は固定 commit の使い捨て worktree で取れており影響しない (mutation-discipline の既知の型)。probe 走の wrapper は rc=1 (MISMATCH 期待どおり) で事後検査は通過。
- hang_risk の変異は登録していない (M6 は test 側の 120 s timeout で赤化するため dispatch で孤児にならない)。

## 6. 限定・言わないこと

- 本 wave が示すのは、保全済み fixed-5 trace (balanced 10 s / write-heavy 10 s) と完走済み 6 s / 3 s trace について、改修 verifier が node memory 内で完走し判定が旧版と同一であることまで。**B-8 (種を変えた長時間実行による最終候補の検証) の取得ではない** — 対象 (最終候補)・種 (seed 記録)・長さ (校正規則 ≤ 600 s) は別の裁定事項。
- read-heavy 10 s の trace は存在しない (前 wave で `not_run`)。read-heavy 6 s の親 RSS (replay 後 ≈ 80 GiB) は改修でも `set`/tuple 隣接 (595M edge) が支配し、10 s (1.2B edge 見込み) は隣接構造を変えない限り 115 GiB を超える見込み。
- CoW の同定は対照比較 (freeze A/B、worker 数) と Private_Dirty の時系列によるもので、page 単位の帰属は測っていない。
- `orchestrator/verifier/dsg.py` / `parse.py` の bytes が変わるので、enforcement source closure (`campaign_lock.py`) の digest が変わり既存 campaign lock は `contract-loader-drift` で再開不能 (D1552 と同じ帰結)。T126 code identity の旧記録は歴史記録として不変。
- 見積り probe の値 (dict → packed: bal6 8.96 → 1.96 GB / 105 → 70 s) は同 process 内の構築だけの値で、統合版の producer 段 wall (bal6 95 s、bal10 161 s、wh10 145 s) はそれより長い (token→key 解決の走査と診断再生を含む)。

## 7. 裁定パッケージ (ユーザーへ) と将来 wave の設計メモ

1. read-heavy 10 s の入力取得 (bench を伴う) と、B-8 の対象・種・長さ。
2. 校正規則 ≤ 600 s の扱い (改修版では bal10 478 s / wh10 297 s)。
3. 既存 campaign lock の drift の扱い (旧成果物保存 + 新 closure で再走)。
4. 将来 wave (read-heavy 10 s 級): source 範囲で bucket 化した set 再生 + CSR (dst 順は set 反復順を保存、root は初出順)、`U ≤ 2N` の txid 直接 index Tarjan、txid ごとに int object を 1 個共有する table — [T-2351] の候補。前判定 (v) は rw 辺が commit 順・txid 順で逆向きになりうるため不採用。

## 8. 工数・再現

- codex 子: profile author 1 (19 call 級)、plan 1、consult 2、author 2 (単位 1 / 2)、compare-probe author 1、review 2。計算ノード job: profile 9 (+ 失敗 attempt 6)、焦点走 2、compare 14、変異 probe / 本走。
- 再現: `python3.10 -B probe/verifier_profile_probe.py run|compare ...` (job dir)。判定同一性は `orchestrator/tests/test_verifier.py::test_capacity_all_fixture_results_match_frozen_baseline`。
