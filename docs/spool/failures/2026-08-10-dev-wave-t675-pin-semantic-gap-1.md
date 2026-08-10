---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-10
wave: dev-wave-t675-pin-semantic-gap
seq: 1
---

## 新規

### {{F:codex-child-oom-under-shared-user-cap}}. 並行 wave が増えると codex 子が共有 16GiB 上限で無音 kill される [セッション死・救出]

- 事象: 本 wave で read-only の codex 子が **3 回**、`.done` を書かず log を途中で切って消滅した
  (段 2 の 1 本目、段 3 レンズ A・B の初回)。error 文字列も終了メッセージも出ない。
  いずれも大きいファイル (`tools/check_docs.py` 4500 行超、`docs/decisions.md`) を
  丸ごと表示した直後だった。
- 根本原因: login node の cgroup 上限は **session ではなく user 単位**である。
  実測 = `/sys/fs/cgroup/user.slice/user-<uid>.slice/memory.max` が
  **17179869184 (16 GiB)**、同 `memory.events` の `oom_kill` が 1308。
  自分の子が居ない時点でも `memory.current` が 10.6 GB あり、これは
  **同時に走る別の背景 job (別 wave) の codex 子が同じ user slice を食っている**ためである。
  1 wave 単独の見積りで子を並列投入すると、他 wave の分と合算して上限に当たる。
- 影響: 実害は wall-clock のみ。pid 監視の待ち手が 3 回とも producer 死を検出したため、
  無音ハングにはならなかった。`.done` の出現だけを待つ待ち手なら 3 回とも永久に待つ。
- 恒久対応: memory `login-node-memory-cap-16gib` の「上限は user 単位で全並行 job が共有する」
  という射程を運用へ効かせる — (1) 待ち手は必ず pid を待ち条件に含める
  (`docs/dev-wave/core.md` `DW-C00` の「生産者の死も待ち条件に含める」が既に義務化しており、
  本件はその義務が実際に効いた事例である)、(2) 子の prompt に**巨大ファイルの全文表示を
  禁じ、行範囲読みを指示する**。本 wave では (2) を適用した prompt へ差し替えた 2 本が
  いずれも完走した (段 2 再投入、段 3 レンズ A・B の再投入)。
- 再発検知: 子が死んだら `/sys/fs/cgroup/user.slice/user-<uid>.slice/memory.events` の
  `oom_kill` を読む。増えていれば資源であり、prompt や認証を疑う前に並列度を下げる。
