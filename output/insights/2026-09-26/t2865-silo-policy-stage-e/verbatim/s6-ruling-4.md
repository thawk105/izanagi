# 段 6 裁定 4 巡目 — [T-2865] (2026-09-26、親)

入力: 焦点再レビュー 2 (`codex/s6-focus-2.md`、NO-GO、must-fix 2)。G3・G4 closed、F1・F3〜F9 と gate 順・auditor 上限・firewall は回帰なし (静的)。

| ID | 所見 | 判定 | 処置 |
|---|---|---|---|
| J1 | anomaly の `edges[].reasons[].key` に trace 由来の未検証文字列が残り coder 入力へ届く | **refuted (仮想リスク)** | trace は固定骨格の計装が出す。候補は policy-C++ v1 で文字列・pointer・外部名を持てず (構文検査と単独 TU compile)、trace へ文字列を注入する経路が無い。不正な key は verifier の integrity (`malformed_keys`) に数えられ、既に `verifier_digest.integrity` に載る。辺の key は規律 3 が求める「どの trx 間のどの依存か」そのものなので残す。仮想リスク向けの検証は足さない (依頼の scope) |
| J2 | `anomaly_count` は verifier が返した witness 配列 (既定最大 20) の長さで、全 cycle 数ではない | real / must-fix | `anomaly_count` を `witness_count` (verifier が返した witness の件数) に改名し、全 cycle 数は既存の `total_cycles` だと分かる形にする。表示の 8 件は witness の抜粋。s6-ruling-2 の G2 の「全件数」の記述はこの改名で訂正する (erratum) |

DW-O16 の焦点再レビューはこれが 3 巡目の fix。fix-4 の後の焦点再レビューを最終巡とし、なお NO-GO なら親が変異で裏取りして残りを裁定する。

変異 M-E16 (上限を外す) の期待 test は J2 の改名後の test に照準し直す。
