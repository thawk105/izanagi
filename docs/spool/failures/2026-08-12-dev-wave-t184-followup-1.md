---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t184-followup
seq: 1
---

## 新規

### {{F:running-worktree-deleted-by-cwd-scan}}. 走行中の worktree が掃除の生存判定をすり抜けて削除された [計測汚染] [手順漏れ]

- 事象: 2026-08-12 20:57:55 JST、並行 session の worktree 掃除が、本 wave が測定 fixture として
  作った `.claude/worktrees/` 配下の 5 本を**子 7 走が使用中に削除**した。7 走中 6 走が走行中に
  working directory を失い、測定が無効になった (削除前に完了した 1 走のみ無傷)。
  施錠して再走した第 2 走と比較すると、**汚染は消費量を系統的に下振れさせていた**
  (7 cell 中 6 cell で第 2 走の `model_calls` が大きい。最大 65 → 128 の 2.0 倍)。
  気づかず報告していれば資源上限を実際より低く見積もる提案になっていた。
- 根本原因: 2 層ある。
  (1) 生成側 — detached HEAD・未施錠・main の祖先・dirty ゼロは残骸の 4 条件をすべて満たす。
  (2) **検出側 (本命)** — 掃除の生存判定 `/proc/*/cwd` 全走査は launcher 型の子を構造的に
  検出できない。`tools/codex_worker_launch.py` の cwd は**起動元** (親 wave の worktree) であり、
  操作対象 worktree は `--repo-root` / `--cwd` / `--artifact-dir` として **argv にしか現れない**。
  実測 (2026-08-12 21:28、稼働中の 7 走): `/proc/*/cwd` 一致 **0 件**、
  `/proc/*/cmdline` 一致 **14 件** (launcher 7 + codex 本体 7)。削除した session の同時刻観測と独立に一致。
  **`git worktree lock` は必要だが十分ではない** — lock が止めるのは `git worktree remove` であり、
  実際に使われた `rm -rf` + `git worktree prune` は lock を見ない。
- 恒久対応: {{D:worktree-liveness-by-cmdline}} — 生存判定に `/proc/*/cmdline` を含める。
  併せて子を走らせる worktree は `git worktree lock` する。保護の合図は **worktree の外**に置き、
  掃除側がそこを見る形にする (worktree 内へ命令形の目印 file を置くのは規律 6 に反する。下記参照)。
- 再発検知: 掃除手順の生存判定に cmdline 走査が含まれることの検査。加えて、
  **汚染は receipt からは見えない** — 汚染 6 走の receipt は `codex_exit_code=0` /
  `metering_status=complete` / `evidence_status=complete` / `limit_trigger=null` のまま残った。
  検出できたのは rollout 逐語の `exec_command failed for '/bin/bash -lc pwd': ... Rejected(...)` と
  `rg: external/ccbench/common/runner.cc: No such file or directory` (いずれも 11:57:5xZ) だけである。
  **工数・資源の集計前に rollout の失敗行を必ず見る。**

### {{F:contamination-detector-false-positive-on-rejected}}. 汚染判定器が sandbox の方針拒否を誤検知した [計測汚染]

- 事象: 上記の汚染を検出する判定器で `Rejected(...)` を徴候に使ったところ、第 2 走の 1 cell を
  汚染と誤判定した。実体は `rejected: rm -f style commands are not permitted. Use a safer approach`
  という **read-only sandbox の方針拒否**で、working directory の消失ではなかった。
  誤検知のまま進めれば、有効な測定 1 件を捨てて sweep 発火条件 (iii) の判定を誤っていた。
- 根本原因: 「失敗語が出た」を汚染の徴候にしたため、正常運用で出る拒否と区別できなかった。
- 恒久対応: 判定を **`pwd` 自体の失敗**と **worktree 配下の file 消失**に限定する
  ({{F:running-worktree-deleted-by-cwd-scan}} の再発検知手段と同じ実体)。
- 再発検知: 判定器が hit したら**逐語を出して中身を読む**まで判定を確定しない。

### {{F:truncated-job-prompt-absent-from-job-dir}}. 打ち切られた job の prompt bytes が job dir に残っていなかった [手順漏れ]

- 事象: 追走対象 5 件のうち 1 件 (`dev-wave-t786-docs-budget` の plan) の prompt が、
  同 job dir 内 93 file を全 hash しても存在しなかった。同一 wave の後続 plan 投入が
  prompt file を上書きしたためと考えられる。codex rollout jsonl から復元して初めて
  receipt の `prompt_sha256` (`33599e9c...`) と一致した。
- 根本原因: prompt file は上書きされうるが、receipt はその sha256 しか持たない。
  bytes の保全先が rollout しかない場合がある。
- 恒久対応: 再現・追走の一次資料として **rollout jsonl を receipt と対で扱う**
  (`docs/README.md` の地図に receipt の所在を記載済み。rollout path は receipt の
  `attempts[].rollouts[].path` にある)。
- 再発検知: 追走・再現の前に prompt bytes の sha256 一致を確認し、不在なら rollout から復元する。

### {{F:dryrun-argv-missing-artifact-parent}}. dry-run 生成 argv をそのまま走らせると起動前に停止した [手順漏れ]

- 事象: `tools/dev_wave_codex.py --dry-run` が出した argv をそのまま
  `codex_worker_launch.py run` へ渡したところ、7 走とも rc=2 で起動前停止した
  (`NG: parent directory が存在しない`)。dry-run は directory を作らないが launcher は
  artifact-dir の親の実在を要求する。
- 根本原因: dry-run と実投入で directory 作成の責務が分かれていることが argv からは分からない。
- 恒久対応: dry-run argv を再利用する運転側で、`--artifact-dir` / `--receipt` / `--manifest` の
  親 directory を先に作る。
- 再発検知: 投入前に rc=2 で止まるため実害は無い (本件も空費ゼロ)。手順として明記する。

## 再発

### F1

- **再発: 2026-08-12** — handoff の worktree 作成時刻を記帳時刻 (20:23) で書き、実際の dir mtime (20:18:15〜20:21:28) と最大 5 分ずれた。並行 session の撤去前実測の指摘で訂正。時刻の一次資料は記帳ではなく filesystem 側にある。
