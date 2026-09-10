# 段 1 brief（再実行）— Pegasus 高負荷処理の計算ノード強制

- 確定済み裁定: Pegasus ではビルドとテストをログインノードで走らせず、計算ノードの割当 affinity
  全コアを使う。runbook §7/§8 の 2026-07-27 裁定を最新ユーザー指示で置換する。
- 生死実験: `874129.nqsv` は bnode114 / affinity 48 / Python 3.10.12 で全走を
  `-n 48` = 3891 passed / 19 skipped / 205.12s、`-n 32` = 同件数 / 206.94s と完遂し、
  stdout・stderr・会計 footer が永続した。48 worker の性能優位は主張しない。
- scope S1: hostname、PBS identity、CPU affinity を一つの軽量 policy module で分類し、
  Pegasus login / compute / other と既定並列度を返す。
- scope S2: `tools/run_tests.py` は非実行形を除き Pegasus login から計算ノードへ同期 dispatch し、
  compute 側だけ affinity 全数を使う。preflight・task-run は compute 側一回に保つ。
- scope S3: gen_S submitter は Python 3.10 gate、network 非依存、source bytes 束縛、永続 receipt、
  qstat 可視性、stdout/stderr、子 rc、会計痕跡、timeout / interrupt 時 qdel を fail-closed に扱う。
- scope S4: buildcache v1/v2 と coverage 4 経路の実 build を Pegasus login で拒否し、compute では
  affinity 全数、other では現行 `-j 16` とする。caller の明示 `jobs` は維持する。
- scope S5: Claude の既存 `guard_bash.py` に Pegasus login 上の直接 pytest / cmake build / make /
  ninja / ctest 拒否を追加し、qsub と正規 submitter は許可する。Codex hook 未配線は不変。
- scope S6: runbook §7/§8、新 decision、phase / worklog、検査・変異・receipt を記録する。
- O09 pin 閉包: 既存 `FROZEN_MANIFEST` 23件、protocol / selector / v1 freeze bytes は変更しない。
  `build_argv` の live consumer は floor manifest/result と ratified generation validator、独立 golden は
  floor / freeze tests、既存 env/campaign JSON は歴史記録である。
- O09 durable 状態: v2 active generation は存在せず、official floor の現行受理集合は空であるため
  再発行対象はない。将来発行する build provenance だけが実 argv の新しい `-j` を正直に記録する。
- O10 producer 出力: buildcache は binary と v2 `completion.json`、floor は `manifest.json` /
  `journal.jsonl` / `result.json` / `result.md` と launch certificate を生成する。jobs は cache key /
  contract / completion manifest に入らず、floor 側の表示・照合用 `build_argv` にだけ入る。
- 不変条件: frozen bytes、trace 分離、source digest、binary SHA、proof chain、既存 active 選択、
  非 Pegasus の挙動、push 境界を変えない。submodule `d706650` は初期化済み。
- 既存被覆: runner cap / argv / preflight / task-run、buildcache subprocess、hook 判定核はあるが、
  site 3区分・dispatch receipt・login 拒否・other 不変の境界テストは未実装。
- 成果物影響: 未実装では login node が pytest / build 負荷を受け task-run も login のまま。
  実装後は直接実行を拒否し、compute receipt と実 build argv が将来の provenance に残る。
- (P1) 自動 dispatch は `run_tests.py` に限定し、任意 campaign/build call は login で拒否する。
- (P2) 「最大並列」は affinity 全数。明示 `-n` / `jobs` は caller 裁定として優先する。
- (P3) site 判定不能は other とし、Pegasus と判定後の PBS 不整合は fail-closed とする。
- (P4) dirty tree dispatch は投入時 bytes を隔離 snapshot に固定できる場合だけ受理し、共有 worktree
  直接実行はしない。P1〜P4 は親の provisional 裁定であり段3の攻撃対象。
- 分割: U1 policy、U2 runner/submitter、U3 build paths、U4 guard を所有非重複で実装し、
  docs は親が担当する。ビルド・pytest・mutation・受入は全て Pegasus 計算ノードで行う。
