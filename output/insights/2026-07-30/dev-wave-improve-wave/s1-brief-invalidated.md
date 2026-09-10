# 無効化済み段 1 brief — Pegasus 高負荷処理の計算ノード強制

> 無効化理由: 段2中に `build_argv` の floor / ratified-freeze consumer 閉包を検出した。
> DW-O09/O10 の最遅読了段は段1前なので、この brief と段2 planner は採用しない。

- 確定済み裁定: Pegasus ではビルドとテストをログインノードで走らせず、計算ノードの割当 affinity
  全コアを使う。現行 runbook §7/§8 の 2026-07-27 裁定を最新ユーザー指示で置換する。
- 生死実験: request `874129.nqsv` は bnode114 / affinity 48 / Python 3.10.12 で全走を
  `-n 48` = 3891 passed / 19 skipped / 205.12s、`-n 32` = 同件数 / 206.94s と完遂し、
  stdout・stderr・NQSV 会計 footer が永続した。48 worker の優位は主張せず、指示準拠の既定とする。
- scope S1: hostname、PBS job identity、CPU affinity を一つの軽量 policy module で分類し、
  Pegasus login / Pegasus compute / other と既定並列度を返す。
- scope S2: `tools/run_tests.py` は非実行形を除き Pegasus login から計算ノードへ同期 dispatch し、
  compute 側だけ affinity 全数を使う。既存 preflight・task-run の実行は compute 側一回に保つ。
- scope S3: gen_S submitter は Python 3.10 gate、外部 network 非依存、永続 receipt、qstat 可視性、
  stdout/stderr、子 rc、会計痕跡、timeout / interrupt 時 qdel を fail-closed に扱う。
- scope S4: buildcache 2 経路と coverage 4 経路の build 並列度を policy 化し、Pegasus login で
  実 build に到達したら拒否する。other 環境の既定 `-j 16` は変えない。
- scope S5: Claude の既存 `guard_bash.py` に Pegasus login 上の直接 pytest / cmake build / make /
  ninja / ctest 拒否を追加し、qsub と正規 submitter は許可する。Codex hook 未配線は不変。
- scope S6: runbook §7/§8、新しい decision、phase / worklog、検査・変異・receipt を記録する。
- 不変条件: 非 Pegasus 環境の挙動、正しさ gate、trace 分離、cache key / contract / frozen manifest、
  proof chain、push 境界を変えない。submodule `d706650` は初期化済み。
- 不変条件: jobs は cache key / contract 入力に加えず、既存 binary SHA 検査を維持する。同一入力の
  build bytes が並列度で変わる事実を観測した場合は受入を止める。
- 既存被覆: runner の cap / argv / preflight / task-run、buildcache の subprocess seam、hook 判定核は
  個別テスト済みだが、site 3 区分・dispatch receipt・login 拒否・other 不変の境界テストは未実装。
- 成果物影響: 未実装では login node が 3900 件級 pytest / build の負荷を受け、task-run の実行場所も
  login のまま。実装後は Pegasus login の直接実行を新 gate が拒否し、計算ノード receipt が必要になる。
- (P1) 自動 dispatch は `run_tests.py` に限定し、任意 campaign/build call は login で拒否して
  呼出側を計算ノード job 内へ移す。汎用 remote execution 化は scope 外。
- (P2) 「最大並列」は affinity 全数とし、明示 `-n` / `jobs` の caller override は維持する。
- (P3) site 判定不能は other とし既存環境を壊さないが、Pegasus login と判定できた後の PBS 不整合は
  fail-closed とする。P1〜P3 は親の provisional 裁定であり段 3 の攻撃対象。
- 分割: U1 policy、U2 runner/submitter、U3 build paths、U4 guard を所有非重複で実装し、
  docs は親が担当する。ビルド・pytest・mutation・受入は全て Pegasus 計算ノードで行う。
