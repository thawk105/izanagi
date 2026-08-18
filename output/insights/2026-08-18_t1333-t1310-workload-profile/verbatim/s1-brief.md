# 段 1 brief — [T-1333] 形 1 + [T-1310] 択 (β) + [T-1349]

起点 main `a160f4aa` / branch `worktree-dev-wave-t1333-t1310-workload-profile`。

## scope (確定済みユーザー裁定)

1. **[T-1333] 形 1** — scale (records/threads) を producer の workload 表 entry に持たせ、
   producer の 3 sink と Layer-3 の campaign-chain 検査が**同じ entry から**導出する。
   検査を profile-aware にする形 2 は不採用。
2. **[T-1310] 択 (β)** — `s8b_ratified_freeze.load_legacy_freeze` の `legacy-v1` 源を
   正式 profile の**暫定源**として受理する。**non-certifying と明記する。**
   `load_verified_freeze` を `expected_hash` なしで使う形は採らない。
3. **[T-1349]** — arm resolver が読む `s8b_holdout_freeze.HOLDOUTS` と producer 側 profile が
   **同一 bytes を指すことを本 wave が assert する**。

## 親の実測 (M1〜M6、一次資料は本 job dir)

- **M1** `load_legacy_freeze()` は HEAD で成功。sha256 = `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688`、
  path = `output/s8b-freeze/holdout_freeze.json`。`floor` / `budget` はいずれも `null` のまま。
- **M2** `load_ratified_freeze()` は `RatifiedFreezeError [no-active] live active pointer が無い (v2 未発効)`。
  択 (β) が要る理由 (3) は現時点でも成立する。
- **M3** legacy freeze の `holdouts[name]` は `s8b_holdout_freeze.HOLDOUTS[name]` の**上位集合**。
  `candidate_id` / `records`(1000000) / `threads`(48) / `ycsb` の 4 key は同値で、
  `unknownness_check` と `variant_binding` が legacy 側にだけ在る。
  [T-1349] の assert は「4 key の射影が同値」で書ける (単純な `==` では常に False)。
- **M4** arm resolver (`s8c_arm_inputs._holdout_entries_by_candidate`) は
  `s8b_holdout_freeze.HOLDOUTS` を**同一 process 内の module 表として**読む
  (freeze ファイル経由ではない)。producer 側も同じ module 表を読めば同一 object 同一性が取れる。
- **M5** Layer-3 の単一 scale 固定は 3 箇所:
  `autonomous_trial_completeness.py:2884` (`workload not in producer.WORKLOADS`)、
  `:2903` (`workload_flags = producer.WORKLOADS[workload]`)、
  `:1612 付近 _check_cell_campaign_identity` の `expected_search_values`
  (`"records": 100_000`, `"threads": 4`, `"pilot_scope": "exploratory-ycsb-abc"`)。
  producer 側の 3 sink は `_campaign_for`(:651-659)、`_perf_for`(:691)、`_descriptor_for`(:701)。
- **M6** C01 (`s8c_preregistration_evidence._evaluate_c01`) は
  (a) 3 sink 関数の**本体に整数 literal `1_000_000` と `48` が在ること**、
  (b) `load_ratified_freeze` が宣言 path から**呼ばれていること**、を要求する。
  現在の snapshot は `orchestrator/tests/test_s8c_preregistration_predicates.py:151` の 1 箇所で
  `C01: (UNSATISFIED, "workload-projection-mismatch")`。
  **(β) は `load_ratified_freeze` を呼ばないので C01 は UNSATISFIED のままで正しい**
  (reason は `ratified-generation-reference-absent` へ遷移する見込み)。

## 不変条件 (緩めない)

- **規律 2**: 正しさゲートを緩める方向の変更は採らない。
- **repo scan invariant**: 正式 read 比率 (`ycsb_rratio` の正式値) を producer に literal で書かない。
  三軸 (rratio / skew / rmw) conjunction が 1 file 内で成立した瞬間に 0 hit が壊れる。
  records / threads は三軸に含まれないので literal でよい (C01 が要求してもいる)。
- **探索既定不変**: `ycsb-a/b/c` @ 100,000 records / 4 threads と
  `pilot_scope="exploratory-ycsb-abc"` の値・campaign identity preimage を変えない。
- **凍結 bytes 不変**: `output/s8b-freeze/holdout_freeze.json` と `V1_FREEZE_SHA256` を変えない
  (本 wave は読むだけ。`test_frozen_artifacts.py` の pin は緑のまま)。
- 正式 profile は **non-certifying** と機械可読に明記する。certifying を主張しない。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** `cells[].workload_flags` の bytes 形は**不変**に保つ。workload 表 entry を
  `{"ycsb": {...}, "records": N, "threads": M}` の構造体にし、`workload_flags` は entry の
  `ycsb` 面だけを射影する。T-1333 台帳文は「cell に載る値の形と campaign identity が変わる」と
  予測していたが、探索既定不変の実装要件と [T-1334] の byte 非回帰要求を両立させるには射影形が正しい。
- **(P2)** 正式 profile entry の `ycsb` は `s8b_holdout_freeze.HOLDOUTS` から**実行時読取**。
  `records` / `threads` は 3 sink 内に literal `1_000_000` / `48` として書き、
  かつ **その literal が実際に射影へ使われる**ことをテストで示す (C01 は存在しか見ない)。
- **(P3)** non-certifying provenance は `load_legacy_freeze` から取り、profile 記録へ
  `source="legacy-v1"` / `certifying=False` を持たせる。`load_ratified_freeze` は呼ばない。
  C01 snapshot の 1 箇所だけ更新し、負の control は更新しない。
- **(P4)** profile は明示 selector (CLI flag) とし、未知 selector は fail-closed。既定は探索。
- **(P5)** `pilot_scope` は正式 profile では別値にする (探索値を使い回すと Layer-3 の
  探索側検査が正式 run を素通しする)。値は段 2 で決める。

## 成果物の形

コード + テストのみ (docs は親が段 7 で書く)。実装面は Codex `role=author`。
変異 matrix は本 wave で実装した検査へ事前登録し、**wave 前の実コードの形**
(3 sink がそれぞれ独立に 100_000/4 を literal で持つ形) を必ず変異に含める。

## 成果物影響 (DW-G05)

これを実装しないと 8c 正式受入は空のまま (certified 選択が 1 件も出せない)。
実装すると rr80/rr20 の 1,000,000 records / 48 threads の実測が起動可能になり、
台帳の受理集合に「non-certifying な正式 scale run」が追加される。

## 分割方針

編集面が producer / checker / evidence の 3 module に分かれるが、
entry 型と射影規約を共有するため**一枚岩の 1 単位**とする (所有分割すると型定義が競合する)。

## 段 1 追記 (親の追加実測 M7)

- **M7** non-certifying は既に機械強制されている。
  `autonomous_trial_completeness.py:1574-1575` が
  `report_admission.get("certifying") is not False` で fail し
  (`"this producer cannot emit certifying input"`)、registered 経路は `:1644` で
  `reason_code == "registered-effective-non-certifying"` を要求する。
  したがって (β) の「non-certifying と明記」は**新しい certifying flag を作る作業ではない**。
  未記録なのは **scale / profile の出所** (`legacy-v1` か ratified v2 か) であり、
  本 wave が閉じるべきはそこである。(P3) をこの形へ差し替える。
- **M8** 正式 scale は producer 自身の descriptor sink を素通しで通る。
  `s8b_holdout_freeze.HOLDOUTS[name]` の `records`/`threads`/`ycsb` を
  `project_from_search_config` + `validate_descriptor` + `projection_record` へ通した結果が、
  `s8c_arm_inputs._descriptor_for_candidate` の出す descriptor と **byte 一致**する。
  rr80 = `80501db0235d88314edd4a4c29a1949e67acc2b466ae426fbbb1cb3da4b7d843`、
  rr20 = `53230b8b1f0e0d82def3c384f4d8d8b050a1ce872afd2ed9e2a403c61c3c550b`。
  **[T-1349] の assert はこの一致で書く** — producer profile を producer の sink へ通した
  content digest が arm resolver の封印 digest と一致することを要求する形にすれば、
  恒真ではなく (どちらかの scale / 比率がずれれば落ちる)、かつ二重管理を構造的に消せる。
- **M9** 形 1 の先例が既に在る。`s8b_oracle_driver._perf_for_holdout`
  (`orchestrator/campaign/s8b_oracle_driver.py:747-765`) は holdout entry の
  `records` / `threads` / `ycsb` から `PerfConfig` を fail-closed schema 検査つきで導出する。
  ただし源は freeze **文書** (Mapping) であり、arm resolver が読む module 表ではない。
  つまり現状 scale の源は 3 つある — module 表 `HOLDOUTS` / legacy freeze 文書 / producer の literal。
  本 wave はこの 3 者の関係を確定させる必要がある。共通 helper へ一般化するかは
  `DW-G03` (族一般化には独立 2 例) の判定対象として段 3・段 4 へ回す。
