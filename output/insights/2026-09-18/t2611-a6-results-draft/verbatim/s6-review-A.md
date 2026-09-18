## must-fix

**MF-1 — `high_variance` と `rounds` の出所が誤っている。**

根拠：[稿](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2611-a6-results-draft/docs/paper-story/results/2026-09-18-a6-certification-reject.md:353) §5.3 は、この2 field を raw JSON の `performance` に帰属させている。しかし durable authority の `rr95-stock.json` / `rr95-fixed2.json` に両 field は存在しない。実際の出所は `wal.jsonl` の9行目・19行目、`bench_done.payload` であり、両方とも `high_variance=false`、`rounds=1`。`unstable=false` と `rep_notes=[]` は raw にも存在する。

放置時の影響：値自体は正しいが、執筆者が指定された転記元から再照合できず、出所表が誤ったまま残る。

是正案（§5.3 の該当2行を置換）：

> | 生の5標本、`unstable` / `rep_notes`、各 cell の正しさ検査6件の verdict と commit witness、toolchain | raw JSON 2 file の `performance` / `correctness` / `build_evidence` |
> | `high_variance` / `rounds`、abort 率、`cv`、run argv、configure argv、perf の観測、時刻、`verify_done` の commits / aborts / anomalies / `proof_surfaces` | campaign WAL |

**MF-2 — A-2 の status と adopted genome を支える一次資料が §5 にない。**

根拠：稿238〜242行は、attempt `t2364-20260907b` の `observed-positive`、rr5 の10 µs、rr50 の5 µsを記載する。§5 の A-6 権威 bytes は rr95 のみ。D1993 は A-2 の attempt・束縛・正しさ・集計禁止を記すが、この status 値と2つの genome 値は記さない。D1645 の fixed10 / fixed5 は旧 attempt の記述であり、新 attempt の転記元にはならない。

横断稿にはこれらの値と A-2 権威 bytes の所在があるが、横断稿を証拠にして穴を埋めることはできない。**横断稿から転記したと断定する所見ではなく、本稿単独の出所が不足しているという所見である。**

放置時の影響：「出所は §5 の一次資料だけ」という宣言に反し、workload 間で異なる variant を測ったという説明を一次資料へ辿れない。

是正案：A-2 権威 bytes を直接照合したうえで、§5.3 に次の行を追加する。

> | §3.4 の A-2 attempt、outer status、adopted genome、判定の合成規則 | `output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json` の `attempt_id` / `status` / `cells[].genome` と、`policy_bytes_base64` を復号した `workloads` / `certification_composition` |

この A-2 ファイルは今回の必読射影に含まれないため、その現物照合を実施済みとは報告しない。

## should

なし。

## nit

**N-1 — WAL の行数内訳で、build の回数と event 行数が混在する。**

根拠：稿343行の「20行（build 2・verify_done 12・bench_done 2・commit 2）」に対し、現物を `stage` 別に数えた結果は以下だった。

| stage | 行数 |
|---|---:|
| `build_start` | 2 |
| `build_done` | 2 |
| `verify_done` | 12 |
| `bench_done` | 2 |
| `commit` | 2 |
| 合計 | 20 |

放置時の影響：20行という総数・build 2回・結果値・参照先は変わらないが、括弧内を行数として足すと18になる。DW-G05 に従い nit。

是正案：

> campaign WAL は20行 (`build_start` 2・`build_done` 2・`verify_done` 12・`bench_done` 2・`commit` 2) である。

**N-2 — 埋込み policy bytes を「canonical」と呼ぶのは紛らわしい。**

根拠：§1.3 の埋込み bytes は、producer の `_canonical_json` による bytes とは異なる。再計算結果：

- 埋込み bytes：`96ed47d0ea72811aa8ee8ced6740fa58c5896e026cb24fa4420a31919d12384a`
- 復号 JSON を `_canonical_json` で直列化：`500b329f28dccc8e4a2e7ff6d307d76788b252b45e18922d0db9a5c9cb7c49b8`

放置時の影響：掲載 hash と参照先は正しいため結果は変わらないが、再計算時に不要な直列化を誘発する。

是正案：

> 公開された `certification.json` の `policy_bytes_base64` を復号した policy file bytes の SHA-256 は……

## 一致 — 数値・実行記録

**A-6 の10標本から再計算した性能表は、丸めの桁まで全件一致した。**

| 項目 | stock | fixed2 |
|---|---:|---:|
| 標本数 | 5 | 5 |
| median | 10,088,796 | 9,505,248 |
| mean | 10,132,250.6 | 9,565,649.4 |
| 標本 sd | 133,406.6 | 112,221.9 |
| cv | 0.0132 | 0.0117 |
| 95% CI 半幅 | 165,646.2 | 139,341.9 |
| min | 10,029,940 | 9,488,225 |
| max | 10,365,808 | 9,753,031 |
| WAL の abort 率 | 0.1547 | 0.145 |

- 効果は `9505248 / 10088796 - 1 = -0.057841193339621455`、百分率の丸めは **−5.7841%**。権威値・稿・README 行が一致。
- 生標本10値は raw と WAL で順序も一致。母標準偏差 / median の **1.18% / 1.06%** も再計算で一致。
- 正しさ検査12件の commits / aborts、計24個の整数は表と一致。全件 `serializable`、`certified=true`、`anomalies=0`。`proof_surfaces` の4値も全件一致。
- performance 条件の trace 走行10件から計算した aborts / commits の範囲は **0.1771〜0.1792 / 0.1641〜0.1657**。
- WAL の両 `build_done` で `trace_cached=false`、`perf_cached=false`。両 bench の `rounds=1`、`rep_notes=[]` 等も一致。ただし転記元は MF-1 のとおり。
- 走行時 commit `ae8a767eb` の `runner.py` 1035〜1045行で、throughput の中央の値に最も近い rep の指標を選ぶ規則を確認。5標本では stock の第4標本、fixed2 の第5標本に対応する。`benchparse.abort_rate` の定義も一致。
- Created **01:28:55**、Started **01:29:06**、Ended **02:42:03 JST**、会計 field の Elapse **4382S** が一致。Elapse は時刻差から置き換えず、会計値として確認した。
- WAL の build 開始・commit 時刻4点、性能 run の引数、Release / sanitizer OFF / TRACE=0、FetchContent 4 path が一致。
- `use_perf=false`、preflight `unavailable`、`counter_status=not_required`、throughput `eligible`、LLC / IPC の `null` が一致。

**B-10 は6 record・計30標本から再計算した。**

| block | none median | constant-mu2 median | 効果 |
|---|---:|---:|---:|
| 1 | 10,311,699 | 9,630,186 | −6.609% |
| 2 | 10,179,288 | 9,631,925 | −5.377% |
| 3 | 10,158,776 | 9,618,673 | −5.317% |

abort 率6値も記載桁で一致。全6 record の `official_certification=false`、`correctness_certified=true`、host `bnode088`、request `977647.nqsv`、source `2a338449b…` が一致した。

## 一致 — SHA-256・policy・識別子

- **§5.1 の掲載 hash 7件**を現物 bytes から計算し一致。artifact manifest の6 file の束縛も全件一致。`COMPLETE.json` の certification / manifest / protocol の束縛も一致。
- **§5.2 の掲載 hash 11件**を現物から計算し一致。raw 2 file、WAL、lock、claim、admissions、raw manifest、reservation、compute-result、stdout、stderr を含む。
- **insight README 3本**の hash は全件一致。
- stdout **589,570 bytes**、stderr **547 bytes** が一致。
- admission 2件、source-evidence 2件、record ID 8件を確認。各 ID の stdout に対する `grep -F -c` はすべて **1**。末尾は **`2 committed / 0 aborted / 0 skipped (of 2)`**。
- perf / trace binary の hash 4値、build attempt ID 2値は certification・raw・WAL の記録間で一致。`tracked_diff_sha256` と adopted `src_token` は source-evidence と一致。**binary 本体の再ハッシュや source preimage の再生成を行ったという意味ではない。**
- attempt、study、schema、request、host、source commit、pin、campaign ID、genome、toolchain の記載値は照合した記録と一致。gcc / g++ は **11.4.0**、cmake は **3.22.1**。
- `a4_noise_floor_status=open`、`global_minimality_established=false`、`smallest_observed_sufficient_in_this_two_point_protocol=null` も一致。

**policy の比較は実関数で再計算し、主張と一致した。**

| 比較 | JSON の差 | protocol SHA-256 |
|---|---|---|
| 走行時 → 公開 | `tracked_destination` のみ | 同一 |
| 公開 → 現行 | `scheduler.nodes`: 1 → 5 のみ | 同一 |

3者とも以下になった。

`21427e71793ea744777d11bd90429ce2db1a8d3333ea9e2e0f227ecf377c25dc`

走行時 policy は commit `ae8a767eb` の bytes を取得し、SHA-256 が preregistration の `8969a7e4…` と一致することを確認した。現行 policy は `302b94796` の bytes と worktree の現物が一致した。

## 一致 — 限定・README・横断稿との境界

- 限定 (v) は T-2630 の到達を identity 層に限定し、A-6 で変異や認証結果の継承が起きたとは書いていない。
- **「A-6 の `src_token` を新実装で再計算して照合していない」**と明記している。D2108 の8/8一致を、A-6 token 自体の再照合へ拡張していない。
- `-dD` と環境 prefix 除去、再認証しない扱い、相対位置・push/pop_macro の残る限界は D2108 / D2120 項7と整合する。
- 反復 attempt を行わない判断と、その代償である attempt 間変動の未観測は T-2430 と一致。**−4.876% を attempt に数えない**扱いは D1870 と一致。
- README 196行は **4列**。稿の日付、測定日、request、2 cell、限定12件、効果、outer `reject`、別走行の correctness と一致。
- A-6 と B-10 の数値は今回指定された一次資料から再導出でき、横断稿を補助証拠にする必要はなかった。ただし A-2 に関する出所不足は MF-2 として残る。
- stdout は指定どおり ID の出現行数と終了行のみ確認した。「record 本文」の構造を独立に解析したとは扱っていない。

## 総括

**NO-GO。must-fix 2件、should 0件、nit 2件。**

A-6 の性能値・正しさ記録・掲載ファイル hash・protocol hash に不一致はなかった。修正が必要なのは、**`high_variance` / `rounds` の転記元**と、**A-2 の status・genome を支える一次資料の参照**である。これらは A-6 の `reject` や −5.7841% を変える指摘ではない。

ファイル変更・pytest 実行は行っていない。