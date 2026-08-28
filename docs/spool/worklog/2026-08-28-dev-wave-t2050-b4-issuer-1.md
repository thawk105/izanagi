---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: dev-wave-t2050-b4-issuer
seq: 1
title: [T-2050] B-4実走前issuerを実装し、予定attempt・seed・result前点検・receiptを局所publicationへ束縛した (コード + tests + insight、branch worktree-dev-wave-t2050-b4-issuer、変異matrix = baseline PASSED・5/5 KILLED)
---

## 本文

- B-4専用 `p3_b4_prerun_issuer.py` と専用testを新設した。予定attempt全列、一度だけ取得する32 byte seed、既存ledger APIが作るregistry / manifest、全予定result path、final receiptを同じcommitmentへ束縛し、strict loaderで全edgeを再検証する。
- reviewの元8 must-fixに加え、焦点reviewが見つけたloader側fixed-artifact衝突、planned result同士の祖先関係、M1件数maskを同じD95 fix単位で閉じた。既存testの期待を削除・反転・skipせず、issuer焦点走29 passed、既存ledger + campaign source列挙meta 32 passedを得た。
- 変異matrix初回はbaseline PASSED、M1〜M3 KILLED、M4 / M5 MISMATCH。初回ledgerをerratumとして残し、M4のexact赤を3 nodeへ、M5をtemp cleanupの意味を保つ上書き変異へ再照準した。再登録後はbaseline PASSED、M1〜M5のexpected / failed node集合完全一致、5/5 KILLED、SURVIVED 0、MISMATCH 0。構造化証拠は `output/insights/2026-08-28_t2050-b4-prerun-issuer/`。
- 回収時のindexはrepo外 `pre-fix.patch` とSHA-256 `4366481ac47067db49a072f8f3d40b53be171e4bde7742700cc0a9b6fa1249ac` でbyte一致し、停止workerのpartial working差分とは分離して保全した。`f45_missing_output` の部分成果を採用せず、新しいD95 fix workerへ戻した。
- T-2001が所有するconsumer、README、verbatim planは起動時の未コミット3 pathから変更せずread-onlyとした。T-2050の所有は新規issuer/testと本記録だけで、重複0。
- formal launcher / raw producerへの必須配線、外部権威母集合、別root再発行拒否、署名・外部pin、別campaign、汎用authority framework、並行result writer排他、B-4正式実走はscope外。result不存在はpoint-in-time検査であり、formal全経路の結果前発行やfile-drawer閉鎖を主張しない。
- 実装commit `80da45e6f` 後のfull-history provenanceは6870件・新規違反なし。final acceptanceは本記録commit後のtipで実行するため、このentryには未実施値を書かない。

## 次の一手差分

### 完了

- [T-2050] B-4専用の実走前issuerを実装し、局所publicationの予定attempt全列・seed・result path・receipt束縛と検出力を閉じた。
  remaining: none
  base: 7f05803a0ca67af472bb1ad5b359970fc9cc86347c0b7154b44eb8da7ab23bbb
