---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-b10-overthrottle-grid
seq: 4
---

## 新規

### {{F:submitter-required-command-absent}}. 投入 script が実在しないコマンドを必須にしており、着地後の初回起動でしか出なかった [手順漏れ]

- 事象: 新設した Pegasus 投入 script が必須コマンドとして `quota` を要求していたが、
  このクラスタに `quota` は存在しない (`command -v` も `/usr/bin` `/usr/sbin` `/bin` `/sbin`
  の探索も 0 件)。実機で起動すると
  `required submission command is unavailable: quota` で rc=2 になり、**永久に起動できない。**
  正しいコマンドは `check_quota` (`/system/tool/bin/check_quota`) で、
  `docs/pegasus-runbook.md` の「ストレージと quota」節と投入前チェックリストの両方が
  そう書いていた。
- 根本原因: 実装子が汎用 Unix の `quota` を書き、**実在を確かめなかった。**
  受入全走はこの型を捕まえない — script を実機で起動して初めて出る。
  さらに**新しい Pegasus 実行体は登録簿が main へ着地するまで hook に拒否されて起動できない**
  ため、**着地後の初回起動でしか発見できない**構造になっていた。
  段 6 のレビューは payload の中身を静的に読んだが、コマンドの実在は照合しなかった。
- 恒久対応: 必須コマンド一覧と実呼び出しを `check_quota` へ直し、
  **必須一覧・実呼び出し・旧呼び出しの不在の 3 点を golden で固定する検査**を
  `orchestrator/tests/test_backoff_extended_sweep.py` へ追加した。
  あわせて job body の固定 PATH 上のコマンドを含め、全必須コマンドの実在を
  `command -v` で確認した (submitter 5 件 + job body 8 件、全件 rc=0)。
- 再発検知: **新しい実行体を足す wave では、必須コマンド一覧の各要素を
  `command -v` で 1 件ずつ確かめてから commit する。** runbook が名前を定めている場合は
  そちらを正本にする (このクラスタは `check_quota` / `rbudgetcheck` であって
  `quota` / `df` ではない)。段 6 のレビュー観点にも「payload が要求する外部コマンドの実在」を含める。
