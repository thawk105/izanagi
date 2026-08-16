---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1140-t330-claim-authority
seq: 1
title: 生存プロセス単位の claim 排他と submitter receipt authority を実装する (コード + テスト、branch worktree-dev-wave-t1140-t330-claim-authority)
---

## 本文

- ユーザー裁定 (2026-08-16 全件第 2 回 #4 / #5) に従い [T-1140] 択 (a) と [T-330] 択 (a) を
  1 wave で実装した。裁定の設計材料は前 wave が実装差分ゼロで返した再裁定パッケージである。
- **保証範囲は同一ノード・同一 boot・共有 out_root に限る。** protocol 単位の global な排他は
  実装していないし、成立もしない。別 boot_id の claim は生存を判定できないため通す
  (裁定どおりの明示的 fail-open)。単独性を証明したとは書けない。
- 親が brief 前に実測して裁定の前提を検算した。(1) `/proc/<pid>/stat` 第 22 field は
  他ユーザーの process でも読め、同一ノードの生存判定は成立する。(2) 実 floor receipt 3 件が
  `output/env/pegasus/floor/attempts/submissions/<nonce>/submit-receipt.json` に実在し、
  新 gate の発火面がある。(3) **同名識別子の二義化**を発見した — calibration 系 receipt
  (`pegasus-submit-receipt/v1`) は `submission_nonce`、floor 系
  (`pegasus-floor-submit-receipt/v1`) は `nonce` を持つ。新 leaf は schema_version を先に
  検査してから field を読む。(4) Python 側の receipt 照合は
  `certified_writer_admission._admit_floor` に既存だったが、呼び手が wrapper 経由の CLI だけで、
  「wrapper を通らない呼び手には無い」ことを確認した。
- **oracle は新 gate の発火面ではない。** 親の実測により `campaign_id = block["campaign_id"]` は
  manifest 従属であり、preimage から campaign_id を外しても claim identity と protocol digest が
  1 対 1 のままだと確定した。oracle は claim schema 追随のみとし、receipt gate は配線しない。
  検出力にも計上しない。詳細は {{D:claim-liveness-exclusion-scope}}。
- receipt gate を floor 経路に限ったのは、段 3 の敵対相談 2 本が**独立に**
  「oracle を起動して floor receipt を運ぶ実 producer が repo に存在しない」を blocker として
  挙げたためである。配線すれば oracle の正当な実行が常に拒否される。
- 段 3 の敵対相談が blocker 2 件を実装前に倒した。うち 1 件 (`Path.glob()` が権限拒否を
  空集合へ変え post-scan が恒真化する) は親が実測で確認した — Python 3.10.12 の
  `pathlib.py:459-460` は `except PermissionError: return` で空を返し、`os.scandir()` は送出する。
  {{F:glob-swallows-permission-error}} に記録した。
- 段 6 の敵対レビュー 2 本が blocker 1 件 (作成途中の claim record を破損と誤認し、
  無関係な別 protocol の同時投入まで拒否する) と major 3 件を出し、fix で閉じた。
- 変異検査の途中で、本 wave が新設した POS-8 node が
  **production が保証しない期待**を書いていたことが判明した。post-scan の双方拒否は保証されず、
  先に拒否した側が終了すれば後続からは DEAD に見えて正当に通る。判定を
  「成功数は高々 1」+「全 owner 死亡後に次が通る」へ訂正した。{{F:postscan-both-reject-overclaim}}。
- 段 5・段 6 の実装子はいずれも sandbox 内で `qstat -Q` preflight が rc=1 となり、
  pytest を 1 node も実走できなかった (rc=16)。緑はすべて親が bounded local または
  dispatch 経由で実測した値である。
- ログインノードのメモリ逼迫 (回収不能 8.2GiB) により、親も
  `test_s8b_oracle_driver.py` と `test_campaign.py` を bounded local で走らせられなかった。
  これらは受入全走と変異走行 (計算ノード) で確認している。

## 次の一手差分

### 完了

- [T-1140] claim record に必須 `protocol_digest` を持たせ、同一 protocol の claim があり
  持ち主が生存しているときだけ拒否する排他を実装した。生存判定は同一 boot_id かつ
  `/proc` の starttime 一致かつ state が `Z` でないの 3 条件で、pid 再利用と zombie は DEAD。
  claim root を列挙できない・`/proc` が読めない・record が破損している場合は fail-closed。
  release・stale 自動削除・期限切れ回収は従来どおり持たない。
  保証範囲は同一ノード・同一 boot・共有 out_root まで。別ノードの生死判定は次 wave (択 (c))。
  remaining: none
  base: 35eec9f605aefdf75e646b46269a8d936ce361a8ee78b0089b6aefa264cc1105
- [T-330] submitter 所有 receipt を「`PBS_JOBID` 束縛があるため恒真ではない」という理由付きで
  authority と認め、script SHA と nonce の照合を Python 側にも入れた。新 leaf
  `floor_submit_receipt.py` は site 判定・calibration・subprocess・環境変数直読みを持たない
  pure leaf で、`certified_writer_admission` も同 leaf の consumer にした。
  hostname は API 引数に持たせず、authority ではなく wrapper 側の drift 観測に留める。
  配線は floor 経路のみ。
  remaining: none
  base: e6e1d93d636aeca27fe118dfeb91411089d29f855d50ceac038ed6e63c4aadad
