---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-b10-balanced-profile
seq: 1
---

## 新規

### {{F:silent-ignored-build-define}}. 要求した build define が黙って無視され、別条件の測定として記録される [計測汚染] [恒真ゲート]

- 事象: `orchestrator/campaign/backoff_profile.py` を Pegasus 計算ノードで走らせたところ、
  静的 backoff 量を要求した 6 点が、実際には stock の適応 backoff で測られる状態だった。
  perf report に対象 symbol が出ることを要求する gate が計測途中で止めたため顕在化した。
  gate が無ければ、6 点とも実質同条件の値が「機序 profile」として成果物になっていた。
- 根本原因: 2 つの合成である。
  (1) `BACKOFF_FIXED` / `BACKOFF_NOINLINE` は ccbench 本体に存在せず template patch が供給する。
  現 pin の `CMakeLists.txt` / `cmake/Options.cmake` を検索して不在を確認した
  (`BACK_OFF` と `NO_WAIT_LOCKING_IN_VALIDATION` は実在)。
  (2) **CMake は未定義の define を黙って無視する。** patch 適用は呼び手の責務だが、
  適用されたことを検査する層がどこにも無かった。driver は `patchharness` を呼んでいなかった。
- **独立再現 (別 producer・別 flag):** 並行 wave `dev-wave-b10-overthrottle-grid` が
  `backoff_extended_sweep.py` / `backoff_overthrottle.py` / **`backoff_sweep.py` (論文値を出した
  既存 driver)** の 3 本とも `patchharness` 参照 0 件であることを確認した。そのまま投入していれば
  29 の静的点が全部 stock 適応 backoff になっていた。同 wave の guard
  (`BACK_OFF=1` で backoff 指標が無ければ raise) はこの型を捕まえない — 量が無視されても
  適応 backoff は spin するので指標自体は出るためである。
- **歴史的成果物は無事**だが、それは driver の保証ではない。同 wave が既存 3 系列の WAL を
  全点集計し、いずれも 7 点の binary と throughput が 7/7 相異なり、ピーク位置が
  `orchestrator/tests/s1_expected_goldens.py` の `EXPECTED_BACKOFF`
  (balanced=5 / write-heavy=10 / read-heavy=2) と一致することを示した。
  つまり当時は patch が当たった状態で起動されていた。**同じ driver が起動のしかた次第で
  有効にも無効にもなる。「当てたか」は状態であって driver の性質ではない。**
- 恒久対応: `orchestrator/campaign/backoff_profile.py` は
  (1) 計測全体を `patchharness.applied()` の内側で行い、
  (2) **要求した define が実際に効いたことを build 側の実体で確かめる** — 計測を 1 点も
  始める前に 7 点を build し、binary hash が相異なることを検査して停止する fails-closed gate。
  無視されていれば静的量を持つ全点が同一 binary になる。診断ノブ側は完成 binary の ELF
  symbol table を stdlib で読んで実在を確かめる (backoff 有効点のみ。無参照の関数は emit
  されないため)。検査は `orchestrator/tests/test_backoff_profile_pegasus.py` が固定する。
- 再発検知: 上記 2 gate。**「patch を当てた」という事実や patch file の内容は正例にしない** —
  当て方の誤り (pin 不一致・部分適用・revert 漏れ) が再び黙って通るため。
  族全体への一般化 ({{T:build-define-positive-control-family}}) はユーザー裁定へ送る。

### {{F:fresh-worktree-missing-ignored-dir}}. 新規 worktree に無い ignored directory を前提にする検査が決定的に赤になる [テスト代表性]

- 事象: `test_s8b_floor_campaign.py::test_real_output_snapshot_excludes_git_ignored_real_output_changes`
  が新規 worktree で決定的に赤になった。主張は
  `assert "runs" in git_ignored_output_prefixes(ROOT)`。
- 根本原因: 判定は `git ls-files -o -i --exclude-standard --directory` の列挙に依存する。
  `.gitignore` に載っているだけでは足りず、**directory が実在しないと列挙されない**。
  当該 directory は campaign を実際に走らせた worktree にだけ生える。campaign を走らせない
  種類の wave の新規 worktree には永久に生えない。
- 影響: 差分では到達しえない赤であり、受入全走まで持ち越すと 1 走を捨てる。
  他 worktree を比較して、campaign 実行済みには実在し未実行には不在であることを確認した。
- 恒久対応: 当該 ignored directory を worktree に作る (tracked bytes は変わらず、
  作業ツリーは clean のまま)。前提が環境状態に依存することを本エントリで顕在化させる。
- 再発検知: 焦点走に本番 root を内容走査する検査を含めること。名前 grep では引けない
  (この検査の file 名には対象語が現れない)。`orchestrator/tests/` を
  `rglob` / `iterdir` / `os.walk` / `.glob` の呼出し近傍で機械的に洗うと 13 本ある。
