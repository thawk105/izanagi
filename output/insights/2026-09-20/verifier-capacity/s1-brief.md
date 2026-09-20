# 段 1 brief — verifier の容量: 10 s trace の未完走 2 型の原因同定と、省メモリ化・分割の設計・実測

- wave: `dev-wave-verifier-capacity`、worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-verifier-capacity` (branch `worktree-dev-wave-verifier-capacity`、base = local main `947fd160a`、2026-09-20 13:2x JST)、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verifier-capacity/`
- 台帳 ID: 未起票 (段 7 で採番)。起動 gate rc=0、重複検査: 42 worktree で `orchestrator/verifier/*.py` は全 file byte 一致 (誰も触っていない)、branch tip 差分 0。

## 研究前進 (1 行)

B-8 (種を変えた長時間実行による最終候補の検証、`docs/paper-story/2026-09-20.md` §8) は「長さ」要件で止まっている — trace-enabled 10 s 走の trace を現行 verifier が完走できない (balanced 14.2〜14.7M commit で SIGKILL、write-heavy 8.3M commit で 3600 s timeout、read-heavy は 6 s でも 808〜864 s / 主 process 80〜86 GiB。D2160 項 4、insight `output/insights/2026-09-20/verify-phase-adopted-backoff/README.md` §5.3)。完了判定 = (1) 未完走 2 型の原因を計算ノードの実測 (phase 別 wall と process tree の記憶量) で同定、(2) 改善案の効果を実装前に実測で見積もる、(3) 改修 verifier で保全済み 10 s trace × 3 workload (fixed-5) が node memory (≤ 115 GiB) 内・hard timeout 3600 s 内に完走し、verdict / certified / anomaly_count / total_cycles / integrity / stats が現行と一致する負例 (完走済み校正 12 verdict + `orchestrator/tests/fixtures/` の緑 fixture 全件) と正例 (anomaly fixture 全件で赤) を変更前後で同一に保つ。

## scope (実アンカー)

- 変更面: `orchestrator/verifier/parse.py` (`_parse_file_to_columns` L547〜、`_parallel_file_outcomes` L627〜、`_merge_issues_and_winners` L695〜、`_effective_worker_count` L493〜)、`orchestrator/verifier/dsg.py` (`_build_compact` L253〜 = producer / versions の dict、`_build_compact_edges` L290〜 = fork した edge worker と `adjacency: Dict[int, Set[int]]` の再生 L364〜、`_edge_candidates_for_task` L110〜、`_sccs` L429〜 = Tarjan)、`orchestrator/verifier/core.py` (`verify_trace_dir` L28〜、必要時のみ)、`orchestrator/tests/test_verifier.py` (既存期待値は変えない、追加のみ)。**`orchestrator/verifier/` に新 file を作らない** (enforcement source closure は exact path 集合: `orchestrator/campaign/campaign_lock.py` L58/L127/L155、`orchestrator/qualification/contract.py` L75〜78、test 4 本。D1552 の同じ制約)。
- 段 1 の計測物: job dir `probe/` の使い捨て profile probe (Codex author 作、repo へ入れない)。計測は Pegasus gen_S 計算ノードへ generic dispatch (login 直実行禁止、node ごとに detached submit-tree、`p2_2._assert_single_tenant()` を verifier 直前に実行)。入力 = 前 wave の保全済み zstd trace (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verify-phase-adopted-backoff/run/calib/fixed-5-<w>/extime-<e>/trace/*.zst`、原本 sha256 は同 dir の `preservation.json`)。
- scope 外: CCBench・patch・性能計測 build (規律 1、触らない)、`orchestrator/campaign/pipeline.py`・runner・校正規則 (≤ 600 s、D2160)・phase doc・campaign lock・capability / receipt の意味論、新 protocol、新 gate・台帳・一般化、verifier CLI の引数意味論と JSON schema。
- 成果物影響 (DW-G05): 放置すると B-8 の「長さ」は 3 s に固定され、10 s の certified 判定は永久に得られない。改修は certified 選択・レポート・台帳の既存値を変えない (規律 7)。verifier bytes が変わるので既存 campaign lock は `contract-loader-drift` で再開不能になる (D1552 と同じ帰結、新規 lock は影響なし)。

## 確定済み裁定 (従う)

- D1552: 並列化は純データ処理の段まで、判定・受領証は親。子は固定幅配列と token blob だけを返す。`orchestrator/verifier/` に新 file を作らない。
- D1553: 既定並列度は記憶量で決め上限 16。明示 `workers` の上限 48 は変えない。
- D1664: 辺結合は「task 順の連結 + `set.update`」に限り、登録 pass を持つ dense 配列 Tarjan と親が read を走査する鍵の大域 id は所要の実測で退けた。「登録 pass を持たない形」「writer を持つ鍵だけに id を振る形」は別 wave の候補として残されている (本 wave はその候補を記憶量の実測で評価する立場)。
- D1817: 同一 trace から同一の anomaly digest (決定性)。D2160 項 5: 校正の未完走は `indeterminate (operational)`、判定規則は変えない。
- 絶対規律 2 / 3: cycle 検出 (G0/G1c/G2) と integrity 検査 (framing / orphan / version dup / lock coverage / write intent / permutation / commit witness) の意味を 1 つも弱めない。anomaly は構造化のまま。

## 不変条件

1. 負例・正例の verdict 同一性 (上の完了判定 (3))。**`result_to_dict` の sha256 一致**を fixture 全件 (`test_verifier.py` の exact pin 含む) と、現行 verifier が完走する校正 trace (3 s 全 3 workload) で要求する。
2. 性能計測 build に影響しない (Python 側のみ、CCBench は不変)。
3. `orchestrator/verifier/` の file 集合は不変 (closure)。verifier に新しい第三者依存を入れない (P1)。
4. 部分結果の採用・完全性検査の緩和はしない (D1552)。fallback (逐次) の経路は残す。
5. 実装は段 1 の実測で効果を見積もった案だけ (未確認のまま実装しない)。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) verifier は stdlib のみ (`array` / `bisect` / `multiprocessing` fork / `gc.freeze`) で足り、numpy 等を入れない。理由: 正しさ判定の実体を版の pin されない外部 C 実装へ移すと identity (closure は .py だけ) から漏れる。計算ノードの `/usr/bin/python3.10` に numpy は user site (`~/.local`) にあるが、scipy は無い。
- (P2) 判定同一性は verdict 層 (verdict / certified / anomaly_count / total_cycles / integrity / stats.edges) だけでなく **witness 列 (anomalies) の bytes まで**要求する。現行の witness 選択は `adj` の tuple 順 = Python set の反復順に依存しており (`dsg.py` L364〜 のコメント)、辺の格納形式を変えると witness が変わりうる。既定は「同一を要求」、変えるなら段 4 で裁定パッケージにする。
- (P3) 原因仮説 (実装前に段 1 で実測して確認): (a) 主 process の記憶量は writes に比例する producer / versions の dict (`(str key, (epoch, tid)) → txid`、write ごとに新 str object、≈ 400 B/write: write-heavy 6 s 47M write で 18.8 GiB) と edges に比例する `set` 隣接 (≈ 150 B/edge: read-heavy 6 s 595M edge で 85.6 GiB) で決まる。(b) balanced 10 s の SIGKILL (主 process 21 GiB の時点、wall 303 s) は edge worker 16 本が fork 後に親の object graph (dict / tuple / int) の refcount と GC header を触って copy-on-write で page を複製し、node 128 GiB を枯渇させた (F840 が言う「RSS の二重計上」ではなく実際の複製。判別は各 worker の `Private_Dirty` と node の `MemAvailable`)。(c) write-heavy 10 s の 3600 s timeout (主 process CPU 520 s < 6 s 走の 816 s、maxrss 17.9 GiB 頭打ち) は同じ CoW 膨張が swap / 圧縮 memory の thrash か worker の OOM kill → `BrokenProcessPool` → 親の逐次 fallback へ落ちた形 (どちらかは実測で分ける)。
- (P4) 目標は「10 s × 3 workload の完走 (≤ 115 GiB、≤ 3600 s) と verdict 同一性」であり、校正規則 (verifier wall ≤ 600 s) の充足は目標にしない (規則の改訂は裁定事項)。所要の短縮は記憶量の削減に付随する分だけを取る。
- (P5) 改善案の候補 (段 2 の plan が file:line で具体化、段 1 実測で効果を見積もる): (i) producer / versions を鍵ごとの `array` (version を 1 整数に詰め、producer txid を並走 array) にして dict entry を write 単位から鍵単位へ、(ii) fork 前に `gc.freeze()`、worker は親の Python object graph に触れず配列だけ読む、(iii) 隣接を `set` から CSR (offsets + dst の `array`) へ、重複除去は source ごとに局所 (辺候補を source 範囲で分割 = 「分割」)、(iv) Tarjan を txid を直接 index にした配列で (登録 pass なし、txid は dense)、(v) 「全辺が txid 順に前向きなら非巡回」の健全な前判定 (任意の全順序で成り立つ数学的事実。発火しなければ全 Tarjan) — (v) は正例で必ず全 Tarjan に落ちることを test で固定する。

## 成果物の形

1. 段 1 profile: `run/profile/<w>-<e>/` (phase 別 wall、主 process と worker の RSS / Pss / Private_Dirty 時系列、node MemAvailable / Swap、pool の破綻有無、exit signal)、要約表を insight に。
2. 改修 verifier (`parse.py` / `dsg.py` / `core.py`) + `test_verifier.py` の追加 test (同一性・正例が全 Tarjan に落ちる・fallback)。
3. 改修版の実測: 保全 10 s trace × 3 workload の再検証 (wall / maxrss / verdict) と、現行版との verdict 一致表 (3 s × 3 workload、fixture 全件の `result_to_dict` sha256)。
4. insight `output/insights/2026-09-20/verifier-capacity/README.md`、spool fragment (worklog / decisions)、変異 matrix、受入。

## 並列分割

- 段 1: profile probe = Codex author 1 本 (job dir `probe/`)。計測 job = 4 本 (balanced 10 s、write-heavy 10 s、read-heavy 6 s、balanced 6 s を node 別 submit-tree で並行)。
- 段 2 / 3: plan 1 本、consult 2 本 (正しさ境界 / 過剰・削除)。
- 段 5: 実装単位 1 (parse / dsg / core / test_verifier は密結合)。段 6: review 2 本 + fix 子。
- 受入・実測環境: 受入は `tools/dev_wave_wait.py acceptance`、実測は gen_S 計算ノード (runbook §7、単独性は node 上で実測)。
