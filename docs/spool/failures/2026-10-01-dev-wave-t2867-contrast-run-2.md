---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-10-01
wave: dev-wave-t2867-contrast-run
seq: 2
---

## 新規

### {{F:guard-computed-args-repeated}}. 隔離 session の Bash guard が計算値の引数・複合コマンドを拒否する型を、同じ wave で約 10 回踏んだ [手順漏れ]

- 事象: 2026-09-30 の生成器対照の本走 wave ([T-2867]) で、親が `J=<dir>; python3 $J/…`、`for n in …; do … $n …; done`、`sed -i … $J/…`、`bash $J/….sh` のように
  shell 変数や loop 変数で組み立てたコマンドを Bash tool へ書き、隔離 session の guard に「値が実行時に計算されるので git でないと示せない」として約 10 回拒否された。
  毎回、引数を逐語の絶対 path に書き直すか、処理を job dir の `.sh`・`python3 -c` の本文へ移して通した。同じものを投げ直してはおらず、実害は tool 呼出しの空転だけ。
- 根本原因: 拒否の型 (計算値の argv、`git` を名指しうる複合コマンド、heredoc) は記憶 `git-and-guard-discipline` の 2026-09-20 追記に書かれていたが、
  wave の途中で読み返さず、長い監視の合間に書いた一回限りのコマンドで同じ型を繰り返した。
- 恒久対応: 新しい防壁は足さない (guard は正しく拒否している)。親は Bash tool のコマンドに shell 変数・loop・`$()` を置かず、path を逐語で書く。
  繰り返す処理は job dir の `.sh` に path を固定して書き、`bash <絶対 path>.sh <逐語の引数>` の 1 行で呼ぶ。
- 再発検知: 同じ session で guard の拒否文言 (「computed at runtime」「too complex to verify」) が 2 回目に出たら、以後のコマンドをすべて逐語 path 形に切り替える。

## 再発

### F26

- **再発: 2026-09-30** — 生成器対照の本走 wave ([T-2867]) で、submit checkout 16 本を 4 本ずつ並行の `git worktree add --detach` で作り、c03・c06・c11 の 3 本が rc=128 で落ちた
  (stderr を捨てていたので理由は未記録。login は他 wave の worktree 操作が並走)。作りかけは残らなかった。3 本を 1 本ずつ直列に作り直すと全部 1 回目で成功した。
  次からは作成側も 1 本ずつ直列にし、stderr を log に残す (2026-09-29 の再発が記した `--no-checkout` → lock → `reset --hard` の形も候補)。

### F273

- **再発: 2026-09-30** — 同じ wave で、親が driver 修正の commit 後に焦点走の `run_tests` dispatch と全史 provenance 監査を同一 worktree からほぼ同時に投入し、
  監査が焦点走の pending orphan hold (`phase: pending-qsub`) を検知して rc=16 (`reason=orphan-hold`) になった (`DW-C00` の「同一 worktree の dispatch は全種直列」違反、親の操作ミス)。
  焦点走 (37868.nqsv) は走り切って hold も自然に解除され、監査は単独の再投入で rc=0。qdel も hold の手動削除もしていない。既存恒久対応に直すべき新事実はない。

### F859

- **再発: 2026-09-30** — 同じ wave で、codex の dry-run のために Bash tool で `cd <子 worktree> && python3 tools/dev_wave_codex.py … --dry-run` を打ち、永続 shell の cwd が子の worktree へ移って
  次の Bash が拒否された。`EnterWorktree({path: <自分の wave worktree>})` で即座に戻した (空転 1 回)。以後の dry-run は launcher と同じく job dir の `.sh` 経由にした。
