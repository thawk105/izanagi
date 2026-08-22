---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-t1472-provider-init-indeterminate
seq: 2
---

## 新規

### {{F:message-file-preflight-does-not-narrow-merge-paths}}. commit 前 provenance preflight が merge の path 集合を combined diff まで絞らず偽赤を出す [検査の非対称] [偽赤]

- 事象: [T-1472] wave が受入投入前に local main (40 commit) を取り込んだ merge は競合なしの
  自動 merge で、両親がともに `orchestrator/tests/test_p3_autonomous_workload_trial.py` を
  変更していた (main 側 = T-1458 が 7003 行付近の monkeypatch 2 件を削除、wave 側 = 8043 行
  以降へ新規 test 4 本)。この merge に対し `tools/check_ai_provenance.py --message-file` は
  `実装面に Codex role=author がない — paths=orchestrator/tests/test_p3_autonomous_workload_trial.py`
  で rc=1 を返した。同じ merge を commit した後に**権威である既定 full-history 監査**を
  `--range` で走らせると「4 件、違反なし」を返した。実測の内訳は
  `git diff-tree --cc <merge>` が空、`git diff-tree -c --name-only <merge>` が当該 file を
  1 件返す、である。
- 根本原因: commit 済み merge の path を決める `_commit_paths()` は、各親からの変更 path の
  積集合を候補にしたうえで `_combined_diff_paths()` (`git diff-tree --cc -p` の patch 本体が
  空でない path だけを残す) で絞り込む。一方 commit 前の `_message_file_paths()` は
  `MERGE_HEAD` 由来の親集合から積集合を作るところで終わり、この絞り込みを持たない。
  dense combined diff は「全 hunk がいずれかの親と一致する」merge を空にするため、
  両親が同じ file の重ならない領域を変更しただけの merge では 2 経路の判定が割れる。
  T-1479 が `_commit_paths()` を pairwise 積集合から combined diff 基準へ変えたとき、
  `--message-file` 経路が追随しなかった consumer 取り残しである。
- near miss: `DW-STOP` は「検査が赤なら止める」と定めるため、preflight の赤をそのまま
  受け取ると wave が止まる。逆に preflight を通すために merge message へ実体のない
  `role=author` を書けば帰属の捏造になる — F120 が「選ばなかったのは正しい」と記録した
  選択肢そのものである。本 wave は 2 経路の権威関係を実測で切り分け、preflight の赤を
  理由に author 行を書かずに済ませた。
- 恒久対応: `docs/ai-provenance.md` の「commit 前の確認」が既に
  「既定 full-history を権威とする」と定めており、**merge commit で 2 経路が割れた場合は
  この権威規定が preflight に優先する**。`_message_file_paths()` を combined diff 基準へ
  揃える checker 是正は実装面の変更であり本 wave の scope 外のため、裁定パッケージとして
  ユーザーへ返す (段 8 裁定)。
- 再発検知: merge の preflight が赤になったら、`commit -F` の後に
  `check_ai_provenance.py --range <main>..HEAD` を走らせ、`git diff-tree --cc <merge>` の
  空・非空と突き合わせる。非 merge commit では staged path と commit path が一致するため
  この差は生じない。

## supersede 追記

- F120 **supersede: 2026-08-23** — 派生節の「両側が同じ実装面ファイルを変更していると merge commit 自体が D95 で赤くなる」は現行 checker では一般には成り立たない。dense combined diff は全 hunk がいずれかの親と一致する merge を空にするため、競合なしで領域が重ならない merge は full-history 監査を role=integrator のみで通る ([T-1472] 実測)。赤になるのは combined diff の patch 本体が残る merge (競合解消を伴うもの等) である。
