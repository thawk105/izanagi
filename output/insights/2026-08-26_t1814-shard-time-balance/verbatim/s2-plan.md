## (a) 実装プラン

### 1. 台帳の読み手

`acceptance_shards.py` に新しい file reader は作らず、`conftest.py` の既存 snapshot を再利用する。

- `orchestrator/tests/conftest.py:752-765` の台帳 path・上限・config attr、`:783-844` の検証・bounded load、`:885-907` の controller/worker 分岐、`:1458-1479` の `workerinput` 配布、`:1845-1849` の configure 呼出しは変更しない。
- `tools/acceptance_shards.py:49-60` に config attr 名だけを定数として置き、`:763-771` で `getattr(config, attr, {})` を取得して `allocate(..., duration_seconds_by_nodeid=snapshot)` へ渡す。
- `tools` から `orchestrator.tests.conftest` は import しない。現在は `acceptance_shards.py:25-44` が pytest 不在でも import 可能で、production 側 import は `tools.dev_wave_land` だけである (`:46`)。`conftest.py` は pytest、hold registry、fixture 群を強制 import する (`conftest.py:45-150`)。直接 import は循環こそしないが、production tool の isolated-import 契約を壊す。
- 各 shard の xdist controller が同じ committed file を一度ずつ読み、その shard の全 worker は同じ `workerinput` snapshot を使う。`acceptance_shards.py` 自身で読むと最大 `48×K` 回の read になり、worker 間で file swap・一時的 I/O failure を観測する窓も増える。

なぜそこか: allocator が動く `pytest_collection_modifyitems` 時点では、`pytest_configure` による snapshot 配線が完了しているためである。

ただし、K 個の shard controller をまたぐ「一度だけの global snapshot」ではない。片方だけが I/O failure になれば片方だけ count fallback へ入る。この場合は通常 `selected-partition` で fail-closed になるが、同一 snapshot の機械的証明は現 schema に無い。この限界は実装採否上の実質的な不利である。

### 2. `_components()` と `allocate()` の変更

- `tools/acceptance_shards.py:92-96`
  - `Assignment.loads` を `tuple[float, ...]` に変更する。
  - weighted・fallback とも `weight` / `loads` は float に統一する。

なぜそこか: 秒単位の台帳値を丸めず保持し、経路ごとの型揺れを避けるため。

- `tools/acceptance_shards.py:288` の直前
  - `_complete_allocation_costs(records, snapshot) -> dict[str, float] | None` を追加する。
  - snapshot が `dict` で、全 record nodeid が存在し、各値が bool でない有限・非負の int/float であるときだけ float map を返す。
  - stale な余分の台帳 key は無視する。
  - 1 nodeid でも欠ける、型不正、非有限、負値、または component 和が overflow/nonfinite なら `None` を返す。

なぜそこか: component 単位で既知値と擬似値を混ぜず、割付全体を一度に duration mode / count mode のどちらかへ確定するため。

- `tools/acceptance_shards.py:288-320`
  - `_components(records, node_costs=None)` とする。
  - duration mode では、既に sort された `nodeids` の cost を `math.fsum` して `"weight"` に置く。
  - fallback では従来の `float(len(nodeids))` を置く。
  - `files/groups/nodeids` と tie-break (`:315-320`) は変えない。

なぜそこか: file/group の連結成分が shard 閉包の最小 work unit であり、node 単位の duration を足す場所はここだけだからである。

- `tools/acceptance_shards.py:323-385`
  - `allocate(records, shard_count, *, duration_seconds_by_nodeid=None)` とする。
  - records を sort 後、完全な cost map を一度構成し `_components()` へ渡す。
  - grouped/remaining の `-weight` LPT (`:348-364`) は維持する。
  - cost が全て `0.0` でも空 shard を作らないよう、min-bin 選択では未使用 bin を先に埋め、その後 `(load, index)` を使う。正の count fallback での既存選択は変わらない。

なぜそこか: 台帳はゼロを正当値として受理しており、現行 `(load, index)` だけでは全 zero component が shard 0 に集中して `empty-shard` になり得るため。

### 3. 未知 nodeid の擬似 cost

未知 nodeid が1件でもあれば、既知値も含めて全 nodeid の cost を一律 `1.0` とし、割付全体を既存の要素数 packing に戻す。

96 位は採らない。96 は `48 worker × 初期2 unit` という shard 内 scheduler の投入窓に由来する (`conftest.py:766-768, 987-998`)。外側の K=2/3 bin packing には対応する窓がない。`1.0` は任意の新しい統計量を導入せず、現在の `len(nodeids)` と完全に同じ順位・load を再現する唯一の自然な値である。

### 4. fail-soft 経路

経路は次で固定する。

1. 不在・読取不能・16 MiB 超過・UTF-8/JSON/schema 破損  
   → `conftest.py:823-844` が `{}`。
2. invalid entry の除去や suite 更新による部分欠落  
   → `_complete_allocation_costs()` が全 nodeid coverage 不成立を検出。
3. config attr 欠落・型破損・component sum overflow  
   → 同 helper が duration mode を拒否。
4. 全ケースで `_components(..., None)` により全 node cost `1.0`。
5. 警告やエラーを出さず、selection・skip・marker・受理 gate へ台帳値を渡さない。

台帳は `records`、`selected`、`finished`、terminal counts、failure 判定には使わない。

### 5. `weight` float 化の全波及

| consumer | 変更 |
|---|---|
| `Assignment.loads` (`acceptance_shards.py:92-96`) | `tuple[float, ...]` へ変更 |
| component `"weight"` (`:309-314`) | duration 秒または fallback `float(len(nodeids))` |
| component sort (`:315-320, 348-350, 358-360`) | float 比較。既存 lexical tie-break は維持 |
| bin loads (`:337-364`) | `[0.0] * shard_count`、加算結果も float |
| `component_report["weight"]` (`:376-385`) | float。ただし `Assignment.components` 内部だけ |
| collection state `"loads"` (`:783-789`) | float の list になる |
| `_worker_payload()` (`:850-862`) | `loads` を転送していないため変更なし |
| `assignment_closure_gate()` (`:388-411`) | node partition と file/group だけを検査し、weight を読まないため変更なし |
| `validate_report_evidence()` (`:455-538`) | worker 実測 duration は既に int/float を受理。allocator weight を読まないため変更なし |
| report schema (`:61-66, 936-959`) | `loads`、`components`、`weight` は含まれない。`SCHEMA` と `_REPORT_FIELDS` は変更しない |
| merge gate (`:540-638`) | report から allocation cost を再計算しないため変更なし |

既存 exact 述語で影響するものは以下。

- `test_run_tests_shards.py:720-737`: `Assignment` 全体の permutation equality と `loads == len(selected)`。後者を float expected と型検査へ更新する。
- `:706-718`: `_components()` の component dict を直接読む。fallback weight が float になる。
- `:79-111`: `_reports()` が引数なし `allocate()` を使うため、selected は現行 count packing のままにする。
- `:740-754`: K=3 の grouped placement は維持する。
- `:783-796`: closure gate は weighted assignment でも独立に通す試験を足す。
- `:883-928` と production `acceptance_shards.py:556`: report field 集合の exact 検査は変えない。

### 6. テスト計画

`orchestrator/tests/test_run_tests_shards.py:706-756` の allocator test 群へ以下を追加・変更する。

- `test_allocator_count_fallback_keeps_exact_legacy_partition_and_float_loads`
  - 現 `test_allocator_separates_groups_when_k_covers_group_count_and_is_deterministic` を拡張する。
  - empty snapshot で selected/components が legacy と同じ、全 load/weight が float で値は node 数と等しいことを固定する。
  - 落とす変異: fallback assignment drift、int/float 経路混在。

- `test_allocator_duration_weights_change_partition_and_are_deterministic`
  - node 数では均等だが duration が偏る fixture を用意する。
  - records の全 permutation と ledger insertion order 反転で `Assignment` 全体が一致し、duration load が均されることを検査する。
  - 落とす変異: duration 未配線、入力順依存、lexical-only allocation。

- `test_allocator_partial_or_invalid_snapshot_falls_back_wholly_to_count`
  - `{}`、1 node 欠落、bool、負、NaN、Infinity、component sum overflow を parameterize し、引数なし allocation と `Assignment` 全体が一致することを検査する。
  - 落とす変異: known/unknown の混合 weighting、部分 fail-open。

- `test_allocator_zero_costs_fill_every_shard`
  - K=2/3 と全 zero duration で全 shard 非空かつ closure 成立を検査する。
  - 落とす変異: `(load, index)` による shard 0 集中。

- `test_weighted_allocator_preserves_exact_partition_and_file_group_closure`
  - weighted selected の Counter が universe と exact 一致し、`assignment_closure_gate()` が真であることを検査する。
  - 落とす変異: component 分割、重複、欠落。

- `test_shard_collection_consumes_conftest_snapshot_without_reading_ledger`
  - `config` の既存 attr に snapshot を置き、`pytest_collection_modifyitems()` から同じ snapshot が `allocate()` へ渡ることを spy する。
  - production module が `orchestrator.tests.conftest` を import していないことも AST で固定する。
  - 落とす変異: worker 自前 read、attr 名 drift、snapshot 未配線。

- `test_weighted_assignment_does_not_expand_report_schema`
  - `"loads"`, `"components"`, `"weight"` が `_REPORT_FIELDS` に入らず、既存 `_reports()` が `merge_reports()` を通ることを固定する。
  - 落とす変異: diagnostic 値の受理 schema 混入。

`orchestrator/tests/test_acceptance_schedule_order.py:297-413, 895-1060` は変更せず関連回帰として使う。不在・broken JSON・oversize・invalid entry、controller 一度読み、worker snapshot-only の既存 killer が reader 側を覆っている。

pytest はこの read-only 段では実行しない。

## (b) 判定式と検出可能性

同じ K・同じ走行条件について、次の観測量を定義する。

\[
W_K=\sum_{s=0}^{K-1}\sum_w \mathrm{worker\_occupancy}_{s,w}.\mathrm{duration\_s}
\]

\[
C_K=\text{その走で real-repo に属した testcase duration の総和}
\]

親の式が破れる単純な境界は次である。

\[
C_K < \frac{W_K}{48K}
\quad\Longleftrightarrow\quad
W_K > 48K C_K
\]

ただし、この不等式が逆側でも「balance しても makespan が下がらない」は導けない。平均 capacity が chain 以下でも、chain の開始遅延、別 component の LPT 裾、worker idle gap、collection/prewarm/finalization の shard 差が critical path になり得るためである。

また、親の数値代入には不整合がある。`W=4215.5+3257.0=7472.5`, `K=2` なら、

\[
W/(48K)=7472.5/96=77.84\text{ 秒}
\]

であり、brief の `155.7` 秒は `W/48` で K を掛けていない。結論の真偽以前に、decision へ残す式では `W` が全 shard 合計か shard 平均かを固定する必要がある。

既存成果物からの検出可能性は限定的である。

- `report.json`
  - K は `shard_count`。
  - \(W_K\) は全 shard の `worker_occupancy.*.duration_s` の和で算出できる。
  - `group_to_workers["real-repo"]` で group を担当した worker 名は分かる。
  - しかし node→worker、group 単独 duration、worker 上の開始・終了時刻は無い。その worker の occupancy は他 unit も含むため \(C_K\) ではない。
- `junit.xml`
  - static な `REAL_REPO_SERIAL_NODES` と testcase を正規化して join すれば \(C_K\) をオフライン再構成できる可能性はある。
  - ただし既存 report の field ではなく、現時点で accepted な自動 detector もない。
- pytest wall、queue 待ち、job Elapse、外側 wall は shard report schema に無い。dispatcher/親 log との追加 join が必要である。

したがって、既存 field だけで機械的に検出できるのは `W_K` と real-repo worker の粗い proxy までである。「式が破れた」「balance が makespan を短縮する」を恒真に判定する機械 gate は存在しない。実装しない decision には、この不等式を保証ではなく再検討 trigger として記録し、最終判定は同一 tip の paired A/B に限定すべきである。

## (c) 親への攻撃

- 「固定費」56.4 / 39.2 秒は固定ではない。差は 17.2 秒あり、D531 の旧観測 20.6〜28.8 秒からも外れている。`worker_occupancy.duration_s` は各 node の pytest report duration の和であり、collection、worker 起動、scheduler 待ち、worker idle、controller 処理、JUnit/report finalization を含まない。したがって `wall − max(worker busy sum)` は chain と独立な定数ではなく、chain の開始時刻・内部 gap・選択内容にも依存する。2 shard の異なる残差から共通 intercept を置く P1 は同定されていない。[根拠 `anchors.md:48-53`; `tools/acceptance_shards.py:799-809, 920-960`; `docs/decisions.md:21910-21921`]

- `real-repo` は現実装上は一 worker に載るが、本質的に分割不能とは証明されていない。正本は73個の function IDで、parametrize suffix を除いた ID で照合し、既存 group marker が無い item にだけ `xdist_group("real-repo")` を付ける。全 real-repo marker は `_components()` の group vertex で同じ shard component に結合され、その shard 内では loadgroup の1 scopeになる。一方、73件には `applied()` を fake 化した4件を「over-approximation」として残すことが明記されている。資源競合を細分化できれば chain は分割可能であり、allocator が分けられないだけである。[根拠 `orchestrator/tests/conftest.py:335-438, 569-572, 1327-1333`; `tools/acceptance_shards.py:288-305, 679-705, 762-770`; `orchestrator/tests/test_acceptance_schedule_order.py:721-755`]

- static 正本73件と参照走の「72件」に既に差がある。tested tip と現在の registry、parametrize、skip/collection のどれが原因かは anchors から確定できない。したがって 210.5 秒は「現正本73件の不変な chain 長」ではなく、参照走で観測した72 testcase の値に限る。さらに D531 により、その秒数自体も共走競合で変わる。[根拠 `brief.md:30-33`; `anchors.md:22, 42-53`; `docs/decisions.md:21915-21921`]

- junit 合計と worker occupancy 合計の一致は、worker がその時間連続して占有されたことを意味しない。shard plugin は `pytest_runtest_logreport` の `when` を絞らず、setup/call/teardown の全 report.duration を nodeid ごとに加算する。その後、選択 node を worker 別に足しているだけで、実 elapsed interval は測っていない。したがって setup/teardown は occupancy 側には含まれるが、collection・worker startup・report 間の idle・session 外処理は含まれない。JUnit 側も total duration 設定なら近似一致するが、その設定は射影資料から確認できない。call-only 設定、collection error、plugin report、欠落 phase が入れば一致は破れる。[根拠 `tools/acceptance_shards.py:792-809, 903-929, 950-958`; `anchors.md:50-55`]

- D531 は duration を内生変数としている。K=2 の台帳値は、K=2・48 worker×2・当該配置・当該負荷で生じた競合込みの順位 proxy としてのみ妥当で、K=1 の秒数予測や hard lower bound には使えない。重み付き shard 割付は「似た K=2 条件で総 busy-time の偏りを減らす heuristic」であり、wall 改善の証明ではない。D746 の「順位だけでよい」という頑健性は shard 間にも期待できるが、採否は同一 tip の A/B 実測を要する。[根拠 `docs/decisions.md:21910-21925, 27997-28015, 29093-29105`; `brief.md:35-48`]

- P2 の平均式は必要条件の screening にすぎず、no-gain の十分条件ではない。参照走でも non-chain 最遅 worker は149.4秒あり、chain が遅れて開始すればその tail と直列に並ぶ。既存 report は開始・終了時刻を持たないため、`C ≥ W/(48K)` から critical path を復元できない。さらに P2 の数値は K=2 の分母を誤っている。[根拠 `brief.md:30-44`; `anchors.md:36-53`; `tools/acceptance_shards.py:61-66, 936-959`]

## 未確認事項

- 射影対象でなかった `orchestrator/tests/acceptance_duration_ledger.json` 本体は読んでいない。schema・件数・容量は anchors の記載だけに依拠した。
- repo 外の参照走 `report.json`、`junit.xml`、dispatcher log、親 probe は読んでいない。実測値は anchors/brief の転記として扱った。
- static 正本73件と参照走72件の差の原因は確認できなかった。
- pytest の JUnit duration 設定が total か call-only かは、射影ファイルから確認できなかった。
- K 個の shard controller が同一 ledger bytes を読んだことを証明する field は無い。
- pytest、import probe、テスト実測は実行していない。緑とは判定していない。
- Web 検索は使用していない。

## 総括

推奨は、現時点では実装しないことである。根拠は P2 ではなく、weighted allocation が critical-path wall を下げる証拠と shard 間 snapshot 同一性の証明がともに無いことにある。  
P2 は K=2 の分母が不整合で、平均式だけでは no-gain を保証できないため、そのまま decision に残してはならない。  
再検討条件は、同一 tip の paired A/B で non-chain tail が makespan を決めるか、`C_K < W_K/(48K)` が再現して観測された場合とする。  
その条件が満たされた場合は、上記の「conftest snapshot 再利用・全欠落時1.0 fallback・report schema不変」が最小変更になる。