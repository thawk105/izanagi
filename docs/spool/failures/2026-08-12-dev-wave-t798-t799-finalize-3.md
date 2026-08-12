---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t798-t799-finalize
seq: 3
---

## 新規

### {{F:waiter-merge-conflict-hides-paths}}. 受入待ち手の merge 競合が競合 path を出さず、親が手で再現した [手順漏れ] [コンテキスト浪費]

- 事象: `tools/dev_wave_wait.py acceptance` が lease 取得後の main 取り込みで競合し、
  ログに `error: stage=merge rc=70 source_rc=1` の 1 行だけを残して終了した。
  **どの file が競合したかは出力されない。** 受入全走は 1 度も走っていない。
  親は `git merge --no-commit --no-ff refs/heads/main` を自分で打ち直して競合を再現し、
  `orchestrator/tests/test_spool_fold.py` の import ブロック 1 hunk だけと特定した
  (本 wave 側 `import dataclasses`、main 側 `Iterator` / `contextmanager`、双方必要)。
  待ち行列 5 本を待って得た lease 1 サイクルを、import 3 行のために丸ごと捨てた。
- 根本原因: F196 / F197 の恒久対応どおり、待ち手は競合時に `git merge --abort` して
  lease を返す。実装面を自動解決しないのは D95 の Codex author 契約に照らして正しい。
  **誤っているのは解決方針ではなく診断の粒度**で、rc だけでは親が着手できず、
  merge を手で再現する 1 往復が必ず挟まる。競合の発生確率は待ち行列長に比例して上がるため、
  区画が混むほどこの往復が増える。
- 恒久対応: memory `waiter-merge-conflict-rc70-hides-paths` — rc=70 を見たら
  (1) 作業木が clean に戻っていることを確認、(2) 自分で merge を打って競合 path を特定、
  (3) 実装面なら Codex `role=author` に解決させる、(4) `git show :1: :2: :3:` +
  `git merge-file` で marker 付き automerge を再生成し、子の成果との差分が
  **marker 除去だけ**であることを検査、(5) commit して並び直す、という手順を固定した。
  待ち手側の診断出力の改善は本 wave の scope 外であり、起票 {{T:waiter-conflict-diagnostics}} へ回す。
- 再発検知: 待ち手ログに `stage=merge rc=70` があり、かつ同 job に受入 log が
  生成されていない組み合わせ。この組が出たら親は merge の手動再現から始める。

### {{F:land-phase-probe-cannot-use-hooks}}. land の相を測る probe を git hook で組もうとして空振りした [手順漏れ]

- 事象: fold / land の**どの相で落ちるか**を実測する probe を `post-commit` hook による
  crash 注入で組もうとしたが、hook が一切発火しなかった。`GIT_HARDENING_CONFIG` が
  `core.hooksPath=/dev/null` を設定しているためである。`DW-O01` は背景 job の detach 形を
  書いているが、この制約は書かれていない。
- 根本原因: 防壁 (hook 経路の遮断) と観測 (相の実測) が同じ機構を使うため、
  防壁が有効な環境では観測手段として成立しない。probe 設計時にこの衝突を検査していなかった。
- 恒久対応: memory `land-phase-probe-cannot-use-git-hooks` — 代わりに
  `refs/heads/<branch>` を tight loop で監視する **ref-watcher** を別 process に立て、
  狙った ref 遷移で対象 pid へ SIGKILL を送る。land の post-commit 相を狙うときは
  **二相 watcher** が要る (まず tested_tip への ff を待ち、その次の ref 変化で kill する。
  1 相だと ff 自体で撃つ)。probe は repo の外に置く ([T-317] 裁定)。
  実体 = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/probe/probe_post_commit_crash.py`。
- 再発検知: probe が hook 経路に依存していないかを、`git config core.hooksPath` の値と
  併せて設計時に確認する。値が `/dev/null` なら hook 案は不成立である。
