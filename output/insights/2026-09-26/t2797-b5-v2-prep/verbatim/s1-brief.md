# 段 1 brief — [T-2797] B-5 v2 の投入準備 (2026-09-26、main 6c3913bc5、branch worktree-dev-wave-t2797-b5-v2-prep)

**研究前進:** 論文素材 §8 B-5 (LLM 固有性の条件付き対照、D1067) を、write-heavy・balanced の 2 workload・n = 12 (D2249 項 1 択 C) で
投入できる状態にする。完了判定 = (d) 原因と修正の land、v1 閉鎖の開示、(1a)(2) の実装と test 緑、v2 事前登録と発効束 (draft)、
実測単価による図 1 枚あたりの node 時間をユーザーへ提示して発効の確認を求める (D2212 項 4)。本走 job は投げない。

**確定裁定 (逐語は `verbatim/d2249-item1-and-time.md`):** D2249 項 1 (択 C、前提 (a)〜(d)) と追加項 (時間帯の block を外す、同時刻対照と系列の対づけは残す、既存 cohort は遡らない)。

**scope (実アンカー):**
- (d) 原因は親が確認済み (`verbatim/d-cause.md`)。修正 = `tools/b5_llm_round.py:404` の critic prompt `output_format_request` への 1 節追加 (+ test)。
- (a) v1 閉鎖 = `docs/b5-generator-contrast-preregistration.md` 末尾への閉鎖・開示節 (本文 bytes は書き換えず追記)、既知結果の閲覧台帳。docs-only (親)。
- (c1) 案 (1a) = `orchestrator/campaign/b5_generator_contrast.py` の `run_series` (:722) を「1 job = 1 実行単位」で再開可能にし、
  提案待ち `_handshake` (:672) を計算 node の外 (login の起動器) へ移す。起動器 = `tools/pegasus/b5_contrast_launch.py` の registered 経路 (:249〜) の v2 化。
  LLM 親の起動は v1 では repo 外 script (`dev-wave-t2797-b5-main-run/llm_parent_driver.py`) だった。
- (c2) 案 (2) = [T-2850] (b) の `--verify-performance-concurrent` (`p3_s4_loop.py:3488,3623`、`pipeline.py:1340` の 120 s) を B-5 の slot argv (`slot_argv` :507) に付ける。
  balanced は `p3_s4_loop.py:3623` が拒否する。balanced に使う前に計算 node で記憶量と静定待ちを**本番順序**で測る (F1052)。
- (b) v2 事前登録 (新 file) と発効束 (新 insight dir)。report `b5_generator_contrast_report.py` を v2 の判定規則 (2 workload・族 4、block 再現条件なし) に合わせる。

**不変条件:** 規律 2 (legacy 1 + 性能 trace 5 本、anomaly 即 reject、bench 前に検証完了) と trace 本数・verifier・判定規則。
規律 6: `_consume_k2_coder_output`・`.claude/agents/*.md`・critic 診断の節抽出 (射影) は bytes 不変。n = 12・B = 10・A = 30・N_eval = 5・session 定義は不変。
v1 の台帳・既存 cohort の判定規則は遡って変えない。計算は本 wave 合計 2 node 時間未満 (超えるならユーザー確認)。実装面は Codex author (D95)。

**provisional 裁定 (攻撃対象):**
- (P1) (d) の修正先は critic の入力 (prompt) で足り、検疫・coder 役割文書・射影・`.claude/agents/` は変えない。吸収状態と planner のフェンス書式は開示だけ。
- (P2) job の切り方は全 arm 共通で「job 1 = 系列開始 stock のみ、job 2〜11 = 評価 1 回ずつ、最終 job = score 5 session」。
  LLM の a = 1 は stock の current_perf を要するので、stock と評価 1 を同 job に置くと node 上で提案を待つことになる。v2 §5.4 を「stock は評価 1 の直前の別 job」に改める。
  提案が却下された原提案は job を起こさない (A だけ消費)。
- (P3) 429 (利用上限) は v2 §3.3 の「候補と独立な依存物の供給障害」とし、提案待ちに期限を置かず、解除後に同じ a を再開する (A も B も消費しない、欠測にしない)。
  その他の親の異常終了は同じ a の機械故障 retry (追加 2 回まで)。LLM 親の起動器 (429 の扱いを含む) は repo に入れる。
- (P4) 時間帯の block を外す: block 間 1 時間の規則と「各 block の median(d) > 0」(§7.3 (iii)) を削る。系列番号で 3 arm を対にし、対の 3 系列は同時に流す (同時刻対照)。
  block stock (fallback・CV 用) は workload ごとに 15 session を 3 job (5 session ずつ) で測り、配置は発効前に固定する。
- (P5) balanced の同時検査は、本番順序の実測で node 記憶量の最大が利用上限 (約 115 GiB) に余裕を持って収まり、静定が上限内に戻る場合だけ使う。
  上限は実測最大への倍率で決める (DW-O13)。収まらなければ balanced は直列のまま、その旨を v2 に書く。

**成果物:** code + test (Codex author)、`docs/b5-generator-contrast-preregistration-v2.md`、v1 の閉鎖節、`output/insights/2026-09-26/t2797-b5-v2-prep/` (d の原因、balanced 実測、
発効束 draft、node 時間の試算)、spool fragment (worklog / decisions / failures)。

**並列分割 (所有 path 素集合):** 単位 A = `tools/b5_llm_round.py` + その test。単位 B = `b5_generator_contrast.py`・`tools/pegasus/b5_contrast_launch.py`・新 LLM 親起動器 + test。
単位 C = `p3_s4_loop.py` の balanced 許可 + test (実測の後)。単位 D = `b5_generator_contrast_report.py` + test。docs は親。

**受入・実測環境:** Pegasus login (受入 `tools/dev_wave_wait.py acceptance`)、balanced の実測は計算 node 1〜3 job (所在 = worklog、機体固有は `docs/pegasus-runbook.md`)。
