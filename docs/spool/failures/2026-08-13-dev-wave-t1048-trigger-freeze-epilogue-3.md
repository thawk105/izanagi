---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-t1048-trigger-freeze-epilogue
seq: 3
---

## 新規

### {{F:mutation-shared-tree-postcheck}}. 変異本走の共有木事後検査が、走行完了後に全結果を捨てさせた [手順漏れ]

- 事象: `tools/mutation_worktree.py` の本走中に、親が段 7 の insight README を worktree へ書いた。
  3 変異と baseline はすべて隔離 worktree 側で完走し、結果 JSON も `KILLED` / 期待 node 完全一致で
  書かれたが、最後の**共有木の事後検査**が
  `共有木の事後検査に失敗: source/main 共有木の観測 bytes が変化した` で `rc=125` を返し、
  run 全体が中止扱いになった。1 走を捨てて clean tree で再走した。
- 根本原因: F106 と同一で、長い走行を待ち時間とみなし repo 内で別の段の作業を進めたこと。
  本 wave の親は F106 の再発を 5 件読んだうえで踏んでいる。
- 恒久対応: F106 の恒久対応 (`DW-O19` の「本走は統合 commit 後に限る」、投入から結果取得までは
  commit・stage・tracked file 編集を行わない、待ち時間には repo 外の作業だけを置く) をそのまま適用する。
  本エントリは**検知点が 3 つ目である**ことを顕在化する — harness preflight の `rc=2` (走行前)、
  テストの偽の赤 (走行中)、に加えて **`mutation_worktree.py` の事後検査 (走行後)** がある。
  事後検査は全 run を消費してから落ちるため、3 者のうち最も高くつく。
- 再発検知: `mutation_worktree.py` の rc が 125 で、結果 JSON 自体は完全に書かれている場合。
  ログ末尾の `共有木の事後検査に失敗` が literal の目印になる。

## 再発

### F106

- **再発: 2026-08-13** — [T-1048] trigger 凍結領域拡大 wave。**6 度目**。変異本走の走行中に親が
  段 7 の insight README を worktree へ書いた。過去 5 件と違い、harness preflight でも走行中の
  偽の赤でもなく、`mutation_worktree.py` の**走行後の共有木事後検査**が捕まえた (`rc=125`)。
  全 4 run を消費してから中止されるため損失が最大になる点が新しい情報である。詳細は
  {{F:mutation-shared-tree-postcheck}}。恒久対応は F106 のままで、
  待ち時間には repo 外の job directory だけを触る。
