---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2698-official-floor-resubmit
seq: 1
title: [T-2698] T-2650 の config.h 供給修正を載せた main から official 床値 campaign を再投入し、cell build 段を越えて完走した — official 床値の実値と試行台帳側 gate の実値域を初めて取得した (docs のみ、branch worktree-dev-wave-t2698-official-floor-resubmit、変異 matrix = 実装面差分ゼロにつき免除)
---

## 本文

- ユーザー依頼は「T-2650 の Masstree `config.h` 供給修正 (main 着地済) を載せた着手直前の local main から
  official 床値 campaign を再投入し、cell build 段を越えるかを実機で確かめる。越えたら試行台帳側 gate の
  実値域を取得する。投入は main の `floor_campaign.sh` / `submit_floor.sh` を編集せずに使う。段 1 で
  稼働中の `dev-wave-t2386-floor-evac-order` と `dev-wave-t548-versioned-dep-procurement` の着地状態を
  確認し、退避・読取は着地済みの規則に従う。本題の再投入と記録だけ。仮想リスク向けの gate・検査・台帳・
  一般化の追加は scope 外」。実装面の差分はゼロで、軽量版 (`1→4→7→8→9`) の docs-only wave として進めた。
- **official 床値 campaign は cell build 段を越え、96 attempt すべてを計測して `driver_rc=0` で完走した**
  (request `1818.nqsv`、nonce `eb2759286496ac320307d0b3c3064e18`、source commit `8f17db598`、
  実行ノード `bnode004`、job Elapse 4769 秒、うち cell build 段 7 分 18 秒・計測 8 round 71 分 24 秒)。
  2026-09-09 の初回 official と T-1851 の 3 走行はいずれも計測段に届いていなかったので、
  **official 床値が計測段へ到達し完走したのはこれが初めて**である。停止していた走行との差は
  T-2650 の供給修正だけ (job script blob `9a7cd1f8…`、凍結 file、投入 script、policy は T-1851 走行時と
  差分ゼロを main 現物で実測)。T-2650 §9 が「本 wave では確認していない」と残した実機通過が閉じた。
- **official 床値の実値 (floor 案、未発効)**: rr20 = 35,817.945 (scale_ref 1,193,931.5)、
  rr80 = 46,065.78 (scale_ref 1,535,526.0)。**両 holdout とも `wired_min_rel_floor` 0.03 × stock 中央値に
  一致し、実測 noise 項 (`u_noise` 1.6〜2.9 万) が配線下限を下回るため、床は配線下限で決まっている。**
  12 cell すべて valid、cell CV 0.0023〜0.0124 (上限 0.15)、除外 0・retry 0・exec 失敗 0・machine anomaly 0。
  `eligible_for_refreeze: true` は producer 自己申告 (D488) であり、本 wave は床値を発効させていない。
- **試行台帳側 gate の実値域**を C3b の 4 分類で埋め直した。registry (`315b1eb8…/2c8cf9be…`、481 行 =
  freeze 1 + 96 attempt × 5 event) は planned 96 slot がすべて `terminal_status=observed`、
  `failure_reason` / `measurement_retry_reason` / `pre_observation_failure_reason` はすべて null、
  `attempt_ordinal` は 0 のみ、`probe_before/after` の 4 値 (rc 1 / stdout '' / stderr '' / competing false) を
  96 session で初めて観測した。C3b の「静的宣言 288 slot」は freeze event で実体化し、planned 96 が消費、
  retry 192 は未消費。「所在なし」の入力は間接証拠 (96 件の classification / terminal 成立) まで。
  競合分岐・retry 分岐・replay 分岐は依然として未発火 (未観測 ≠ 到達不能)。
- **台帳消費が初めて実体化した**: 共有 admission root の投入前 snapshot は T-1851 走行後と bytes 一致、
  走行後は ledger +12 (`admit`、cell ごと)、attempt-ledger +96 (`consume`)、measurement-generation
  claims +12 / consumed +96、registry namespace +1。`claims` / `consumed` と旧 fixture namespace は不変。
  計測枠 120 のうち 96 を消費し retry 24 は未使用。数量と bytes/hash の一致・差分に限定した主張。
- **段 1 の実測**: `dev-wave-t2386-floor-evac-order` (main 比 9 commit) と
  `dev-wave-t548-versioned-dep-procurement` (3 commit) は**いずれも未着地**だったため、退避・読取は main の
  既存規則 (T-1851 の手順 + runbook `phase3-8b-restart-runbook.md` W-2 の bundle 要件) に従った。
  D2060 以降の裁定と裁定 inbox に本 wave を止めるものは無く、2026-08-28 の「他者の待ち job 数を投入停止
  理由にしない」裁定が投入を支持した。
- **記録の作法**: run_dir の `result.json` / `result.md` / `journal.jsonl` / `manifest.json` は holdout の
  三軸 literal を含むため repo へ複製せず (F39 / D88 の clean scan 不変条件)、三軸 literal を含まない射影
  (`floors` / `attempt_registry` / `holdout_admission`) と registry・起動証明書・job-result・会計・
  checkpoint・snapshot を insight `evidence/` に置いた。`s8b_holdout_freeze search` は wave worktree では
  untracked の run_dir 原本 3 file だけを hit し (rc=1、陽性対照 181 件)、evidence 複製に hit なし。
  原本は runbook W-2 に従い run directory / binary store 12 本 / submission receipt / job staging / claim を
  manifest 付き bundle (108 file) として repo 外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2698-official-floor-resubmit/run-backup/`
  へ退避した。wave worktree は campaign 成果物 (untracked 67 件) で恒久的に dirty になるため、受入と land は
  同じ commit の clean な別木から行う。
- **観測 (診断であって欠陥の主張ではない)**: session 所要が seq 0 の 26.95 秒から seq 95 の 33.09 秒へ、
  round 間オーバーヘッドが 49 秒から 308 秒へ、いずれも attempt 数に線形に増えた (round 壁時計 377→700 秒)。
  96 attempt の 71 分は walltime 36000 秒に対して問題にならない。原因の特定は scope 外。
- **検査**: `check_wave_startup.py --mode fresh` rc=0、hydrate rc=0、`submit_floor.sh` rc=0、
  `dev_wave_wait.py compute` rc=0 (`done_evidence: true`)、投入直後の 3 点検査 (marker / qstat / 会計) 成立。
  記録 commit 後の検査結果は本エントリ末尾の「記録後検査」に書く。実測と統合記録は
  `output/insights/2026-09-16/t2698-official-floor-resubmit/README.md`。

## 次の一手差分

### 完了

- [T-2698] official 床値 campaign を再投入し cell build 段を越えて完走した (request `1818.nqsv`)。
  official 床値の実値 (rr20 35,817.945 / rr80 46,065.78、いずれも配線下限 0.03 × stock 中央値) と
  試行台帳側 gate の実値域 (registry 481 行、planned 96 slot すべて observed) を取得し、
  `output/insights/2026-09-16/t2698-official-floor-resubmit/README.md` に記録した。
  remaining: none
  base: 50fc239c400513e2fc5cc9a3f0562204d01a3c2ed135216794e205b9f3b02384

### 更新

- [T-1851] **P1・裁定済み (D1936 項14) → official 床値の実値を取得済 ([T-2698]、request `1818.nqsv`)**:
  official 床値 campaign が計測段へ到達して完走し、試行台帳側 gate の実値域が
  `output/insights/2026-09-16/t2698-official-floor-resubmit/README.md` §4 に揃った。床は両 holdout とも
  配線下限 0.03 × stock 中央値で決まった (実測 noise 項が下限を下回る)。result は floor 案であり未発効。
  C3c の残件は無い。次は 8b 再開 runbook の W-3 (freeze v2 候補 document の producer) と
  [T-2386] (退避と再配置の順序) で、本項ではなく {{T:floor-v2-candidate-from-official-result}} が持つ。
  base: e247865f947debe9f3c2eceea81444255bebe24c7b0b39d5f65554a3b3927d2a

### 新規

- {{T:floor-v2-candidate-from-official-result}} **P1・新規**: 完走した official 床値 result
  (run `20260916T111925Z-2c8cf9be`、`result.json` sha256 `b111831e…`、退避 bundle は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2698-official-floor-resubmit/run-backup/`) を入力に、
  8b 再開 runbook W-3 の freeze v2 候補 document の producer を実装し、人間承認の受領証発行まで
  進めるかを諮る。前提として [T-2386] (result の repo 相対読取りと repo 外退避の順序、稼働中 wave の
  着地待ち) の規則に従う。`eligible_for_refreeze` の producer 自己申告を発効根拠にしない (D488)。
  床が配線下限で決まっている事実 (実測 noise < 0.03 × scale_ref) を再凍結の判断材料として明示する。
