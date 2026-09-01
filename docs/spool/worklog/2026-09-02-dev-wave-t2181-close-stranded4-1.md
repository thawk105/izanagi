---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2181-close-stranded4
seq: 1
title: [T-2181] 取り残し branch 4 本をユーザー裁定で削除して閉じた — 削除前の tip は台帳にしか残らないので逐語で控えた (docs のみ、branch worktree-dev-wave-t2181-close-stranded4、実装面の差分ゼロにつき変異 matrix は DW-S04 の免除)
---

## 本文

- **ユーザー裁定で決着した。** 2026-09-02、取り残し branch 4 本を削除してよいという指示が出て、
  `git branch -D` で 4 本とも削除された。3 度の独立判定 (2026-08-29 の archive エントリ 1094、
  2026-09-01 の insight、2026-09-02 のエントリ 1180) がいずれも「取り込む commit は 0 件」と
  結論しており、削除は内容を失わない。裁定の本体は {{D:stranded4-user-deletion}}。
- **削除は本 wave が行ったのではない。** 本 wave は削除済みの状態を実測で確認し、記録だけを行った。
  `git branch --list` で 4 本の不在を、`git merge-base --is-ancestor` で 4 tip が main から
  到達不能であることを確認した。
- **削除前の tip はここにしか残らない。** 控えは repo 外の
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-stranded4-recheck-20260902/deleted-branches.md` に
  あるが、これは job の作業領域であって repo の成果物ではない。到達不能 commit は自動 prune の
  対象で、prune 後は SHA を再導出する手段が無い。よって台帳へ逐語で移す。

  | 削除された branch | 削除前 tip |
  |---|---|
  | `worktree-dev-wave-t1933-reconciliation` | `6f5de08ce103e944a0f0bc633b8b4fb0f8cca1d6` |
  | `worktree-dev-wave-acceptance-fastest` | `7da26497763e53fca32301c0b9990b9fce989b42` |
  | `worktree-dev-wave-t1933-acceptance-longest-node` | `209698aedc0bec681eb4f097a93da9e1d7cd9e88` |
  | `worktree-dw-c01-websearch-ruling-20260827` | `df20d363146e1b88dc7813f78946d594c2be38cc` |

- **到達不能になった 14 commit** (`check_branch_rescue` の `deletion_loss_closure`) は
  `df20d3631` `0c2a72713` `85ab06c3c` `ea2a50b26` `f4e762162` `209698aed` `60c758a86`
  `2ffb32a0e` `2aa85c451` `1bafd884a` `5d4393233` `7da264977` `8b677a197` `6f5de08ce`。
  `loss_possible_not_before` は `6f5de08ce` だけ 2026-09-27T08:22:14Z、他 13 件は
  2026-09-01T21:52:23Z で**既に経過している**。復元は `git branch <名前> <SHA>` だが、
  期限を過ぎた 13 件は object が消えていれば復元できない。本 wave の実測時点では 4 tip の
  object はまだ存在していた。
- **失われるのは停止した wave の履歴だけである。** fork 点からの file 閉包 distinct 22 path の
  blob を main の全 blob 索引と照合した結果 (エントリ 1180 で land 済み) は、main に無いのが
  fold が消費して削除した spool fragment 2 件だけで、その本文は D1260 と F606 の 2026-08-28
  再発文として canonical に逐語で実在する。main に blob として残っていなかった原文 3 件
  (`bee4d47fd` `c778863e1` `e94c0ea18`) は insight の `sources/` に保存済みである。
- **insight は改訂しなかった。** `output/insights/2026-09-01_stranded4-branch-recovery/README.md` の
  「branch は削除しない」は判定日 2026-09-01・base main `24014bdb2` 時点でその wave が何を
  したかの記述であって、現況への主張ではない。時点の事実は後から変わらないので追記しない
  (CLAUDE.md 規律 7)。
- **ref を残す限り毎回挙がる、という T-2181 起票時の懸念は削除で解消した。** ref だけを見る棚卸しが
  この 4 本を回収候補に挙げ、blob 照合まで進んで初めて 0 件と分かる往復は、もう発生しない。

## 次の一手差分

### 完了

- [T-2181] 取り残し branch 4 本はユーザー裁定で削除され、削除前 tip と到達不能 14 commit を
  台帳へ控えた。3 度の独立判定はいずれも取り込み 0 件で、内容は main に着地済み。
  remaining: none
  base: dd108dbf33e7342e8136d4a9efb8fc75b4cffe5c5926c6586492ba77c70c457d
