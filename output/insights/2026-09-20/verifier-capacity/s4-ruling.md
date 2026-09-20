# 段 4 裁定 — verifier の容量 (dev-wave-verifier-capacity)

親 (Claude) の裁定。入力 = 段 1 brief (`s1-brief.md`)、段 1 profile 実測 (`run/profile/*/`、要約は §1)、段 2 plan (`codex/s2-plan.md`)、段 3 相談 A (`codex/s3-consult-A.md`) / B (`codex/s3-consult-B.md`)。本文の行番号は base `947fd160a`。

## 1. 段 1 実測 (計算ノード、現行 verifier、probe `probe/verifier_profile_probe.py` sha `bc86ca22…`)

| run | node | txns / reads / writes | phase wall s (parse / producer / edge-workers / replay / scc) | 親 RSS peak GiB | node used peak GiB | worker Private_Dirty 最大 GiB | 結末 |
|---|---|---|---|---|---|---|---|
| bal10 (14.7M commit) | bnode029 | 14.75M / 73.1M / 73.4M | 55 / 172 / (fork +80 s で kill) / — / — | 20.7 | 111.5 (t≈295 s) | 5.8 | **t≈308 s に OOM kill (`vmstat oom_kill` 0→1、全 process 消滅)**。前 wave の 303 s / rc −9 / 21.2 GiB と一致 |
| wh10 (8.3M commit) | bnode0xx | 8.32M / 4.1M / 78.4M | 28 / 175 / (fork +65 s で worker kill) / — / — | 17.5 | 119.2 (t≈265 s) | 6.7 | **t≈270 s に worker 1 本が OOM kill (oom_kill=1、np 17→16)、残 15 worker は state S で停止、node 114 GiB のまま、親は待つだけ** (= 前 wave の 3600 s timeout・親 CPU 低の正体) |
| bal6 (8.9M) | bnode0xx | 8.86M / 43.9M / 44.1M | 33 / 100 / 62 / 110 / 46 (計 356、前 wave 357) | 25.5 | 77.1 (edge-workers) | 3.9 | 完走 serializable。**完走する 6 s でも edge-workers 段の node peak は CoW で 77 GiB** |
| bal6gf (= bal6 + `gc.freeze()` を fork 前に) | bnode044 | 同上 | 33 / 100 / 60 / 110 / 46 | 25.4 | 76.1 | 4.2 | 完走。**freeze 単独は CoW をほぼ減らさない** (peak 77.1 → 76.1、worker 最大 3.9 → 4.2) |
| rh6 (32.8M) | bnode0xx | 32.75M / 308.3M / 16.4M | 135 / 57 / ≈110 / (進行中) | — | 70.6 (edge-workers) | 3.3 | (集計待ち) |
| bal10w8 / bal10w4 / wh10w8 (worker 数対照) | — | — | — | — | — | — | (集計待ち、§3 の D-3 で参照) |

parse 段: 16 worker の Txn object でも node peak は 18 GiB (bal10)、worker 最大 1.4 GiB — 支配項ではない (仮説 P3 のうち parse 側は棄却)。swap (24 GiB) は使われていない (`pswpout` 不変)。単独性: 全 run で `_assert_single_tenant` OK、開始時 MemAvailable ≥ 117 GiB。

**原因の同定 (仮説 P3 の判定):**
- (a) 主 process の記憶量は producer / versions 構築 (`_build_compact` L253〜) で writes に比例して増え (bal10: 4.0 → 19.1 GiB、73.4M writes → 約 220 B/write 増分)、replay (`set` 隣接、L364〜) で edges に比例して増える (bal6: 13.6 → 25.5 GiB、128M edges → 約 100 B/edge 増分)。単価は phase 増分として測った (段 3 A/B の指摘どおり全体比ではない)。
- (b) **fork した edge worker が親の Python object (producer dict の key tuple / value int、versions list の版 tuple) に refcount で触り、copy-on-write で page を複製する** — 各 worker の `Private_Dirty` は fork 後 15 s で 3〜4 GiB、最大 5.8〜6.7 GiB に達し (worker 自身の出力配列は数百 MB)、node の MemAvailable の減少と一致する。`gc.freeze()` 単独では減らない (bal6 vs bal6gf) ので、GC header の書込みでなく refcount 書込みが主因である。これは「対照比較で補強した同定」であり、page 単位の帰属 (どの object の page か) までは測っていない。
- (c) 2 型の違いは OOM killer の選択: balanced は親 (最大 RSS ≈ 20.7 GiB + 共有 page) が殺され rc −9、write-heavy は worker が殺され `BrokenProcessPool` → 残 worker が `executor.shutdown(wait=True)` の下で停止 (state S) → 親は待ち続け hard timeout。swap / thrash 型ではない。

## 2. 段 3 の所見の real / refuted

| # | 所見 | 判定 | 反映 |
|---|---|---|---|
| A-3 | JSON bytes 一致は非 wire integrity (expected/observed commits、proof_surfaces) の代用にならない | real | 同一性検査は `result_to_dict` の sha256 + `VerifyResult` 全 field (dataclass 等価) + 境界 trace の隣接 tuple・SCC 列の比較 (§4 (b)) |
| A-5 | source replay の完全性の実行時検査が無い | real (ただし §3 で (iii) を本 wave の外に出したので、本 wave では task 完全性検査 (L99〜107) を保つ義務として残す) | (iii) を採る将来 wave の前提条件として記録 |
| A-8 / B-7 | Private_Dirty だけでは CoW を同定できない | real → 対照 (freeze A/B、worker 数) を足した。§1 (b) の限定を明記 | 記録 |
| A-9 | 観測 schema と閾値の固定、write-heavy を候補比較入力に、facts の完走行は 6 件 | real | §4 (c) に固定。facts の「7 件」は plan の誤りで 6 件が正 |
| A-1 / A-2 | packed 化の退避と genesis / dup note の順序、last-wins の辺集合を固定する test | real | 実装契約 §4 (a)(3)(4)、追加 test §5 |
| A-4 | P2 は A 案、B は別裁定 | real | **A 案を採る** (§3 D-4) |
| A-6 | freeze の子 GC 状態・initializer 順序 | real だが **freeze は不採用** (bal6gf) | 不要 |
| A-7 | T126 code identity の帰結が未点検 | real | §6 に対応表 (旧 identity は歴史記録、再発行は要求しない) |
| A-10 / B-12 | 「3 s に固定」「永久に」「B-8 の長時間実行を可能にする」は言い過ぎ | real | 成果物影響を「保全済み fixed-5 trace の容量障害の除去。B-8 取得は主張しない」に置換 |
| B-1 / B-3 / B-5 | 最小案から: (i)+(ii) が同じ構造変更で、(iii)(iv)(v) は未完走 2 件の解消に不要 | real | **本 wave は (i)+(ii) と pool 破綻の停滞修正だけを実装**。(iii)〜(v) は設計メモとして記録し実装しない (§3) |
| B-2 | 既定 worker 削減を候補から排除する根拠がない | 部分 real: 対照を測った (bal10w8 / w4 / wh10w8)。**既定 16 は変えない** (D1553 の pin、根本原因は worker 数でなく共有 object graph の複製で、削減は所要を伸ばし規模で再発する) | §3 D-3 に対照値を記録 |
| B-4 | read-heavy 10 s は未保全・未実走 → 完了条件を修正 | real | **完了条件 = 未完走 2 件 (bal10 / wh10) の完走 + 完走済み 6 s / 3 s の同一性**。read-heavy 10 s は入力が無く本 wave の対象外 (§3 D-1) |
| B-6 | 局所修正表 (key str 共有、per_key 解放、seen 削除、fallback の参照解放) | real (一部は (i) に吸収、fallback 解放は採用) | §4 (a)(5) |
| B-9 | 不採用案の test / view は作らない | real | §5 の test は採用変更の境界だけ |
| B-10 | 600 s は副次観測 | real (P4 不変) | 報告欄を分ける |
| B-11 | author 一本は過大 | real | 段 5 を単位 1 (packed producer + 配列 worker) → 単位 2 (pool 破綻の停滞修正 + fallback 解放) の直列 2 author にする |
| A / B 共通 | brief の 400 B/write・150 B/edge は全体比、「主 process CPU 520 s」は worker 合算 | real | brief 誤りとして記録 (§7) |

## 3. 裁定

- **D-1 完了条件 (brief の完了判定 (3) を置換):** 改修 verifier で保全済み **bal10 (14.75M commit) と wh10 (8.32M commit) が node memory ≤ 115 GiB・hard timeout 3600 s 内に完走**し、完走済み 12 verdict (fixed-5 / fixed-10 × {wh, bal, rh} × {3 s, 6 s}) の同一 trace で旧 verifier と `result_to_dict` sha256 + 全 field が一致、fixture 全件で一致 (正例は全件 anomaly で赤)。read-heavy 10 s は入力不在で対象外 (取得は bench を伴うため別裁定へ返す)。
- **D-2 採る案:** (i) 鍵単位の packed 配列 (versions を `(epoch<<32)|tid` の `array("q")`、producer txid を並走 `array("q")`、鍵は writer を持つものだけに初出順 id、file ごとの `token_id → key_id` 配列を親が作る) と (ii) edge worker の入力を配列だけにする (worker は producer dict / versions list / keys tuple に触れない。lookup は `bisect` を array 上で `lo/hi` 付きで行う) を **1 つの変更**として実装する。`gc.freeze()` は採らない (bal6gf で効果なし)。範囲外 (epoch / tid が 32 bit 非負に収まらない) は現行の tuple 経路 (packed 化しない builder) へ退避し、部分状態を残さない (A-1)。
- **D-3 既定 worker 16 は変えない** (D1553)。対照 (bal10w8 / bal10w4 / wh10w8) は記録のみ。
- **D-4 判定同一性 (P2) = A 案:** `adj` は dict-of-tuple のまま、set 再生順・root 初出順を変えない。witness bytes を含む `result_to_dict` の完全一致を要求。
- **D-5 (iii) CSR / (iv) 配列 Tarjan / (v) 前判定は実装しない。** 理由: 未完走 2 件は edge-workers 段の CoW で死んでおり、replay / SCC 段には到達していない。bal10 の replay 見込み (約 215M edge × 100 B/edge ≈ 22 GiB + 親 19 → 5 GiB (packed 後)) は上限内。(v) は rw 辺が commit 順・txid 順で逆向きになりうる (`_classify` docstring) ので緑 trace で発火する見込みが無く、採用条件 (緑 1 件で発火) を満たさない。read-heavy 10 s (見込み 1B edge) を扱う将来 wave の候補として §8 に設計を残す。
- **D-6 pool 破綻の停滞:** worker が OOM kill 等で消えた (`future.result()` が例外) とき、残 worker を殺してから (SIGKILL) `shutdown` し、部分結果・future 参照を解放して**全件**を親で逐次再計算する (D1552 の fallback を「終端する」形にする)。parse 側 (`_parallel_file_outcomes` L627〜) も同型。受理集合は変えない (部分結果は採らない)。
- **D-7 変異 (事前登録、§5):** 採用分岐だけに変異を適用する。
- **D-8 段 5 の分割:** 単位 1 = (i)+(ii) (`dsg.py` + `test_verifier.py`)、単位 2 = D-6 (`dsg.py` / `parse.py` + test)。直列 (単位 2 は単位 1 の統合 commit から)。
- **D-9 最終実測 (段 6 後):** 計算ノードで (a) bal10 / wh10 を改修版で完走 (probe の `_child` を改修版で走らせ phase wall / peak / verdict を記録)、(b) 12 verdict trace + 3 s 校正で **同一 job 内に旧版 (`947fd160a` の `orchestrator/verifier`) と改修版を別 process で走らせ** `result_to_dict` sha256 と全 field を比較、(c) fixture 全件は login で pytest。600 s 規則は別欄。

## 4. 実装契約 (単位 1、Codex author)

(a) `dsg.py`:
1. `_build_compact` L253〜: winner を rank 順に走査し write ごとに `(key_id, packed_version, txid, ordinal)` を集め、鍵ごとに版昇順 (同版は ordinal 順) に整列。重複版は最初の writer を残し、以後の異なる txid の occurrence を `version_dups` に数え、note (`version dup: key=… ver=(e, t) by txid A and B`) を **走査順 (ordinal 順)** で `integrity.notes` に積む (現行と同じ順序・同じ文言)。`genesis_commits` の note も現行の位置 (txn 単位、write の有無に依らず) を保つ。
2. `self.producer` / `self.versions` は現行の消費者 (`_reasons` L517〜、`core.py` L186 `len(dsg.versions)`、test L2604〜/L2725 の `graph.producer[(key, ver)]`・`tuple(graph.versions)`・`graph.versions.get(key)`) が使う操作だけを持つ薄い view (`__getitem__` / `get` / `__contains__` / `__iter__` (writer 鍵の初出順) / `__len__`) にする。通常経路 (worker / replay / SCC) は view を通さず配列を直接使う。
3. `_EdgeWorkerState` の field 名 (`trace`, `producer`, `versions`, `keys`) は保ち、値は配列側の構造 (view と同じ object でよい)。`_edge_candidates_for_task` の戻り (`_EdgeCandidateColumns`: `run_src` / `run_offsets` / `run_dst` / `orphan_reads`) と **run の順序 (source 初出順、宛先は現行の `add` 呼出し順)** を変えない。worker 内で親の dict / list / str / tuple object に触れない (token blob の bytes slice と array の要素取り出しだけ)。
4. packed 化の適用条件: 全 write の epoch / tid が `0 ≤ v < 2**32`。1 つでも外れたら packed 構造を捨てて現行 builder (tuple 版) で最初から作り直す (integrity を二重計上しない)。legacy 経路 (`_LegacyTrace` → `DSG(txns)`) は不変。
5. fallback (`outcomes is None` の枝 L352〜) と parse 側 L793〜: 逐次再計算の前に `received` / futures / executor への参照を解放する (B-6)。
(b) 不変: `core.py` は変更しない (必要なら理由を報告)。`report.py` / `model.py` / CLI schema 不変。`orchestrator/verifier/` に新 file を作らない。既存 test の期待値を変えない。`_LAST_DSG_WORKER_PIDS` の意味論 (採用 outcome の pid、fallback は親 pid) 不変。
(c) 観測 schema (最終実測で固定): `phase.wall_s` (parse / producer / edges-workers / adjacency-replay / scc)、`peaks.node_used_kib_peak`、`peaks.sum_private_dirty_kib_peak`、`peaks.worker_private_dirty_kib_max`、`peaks.main_vmrss_kib_peak`、`vmstat_delta.oom_kill`、`stop_reason`、`serializable`。採用判定: bal10 / wh10 が `completed` かつ `node_used_kib_peak ≤ 115 GiB`。付随の期待 (未達でも不採用にはしないが報告する): bal6 の producer 段の親 RSS 増分 ≤ 0.25 × 現行 (8.5 GiB)、edge-workers 段の worker Private_Dirty 最大 ≤ 0.2 × 現行 (0.8 GiB)、各 phase wall ≤ 1.5 × 現行。

## 5. 追加 test と変異 (事前登録)

追加 test (`orchestrator/tests/test_verifier.py` 末尾の runner より前):
- `test_capacity_packed_versions_preserve_bounds_duplicates_and_notes` — 同鍵同版の複数 writer (同 file / 別 file)、genesis 以下の commit、範囲外 (epoch ≥ 2**32) の退避、notes の順序と文言を literal で固定。
- `test_capacity_last_wins_drops_old_writer_edges_and_orphans_reads` (A-2) — last-wins で消えた旧 writer の辺が無く、その版の read が orphan になることを辺集合・stats・integrity で固定。
- `test_capacity_edge_worker_reads_only_arrays` — `_EdgeWorkerState` に渡す view を「dict / list 操作を呼ぶと例外を投げる代役」に差し替えても `_edge_candidates_for_task` が完走する (worker が Python object graph に触れないことの機構検査、F649 型: 実体を名指し)。
- `test_capacity_all_fixture_results_match_frozen_baseline` — fixture 全件の `result_to_dict` を旧版で固定した sha256 一覧と照合 (一覧は親が base `947fd160a` の pytest 走で採る)。
- `test_capacity_workers_1_and_16_match` — 合成 trace で `workers=1` / `16` / 既定の `result_to_dict` 一致 (既存 L2211 型)。
- (単位 2) `test_capacity_broken_pool_terminates_workers_and_falls_back` — worker が `os._exit` で死ぬ task を注入し、残 worker が終端され、全件が親で再計算され、結果が逐次と一致、`_LAST_DSG_WORKER_PIDS == {os.getpid()}`。

変異 matrix (採用分岐に限る):
| 変異 | 殺す test |
|---|---|
| 同版重複の最後の writer を採る | packed_versions test、既存 L2704 |
| 版の整列を tid 優先にする / packed を wrap する | packed_versions test、既存 L2062 / L2073 |
| 範囲外で退避せず切り捨てる | packed_versions test |
| worker が親 dict を読む経路を残す | edge_worker_reads_only_arrays |
| run の宛先順を昇順に sort する | 既存 L2506 / L2576 |
| rw の直後版を `bisect_left` にする (直後でなく同版) | 既存 L2073、fixture r7 |
| 破綻時に部分結果を採用する | 既存 L2734、broken_pool test |
| 破綻時に残 worker を殺さない | broken_pool test (timeout 付き) |

## 6. identity / closure の帰結

- `orchestrator/verifier/dsg.py` (と単位 2 で `parse.py`) の bytes が変わる → enforcement source closure (`campaign_lock.py` L58/L127/L155) の digest が変わり、**既存 campaign lock は `contract-loader-drift` で再開不能** (D1552 と同じ帰結)。新規 lock は改修後 bytes で生成される。旧 lock の扱い (旧成果物保存 + 新 closure で再走) は裁定パッケージ (§9)。
- T126 code identity (`qualification/contract.py` L75〜78): 旧 qualification 記録は歴史記録として不変。再発行は本 wave で要求しない。
- 凍結成果物の live pin は無い (DW-O09、handoff 参照)。

## 7. brief の訂正 (追記で)

- 「保全済み 10 s trace × 3 workload」→ 保全済みは bal10 / wh10 の 2 件 (read-heavy 10 s は `not_run`)。
- 「400 B/write・150 B/edge」は主 process 全体比。phase 増分は約 220 B/write (producer)、約 100 B/edge (replay)。
- 「主 process CPU 520 s」は worker 合算の rusage。
- 「長さは 3 s に固定され、永久に得られない」→ 「現行 verifier では 10 s の 2 workload が完走しない」。

## 8. 将来 wave への設計メモ (実装しない)

(iii) source 範囲で bucket 化した set 再生 + CSR (dst の順は set 反復順を保存、root は初出順)、(iv) `U ≤ 2N` の txid 直接 index Tarjan、txid ごとに int object を 1 個共有する table で dict-of-tuple の辺単価を 8 B へ — read-heavy 10 s (見込み 1B edge) を扱うときの候補。(v) は不採用。

## 9. 裁定パッケージ (ユーザーへ返す、本 wave は実装しない)

1. read-heavy 10 s の入力取得 (bench を伴う) と B-8 の対象・種・長さ。2. 校正規則 ≤ 600 s の扱い (本 wave は容量完走を適格化と扱わない)。3. 既存 campaign lock の drift (旧成果物保存 + 新 closure で再走)。

## 10. 裁定 inbox の再走査 (段 4 直前、14:14 JST)

`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/` の wave 開始 (13:15) 以後の更新は 3 件 (`2026-09-20-t750-w4-oracle-wiring-launch-pending.md` 13:30、`2026-09-20-rulings-full25-verdicts.md` 13:02 は開始前、`2026-09-20-t2724-ax-approval-by-ai.md` 12:50 は開始前)。いずれも verifier / 直列性検査の容量に触れない。本裁定を変える更新なし。

## 11. 段 5 投入 (14:15 JST)

単位 1 author を `codex/prompt-u1-author.md` で投入 (worktree `.codex/worktrees/vcap-u1`、base `947fd160a`、所有 `orchestrator/verifier/dsg.py` + `orchestrator/tests/test_verifier.py`)。§1 の集計待ち行 (rh6 / bal10w8 / bal10w4 / wh10w8) は D-2〜D-9 を変えない (D-3 の対照値として追記する)。

## 1b. 段 1 実測の確定表 (14:17 JST、`run/profile/<label>/result.json`。wall は秒、記憶量は GiB)

| run | node | 結末 | total | parse | producer | edge-workers | replay | scc | node used peak | 親 RSS peak | worker Private_Dirty 最大 | edges |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bal6 (8.86M txn) | bnode040 | 完走 serializable | 553 (見積り込み) | 33 | 101 | 62 | 112 | 45 | 80.4 | 27.7 | 4.8 | 128.0M |
| bal6gf (+gc.freeze) | bnode026 | 完走 | 326 | 33 | 102 | 34 | 85 | 46 | 78.9 | 27.5 | 4.7 | 128.0M |
| rh6 (32.75M txn) | bnode042 | 完走 | 1090 (見積り込み) | 135 | 57 | 122 | 322 | 277 | 86.0 | 85.6 | 3.7 | 594.8M |
| bal10 (14.75M) | bnode029 | **OOM kill (oom_kill=1、rc −9、t≈308)** | 325 | 55 | 173 | (kill) | — | — | 113.6 | 20.7 | 6.1 | — |
| wh10 (8.32M) | bnode018 | **worker OOM kill → 残 15 worker が S で停滞** | (hard timeout 待ち) | 28 | 175 | (kill) | — | — | 119.2 | 17.5 | 6.7 | — |
| wh10w8 (`--workers 8`) | bnode083 | 完走 serializable | 500 | 45 | 175 | 109 | 118 | 32 | 71.7 | 29.1 | 7.7 | 85.0M |
| bal10w8 (`--workers 8`) | bnode103 | 完走 serializable | 746 | 89 | 176 | 172 | 196 | 79 | 78.9 | 46.4 | 8.3 | 215.1M |
| bal10w4 (`--workers 4`) | bnode019 | 完走 serializable | 882 | 162 | 173 | 256 | 181 | 77 | 52.4 | 46.0 | 8.9 | 215.1M |

- 見積り (同 process 内、SCC 後に graph を解放して同じ write 列から構築、`estimate.dict_producer` vs `estimate.packed_producer`): **bal6 (44.1M write): dict 8.96 GB / 104.5 s → packed 1.96 GB / 69.8 s (記憶量 0.22 倍、wall 0.67 倍)。rh6 (16.4M write): 4.15 GB / 61.9 s → 1.04 GB / 53.4 s (0.25 倍、0.86 倍)。** 採用条件 (≥64 B/write 削減、peak ≤ 0.75、wall ≤ 1.5) を両入力で満たす (削減 159 B/write / 190 B/write)。
- worker 数の対照 (D-3): 8 worker なら現行 verifier でも bal10 / wh10 は完走する (node peak 79 / 72 GiB) が、worker 1 本あたりの Private_Dirty はむしろ増える (16 worker 6.1 → 8 worker 8.3 → 4 worker 8.9 GiB) = **CoW は task 範囲でなく親の object graph の大きさで決まる**。所要は 16 → 8 で edge-workers 段が 1.6〜2 倍、4 で 4 倍。既定 16 は変えない (D-3 のとおり)。
- read-heavy 6 s: replay 322 s + scc 277 s が所要の 55%、親 RSS 85.6 GiB は replay の `set`/tuple 隣接 (595M edge) が支配。read-heavy 10 s (見込み 1.2B edge) は本 wave の対象外だが、(iii)/(iv) の必要性の根拠としてここに残す。
- wh3 (write-heavy 3 s、2.53M txn、23.8M write、bnode017、14:41 確定): 完走 214 s (parse 8 / producer 53 / edge-workers 15 / replay 27 / scc 9)、node peak 39.9 GiB、親 RSS 9.6 GiB、worker Private_Dirty 最大 2.5 GiB。見積り: dict 5.28 GB / 54.9 s → packed 1.55 GB / 36.0 s (0.29 倍、0.66 倍)。write-heavy 入力でも (i) の採用条件を満たす。
