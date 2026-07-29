# 段 4 裁定 + プラン v2 — [T-153](a-d) + [T-158]

裁定: 相談 A (21 件) / B (13 件) の所見はすべて real (refuted 0)。うち scope 外 4 群
(B4/A13 後段 = dev_waves 隔離 checkout・daemon 統合、A5/B12 後段 = task-run 台帳への
bypass field、A15 後段 = 総括と本文の意味整合検査、B8 の hooks/settings 配線) は実装せず
worklog へ backlog / 裁定パッケージ候補として記録する。残りは以下のプラン v2 へ全採用。

## 不変条件 (v2 — A1 で是正)

- 「縮小方向のみ」を撤回する。正: (i) 既存の正当な緑を赤にしない、(ii) 新規拒否は
  偽赤・偽緑源の fail-closed 化に限る、(iii) 修復 (自動 init・cwd 正規化) は受理拡大であり、
  過剰拒否・過剰受理の両方向へ正例/負例の変異を登録する。
- orchestrator 本体・freeze 成果物・output/・conftest.py・README allowlist に触れない。
- _is_full_suite() と task-run suite identity の意味は変更しない (A4/B2)。

## author A: tools/run_tests.py + 既存テスト追随

編集所有: tools/run_tests.py、orchestrator/tests/test_run_tests_preflight.py (新規)、
test_run_tests_task_run.py・test_run_tests_nproc.py (call-shape 追随のみ、A10/B10)。

1. **引数正規化 (T-153a、A7/A8/A9/B1):** main() 冒頭で argv を一度だけ正規化する。
   - 位置 token (先頭が `-` でなく、直前が値取り option でない) の path 部 (`::` 手前) が
     呼び手 cwd 相対で実在すれば絶対化する。option・option 値・`-k` 等は書き換えない。
   - path 値 option の閉集合 {--rootdir, --confcutdir, --basetemp, --junitxml, --log-file}
     の値 (= 形式と空白区切り形式の両方) も呼び手 cwd 基準で絶対化する (A8)。
   - 正規化後 argv を組立て・_is_target 判定・_suite_identity の全部に使う (A9: 相対/絶対の
     suite ID 分裂を正規化で解消。full-suite identity は不変)。
2. **cwd 強制 (T-153a):** subprocess.call 3 経路 (現 :377,:379,:441) すべてに cwd=_REPO。
3. **受入形述語 (T-153b、A4/B2):** 新設 `_is_acceptance_run(args)` — 正規化後の位置 target が
   空 (既定) または全て _DEFAULT_TARGET 配下、かつ _SELECT_FLAGS・`--`・`-o`/`-p`/
   `--override-ini` なし、_NO_EXECUTION_FLAGS なし。_is_full_suite とは独立。
4. **preflight 順序 (A21):** main() で _ensure_xdist() より前に preflight を実行する。
5. **未 stage 削除 gate (T-153b、A5/B12):** acceptance run のみ。git env 消毒
   (GIT_* を環境から除去した env で `git -C _REPO ls-files --deleted`、A6)。検出時は
   一覧 + `git add -A` 案内を stderr へ出し rc=3。bypass は
   `IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS` の exact "1" のみ、警告必須、
   `IZANAGI_TEST_TRIGGER=final` では bypass 不可 (fail-closed)。git 不在・git 失敗時は
   警告して続行 (gate は git が機能する環境の偽緑防止が目的)。
6. **submodule 実体検査 (T-158、A2/A3/B3/B5):** marker = `external/ccbench/CMakeLists.txt`
   の実在のみ (prefix 解析・再帰なし。nested shirakami は対象外。pin 一致は freeze テスト
   自身の責務)。_NO_EXECUTION_FLAGS があれば skip。marker 欠落時: acceptance run なら
   env 消毒付き `git submodule update --init -- external/ccbench` を試行し、再確認で
   なお欠落なら rc=4 + 案内 (fail-closed)。非 acceptance run は init を試みず警告のみで続行。
7. テスト: 新規 test_run_tests_preflight.py は self-runnable footer 必須 (README allowlist を
   編集しない)。既存 2 ファイルの fake/assert を cwd kwarg へ追随。preflight は repo path を
   引数に取る関数へ切り出し、tmp git repo (既存 _git ヘルパ流) で単体検証 + main() 配線は
   monkeypatch 注入で rc を検証 (A19: 変異が実入口で殺せる形)。

## author B: 新 checker 2 本 + テスト

編集所有: tools/check_wave_startup.py、tools/check_codex_output.py、
orchestrator/tests/test_check_wave_startup.py、test_check_codex_output.py (いずれも新規)。

1. **check_wave_startup.py (T-153c、A11/A12/A14/B6/B7):** 完全 passive (git 状態を一切変更
   しない。auto-init しない)。git 呼び出しは GIT_* 消毒 env。`--repo <path>` (既定 cwd の
   repo root)。モード: `--mode fresh` (既定) = (i) HEAD SHA == local `main` SHA、
   (ii) branch 上にいて branch 名 != main、(iii) rebase/merge 進行中でない
   (rebase-merge/rebase-apply/MERGE_HEAD 不在)、(iv) clean tree (porcelain 空)、
   (v) submodule marker 実在、(vi) `--expect-external-handoff` 指定時のみ worktree 内
   docs/handoff/ に README 以外が無いこと。`--mode resume` = (iii)(v)(+(vi)) のみ。
   全項目を検査してから rc 集約 (0 / 1)、各失敗に是正 1 行。qsub 有効性検査 (memory 第 3 点)
   は scope 外と --help に明記 (B7、機械化したふりをしない)。
2. **check_codex_output.py (T-153d、A15/A16/A17/A20/B9):** 引数 = 対象 file。
   `--min-bytes N` (既定 500、N<1 は引数エラー)、`--require-heading REGEX` (既定 `^## 総括`)。
   検査: (i) regular file (symlink/FIFO 拒否、lstat)、read 上限 10MB、(ii) raw byte 数 >=
   min-bytes、(iii) fenced code block (``` 系) を除去した本文の行頭で heading regex が
   match。違反理由を全列挙して rc=1。意味整合 (総括の件数 vs 本文) は scope 外と --help に
   明記 — 内容検収は親の行動規律のまま (F43 prose は削除しない)。
3. テスト: tmp git repo / tmp file で全 gate の負例 + 正例 (fresh 正常 worktree rc=0、
   正常成果物 rc=0、resume モードで HEAD 前進を拒否しない) を検証。self-runnable footer。
   conftest.py は編集しない。

## 配線 (親 docs、B8/A17、予算純減)

- DW-O01 へ「`-o` 成果物は採用前に `python3 tools/check_codex_output.py` で検収し rc≠0 は
  再投」を追記。DW-O20 へ「立ち上げ検査は `python3 tools/check_wave_startup.py` (背景 job は
  --expect-external-handoff) を実行し rc≠0 で停止」を追記。増分は O20 の F48 逸話と O11 の
  縮約で相殺し、4 冊合計を純減させる。O11 は「stage (`git add -A`) 後に再走」の規範を残す
  (B11: 義務は削らない)。skill-self-improvement.md は触らない (B13)。
- 本 wave 自身が段 5/6 の子成果物検収で check_codex_output.py を実運用する (発火実績)。

## 変異事前登録 (DW-M01、B-057 形。anchor は統合 commit 後に M07 で再検証)

負例 (gate 無効化 → 期待 kill test、KILL = rc/受理の期待方向変化):
- V1 main() の削除 gate 配線除去 → preflight 配線 test (注入失敗→rc≠0) が赤
- V2 main() の submodule gate 配線除去 → 同上 (marker 欠落注入→rc≠0) が赤
- V3/V4 cwd=_REPO を記録経路/非記録経路から各individually除去 → call-shape test が赤
- V5 位置 target 絶対化の除去 → 他 cwd からの相対 target 組立て test が赤
- V6 check_wave_startup の submodule 検査恒真化 → 負例 test が赤
- V7 同 clean-tree 検査恒真化 → 負例 test が赤
- V8 check_codex_output の min-bytes 恒真化 → 小断片 test が赤
- V9 同 heading 検査の fence 除去を外す → fence 内見出しのみ file の test が赤
正例 (過剰拒否方向、M01 の正例義務):
- P1 削除 gate の acceptance 判定恒真化 → targeted 実行が発火しないことの test が赤
- P2 submodule fail-closed を非 acceptance へ拡大 → 警告のみで続行する test が赤
- P3 heading regex 不能化 → 正常成果物 rc=0 test が赤
- P4 fresh 正常 worktree の HEAD 検査恒偽化 → rc=0 正例 test が赤
単一理由性: 各 gate は独立関数で同一入力を先行検査しない構成とする (実装後に確認、F28)。
