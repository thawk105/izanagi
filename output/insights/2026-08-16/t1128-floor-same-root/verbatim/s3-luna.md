## 所見

1. [severity: must-fix] prebuild 失敗が閉じた `UNAVAILABLE` 経路へ接続されていない。

   実測では `build_cells` が捕捉するのは `_FloorOraclePreflightError` だけであり、`buildcache._run()` は `RuntimeError`、`build_v2()` は `BuildError` を投げる。  
   攻撃シナリオ（推測）は configure、target build、`mkdtemp()`、CCBench checkout のいずれかを失敗させる入力で、private failure artifact が無く、`OracleStatus.UNAVAILABLE` へ変換されない経路である。  
   [根拠 orchestrator/campaign/s8b_floor_campaign.py:2029-2037] [根拠 orchestrator/campaign/buildcache.py:1430-1431] [根拠 orchestrator/campaign/buildcache.py:1873-1889] [根拠 s2-plan.md:14,43-59]  
   提案: base 作成、checkout、configure、target build を段階別の閉じた detail code へ変換し、oracle・`build_fn` の呼出し回数 0、private `UNAVAILABLE` 記録、正確な `outcome` を負例で固定する。F309 の再発である。

2. [severity: must-fix] floor が実際の oracle `PASS` receipt を受理条件にしていない。

   実測では `prepare_cell` が `oracle_attempt` を生成する一方、floor は `genome`、`src_token`、CCBench root だけを使い、oracle attempt を保存も検査もしていない。  
   攻撃シナリオは `sort_best` の `PreparedCell` を `oracle_attempt=None` で返す変異であり、現在の流れでは `build_fn` と binary admission まで到達できる。  
   [根拠 orchestrator/campaign/s1_direct_comparison.py:681-722] [根拠 orchestrator/campaign/s8b_floor_campaign.py:2070-2176] [根拠 s2-plan.md:73-79]  
   提案: `sort_best` では exact `PASS`、contract、`dependency_root_realpath`、config hash を必須化し、cell の durable record に oracle receipt を結び付ける。負例は oracle 呼出しを除去し、build と admission が 0 回になることを確認する。

3. [severity: must-fix] oracle 後にも CMake の FetchContent と in-source build が書込み可能なまま残る。

   実測では `FetchContent_Populate()` と `masstree_SOURCE_DIR` 内の bootstrap/configure/make が存在し、fresh cell build は oracle 後に configure を実行する。  
   攻撃シナリオは oracle 後に populate stamp を消す、または別プロセスが source tree を変更してから次の cell を build する入力である。stamp が通常どおり残る場合の静的根拠だけでは、書換え不能性を証明しない。  
   [根拠 external/ccbench/cmake/ThirdParty.cmake:52-74] [根拠 orchestrator/campaign/buildcache.py:1408-1431] [根拠 s2-plan.md:21-34,150-158]  
   提案: oracle 後は `FETCHCONTENT_FULLY_DISCONNECTED=ON` 等で再 fetch を禁止し、source tree の所有ロックを保持する。probe だけでなく本番経路で、実際の include/archive path と no-write を検査する。

4. [severity: must-fix] cache key の追加案は dependency tree の identity ではなく base path の identity に留まる。

   実測では現行 `_v2_identity()` に masstree の HEAD、config hash、archive hash は無い。計画は canonical base path の追加だけであり、`completion.json` に保存される preimage も binary の生成元 archive を証明しない。  
   攻撃シナリオは同じ base で ignored な archive を差し替え、HEAD と config.h を維持して cache hit を発生させる入力である。root inode、HEAD、config hash の再検査だけではこの差分を検出できず、古い binary を受理しうる。  
   [根拠 orchestrator/campaign/buildcache.py:750-770] [根拠 orchestrator/campaign/buildcache.py:1458-1471] [根拠 external/ccbench/cmake/ThirdParty.cmake:57-86] [根拠 s2-plan.md:65-79,92-94] [根拠 docs/failures.md:7705-7730]  
   提案: cache preimage と completion に HEAD、config hash、archive hash 等の dependency receipt を含め、cache hit 時にも現在の receipt と一致させる。少なくとも「pinned-clean masstree」や「同じ archive を link した」という主張は削除する。

5. [severity: should] 共有 base の同時利用に実行時の所有権防壁がない。

   実測では現行 floor loop は同期で、job script も一意な `$TMPDIR` を作るため、現在の標準経路で直接の競合は確認できない。  
   攻撃シナリオは同じ base を二つの cell、wave、campaign に注入する入力であり、一方の FetchContent update/clone や in-source `make` が他方の source、config、archive を上書きする。計画自身も将来の並列化時に再審査するとしているだけである。  
   [根拠 orchestrator/campaign/s8b_floor_campaign.py:2039-2115] [根拠 tools/pegasus/floor_campaign.sh:97-101] [根拠 external/ccbench/cmake/ThirdParty.cmake:66-74] [根拠 s2-plan.md:34]  
   提案: base ごとの create-only lock/owner token を導入し、所有者不一致や既存 lock は fail-closed にする。

6. [severity: must-fix] テスト計画に独立した期待値と mutation の負例が不足している。

   実測では計画は nodeid と欠陥名を列挙するが、期待値の独立性、下流呼出し 0 回、archive の durable record 検査までは規定していない。  
   攻撃シナリオは `_v2_identity()` から期待 digest を導出する、post-build verifier を削除する、prebuild 失敗後に下流で同じ例外型を出す、という変異である。テストが緑でも対象 gate の存在を証明しない。  
   [根拠 s2-plan.md:164-179] [根拠 docs/failures.md:4238-4256] [根拠 docs/failures.md:5520-5535]  
   提案: 正常な同一 tree の positive control に加え、oracle 除去、configure/target 失敗、root/config/archive drift、base 欠落、duplicate define の各 negative control を置く。F150、F207、F209 の型を再発させない。

7. [severity: should] private runtime field と portable 化の設計が現行 exact-key 契約と噛み合っていない。

   実測では runtime store は exact key 集合を要求し、portable argv は `OUT_ROOT` と `CCBENCH_ROOT` しか置換しない。計画どおり `_fetchcontent_base_dir` を追加するだけでは store 書込みが拒否され、base placeholder を追加するだけでは `/scr/<job>` が残る。  
   [根拠 orchestrator/campaign/s8b_floor_campaign.py:2223-2241] [根拠 orchestrator/campaign/s8b_floor_campaign.py:2971-2989] [根拠 s2-plan.md:98]  
   提案: exact-key 集合、projector、placeholder 置換、全 durable JSON の raw path 検査を同時に更新する。resolver の既存 consumer は不変方針と空 default により現時点で取り残しは見つからない。

8. [severity: nit] configure/target 実行失敗を `outcome="invalid-path"` に流す設計は意味が曖昧である。

   [根拠 s8b_floor_campaign.py:205-215] [根拠 s2-plan.md:57-59]  
   提案: 閉集合へ `failed` を追加するか、`invalid-path` を使うなら process failure も表すことを schema とテストで明記する。

## 判定

NO-GO — prebuild failure、oracle receipt、cache dependency identity がまだ fail-closed に結び付いていない。

## 総括

- 最大の危険は、base path の一致を masstree tree と archive の一致として扱うことである。
- configure、target build、checkout、base 作成の失敗を private `UNAVAILABLE` へ変換する必要がある。
- `sort_best` の実 oracle `PASS` receipt を build/admission の必須入力にする必要がある。
- oracle 後の FetchContent 書込みと共有 base の競合を禁止する必要がある。
- config hash は同一 bytes の再検査にはなるが、期待 bytes や archive bytes の証明ではない。
- テストは独立期待値、下流呼出し 0 回、mutation negative control を含めるべきである。
- resolver consumer の変更は不要に見えるが、floor の証拠経路は未完成である。
- pytest は指示どおり未実行であり、判定は静的検証による。