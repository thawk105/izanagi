---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t2396-a1-receipt-oslink
seq: 3
---

## 新規

### {{F:hardlink-publish-aliases-staging-and-destination}}. hard link 公開への切替えが、staging と宛先を同一 inode にして撤去処理へ受領証削除の経路を開きかけた [恒真ゲート] [手順漏れ]

- 事象: 受領証の公開を `renameat2(RENAME_NOREPLACE)` から `os.link` へ替える段 2 プランは、
  公開成功後に staging を撤去する経路を足しつつ、撤去側の `(st_dev, st_ino)` 照合を
  **rename 時代のまま**据え置いていた。段 3 の敵対相談が、公開後に第三者が
  `unlink(staging)` と `rename(destination, staging)` を行うと照合が通り、
  撤去が受領証の最後の link を消して**例外なしで成功が返る**並びを実証した。着地前に閉じた。
- 根本原因: rename では公開後に staging 名が消えるため撤去処理そのものが存在せず、
  identity 照合は「自分が作った staging か」だけを見ればよかった。hard link は
  **2 つの名前が同じ inode を指す**ので、同じ照合が「宛先を staging 名へ移したもの」も
  通してしまう。**公開 primitive を替えると、その primitive に紐づく不変条件も替わる**という
  点がプランから抜けていた。既存テストも rename 時代の性質しか固定していなかった。
- 恒久対応: {{D:a1-published-receipt-cleanup-contract}}。公開済み経路の撤去は宛先の存在と
  identity 一致を前提にし、不成立なら unlink せず fail-closed で止める。
  正例・負例は `orchestrator/tests/test_paper_story_a1_job_contract.py` の
  `test_published_receipt_cleanup_preserves_same_inode_after_destination_move` と
  `test_published_receipt_cleanup_preserves_staging_when_destination_disappears`
  が持ち、変異 `t2396.m01a` / `t2396.m01b` が両 guard を単独で殺せることを実測した。
- 再発検知: 公開・施錠・claim の primitive を差し替える wave は、**差し替え前の primitive が
  暗黙に与えていた不変条件**を 1 つずつ書き出して、差し替え後も成立するかを見る。
  `os.link` のように 2 つの名前が同じ inode を指す形へ移す場合は、identity 照合が
  「どちらの名前か」を区別できなくなる点を必ず攻撃面に入れる。

## supersede 追記

- F870 **supersede: 2026-09-08** — 恒久対応が指す実装が着地した。group submission receipt と `complete` の completion receipt は完成した staging への `os.link` で公開し、materialize の directory 公開は現行のまま残す ({{D:a1-receipt-file-publish-form}})。
