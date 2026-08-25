---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1239-branch-landing-check
seq: 2
---

## 再発

### F28

- **再発: 2026-08-26** ([T-1239] wave)。事前登録 10 件のうち 3 件が無効で、段 6 の敵対レビューが
  静的に実証した。M8 (blob 一致で path を要求) は tree entry の取得関数が常に要求 path を返すため
  比較する 2 つの path が恒等的に同じで、さらに後段が別 path の blob を再度拒否するので**完全に
  masking**されていた。M4 (merge を closure へ含める) は fixture の side commit が変異後も
  `indeterminate` を保つため verdict 上は masking され、proof-unit 集合の assertion だけが落ちる形で
  「merge-only を落とすと landed になる」という登録した単一理由になっていなかった。
  M2 (逐語層を landed の十分条件に戻す) はそのような合成式が実装に存在せず、変異点として成立しない。
  **今回の新しさは、事前登録の時点で実装が存在しなかったことである。**
  `DW-M01` は「同じ入力を拒否する層が前後に無いことをコードで確認する」と定めるが、
  新設 tool の wave では段 4 の裁定時にコードが無く、確認は規則名の水準でしかできない。
  親は登録を規則名で行い、実装後の段 6 で再照準した (M2 を取り下げ M2' を新設、M4→M4'、M8→M8')。
  恒久対応の追補 = **新設 tool の wave では、段 4 の事前登録を暫定と明記し、
  段 6 のレビューへ「事前登録変異の帰属が実装後も成立するか」を必ずレンズ項目として渡す。**
  本 wave はこれを prompt に明記して実施し、3 件の無効を実装前でなく実装直後に落とせた。

### F537

- **再発 (near miss): 2026-08-26** ([T-1239] wave)。**共有 main checkout の untracked 集合を
  掃除で書き換える経路が、除外設定の追加以外にもう 1 本あった** — `.codex/worktrees/` 配下の
  worktree 残骸そのものを撤去することである。親は t1563 系 11 本を退避し、その結果
  共有 root の `git status --porcelain=v1 --untracked-files=all` の出力行が 16 から 5 へ減った。
  `tools/mutation_worktree.py` の `_observe_shared()` は走行前後でこの stdout bytes の完全一致を
  要求するため、共有木を観測する変異が走行中であれば `shared_snapshot_matches=false` /
  `MUT_RC=125` で空振りしていた。**実害は出ていない** — 撤去直後に `pgrep -af` で確認したところ、
  走行中の変異は `tools/mutation_harness.py` を直接呼ぶ 1 本 (T-1434 の probe) だけで、
  これは `--repo` に自分の wave worktree を取り共有木を観測しない。`mutation_worktree.py` 由来の
  process は 0 本だった。**しかし親はこの確認を撤去の前でなく後に行った。**
  恒久対応 = memory `shared-untracked-set-preflight-before-worktree-retire` — 共有 main checkout の
  untracked 集合を変える操作 (worktree 残骸の撤去を含む) の直前に `pgrep -af mutation_worktree.py` で
  共有木観測の走行が 0 本であることを確かめ、撤去は削除でなく退避とする 5 点検査を記録する。
  再発検知: `shared_snapshot_matches=false` は既に `MUT_RC=125` で fails-closed に落ちるが、
  それは被害が出た後の検知である。事前の防壁は本エントリと当該 memory だけで、機械検査は持たない。
