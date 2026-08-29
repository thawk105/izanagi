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
| 段 6 run4 | fix3 適用後 | **29 passed** (451.31s) |
| 一覧検査 批1 | plain_runner_coverage / campaign_import_invariant / pytest_collection_config | 103 passed / 6 skipped (71.22s) |
| 一覧検査 批2 | campaign / t1286_commit_receipt / ccbench_spawn_sites / p3_b4_analysis_path | 424 passed / 3 skipped (23.79s) |
| 一覧検査 批3 | s8b_floor_campaign / p3_s4_loop | 783 passed / 3 skipped (51.06s) |

受入全走、変異 matrix、正式 B-4 実走、qsub、性能測定は**行っていない**。
変異 matrix は下記のテスト時間問題により実行不能である。

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

## テスト時間 — land を止めている実測

新規 test file 単独で **451.31 秒**。内訳は 2 node が 99% を占める。

```
447.39s call  test_positive_201_block_certified_preserves_decimal_and_all_pair_protocol_bindings
447.12s call  test_positive_201_block_all_terminal_records_absent
 17.38s setup 以下 27 node
```

受入台帳 `orchestrator/tests/acceptance_duration_ledger.json` の実測と比較する。

- 登録 nodeid 数 17,639、全 node の所要合計 9,610 秒。
- **現状の最遅 node は 140.0 秒** (`test_p3_autonomous_workload_trial.py::test_role_sink_bytes_vary_only_at_declared_declassifications`)。
- 本 wave の 2 node は **447 秒で、repo 全体の最遅 node の 3.2 倍**である。
- 並列実行では suite の wall 下限が最長 node に支配されるため、
  **この 2 node が受入全走の critical path になり、wall 下限を 140 秒から 447 秒へ 3.2 倍にする。**
- ユーザー裁定の絶対上限は**スイート全体で 5 分 (300 秒)**。単独 node で超える。

### 律速の所在 (構造で特定)

`p3_b4_closed_critic.invoke()` は arm ごとに
`artifact_admission.require_admitted_campaign(..., CERTIFIED_ACCEPTANCE)` を通る。
その中の `_require_verifier_epoch_for_purpose` が
`contract_loader_binding.capture_contract_loader_binding()` を呼び、同関数は

- `git rev-parse --verify HEAD^{commit}` を 1 回、
- `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` の **24 path それぞれに `git cat-file blob`**

を実行する (`contract_loader_binding.py:318-361`)。**1 回あたり 25 個の git subprocess** であり、
402 arm 分では約 1 万回になる。

**これは本 wave の編集禁止面である。** さらに `artifact_admission.py` 自身が
contract loader closure の 24 path に含まれるため、編集すると
「自分が検証している digest」が変わる自己参照面になる。
またこの gate は D1163 に基づき **admitted read ごとに drift を検出する**設計であり、
呼出頻度を下げることは単なる高速化ではなく**正しさゲートの設計変更**である。

**したがって本 wave では直せない。** 裁定パッケージ 5 として返す。

### 誤りだった仮説 (記録)

fix2 は「律速は projection closure の 12 file 再 hash」と報告し、
test から `mock.patch.object(C, "projection_sha256", ...)` で production 関数を差し替えて
高速化していた。しかし**差し替えても 447 秒のまま**であり仮説は成立しなかった。
検査を弱めて速度を買う形でもあるため fix3 で全除去した。
`cProfile` による確定は、codex 子の sandbox が scheduler へ到達できず (rc=16) 未実施である。

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
