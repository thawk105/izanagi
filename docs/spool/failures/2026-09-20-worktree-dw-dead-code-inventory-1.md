---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: worktree-dw-dead-code-inventory
seq: 1
---

## 再発

### F30

- **再発: 2026-09-19** — near miss (実害なし)。dead-code 棚卸し wave (`worktree-dw-dead-code-inventory`) の段 1 で、削除候補 3 file の参照を tracked text へ `grep -F` で走査したが、**走査対象を拡張子 allowlist (`.md .sh .py .json …`) で絞った**ため `output/insights/2026-09-16/t2638-codex-worktree-retirement/data/reach2.tsv` (到達性台帳、`.tsv`) の参照 6 件を落とし、hit 0 を「無参照 (A)」と結論して削除を brief に載せた。段 5 の author 子に「削除前に自分でも grep して 0 件を確かめよ」と書いていたため子が参照を見つけて削除を保留し、実害はない。恒久対応は `DW-O09` から変更なし (「hit 0 件を pin なしとしない」の適用先に**走査対象の絞り込み**を加える: 参照走査は binary 以外の全 tracked file を対象にし、allowlist で絞った走査の 0 件を根拠にしない。同 wave の段 6 review は import graph 側でも親 package `__init__.py` への暗黙辺の欠落を見つけた — 「静的走査の 0 件」は削除の十分条件ではなく、削除 prompt の自己検査を常に併用する)。原本 `output/insights/2026-09-19/dw-dead-code-inventory/README.md` §1。
