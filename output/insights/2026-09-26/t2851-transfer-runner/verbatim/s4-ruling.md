# 段 4 裁定 — [T-2851] 残り (2) 転移 runner (2026-09-23 21:10 JST、基準 main 620a6bb13、裁定 inbox の新着なし)

## 所見の裁定
| ID | 判定 | 採否 | 内容 |
|---|---|---|---|
| plan P2〜P7 修正 | real | 採用 | 下のプラン v2 に反映 |
| A1 既知別枠は protocol 依存 | real | 採用 | 既知別枠は (protocol, cell) = (silo, bal-rmw1) だけ。MOCC の bal-rmw1 は留保・主要族 |
| A2 学習条件の照合 | real | 採用 (最小) | 凍結記録の各探索群が学習 cell 名 (錨名) の集合を宣言し、runner は登録済み錨名の部分集合であること (TPC-C は同じ段の錨) だけを検査 |
| A3 参照 identity の束縛 | real (一部) | 採用 (最小) | 凍結記録の参照 identity は binary 対応表 (identity → 性能用・検証用 binary の path と sha256) に全て在ることを要求。build 内容の再審査はしない (B2) |
| A4 記述比較の区間 | real | 採用 | R0 比・参照どうし・silo bal-rmw1 は無補正 95% 区間 (t(0.975, n_eff−1)) で同じ 4 分類、「記述」と付す |
| A5 再検証・再投入の状態遷移 | real | 採用 | 理由別の試行記録: 同 hostname 棄却は 2 回まで (3 回目は測定し「別割当て不成立」)、単独性違反・job 失敗は丸ごと 1 回。未確定の再検証は別 hostname で 1 回。解析器は (段?, cohort, protocol, cell) ごとに採用 job を一意に決める (最後の有効 attempt、規則は下) |
| A6/B2 発効入力 | real | 採用 (最小) | 下の「解禁」 |
| A7 実効性 | real | 採用 | 親の錨実走で確認 (下の「生死確認」) |
| B1 凍結 schema の縮小 | real | 採用 | 独自 schema 版・逆対応キャッシュは作らない |
| B3 既存経路の再実装回避 | real | 採用 | 下の「呼ぶ既存関数」 |
| B4 P7 の費用断定 | real | 採用 | 所要は実測で書く |
| B5 境界 test | real | 採用 | 下の test 規則 |
| B6 単位間 interface | real | 採用 | 下の JSON 契約を正本とする |
| plan の `plan` CLI | — | 不採用 | `freeze` の出力に M と job 一覧を含めて代える |

## プラン v2

### 単位 A: `orchestrator/campaign/t2851_transfer_runner.py` + `orchestrator/tests/test_t2851_transfer_runner.py`
- **cell 表**: YCSB 26 cell (v1 §2.3)、TPC-C 段 s1・s2 各 12 cell (TPC-C 版 §2.1・§2.3)。flags は CCBench の実引数名。既知別枠は `known_separate(protocol, cell)`。錨と留保の別 (`held_out`)。留保の値はこの module 内の表だけに置く。
- **順序**: v1 §5 の Fisher–Yates (identity 辞書順 → i = K−1..1、j = int.from_bytes(SHA-256(鍵 + "|" + str(i)), "big") mod (i+1)、swap)。鍵 YCSB `t2851-order-v1|<cohort>|<protocol>|<cell>|<b>`、TPC-C `t2851-tpcc-order-v1|<段>|<cohort>|<protocol>|<cell>|<b>`。b は 1 始まりか 0 始まりかを登録文は書いていない → **b は 1..32** とし、その選択を module 冒頭の docstring に「登録文に明記なし、実装の選択」と書く (発効束で確認する項目)。
- **freeze**: 入力 = `workload`、(TPC-C) `stage`、`series` (全 (task, method, independent_search) ごとに protocol、anchor、`selected_identity` か `selection_failure` の排他)、`search_groups` (各 (task, method) の learning_cells と reachability)、`selection_rule`、`references` (protocol ごと: YCSB silo は R0/R1/R2 が錨ごと、MOCC と TPC-C は `mode` (a/b/c) と (a) の参照 identity・(b) の測る候補集合)、`binaries` (identity → perf_path/perf_sha256/trace_path/trace_sha256)。検査 = 系列キーの欠落・重複・排他、learning_cells ⊆ 登録錨、参照 identity と sel identity が binaries に在る。出力 = 正規化 JSON (sort_keys) と sha256、cell ごとの測る identity 集合 (重複除去、R0 を含む)、比較組の一覧 (主要 / 記述の別、same_identity 除外の記録)、族ごとの M。選択・参照選定はしない。
- **解禁**: 留保 cell の `run-job` / `verify` は `--activation <json>` を要し、その `decision_id` が非空・`freeze_sha256` が使う凍結記録の sha256 と一致・(TPC-C) `stage` が一致し `certification_path` が非空、のときだけ許す。欠ければ rc≠0 で測定前に拒否。錨 cell は不要。発効束の他項目は審査しない。**TPC-C の検証は現行 `_run_trace` が YCSB 以外を拒否するので常に「未確定 (認定経路なし)」を記録**。
- **run-job**: 1 job = (cohort, protocol, cell)、TPC-C は (段, cohort, protocol, cell)。開始時 hostname と単独性 (YCSB は `composite_competing_probe`、TPC-C は同 probe に加えて `tpcc_.*\.exe` の自ノード pgrep、probe の失敗は不成立)、R0 捨て走 1 回、b = 1..32 で順序どおり各 identity を `run_once(..., use_perf=False, rep_returncodes=...)` 1 回、終了時の単独性。tps は `metrics["throughput[tps]"]` だけ (commit 数からの代替を使わない)。TPC-C の取引別 commit / abort は同 process の stdout を注入 seam (`subprocess_runner`) で保持して parse、parse 不能は使えない走ではなく「取引別件数欠落」として記録 (tps は総 throughput で使う)。使えない走 = rc≠0・signal・timeout・例外・tps 欠落・0・非有限。cohort 2 は `--cohort1-record` で同じ (段?, protocol, cell) の cohort 1 hostname と比べ、同じなら測定せず `next_action=resubmit-same-host` で終える (試行回数は `--attempt-history` の入力から数え、3 回目は測定して `separate_allocation=false`)。24 時間判定は cohort 1 全 job の最後の終了時刻と cohort 2 の最初の job の開始を比べる関数を持ち、run-job の開始時に未達なら測定しない。qsub は呼び手。
- **verify**: (protocol, cell, R0 以外の identity) ごとに 1 本、trace-enabled binary、flags は性能と同じで extime 3。YCSB は `pipeline._run_trace` と、pipeline の verifier 経路・witness 検査に使われている既存 helper を**呼ぶ** (同等の判定を新規に書く場合は既存箇所の file:line を comment に書き、判定を緩めない)。3 値: certified (verifier 完走・serializable・anomaly 0・witness 条件成立) / 失格 (anomaly ≥ 1 または non-serializable) / 未確定 (その他全部)。未確定の再検証は別 hostname で 1 回、同じ hostname なら測らない。
- **CLI**: `freeze | run-job | verify` の 3 つ。出力は JSON を create-only で書く。

### 単位 B: `orchestrator/campaign/t2851_transfer_analysis.py` + `orchestrator/tests/test_t2851_transfer_analysis.py`
- 入力 = freeze 出力 + 全 job 記録 + 全 verify 記録。
- 採用 job: 各 (段?, cohort, protocol, cell) で、単独性・完走 (32 block 到達) が成立した最初の attempt を採用。§9 の再投入枠を超えた attempt と、不成立 attempt の値は記述だけ。採用 job が無ければ全組が主要族で判定不能。
- 推定 (§6.1): 同一 block の ln(tps_k/tps_r) の平均・標本 SD (n−1)。主要族の資格 = n_eff = 32 かつ採用 job 成立かつ (cohort 2 は) 別割当て成立かつ k・r とも失格でなく、当該 (候補, cell) の検証が未確定でないこと (v1 §8)。
- 同時区間: `student_t_quantile(1 − 0.025/M, 31)` (既存 `b10_backoff_static_tail_formal.student_t_quantile` を import)。分類は厳密不等号 (L > δ 優越、U < −δ 退行、−δ < L かつ U < δ 同等、他は判定不能)、δ = ln(1.03)。
- 記述: 非主要比較と資格外の組は無補正 95% (n_eff ≥ 2)、n_eff = 1 は値だけ、0 は算出不能。
- 主要結果 = 両 cohort 同分類 (判定不能どうしを除く)。不一致は「追試で不一致」。勝者交代 (§6.4)、転移差の Welch 95% 区間 (記述)、因子別・手法別の記述集約 (§6.5、TPC-C は置換表の読み)。
- 失格: 候補 k が 1 cell でも失格なら全 cell・両 cohort の主張から外す。参照失格はその参照との全比較を外す。M は減らさない。
- 出力: `primary_rows`、`descriptive_rows`、`known_separate_rows`、`winner_changes`、`factor_summary`、`method_summary`、`disqualified`、`m_by_family`。

### 呼ぶ既存関数 (編集しない)
`calibrator/runner.py`: `run_once`, `composite_competing_probe`。`campaign/pipeline.py`: `_run_trace` と verifier 経路の helper。`orchestrator.verifier`。`campaign/b10_backoff_static_tail_formal.py`: `student_t_quantile`。

### test 規則 (fixture のみ、計算ノード・build・binary 実行なし)
- 各数値規則に正例と負例: 順序 (手計算した K=3 の置換、鍵の 1 文字違いで変わる)、t 分位点 (M=1 で t(0.975,31)=2.0395、M=100 で 3.887 を既知値に)、4 分類の等号境界、n_eff 0/1/31/32、24 時間ちょうど (以上で可) と 1 秒不足、同 hostname の 1・2・3 回目、単独性違反・job 失敗の 1 回目と 2 回目、既知別枠の silo/mocc、失格の全 cell 除外、same_identity 除外と M、留保 cell の解禁の有無、TPC-C stdout の取引別行 (CCBench `common/result.cc` の出力形式から作った fixture)。
- 揮発値 (hostname・時刻・hash の実値) を期待値に焼き込まない。新 test file は自走 harness 条件 (`test_plain_runner_coverage.py`) を満たす。

### 規模上限
runner ≤ 900 行、analysis ≤ 550 行、test 2 本で ≤ 750 行。超過は所見が閉じても差し戻す。

### 生死確認 (段 6 後、親が計算ノードで実行、錨だけ)
- YCSB Silo `wh-base`、cohort 1、K = 2 (R0 = BACK_OFF=1 既定、R1 = B0-L-W0) の 1 job (32 block) と、R1 の検証 1 本。build は `buildcache.build` を呼ぶ使い捨て driver (Codex author が repo 内の一時 path に書き、親が repo 外へ退避して `dispatch_compute.py --task generic` で投げる)。
- TPC-C は build 経路が buildcache に無いので本 wave では実走しない (取引別 parser は fixture のみ、「未実走」と記録)。
- 所要は実測で書く。見込みは D2212 項 4 の確認ライン (2 node 時間) 未満。

## 変異の事前登録 (位置は実装後に一意 anchor へ確定、DW-M01)
| ID | 対象 | 変異 | 期待 |
|---|---|---|---|
| M1 | runner 順序 | `mod (i + 1)` → `mod i` 相当 | KILLED |
| M2 | runner 順序鍵 | YCSB 鍵の接頭辞 `t2851-order-v1` の版を変える | KILLED |
| M3 | runner 既知別枠 | protocol を見ず bal-rmw1 を既知別枠にする | KILLED |
| M4 | runner 解禁 | 留保 cell の activation 検査を素通しにする | KILLED |
| M5 | runner cohort 2 | 同 hostname の棄却上限 2 → 3 | KILLED |
| M6 | runner 24 時間 | 24 時間の閾値を 23 時間にする | KILLED |
| M7 | runner 検証 3 値 | 未確定を certified に写す | KILLED |
| M8 | analysis 分類 | `L > δ` → `L >= δ` | KILLED |
| M9 | analysis Bonferroni | `0.025 / M` → `0.025` | KILLED |
| M10 | analysis 資格 | n_eff == 32 → n_eff >= 24 | KILLED |
| M11 | analysis 失格 | 失格を当該 cell だけに限る | KILLED |
| M12 | analysis same_identity | 同 identity の組を比較に含める | KILLED |
