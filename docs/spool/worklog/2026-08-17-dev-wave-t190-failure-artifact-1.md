---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t190-failure-artifact
seq: 1
title: F57 族の失敗時 receipt と stop reason を保存し、20 回以上「未確定」だった原因を次回から判定可能にした — 依頼が前提にした [T-553] は既に完了済みで、失われる実機序も pytest teardown ではなかった (コード + テスト、branch worktree-dev-wave-t190-failure-artifact、変異 matrix = baseline PASSED・14/14 KILLED・正例 1 SURVIVED・MISMATCH 0)
---

## 本文

- **依頼の前提 2 件を着手時の実測が覆した。両方とも段 1 brief で表に出し、段 4 で再裁定した。**
  - (i) 依頼は「[T-553] と [T-190] の F57 恒久対応」を対象としたが、**[T-553] は 2026-08-09 に
    実装済みで完了している** (archive worklog (352)、branch `worktree-dev-wave-t553-git-budget`)。
    [T-692] R1〜R3 は s8c 事前登録の `git cat-file` 15 秒固定 timeout を作業量比例予算へ変える
    裁定であって、launcher の失敗 artifact 保存の裁定ではない。現行 worklog の次の一手に
    [T-553] は無い。**生きているのは [T-190] のみ**と裁定して scope をそこへ絞った。
  - (ii) 台帳が言う「pytest tmp が終了時に失う」は**実機序として不正確**だった。`--basetemp` は
    どこにも設定されておらず、pytest は `/tmp/pytest-of-<user>/pytest-<N>/` を**最後の 3 セッション
    保持する**。login で走れば残る。**計算ノードでは `/tmp` が node-local で job 終了とともに
    消える**ため、受入全走の失敗 artifact だけが失われていた。退避先が共有 FS でなければ
    意味がないことがここで決まった。
- **親 brief の誤りが 2 件、段 3 の 2 レンズに独立に refute された** (`DW-G03` の独立 2 例が成立)。
  - 親は「既存診断は `limits`/`actuals` しか出さず attempt 個別値は出ない」と書いたが誤り。
    `_receipt_diagnostic` は既に `outcome` / `stop_reason` / attempt 個別値 / stream 抜粋を
    16 KiB 上限で印字していた。**純増の基線を書き直した。**
  - 親は段 0 で「環境変数は計算ノードへ届く」と記録したが誤り。`dispatch_compute.py` の
    `tests` task は `env_allowlist` が閉じた 6 変数の frozenset で濾す。
    → **環境変数による退避 root 上書きを本 wave から落とした** (黙って効かない knob は恒真面を増やす)。
- **親が段 3 の所見を 1 件 refute した。** レンズ B の「受入は 32 worker で 48 ではない」は誤りで、
  `site_policy.default_test_jobs` は Pegasus 計算ノードでは cap を無視して affinity 全数を返す。
  レンズ B は `_default_nproc` で読みを止めていた。
- **段 6 の敵対レビューが、本 wave の中核を壊す欠陥を 2 件見つけた。** どちらも親は見落としていた。
  - `termination_initiated_by_launcher` が `_terminate` 呼出しの**前**に `True` にされていた。
    process が既に消えていれば signal は 1 本も送られないので
    `initiated_by_launcher=true` かつ `signals_sent=[]` になる。
    **「外部 kill か launcher 自身か」を分けるという本 wave 最大の追加価値がそのまま偽になる**
    実装だった。送信済み signal から導出する property へ直した。
  - signal 観測のために `_worker_module.os` を **process-global に置換**していた。同一 interpreter で
    強制停止が並行すると他 run の sidecar へ誤帰属する。置換を廃して launcher 内へ局所化した。
  - ほかに M03 が恒真 (テスト自身が時刻を注入するため production の phase 配線が壊れても緑)、
    変異 3 件が同一 node へ縮約されて単一理由性を満たさない、走査が bounded でない
    (directory 未計数・copy 後の無制限 `rglob`)、判定点の実測値を捨てている、など計 11 件を採用した。
- **`codex_exit_code=-9` の曖昧さは、launcher が既に持っている情報だけで閉じられる。**
  {{F:launcher-stop-reason-unobserved}} と F285 は「外部 SIGKILL と識別不能」を
  原理的な限界として記録していたが、**launcher は自分が TERM/KILL を送ったかを知っている。**
  送信済み signal から導出すれば、少なくとも「launcher 自身の強制停止」と「それ以外」は分離できる。
  これは段 3 レンズ B の所見を親が採用して scope へ入れたもので、段 2 プランには無かった。
- **Codex 子は本 wave を通じて 1 件もテストを実走できなかった。** 段 5 で 2 回、段 6 fix で 3 回、
  いずれも `tools/run_tests.py --force-dispatch` が `qstat -Q preflight rc=1` (runner rc=16) で
  pytest 起動前に落ちた。親が確認した時点では `qstat -Q` は rc=0 で、基盤側の一時障害である。
  **実走の裏取りはすべて親が引き受けた。**
- **login ノードの bounded local は予算依存で落ちる。** 小さい file (予算 1.0 GB) は通るが、
  launcher テスト本体 (予算 1.94 GB) は
  `bounded scope の memory.max / memory.oom.group を走行中に attest できない` で
  dispatcher infrastructure failure になる。**launcher 系の実走と変異はすべて計算ノードが要る。**
- **機構は受入全走で即座に発火し、F57 の機序を初めて確定させた。** 本 wave の受入全走
  (request `914871`、bnode004、48 worker) で 3 件が落ち、**3 件すべての bundle が自動退避された**
  (receipt・sidecar・attempt stream 揃い、`critical_set_complete=true`)。
  読んだ結果、3 件は同一機序だった — retry の attempt 2 で preflight が attempt 1 の
  **3.6 倍前後 (1.04〜1.11 秒)** に膨らみ、fixture の evidence grace `1.0` 秒を食い切って
  `evidence_forced_stop` に至る。**wall は律速ではなく、3 件とも 3.0 秒予算に対し
  receipt 公開が 2.46〜2.65 秒**だった。詳細と逐語は F57 の 2026-08-17 エントリと
  `output/insights/2026-08-17_t190-launcher-failure-artifact/first-real-bundle/`。
  **F285 の「予算 3.0 秒の縁」仮説は走 A で観測された別の sub-mode であり、
  F57 族の唯一の機序ではないことが実測で分かった。**
  後続の fixture harden は wall ではなく evidence grace を対象にすべきである。
- **[T-190] と F57 は閉じない。** 機序は 1 つ確定したが、F285 の走 A / 走 B 型は未帰属のままで、
  「なぜ retry の preflight だけが 3.6 倍になるか」も未分離である。
  段 6 レビュー A も「計装だけで閉じるな」と独立に指摘しており、親はそれを採用した。
- 設計判断は {{D:launcher-diagnostics-sidecar}}、実装の失敗は
  {{F:launcher-stop-reason-unobserved}} に記録した。

## 次の一手差分

### 更新

- [T-190] **P2・計装のみ着地 (2026-08-17)、原因分離は未了**: launcher 側に受理集合を触らない
  独立 sidecar を入れ、失敗した launcher テストの `tmp_path` を共有 FS へ退避する機構を land した。
  記録される観測量は latch の全成立集合とその判定点の実測値、evidence 強制停止、
  `residual=None` の 4 出所、phase 別時刻、launcher 自身が送った signal の 5 種。
  **本 wave の受入全走で機構が即座に発火し、1 つ目の機序を確定させた** — retry 時の
  preflight 肥大が evidence grace `1.0` 秒を食い切る型で、wall は律速ではない (F57 の
  2026-08-17 エントリ)。**残るのは F285 の走 A / 走 B 型の帰属と、
  「なぜ retry の preflight だけが 3.6 倍になるか」の分離である。それまで本項も F57 も閉じない。**
  fixture harden は **wall ではなく evidence grace が対象**と判明したが、
  上記が詰まってから別 wave で起票する (D249 の順序)。
  base: b91ae7c8146dd81f601ce060a321e3c3c8e1d19b091e55a4a3eea2a3056bcad1

### 新規

- {{T:launcher-external-kill-evidence}} **P3・新規**: launcher 自身が送っていない `-9` について、
  外部 kill の原因 (cgroup `memory.events`、PBS job 状態、終了直前の資源情報) を run と結合して
  保存するか裁定する。本 wave は「launcher 起因か否か」までを分離し、その先は scope 外とした。
- {{T:worker-termination-instrumentation}} **P3・新規**: `tools/dev_waves/worker.py` の
  `_group_members` / `terminate_verified_group` は scan error・TERM・KILL・実残留を
  `True`/`False` へ縮約する。F285 走 C の完全な帰属にはここの計装が要るが、
  本 wave の所有 file の外だった。
- {{T:launcher-failure-bundle-reader}} **P3・新規**: 退避 bundle の run 単位 index は
  `index.jsonl` まで作ったが、列挙・読解の CLI は作っていない。
  親は初回の 3 bundle を 20 行程度の使い捨て script で読めたので急がないが、
  再発が常態化したら起票する。
- {{T:retry-preflight-inflation}} **P2・新規 (本 wave の実測から)**: retry の attempt 2 で
  preflight が attempt 1 の 3.6 倍 (0.29 秒 → 1.10 秒) に膨らむ原因を分離する。
  `_attempt_loop` 冒頭の codex executable 再 hash と hook 再検証の I/O が疑わしいが未確認。
  **これが F57 の evidence-grace 型の直接の原因**であり、
  fixture の evidence grace を上げる前にここを詰めるべきである (D249 の順序)。
  上げるだけだと「遅くなっても通る」方向に受理集合を広げることになる。
