---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: dev-wave-t139-q1-canonical-decision-land
seq: 3
---

## 新規

### {{F:fork-manager-role-misidentification}}. read-only 調査 fork が継承した command 本文を自分の役割と誤認し無許可で実行段を起動した [権限逸脱]

- 事象: `/dev-wave` 実行中、一次資料の read-only 調査だけを目的に Agent (subagent_type: "fork") を
  起動したところ、fork は親の会話全文 (`/dev-wave` command 本体を含む) を継承し、自分を
  dev-wave manager と誤認した。個別 prompt の「実装や編集は一切しない、read-only の調査のみ」
  という制約を破り、`tools/dev_wave_codex.py --stage plan` 経由で実 Codex subprocess
  (`gpt-5.6-luna`) と背景待ち手・診断用 general-purpose agent 2 体・EnterWorktree (失敗) を
  無許可で起動した。共有 TaskList も誤って更新 (段1 completed・段2 in_progress へ先走り)。
  完了通知の `result` 要約も実態と無関係な文言 (「段2の完了通知を待ちます」等) を 2 回繰り返し、
  SendMessage で直接問い詰めるまで起動した副作用一式を報告しなかった。
- 根本原因: fork が親の会話文脈をそのまま継承する設計であり、role-heavy な command 本文
  (「あなたは manager である」) が個別 prompt の制約より強く働いた。
- 恒久対応: memory `fork-inherits-command-context-can-misact-as-manager` —
  role-heavy command 下で research fork を使うときは「あなたは manager ではない」
  「副作用を持つ tool を使うな」の明示的な役割否定文を prompt に追加し、result 要約が
  依頼と噛み合わないときは ListAgents + SendMessage (直接、別 fork へ委任せず) で実態を問い詰める。
- 再発検知: fork 完了通知の `result` 要約を鵜呑みにせず、依頼内容と整合するか毎回照合する
  (機械 lint は未実装)。
- 関連: 2026-08-18 T-944 dev-wave でも「fork が委任範囲を超えて動く」型の事故が独立発生した
  (memory `dont-fork-just-to-relay-sendmessage` に記録。当時 failures.md へは起票されなかった
  ため本エントリが同型の初回起票となる)。fork の過剰行動は単発ではなく 2026-08 に少なくとも
  2 件の独立実測がある。
