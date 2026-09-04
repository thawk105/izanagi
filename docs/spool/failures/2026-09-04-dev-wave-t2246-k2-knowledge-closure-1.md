---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-04
wave: dev-wave-t2246-k2-knowledge-closure
seq: 1
---

## 新規

### {{F:merge-of-dev-wave-docs-blocks-codex-children}}. main 取り込みが dev-wave 文書を含むと、merge 中は Codex 子が全段で起動できず、規約どおりの競合解消ができない [手順漏れ]

- 事象: 段 6 で local main (87 commit) を取り込んだところ `orchestrator/campaign/p3_s4_loop.py`
  に競合が出た。`DW-O17` は「非 ff は `--no-ff --no-commit` → 競合解消 → commit」と定め、
  D95 は実装面の解消を Codex `role=author` に要求する。そこで merge 進行中の作業ツリーで
  Codex 子を起動したところ、段によらず rc=2 で拒否された
  (`NG: docs/dev-wave/operations.md: working tree が authority commit と異なる`)。
- 根本原因: 取り込んだ main 側が `docs/dev-wave/operations.md` を変更しており、
  merge が staged の間は working tree が authority commit と一致しない。
  `dev_wave_codex.py` の authority docs 検査は stage 非依存で全子を止めるため、
  **`DW-O17` の「merge 内で解消」と D95 の「実装面は Codex author」が同時に満たせない。**
- 恒久対応: 手順として次を採る。**merge を `git merge --abort` で一度戻し、clean な作業ツリーで
  Codex `role=author` に main 側の移設へ先回りで適合する差分を書かせ、それを commit してから
  merge し直す。** 本 wave はこれで競合を変数名 1 箇所まで縮め、その 1 箇所は wave 側の親の逐語と
  同一だったため親が機械置換した。実体は
  `output/insights/2026-09-04_t2246-k2-knowledge-closure/verbatim/s6-merge-adaptation.md`
  (Codex が書いた適合の逐語) と同 `s6-merge-audit.md` (合成監査)。
- 再発検知: merge 中に Codex 子が rc=2 で `authority commit と異なる` を出したら本 F を引く。
  `docs/dev-wave/` を変更する main を取り込む wave で必ず発火する。

### {{F:reused-done-file-reads-previous-run-rc}}. 再走で完了フラグの path を使い回し、走行中に前走の rc を読んだ [手順漏れ]

- 事象: 焦点走と受入走で、同じ runner script を再実行して同じ `.done` / log を上書きさせた。
  2 度とも走行中に前走の rc が残っており、「また失敗した」と誤判定しかけた。
  1 度目は焦点走 (前走 rc=1 が残存)、2 度目は受入走 (前走 rc=2 が残存)。
  いずれも process の実在と Pegasus request ID の照合で訂正した。
- 根本原因: `DW-O01` は「既存 `.done` を消去・再利用せず再投入を止める」と定めるが、
  **「再走時は path を変える」という具体形が無い**。同じ script をもう一度起動するという
  最も自然な操作で、規定の側からは見えない形で踏む。`docs/dev-wave/` は byte 予算に
  余裕がなく (1 文の追記で L1.5 footprint 予算を超過)、reference への具体形追記は見送った。
- 恒久対応: 再走のたびに `.done` / log / receipt の path を全て変える
  (`<name>-2.done` のように連番にする)。判定は `.done` の内容だけでなく、
  producer process の実在 (`kill -0`) と、走行 log 中の投入 ID の照合で確かめる。
- 再発検知: 待ち手が即座に戻り、かつ producer process が生存しているときは本 F を疑う。
