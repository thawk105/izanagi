---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-t1506-mocc-trace0
seq: 3
---

## 新規

### {{F:gate-hardening-blocked-the-measurement-path}}. 検査を強めた結果、計測 job が使う実 topology を塞いだ [恒真ゲート] [テスト代表性]

- 事象: TRACE=0 前処理同一性検査の不在証明を commit tree へ広げるとき、gitlink の coverage を
  証明できないなら停止する設計にした。この checker を呼ぶ計測 job
  (`tools/pegasus/mocc_trace_pilot.sh`) は submodule を初期化せずに
  `git worktree add --detach` した tree を渡すため、**その topology では checker が必ず
  rc=1 になり、TRACE=0 の workload が毎回 skip される**状態になっていた。
  段 6 の敵対レビュー 2 本が独立に指摘し、親が同じ topology を再現して実測で確認した。
- 根本原因: 2 つある。(a) 未初期化の directory へ `git -C <dir> rev-parse HEAD` を撃つと
  git は親 repository まで遡って解決するため、submodule の HEAD のつもりで superproject の
  HEAD を得ていた。(b) 「証明できないなら停止」は従来より強い要求を新たに課すものであり、
  submodule の中身が元々厳密な保証の対象外だった事実に照らして過剰だった。
  実装子が書いたテストは初期化済み submodule の topology しか覆っておらず、
  実 job の topology を代表していなかった。
- 恒久対応: {{D:mocc-trace0-gitlink-not-fatal}} が (a) を repository 境界の事前確認で塞ぎ、
  (b) を「確認できたときだけ確認し、できないときは coverage を主張せず進む」へ改める。
  限界は関数の docstring に明記する。手順面 (gate を強める変更では、その gate を呼ぶ実 script の
  topology を再現して実走する) は memory
  `git-c-on-uninitialized-submodule-escapes-to-parent` が正本
  — `docs/dev-wave/operations.md` の `DW-O13` へ足そうとしたが単節予算を超過して入らなかった。
- 再発検知: `orchestrator/tests/test_check_trace0_preprocess_identity.py` の
  `test_uninitialized_gitlink_directory_is_not_asked_to_resolve_parent_head` と
  `test_commit_tree_with_uninitialized_gitlink_worktree_is_accepted`。
  変異 M11 (repository 境界判定の除去) がこれを殺すことを実測で確認した
  (`mutation-ledger-final.json`)。

### {{F:ruling-premise-is-necessary-not-sufficient}}. 裁定が述べた因果を十分条件と読み、解除後の状態を測らずに着手した [手順漏れ]

- 事象: D673 は「trace ヘッダの include 行に旧版コメントが残る限り TRACE=0 の性能計測は
  一度も走らない」と述べていた。この主張自体は正しかったが、**その 1 行を直しても
  計測は走らなかった**。checker は別の gate (未知マクロ) で拒否し続けた。
  段 1 の brief は「1 行を直せば計測できる」を前提に scope を組んでいた。
- 根本原因: 裁定文の因果は必要条件を述べたものであって、十分条件の主張ではない。
  段 1 の前提実測が「その 1 行が拒否の原因である」ことまでしか測っておらず、
  「直した後に何が起きるか」を測っていなかった。
- 恒久対応: {{D:mocc-trace0-checker-wiring}} が実際の解除条件を確定させた。
  手順面は memory `ruling-premise-is-necessary-not-sufficient` が正本
  (段 1 の前提実測で解除後の状態まで probe する)。`docs/dev-wave/core.md` の `DW-S01` へ
  足そうとしたが L1 予算を 257 bytes 超過して入らないため、memory へ routing した
  ({{T:dev-wave-docs-budget-review}} が予算の独立審査を持つ)。
- 再発検知: 本 wave では job dir の `probe-wiring.py` と `probe-fullchecker.py` が
  解除後の状態を段 2 直後に実測し、scope の作り直し (brief v3、段 2 からの巻き戻し) を
  段 4 より前に発火させた。
