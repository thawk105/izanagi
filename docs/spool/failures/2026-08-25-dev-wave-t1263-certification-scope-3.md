---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1263-certification-scope
seq: 3
---

## 新規

### {{F:mutation-worktree-skips-submodule-init}}. 使い捨て変異 worktree が submodule を初期化せず baseline を赤にした [手順漏れ]

- 事象: (2026-08-25、変異 probe の起動時) `tools/mutation_worktree.py` が作った使い捨て
  worktree で baseline が `PARSE_ERROR` になり、production write の前で停止した。
  失敗本文は `submodule is not initialized: external/ccbench/third_party/shirakami` で、
  real repo を読む 3 node が error になっていた。`--resume` は baseline を再走せず
  前回の赤を引き継ぐため、初期化しないまま再試行しても同じ場所で止まる。
- 根本原因: wrapper は固定 commit の worktree を作るだけで、submodule の再帰初期化を行わない。
  `DW-C01` が要求する `tools/dev_wave_submodule_init.py` は wave worktree の作成時にだけ
  適用されており、変異 wrapper が作る worktree はその導線の外にある。実 repo を読む
  テストを変異対象に含む wave でだけ発火するため、合成 fixture だけの wave では表面化しない。
- 恒久対応: 未実施。回避策は、保持された container
  (`<scratch-root>/.izanagi-mutation-worktree/repo`) に対して
  `python3 tools/dev_wave_submodule_init.py --worktree <container>` を実行し、
  以後はその container へ `tools/mutation_harness.py --repo <container>` を直接当てること。
  `--resume` 経由では baseline の赤が更新されないため、`--out` を新しくして harness を
  直接起動する。本 wave はこの手順で baseline PASSED を得た。
- 再発検知: 変異対象の runner command が `REAL_REPO_SERIAL_NODES` の node を含むなら、
  wrapper 起動前に container の submodule 初期化が要る。baseline が
  `submodule is not initialized` を含む `PARSE_ERROR` で止まったらこの型である。

## 再発

### F273

- **再発: 2026-08-25** — 受入全走 attempt 2 (tested tip `cd0955c7`) で
  `test_codex_worker_launch.py` の 4 件 (`test_check_receipt_reads_v2/v3_parent_attempt_field_sets_without_upgrade`
  の 3 param と `test_sigterm_ignoring_child_is_killed`) が落ちた。前者の本文は
  子 process の `returncode=2` (`NG: receipt truth table が不正`)、後者は
  `child.pid was not registered before deadline; stderr=''` で、いずれも子の起動・応答が
  期限に間に合わなかった形である。attempt 1 では 4 件とも緑だった。
- **この再発は単独では終わらなかった。** 落ちた 4 worker (`gw21` / `gw24` / `gw33` / `gw34`) の
  launcher 失敗 dump が `output/runs/pytest-launcher-failures/0-945252.nqsv--bnode018/` へ
  78 file 書かれ、**同じ走行の中で F136 を誘発した** (下記)。

### F136

- **再発: 2026-08-25** — 受入全走 attempt 2 で `test_s8b_floor_campaign.py` の 12 件が
  同一 assertion で落ちた。いずれも `repo_before = _real_output_snapshot()` と
  test 末尾の再取得を比較する before/after 検査で、差分の実体は
  `('dir', 'runs/pytest-launcher-failures/0-945252.nqsv--bnode018')` を含む 119 entry の増加である。
  **汚染源は外部の並行 dispatch ではなく、同じ受入走行の launcher テスト自身の失敗 dump だった**
  (上記 F273 の再発)。F136 の既知形 (隣で別 command を走らせた) と違い、
  **受入全走 1 本の内部で完結する自己汚染**である点が新しい。
  親は dump が追跡外であることを `git ls-files` で確認してから除去し、受入を再投入した。

### F480

- **再発: 2026-08-25** — 受入全走 attempt 1 (tested tip `cd0955c7`) が
  `orchestrator/tests/test_pegasus_dispatch_compute.py::test_control_lock_allows_peer_after_pending_hold_is_durably_released`
  1 件だけで赤になった (1 failed / 15431 passed / 60 skipped)。破れたのは
  `assert not first.is_alive() and not second.is_alive()` で、直前の `first.join(10)` が
  10 秒で戻りきらなかったことによる。**同 node の単独走は 1 passed / 13.49 秒 / rc=0 で緑**であり
  再現しない。本 wave の差分 (A/B 装置とそのテスト、共有 test 基盤 2 file) から当該ファイルへの
  到達経路は無い。junit の記録では worker は `popen-gw30` で、48 並列下の thread 待ちである。
  F480 の「絶対 wall-clock を assert するテスト」族に、`Thread.join(<秒>)` の上界も入る。

### F494

- **再発: 2026-08-25** — 期待 node に real-repo 直列 node を含む変異本走が
  `期待 node が pytest collection に実在しない` で rc=2 停止した。先行 wave の回避策
  (`--deselect` で該当 node を外す) は、本 wave の kill 集合が当該 node に依存するため使えなかった。
  **runner argv へ `-n 0` を渡して分散を切ると、collection 側と `FAILED` 行側の node 表記が
  揃い、real-repo node を期待 node として登録できる。** 実測で baseline PASSED、
  8 変異中 7 KILLED を得た (うち 3 変異は real-repo node だけが kill する)。
  受入形では `--dist loadgroup` 以外が拒否されるが、変異の runner command は受入形ではない。
  恒久対応の代替ではなく、`--deselect` より射程の広い回避策として記録する。
