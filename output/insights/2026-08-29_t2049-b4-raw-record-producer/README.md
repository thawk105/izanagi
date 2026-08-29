# [T-2049] B-4 raw 試行記録 producer — 一次資料

wave `dev-wave-t2049-b4-raw-record-producer`、branch `worktree-dev-wave-t2049-b4-raw-record-producer`。
base commit `d03855e92`。2026-08-29。

`verbatim/` に段 1〜6 の全成果物 (brief、plan、敵対相談 2 本、裁定、実装子報告、
敵対レビュー 2 本、レビュー裁定、fix 3 巡の報告) を逐語で置く。

## 成果物

- `orchestrator/campaign/p3_b4_raw_record_producer.py` (新規、2076 行)
- `orchestrator/tests/test_p3_b4_raw_record_producer.py` (新規、1153 行、29 node)

既存 file は 1 byte も変更していない。分析 source closure
(`p3_b4_analysis_path.py` の `_SOURCE_CLOSURE_PATHS` 5 file) には触れていない。

## この wave が埋めたもの

`p3_b4_analysis_path.py` の docstring が自ら「authoritative artifact producer, sanctioned command,
durable writer, report generator, certified-selection connection は scope 外」と明記している 5 語の
うち、**producer と durable writer の 2 つだけ**を埋めた。残り 3 つは別 task。

## 実測 (親が実走した値)

| 走 | 内容 | 結果 |
|---|---|---|
| 段 1 生死確認 | `test_p3_b4_analysis_path` + `test_p3_b4_analysis_adapter` | 49 passed |
| 段 6 run1 | 段 5 実装子の成果物 | 7 failed / 1 passed / 14 errors |
| 段 6 run2 | fix1 適用後 | **22 passed** (897.25s) |
| 段 6 run3 | fix2 適用後 | 3 failed (451.33s) |
| 段 6 run4 | fix3 適用後 | 29 passed (451.31s) |
| 段 6 run5 | fix4 適用後 | 1 failed / 28 passed (634.44s) |
| 段 6 run6 | fix5 適用後 | **29 passed** (26.25s) |
| 一覧検査 批1 | plain_runner_coverage / campaign_import_invariant / pytest_collection_config | 103 passed / 6 skipped (71.22s) |
| 一覧検査 批2 | campaign / t1286_commit_receipt / ccbench_spawn_sites / p3_b4_analysis_path | 424 passed / 3 skipped (23.79s) |
| 一覧検査 批3 | s8b_floor_campaign / p3_s4_loop | 783 passed / 3 skipped (51.06s) |

正式 B-4 実走、qsub、性能測定は**行っていない**。
テスト時間が 26 秒へ下がったため、変異 matrix と受入全走は実行可能になった。

## 段 3 と段 6 で独立 2 レーンが一致した所見

段 3 (plan への敵対相談) では 4 件が独立に一致した。

1. `precursor_hash` が registry からの転記だけで実 campaign と束縛されず恒真。
2. 任意 root への slot 群は新しい一回性台帳の新設であり、既存機構の再利用というユーザー裁定に反する。
3. `assignment_observation` を publish 順から作ると実行順と逆の遵守判定が通る。
4. arm ごとに別の receipt pair を選べる。

段 6 (実装への敵対レビュー) でも最重要欠陥が独立に一致した。

- **最終組立てが判断値を転記しており再導出しない。** 事前確定 path へ canonical file を先置きすれば
  証拠なしで任意の判断値を注入でき、**実装と消費側を両方 stub にしても正例が緑**になっていた。
  D162 決定 4「consumer は decision を入力として受け取らず、trusted validator を同一呼出し内で
  再実行する」の要求そのものであり、assembly 側でも再導出する形へ直した。

## 親が裁定後に自分で塞いだ穴

段 4 裁定を書いた後、`§2.4` の終端性判定に穴を見つけて塞いだ。
「終端記録が無い」ときに実行中と異常終了を区別しないと、
**実行中を欠測として封印する**か**異常終了を報告から消す**かのどちらかになり、
事前登録 §7.1 の全件報告に違反する。既存 `orchestrator/campaign/lock.py` の
`campaign_lock` を使う 3 分岐にした。

## 段 4 直前の既裁定照合で発見した D162

主題照合 (T-ID ではなく主題で `docs/decisions.md` を引く) により D162
「正例 artifact の適格性は producer が宣言せず、独立 validator の再計算だけを権威とする」が
本件に直接効くことが判明し、設計を 2 か所変えた。

- 判断 field を caller から受け取らない (入力 schema を閉じる)。
- 証拠は単一 fd / 単一 snapshot で読み、hash と parse を同一 byte buffer に対して行う。symlink は拒否。

## 閉じられないと確定したこと (非保証として実装に列挙)

- **`initial_proposal_sha256` を計算・記録する経路が repo のどこにも無い。**
  registry の field としてしか現れないため、precursor と実 campaign の束縛は転記に留まる。
- advisory flock は campaign 実行の内側区間しか覆わない。
- 事前登録 §7.1 が要求する model hash は存在しない (`model_snapshot` は非 hash の識別子)。
- `treatment_fired` は receipt 水準の意味に限定され、「その decision で次を合成した」を証明しない。

## テスト時間 — 451 秒から 26 秒へ

ユーザー裁定は「**受入全走 5 分以上は絶対に許さない**」である。
本 wave が新設した 2 node が 447 秒ずつを占めており、単独でこの上限を超えていた。
**原因は本 wave のテストの書き方であって、既存 production の設計ではない。**

| 版 | 結果 | file 全体 |
|---|---|---|
| fix3 | 29 passed | 451.31 秒 |
| fix4 (複製導入・共有 fixture) | 1 failed / 28 passed | 634.44 秒 |
| fix5 (最終) | **29 passed** | **26.25 秒** |

### 誤っていた最初の帰属 (記録)

当初「律速は編集禁止面にある drift gate なので本 wave では直せない」と報告した。
**これは誤りだった。** 切り分けると `p3_b4_raw_record_producer.py` は
`require_admitted_campaign` を一度も呼んでおらず、402 回呼んでいたのは
本 wave のテストの証拠生成部分だけである。実際の B-4 実走はこのコストを払わない。
既存 gate は既存の呼出頻度では問題になっておらず、402 倍にしたのがこの wave である。

### 実測した 2 つの律速

1. **実 `invoke()` 402 回。** `contract_loader_binding.capture_contract_loader_binding()`
   (`contract_loader_binding.py:318-361`) が 24 path へ `git cat-file blob`、
   加えて `git rev-parse` を 1 回、計 **25 個の git subprocess** を起動する。
   親の実測で **1 回 0.38 秒** (`git cat-file` 25 回 = 0.367s、`git rev-parse` = 0.013s)。
   402 回で約 153 秒。**447 秒の 34% にすぎない。**
2. **fsync。** この機械で親が実測した値。

   ```
   /tmp  : 50 回の write+fsync = 2.425 秒 (1 回 48.5 ms)
   /work : 50 回の write+fsync = 0.267 秒 (1 回  5.3 ms)
   ```

   pytest の `tmp_path` は遅い側にある。201 block x 2 arm x 約 10 file の耐久書き込みで
   概算 4000 file x 48.5 ms = 約 194 秒を払っていた。

### 対処 (テスト file だけを変更。producer は 1 byte も変えていない)

- certified / abort / terminal-absent の **3 block は完全な実経路**で生成する。
  `invoke()` の呼出は `test_p3_b4_raw_record_producer.py:401-402` の 1 か所だけになった。
- 残りの block は production writer と同じ bytes で複製し、
  **耐久性のためだけの fsync を払わない。**
  内容の真正性は `_assert_replicas_match_real_except_identity` (同 file 1521 行) が担保する
  — 種の実 block に対し、複製は iteration と pair_id が必ず異なり、
  それ以外の正規化した arm evidence は全複製が種と一致することを要求する。
- 複製時に WAL 先頭 record の `ts` を block の無作為化 schedule どおりに与える。
  これを欠いた fix4 版は割当遵守の検査が**正しく赤になった** (検査が効いている証拠)。
- 2 正例を直列化していた共有 session fixture を解いた
  (fix4 の 523 秒 setup は両 node に計上され、並列だった 447 秒より悪化していた)。

### 弱めていないことの確認

- skip / xfail / marker / 除外 / 保留: **0 件** (`grep` で確認)。
- `EXPECTED_BLOCK_COUNT` は 201 のまま。402 source artifact、全 hash 相異、
  十進 token `0.10000000000000001` の 402 回一致という検査はすべて残っている。
- production 関数の差し替え (`mock.patch.object(C, "projection_sha256", ...)` 型) は
  fix2 で一度混入したが fix3 で全除去し、以後入れていない。
- producer 側の検査は 402 arm すべてで従来どおり走る。速くしたのは**証拠の作り方**だけである。

### 受入台帳との比較

`orchestrator/tests/acceptance_duration_ledger.json`: 登録 nodeid 17,639、
全 node 所要合計 9,610 秒、**現状の最遅 node は 140.0 秒**
(`test_p3_autonomous_workload_trial.py::test_role_sink_bytes_vary_only_at_declared_declassifications`)。
本 file は 26.25 秒であり、最遅 node の 1/5 である。受入全走の critical path にはならない。

## 変異事前登録の帰属 (段 6 レビューの検証)

段 4 で M01〜M18 を登録したが、レビューが「実効的に一意なのは M04・M16・M18 と
publish 層限定の M12 の 4 点だけ」と示した。

- **到達不能** (前段が同じ入力を先に拒否): M02、M08。
- **検出不能** (登録 node が機構を pin していない): M01、M03、M05、M13、M17。
- **複数 node が落ちる:** M06、M07、M09、M10、M11、M14、M15。

fix3 でこの 7 点を実効 gate へ再照準し、
**「両 arm を一律 true にする」逆向き変異が全新規 test を通過する穴**にも負例を追加した。
**ただし変異 matrix の実走は上記テスト時間の問題により行えていない。**
再照準の有効性は静的確認までであり、kill 数は未検証である。

## 使用した子 (`receipt.json` schema v3、全件 `accepted`)

| 段 | stage | model | effort |
|---|---|---|---|
| 2 | plan | gpt-5.6-sol | xhigh |
| 3 | consult x2 (sol / luna) | gpt-5.6-sol | xhigh |
| 5 | author | gpt-5.6-sol | xhigh |
| 6 | review x2 (sol / luna) | gpt-5.6-sol | xhigh |
| 6 | fix x3 | gpt-5.6-sol | xhigh |

codex-cli 0.150.1。
