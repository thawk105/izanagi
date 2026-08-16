実装を完了しました。dev-wave 段 5 の境界に従い、commit、`git add`、docs 編集、凍結成果物の操作はしていません。

変更ファイル:

- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:742) — index の contract 単位拒否を削除し、issuer を同一組の発行前拒否へ変更。
- [test_s8b_protocol_builder.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:636) — 指定された 3 本を反転・改名し、legacy 組衝突と resolver `count=2` の 2 本を新設。

変更前後の挙動:

- 変更前: 同じ `contract_sha256` の record は pin が異なっても index と issuer の双方で拒否。
- 変更後: 同じ contract、異なる pin の組を index と issuer が受理し、導出 path へ発行可能。
- 同一 `(contract_sha256, ccbench_pin)` は引き続き拒否。issuer は writer 呼出し前に停止し、既存 record の exact path を通知します。
- index の既存「同一組が複数ある」分岐は bytes 不変です。
- resolver は bytes 不変で、同じ現行 contract の record が 2 件あれば引き続き `count=2` で fail-closed になります。
- `FROZEN_MANIFEST` と `output/s8b-freeze/` は無変更です。

静的な波及確認:

- `certified_writer_admission.py` は未変更の resolver を利用するため、同一現行 contract が 2 件ある状態では admission が停止します。
- CLI の `reseal_protocol` と index 表示は、新しい同一 contract・異 pin の受理集合を観測します。
- 共有 fixture `_init_reseal_protocol_repo` は変更しておらず、利用箇所は同じテストファイル内だけです。
- `test_campaign.py` の実 admission 回帰 3 本は未変更です。
- 改名対象 nodeid を固定する live meta-test は見つかりませんでした。歴史 insight 内の旧 nodeid は記録なので変更していません。

検査状況:

- `python3 -m py_compile` 成功。
- `git diff --check` 成功。
- resolver と HEAD 版の byte 比較一致。
- 変更ファイルは上記 2 本だけ。
- pytest は指示どおり未実行です。テストは実装済み・未実走であり、緑とは報告しません。

## 総括

contract 単位の過剰拒否を撤去し、組単位の一意性だけを維持しました。  
同じ contract の新 pin は発行でき、同一組の再発行は writer 前に拒否されます。  
resolver、凍結 manifest、既存凍結 bytes、consumer test は変更していません。  
段 5 実装は完了し、pytest による実走は親へ引き継ぎます。