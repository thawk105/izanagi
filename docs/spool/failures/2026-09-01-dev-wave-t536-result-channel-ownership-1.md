---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t536-result-channel-ownership
seq: 1
---

## 新規

### {{F:acceptance-merge-tree-race}}. 受入走行中の親の checkout が待ち手の merge に混ざり、台帳を巻き戻す merge が無検出で成立した [手順漏れ] [恒真ゲート]

- 事象: 受入 command を投入した直後、親が spool の base digest を取るため同じ作業ツリーで
  `git checkout main -- docs/` と `git checkout HEAD -- docs/` を実行した。受入待ち手は
  その裏で post-claim merge を進めており、両者が競合した。出来上がった merge commit は、
  第 2 parent が local main そのものであるにもかかわらず、**main 側の worklog・decisions・
  failures・FOLDED の更新を巻き戻し**、main にだけ在る archive file だけを含む混成になっていた。
  land していれば他 wave の台帳記録を消していた。
- 根本原因: `DW-M05` は変異走行について「変異中は親の編集と worktree へ書きうる子の起動を止める」と
  定めるが、受入走行についての同じ規律が無かった。親は「digest の借用は読み取りに近い」と
  暗黙に例外扱いした。`git checkout <ref> -- <path>` は index と作業ツリーの両方を書く。
- **どの gate も捕まえなかった。** 変異走行の同型 (F666) は共有木の事後検査が rc=125 で中止する。
  受入側には対応する検査が無く、merge は正常に完了し、tree は clean で、
  親が merge commit と main を自分で diff するまで気づけなかった。
- 恒久対応: `DW-O27` へ「受入 command の稼働中は親が作業ツリーを触らない。台帳 digest の借用は
  投入前に済ませる」を追記した。本 wave では壊れた merge を捨てて実装 commit へ戻し、
  記録 commit を受入より前に置く順序へ組み直した。
- 再発検知: 現時点では機械検査が無い。親が受入後の tip について
  `git diff <tip> <merge の第 2 parent> -- docs/` が空であることを確かめるのが最も安い照合である。
  第 2 parent が現 main と一致する場合、この diff が空でなければ混成である。

## 再発

### F45

- **再発: 2026-09-01** — 段 3 敵対相談の 1 本が
  `This content was flagged for possible cybersecurity risk` で rc=1・出力 0 bytes になった
  (49 model call・1358 秒を空費)。親 prompt が「誤った緑を作る経路を手順として具体的に書け」と
  求めていた。受理条件を 1 つずつ列挙させ、条件ごとに「親だけが用意できるか」を判定させる
  検査の語彙へ書き直して再投入し、通った。**5 回目である。**
  `DW-S03` が「攻撃させる」と指示したままだったのが根本原因なので、同節を「検査させる」へ
  是正し、語彙の注意を 1 行加えた。
