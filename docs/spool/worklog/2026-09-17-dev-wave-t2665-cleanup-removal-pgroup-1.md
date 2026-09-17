---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2665-cleanup-removal-pgroup
seq: 1
title: [T-2665] 並列撤去の launcher を置き、子を親の process group で起動して親の停止で道連れにする (コード + テスト + docs、branch worktree-dev-wave-t2665-cleanup-removal-pgroup、変異 matrix = baseline PASSED・10/10 KILLED・等価 1 SURVIVED・MISMATCH 0・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「[T-2665] 並列撤去の子 process を親の process group に置き (setsid しない)、親 kill で道連れにする
  局所修正 (D2104 項 32)。中断・不明は完了扱いせず prune へ進まない。対象は撤去 tool (段 1 で現物同定)。文書収容
  (byte 予算) は D782 の手順で別扱い。Codex author (D95) + 変異事前登録。汎用 process supervisor へ広げない。本題だけ」。
- **閉じた。** 一次資料は `output/insights/2026-09-17/t2665-cleanup-removal-pgroup/README.md`。設計判断は
  {{D:cleanup-removal-launcher-same-process-group}}。実装 commit `46a88693c` (Codex author)。
- **段 1 の現物同定で引数の前提が 1 つ覆った。** `tools/dev_wave_cleanup.py` (段 9 専用) は `shutil.rmtree` を同一
  process 内で行い子を作らない。並列撤去は `/cleanup-branches` §3 手順 3 の手動手順にしか無く、launcher は repo に
  存在しなかった。Bash guard は `nohup setsid rm -rf <worktree>` を許可する (`decide()`、site=None の probe)。
  新規 `tools/cleanup_remove_dirs.py` を裁定の機構を固定する最小 launcher として置いた。引数の「worklog entry 1422」は
  archive file の行番号で、実体は entry 1526 の起票。
- **段 3 の 2 レンズが独立に親 brief の完了判定 (b)「親 kill で道連れ」を反証した。** 同じ process group は signal の
  宛先を共有する条件であって親の死を子へ通知する機構ではない。「親」= launcher 自身が受けた TERM/INT/HUP の転送に
  保証範囲を限定し、SIGKILL・上位 shell の kill・Bash tool / session 終了時の配送は限界として docstring に書いた。
- **plan の ptrace 同期案を不採用にし、親の生死実験で自己停止 wrapper を採った。** `kill -STOP $$; exec /bin/rm "$@"`
  を PATH 先頭に置き、`/proc` の T 状態 → pending signal (ShdPnd) → SIGCONT の順で同期する (login node 実測: 停止 6 ms、
  TERM/INT/HUP で -15/-2/-1、対象残存、正例は委譲で消える)。レンズ A/B は DW-O14 の「実物へ委譲する観測 wrapper」に
  当たると判定し、条件 (同 PID で exec、`-signum` 必須、KILL の -9 は赤、skip を作らない、wrapper なし正例を別 node) を
  付けた。
- **段 6 レビュー 2 本は NO-GO (must-fix 3・nit 3) で全件 real・採用、fix 1 巡で closed、焦点再レビュー GO。**
  A1 = timeout 検出と取消の間に子が rc 0 で完走すると removed / rc 0 に落ちる競合 (検出時点で取消印)、A2 = timeout
  取消の猶予待ち中に全体 signal を読まない (各周で flag を見て即全体取消)、B-01 = summary 確定後の signal で JSON rc 0
  と process rc 2 が食い違う (成功境界で SIG_DFL へ戻し、process exit status を正と契約)。
- docs 収容は D782 の削減段階で閉じた: 手順 1 の重複補足 19 bytes を削り、§3 手順 3 を launcher 呼出し + 「全対象の
  1・2・占有検査の後」「前景 1 回 (setsid・nohup・& 禁止)」「rc0 以外は停止」へ差し替えて 6201 / 6204 bytes。上限は
  上げていない。削除述語・閾値・評価順は不変 (§1・§2・§3 冒頭 2 行・§4 以降は byte 不変、レビュー B が照合)。
- 実走 (計算ノード dispatch): 新規 test 単独 36 passed / 4.4 s、consumer + meta 7 file 1169 passed / 3 skipped (growth
  hold) / 108 s、fix 後 3 file 115 passed / 99 s。親の dogfood (login、repo 外): 2 dir → rc 0 (子 pgid = 親 pgid 実測)、
  入れ子 → rc 64、実 rm 4 万 file 走行中に launcher へ TERM → rc 2・子 -15・生存子なし・39,655 entry 残存 (fix 前後で同じ)。
  provenance full 10,910 件・新規違反なし。
- **変異 matrix** (独立 clone `/work/1/SFC/tanab/mutation-src-t2665` を source にした使い捨て worktree、
  `run_tests.py` 1 file、`--force-dispatch`): probe 走 (全件 SURVIVED 登録) で観測 node を集めてから本走。本走は baseline PASSED、負例 10 件 (M1〜M10) すべて KILLED で期待 node と観測 node が完全一致 (matching 11/11)、等価変異 M0 (docstring) は SURVIVED、MISMATCH 0、TIMEOUT 0、所要 23 分。専属 killer: M4 lstat 再確認の恒真化 → rc0 残存 node、M5 rc>0 成功扱い → rc>0 不在 node、M6 包含検査 → nested、M8 timeout 取消の削除 → timeout 負例、M10 HUP 未登録 → [HUP]。M1 (start_new_session) は launcher の fail-closed で 7 node、両層 M9 (M1 + pgid 検査の恒真化) は test 側の独立観測 1 node だけが殺す。受入全走は記録 commit 後の tip へ投入する (結果は land の受領証と worklog 末尾)。
- 残存 (scope 外、記録のみ): launcher PID 単独への SIGKILL・上位 shell だけの kill・Bash tool / session 終了時の signal
  配送は保証外 (docstring 明記、実測せず)。`tools/README.md` 1 の実行場所分類 (login の cgroup ピーク実測) はユーザー手番
  で未実施 — 先例 `dev_wave_cleanup.py` / `dev_wave_land.py` も未登録で login 運用、launcher の資源は §3 が従来から許す
  `rm -rf` と同じ。Codex overlay (`.agents/skills/cleanup-branches/SKILL.md`) は未変更で §3 を継承 (real prune 禁止は維持)。
  `mutation_worktree.py` は wave worktree を source にすると共有木 (primary) の churn で事後検査 rc 125 になり、独立
  clone (`git clone --no-checkout` + local URL の submodule init) へ切り替えて完走した。
- 工数: codex 子 8 本 (plan 1、consult 2、author 1、review 2、fix 1、focus 1、全段 `gpt-6-astra` / `medium`)。親の実測は
  probe 4 本 (guard / 自己停止 wrapper / signal 3 種 / dogfood 2 回)、焦点走 3 本 (計算ノード)、変異 2 走。

## 次の一手差分

### 完了

- [T-2665] 並列撤去の launcher `tools/cleanup_remove_dirs.py` を置き、子を親と同じ process group で起動、launcher が
  受けた TERM/INT/HUP を転送、中断・不明を rc 2 で完了扱いせず prune へ進まない契約を §3 手順 3 と test + 変異で固定した。
  remaining: none
  base: f15245a43ab42ef6dafc033591fdd0e5f983ce0e1bba93afc240809d42d3793a
