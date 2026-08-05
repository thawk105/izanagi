---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t476-flock-race-flake
seq: 1
title: [T-476] main を断続的に赤くしていた flock 競合窓テストを決定的に直した — 空読みを実測で特定し、待ちを時計から事象通知へ置換 (コード + docs、branch worktree-dev-wave-t476-flock-race-flake)
---

## 本文

- **機序を実測で特定した。想定していた timeout 超過ではなかった。** 子は probe 結果を
  `Path(probe).write_text('blocked')` で publish していたが、これは「生成 → 内容書込」の 2 段で
  原子的でない。親は `probe_b.exists()` で待つため、**生成直後・内容書込前の空ファイル**を読み
  `probe_state == ""` になる。計装を一時的に入れて受入全走 (request 889220 =
  `1 failed / 5899 passed / 19 skipped`、赤は当該 nodeid のみ) を走らせ、
  `probe_wait_s=0.051 / probe_deadline_expired=false / probe_state="" / marker_b=true / rc=(0,19)`
  を記録した。deadline も kill も無関係な、publish の非原子性そのものだった。
  計装は `DW-O19` に従い実測後に復元した (`git diff HEAD` = 0 行)。
- **排除した仮説を残す。** (a) lock ファイルの inode 差し替え → `_locked()` が flock 取得後に
  inode 一致を再確認するため不成立。(b) 子の 30 秒 deadline 超過、(c) 親の 10 秒 probe deadline
  超過後の kill → いずれも実測値と矛盾。ただし (b)(c) は**構造としては残っていた**ため、
  修正では 3 つとも同時に消した。
- **負荷再現の失敗を記録する。** 同一 nodeid を 32 回並べて `-n 32` で走らせる案は成立しない —
  pytest が重複 nodeid を 1 item に畳む (request 889219 = 1 passed)。負荷再現は実負荷
  (受入全走) でしか作れなかった。
- **段 2 プランは採用しなかった。** codex の起草案は「一時 file へ書いて `os.replace`」+
  「厳密値待ち」+「deadline 超過を即 fail」だったが、敵対 2 レンズが
  (i) deadline を fail の根拠にすると**正しい実装が負荷で赤くなる** (受理集合を無裁定で狭める)、
  (ii) 子の 30 秒 self-timeout も同じ理由で正しい実装を赤にする、
  (iii) kill 後の無期限 `communicate()` が受入全走を丸ごと止めうる、
  (iv) 過去 2 赤 (888571 / 888600) の機序は標本 1 件からは一般化できない、を指摘した。
  親はいずれも real と裁定し、**probe file と release file を廃して待ちを pipe の事象通知へ
  置き換える** plan v2 を確定した。子は readiness と probe 結果を stdout へ 1 行で通知し、
  release は stdin の 1 byte / EOF で受け取る。詳細は {{D:flock-observation-by-event}}。
- **(iv) への回答**: 過去 2 赤の機序は確定していない。ただし plan v2 は (a)(b)(c) と空読みを
  すべて同時に除去するため、どれだったかを確定せずとも修理は成立する。
  worklog (194) の「機序 (確定)」という書き方は request 889220 についての確定に限定する。
- **主張の訂正 (レビュー B-3 を採用)**: 「正常経路から wall-clock 依存を除去した」は過大である。
  正しくは **「10 秒 / 30 秒の file-poll race を、事象通知 + 各段 `SUBPROCESS_TIMEOUT` (=120 秒、
  既存定数) の hang guard へ置換した」**。guard は真のハングでしか発火せず、正常経路の
  成否には関与しない。新しい timeout 定数は導入していない。
- **段 6 レビューが実装の穴を 3 つ見つけ、いずれも fix した (対応表は closed / closed / closed)。**
  (F-1) `removeprefix("PROBE ")` は prefix 不一致時に元文字列を返すため、素の `blocked` 行を
  正常値として受理していた → 完全一致検査へ。
  (F-2) `select` が readable を返した後の **buffered `readline()` が次の行を先読みし、
  その行が後続の `select` から見えなくなる**ため、変異適用時に 120 秒の循環待ちが成立しえた
  → `bufsize=0` + fd から 1 byte 読み + 単一 monotonic deadline へ。
  (F-3) 失敗時に回収済みの子 rc / stdout / stderr が診断へ付かない → 付くようにした。
- **変異事前登録を段 6 で訂正した。** 当初 M-A2 (production の `fcntl.flock(fd, LOCK_EX)` → `pass`)
  の kill 理由を「probe が available を観測する」と登録したが、これは誤り。flock を外すと
  同じテストの**前半 (thread 版)** の `_assert_flock_state(store.lock_path, blocked=True)` が
  先に落ち、process 節へ到達しない。M-A2 は node 単位の control としては有効だが、
  本 wave が書き換えた節の証拠にはならない。そこで節専用の正例 M-P1 (probe を `available` に固定)
  と M-P2 (`PROBE` 通知の write を削除) を追加した。
- **変異実測**: baseline PASSED、**M-A2 / M-P1 / M-P2 = いずれも KILLED**
  (`mutation-new-ledger.json`、failed node は 3 件とも当該 nodeid、hang なし)。
  `DW-M08` の新旧両走として、変更前 HEAD (f009da3) の clone に対しても M-A2 を走らせ
  **M-A2-old = KILLED** を得た。新旧で kill 結果が同一 = **検出力を増やしても減らしてもいない**。
- **手順違反 1 件 (自己申告)**: 変異 harness が同じ worktree へ mutant を注入している最中に
  受入全走 1 回目 (request 889355) を投入し、**mutant 入りの木を計測して偽の赤を得た**
  (traceback に `mutant: drop the PROBE notification` が写っている)。この赤は成果物の欠陥ではなく
  計測の無効である。harness の repo lock は**他の harness だけ**を排除し、素の受入全走は
  排除しない。恒久対応は {{F:mutation-run-vs-acceptance-run}}。
- **手順違反 2 件目 (自己申告、1 件目と同型)**: 上記フレークの起票を書くために、
  **受入全走 (request 889465) の実行中に本 fragment を編集し `git add` した。**
  結果、`test_check_docs.py::test_real_repo_clean` が中間状態を拾って赤くなり
  (`1 failed / 6038 passed`)、`git add` は real_repo 系テストが保持する `index.lock` とも衝突した。
  **受入全走はこの worktree に対して git 操作を行う**ため、走行中の編集・stage・commit は
  木を壊さなくても計測を無効にする。これは worklog (194) が同じ形で自己申告した違反の再発であり、
  本 wave では 1 件目 (変異注入中の全走投入) と合わせて 2 回踏んだ。恒久対応は
  {{F:mutation-run-vs-acceptance-run}} の memory を「計測中の worktree は読むだけ」まで広げた。
- **段 8 自己改善**: 候補 2 件を裁定した。(1) 上記の計測汚染 → failures へ起票し、恒久対応は
  memory `no-acceptance-run-during-mutation` に置いた。`DW-M05` への追記を試みたが
  `docs/dev-wave/` の byte 予算が上限まで残り 4 bytes で入らず、**上限は上げない方針**に従って
  memory を実体とした。`dispatch_compute` に harness 生存時の fail-closed 拒否を入れる案は
  防壁の新設なので実装せず裁定へ返す。(2) 「pytest が重複 nodeid を 1 item に畳むため、
  同一テストの多重指定では負荷再現にならない」は実害がなく、契約文書の byte を使う価値が
  小さいため契約変更なし (本エントリの記録に留める)。
- **受入全走 (有効分)**: request 889404 = `5900 passed / 19 skipped / 0 failed` (473.84s)、
  request 889423 = `5900 passed / 19 skipped / 0 failed` (487.08s)。
  いずれも waiver なし。**worklog (194) の既知赤 waiver W2 は本 land で失効する** (T-476 の land が
  失効条件であり、本 wave では一度も適用していない)。
- **実測回数の縮小を明記する。** レンズ B は「waiver なしの全走 6 回 (`-n 32` ×3 / `-n 48` ×3、
  2 ノード以上に分散)」を要求したが、(1) 修正は確率を下げるのではなく機序を構造的に消すもので
  あること、(2) gen_S が本日 38 件待ちで混雑していたことから **3 回**へ縮小した。
  強制 interleaving の latch テスト新設も見送った (`DW-G02`。M-P1 / M-P2 が
  「本物の available」「通知欠落」を直接赤にすることを実測で示せるため、latch の純増検出力は小さい)。
- **scope 外として記録だけする残存**: 同ファイル thread 版 (`:522-570`) の
  `Barrier.wait()` / `Event.wait(timeout=10)` / `join(timeout=10)`、`marker_a` / `marker_b` の
  存在待ち、production 側 `_git_text` の 30 秒 timeout は同じ wall-clock 感度を持つが、
  独立 2 例の再現がないため `DW-G03` に従い族一般化しない。
  cleanup 自身が timeout したときに再 kill しない経路 (nit) も残る。
- 子の工数: 段 2 が約 13 分、段 3 の 2 レンズが並列で約 9 分、段 5 実装が約 6 分、
  段 6 レビュー 2 本が並列で約 12 分、段 6 fix が約 5 分 (いずれも codex `gpt-5.6-sol`、
  段 2/3/6 レビューは effort=max、実装・fix は high)。実装子と fix 子はいずれも
  Pegasus scheduler へ到達できず (`qstat -Q` が sandbox で失敗、rc=16)、
  **正しく「緑を主張しない」と報告した**。テスト実測はすべて親が行った。

- **land 直前の merge 後全走で、無関係な赤を 1 件観測した。** local main 33 commit を
  merge commit で取り込んだ後の全走 (request 889456) が
  `1 failed / 6038 passed / 19 skipped` を返し、赤は
  `test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight@real_repo`
  ただ 1 件だった。`tools/ruleops.py inventory --repo <worktree>` が **exit 2** で落ちている。
  本 wave の差分は `orchestrator/tests/test_reflux_origin_ledger.py` と `docs/spool/` だけで
  `tools/ruleops.py` にも同テストにも到達しない。`DW-O18` に従い単独再走で再現性を実測したところ
  **90 passed / rc=0** で再現せず、親環境での `ruleops.py inventory` 単独実行も rc=0 だった。
  よって実装差分へ帰属させず、フレークとして {{T:ruleops-real-repo-inventory-flake}} を起票する。
  exit 2 は `RuleOpsError` / `OSError` / その他例外の総称で、テストが子の stderr を
  assertion message へ出さないため理由が残っていない (この診断欠落自体が起票内容に含まれる)。

## 次の一手差分

### 完了

- [T-476] flock 競合窓テストの非決定性を、待ちを時計から事象通知へ置き換えて解消した。
  変異 M-A2 / M-P1 / M-P2 / M-A2-old は全て KILLED、受入全走 2 回が waiver なしで
  5900 passed / 0 failed。既知赤 waiver W2 は本 land で失効する。
  remaining: none
  base: 20f74230f0214e972b7929d2204747b4285bbbf615f155fe22f0e6c0dcd61d11

### 新規

- {{T:ruleops-real-repo-inventory-flake}} **P2・新規 (受入全走を断続的に赤くする)**:
  `test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight@real_repo`
  が並列受入全走で `tools/ruleops.py inventory` の **exit 2** により赤くなった
  (request 889456)。同 file の単独走行は 90 passed、親環境での単独実行も rc=0 で再現しない。
  並行 wave が共有 `.git` を触っている最中の git 呼び出し失敗が疑われるが、**exit 2 が
  `RuleOpsError` / `OSError` / 汎用例外の総称で、テストが子の stderr を assertion message へ
  出さないため理由が残らない**。まず失敗時に子の stdout / stderr を診断へ出す
  (これが無いと次の再発でも原因が分からない)。そのうえで、共有 `.git` への並行アクセス下で
  inventory が fail-closed で落ちる条件を特定する。所有は ruleops 系
