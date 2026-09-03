---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-03
wave: dev-wave-t2103-producer-auth-layer
seq: 1
---

## 新規

### {{F:submodule-init-rc-contradicts-state}}. submodule 初期化ツールの rc=1 が実際の展開状態と食い違う [手順漏れ]

- 事象: `tools/dev_wave_submodule_init.py --worktree <ABS>` が 3 つの worktree
  (wave / author / fix) すべてで `ERROR: runtime-io-failure: detail={'label': 'submodule',
  'kind': 'update-no-fetch'}` を出し rc=1 で戻ったが、`external/ccbench/CMakeLists.txt` は
  実際には展開されており、`tools/check_wave_startup.py` は rc=0 で通った。
- 根本原因: 未特定。直接の `git submodule update --init --recursive --no-fetch` は
  wave worktree では無出力成功、author worktree では
  `fatal: transport 'file' not allowed` (git 2.34、`protocol.file.allow` 未設定) を返した。
  ツールの rc がどちらの経路の失敗を表しているか、報告からは区別できない。
- 恒久対応: 未実施。rc を実状態の判定に使わず、`check_wave_startup.py` の結果で判定する
  運用で回避した。ツール側の是正は本 wave の scope 外。
- 再発検知: 新規 worktree 作成のたびに rc と `external/ccbench/CMakeLists.txt` の実在が
  食い違うかを見る。食い違えば本 F へ再発として追記する。
- 危険: rc だけを見て「worktree が壊れた」と誤判定し、正常な worktree を作り直す無駄を招く。
  逆に rc=1 を無視する運用が定着すると、本物の初期化失敗を見逃す。
