# 段 1 brief — [T-2851] 残り (2) 未知条件への転移の runner (Codex author、D95)

- 作成: 2026-09-23 20:51 JST、基準 local main = 620a6bb13 (worktree `.claude/worktrees/t2851-unseen-transfer-runner`、branch `worktree-t2851-unseen-transfer-runner`、開始 gate rc=0)

## 研究前進
VLDB 差分分析 P4 (未知条件への転移と再現) の主要表を出す測定 (T-2851 残り (3): 性能 2 cohort + 検証) の実行器と解析器を作る。
完了判定 = 事前登録 v1 §11 表の 7 行 (MOCC 参照の選定を除く) と TPC-C 版 §5 置換表の各行が、新 module の関数・CLI に 1 対 1 で対応し、
fixture test と学習条件 (錨) 側の最小走で動くこと。測定の発効 (残り (1)) と実施 (残り (3)) は本 wave に含まない。

## 確定済みのユーザー指示 (引数、逐語は `.claude` の command 引数)
- 新しい module に置く。`orchestrator/campaign/pipeline.py` と `orchestrator/calibrator/runner.py` は呼ぶだけで編集しない (T-2854 単位 5 が pipeline.py を編集中)。
- MOCC の参照・対象探索群・候補凍結は入力として受け取り、選定を先取りしない。
- 留保条件の値で生成・選択を動かさない (v1 §3 の不使用義務)。発効前なので計算ノードで留保 cell を実行しない (smoke 含む)。
- test は fixture と学習条件側の最小走に限る。規律 2 を緩めない (verifier の判定は不変)。
- 本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。

## 正本 (事前登録、本文は変えない)
- v1: `docs/unseen-condition-transfer-preregistration.md` §2.3 (26 cell)、§3.2〜3.3、§4、§5 (順序)、§6.1〜6.5、§7、§8、§9、§11。
- TPC-C 版: `docs/tpcc-unseen-condition-transfer-preregistration.md` §2.1・§2.3 (段ごと 12 cell)、§3.3、§4、§5 置換表、§6。
- D2223、D2228 (`docs/decisions.md`)。

## 実アンカー (呼ぶだけ・編集しない)
| 要素 | 既存 | 位置 |
|---|---|---|
| 1 走 | `run_once` (perf 省略可 `use_perf`) | `orchestrator/calibrator/runner.py` の `def run_once` |
| 単独性 | `composite_competing_probe` / `competing_bench_pids` | 同上 |
| trace 走 | `_run_trace` (YCSB binary のみ許可、`_TraceWitnessUnsupportedWorkload`) | `orchestrator/campaign/pipeline.py` の `def _run_trace` |
| 検証 workload | `performance_correctness_workload(PerfConfig)` | 同 `def performance_correctness_workload` |
| verifier | `python3 -m orchestrator.verifier` | `orchestrator/verifier/` |
| t 分位点 | `student_t_quantile` (scipy は未導入) | `orchestrator/campaign/b10_backoff_static_tail_formal.py` |
| 先例 | T-2849 比較基盤 (1 走記録・集計の形) | `orchestrator/campaign/t2849_comparison_harness.py` |

## 親の provisional 裁定 (攻撃対象)
- (P1) 置き場: 新 module `orchestrator/campaign/t2851_transfer_runner.py` (cell 展開・順序・候補対応・job 実行・cohort 2 判定・検証接続・欠測分類) と `orchestrator/campaign/t2851_transfer_analysis.py` (§6 の区間・分類・主要表・記述表、§9 の n_eff)。test は `orchestrator/tests/test_t2851_transfer_runner.py` と `..._analysis.py`。分割は所有素集合の 2 単位にできる。
- (P2) 候補の凍結記録は入力 JSON (全 (課題, 手法, 独立探索) → identity または「選択できず」、選択規則、R0〜R2 / R* の identity、MOCC / R* の 3 択、到達可能性) を受け、形の完全性だけ検査して identity で重複除去し、正規化 JSON と sha256 を出す。identity は不透明な文字列 (書式は発効束が決める)。選択・参照の選定はしない。
- (P3) 留保 cell の実行は、発効の決定の記録 (D 番号と候補凍結記録の sha256 を持つ JSON) を引数で受けたときだけ許し、無ければ錨 cell だけ走らせる。§3.3 の登録済み契約の接続であり、発効束の全項目の検証はしない (新しい gate を足さない)。
- (P4) 1 走 = `run_once` を 1 回 (`use_perf=False`、内部反復なし)。build は外で済ませ、identity → binary path + sha256 の対応を入力で受ける (runner は build しない)。
- (P5) cohort 2 の別日判定・hostname 比較は job 開始時に cohort 1 の記録から行い、同 hostname なら測定せず「再投入要」で終える。再投入の回数判定 (2 回まで、3 回目は測って「別割当て不成立」) は関数で返し、qsub 自体は呼び手 (既存の投入経路) に任せる。
- (P6) 検証の接続: YCSB は `_run_trace` + verifier を呼び、結果を certified / 失格 / 未確定に写す。TPC-C は現行の trace 経路が YCSB 以外を拒否するので、認定経路の着地 (T-2854/T-2855) まで常に「未確定 (認定経路なし)」を記録する。verifier の判定は変えない。
- (P7) 生死確認: 錨 cell (例 wh-base、Silo、R0 と R1 の 2 build) の 1 job を計算ノードで 1 回、検証 1 本を付けて走らせる (見込み 0.5 node 時間未満、D2212 項 4 の確認ライン未満)。

## 不変条件
- 事前登録 2 本の本文 bytes を変えない。既存の凍結物・台帳・verifier・pipeline.py・runner.py を変えない。
- 留保 cell の値は runner の cell 表 (事前登録からの転記) にだけ置き、生成・選択の経路 (loop・planner・coder・selector) から import しない。
- 性能は trace-disabled build だけ、検証は trace-enabled build で別 run (規律 1)。anomaly は候補ごとに失格 (規律 2)。

## 成果物の形
新 module 2 本 + test 2 本、insight `output/insights/2026-09-23/t2851-transfer-runner/README.md`、spool fragment (worklog / decisions)。

## 分割方針
段 2 plan 1 本 (read-only) → 段 3 相談 2 本 (正しさ境界・契約整合 / 過剰・削除) → 段 5 実装子 2 単位 (runner / analysis、所有 path 素集合) → 段 6 review 2 本 + fix。受入は計算ノード (受入全走)。
