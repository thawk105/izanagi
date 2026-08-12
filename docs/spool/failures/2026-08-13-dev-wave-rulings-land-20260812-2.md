---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-rulings-land-20260812
seq: 2
---

## 新規

### {{F:wave-side-fragment-deletion}}. 既 fold の fragment を wave 側で削除して land が rc=26 で止まった — fold の dry-run は緑のまま [手順漏れ]

- 事象: 古い 3 branch の裁定 fragment を land する wave で、`spool_fold.py --dry-run` が
  `receipt-replay` を出した既 fold の fragment 2 本を `git rm` して独立 commit にした。
  dry-run はその後 rc=0 (`status=planned`) になり、`check_docs.py` も rc=0 だったが、
  `dev_wave_land.py` が `rc=26` `status=fold-failed`
  `reason=landed-fold-owned-path` で拒否した。main は 1 bit も動いていない。
- 根本原因: **fragment path の削除は fold だけの署名**であり、land は landed 区間の各 commit を
  `_landed_fold_output_path` で検査して弾く (F82 が定めた署名 2 条件の片方)。gate は正しく発火した。
  誤りは wave 側にあり、「不要な fragment を消す」という発想そのものが fold の役を奪っていた。
  `spool_fold.py --dry-run` は fold の意味論 (replay・遷移対象・base) だけを見て git 履歴の署名は
  見ないため、**dry-run の緑は land の緑を含意しない**。この非含意が見えにくさの本体である。
- 恒久対応: 不要な fragment は削除せず**最初から持ち込まない**。branch を main から作り直し、
  `git merge --no-ff --no-commit <branch>` の後 commit 前に `git rm` して、除外を merge commit 自身の
  中で完結させる。land の `_landed_commit_diff` は親が 2 つで trusted が 1 つの commit では
  trusted な main 側の親とだけ差分を取るため、merge commit の差分は「追加のみ」になり通る。
- 再発検知: land 前に `git diff --name-status <tested-main>..<tip>` を取り、`D` で始まる行の path が
  `docs/spool/**` の fragment に当たらないことを確認する (当たれば rc=26 が確定しているので
  land を投入しない)。`docs/spool/FOLDED.md` の `M` も同じ扱い。ただしこの累積差分検査は
  必要条件でしかない — 同 land が commit 単位でも検査するため、{{F:chained-old-branch-merge}} の
  条件も併せて満たす必要がある。

### {{F:chained-old-branch-merge}}. 古い branch を順に merge すると 2 本目以降で land が止まる — 親が 1 つも trusted でない merge は両親と差分を取る [受理集合の過剰縮小]

- 事象: 古い 3 branch を main 基点の wave branch へ**順に** merge したところ、1 本目の merge commit は
  通り、2 本目と 3 本目が `landed-fold-owned-path` で違反になった。違反内容は
  `M docs/spool/FOLDED.md`。累積差分 (`main..tip`) は追加のみで、`FOLDED.md` は 1 byte も変わって
  いない。land は `rc=26` で 2 度止まった。
- 根本原因: `_landed_commit_diff` は merge commit の親のうち **tested main の祖先であるもの**を
  trusted とし、trusted がちょうど 1 つのときだけその親との差分に絞る。順に merge すると 2 本目以降は
  第 1 親が自分の直前 commit (main の祖先でない)、第 2 親が古い branch tip (同じく祖先でない) となり
  **trusted が 0 個**になる。この場合は両親と差分を取るため、古い branch 基点以降に main で起きた
  fold の署名を wave の変更として読んでしまう。F82 の 3 度目の再発で `trusted_main_cutoff` が
  入ったが、救われるのは trusted が 1 つ以上ある形だけで、trusted 0 の連鎖 merge は残っていた。
- 恒久対応: 複数の古い branch を取り込む wave は、**main から 1 つの merge commit で同時に取り込む**
  (`git merge --no-ff --no-commit <b1> <b2> <b3>`)。main を唯一の trusted な親とする形にすれば
  差分は追加のみになる。fragment の除外・編集も同じ commit の中で済ませる。
- 再発検知: land 前に `git rev-list --reverse <tested-main>..<tip>` の各 commit について、親が 2 つ
  以上あるなら少なくとも 1 つが `git merge-base --is-ancestor <parent> <tested-main>` を満たすことを
  確認する。満たさない commit が 1 つでもあれば land は必ず止まる。
