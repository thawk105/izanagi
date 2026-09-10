## 総括

最重所見は、同一 module 内の parent SH fixture から parent EX fixture への自己 deadlock である。  
H1〜H7 の差分自体は存在するが、H2 は申告どおり安全には機能しない。C3 も function fixture を検査対象から落としている。  
C1、C2 と 9 変異のうち 7 件は静的に裁定どおり。残る 2 件の原子的 map 変異条件も実装子の申告どおりである。  
pytest は実行していない。K=2 / K=3 は割付コード上は成立する。

## 所見

### 1. BLOCKER: 同一 module の SH fixture が後続 EX fixture を自己 deadlock させる

- **所見:** `test_s8c_preregistration_predicates.py` では、`current_commit_snapshot` が module scope の parent SH を `yield` 全体で保持する。その後、同じ module の function-scope `repository_candidate_commit` が parent EX を別 fd で取得するため、同一 process へ両 test が載ると自己競合する。serial 実行では source 順からこの経路を直接構成でき、xdist でも別 work unit が同一 worker へ配られない保証はない。

- **根拠 file:line:** fixture 実装は `s5-integration-snapshot.patch:1241-1279`、fixture の同一 module 帰属は `test_real_repo_serialization.py:311-322`。各取得は毎回新しい fd を開く `conftest.py:1196-1235`、timeout は 245 秒 `conftest.py:997-1001`。同一 process の別 fd による同資源再取得が timeout することを既存対照自身が固定している `test_real_repo_serialization.py:2061-2070`。C2 は各 fixture を個別に完走するだけで同時生存を作らない `test_real_repo_serialization.py:3660-3759`。

- **成果物影響:** candidate consumer が setup error となり、shard report の `error` / `failures` と merged rc が変わる。完走しても台帳所要へ約 245 秒が加算され、5 分上限付近では report 未生成の infra red になりうる。

- **提案:** writer fixture/test を別 module へ分離するか、candidate の EX 生成を module SH 取得前に完了させる単一 coordinator fixtureへ再設計する。実 lock を用い、`current_commit_snapshot` を `yield` 中に保ったまま candidate fixtureを開始して短い timeout で拒否する回帰検査を追加する。

### 2. HIGH: C3 が function-scope fixture を fixture 集合から除外している

- **所見:** 独立 literal には function-scope candidate fixture があるが、C3 の `fixture_nodes` は3 loadgroupの14 nodeだけから作られる。さらに collection detector が function fixtureを明示的に除外し、後段も `[function]` contractを `continue` している。裁定の「fixture 集合と resource node 集合が素」は満たしていない。

- **根拠 file:line:** function fixture contract は `test_real_repo_serialization.py:316-323`。collector 除外は同 `:824-827`、disjoint集合の構築は `:1187-1210`、function contract の検証抑止は `:1212-1215`。実装子の「14 retained node」申告は `s5-author.md:33-36`。

- **成果物影響:** function fixture consumer が resource mapへ混入してもC3自身は通る。parent reader protocol下で candidate EXを取れば約245秒後に errorとなり、certified結果、shard report、台帳所要が変わる。

- **提案:** function fixtureの実 consumerも独立 literalとlive collectionから固定し、全 fixture-owned consumerと `REAL_REPO_RESOURCE_NODES` のdisjointを検査する。加えて、resourceとのdisjointだけでなく、同一processで同時生存できるfixture同士のmode互換性も検査する。

## 申告と実物の照合

| 項目 | 静的判定 | 根拠 file:line |
|---|---|---|
| H1 T810 3 node | parent reader登録あり | `conftest.py:356-359,480-488,590-637` |
| H2 candidate 2系統 | 差分あり。ただし所見1のdeadlockで効果不成立 | `s5-integration-snapshot.patch:1219-1231,1263-1279` |
| H3 repository scan | module scope、`("read","read")`、6 decoratorあり | `s5-integration-snapshot.patch:414-465` |
| H4 common-dirと旧key併取 | Git authority閉鎖、旧→新、同一mode、共通deadlineあり | `conftest.py:1005-1139,1238-1266` |
| H5 current snapshot | module SHをyield全体で保持 | `s5-integration-snapshot.patch:1241-1255` |
| H6 nested collection 2 node | inventoryとparent-only partitionに存在 | `conftest.py:351-354,480-485` |
| H7 prewarm 2系統 | 実endpoint呼出しがparent SH内 | `conftest.py:848-938` |
| fixture別loadgroup | 5 + 3 + 6 = 14 retained nodeのliteralあり | `test_real_repo_serialization.py:245-281` |
| shard衝突辺 | 4 groupのK4、6辺をunionしclosureでも再検査 | `acceptance_shards.py:74-86,321-474` |
| C1 | production matrixから独立したexact literalを先に比較 | `test_real_repo_serialization.py:283-329,3982-4024` |
| C2 | 4つの実fixture bodyをunwrapしてsetup、yield、teardownまで実行 | `test_real_repo_serialization.py:3652-3773` |
| C3 | **不完全**。function fixtureが対象外 | `test_real_repo_serialization.py:1187-1215` |
| 9 mutation ID | 全IDと分岐が存在 | `test_real_repo_serialization.py:3776-4100` |

## 9変異の最初の落下点

| 変異 | 最初のassert | 判定 |
|---|---|---|
| `t810-live-reader-unregistered` | access map exact比較 `:3803` | 原子的map変異なら単独。source literalだけなら `conftest.py:613-633` のpartition guardが先 |
| `invariant-candidate-write-downgraded` | builder中のactive mode `:3688` | 単独 |
| `predicate-candidate-lock-removed` | builder中のactive context `:3700` | 単独 |
| `campaign-scan-lock-removed` | scan中のactive context `:3717` | 単独 |
| `parent-key-uses-worktree-root` | sibling key一致 `:3900` | 単独 |
| `legacy-key-not-acquired` | 旧→新のevent exact `:3932` | 単独 |
| `conflict-edge-removed` | production edgeと独立goldenのexact比較 `:3986` | 単独。component検査より先 |
| `prewarm-lock-removed` | 実endpoint内のactive SH `:4069` | 単独 |
| `nested-collection-node-unregistered` | access map exact比較 `:4094` | 原子的map変異なら単独。source literalだけならpartition guardが先 |

原子的map変異を要するのは実装子申告の2件だけで、他に同型の先行拒否は見つからなかった。

## lock、scope、shardの補足

- 旧→新 key は `conftest.py:1256-1265`、parent→ccbench は `:1275-1282` で固定され、process間の逆順経路は見つからなかった。
- scope縮小による生成回数は、申告literal上では増えない。invariantとscanは各1 module、predicate candidateは1 consumer想定である。ただしfunction consumer数はlive検査されていない。
- 別processならsnapshot側の約52秒間待つ可能性がある `s4-adjudication.md:67-72`。同一processでは所見1の245秒timeoutになる。
- 4衝突groupは1 componentへunionされる。K=2/K=3はいずれも `shard_count < len(group_names)` 側でLPT配置され、既存の `connected-exclusive-groups` 停止条件には入らない `acceptance_shards.py:377-424`。K=3のlive入力呼出しは存在するが未実走 `test_real_repo_serialization.py:1557-1586`。K=2専用の直接回帰がない点はnitであり、K=2/K=3のparametrize化が望ましい。