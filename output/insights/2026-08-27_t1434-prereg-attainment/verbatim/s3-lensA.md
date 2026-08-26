## 所見

### A-01

- **対象** — A1 の「**実装済み**」「task/arm cardinality を manifest 由来で検査する」。
- **主張** — manifest が schema v3 でも、schedule が schema v2 または `schema_version` 欠落なら cardinality は `LEGACY_EXPECTED_SCHEDULE` 固定である。外部 manifest 由来になるのは v3 schedule 経路だけであり、A1 全体を無条件に「実装済み」とするのは過大。
- **一次資料** — `tools/codex_reasoning_ab.py:2931-2955` は v2/v3 を分岐する。`:2990-3001` は v2 で manifest を使わず `LEGACY_EXPECTED_SCHEDULE` を返す。`:9106-9117` は version 欠落 schedule を v2 として扱い、`:9181-9191` でその固定値と照合する。
- **重大度** — **must-fix**
- **代案の文** — **部分実装**。外部 task manifest は10 verbの `--task-manifest` から読み込まれ、v3 schedule 経路では task/arm cardinality と task 別 known finding 集合を manifest 由来で検査する。一方、schema v2 または version 欠落 schedule の互換経路は `LEGACY_EXPECTED_SCHEDULE` 固定のままである。

### A-02

- **対象** — A1 の「canonical digest は schedule、material へ**伝播する**」。
- **主張** — snapshot、prompt、run、packet、verdict の出力には digest を書くが、schedule と material manifest はこの実装が生成しない。両者には外部 producer があらかじめ digest を入れる必要があり、本コードはそれを要求、照合するだけである。「伝播する」は producer まで着地したように読める。
- **一次資料** — `tools/codex_reasoning_ab.py:3376-3398` と `:3539-3555` は snapshot/prompt 出力へ digest を書く。`:7421-7426` は既存 schedule の digest を要求する。`:10750-10763` は既存 material manifest と schedule の digest を要求する。
- **重大度** — **should-fix**
- **代案の文** — canonical digest は snapshot、prompt、run、packet、verdict 系の生成物へ記録される。schedule と material manifest については producer は本実装に無く、consumer が外部生成済み digest の完全一致を要求する。

### A-03

- **対象** — A3 の「`render-prompt` も task provenance と **snapshot 入力を manifest から決定する**」。
- **主張** — Q2 の中心結論、つまり provenance の記録だけではないという判断は正しい。外部 manifest により source session、rollout、prompt-source pin、期待する untracked artifact 集合は変わる。ただし実際の `new_root` と snapshot oracle は CLI 引数であり、manifest が snapshot 入力全体を決定するわけではない。
- **一次資料** — `tools/codex_reasoning_ab.py:3451-3458` は `new_root` と `snapshot_oracle` を外部引数として受ける。`:3461-3505` は manifest から task provenance を選ぶ。`:3522-3535` は prompt 内の untracked path 集合を `artifact_names` と照合するだけである。
- **重大度** — **should-fix**
- **代案の文** — **部分実装**。`render-prompt` は外部 task manifest から source session、rollout、prompt-source pin を選び、prompt が参照する untracked artifact 集合を task の `snapshot.artifact_names` と照合する。`new_root` と snapshot oracle 自体は CLI 入力である。standalone `verify-snapshot` と v2 schedule の固定 cardinality 経路は未閉包である。

### A-04

- **対象** — A4/A10 の「費用 field は certified field、resource gate、overall の**いずれにも接続していない**」。
- **主張** — 金額 field 自体を読む routing/resource gate は無いが、費用計算中の validation error は共通 `reasons` に追加され、最終的な certified field `valid` を false にできる。したがって certification 結果から完全に独立とは書けない。
- **一次資料** — `tools/codex_reasoning_ab.py:9819-9835` は cost validation failure を `reasons` に追加する。`:10452-10463` は `reasons` があれば experiment を不完了にし、`:10502-10510` は `valid = not reasons` とする。`:11208-11213` は certified report field を `valid` と定義する。
- **重大度** — **must-fix**
- **代案の文** — **部分実装**。material に schedule descriptor があり、全 slot が凍結 price version を持つ場合に、観測可能 attempt の部分正規化額と軸別集計を生成する。観測不能 attempt は金額を持たず状態別件数だけを残す。金額 field 自体は certified field や routing/resource gate の判定値ではないが、cost validation failure は共通 failure reasons を通じて certified `valid` を false にし得る。

### A-05

- **対象** — A7 の「oracle contract は**機構は着地**」「`oracle_kind` は normalized schedule、**run/attempt**、aggregate 軸へ伝播する」。
- **主張** — 着地しているのは二つの field と一部 consumer である。`oracle_kind` は raw launch receipt、completion、supervisor attempt ledgerには保存されず、replay 時に schedule/task manifest から in-memory attempt へ再付与され、aggregate resource ledgerへ出る。「run/attempt へ伝播」は永続 artifact にも保存されるように読める。また blind verdict の finding 検査は task-specific ではなく manifest-wide union である。
- **一次資料** — `tools/codex_reasoning_ab.py:7235-7299`、`:7339-7360`、`:7498-7510` の永続行には `oracle_kind` が無い。`:11069-11087` が replay 時に slot から attempt viewへ付与し、`:10404-10425` が resource ledgerへ出す。`:11506-11516` は blind 時に manifest-wide union、`:10179-10184` は reveal 後 aggregate で task-specific 集合を使う。
- **重大度** — **should-fix**
- **代案の文** — 現行 task manifest 内の `oracle_kind` と `known_finding_ids` の consumer は**一部着地**している。`oracle_kind` は normalized schedule と replay後の aggregate dimension/resource ledgerへ反映されるが、raw run receiptや supervisor attempt ledgerには保存されない。`known_finding_ids` は blind 時には manifest-wide union、reveal 後の aggregate では task-specific 集合として検査される。独立 oracle manifest、ledger、固有 hash、task acceptance は未登録である。

### A-06

- **対象** — A9 の「price snapshot の**保存、parser、schedule/aggregate への接続は機構は着地**」。
- **主張** — parser は保存済み HTML bytes を artifact bytesへ変換して stdout に出すだけで、fetch も保存も行わない。また aggregate の費用接続は material schedule descriptorがあり、全 slot が凍結 versionを持つ場合に限る。条件を落とした「接続済み」は広すぎる。
- **一次資料** — `tools/t189_price_snapshot.py:462-562` は保存済み bytes の parse/validate、`:783-800` は結果を stdout へ書くだけである。`tools/codex_reasoning_ab.py:10105-10136` は凍結 versionと material schedule descriptorの両方がある場合だけ calculatorを呼ぶ。
- **重大度** — **should-fix**
- **代案の文** — 保存済み price snapshot の parser/validator と固定 path の検査は着地している。parser 自身は fetch も保存も行わない。aggregate の部分正規化費用への接続は、material に schedule descriptor があり、全 slot が凍結 price version を持つ場合に限って発火する。登録世代 lock と cache-write 数量 receipt は未完了である。

## 見落としの疑い

A2、A5、A6、A8、A11、A12には追加の過大主張を認めなかった。

- A2 は schedule digest の完全一致要求と、予約・launch・completion・返却値への digest 記録を確認した。
- A5 は packet-source manifest の digest 要求が scheduleless 分岐より前にあるため、既存 digest無し bytesとの後方互換が無いという結論でよい。
- A8 は task単位の prompt/snapshot hash集中検査と supervisorの実 bytes照合を確認した。独立 oracle hash未登録も文案に残っている。
- A11 は `unavailable` と `not-incurred` を金額と `attempt_count` から外し、別件数へ残す実装と一致する。
- A12 は cache-write単価が存在する一方、receipt fieldと演算が無く計算器が skipするため、「価格不明」ではなく「数量不明」が正しい。
- A6 は測定日の更新だけで、新しい到達保証を追加しない。

別の整合性問題として、A1〜A12を差し替えても §13、§14、総括には「task manifest CLI未接続」「費用計算未実装」が残る (`docs/phase3-t189-model-routing-preregistration.md:897-899,948-951,975,996-998,1012-1013`)。これは到達度の過大主張ではなく過小主張だが、文書内で正本が矛盾する疑いがある。

## 総括

Q2 の核心、すなわち `render-prompt` が provenance記録だけでなく外部 manifestによって source task入力を変えるという結論は正しい。ただし snapshot入力全体を manifestが決定するとは書けない。

planをそのまま採用すると、A1の legacy schedule固定経路と、A4/A10の cost validationから certified `valid` への接続を隠すため、2件が must-fixである。ほか4件は条件や永続 artifactの範囲を明示すべき should-fixである。pytestやruntime実走は行っておらず、結論は指定資料の静的な全件検索と分岐追跡による。