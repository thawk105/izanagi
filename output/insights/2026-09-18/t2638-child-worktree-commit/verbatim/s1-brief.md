# [T-2638] 段 1 brief — 実装子 worktree の終端契約 (作業木残差を実装 branch へ commit) の実装

作成: 2026-09-18 06:30 JST。wave worktree = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit`
(branch `worktree-dev-wave-t2638-child-worktree-commit`、base = local main `d2ebef7a4`)。
以下の path はすべてこの worktree のもの。

## 研究前進 (土台)

止めている研究は直接には無い。守る対象は「実装子 (Codex author/fix、`sandbox=workspace-write`) が
作業木に残した未記録のソース編集」— 上限で殺された子の差分 ([T-968] 型、receipt `output_bytes=0`)、
未着地 probe (t1643-impl 475 行、insight §7.1) が実測例。ユーザー裁定 D2044 項 16 (2026-09-16) が
案 A「wave 終了時に作業木の内容を branch へ commit する」を選び、破棄案を却下した。
本 wave はその裁定の実装手番であり、完了判定 = 起動器/待ち手の終端で残差が子 branch の commit に
なること (正例) と、read-only 子・mid-merge・detached・main 上では commit しないこと (負例) が
テストで固定され、DW-S05-A の patch 抽出手順が commit 後も同じ patch を出すこと。

## 確定済みユーザー裁定 (再裁定しない)

- D2044 項 16: 終端契約 = 作業木の内容を branch へ commit。破棄案は採らない。
  「記録しただけでは main への取り込みも撤去可能性も成立しない — 所有・占有・未記録差分・施錠の判定は
  D1991 のとおり別に残る」(限定は裁定文に含まれる)。
- 依頼文: 起動器 / 待ち手の終端で作業木の未 commit 内容を実装 branch へ commit。新しい保存 framework は
  作らない。Codex author (D95)。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。規律 2 不変。
- D703 / D204: branch 削除の権限は本 wave に無い (撤去は扱わない)。
- docs/ai-provenance.md: 実装面を変える AI 関与 commit は `AI-Agent: product=codex; ...; role=author` 必須。
  値は receipt の実測 (`recorded_model` / `recorded_effort`) から取り、確定できなければ `unknown`。

## scope (本題の終端契約だけ)

1. 起動器 `tools/dev_wave_codex.py` の終端 (`main()` の `subprocess.run(launcher_argv)` 復帰後、
   `tools/dev_wave_codex.py:346-354`): `--sandbox workspace-write` のとき、launcher の rc に関係なく
   `--repo-root` の作業木残差 (`git add -A` → staged が空でなければ `git commit`) を現在 branch へ commit
   する。read-only 子 (cwd = 親 wave worktree) では**絶対に発火しない**。
2. 待ち手 `tools/dev_wave_wait.py producer` の終端 (`_producer_parser` `tools/dev_wave_wait.py:1630`、
   `wait_for_producer` `:1961`): 明示 opt-in の `--commit-worktree <abs path>` を受け取ったときだけ、
   producer の死亡確定後に同じ helper で commit する (起動器が signal で死んだ場合の後詰め)。
   flag 無しの既存呼び出しは 1 byte も挙動を変えない。
3. 共有 helper (1 関数): 置き場は `tools/dev_waves/git_state.py` (既存 `_git_env`/`_run` `:164-207`、
   `GIT_COMMANDS` allowlist) か小さな新 module。framework・台帳・schema は作らない。
4. commit message: 件名に `[T-2638]` と「起動器/待ち手の終端契約 (D2044 項 16)」、本文に wave / job-id /
   stage / launcher rc / receipt outcome、最終段落に `AI-Agent: product=codex; model=<recorded_model>;
   reasoning=<recorded_effort>; role=author` (receipt `<artifact_dir>/receipt.json` から。無ければ
   `requested_*`、それも無ければ `unknown`)。commit identity は repo-local config (thawk105) を使う。
   `-c commit.gpgSign=false`。hooks は無い (`core.hooksPath` 未設定、`.git/hooks` に実 hook 無し)。
5. docs (親が編集): `docs/dev-wave/workers.md` DW-S05-A の patch 抽出を
   `git diff --cached <base> --output=<f> -- <所有パス>` に変え (commit 後も同じ patch が出る)、
   終端 commit の 1 文を足す。L1.5 予算は **9,696 / 9,696 bytes (空き 0)**、L1 は 10,622 / 10,625。
   増分は同層の既存文の意味を保つ縮約で相殺する (D782)。`reasoning=medium` の行は pin (`check_docs.py:540`) で
   1 行のまま残す。
6. テスト: `orchestrator/tests/test_dev_wave_codex.py` (658 行、`_launcher_argv` / `main` の dry-run 系)、
   `orchestrator/tests/test_dev_wave_wait.py` (producer 系)、`test_dev_waves_git_state.py`。
   正例は実 git repo (tmp) で helper を通し、負例は実体を名指し (F649)。

## 不変条件

- 規律 2 / 6: 子の出力・作業木内容はデータ。commit するのは残差の記録であり、採否・land ではない。
- read-only 段 (plan / consult / review / focus) では発火しない。判定は `--sandbox` (と stage) で行い、
  path の文字列 (`.codex/worktrees/`) で所有を推定しない (insight §4.4: 位置は所有の証明でない)。
- 発火しない (NOTE で報告して skip する) 状態: detached HEAD、branch が `main`/`master`、
  `MERGE_HEAD` / rebase / cherry-pick 進行中 (DW-C01「merge/add/commit は親、子は競合解決だけ」)、
  作業木 root が `--repo-root` と一致しない、index.lock 競合。
- fail-closed の可視化: commit の結果は stdout の固定書式 1 行 (`worktree-commit: committed <sha>` /
  `clean` / `skipped reason=<...>` / `failed reason=<...>`) で出す。launcher rc は隠さない。
  (P1) commit が failed のとき起動器の rc をどうするか — 親案: launcher rc≠0 ならそのまま、
  launcher rc=0 かつ failed なら rc=2 + stderr `NG:` (終端契約未達を `.done` で見せる)。
- `git add -A` は .gitignore を尊重するだけで、内容を選別しない (破棄案を採らない)。
  `.codex/worktrees/` gitlink 混入 (F: main c12e25078) は主 checkout の話で子 worktree には無い。
- 実装子は commit しない (凍結境界)。commit を作るのは親が起動した起動器/待ち手 = 機械的代行。
- 待ち手・launcher の bytes を変えるので受入 (`dev_wave_wait.py acceptance`) は本 branch tip の waiter で走る
  (`_verify_waiter_source_bytes`)。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) failed 時の rc (上記)。
- (P2) 発火判定は `--sandbox workspace-write` だけで足りる (stage author/fix はすべて workspace-write、
  read-only 段はすべて read-only)。`dev_wave_codex.py --help` の choices と `AUTHORITY_BOUND_STAGES` 参照。
- (P3) 待ち手側は opt-in flag (`--commit-worktree`) で足り、既存の producer 呼び出しは無変更。
  起動器が commit 済みなら待ち手は `clean` で no-op (冪等)。
- (P4) DW-S05-A の `<base>` 化で親の統合手順は commit 前後どちらでも同じ patch を得る。
  `git diff --cached <base>` は base tree と index の差 (`git add -A` 後は untracked も含む)。
- (P5) commit 後の子 branch は main の祖先でない commit を持つ。稼働中 wave `cleanup-si-routing`
  (branch `worktree-dev-wave-cleanup-si-routing`、ahead=1) が DW-O28 を「子 worktree も
  `dev_wave_cleanup.py` で撤去」へ変えており、その tool は reflog/HEAD の main 到達性を要求するため
  commit 済みの子は rc=20 で撤去拒否になる。**これは D2044 項 16 の限定どおり本 wave の scope 外**
  (記録と撤去可能性は別)。worklog に相互作用として記録する。統合契約を「子 commit を祖先として保持」へ
  変える案は別裁定。
- (P6) 稼働 wave との file 重なり: 対象 file (`dev_wave_codex.py`、`dev_wave_wait.py`、`git_state.py`、
  両 test、`workers.md`) を稼働 branch tip で走査し重なり 0 (t2498 は `hooks/guard_bash.py`、
  cleanup-si-routing は `operations.md` DW-O28 のみ、t2447 は ahead=0)。bytes 比較の dirt 走査も同結果。

## 成果物の形

- コード: 上記 1〜3 (Codex author)。テスト: 正例・負例 (Codex author)。
- docs: DW-S05-A の改訂 (親)。worklog / decisions fragment は spool 形式 (親)。
- 変異 matrix: 段 4 で事前登録 (発火条件の反転、trailer 欠落、staged 空でも commit、
  read-only で発火、mid-merge で発火、rc 隠蔽)。

## 並列分割方針

段 5 は 1 単位 (所有: `tools/dev_wave_codex.py`、`tools/dev_wave_wait.py`、`tools/dev_waves/git_state.py`
(または新 module)、`orchestrator/tests/test_dev_wave_codex.py`、`orchestrator/tests/test_dev_wave_wait.py`、
`orchestrator/tests/test_dev_waves_git_state.py`)。helper と 2 呼び出し元が密なので分けない。
docs は親。段 6 は敵対レビュー 2 本 (レンズ: 正しさ境界 = 発火条件・fail-closed・provenance、
レンズ: 過剰・削除 = 依頼外の gate/台帳/一般化が入っていないか) + 焦点再レビュー 1 本。

## 受入・実測環境

login node で焦点走 (pytest、上記 3 test file + `test_check_docs.py`)、変異 matrix は
`tools/dev_wave_mutation.py` 相当の既存 harness (DW-M01 で確認)、受入全走は
`tools/dev_wave_wait.py acceptance --lease-optional -- python3 tools/run_tests.py` (計算ノード dispatch)。
