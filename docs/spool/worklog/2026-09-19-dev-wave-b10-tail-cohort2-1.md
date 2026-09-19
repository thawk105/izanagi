---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-19
wave: dev-wave-b10-tail-cohort2
seq: 1
title: B-10 静的右 tail の第 2 cohort (独立再現) を事前登録追記の commit 後に投入し集団判定まで出した (docs + insight のみ、branch worktree-dev-wave-b10-tail-cohort2、変異 matrix = 免除 (実装面差分ゼロ))
---

## 本文

- ユーザー決定 (2026-09-19) 「第 2 cohort は独立再現。cohort 1 の verdict を主として保持し、cohort 2 の verdict は再現欄に併記。合成しない」を、
  結果を見る前に事前登録 `docs/b10-backoff-static-tail-preregistration.md` の末尾追記として commit `8737cacb4` (22:01 JST) に固定した。
  D2050 の充足。D2104 項 7 / D2120 項 16 が「走らせるなら D2050 を満たす別 wave」と書いた保留を、この 1 cohort についてユーザー決定で解いた ({{D:b10-tail-cohort2-independent-reproduction}})。
  `cad6f46d8` の 71,231 bytes は新 file の先頭部分として不変、§5 spec SHA `08f5849b…` も不変。§0 への挿入は consult の real 所見で取り消し、§0 が求める記載は追記の冒頭に置いた。
- consult 1 本 (read-only、9 所見、real 7 採用・refuted 2)。段 6 レビュー 1 本 (results 稿、read-only、must-fix 1・should 3・nit 1、全部 real で closed、数値の転記誤り 0)。実装子ゼロ。
- attempt 1 (22:11、job 10743/10744/10745) は 3 job とも 5 秒で `dependency_policy_contract` rc=2 (gflags source 不在)。原因は T-548 以後の job body が hydrate 済み staging を要求するのに新規 worktree に無かったこと。測定・campaign は作られていない。hydrate と鎖の残り 5 項目を login で実測してから attempt 2 (22:15、job 10752/10753/10754、group `b10-backoff-grid-20260919T131526Z-2235286`) を投入、3 job とも 14 分で完走。
- 本番 CLI の集団判定 (22:30) は `not-observed-in-any-workload`、18 区間すべて `declining`、`failures` 空、正しさ 120 記録 certified・anomaly 0、変動係数は全 cell で 0.6% 未満。cohort 1 と同じ verdict だが合成せず、稿 §2.6 の再現欄に両 cohort を区別して併記した。言い方は事前登録 §4.5 の固定表現のまま。`performance_certified: false` 不変。
- 素材: `docs/paper-story/results/2026-09-19-b10-static-tail-cohort2.md` (file 名は結果前に中立名で固定、限定 16 件)、README 表 1 行。fig8 への再現欄の材料は同稿 §2.6 / §4.1。一次資料は `output/insights/2026-09-19/b10-tail-cohort2/README.md` と verbatim。
- login node の `/tmp/.git` (他ユーザー) で `test_b10_backoff_grid_submit.py` が 17 件偽赤 → `--basetemp` を job dir へ移して 166 passed。非帰属。
- 専用 handoff は repo 外 job dir の `HANDOFF.md`。push は行わない。

## 次の一手差分

### 新規

- {{T:fig8-cohort2-reproduction-column}} **P2・新規**: fig8 `plot_b10_static_tail_formal.py` に第 2 cohort (group `b10-backoff-grid-20260919T131526Z-2235286`) の再現欄を足す。主結果 cohort 1 と区別して併記し合成しない (事前登録 2026-09-19 追記の項 2)。材料は `results/2026-09-19-b10-static-tail-cohort2.md` §2.6 / §4.1。実装面なので Codex author の別 wave。
- {{T:b10-submission-doc-hydrate-precondition}} **P3・新規**: `docs/b10-backoff-static-tail-submission.md` §1 に「hydrate 済み staging (T-548 以後の job body の前提) を投入元 checkout に用意する」を足す (docs のみ)。2026-09-19 の attempt 1 が 3 ノード 1 投入を無駄にした実測欠陥。投入 script 側での login 検査の追加は要求外なので起票しない。
