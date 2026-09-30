# 段 1 brief — [T-2884] 正しさ関門の記録 (CCBench trace 拡張 U1) と判定器 (U2)

- 作成: 2026-09-30 12:15 JST、wave `dev-wave-t2884-gate-verifier`、base main `4f412c67b`、開始 gate rc=0
- 依頼: `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_14.txt` (+ `common-4.txt`)。設計正本 `output/insights/2026-09-29/gen-opt-correctness-gate/README.md` §3.2〜§3.5・§5.4・§7、U0 実測 `output/insights/2026-09-29/gen-opt-gate-liveness/README.md`

## 研究前進
段 A・B で LLM の編集範囲を読み書きの経路へ広げる前提 (設計 §3.5 の 4)。今の判定器は「読みを読み集合に載せない」B1 を certified にする (U0 実測 212,921 取引の迂回を見逃し)。完了判定 = 正式な記録と判定器で B1 が D1 赤、修正なし stock が D2b 赤、修正ありが D1・D2 とも 0 件 (計算ノード実走) + fixture の B1〜B7 赤・N1〜N4 緑 + 判定器変異の KILL。

## scope (2 単位、所有を分ける)
- **U1 (CCBench、Codex author):** F `25898d00` から新 branch `izanagi-gate-witness-trace` (仮)。`include/trace.hh`・`include/ycsb.hh`・`cc/silo/transaction.cc` の `#if TRACE` の内側だけ。gitlink・`CCBENCH_FULL_SHA`・`patches/`・`.gitmodules` は動かさない。
- **U2 (判定器、Codex author):** `orchestrator/verifier/` (parse/model/core/report と必要なら新 module) + `orchestrator/tests/`。呼び出し元の変更は requirement 引数を通す最小限だけ (pipeline などの既定挙動を変えない)。
- 生死確認 (親、計算ノード): U1 tip (修正なし)・U1 tip + Silo 修正 patch・U1 tip + B1 の 3 build × 2 workload (W-rmw・W-blind、U0 と同じ flags)、判定器は本 wave の production CLI。加えて設計 §3.2 注記の「刻印あり/なし trace build の commit・abort の差」の記述的な 1 回 (F の trace build、同 flags)。
- scope 外: gitlink 前進、[T-2889] 変異 7 本 + 負例 4 本の本走、md_13 の軸、auditor (U7)、gen-opt driver 接続 (U5)。

## 確定済み裁定 (覆さない)
- D2305 項 1: 生成器対照は pin C 固定で走行中 (md_11)。項 5: Silo 修正 branch は md_12 が `#line` +3 commit を足す (本 wave は触らない)。
- 設計 §3.5: D2b は全 key で照合。stock に合わせて緩めない。修正前 stock の D2b 赤は正しい結果。
- 規律 7: 過去の判定を遡って certified にしない。再検証の発火条件は結果の前に決めて commit する。
- D14 (`#if TRACE`)、D16 (trace 計装は izanagi 枝、push は人間)、D297 (TRACE=0 同一性)、D442 (判定器 4 file は epoch の束縛対象)。

## 不変条件
- TRACE=0 の前処理出力が F と同一 (`__LINE__` を含む。追加した `#if TRACE` 区間の後ろに `#line` で戻すか、行数が動かない位置に置く)。性能 build に trace 記号なし。上流 CI 相当 (全体 build + clang-format 14 の全 213 file rc=0) を満たす。
- 照合の入力が欠ける・読めない・食い違う → certified にしない (indeterminate)。巡回があれば non-serializable を優先 (既存どおり)。
- 手順列・刻印の無い既存 trace (pin C の全 campaign) の判定は、要求しない呼び出しでは今と同一 (md_11 の本走を変えない)。

## 親の provisional 裁定 (攻撃対象)
- (P1) 行名と置き場は U0 を継承: `gate_<thid>.log` に `Q` (手順列)・`V` (据えた値の刻印)。`A` は使わない。書式は U0 §1.1 のまま。
- (P2) 刻印は `YCSB::id_` の 64 bit (`val_` は変えない)。書き手 `((thid+1)<<48)|seq`、初期 load は既存の `id_ = key id` なので genesis の期待刻印 = key hex の整数値。`id_` を load 後に読む経路が全 protocol に無いことを実装前に rg で確かめる。
- (P3) `run` (7 protocol 共用) の `Q` 出力は、protocol の commit 経路が txid を渡した thread だけで有効化 (Silo の writePhase だけが渡す)。他 protocol の trace build には gate file ができない。有効化後に txid の渡しが無い commit は txid `-` の `Q` を出し D1(c) で赤。
- (P4) 判定器の要求方針: gate file が在れば常に照合 (在るのに崩れていれば indeterminate)。呼び出し側が `require_gate_witness=True` (keyword、既定 False) を渡したときだけ、gate file の欠落と emitter 証拠面 (D5: `ycsb.hh` の `Q` emitter と Silo の `V` emitter が `#if TRACE` 内に在る) の不成立を indeterminate にする。既定 False は現行 campaign を変えないため。gen-opt の driver (U5) は True を渡す義務を負う。
- (P5) 意味の版: 判定器に版定数を置き (v1 = 本 wave 前、v2 = 本 wave)、判定結果に載せる。発火条件 (案): v1 の記録は再判定も昇格もしない。v2 で読み直すのは gate file を持つ trace だけ (現 repo の campaign には無い)。gen-opt の certified は v2 以上 + require=True を要する。
- (P6) D1/D2a/D2b の違反は integrity の新しい計数 (anomalies ではない)。D2a は他の取引から来た値の読み (key への最初の操作が R/M) を、R が指す版の `V` 刻印 (genesis なら key 整数) と照合。
- (P7) D442 の影響: 判定器 4 file の bytes 変更で既存 E1 lock は main 上で E1-stale になる。repo 内 lock は 32 本すべて v1・v2 は 0 本 (実測)。md_11 の本走は submit checkout で走るが、land 後の main から再開すると CERTIFIED_ACCEPTANCE で拒否されうる → land 時に md_11 へ通知する。

## 成果物
CCBench local branch (commit のみ、bundle で主 checkout の submodule へ非 force fetch)、判定器 + test、`output/insights/2026-09-30/gen-opt-gate-verifier/README.md` (+ 事前登録 `prereg.md` を計算前に commit)、spool worklog fragment ([T-2884] 完了、[T-2889] の前提と計算見積り)、必要なら decisions fragment (意味の版と発火条件)。

## 分割・環境
正しさ防壁に触るので全段 (段 2・3・6 review 2 本) を回す。段 5 は U1・U2 を別 Codex author 並列 (所有 = U1: CCBench 3 file、U2: verifier/tests)。書式は (P1) で先に固定し U2 は fixture で並行。受入・build・D297・CI 相当・生死確認は計算ノード (Pegasus gen_S、generic dispatch)、見積り合計 約 0.8 node 時間 (< 2)。

## DW-O09 閉包 (実測 `s1-pin-closure.log`)
- 判定器 file の変更前 sha256/blob を持つ tracked file: 歴史記録 (output/insights の identity・bundle・compare・prerun、mocc-g2-repro の receipt、`output/env/pegasus/silo_ladder_rung1/*.json`) と、test fixture `orchestrator/tests/fixtures/b10_backoff_shape_locks/{balanced,read-heavy,write-heavy}.campaign.lock` (report.py・__init__.py の hash)。歴史記録は再発行しない (規律 7)。fixture が現行 bytes と比べるかは段 2 で読む。
- path を持つ実装・test: `orchestrator/campaign/campaign_lock.py` (閉包 12 path)、`orchestrator/qualification/contract.py` (T126 code identity)、`test_campaign_lock_codec.py`・`test_artifact_admission.py`・`test_t126_pegasus_tools.py`・`test_t671_source_binding.py`・`test_p3_b4_producer_auth_experiment.py`・`test_silo_ladder_rung1_*`、`acceptance_duration_ledger.json`。閉包の path 集合は変えない (新 module を足すなら閉包へ足すかを段 2 で決める — 足さなければ D442 の「閉包外の dispatch 面」を増やす)。
