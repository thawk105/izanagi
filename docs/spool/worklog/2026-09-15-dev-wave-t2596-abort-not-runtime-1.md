---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-15
wave: dev-wave-t2596-abort-not-runtime
seq: 1
title: [T-2596] 非 certified 床値 campaign で CampaignAbort を即時停止へ戻した (コード + テスト、branch worktree-dev-wave-t2596-abort-not-runtime、変異 baseline PASSED・3/3 KILLED・期待 node 完全一致を実装 commit と最終 commit の 2 回)
---

## 本文

- ユーザー依頼は「非 certified の床値 campaign 経路で CampaignAbort が RuntimeError を継承して
  いるため測定側の except に捕まり、即時停止でなく継続してしまう問題を直す。停止の意味を回復する
  局所修正に限定する。規律 2 を緩めない。Codex author = D95。本題の修正だけ。仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外。codex と一致」。
- **飲まれていた停止の中身を brief 前に現物で確定した。** `_wrap_admission_aware_measure` が返す
  `measure_attempt` は 3 箇所で `CampaignAbort` を投げる — holdout admission の不在、
  **凍結 cell と測定呼び出し座標の不一致**、admission の拒否。いずれも凍結との束縛が破れたことを
  意味する。これが `launch_failure` に化けると、journal の試行行・retry 枠・terminal 診断が
  「起こっていない事象 (プロセス起動失敗)」を記録する。
- **段 3 の 2 レンズはどちらも局所修正を支持し、代わりに親の記述の誤りを 9 件出した。** 全部採用した。
  主なものは (a)「非 certified 経路の唯一の except」は限定不足で、正しくは「この measure 呼出しを
  包む except として唯一」、(b) `runner.py:963` は `open_measurement_point`、`:1184` が
  `measure_point` で親は両者を混同していた、(c)「凍結 bytes の pin は無い」は断言が強すぎ、
  正しくは「確認範囲で該当 pin 未発見」、(d) 受理集合は「certified と最終 inspection は不変、
  非 certified の実行継続条件だけが厳しくなる」が正確、(e) retry 枠は「既に開始した分は
  abort 後も消費済みのまま」。
- **(P2) の根拠を段 4 で差し替えた。** 親の当初の根拠「admission abort は常に測定前だから
  post-probe は不要」は、再送出が「測定後に投げられた abort」にも掛かるため足りないと段 3 が
  指摘した。採用した根拠は「post-probe (`strict_probe`) 自身が `CampaignAbort` を投げるため、
  先に走らせると元の停止理由が置き換わり `terminal/status=aborted` の reason が失われる」。
  結論 (即時送出) は変えていない。冒頭 33-34 行の β-7 の全称表現との不一致は解釈上の未解消点として
  記録し、docs は変更していない。
- **scope 外と裁定した real 所見 4 件**: 族一般化 (runner / launcher にも広い捕捉が残るが
  DW-G03 の独立 2 例に足りない)、注入 callback が親型を投げる経路、wrapper の 3 拒否条件それぞれの
  到達性、未特定の外部 consumer 全体の保証。一次資料は
  `output/insights/2026-09-15/t2596-abort-not-runtime/README.md` (段 2〜6 の全逐語 13 file)。
- **受入全走で私起因の赤を 1 型引き当てた。** `test_ccbench_spawn_sites.py` は spawn site を
  **行番号で pin** しており、2 行の追加で `<module>.main` 内の `run_campaign(` が 8659 から 8661 へ
  ずれて 4 件が赤になった (単独再走でも再現する決定的赤)。段 1 の凍結 pin 閉包で
  `s8b_floor_campaign` を参照する test を 30 件まで path 検索で絞ったのに **中身を読まなかった**
  のが漏れである。行番号という形の pin は path の hit だけでは見えない。fix 子が数値 2 箇所だけを
  更新し、焦点再レビューが修正前 bytes との比較で緩和の不在と、取りこぼした同種 pin が
  `orchestrator` / `tools` に無いことを独立に確認した。
- 同時に赤だった `test_t1259_qsub_env_delivery_probe.py` 2 件と
  `test_s8c_preregistration_predicates.py::test_repository_candidate_uses_real_s8c_budget_module`
  1 件は、fix 後の同一走行で緑になった (計 50 passed)。本 wave に帰属しない (F57 と同型)。
- **手順の実測 4 件。** (1) 受入の argv は末尾に `-- python3 tools/run_tests.py` が必須で、
  欠けると `stage=cli-usage rc=2` で即死する。`--help` は rc=2 で読めず、エラー本文も 1 行だけで、
  他 session の `ps` の argv を見る以外に解法が無かった。`--lease-dir` は共有
  `/work/1/SFC/tanab/dev-wave-jobs/land-lease` を使う。(2) 受入は untracked が残っていると
  `stage=prerun-clean rc=70` で止まる — insight を先に commit してから投げる。(3) `--log-file` と
  `--receipt-file` は create-only で、再投入では別 path にしないと
  `stage=acceptance-log-preflight rc=2` になる。(4) `EnterWorktree` tool は
  `Could not read the repository git config` で失敗し、手動 `git worktree add` と `path` 形で回復した。
- **待ち手の実測**: 背景 job の完了通知が実体より早く届く事象を 5 回観測した
  (`.done` も成果物も無いのに completed)。`tail --pid` も即戻りした。確実だったのは前景で走らせる
  `tools/dev_wave_wait.py producer` だけである。完了判定は毎回 `.done` と成果物で裏取りした。
- 工数: codex 子 8 本 (plan 1、consult 2、author 1、review 2、fix 1、focus 1)。
  いずれも gpt-6-astra・medium・attempt 1 回。

## 次の一手差分

### 完了

- [T-2596] 非 certified 床値 campaign の `CampaignAbort` を即時停止へ戻し、負例・正例と
  変異 3 件で gate の実効を両方向から示した。
  remaining: none
  base: 027da2a9fa170e040de96545130f7c6c8d877fd27000057b8b979e1d4cb1f112
