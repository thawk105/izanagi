# [T-2871] 段 6 裁定 5 (親) — 焦点再レビュー (codex/rereview.md、HEAD d7161a2a1)

- R1〜R14: 再レビューの対応表で R6・R8 (不採用) を除き closed。driver の受理集合と正しさゲートの順序は fix-1〜4 で不変、代役は実 `_authorize_measurement`・`acquire_claim`・`check_reservation`・`authorization_session`・admission・auditor gate を通り、`run_campaign` spy は実物へ委譲 (再レビュー「機構を実物で通っていることの根拠」)。
- 新所見 N1 (再レビューは must-fix): T1 は系列 digest が「2 本目の計測 WAL 由来」か「1 本目由来」かを区別できない (両 process が同じ proposal・同じ候補 token)。
  - 裁定: **real (検査の弁別力の不足) だが must-fix ではない・scope 外。** digest の admitted view は、その pair の候補を評価したのと同じ `evaluation_layout` (= その iteration の計測 layout) から作られ、前 iteration の計測 dir を読むコード経路は無い (p3_s4_loop_policy.py の `drive_iteration`)。番号の取り違えは M1・M2、系列 dir への取り違えは M5 の変異で押さえる。残るのは存在しない経路の仮想欠陥で、依頼が scope 外とした「仮想リスク向けの検査追加」に当たる (DW-G05)。insight の scope 外に記録する。
- DW-O16 の巡数: レビュー所見への fix は fix-1 の 1 巡。fix-2〜4 は焦点走 (実機) の赤への対処で、上限の別枠。
