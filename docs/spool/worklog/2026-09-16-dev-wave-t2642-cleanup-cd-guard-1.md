---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2642-cleanup-cd-guard
seq: 1
title: [T-2642] は [T-2641] と編集面が衝突したため実装を降り、文面案・pin 閉包 17 群・checker の rc0 の射程を凍結した (docs のみ、branch worktree-dev-wave-t2642-cleanup-cd-guard、実装面の差分ゼロにつき変異 matrix 免除)
---

## 本文

**後発として実装を降りた。** 依頼は「[T-2641] が同じ面を触るので、着手前に稼働 wave の編集面重複を
作業ツリーの未 commit まで見て確認し、重なれば後発が降りる」と定めていた。着手前検査 (≈04:33 JST) では
全 74 worktree の未 commit 差分・branch tip 差分ともに 0 件、`ps` でも T-2641 の稼働は 0 件だった。
04:47 JST に T-2641 の plan 子が `ps` に現れ、`.git/worktrees/` の birth time を実測すると
`dev-wave-t2641-cleanup-gate-order` = **04:34:10**、本 wave = **04:34:38** で **T-2641 が 28 秒先発**
だった。編集面 (`.claude/commands/cleanup-branches.md` §1/§2/§3、`tools/check_docs.py` の
`CLEANUP_COMMAND_SHA256`) は完全に重なるため、後発の本 wave が降りた。

**この検査法自体が不十分だった。** worktree 一覧 + 未 commit 差分 + `ps` の 3 点で見ても、相手が
worktree を作った直後・編集前だと全部 0 件になる。先後の判定には `.git/worktrees/*` の birth time か
`ListAgents` の peer 一覧が要る。

**peer session へ実測データを 2 度送った** (04:52 / 05:12 JST、`SendMessage`)。pin 閉包、予算の実数、
SKILL digest の要否、pin 閉包の補足 7 群を渡した。返信は本 wave の終了時点で未着。通知は一方向の
データ提供として扱い、待機・検査省略の根拠にしていない。

**依頼文の前提を 1 つ実測で訂正した。** 依頼は編集面を「`CLEANUP_COMMAND_SHA256` と
`CODEX_CLEANUP_BRANCHES_SKILL_SHA256` の同時更新」としていたが、`.agents/skills/cleanup-branches/SKILL.md`
は command を全文読む設計で、command だけを変えたときに skill 側 digest の更新が要る経路は無い
(`tools/check_docs.py:5183`・5219 は skill 自身の文字列だけを hash し、command は 6571 で別に hash する)。
**要る定数は 1 つだった。**

**親の pin 閉包主張が不完全だった。** 親は 10 アンカーを全数として brief に書いたが、敵対相談が
独立に 7 群の逐語依存を検出した (`commit graph` の一意性 / `## 4. 事後検査` の見出し / §2 見出し全文の
一意性 / checker 呼出し〜「停止。」の部分逐語 / F26 住所表現 / description 行全文 /
`CLEANUP_COMMAND_SHA256` の代入書式)。いずれも `orchestrator/tests/test_check_docs.py`。
**§2 見出し全文の一意性は、§2 を書き換える T-2641 に直撃する。** 一方、command の固定行番号・総行数を
assert する pin は 2 file 内に存在しないことも実測された (行番号・数値・digest・値文字列で検索)。

**親の provisional 裁定 (P1) は一部反証された。** 「既存 `tools/check_worktree_occupancy.py` で足りる」
のうち、自己 PID の cwd を除外しないこと・`seen = {self_pid}` が祖先探索の循環防止であることは
confirm されたが、**「対象内に居れば必ず rc=1」は成立しない**。rc0 になる経路が 4 つある —
別 PID namespace、cwd 読取権限不足 (`:403` は非阻害診断)、`resolve(strict=True)` の PermissionError
(`:422` も非阻害)、対象外の deleted cwd (`:430`)。**rc0 は進入防止でも退避証明でもない。**
文面側に「rc0 を退避の証明として扱わない」を明示する義務が生じる。

**敵対相談が文面案の穴を 2 つ突いた (いずれも must-fix、実装 wave への持ち越し)。**
(1) 「撤去対象へは `cd` せず」だけでは、**撤去対象が確定する前の棚卸し中**の `cd` を許す読み方が残る。
2026-09-15 の実経路 (§1 の status/untracked 確認で入った) と一致する。禁止対象に棚卸し候補を含めて
明記する必要がある。(2) 「別 cwd を指定した一時シェルの `pwd` では確認完了と扱わない」という制限が
プラン本文へ転記されておらず、文面だけを読む実行者へ届かない。

**段 3 の片方が 2 回不採用になった。** 原因は子が `orchestrator/tests/test_check_docs.py`
(476 KB / 12753 行) を全文 `cat` したことで、巨大出力を含む rollout の行が壊れ `event_invalid` で
`outcome=not_accepted` になった (`launcher_rc=1`、log は空、`codex_exit_code=0`)。同じ prompt で 2 回
同じ落ち方をした。prompt に「`grep -n` で位置を出し `sed -n` で 200 行以内ずつ読む」を足した 3 回目で
採用された。**read-only 子に巨大 file を読ませる wave では、読み方を prompt で縛る必要がある。**

工数: Codex 子 5 本 (plan 1・consult 4、うち 2 本は不採用、いずれも gpt-6-astra / medium)。
計算ノード job は 0 件 (repo 内の docs のみ)。

記録 commit 前に実走した検査: `python3 tools/check_docs.py`、`python3 tools/check_codex_output.py`
(採用した 3 成果物すべて rc=0)、`python3 -m orchestrator.campaign.s8b_holdout_freeze search` (hit 0)、
`python3 tools/check_ai_provenance.py` の全史監査 (10270 件、新規違反なし)。

**受入 attempt 1 (tip bd8c600e8) は 5 件の赤で返り、非帰属と判定した。** 23773 passed / 5 failed。
赤は `test_check_ai_provenance.py::test_provenance_headroom_short_queue_unavailable_cap_oom_stops`、
`test_p3_b4_producer_auth_experiment.py::test_disposable_tree_mutation_does_not_change_main_worktree`、
`test_run_tests_preflight.py::test_headroom_short_queue_unavailable_cap_oom_stops_without_dispatch`、
`test_s1_known_axes_freeze.py::test_historical_oracle_nonadapter_reaches_current_semantics`、
`test_t338_submission_gate_unit5.py::test_receipt_publish_call_sites_are_path_aware_and_allow_event_sink`。
根拠は (a) 本 wave の変更面は `docs/spool/` の fragment 2 件と `output/insights/2026-09-16/` の
新規 md 6 件だけで、この 5 test はいずれもそれらを読まず差分から到達しない、(b) **同一 tip での
単独再走で 5 件とも緑** (68.33 秒、5 passed)、(c) 投入時の load average が 17 台の高負荷局面で、
赤 2 件は headroom / queue / OOM の資源判定 test、1 件は使い捨て木と main worktree の分離 test という
負荷・並行に敏感な型だった。DW-O18 に従い単独再走 1 回だけ行い、受入を再投入した。

## 次の一手差分

### 更新

- [T-2642] **P3・設計済み / 実装は [T-2641] の land 後**: `/cleanup-branches` の進入禁止と
  cwd 検査の明文化。文面案 (§1 冒頭へ進入禁止 1 行、§1/§2 の縮約で 108 bytes 捻出、§2 の退避指示を
  §3 へ移設・強化、改訂後 5897 / 5900 bytes・最長 105 文字) と pin 閉包 17 群は
  `output/insights/2026-09-16/t2642-cleanup-cd-guard/` に凍結済み。**そのまま実装してはならない** —
  敵対相談の must-fix 2 件 (撤去対象が確定する前の棚卸し中の `cd` を禁止対象に含める / checker の rc0 を
  退避の証明として扱わない旨を文面へ載せる) を反映した文面に直す必要がある。要る checker 定数は
  `CLEANUP_COMMAND_SHA256` の 1 つだけ (skill 側 digest は不要、実測済み)。T-2641 が §1/§2 を
  書き換えるため、実装は T-2641 の land 後に main の現物から再採寸して始める。
  base: d071ae31c19de82703e27c90edf2c4a8fb594d09dd80fed3f4afa171716f88a0
