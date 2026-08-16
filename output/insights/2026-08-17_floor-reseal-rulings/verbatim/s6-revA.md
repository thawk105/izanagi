所見はゼロ。blocker / major / minor はありません。

検査結果:

- index の contract 単位拒否は撤去済み。組単位拒否は [s8b_floor_campaign.py:748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:748) に残る。
- issuer は同一組を [s8b_floor_campaign.py:956](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:956) で writer 前に拒否する。既存 exact path を含み、`artifact=` は出さない。
- 同一 contract・新 pin の正例は [test_s8b_protocol_builder.py:636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:636) で発行成功まで検査される。
- resolver は HEAD 版と関数 bytes の SHA-256 が一致した。`FROZEN_MANIFEST`、`certified_writer_admission.py` に差分はない。
- 新しい束縛機構・恒真ゲート・skip・xfail・テスト削除はない。反転 3 本も必要な拒否 assert を別の検査へ置換しており、過剰な弱体化はない。

変異の検出力:

- (i) `_index_protocol_record` の組単位一意性を削除すると、[test_s8b_protocol_builder.py:986](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:986) が例外不発で赤になる。
- (ii) 発行前 pair 拒否を削除すると、[test_s8b_protocol_builder.py:688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:688) が artifact 生成まで進み赤になる。[同:661](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:661) も writer 呼出しを検出する。
- (iii) create-only writer を上書き可能にすると、[test_s8b_protocol_builder.py:242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:242) の二回目書込み拒否が不発となり赤になる。

`_admit_floor` の今日の受理 bit も不変である。現在 ever-active な Pegasus contract は g1 のみなので、新たに index を通る同一 contract・異 pin の複数 record は resolver の `count != 1` 分岐 [s8b_floor_campaign.py:896](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:896) で引き続き拒否される。拒否層が index から resolver へ移るだけである。

判定: **GO**

## 総括

裁定の 5 条件からの乖離は見つからなかった。  
新設 pair gate は到達可能で、writer 前拒否として実効性がある。  
指定された 3 変異はいずれも赤にするテストが存在する。  
既存テストの不当な弱体化と、今日の admission 受理集合の変化もない。  
pytest は指示どおり実行していない。