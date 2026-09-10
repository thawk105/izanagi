## must-fix

### 1. 空 `list` の immutable 化をテストが固定していない

- **所見:** 新たに通る Python 引数表現は Pegasus の `numactl=()` だけでなく `numactl=[]` も含む。現行実装は両方を正しく tuple 化するが、新設テストは「空 tuple」と「非空 list」を別々に確認しており、「空 list は正規化しない」という誤実装が全6本を通過できる。
- **根拠:** 正規化は `orchestrator/campaign/pipeline.py:693-700`。空 prefix 正例は tuple 固定 (`orchestrator/tests/test_campaign.py:7348-7368`)、immutable 配線検査の list は linux-baremetal の非空値 (`orchestrator/tests/test_campaign.py:7315-7345`)。
- **成立条件:** `if type(numactl) in {list, tuple} and numactl:` のように truthy 値だけ tuple 化する変異。`evaluate(..., env_tag="pegasus", clocks_per_us=2100, numactl=[], authorization_contract=ec.authorize("pegasus"), extra_correctness=[...])` は認可を通り、可変 list のまま verify/bench へ届く。
- **成果物影響:** 認可後に共有 `[]` が変更されると、Pegasus 契約外 prefix で実行した結果が Pegasus の `contract_sha256` に帰属して certified 選択・性能台帳へ載り得る。現状のテスト／変異レポートはこの破れを検出済みと誤認する。
- **推奨対応:** Pegasus 正例を `()` と `[]` でパラメータ化し、空 list ケースで trace 受領値が exact tuple であることを確認する。可能なら認可後の fake build 内で元 list を変更し、trace/bench の snapshot が不変であることまで固定する。

### 2. `record_rep_returncodes=True` 側の別 `measure_point` 呼出しが動的配線検査から漏れている

- **所見:** `_run_bench` は `record_rep_returncodes` により別々の `measure_point` 呼出しを持つが、新設動的テストは既定の False 側しか実行しない。True 側だけ `numactl=None` にする誤実装が生存する。
- **根拠:** 分岐した呼出しは `orchestrator/campaign/pipeline.py:450-465`。動的テストは `record_rep_returncodes` を指定していない (`orchestrator/tests/test_campaign.py:7327-7338`)。AST テストが見るのは外側の `_run_bench` 2呼出しまで (`orchestrator/tests/test_campaign.py:7295-7312`)。
- **成立条件:** `pipeline.py:462` だけを `numactl=None` に変更し、linux-baremetal の正規 prefix、fullscale、`record_rep_returncodes=True` で評価する。認可は正しい prefix に対して完了するが、bench は prefix なしで起動できる。
- **成果物影響:** bench の fitness が登録済み contention 条件と異なる配置から得られ、linux-baremetal 契約の certified 選択・BENCH_DONE・COMMIT 台帳へ誤帰属する。M10 の変異検査結果も偽の kill 網羅になり得る。
- **推奨対応:** immutable 動的テストを `record_rep_returncodes=False/True` の両方で走らせ、fake `measure_point` が受け取る prefix を exact tuple・verify と同一オブジェクトとして検査する。

## should-fix

診断変更を direct `evaluate()` だけでなく、`loop.py:266-284` と `screening_driver.py:198-214` の WAL 境界でも1本固定するとよい。契約外 tuple は従来の `CertifiedWriterAuthorizationError` から gate の bare `ValueError` へ、未登録環境は `EnvContractError` へ発火順が変わる。WAL の `reason` は変わる一方、critic は `orchestrator/critic/digest.py:154-157,657-659` でどちらも `eval-exception` 件数へ畳むため、次手生成が失う構造化情報はない。運用者だけが読む例外型・文面の帰属変更であり、現行コードは意図どおりだが consumer-level 回帰検査はない。

## nit

AST テストの `expected = ast.dump(prefixes[0], ...)` (`orchestrator/tests/test_campaign.py:7308-7311`) は実装から作った期待値だが、直前に全要素を独立した `Name("numactl")` へ固定しているため恒真化はしておらず、単に冗長である。揮発値・現行 hash の焼き込み・意味のない恒真 assert は、今回の6本には見当たらない。

## 所見ゼロなら、ゼロである根拠

該当しない。上記2件以外の静的追跡では、正規化は qualification 検査 (`pipeline.py:649-678`) より後、認可と最初の sink (`pipeline.py:708-711,743`) より前にある。screening bench (`1127-1133`)、fullscale verify (`1167-1194`)、通常 bench (`1228-1246`) は同じ正規化値を使い、legacy verify (`1195-1196`) の `None` は裁定どおりである。

受理集合の意味上の純増は、qualification でない fullscale Pegasus の空 prefixだけである。API 表現としては exact `()` と `[]` の2形があり、qualification の `()` は旧実装でも既に受理されていた。`None` は gate、list/tuple 以外は有効な登録環境では認可検査 (`execution_guard.py:124-135`) が sink 前に拒否する。未登録環境や qualification 不整合は、裁定どおりそれ以前の検査に先取りされる。

## 総括

- 現状の実装本体に静的な fail-open は見つからなかった。
- ただしテスト防壁に2件の must-fix があり、このままでは land 不可と判断する。
- 新規受理は意味上 Pegasus の解決済み空 prefix だけで、裁定外の契約値は増えていない。
- Python 引数表現では `()` と `[]` が新規受理され、後者の immutable 性が未固定である。
- screening・通常 bench は固定済みだが、rep return code 分岐の別呼出しが未被覆である。
- 不正型は認可前 sink なしで fail-closed。未登録環境は意図的に lookup が先行する。
- 診断変更は WAL の例外型・文面に現れるが、critic は従来どおり汎用件数へ畳む。
- pytest・変異 harness は実行しておらず、結論は指定どおり静的検査による。