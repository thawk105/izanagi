# 段 1 brief — [T-2866] + [T-2854] 残り (2): TPC-C の候補を campaign で build・評価する配線と、転移実行器の TPC-C 検証の段 1 認定経路への接続

wave: dev-wave-t2866-tpcc-campaign / worktree /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign / 基点 local main 339d7c188

## 研究前進 (1 行)
VLDB P4 (未知条件への転移、TPC-C 段 1) と TPC-C 段 1 の探索は、候補を production の build で作り、pipeline の正しさゲートと実行器の検証に通せることが前提。完了判定 = 計算ノードで錨 s1-H-base だけを使い、buildcache が tpcc_silo.exe (perf / trace) を作り、実行器の 1 job と検証 1 本、pipeline.evaluate の TPC-C 1 genome が走って、現 pin の v2 trace が既存 reason で拒否 (実行器では indeterminate) と記録されること。

## scope (本題だけ)
S1 buildcache: `build()` / `build_v2()` (共有 `_v2_commands`・`_build_v2_impl`) に workload (ycsb | tpcc) を通し、target・binary relpath・compiler input target を `<workload>_<protocol>.exe` にする。cache key / v2 identity は ycsb の preimage を bytes 不変に保ち、tpcc だけ workload を入れて衝突させない。
S2 pipeline.evaluate: workload を `_build_one` へ通し、TPC-C の perf bench (`-ycsb_tuple_num` を付けない、tpcc_silo.exe は ycsb.hh を含まず未定義 flag で落ちる) と、TPC-C の correctness workload (flag は caller が渡す、57:43 以外は既存 reason で拒否) を可能にする。`calibrator/runner.py` の measure_point 系の YCSB 固定は最小差分で外してよい (B-5 は発効 commit の固定 checkout で走る、D2222 項 1。下書き中の pipeline.py の hash は既に現行と不一致)。
S3 critic `orchestrator/critic/digest.py:1336-1337` の説明「YCSB allowlist 外」を、TPC-C の v2 reject と 57:43 以外の拒否も含む意味に直す (reason 文字列は不変)。
S4 実行器 `t2851_transfer_runner.verify_candidate` (現 :507-510 で tpcc は常に「認定経路なし」): 段 s1 の cell は `pipeline._run_trace` (57:43 受理、D2238 項 2) → verifier → v3 要求 (D2238 項 3 と同じ判定 = `existence_violation_details is None` なら拒否) へ接続する。cell.flags は int なので文字列化が要る (`_run_trace` は `"43"` と文字列比較)。s2 と、57:43 でない s1 の cell は indeterminate のまま (経路なし)。
S5 単独性: `_probe("tpcc")` (:342-354、composite ycsb probe + `pgrep -af tpcc_.*\.exe`) を実機で確認する (tpcc 実行中は False、無ければ True、driver 自身の argv の自己一致が無いこと)。欠陥が出た場合だけ局所修正。
S6 [T-156] (phase3.md) の発火条件をこの wave で再評価し記録する (docs、親)。

scope 外: pin 前進・D297 規則 v2 (別 wave が稼働中)、認定の本測定、留保 cell の走行 (発効まで 0 走)、s1 の非 57:43 と s2 の認定経路、TPC-C の探索設計、trace の取引種別検査、新しい gate・台帳・一般化、他の数十の `ycsb_.*\.exe` 単独性 probe 呼び出し元の一般化。

## 確定済みユーザー裁定・決定
D2238 (受理 57:43・v3 要求・新 reason を足さない)、D2241 (実行器)、TPC-C 事前登録 §3.3 (留保 cell は発効まで 0 走)・§6 (未確定は certified と数えない)、D2212 項 4 (1 タスク 2 node 時間以上はユーザー確認)、D95 (実装は Codex author)。

## 不変条件
- 規律 1: trace は compile 時除去のまま。perf / trace は別 build・別 run。TPC-C の perf build も TRACE=0。
- 規律 2: `_run_trace` の受理述語・v3 要求は緩めない。v2 の TPC-C trace を certified にしない。anomaly は即失格。
- YCSB の既存挙動は bytes 不変: cache key / v2 identity の ycsb preimage、ycsb の argv、既存 WAL・受領証の形。
- 留保 cell は生成・選択・smoke に入れない。生死確認は錨 s1-H-base (と必要なら s1-L-base) だけ。

## (P) 親の provisional 裁定・攻撃対象
- (P1) 「評価できる」= pipeline.evaluate で TPC-C 1 genome が build → bench → verify の各段を通り、判定が WAL に残る。探索 loop・critic の TPC-C 固有指標は含めない。
- (P2) workload の表現は既存 dataclass の field 追加ではなく既定値付き引数か別型にし、PerfConfig 等の同一性 hash (asdict 由来) を ycsb で変えない。hash に使われているかを段 2 で実測する。
- (P3) 実行器で v2 の TPC-C trace の結果は indeterminate (reason = D2238 項 3 と同じ語)。ただし verifier が anomaly / 非 serializable を返したら disqualified を優先する (厳しい側)。
- (P4) certified への到達性 (DW-O13) は、実 verifier と合成 v3 trace の正例 test で示す (現 pin では実機到達不能。T-2854 単位 5 の insight §4 が実 v3 trace の pipeline certified を示している)。
- (P5) 計算ノードの buildcache は system の gflags/glog を持たない (T-2851 insight §3 回 1)。production の Pegasus job が依存をどう渡すかを段 2 で実測し、生死確認の driver はそれに従う。

## 成果物
コード + test (Codex author)、repo 外の使い捨て driver (Codex author) による計算ノードの生死確認記録、insight `output/insights/2026-09-27/t2866-tpcc-campaign-wiring/README.md`、spool fragment (worklog / decisions / failures 必要時)。

## 分割方針
段 5 は所有 path 素集合で 3 単位: A = buildcache.py + test_buildcache*、B = pipeline.py + calibrator/runner.py + critic/digest.py + 各 test、C = t2851_transfer_runner.py + test_t2851_transfer_runner.py。B は A の引数契約 (段 4 plan v2 で固定) に依存。

## 受入・実測環境
Pegasus login (pegasus02) で編集・焦点走、受入は `tools/dev_wave_wait.py acceptance`。生死確認は計算ノード 1 job (generic dispatch、見積り < 1 node 時間、2 node 時間未満なので確認不要)。
