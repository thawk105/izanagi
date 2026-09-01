## 総括

親の 3 軸による列挙は完全ではない。shard 配置閉包、共有 fixture flock、controller memo、access map 外の実 repo reader が漏れている。  
したがって親 brief の (P3) と、段 2 の「無印 462 node は実 repo に触れない」という安全性根拠は成立しない。D1103 と同じ「閉包未確定のまま shard affinity を変えない」という判断が妥当である。  
ただし、漏れの存在だけでは「現在の wall の床が排他閉包である」とは言えない。親の追加反実仮想では node 粒度にしても最悪 worker occupancy は 126.1 秒のままであり、(P1) の速度面は覆らなかった。  
静的検査のみで、pytest は実行していない。

## 見つけた列挙漏れ

1. file/group による shard 配置閉包

   - 何が漏れているか: allocator は file と group の二部グラフを union するため、group を持つ数 node が同じ file の無印 node 全部を同一 shard へ引き込む。[tools/acceptance_shards.py:321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/tools/acceptance_shards.py:321)、[tools/acceptance_shards.py:445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/tools/acceptance_shards.py:445)。
   - 作業単位: 実走最大成分は 23 file・3414 node、うち無印 3301 node。対象 file 単独では 465 node、動的 real-repo marker 3 nodeと無印 462 node。
   - 境界: 四つの real-repo 系 group を同じ host に置く部分は正しさ防壁。無印 node の巻き込みは配置と速度だけで、runtime の直列 work unit ではない。
   - 覆す主張: 親 (P3) は覆す。ただし親実測 H/I の file 粒度と node 粒度がともに `LPT48=126.1s` という結果から、親 (P1) は覆さない。

2. `certified_evidence` の 17 node flock

   - 何が漏れているか: fixture は worker 共通ディレクトリに `fixture.lock` を作り、fixture setup から test body 終了まで `LOCK_EX` を保持する。[test_p3_b4_raw_record_producer.py:813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/test_p3_b4_raw_record_producer.py:813)。
   - 作業単位: `certified_evidence` を引数に持つ 17 node の直列鎖。JUnit 合計 220.7 秒には待ち時間が重複して含まれるため、直列実仕事量は静的には算出不能。
   - 境界: 現状は速度上の排他であり、D820 の real-repo 正しさ防壁ではない。shard を跨ぐと host ごとに別 evidence を構築するため、共有物破壊ではなく構築費の重複になる。17 node 間の横断主張も見当たらず、正しさ違反とは判定しない。
   - 覆す主張: 親 (P3) のみ。段 2 は既に列挙している。今回の狭い 462 node 分離ではこの file は動かないため、直接の blocker ではない。

3. controller prewarm と worker cache flock

   - 何が漏れているか: receipt 36 node、oracle environment 25 nodeについて、consumer を持つ shard ごとに controller が prewarm し、worker の初回 cache read も排他 flock を通る。[conftest.py:769](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/conftest.py:769)、[conftest.py:2149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/conftest.py:2149)、[real_repo_receipt_memo.py:434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/real_repo_receipt_memo.py:434)。
   - 作業単位: 61 node の直列鎖ではない。各対象 shardにつき resolver 1 回と、consumer を受け持つ各 worker の初回 cache load 1 回である。
   - shard を跨ぐ場合: cache path は shard 固有 session nonce と `/tmp` から作られるため、別 host の cache 同士は排他されない。[real_repo_receipt_memo.py:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/real_repo_receipt_memo.py:131)。cache byte の破壊は起きず、resolver が shard 数だけ重複する。一方、各 shard が異なる時点の実 repo snapshot を観測しても横断一致検査がないため、writer と重なる場合は正しさ問題になる。
   - 覆す主張: 親 (P3)。段 2 は列挙したが、cross-host 時の snapshot 分岐を評価していない。今回の `test_s8b_floor_campaign.py` 限定分離では consumer file は動かないので直接影響はない。

4. `REAL_REPO_ACCESS_BY_NODE` 外の実 repo reader

   - `test_s8b_floor_campaign.py` の無印 nodeには、実 source 全走査がある。[test_s8b_floor_campaign.py:1588](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/test_s8b_floor_campaign.py:1588)、[test_s8b_floor_campaign.py:6364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/test_s8b_floor_campaign.py:6364)。実 calibration、policy、freeze を読む node もある。[test_s8b_floor_campaign.py:2423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/test_s8b_floor_campaign.py:2423)、[test_s8b_floor_campaign.py:5075](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/test_s8b_floor_campaign.py:5075)。
   - shared ccbench の明白な map 外 reader もある。`git archive` を実 submodule に対して行う [test_b10_backoff_shape_sweep.py:1096](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/test_b10_backoff_shape_sweep.py:1096)、実 gitlink と freeze を読む [test_s8b_approved.py:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/test_s8b_approved.py:34) が map にない。
   - oracle environment 25 node は意図的に別 registry に置かれているが、実際には compiler の include root として共有 ccbench を読む。[conftest.py:576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/conftest.py:576)、[test_sort_swo_oracle.py:206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/test_sort_swo_oracle.py:206)。
   - session fixture の漏れもある。`checker_source_repo` は実 production source 2 本を読み、autouse fixture 経由で同 file の全 node が消費する。[test_mocc_trace_pair.py:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/test_mocc_trace_pair.py:121)、[test_mocc_trace_pair.py:154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/test_mocc_trace_pair.py:154)。
   - map 外では hook の `.get()` が `None` となり、protocol lock は無取得で通過する。[conftest.py:1991](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/conftest.py:1991)、[conftest.py:2068](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/conftest.py:2068)。
   - 作業単位: s8b では提案対象の個別 node、oracle は25 node、mocc は同 file の72 ledger nodeに対する worker ごとの session setup。いずれも排他鎖の速度床ではなく、未登録 reader という正しさ問題。
   - 覆す主張: 親 (P3)、段 2 §3 の安全性根拠、D1008 の allowlist 仮定。

5. access map 検査自体が手書き集合に閉じている

   - live collection 監査は、設定 map と別ファイルの手書き golden が一致することを確認する。[test_real_repo_serialization.py:1465](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/test_real_repo_serialization.py:1465)。
   - fixture 閉包も「既に map に入った node を seed に、その共有 fixture consumer を展開する」方式である。[test_real_repo_serialization.py:1311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/test_real_repo_serialization.py:1311)。全 consumer が map 外の fixtureや、直接 ROOT を読む node は発見できない。
   - 境界: 証明の穴であり正しさ問題。速度問題そのものではない。
   - 覆す主張: 親 (P3) と、段 2 §1 の「live collection が完全列挙を与える」という一般化。

## 覆らなかった主張

- 最終 `iter_markers()` を収集する監査は、定数 decorator、別名、factory、hook 後付けを含めて marker の最終形を観測する。[test_real_repo_serialization.py:789](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/test_real_repo_serialization.py:789)。許可される最終 group 名が5種である点には、識別子検索由来の穴を見つけなかった。
- marker を後付けする collection hook は `conftest.py` の real-repo 経路だけであり、最終 marker audit がこれを含む。[conftest.py:1983](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/conftest.py:1983)。
- ratified memo の4 nodeは `REAL_REPO_PROCESS_MEMO_NODES` に入り、suffix 除去から除外されて単一 worker/processを維持する。[conftest.py:567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/conftest.py:567)、[conftest.py:1944](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/conftest.py:1944)。
- 登録済み4 writerについて、reader と書かれているが実際は writerという反例は見つけなかった。今回の破れは主に map に存在しない reader である。
- 親の速度結論 (P1) は残る。親実測 H/I は file 粒度理想、node 粒度理想とも最悪 `LPT48=126.1s` で、段 2 の容量換算20秒を wall 短縮へ直結できないことを示している。
- 他の `fcntl`、shell `flock`、固定 `/tmp` を追った範囲では、distinct node を結ぶものは real-repo、2 memo、`certified_evidence` に閉じた。その他は `tmp_path` 配下または単一 node 内の競合検査だった。

## 親 brief と段 2 プランへの異議

1. 親 brief (P3) への異議: 列挙は不完全。少なくとも shard component、fixture flock、memo、map 外 reader が欠落している。

2. 親 brief (P1) への異議: 無し。列挙漏れはあるが、現在の最遅 shard の床を下げる排他鎖は確認できなかった。

3. 段 2 §3 の462 node 分離案への異議: 採らない。無印 node が実 repo に触れないという前提が file:line で破れている。lock path の保証は同一 host限定である。[conftest.py:1058](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/conftest.py:1058)。

4. D1103 との関係: 「登録外 writer」は今回新たに確認できなかったが、map 外 reader と未同期の collection 窓は残る。全 shard は独立 processとして先に起動され、cross-shard collection完了 barrierはない。[tools/acceptance_shards.py:1243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/tools/acceptance_shards.py:1243)。したがって D1103 の「閉包未確定の排他を差し替えない」という却下理由は本案にも当たる。

5. 段 2 の20〜32秒短縮仮説への異議: 親が段 3 投入後に追加した反実仮想と矛盾する。node 粒度の完全割付でも最悪 worker occupancy は126.1秒から変化せず、現行詰め込みとの差も最大約9.6秒である。`parent-measurements.md:252-277`。

6. `certified_evidence` と2 memoは今回の狭い file 分離では shard を跨がない。ただし一般的な node component 化へ拡張する場合、前者は setup 重複、後者は shard ごとの snapshot 分岐を生むため、それぞれ専用 affinity 契約が必要である。