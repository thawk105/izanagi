# [T-2256] 直列性検査の親に残る直列部を縮めた — 辺の結合を「順番どおり並べて足す」形に変え、読み中心の 68 万 txn で 18.2 s → 12.6 s (1.45 倍)、判定は 1 bit も変えない

- 日付: 2026-09-05 (実装・計測) 〜 2026-09-07 (レビュー裁定・変異・記録)
- branch: `worktree-dev-wave-t2256-verifier-serial`、基準 main 97ee3cd3a、採用 tip 54183270 (unit 1 709e57b6 + unit 2)
- 変更 file: `orchestrator/verifier/dsg.py`、`orchestrator/tests/test_verifier.py` だけ。`parse.py` / `core.py` は未変更
- 実装: Codex `role=author` (gpt-5.6-sol、xhigh) 3 単位 (unit 3 は親の実測で撤回)。計測・裁定・記録は親 (Claude)
- 一次資料: `output/insights/2026-09-02_t2191-verifier-parallel/README.md` (前 wave。親側直列部が 38.6%、並列度 16 で飽和、漸近 2.6 倍)

## 何を縮めたか

前 wave (T-2191) で parse と辺候補の生成は fork 子へ出したが、親には次の直列部が残っていた。68 万 txn・並列度 16 で総 18.2 s のうち、辺の結合 (子の結果を親で隣接表に入れる) が約 11.4 s、SCC が約 3.0 s、producer 表の構築が約 1.0 s、winner 再生が約 0.5 s。

本 wave が変えたのは辺の結合だけである。

- **P1: 子の結果を task 番号順に並べて連結する。** 旧は `heapq.merge` で全子の辺列を大域 ordinal 順に合流していた (O(E log P))。task ごとの ordinal 範囲は互いに素で単調 (read task は winner rank の連続範囲、ww task は key の連続範囲、全 read task が全 ww task より前) なので、task 番号順に連結すれば同じ列になる。完全性 (件数と task 番号の集合が `range(task_count)` に一致) は helper `_ordered_complete_edge_outcomes` で検査し、欠けていれば並列結果を全部捨てて逐次に戻る (部分結果は採用しない、旧と同じ)。
- **P2: 子が source ごとに辺の宛先を run にまとめ、親は `set.update(array slice)` で一括投入する。** 子は宛先を source の初出順に dict-of-array へ群化し、`run_src` / `run_offsets` / `run_dst` の 3 本の array で返す。親は task 番号順 × run 初出順に `adjacency[source].update(run_dst[start:end])` する。set への挿入列が旧の逐次 `add` と同じ順になることは、親が fuzz (20000 試行、CPython 3.10.12) で列挙順一致を確認した (set の列挙順は witness の選択に効くので、ここが崩れると判定の witness 列が変わる)。

撤回した 3 案 (実測で親側が遅くなった):

- **P3 (dense 配列 Tarjan):** SCC 3.15 → 5.65 s に悪化 (txid → dense index の登録 pass が O(E) の dict lookup を足していた)。unit 2 で `_sccs` を 97ee3cd と byte 同一に戻した。
- **P4 (鍵の大域 id) + P5 (winner 再生の fast path):** producer 構築 (親) 0.94 → 2.98 s に悪化。P4 は read-only の鍵にも id を振るため、親が全 read を走査する O(R) loop を足していた (子の decode を親へ移した形)。P5 の winner 再生 0.53 → 0.50 s は n=3 で採用根拠にならない。差分は wave の job dir に `unit3-rejected.patch` として退避し、repo には入れていない。

## 測った結果

条件と生台帳の要約は本 dir の `measurements.md`。要点:

- 場所は Pegasus login node (96 core、共有・非専有、同時 13〜16 ユーザ、load 5〜17)。interpreter は CPython 3.10.12、`PYTHONHASHSEED=0`、affinity 0-95。旧 (97ee3cd の `orchestrator/` snapshot) と新を交互に走らせ、68 万 txn / 並列度 16 は 3 回、他は 1 回。
- 合成 trace 4 種 (48 file、1 txn 10 op、鍵 10 万、zipf 0.9): 170k (95% read)、680k (95% read)、170k-neg (2% stale read、non-serializable)、170k-wh (50% read、non-serializable)。入力の同一性は trace manifest sha256、判定の同一性は `result_to_dict` の sha256 で束縛した。

### 判定は変わらなかった

`result_to_dict` の sha256 は全 checkpoint・全 trace・並列度 1 / 16 / 48 で旧新一致 (台帳 100 行)。正例 2 種は serializable=true、負例 2 種は anomalies 1 (witness 列まで一致)。

### 速さ

68 万 txn、並列度 16、各走の中央値 (秒):

| 版 | 総 | 辺構築 (子+親) | SCC | producer 構築 (親) | winner 再生 | Pss 峰値 MB |
|---|---:|---:|---:|---:|---:|---:|
| 旧 (同系列) | 18.22 | 11.42 | 2.96 | 0.99 | 0.53 | 2260 |
| 新 (P1 + P2) | 12.60 | 6.17 | 2.93 | 0.94 | 0.53 | 2089 |

各走の比は 1.446 / 1.442 / 1.450。並列度 48 では 18.72 → 12.70 s、並列度 1 では 47.77 → 43.90 s (n=1)。

Amdahl の直列部 S = (16·T16 − T1)/15 は同系列で **16.25 s → 10.51 s** (T1 は n=1 の 2 点近似であり、共有ノード上のモデル値)。段 1 brief の 16.4 s は別走で、系列を混ぜない。残る直列部の内訳は set への挿入 + tuple 凍結 ≈ 5 s、SCC ≈ 3 s、producer ≈ 0.9 s、winner ≈ 0.5 s。

P2 単独の効果 (P1 だけの木と P1+P2 を交互 n=3): 総 14.37 → 12.99 s (3 走とも速い)、辺構築 7.49 → 6.40 s。Pss は P1 単独比 +4% (1982 → 2063 MB) で、旧 baseline 比では −8%。write-heavy (170k-wh) では総 wall に一貫した差がなく (4.71/5.13/5.50 vs 5.42/5.32/4.79)、Pss は +4〜5%。

### 記憶量について言えること

「Pss 峰値が悪化しない」は **680k read-heavy・並列度 16・50 ms poll の Pss 合計**に限った主張である。並列度 1 (480 → 514 MB) と write-heavy (1881 → 1940 MB、並列度 48 で 4095 → 4781 MB、n=1) では増えている。D1553 (既定並列度 16 は記憶量が根拠) は変えない。17M txn への下方外挿は cgroup の charged peak を測るまで行わない。

## B-10 read-heavy の 12 時間枠への含意 — まだ「入る」とは書けない

前 wave の見積り (検査器 1000〜1210 s/反復、並列化で 420〜500 s) に本 wave の倍率を当てると、検査器は約 275〜345 s/反復 (前 wave 公表値を 1.45 で割る計算と、並列化前 45.9 s → 12.6 s の累積 3.64 倍を当てる計算の包絡)。検査器外 240〜340 s を足して 515〜685 s/反復、75 反復で **約 10.7〜14.3 時間**。12 時間境界をまたぐので、入る可能性は生じたが保証しない。

但し書き (前 wave から継承): D1529 の欠測 attempt、17M txn は未実測、実 B-10 trace との版密度差、1.45 倍は 95% read の合成 trace 固有 (write-heavy では 5.80 → 5.72 s に留まる)、共有 login node での測定。

## 変異で歯を確かめた

変異は `orchestrator/verifier/dsg.py` の順序・完全性・SCC 探索に効く 1 行置換 8 本 (negative) と等価変異 1 本 (positive、SURVIVED 期待) で、Pegasus 計算ノードへ dispatch して走らせた (spec sha 74497e73…、baseline は緑)。probe (全 SURVIVED 期待) で実赤 node を採り、final spec に KILLED 期待で厳密固定した (harness は実赤集合と expected_nodes の完全一致で KILLED を判定する)。

| 変異 | 対象 (1 行) | 実赤 node | 判定 |
|---|---|---:|---|
| M1 | 完全性 helper の整列に `reverse=True` | 3 | KILLED |
| M2 | 親 replay の array slice を `[::-1]` | 3 | KILLED |
| M3 | anomalies の SCC 整列に `min(component)` tiebreak | 1 | KILLED |
| M4 | SCC の root loop を `sorted(self.adj)` | 1 | KILLED |
| M5 | Tarjan の low-link 更新を no-op 化 | 20 | KILLED |
| M8b | 完全性検査を「非空なら受理」へ緩める | 4 | KILLED |
| M9 | 子の source 群化を昇順 items へ | 1 | KILLED |
| M6p | SCC 探索の `self.adj.get(w, ())` を `self.adj[w]` | 23 | KILLED |
| E1 | `list(range(n))` を `[*range(n)]` (等価) | 0 | SURVIVED |

- **M8b (完全性検査の緩和) は計算ノードで 4 赤で KILLED.** 段 6 レビュー A の「pool 起動失敗環境では検査が緩んでも赤にならないかもしれない」という懸念は、実機の fallback 経路 (edge-worker 失敗テスト) が発火して否定された。環境依存の但し書きは残す (helper への直接テストは次の一手)。
- **M6p は M6 (dense 写像、unit 2 で撤回) の代替 anchor.** SCC 探索が destination-only node で `KeyError` を起こし 23 赤で KILLED。撤回した機構ではなく現行コードに注入できる 1 行変異へ再基準化した (レビュー A の should)。
- E1 は判定を変えない等価変異で、期待どおり SURVIVED (kill 率対象外)。

## テストと所要

焦点走 (`test_verifier` + consumer 4 file、Pegasus 計算ノード) は 565 passed / 19.86 s。新テスト 4 本 (workers=2/3/4 の fork を含む) は最遅 15 durations (最長 8.4 s、いずれも既存の critic テスト) に入らず、全体 5 分上限に余裕がある。closure drift 由来の `test_critic` 赤は commit 済みで消えた (非帰属)。provenance 全史監査は rc=0。

## この記録が保証しないこと

- 合成 trace は zipf の hot key が全 txn を結ぶため、負例の SCC は 1 個の巨大成分になる。複数 SCC の負例は既存 fixture (cycle3、dense_cycle4 等) と新テストの 2 SCC fixture に頼る。
- `_reasons` の理由文字列は set の列挙順に依存し、`PYTHONHASHSEED` が変わると同じ判定でも文字列の順が変わりうる (旧からある性質。本 wave の sha256 一致は HASHSEED=0 固定で取った)。
- `orchestrator/verifier/dsg.py` の bytes が変わったので、54183270 以前の closure hash を持つ campaign lock は `contract-loader-drift` で再開できない。新しい lock が必要 (T-2191 と同じ)。
- P2 の記憶量微増 (P1 単独比 +4〜5%) は 17M txn で効くかを測っていない。

## 次の一手

- **P4 の再設計:** writer を持つ鍵だけに大域 id を振り、各 file の token 表を 1 度だけ照合し、writer の無い鍵は sentinel として子が「producer / versions に不在」と扱う。親の read 全走査を禁じる (今回の撤回理由)。
- **P5 は単独で再提案しない:** winner 再生 0.5 s の改善は 0.03 s 級。parse を再度触るなら A6 の多重 dup oracle テストを test-first の前提にする。
- **helper の直接テスト:** `_ordered_complete_edge_outcomes` へ重複 task_index・欠落・空集合を直接渡す単体テストと、edge-worker 失敗テストに子 PID marker (子で raise したことの証明)。
- **テスト名の整理:** `test_scc_dense_arrays_keep...` は P3 撤回後の実装とずれている (改名は Codex author)。
- **残る直列部** (set 挿入 + tuple 凍結 ≈ 5 s、SCC ≈ 3 s) は別 wave。SCC は dense 化が遅かった実測を前提に、登録 pass を持たない形だけを候補にする。

## 一次資料

- 本 dir: `measurements.md` (条件・全表)、`ruling-stage4.md` / `ruling-stage6.md` (裁定)、`mutation-spec-probe.json` / `mutation-spec-final.json` / 変異台帳、`unit3-rejected.patch`
- 前 wave: `output/insights/2026-09-02_t2191-verifier-parallel/README.md`
