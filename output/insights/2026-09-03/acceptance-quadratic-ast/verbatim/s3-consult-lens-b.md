## 所見

### 1. file 束縛は「worker 内」には効かないが、「shard 間」には効く

- 判定: real。ただし親の表現は不完全。
- 根拠: 既定 scheduler は `--dist loadgroup` である (`tools/run_tests.py:550-572`, `:2639-2688`)。一方 `_components` は file と group を union-find で連結し、同じ file の全 node を同一 component、従って同一 shard に置く (`tools/acceptance_shards.py:321-350`)。選択後は元の collection 順で retained される (`:826-843`)。
- 結論: group の無い同一 file 内 node は shard 内で別 worker に配られる。しかし file 全体は同じ shard、同じホストに残る。
- 影響: 単位 A の 29重量 node は並列化されるが、負荷は一つの shard に集中するため、その shard の最大 wall と queue 占有には数十秒級で効きうる。
- 推奨対応: 「file 束縛は効かない」を「同一 worker への束縛にはならないが、outer shard affinity としては効く」に修正する。

### 2. `real-repo` group は二つの役割を兼ねており、単純除去は危険

- 判定: real と疑いの混在。
- 根拠: `REAL_REPO_GROUP_CONFLICT_EDGES` は、異なる shard が別ホストになり得て local flock では競合を閉じられないため、共通 mutable resource を触る group を同じ shard へ連結する契約である (`tools/acceptance_shards.py:74-84`, `:329-332`)。現在の `ItemRecord` には file と `xdist_group` しかなく、独立した shard-affinity 属性がない (`:102-113`, `:742-768`)。
- 検査結果: `real-repo` は、内側では「一 worker 直列化」、外側では「全対象を同一ホストへ置く affinity」の両方を担う。後者は明確に load-bearing である。
- 重要な反例: 書き手4件だけを `real-repo` group に残すと、reader-only file は別 component、別 shard、別ホストへ移り得る。そうなると local の SH/EX lock は writer と reader の競合を閉じない。従ってこの部分集合は shard mode では安全でない。
- `LOCK_SH` は同じ lock inode 上の reader 同士なら共有可能である。ただし指定射影に `conftest.py` がないため、legacy/common 二段のどこかで EX を取らないこと、同じ inode を共有することは未確認。prewarm、`patchharness._pytest_node_context`、相対順序の正しさ根拠も未確認。
- 影響: 96 node、台帳303.9秒という集計が正しければ、group を維持したままでは台帳モデル上すでに300秒を3.9秒超える。一方、誤って外すと跨ホスト race を導入する。
- 推奨対応: 全96 node の shard affinity は残し、xdist worker grouping だけを read/write で分離する設計にする。専用 affinity marker または別フィールドを `ItemRecord`、component、closure gateへ追加する必要がある。既存の「単一 unit」「相対順序」テストを変えるため、親の裁定パッケージ化判断は妥当。

### 3. `certified_evidence` の258.1秒鎖は確認できたが、「7 test が共有 evidence を書く」は疑わしい

- 判定: lock 鎖は real。共有書込み7件という一般化は疑い。
- 根拠: fixture は function scope で EX lock を取得し (`test_p3_b4_raw_record_producer.py:1174-1185`)、mock contextと test本体を含む `yield` (`:1230-1238`) まで保持する。静的に直接利用する17関数を確認し、台帳 `:1075-1097` の合計は正確に258.1秒。
- 共有 evidence を直接変更することが明白なのは、M17の receipt 書換えと復元 (`:1601-1625`) と、M18の共有 role file の rename、symlink、unlink、復元 (`:1629-1658`) の2件。M01、M04、assembly系の `write_bytes` は `tmp_path` 配下の publication artifact を変更している (`:1306-1315`, `:1358-1368`, `:1665-1693`)。
- `_publish` の内部副作用は製品 source が射影外なので未確認。このため「共有 writer は2件」とまでは確定できないが、親の7件という数え方は対象 path を区別せず過大評価している可能性が高い。
- 複製については、絶対 path を含む metadata があるため blind copy は不可 (`:1193-1220`)。しかし receipt、layout、hashを再生成して移設する helper は既に存在する (`:562-702`, `:705-769`)。従って「移設不能」ではなく「意味論的な再発行が必要」が正しい。ただし helper は admission を共有するためM18にはそのまま使えない。
- 影響: この鎖は fixture の二段初期化と SH/EX 分類により、期待値変更なしで大幅に短縮できる可能性がある。
- 推奨対応: 最初だけ EX で seed を生成して解放し、その後は確認済み reader を SH、M17/M18と未証明 nodeを EX にする。親の7件分類を保守的 writer 集合として開始する案でもよい。共有 tree の前後 fingerprint と並行 race testを追加してから広げる。

### 4. 親の critical-path モデルは不十分

- 判定: real。
- 根拠: makespan の下限は最長直列鎖だけでなく、最長単体 node、shard ごとの総 worker-time割る worker数、collection/setup/teardown、負荷偏りの最大値で決まる。allocator は台帳時間を使わず、component の `weight = len(nodeids)` だけで割り付ける (`tools/acceptance_shards.py:343-355`, `:377-442`)。
- また4 group の conflict edgeは一つの shard componentを作る (`:74-84`, `:329-332`)。これは worker直列化ではないが、重い処理の shard偏在を生む。
- `run_tests.py` の既定上限は48でなく32 workerである (`tools/run_tests.py:63-65`, `:385-399`)。48は環境変数による明示上書き時にのみ可能。
- 射影内の別 fixtureでは `recorded_rejection_report` が module scopeだが排他 lockはない (`test_p3_b4_raw_record_producer.py:1138-1149`)。repo全体の session fixture、`serial` marker、submodule排他は射影外で未確認。
- 影響: 「258.1秒が5分の壁を決める」および後続の「303.9秒が決める」は、候補となる下限の比較であって、単独では wall の決定因を証明しない。
- 推奨対応: 実測 report の shard別 worker occupancyと最大 worker時間を使い、`max(serial chain, shard work/n, longest node)` を最低限比較する。

### 5. 単位 A の約50秒見積りは妥当な予算値だが、実測値ではない

- 判定: 約50秒は妥当な保守推定。個別秒数と「CPU 7.6%」は疑い。
- 根拠: 台帳では59 node合計903.577秒、29重量 node合計897.0秒。親実測の比率は `1.07 / 27.4 = 0.0391`。重量 nodeを一回load 19件と、B後に二回から一回になる10件へ分けた単純比例モデルは次のとおり。

| 区分 | node数 | 台帳秒 | 楽観的なA+B後 |
|---|---:|---:|---:|
| 一回load | 19 | 456.0 | 17.8秒 |
| 二回load、B後一回 | 10 | 441.0 | 8.6秒 |
| 軽量 node | 30 | 6.577 | 6.577秒 |
| 合計 | 59 | 903.577 | 約33.0秒 |

- 約33秒は非static overheadまで比例縮小する楽観値なので、約50秒という予算は不自然ではない。ただし台帳の22秒 nodeが別計測の27.4秒loadより短く、両測定を直接減算できない。
- 個別 node は「一回loadなら残余時間 + 1.07秒」「B対象も二回から一回になり残余時間 + 1.07秒」としか静的には言えない。全時間比例なら0.84〜1.09秒だが、これは下限寄りである。
- 台帳全体は11956.464秒。903.577秒は7.56%だが、50秒まで減った場合の削減率は7.14%。しかも台帳値はCPU計測ではなく node durationなので、「CPU総量7.6%減」は不正確である。
- 影響: 約853.6 worker-seconds/走の削減となる。理想均等なら32 workerで約26.7秒、48 workerで約17.8秒相当であり、wallにも小さくない。最遅 shardでなくても、終了した shardの計算資源を早く返すので並行 waveのqueue回転率を改善する。
- 推奨対応: 成果物では「台帳 worker-time推定」と呼び、約50秒は事前予算、実装後値は実測で置換する。

### 6. 「5分」の測定面が未定義

- 判定: real。
- 根拠: Pegasus loginの空引数受入形は、指定がなければ既定2 shardである (`tools/run_tests.py:267-297`)。3 shardは `IZANAGI_ACCEPTANCE_SHARDS=3` の明示時だけであり (`:78`, `:253-264`)、各 shardは別 dispatchとして並行起動される (`tools/acceptance_shards.py:1243-1319`)。
- 297.5秒は一回の観測としては300秒未満だが、余裕は2.5秒、0.84%しかない。388.3秒が同じSLO対象の最大 shard wallなら明確に未達。異なるKや異なる測定区間なら直接比較できない。
- 影響: metricが未固定のままでは、A後に「依頼を満たした」と判定できない。
- 推奨対応: canonical command、K、worker数、queue待ちを含むか、collectionからteardownまでを含むかを固定する。実務上は最大 shard execution wallを対象にし、少なくとも連続3走すべて270秒以下など10%程度の余裕を設けるべき。

## 親の scope 選択への評価

**別のものに差し替えるべき。**

A/B/Cは正しい局所改善であり、queue占有削減にも価値がある。しかし「受入全走を安定して5分以内」という成果物の主対象としては、`real-repo` の outer shard affinity と inner xdist serializationを分離する設計へ差し替えるべきである。

具体的には、全real-repo対象の同一shard配置を維持しつつ、検証済みreaderをworker間で並行化し、writerだけを直列化する。併せて `certified_evidence` を二段初期化とSH/EXへ変更するのが次点である。

ただし前者は `conftest.py`、allocator schema、closure gate、既存の単一unit/順序テストを跨ぐ設計変更である。段2プランへ無断で足すべきではない。親の「裁定パッケージとして返し、別waveとして再briefする」という進め方は妥当である。A/B/Cは独立した二乗除去waveとして残してよいが、5分依頼の完了とは報告しないこと。

## 親 brief の誤り

- 「48 workerへ分散」は既定値として誤り。現在の既定上限は32で、48には明示上書きが必要。
- 「file単位の束縛は効かない」は広すぎる。worker束縛にはならないが、同一shard、同一ホストへの束縛にはなる。
- 「CPU総量7.6%減」は、台帳 durationをCPU量と呼んでおり不正確。50秒予測なら台帳総和に対する削減率も約7.14%。
- 「17 test中7 testが共有 evidenceを書き換える」は、射影内sourceでは裏付かない。直接確認できる共有path変更はM17とM18の2件。
- 「258.1秒のlock鎖が5分の壁を決める」は、後発の303.9秒group集計で既に旧情報。また総仕事量、shard偏り、起動費を除外している。
- 903.6秒から約50秒は妥当な推定だが、実測として扱ってはならない。

## 未実走・未確認

- pytest、profile、受入全走、並行race、A実装後の性能は未実走。
- `conftest.py`、二つのgroup期待値テスト、prewarm、patchharnessは射影外。そのためlegacy/common lock二段の実効modeと順序依存は未確認。
- 96 node、303.9秒、うち207.1秒という membershipは直接再構成できていない。提示表の算術は96件、303.9秒で整合する。台帳上の `test_codex_reasoning_ab.py` 全体は630 node、243.624秒なので、207.1秒はその部分集合として矛盾しない。
- `_publish` が入力evidenceへ間接書込みしないことは、製品sourceが射影外のため未確認。
- 297.5秒と388.3秒は提示値を使用し、元reportは未確認。

## 総括

親のscheduler理解は内側では正しいが、file/groupが担うouter shard affinityを過小評価している。  
303.9秒groupは有力な主因だが、groupをwriterだけへ縮めると跨ホスト排他が失われる。  
正攻法はshard affinityとxdist serializationの分離であり、既存期待値を変えるため裁定が必要である。  
`certified_evidence` の258.1秒鎖は確認でき、SH/EX化できる安全な部分集合が存在する可能性が高い。  
A/B/Cは約850 worker-seconds/走を削れる有益な改善だが、それ単独で5分達成を主張してはならない。