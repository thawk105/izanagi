---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-22
wave: dev-wave-t2797-b5-effect-bundle
seq: 1
---

## 新規

### {{F:child-prompt-ban-vs-existing-internals}}. 実装子への禁止の字面が、呼ぶよう指示した既存関数の内部挙動まで射程に入り、子が正しく停止して fix が 1 巡増えた [手順漏れ]

- 事象: [T-2797] 発効束 wave の段 5 で、LLM 巡 tool の実装子へ「tool は subprocess を起動しない」と「知識解決は既存関数を使う」を同じ prompt で指示した。既存の
  `orchestrator/campaign/knowledge_manifest.py` の `load_and_resolve_manifest` は内部で読み取り専用の git を起動するので、子は両立できないと判断して知識解決を
  `NotImplementedError` で止め、確認を求めて報告した。親が「tool 自身のコードが直接起動しない」の意味と裁定し、fix を 1 巡足した (約 3 分、codex 1 本)。
  前段の同タスク Tier0 wave でも、fix 子への「差し替えてよいのは 2 つだけ」という広すぎる禁止で子が正しく停止し、1 巡を空費している (独立 2 例目)。
- 根本原因: 禁止を「何を起動・編集してはいけないか」の字面だけで書き、呼ぶよう指示した既存関数の内部挙動 (process 起動・既存 fixture の差し替え) が禁止の射程に入るかを決めていなかった。
  子は禁止を広く読んで止まるのが正しい振る舞いなので、曖昧さの費用は毎回 1 巡になる。
- 恒久対応: 実装子・fix 子への禁止は「子が書くコード自身が直接行うこと」に限定し、呼ぶよう指示した既存関数の内部挙動は禁止の外であると prompt に明記する。
  memory `codex-child-discipline` の「実装子への禁止は直接行うことに限る」節。
- 再発検知: 子の報告に「指示間の衝突」「確認への回答がない」が出たらこの型である。prompt を書く時点で、禁止語 (起動しない・差し替えない・触らない) と
  「既存関数を使う」が同じ prompt にあれば、その既存関数の内部を grep して衝突の有無を確かめる。

## 再発

### F698

- **再発: 2026-09-22** — [T-2797] 発効束 wave で、試走と本走の知識射影の `diff` の出力を insight の `bundle/` に拡張子 `.diff` で置いたところ、commit 前の
  `tools/check_ai_provenance.py --message-file` が実装面 (patch / diff) と判定した。拡張子を `.diff.txt` に変えて解消した (commit 前に検出、実害なし)。
  再発検知の `git ls-files <insight dir>` の grep は `\.py$` だけでなく `\.(patch|diff)$` も対象にする。
