# [T-2665] 並列撤去の launcher を置き、子を親の process group で起動して親の停止で道連れにする

authority: none / default_effect: no-state-change (プロセス監査・逐語凍結。可変状態の正本は worklog 末尾と現行 phase doc)

- wave branch: `worktree-dev-wave-t2665-cleanup-removal-pgroup`
- 基準 commit: `b4631a92ee57227e9d1d13227896f723895bce35` (local main、段 4 直前に ff 取込。wave 開始時は `abc7085ae`)
- 実装 commit: `46a88693c2371c97eb4c95ae1da44e402a60516d` (Codex `role=author`、5 file、新規 tool 262 行 + 新規 test 296 行 + docs + pin 2 file)
- 起票: worklog archive entry 1526 ([T-2641] wave) の次の一手 [T-2665]。裁定: D2104 項 32 (第 20 回 /rulings 全件、2026-09-17)
- 設計判断: 本 wave の decisions fragment (slug `cleanup-removal-launcher-same-process-group`、D 番号は land の fold が付ける)
- job dir (prompt・log・patch・probe script・dogfood の原本): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2665-cleanup-removal-pgroup/`
  (session の scratch `/home/SFC/tanab/.claude/jobs/8d758a10/tmp/wave-t2665/` から複製)

## 何をしたか

`/cleanup-branches` §3 手順 3 の directory 撤去は「1 件 1 process・各長い timeout・path 相互非包含なら並列可」と
書くだけで launcher が無く、親が止まったとき子が残るか道連れかは起動の仕方次第で未定義だった (起票文のとおり)。
段 1 の現物同定で、引数が名指した `tools/dev_wave_cleanup.py` (段 9 の自己撤去専用) は `_remove_verified_tree` で
`shutil.rmtree` を同一 process 内で行い、子 process も並列も持たないと分かった。並列撤去は command の手動手順にしか
存在せず、Bash guard は `rm -rf <worktree>`、`rm -rf a & rm -rf b & wait`、`nohup setsid rm -rf <worktree> &` を
すべて許可する (`hooks/guard_bash.py` の `decide()`、site=None、`verbatim/parent-probe-guard.txt`)。裁定の
3 要素 (同 process group / 中断・不明を完了扱いしない / prune へ進まない) を prose だけでは検査できないので、
新規 `tools/cleanup_remove_dirs.py` を裁定の機構を固定する最小 launcher として置いた。

- 1 path = 1 子 `rm -rf -- <path>` を親と同じ process group で起動 (`start_new_session` / `preexec_fn` / `shell` /
  `killpg` 不使用)。起動直後に `os.getpgid(child) == os.getpgrp()` を実測し、不一致・取得失敗は unknown + 全体取消。
- launcher 自身が受けた TERM / INT / HUP を生存子へ転送 → 5 秒猶予 → SIGKILL → 1 秒 → 未回収は unknown。timeout は
  子ごとに測り、検出時点で取消印を付けてから同じ取消経路を通す。取消待ちの各周で全体 signal を読む。
- 判定 4 値 (removed / failed / interrupted / unknown)。全子 reap → 全 path を lstat で再確認 (ENOENT だけ absent) →
  TERM/INT/HUP を SIG_DFL へ戻す → cancel flag 最終読取 → JSONL (1 path 1 行 + summary) → flush。rc は 0 / 1 / 2 / 64 を
  1 箇所で決め、process の exit status が正で JSON の rc はそれを写す。
- prune・detach・branch 削除・再試行・任意 command・監視・`PR_SET_PDEATHSIG`・`--one-file-system` は無い。

§3 手順 3 は「全対象の 1・2・占有検査の後、dir 撤去は `python3 tools/cleanup_remove_dirs.py -- <絶対path>...` を前景
1 回 (setsid・nohup・& 禁止)。rc0 (全件 removed) 以外は停止。detach・branch 削除・prune は直列。rc0 後 …」へ
差し替えた。D782 の削減段階 (手順 1 の重複補足「(branch を解放)」19 bytes) で 6201 / 6204 bytes に収まり、上限は
上げていない。whole-file sha pin (`tools/check_docs.py` / `orchestrator/tests/test_check_docs.py`)、synthetic 本文、
予算 test (`6_201`、超過 fixture `"x" * 3`) を同じ commit で更新した。

## 保証範囲 (段 3・段 6 が独立に狭めた)

親 brief の完了判定 (b)「親 kill で道連れ」は広すぎた。同じ process group は signal の宛先を共有する条件であって、
親の死を子へ通知する機構ではない。保証するのは次の 2 つだけである。

- launcher 自身が TERM / INT / HUP を受けたとき、生存子へ同じ signal を転送し、有界に止める。
- process group 宛の signal (killpg、端末の SIGINT) は子へ直接届く。

launcher PID 単独への SIGKILL、上位 shell だけの kill、Bash tool の timeout / Claude session 終了時の配送契約、
SSH 切断が launcher に届かない構成は保証外 (docstring に明記、実測していない)。成功境界の後に届いた signal は
既定動作で launcher を終了させ exit status は非 0 (JSON は不完全になりうる) — 子は既に無いので孤児は出ない。

path 検査は検査時点の名前空間に依存する (検査後の symlink 置換・配下 mount は防がない)。所有・取込・占有の判定は
§1〜§3 が担い、launcher は代替 gate を足さない。launcher の入力表記制約 (絶対・正規形・途中 symlink なし・実在
directory・realpath 一致・相互非包含・cwd が対象外) は受理する表記を狭めるが、削除が成立する述語・閾値・評価順
(§1・§2・§3 冒頭 2 行・§4 以降) は byte 単位で不変 (段 6 レビュー B が照合)。

## 親の生死実験と dogfood (login node、repo 外)

- `probe_selfstop.py`: 自己停止 wrapper `rm` (`#!/bin/bash` / `kill -STOP $$` / `exec /bin/rm "$@"`) を PATH 先頭に
  置くと、子は 6 ms で `/proc/<pid>/stat` の状態 `T` に入り、TERM を送ると `ShdPnd` に bit が立ち、SIGCONT で
  exec 前に rc -15 で死んで sentinel が残る。正例では SIGCONT だけ送ると実 rm へ委譲されて対象が消える。
- `probe_signals.py`: bash / python の両 wrapper とも TERM / INT / HUP で -15 / -2 / -1 (signal 死)。
- `dogfood_interrupt.py` (fix 前後で同じ結果、`verbatim/parent-dogfood-interrupt-*.txt`): 4 万 file の実 rm 走行中に
  launcher へ TERM → launcher rc 2、path 行 `interrupted` / returncode -15、`cancel_signal: 15`、子の生存なし、
  対象は残存 (39,655〜39,966 entry)。
- CLI 正例: 2 dir → rc 0、両 path `removed`、子 pgid = 親 pgid。usage 負例: 入れ子 → rc 64、stdout 空。

## 段 3・段 6 の所見 (逐語は `verbatim/`)

- 段 3 レンズ A (正しさ境界): must-fix 5 (A1 保証範囲、A2 有界待機と共通取消経路、A3 成功境界、A4 ptrace 案の再開と転送の
  競合、A5 path 保証の限界)、nit 2。レンズ B (整合・実効性): must-fix 4 (B1 §3 の順序、B2 「親」の分離、B3 wrapper の
  許容条件、B4 `tools/README.md` の実行場所分類)、裁定パッケージ候補 2、nit 1。段 4 で全件 real・採用 (B4 は scope 外で
  記録、`s4-adjudication.md`)。plan の ptrace 同期案は不採用。
- 段 6 レビュー A: must-fix 2 (A1 timeout 検出と取消の間の rc 0 漏れ、A2 timeout 取消の猶予中に全体 signal を読まない)、
  nit 2。レビュー B: must-fix 1 (B-01 summary 確定後の signal で JSON rc 0 と process rc 2 が食い違う)、nit 2。全件
  real・採用 (`s6-fix-adjudication.md`)、fix 1 巡で 6 件 closed、焦点再レビュー GO、退行なし。
- 変異の帰属について両レビューが指摘した点: M-h (pgid 検査の恒真化) は単独では殺せない (通常の Popen は同じ pgid) ので
  両層 (M1 + M9) で登録し test 側の独立観測が殺す。M4 / M5 は判定関数直呼び node が killer で、CLI 経路を迂回する
  変異まで証明したとは書かない。

## 親の実走

- 段 5 直後 (計算ノード dispatch): 新規 test 単独 36 passed / 4.42 s。consumer + meta 7 file (`test_check_docs`、
  `test_branch_rescue_ledger`、`test_plain_runner_coverage`、`test_pytest_collection_config`、`test_login_headroom`、
  `test_pegasus_dispatch_compute`、`test_t338_submission_gate_unit5`) 1169 passed / 3 skipped (growth hold) / 108 s。
- fix 後: 新規 test + `test_plain_runner_coverage` + `test_pytest_collection_config` 115 passed / 99 s (login の
  bounded local が cap-oom で計算ノードへ自動 dispatch)。`tools/check_docs.py` 違反なし。provenance full 10,910 件・
  新規違反なし。
- author / fix 子は `run_tests.py` の dispatch preflight (`qstat -Q` rc 1) の一過性障害で pytest を起動できず
  「未実走」と申告した。実走はすべて親が行った。
- 受入全走: 記録 commit 後の tip へ `tools/dev_wave_wait.py acceptance` で投入する (結果は land の受領証と worklog 末尾)。本 README の凍結時点では未実施。

## 変異 matrix

独立 clone `/work/1/SFC/tanab/mutation-src-t2665` (`git clone --no-checkout` + local module store への submodule init、
HEAD = 実装 commit `46a88693c`) を source にした `tools/mutation_worktree.py` の使い捨て worktree (scratch
`/work/1/SFC/tanab/dev-wave-jobs/t2665-mutation-3` / `-4`) で `tools/mutation_harness.py --runner-mode dispatch
--detached`、runner は `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_cleanup_remove_dirs.py -q -rf`。
spec と台帳は本 dir の `mutation-spec-probe.json` (sha256 `3a0b5655…`) / `mutation-ledger-probe.json`、
`mutation-spec-final.json` (sha256 `c9e30cca…`) / `mutation-ledger-final.json`。wrapper receipt は両走とも
`child_rc 0`・`shared_snapshot_matches true`。

- probe 走 (全件 SURVIVED 登録、観測 node を集める): baseline PASSED、M0 SURVIVED、M1〜M10 は全件 MISMATCH (= 赤 node を
  観測)。観測 node を本走 spec の `expected_nodes` へそのまま写した。
- 本走: **baseline PASSED、負例 10 件 (M1〜M10) すべて KILLED で期待 node と観測 node が完全一致 (matching 11/11)、
  等価変異 M0 (docstring 1 行) は SURVIVED、MISMATCH 0、TIMEOUT 0**。全変異の anchor は 1 箇所 (anchor_counts = 1、M9 は
  2 箇所とも 1)。所要は変異 11 件で 23 分 (各 28〜370 秒、queue 待ち込み)。

| ID | 変異 (single-site) | KILLED node 数 | killer |
|---|---|---|---|
| M0 | tool docstring の 1 行 (等価) | — (SURVIVED) | — |
| M1 | `Popen` に `start_new_session=True` | 7 | pgid 正例 (test 側の独立観測) + launcher の fail-closed (pgid 不一致 → unknown / rc 2) で実 rm 正例・chmod 負例・転送 3・timeout も赤 |
| M2 | `cancel()` の転送段を消し KILL だけ | 4 | 転送負例 TERM / INT / HUP (pending 未観測) + timeout 負例 |
| M3 | interrupted を removed に | 4 | 転送負例 3 + timeout 負例 (status と rc) |
| M4 | 最終 lstat 再確認を恒真化 (`absent = True`) | 1 | `test_zero_returncode_with_existing_path_is_failed` (専属) |
| M5 | 子 rc > 0 を成功扱い | 1 | `test_nonzero_returncode_with_absent_path_is_failed` (専属) |
| M6 | 包含 (nested) 検査を重複だけに | 1 | `test_usage_rejects_paths_without_removal[nested]` (専属) |
| M7 | cwd 検査を恒偽化 | 2 | `test_usage_rejects_cwd_inside_target[exact / descendant]` |
| M8 | timeout 超過の取消 (取消印 + TERM) を消して待ち続ける | 1 | `test_timeout_is_interrupted` (専属) |
| M9 | M1 + pgid 検査の恒真化 (両層) | 1 | `test_children_share_parent_pgid_then_remove` の独立 pgid 観測だけ (launcher 側は黙る) |
| M10 | handler 登録から HUP を外す | 1 | `test_launcher_signal_is_forwarded_before_removal[HUP]` (専属) |

M1 の 7 node は単一の注入 (`start_new_session=True`) を launcher の fail-closed が全 CLI 経路で rc 2 にした結果で、
理由は 1 つ。M9 が M1 より少ない 1 node なのは、恒真化で launcher が黙り test 側の独立観測だけが残るからで、両層登録の
意図どおり (M-h 単独の検出は主張しない)。M4 / M5 は判定関数直呼び node が専属 killer で、CLI 経路を迂回する変異まで
証明したとは書かない。

## 残存限界・scope 外 (記録のみ)

- 保証外の kill の形 (上記) は実測していない。Bash tool / session 終了時に launcher へ何が届くかは未証明のまま。
- `tools/README.md` 1 の実行場所分類 (login node の cgroup ピーク実測) はユーザー手番で未実施。先例 `dev_wave_cleanup.py` /
  `dev_wave_land.py` も未登録で login 運用、launcher の資源は §3 が従来から許す `rm -rf` と同じ。registry へは足していない。
- Codex overlay (`.agents/skills/cleanup-branches/SKILL.md`) は未変更で §3 を継承する (real prune 禁止は維持)。
- `tools/mutation_worktree.py` は wave worktree を source にすると共有木 (primary) の churn で事後検査 rc 125 になった
  (plan-only で 1 回、1 回目は `git worktree add` の EINTR)。独立 clone (`git clone --no-checkout` + submodule URL を
  local module store へ向けた `submodule update --init`) を source にして完走した。
- launcher の `rm` は PATH 解決 (運用上の信頼境界)。`/bin/rm` 固定にすると wrapper 同期が使えない。

## 逐語の行末空白の可逆正規化 (DW-S07)

`verbatim/` の `.md` / `.txt` は `git diff --check` に触れる行末空白 (Codex 出力の Markdown 二重空白改行と probe 出力の
末尾空白) を除いてある。可視文字は不変。原文 bytes は `verbatim/originals.json` (sha256
`8ac07b5919f3c6a10409d86b1691688a276ae6a45463e3e03f66abccab6d50bb`) に UTF-8 text として収め、各 text をそのまま
書き出せば原文 bytes を復元できる。`s6-focus-rereview.md` は末尾改行を 1 byte 足しただけ。

| file | 原文 bytes | 原文 sha256 | 行末空白を除いた行数 | 正規化後 bytes |
|---|---|---|---|---|
| `s2-plan.md` | 18611 | `b48d99fc7ba25bf9…` | 4 | 18604 |
| `s3-lensA.md` | 13956 | `1c1d91ac86dd2f50…` | 4 | 13949 |
| `s3-lensB.md` | 11652 | `7deb18d1a9b90e90…` | 3 | 11647 |
| `s5-author.md` | 5901 | `92d6740a8a8ebf11…` | 4 | 5894 |
| `s6-reviewA.md` | 6533 | `2deb3d65f53f6974…` | 11 | 6512 |
| `s6-reviewB.md` | 9428 | `35aa3128f643133d…` | 10 | 9409 |
| `s6-fix.md` | 3659 | `282649a25e5f7157…` | 3 | 3654 |
| `s6-focus-rereview.md` | 5419 | `4a6e6a347898bbbb…` | 0 | 5420 |
| `parent-probe-guard.txt` | 698 | `b684c5f4a9877c8a…` | 6 | 692 |
