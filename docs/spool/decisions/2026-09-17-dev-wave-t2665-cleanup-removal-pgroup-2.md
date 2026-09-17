---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2665-cleanup-removal-pgroup
seq: 2
---

## {{D:cleanup-removal-launcher-same-process-group}}. 並列撤去の launcher は子を親と同じ process group で起動し、親自身が受けた TERM/INT/HUP を子へ転送して有界に止める

**決定:** D2104 項 32 の実装として、`/cleanup-branches` §3 手順 3 の directory 撤去は新規
`tools/cleanup_remove_dirs.py` に固定する。

1. 1 path = 1 子 process (`rm -rf -- <path>`) を親と同じ process group で起動する。`start_new_session` /
   `preexec_fn` / `shell` / `killpg` は使わない。起動直後に `os.getpgid(child) == os.getpgrp()` を実測し、
   不一致・取得失敗は unknown として全体を取消す。
2. 「親」とは launcher 自身を指す。launcher が受けた TERM / INT / HUP を生存子へ転送し、5 秒の猶予の後
   SIGKILL、さらに 1 秒待って未回収は unknown。process group 宛の signal は子へ直接届く。launcher PID
   単独への SIGKILL、上位 shell だけの kill、Bash tool / session 終了時の配送契約は保証しない
   (docstring に明記、`PR_SET_PDEATHSIG` は scope 外)。
3. 判定は removed / failed / interrupted / unknown の 4 値。timeout は子ごとに測り、検出時点で取消印を
   付けてから同じ取消経路を通す。取消待ちの間も全体 signal を読む。全子 reap 後に全 path を lstat で
   再確認 (ENOENT だけ absent) し、TERM/INT/HUP を SIG_DFL へ戻してから cancel flag を最終読取して
   summary を確定する。rc は 0 (全件 removed)・1 (failed のみ)・2 (interrupted / unknown / 取消 /
   障害)・64 (usage) を 1 箇所で決める。process の exit status が正で、JSON summary の rc はそれを写す。
4. prune・detach・branch 削除・再試行・任意 command・監視は実装しない。§3 は「全対象の 1・2・占有検査の後、
   前景 1 回 (setsid・nohup・& 禁止)、rc0 以外は停止」と書き、prune へ進む条件を rc0 に限る。
5. 中断の負例は機構を差し替えず、PATH 先頭の自己停止 wrapper (`kill -STOP $$; exec /bin/rm "$@"`) と
   `/proc` の停止状態・pending signal で同期する。launcher が `rm` を PATH 解決することは運用上の信頼境界
   として docstring に書く。

**理由:**
- 段 1 の現物同定で、並列撤去の launcher は repo に存在せず、`tools/dev_wave_cleanup.py` (段 9 専用) は
  同一 process 内の `shutil.rmtree` で子を作らないと分かった。裁定の「同じ process group / 中断・不明を
  完了扱いしない / prune へ進まない」は prose だけでは検査できず、Bash guard は `nohup setsid rm -rf` を
  許可する (site=None の probe)。固定した起動・取消・集約を実装して初めて test と変異で示せる。
- 同じ process group は signal の宛先を共有する条件であって、親の死を子へ通知する機構ではない
  (段 3 レンズ A / B が独立に指摘)。plain `kill <launcher>` にも道連れを成立させるには launcher 自身の
  転送が要り、これは裁定の局所補強であって汎用 supervisor ではない。SIGKILL は捕捉できないので限界として
  書く。
- timeout 検出と取消の間に子が rc 0 で完走すると removed / rc 0 に落ちる競合、取消待ちの間に全体 signal を
  読まない遅延、summary 確定後の signal で JSON と exit status が食い違う窓は、段 6 レビューが静的に見つけ
  fix で閉じた。
- ptrace (exec-event stop) による同期は Yama / container の権限と、再開と転送の競合 (レンズ A) を残す。
  自己停止 wrapper は同 PID で実物へ委譲する観測 wrapper で、login node と計算ノード container の両方で
  決定的に動いた (T 状態 6 ms、CONT 後 -15 / -2 / -1)。

**却下した選択肢:**
- docs-only (§3 の文面だけ) — 機構が検査不能で、setsid 形の起動を止められない。
- `tools/dev_wave_cleanup.py` へ並列撤去を足す — 段 9 の単一 wave 撤去と prune までを持つ別機構で、
  裁定の対象外。
- `PR_SET_PDEATHSIG` / `--one-file-system` / prune の自動化 — 裁定に無い機構で、「本題だけ」に反する。
- test 用 seam (`--remove-command` 等) — 機構の差し替えになる。
