## 総括

現行閉包は親の 3 軸だけでは閉じていない。最大の漏れは、同一 file の全 node を同一 shard に置く shard 配置閉包である。  
実走では 4 個の real-repo 系 group が 23 file・3414 node の一成分となり、無印 3301 node まで shard-0 に拘束されていた。  
残差 87.8 秒の全てを collection / worker 起動へ帰属することはできない。うち約 56 秒は共通固定費らしいが、shard-0 固有の約 22 秒と protocol lock 待ちは未計測である。  
排他の意味を保った細分化は実在する。まず `test_s8b_floor_campaign.py` の無印 node だけを file 閉包から外す 1 手を採否測定すべきである。

## 1. 排他閉包の完全列挙

権威ある列挙方法は AST 単独ではなく、[test_real_repo_serialization.py:789](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/test_real_repo_serialization.py:789) の live collection である。これは最終 `iter_markers()`、fixture closure、real-repo access stamp を全 collected item から取得し、同ファイル 1143–1171 の独立 golden と照合する。親実走ではこの監査、shard closure 監査、手書き marker 監査がそれぞれ passed だった。

| 名前 | 実アンカー・単位 | 親の軸 |
|---|---|---|
| xdist runtime group 5 種 | 独立 golden は [test_real_repo_serialization.py:247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/test_real_repo_serialization.py:247)。実走単位は `campaign-repository-scan` 6 node、`dev-waves-runtime` 22 node、`s8c-predicate-snapshot` 3 node、`s8c-preregistration-candidate` 5 node。 | (a)(c) |
| 動的 `real-repo` marker | [conftest.py:1984](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/conftest.py:1984)–2000 で後付け。実走は 99 marker instance。1944–1960 で suffix を除き、4 process-memo node 以外は node 単位へ戻す。実走は 39 worker。 | (a) は hook 追跡時のみ、(b)(c) |
| P/S 資源別 RW lock | lock key・mode は [conftest.py:918](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/conftest.py:918)–947、flock は 1140–1170、P→S 取得は 1300–1354、全 protocol 包囲は 2068–2085。 | (b)、一部 (c) |
| 長寿命 fixture lock | `repository_candidate_commit` 5 node、`current_commit_snapshot` 3 node、`repository_scan` 6 node。exact fixture/access 契約は [test_real_repo_serialization.py:308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/test_real_repo_serialization.py:308)–348。fixture 本体は各 `yield` 全体を lock する。 | group は (a)(c)、lock 所有は 3 軸外 |
| controller prewarm 2 系統 | [conftest.py:769](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/conftest.py:769)–880、2089–2104。receipt は 36 node、oracle environment は 25 node の consumer がある shard ごとに一度解決する。cache の初回 worker read も [real_repo_receipt_memo.py:434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/real_repo_receipt_memo.py:434)–492 と [sort_swo_oracle_receipt_memo.py:453](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/sort_swo_oracle_receipt_memo.py:453)–512 の排他 flock を通る。 | 3 軸外 |
| ratified process memo | [real_repo_ratified_memo.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/real_repo_ratified_memo.py:29)–36、79–100。4 node を同一 worker/process に維持する。 | (a)(c) には見える |
| `certified_evidence` cross-worker flock | [test_p3_b4_raw_record_producer.py:813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/test_p3_b4_raw_record_producer.py:813)–878。共有 evidence を 17 node が使い、exclusive flock を fixture setup から test body 終了まで保持する。実走 JUnit 合計 220.7 秒だが、待ちの重複を含むため直列実仕事量とは読めない。 | 3 軸外 |
| file/group shard 配置閉包 | [acceptance_shards.py:321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/tools/acceptance_shards.py:321)–357 が file と group の二部グラフを union。衝突辺は同ファイル 74–84、独立 gate は 445–474。実走最大成分は 23 file・3414 node、うち marker 113、無印 3301。 | 3 軸外 |

AST で import alias まで解決して `fcntl`、`filelock`、`portalocker`、`fasteners` と shell `flock` を追うと、distinct collected node を結ぶ suite-wide lock は上表の real-repo、memo、`certified_evidence` に閉じる。それ以外は `tmp_path` など node 固有領域内、または一つの test 内で生成した thread/process 間の検査用 lock である。

session/module fixture は scope だけでは loadgroup work unit を作らない。静的には 13 定義あり、共有実資源を保持するものは上表の fixture lock と、`REAL_REPO_ACCESS_BY_NODE` が閉じる `real_known_axes_doc` / `benchmark_snapshots` である。

## 2. 床の帰属

`5816.6 / 48 = 121.2` と最長 node 126.13 秒は下界であって、213.91 秒の分解式ではない。実走 `report.json` の最大 worker occupancy と並べると次になる。

| shard | pytest wall | 最大 report duration/worker | report 外の差 |
|---|---:|---:|---:|
| 0 | 213.91 | 135.68 | 78.23 |
| 1 | 176.01 | 119.71 | 56.30 |
| 2 | 130.63 | 74.26 | 56.37 |

shard-1/2 の約 56 秒が一致するため、collection、48 worker 起動、初期配布、終了処理の共通費が大きいという親の方向性は支持される。ただし厳密な内訳を現在の artifact から分解することはできない。

shard-0 にはさらに約 21.9 秒ある。候補は controller prewarm、schedule gap、real-repo lock 待ちであり、現状では区別不能である。また最長 node 126.13 秒より最大 worker occupancy が 9.55 秒長く、87.8 秒の一部は単純な worker packing でもある。

protocol lock 待ちは JUnit に現れない。[conftest.py:2068](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/conftest.py:2068) で lock を取得してから内側 protocol へ `yield` する一方、[acceptance_shards.py:862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/tools/acceptance_shards.py:862)–872 は内側が生成した setup/call/teardown report の `duration` だけを加算するためである。反対に `certified_evidence` の待ちは fixture setup 内なので JUnit に含まれる。

既存測点だけでは protocol 待ちを測れない。最小追加は次の二点である。

- `conftest.py:1155–1170` の EAGAIN 再試行と 1220–1232 の same-process condition wait だけを monotonic で累積し、node/resource/mode 別の `lock_wait_s` を report へ出す。lock path 解決用 Git 時間を待ちへ混ぜない。
- `conftest.py:769–880` の二つの prewarm を別々に計時する。

これで `wall - max(worker occupancy)` を、共通固定費、prewarm、protocol 排他待ち、未分類へ分けられる。

## 3. 排他の意味を弱めない細分化

実在する。最小の 1 手は、`test_s8b_floor_campaign.py` のうち `xdist_group` を持たない node だけを file component から node component へ細分化すること。

実装箇所は [acceptance_shards.py:321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/tools/acceptance_shards.py:321)–357 と、その独立検査である同ファイル 445–474。marked 3 node は従来どおり `real-repo` conflict component に残し、無印 462 node だけを file vertex から外す。

この一手が意味を弱めない根拠は以下である。

- 同ファイルの fixture は [test_s8b_floor_campaign.py:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-exclusion-closure-split/orchestrator/tests/test_s8b_floor_campaign.py:197)、212、288 の function-scope autouse だけで、module/session 共有 fixture がない。
- 全 shard は deselect 前に同じ全 collection を行うため、module import・collection の意味は変わらない。
- real-repo 3 nodeの marker、shard conflict edge、protocol RW lock は一切緩めない。
- selected exact partition は `acceptance_shards.py:665–670` が引き続き検査する。
- 個々の test 本体、parametrize、skip、collected/selected 集合は変更しない。

実走ではこの file の無印 node のうち JUnit と一意照合できた 453 nodeだけで 1537.8 node秒あり、92.6–100.2 秒の node が 11 本あった。現在は全て shard-0 である。3 shard へ分散したときの期待短縮は約 20–32 秒を第一仮説とする。根拠は、約 1538 node秒の最大 3 分の 2を shard-0 から外す容量換算約 21秒と、現行 wall 213.9 秒から「共通約56秒 + 最長126秒」までの差約32秒である。

採否は親が同一 K=3・48 worker で paired A/B を行い、次を照合する。

- collected / selected の全体 digest が一致。
- real-repo と3 fixture group が同じ shard componentに残る。
- 対象 file の無印 nodeだけが複数 shardへ分散。
- 最大 shard wall、最大 worker occupancy、上位 node duration、追加した lock wait を比較。
- D1019 の走間差32秒があるため、単走の小差では採らない。

## 4. 排他閉包の外の手 (分類のみ)

該当しない。現時点で排他閉包内に、意味を保った具体的な細分化候補が存在する。これを A/B せずに worker 数、K、個別 test 短縮へ移る理由はない。

## 親 brief への異議

- **(P1) は誤り。** 最大 group 83.5 秒だけを見ても、3414 node の file/group shard component と17 nodeの暗黙 flock closureを評価できない。特に shard-0へ引き込まれた無印3301 nodeが欠落している。
- **(P2) は断定過剰。** 約56秒の共通固定費は支持されるが、shard-0固有約22秒と protocol lock 待ちは未計測である。「87.8秒は排他待ちではない」とはまだ言えない。
- **(P3) は誤り。** file component、group conflict edge、fixture-owned lock、controller memo/cache lock、`certified_evidence` flock が3軸外にある。
- **D1019 の 0.0 秒を本件へ一般化できない。** 同裁定は real-repo が一 workerの直列 poleだった regime の duration-weight割付を否定したもの。本案は weight を変えず、D1008 後にも残った file component の粒度だけを変える。D1019 自体には反しない。
- 効果量20–32秒は一 session の反実仮想であり、D1320どおり一般化前に paired A/B が必要である。本段では pytest を実行しておらず、親 artifact の事後解析と静的検査だけを用いた。