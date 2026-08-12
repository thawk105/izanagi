---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t886-rollout-fastpath
seq: 5
---

## 新規

### {{F:known-violation-ledger-count-pinned-literally}}. 生きた台帳の件数を literal 固定した検査が、承認済みの追加で受入を止めた [恒真ゲート] [誤前提]

- 事象: ユーザー裁定で `KNOWN_PROVENANCE_VIOLATIONS` へ entry を 1 件足したところ、
  件数を **34 で literal 固定**していた検査 2 本が受入全走で赤になった
  (`2 failed / 9781 passed`)。片方は**関数名にも件数が入っていた**
  (`..._is_exactly_thirty_four_literal_entries`)。production は正しく、テストの期待値が古い。
  受入全走 1 回と受入 lease 1 サイクルを空費した。
- 根本原因: 台帳は**承認のたびに必ず伸びる生きた量**であり、件数の完全一致を固定すると
  「正常に伸びたこと」を赤として報告する。D316 が別の台帳
  (`docs/decisions.md` の supersession 走査) で同じ構造を裁定済みだが、
  **provenance 台帳側には適用されていなかった。**
- **これは D316 の 2 例目である。** 異なる producer / consumer で独立に再現したため、
  `DW-G03` の族一般化条件が成立する。台帳を literal で固定する検査は族として見直す。
- 恒久対応: **未実施。** 検出力の本体 (entry の内容一致) を保ったまま件数固定だけを外す形は
  正しさゲートの受理集合を変えるため、独立の敵対検証つきで裁定へ返す
  ({{T:apply-d316-to-provenance-registry-test}})。当面は追加のたびに件数と literal を
  同じ変更単位で更新する。
- 再発検知: 台帳へ entry を足す変更で受入が赤になり、赤の nodeid が件数 assert を含むこと。
  **追加前に `grep -rn "== <現件数>" <対象 test>` で件数 pin を網羅すれば手前で出せる。**

### {{F:submodule-pointer-drift-after-merge}}. main 取り込みが submodule pointer を変えても working tree が追随せず、受入が起動前に止まった [手順漏れ]

- 事象: 受入全走が `stage=prerun-clean rc=70` で停止した。`git status` は
  ` M external/ccbench` を示し、working tree は `d706650c`、index の記録は `511c9538` だった。
  wave 開始時に `git submodule update --init --recursive` を実行済みで、その後の main 取り込みが
  pointer を進めていた。**走行前に止まったので損失は小さいが、lease 待ちを 1 周やり直した。**
- 根本原因: `git merge` は superproject が記録する submodule commit を更新するが、
  **submodule の working tree を checkout し直さない**。初期化だけを手順に書いていたため、
  取り込みのたびに drift しうることが手順から抜けていた。
- 恒久対応: `DW-O20` に「取り込み後・受入投入前に `git submodule update --recursive` で
  記録へ揃える」を追加した。`deinit` は使わない方針は不変。
- 再発検知: 受入が `prerun-clean` で止まり `git status` に ` M <submodule path>` が出ること。
