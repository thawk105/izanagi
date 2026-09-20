# 段 1 brief — wave 起動の固定費の実測と submodule 初期化短縮の可否 (2026-09-21 07:5x JST)

## 研究前進

土台。dev-wave 1 本 (平均 154 分、`output/insights/2026-09-21/dev-wave-wall-decomp`) の「起動→段 1」11.7 分 (impl) のうち、機械的な固定費 (worktree 作成・submodule 初期化・開始 gate) がいくらで、どこに集中しているかを秒単位で分離する。完了判定 = 直近 wave の一次資料 (startup-gate.log / HANDOFF.md / 現存 worktree の git 管理 file の mtime / 自 wave の実測) から内訳表が出て、依頼の条件「submodule 初期化が大半」の成否が決まること。進む研究は論文の実験 wave 全体の回転 (直接の主張・図表はない)。

## scope

- 実測: 直近 wave の startup-gate.log (16 本) と HANDOFF.md の起動行、現存 worktree 21 本の `commondir` / `index` / `modules/**/index` の mtime、自 wave の起動時刻列 (EnterWorktree 前後、submodule init、gate の wall)。
- 条件付き実装: 「submodule 初期化が固定費の大半」が成立する場合だけ、`git submodule update --reference` 等の既存 git 機構で初期化を短縮する局所修正 1 件を Codex author (D95) で実装する。成立しなければ実装せず、実測と効果見積りを insight に記録する。
- scope 外: gate・台帳・一般化の追加、worktree の登録・lock・開始 gate の受理条件・submodule pin 一致検査の変更、superproject の checkout 方式 (sparse 等) の変更。
- 「受入 fresh 木の +60 秒」は、受入が git の木を新たに作らない (wave 木で `tools/run_tests.py` を dispatch、`tools/dev_wave_wait.py` に clone / worktree add 無し) ため、T-2817 の受入 `pre` 61 秒 (pytest collection 側) と読む。git 機構の外なので本 wave では測るだけ。

## 確定済みユーザー裁定

- 規律 2 を緩めない。本題だけ。実装は条件成立時に 1 件、Codex author。alternates の参照先が消えると壊れる条件は runbook に 1 行 (実装した場合)。

## 不変条件

- worktree の登録・lock・開始 gate の受理条件・submodule pin 一致検査は変えない。
- docs-only の場合、実装面 (D95) の差分ゼロ → 変異 matrix 免除、受入全走は免除しない。

## 実測 (段 1 で確定した事実、出所つき)

1. 自 wave (07:35 JST、他 9 wave と同時起動): EnterWorktree 07:35:04→07:36:29 = 85 s、うち git の checkout (`commondir` 07:35:09 → `index` 07:36:14) = 65 s。submodule 再帰初期化 (`tools/dev_wave_submodule_init.py`) wall 7.46 s (user 2.83 / sys 1.59)。開始 gate wall 6.70 s。出所 `~/.claude/jobs/4a4b31b9/tmp/self-startup-timeline.txt`、`submodule-init.log`、`gate-time.txt`。
2. 現存 worktree 10 本 (07:32〜07:39 起動、`.git/worktrees/<name>/` の mtime、`wt_timeline.out`): superproject checkout (`commondir`→`index`) 18 / 33 / 39 / 51 / 65 / 75 / 75 / 82 / 90 / 96 s (中央値 70 s)。submodule 3 段 (`ccbench/config`→`googletest/index`) 4 / 5 / 6 / 6 / 8 / 8 / 9 / 9 / 12 / 21 s (中央値 8 s)。
3. 昨日の単独起動 (混雑なし): t2797 submit-tree `commondir` 21:53:38 → ccbench `config` 21:54:26 (checkout ≈ 45 s、log に「Updating files: 29592」)、submodule 3 段 21:54:26→21:54:33 = 7 s。mutation-source (`git clone --local --no-checkout` + checkout + submodule 再帰) pid 21:54:11 → done 21:55:19 = 68 s。
4. HANDOFF.md (分解像度) の EnterWorktree→gate rc 0: t2797 19:11→19:13:22、t2344 20:53→20:54:39 (ff-only 含む)、t2813 20:59→21:00:14、fig13 19:00→19:01:55、t2795 19:00→19:02:23、t2804 21:01 内、cleanup-backup submodule-init.log 19:46:49 → gate 19:47:27。いずれも 1〜2.5 分で、秒単位標本と整合。
5. tracked file 31,699 (`git ls-files`)、`output/` 28,589 (うち `output/insights` 24,420 = 77%)、`docs` 1,698、`orchestrator` 1,060。総 872 MB。昨日 21:53 の checkout は 29,592 file → 1 日で +2.1K。
6. 主 checkout の module store の pack は現存 worktree と hardlink 共有済み (`stat` nlink 155、同 inode)。object の複製は既に無い。submodule は 3 段入れ子 (ccbench 1,438 file / shirakami 1,036 / googletest)。
7. 受入は wave 木で `tools/run_tests.py` を dispatch (chain log / launcher / `dev_wave_wait.py` に clone・worktree add 無し)。「+60 秒」は T-2817 §1 の受入 `pre` 61.9 s (collection 12〜15 + modify 区間 45 + 起動数秒)。

## 親の provisional 裁定 (攻撃対象)

- (P1) submodule 初期化 (中央値 8 s、最悪 21 s) は固定費 (checkout 中央値 70 s + gate 7 s) の 1 割前後であり「大半」ではない → 依頼の条件不成立 → `--reference` 修正は実装しない。
- (P2) `--reference` / alternates の効果は同じ資料から ≤ 1〜2 s と見積もる: object は hardlink 共有済みで転送は無く、初期化 7 s の内訳は 3 段の clone process 起動 + ≈2,500 file の checkout。alternates は object 転送だけを省く機構で checkout を省かない。
- (P3) EnterWorktree 85 s のうち git checkout 65 s、残り 20 s は tool の前後処理 (branch 作成・lock・session 切替) で git 機構では縮まない。
- (P4) 固定費の本体は superproject 31.7K file (872 MB、`output/insights` 77%) の checkout。impl wave は木を 3〜6 本作る (wave 木、Codex unit 木 1〜3、mutation-source、submit-tree) ので 1 wave あたり 3〜9 分。混雑下 (10 本同時) で 1 本 96 s、F30 再発記録では 7 分。
- (P5) 「受入 fresh 木の +60 秒」は git 木の作成ではなく受入 `pre` (T-2817) → 本 wave の scope 外。

## DW-G05 成果物影響

certified 選択・レポート・台帳の値・受理集合・参照は変わらない (docs-only の insight + worklog fragment)。放置時の影響は dev-wave の壁時計のみ。

## 分割方針

軽量版 + 診断。段 2 省略。段 3 相談 1 本 (read-only codex、P1〜P5 を攻撃)。段 4 裁定。条件不成立なら段 5・6 の実装は無く、insight の独立 read-only レビュー 1 本 (段 6)。段 7 記録 (insight + worklog fragment)、段 9 land。

## 条件表 (段 1 直後の再評価)

- 08 (freeze / oracle gate / proof chain): 触らない → 不成立。
- 09 (凍結 bytes): 変えない → 不成立。
- 10: 09 不成立 → 不成立。
- 13 (gate 新設): 新設しない → 不成立。
