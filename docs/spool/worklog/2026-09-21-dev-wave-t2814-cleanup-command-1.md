---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-t2814-cleanup-command
seq: 1
title: [T-2814] /cleanup-branches §2・§3 に F1034 の 2 命令 (未追跡 output/ の原本確認、退避 tar の -C 順と非 dir entry 数の検算) と同日 cleanup session の罠 (削除直前の非施錠再確認) を足し、Codex overlay と whole-file SHA pin を追随させた — 予算 6,204 は上げず D782 手順 1 段目で 6,201 bytes に収容 (余白 0 は既存 test と衝突)、[T-2601] は対象 2 本の不在を実測して閉鎖 (docs + pin 追随の Codex author 1 + fix 子 4 巡 (本文修正 3 回、最終巡は監査)、branch worktree-dev-wave-t2814-cleanup-command)
---

## 本文

- ユーザー依頼 (2026-09-21、dev-wave 引数の逐語は insight `verbatim/T-2814-origin.md`) の範囲で 1 wave。裁定 = D2044 項 17 (T-2601 の撤去対象)、D782 (予算収容の手順の委任)、
  F1034 恒久対応 (command 反映は T-2814 で別 wave)。一次資料は `output/insights/2026-09-21/t2814-cleanup-command/README.md` (brief・裁定・削減対応表・author・review・
  変異台帳・焦点走の逐語)。専用 handoff は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/HANDOFF.md` (repo 外)。
- 起点 local main `285477c0052819e272e390d798f6442658075866` (fresh worktree、開始 gate rc 0 00:45:42 JST)。段構成: 軽量版 (段 1 → 4 → 5 → 6 → 7 → 8 → 9、段 2・3 省略)。
- **段 1 の実測で依頼の前提を更新した:** (1) 「docs のみ」は成立しない — `tools/check_docs.py` が command 本文と SKILL.md を whole-file SHA-256 で pin し、
  `orchestrator/tests/test_check_docs.py` が本文の byte literal 全文と `len == 6_181` を pin する。追随は Codex author 1 本 (先例 T-2813 と同型、gate・検査の新設なし)。
  (2) SKILL.md は「写し」ではなく command 本文を不可分に適用する overlay。command の 2 命令は Codex にも効くので、overlay には Codex 固有の縮退 2 項だけ足した。
  (3) command 本文に「退避」の概念は無く、command 自身は status 空の worktree だけ撤去し dirty は §5 で引き渡す。F1034 は引き渡し script (repo 外) で起きたので、
  (b) は §3 に「§5 で引き渡す dirty 撤去 script も本節に従い、退避を撤去の前提にする」の形で書いた。
- **収容:** 旧 6,181 + 追加 (2 命令 + 非施錠の 1 句、約 430 bytes) を D782 手順 1 段目 (既存記述の削減) だけで 6,201/6,204 bytes に収めた (最長行 105 文字、上限 110)。
  落としたのは 11 件 (対応表は insight §2): 意味不変の縮約 10 件 (§0 末尾「削除は不可逆に近いので…」= §2 の見出しと高い条件が同義、§1「rebase/cherry-pick 後も ahead>0」、
  §3「(取り込み済み確認の上)」、§3 背景セッションの括弧書き、§4「cleanup 前の status を保存し」→「§1 の status と比べ」、§5 の push command 例と助詞 1 語、argument-hint の
  冗長語ほか) と、**手段指定の削除 1 件** (§3 ExitWorktree 文の「`git log` で確認」→「確認」。確認の義務と `action: keep` は保持、別手段の確認も許す — 段 6 レビュー nit)。
  上限は動かしていない。**予算ちょうど (余白 0) は不可**: `test_cleanup_command_leading_space_h2_is_rejected` が byte-neutral helper を使わず先頭に空白 1 byte を足すので、
  予算超過が 2 件目の違反になり期待件数 1 が崩れる (fix 子 2 巡目が実測して停止 → fix 3 で余白 3 へ)。SKILL.md は 2,646 → 3,060/3,100 (既存記述は削っていない)。
- **段 6 レビュー (read-only 1 本) は NO-GO** → 本文修正 3 回: (1) must-fix = §3 の検算文「list と entry 数が一致」が一次資料 §4「tar の非 dir entry 数が list 数を下回れば
  撤去せず」と受理集合が異なる (dir entry を数えると総数一致で不足を見逃し、逆に正常な退避を誤停止) → fix 1 で一次資料の条件へ訂正 (親の対応表 A2 の判定誤りを反証で採用)。
  (2) 稼働中だった cleanup session (00:20〜00:36 JST 完走) の final の罠「棚卸し後に lock 状態が変わる (実行中に /rulings session が submit-tree-pair を lock)」を
  §2 高い条件「削除直前に status 空と非施錠を再確認」として fix 2 で反映 (依頼の明示 scope。待ってはいない)。(3) fix 2 で予算ちょうどになり上記の test 衝突 → fix 3。
  pin 追随の Codex fix 子は 4 巡: 1 巡目 受理 (統合 A 47e1730b7)、2 巡目 (本文 6,204) は pin を変えた後の焦点走で上記 test 衝突を実測して指示どおり停止 (証拠は
  launcher 未受理、終端 7907abd8b は不採用)、3 巡目 (本文 6,201) は正しい差分を作ったが `test_check_docs.py` の非 NFC fixture 行を cat して証拠が未受理 (F728 再発、終端 d258b0597)、
  4 巡目 (行番号回避を明記) が同差分を監査して一致・変更 0 で受理 → 統合 C 6dae18be1。焦点再レビュー 1 本は GO (所見 1・2 closed、記録面 nit 2 = 巡数の区別・byte 算術 → 訂正)。
- **T-2601 の閉鎖:** 対象 `dev-wave-t1875-delta-min-gate` / `dev-wave-t2267-exec-site-class` は `git worktree list` (38 本)・`git branch --list`・`.git/worktrees/` admin・
  `.claude/worktrees/` と `dev-wave-jobs/` の directory・`docs/unreachable-object-ledger.md` のいずれにも無い (2026-09-21 00:4x JST 実測)。撤去の実行記録 (実行者・日時) は
  worklog 現行 + archive・`cleanup-20260920/inventory/`・git 履歴に無く不明。D2044 項 17 の残り (t2267 は施錠を尊重して残す) も対象不在で実行対象が無い。
- 変異 matrix (DW-M01〜M08、事前登録 5 = 等価 1 + pin 側 4、anchor = fix 統合 6dae18be1、独立 clone、runner `run_tests.py --force-dispatch test_check_docs.py`): probe で観測 node を
  集め final に登録 → **baseline PASSED 37.3 s、KILLED 4/4 (期待 node 完全一致: command sha 旧値 321 / skill sha 旧値 335 / fixture sha 旧値 1 / bytes assert 旧値 1)、等価 1 SURVIVED、
  MISMATCH 0**。docs 側 (+1 byte) は実 repo 正例 test が growth hold で skip のため harness に載せず、fix 子 2 巡目の「6,204 で合成 repo の check_docs が予算超過 + SHA 不一致」が同型の実測。
- 焦点走 19 file (変更 test 1 + `tools/check_docs.py` の consumer 14 + inventory 4 群): f1 (統合 C、untracked の spool fragment あり) は 3869 passed / 16 skipped / 1 failed
  (`test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes` = untracked fragment を検出、実装差分でなく親の手順起因)。f2 は記録 commit 後に
  同集合で再走 (結果は本エントリの追記で確定)。`python3 tools/check_docs.py` 違反なし、全史 provenance 監査 rc 0 (12188 件)。
  受入全走は記録 commit を含む最終 tip に land 前に 1 回投入し、受領証は job dir (`acceptance-receipt-*.json`) と land の記録が持つ。
- 言わないこと: 引き渡し script の退避検算を機械強制する gate・tool は足していない (scope 外、command 本文の命令のみ)。施錠の判定手段 (`git worktree list` の locked 表示 /
  admin dir の `locked` file) は本文に書いていない (余白なし、§2 安い条件と同じ流儀)。T-2601 対象の撤去者・日時は不明のまま (推測しない)。
- 工数: codex 7 本 (author 1・review 1・fix 4 (受理 2)・再レビュー 1、gpt-6-astra / medium)、計算ノード job = 焦点走 2 + 変異 probe 1 + final 1 + 受入 1。

## 次の一手差分

### 完了

- [T-2814] `/cleanup-branches` §2・§3 に (a) 未追跡 `output/` の原本確認 (insight「証拠の所在」節) と (b) 退避 tar の `-C` 順・非 dir entry 数検算を撤去の前提にする命令、
  §2 に同日 cleanup session の罠 (削除直前の非施錠再確認) を足し、`.agents/skills/cleanup-branches/SKILL.md` の overlay と `tools/check_docs.py` /
  `orchestrator/tests/test_check_docs.py` の whole-file SHA pin を追随させた。予算 6,204 は上げていない (6,201 bytes、余白 0 は既存 test と衝突)。
  remaining: none
  base: dab673869c1379c2b2a8f57260186450d775c294b7dbaeaa5fddefc3b194e7ca
- [T-2601] 撤去対象 `dev-wave-t1875-delta-min-gate` と施錠残置対象 `dev-wave-t2267-exec-site-class` はいずれも worktree list・branch・admin dir・directory・到達不能台帳に無く
  (2026-09-21 実測)、実行対象が無いので閉鎖する。撤去の実行者・日時の記録は見つからない (worklog・archive・cleanup-20260920 inventory・git 履歴に無し)。
  remaining: none
  base: 2aeff5a373625accc5bd5b1d62607a07783ccc0192303bd537808d12e01d8d9b

### 見送り追記

- [T-2041] 2026-09-21 に [T-2814] wave で F728 が 2 回再発 (Codex fix 子 2・3 巡目が `test_check_docs.py` を cat し未受理)。行番号名指しの回避で 4 巡目が通り、研究実走の blocker ではないので再訪条件に該当せず記録のみ。
