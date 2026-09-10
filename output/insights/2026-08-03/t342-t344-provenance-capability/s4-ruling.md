# 段 4 裁定 — [T-342]+[T-343]+[T-344]

親が段 2 プランと段 3 の 3 レンズを real / refuted、採用 / 不採用、scope 内 / 外に裁定する。
本書が段 5 以降の唯一の契約である。

## 0. 親の provisional 裁定の帰趨

| # | 帰趨 | 理由 |
|---|---|---|
| (P1) | **一部 real、補強して採用** | evidence 由来の class 導出は正しいが、現行 `assert_worktree_within_allowlist()` は clean を証明していない (レンズ A/plan)。`tracked_clean` を別途取る。優先順位と曖昧 receipt 拒否も明文化する。 |
| (P2) | **採用。ただし security credit は主張しない** | parser 発行 token は誤用防止として有効だが、同一 process 内の caller は factory を自ら呼べる (レンズ A-2)。信頼境界は D127 決定 (4) と同じく「trusted orchestrator code」に留め、docstring と decisions に明記する。 |
| (P3) | **refuted。不採用** | stock だけ key から除外すると receipt を持たない旧 stock cache が受理され続け、「旧 entry は拒否」というユーザー裁定と矛盾する。**legacy key は stock を含む全 class で変える。** |
| (P4) | **方向は real、記述不足として補強** | preimage 変更だけでは旧 entry に検査が到達せず「拒否した」証拠にならない。legacy sidecar と v2 completion manifest の**両方**に exact receipt 検証を置く。 |
| (P5) | **refuted。撤回** | 旧 3 campaign は `output/campaigns/` にあり、現行 driver は D123 で `output/exploration/campaigns/` へ前向き移行済み (レンズ B-3 が実測)。ID を保っても通常 resume で踏む実物は 0/3。**campaign ID を変える plan 案を採る。** 旧成果物への可聴な拒否は overlay + consumer 側が担う。 |
| (P6) | **fail-open として refuted。補強して採用** | 3 件 denylist だけでは未掲載の receipt 欠落 artifact が通る。ただし全歴史成果物への遡及適用は scope 外 (§3-1)。**本 wave の positive receipt 要求は「新 schema 導入後に生成された成果物」に限定する。** |

親の段 1 実測の誤りも訂正する (レンズ B が反証)。

- `s1_known_axes_freeze.py` の sha pin は **3 箇所ではなく 4 ファイル・7 field**。うち live file を照合するのは
  `s1_known_axes_freeze.py:718` の freeze verifier であり、T080 は `migration_basis_commit` の blob を見る。
  **編集禁止という結論は変わらない。**
- 凍結 doc の source pin は **63 record / 31 distinct path / 15 mismatch record / 4 distinct mismatch path**。
  中核 5 ファイルが 0 件なのは正しい。「4 本を再編集しても新規検出は生じない」という一般化は
  **byte pin に限った話**であり、意味契約の検査は別入口にあるため、この一般化は削る。

## 1. scope 内 — 実装する (real かつ採用)

### 1-A capability 中核 (T-342)

1. class は caller が選ばず evidence から導出する。導出順序は plan §2.2 を採る。曖昧 (generator と
   review receipt の同時提示) は拒否。
2. `STOCK` 判定は `src_token == STOCK` かつ `tracked_clean` に加え、**repo 正本の submodule pin と
   宣言 commit の一致**を要求する (レンズ A-3 を採用。`orchestrator/campaign/pin.py` の `CURRENT_PIN` を使う)。
   caller が選んだ任意 checkout の自己整合だけで STOCK 権限を出さない。
3. CLI authority は parser の private action だけが発行する run-scoped token とし、`True`・偽 object・
   別 run token を拒否する。nonce は永続化しない (再起動 resume を壊さないため)。
4. **永続 receipt には canonical body を全部持たせる** (レンズ A-4)。outer SHA だけにしない。
   generator id / review id / 入力 digest / policy SHA / source evidence を exact-key で持つ。
   これが証明するのは構造と一貫性であって発行主体の真正性ではない、と docstring に書く。

### 1-B identity 束縛 (T-343)

5. legacy `cache_key()` は **全 class で** admission receipt digest を織り込む。あわせて legacy entry に
   exact-schema の admission sidecar を置き、hit 時に欠落・不一致なら拒否する。旧 namespace への
   fallback 探索は作らない。
6. v2 は `_v2_identity` の preimage と completion manifest の**両方**に admission を必須 field で入れ、
   preimage・manifest・現在の evidence を exact equality で照合する。
7. campaign は `ident.canonical_preimage()` の `search_config` に admission policy を入れる
   (= campaign ID が変わる)。lock の exact-key 検査にも policy を含める。
8. **replay で要求するのは receipt の canonicality・policy 一致・attempt topology までとする**
   (レンズ B-4)。過去 attempt の source を現在 worktree と一致させる検査は、恒真化するか
   正当な過去 iteration を一律拒否するため**入れない**。現在 source との一致は現在候補と
   cache 再利用の境界だけで要求する。
9. `BUILD_START` / `BUILD_DONE` / `COMMIT` を attempt ID 単位で束ね、receipt SHA を伝播する。
   source 解決前に止まった pre-build rejection は receipt 無しを許すが、その attempt から
   `BUILD_DONE` / `COMMIT` が出ていたら拒否する。

### 1-C overlay と consumer (T-344)

10. overlay 台帳は **2 次元** にする (レンズ C-5)。`verification_status` (歴史的 verifier 判定) と
    `admission_status` (T-316 admission) を別 field にし、overlay は後者を `legacy-unclassified` にする
    deny-only 台帳と明記する。台帳は authority (裁定 ID)・作成元 commit・入力 hash・生成規則を持つ。
    reader は exact ledger SHA を decision receipt として返す。
11. 対象は実測済みの **3 campaign** (`p3-s4-loop-…-0b53a387` / `p3-s5-sort-loop-…-3be89e0d` /
    `p3-s8a-trigger-loop-…-3f72ecd5`)。ユーザー裁定の文言は「段 5 / 段 8a」だが、段 4 loop も
    同型の receipt 欠落を実測しており、fail-closed 方向の同型追加として含める。**この 1 件の拡張は
    親の裁定であり、記録に明示する。**
12. 除外を効かせる consumer は次のとおり。`layer3_report.py` (+ `layer3_schema.json` を v3 にし
    `admission_decision` を必須化)、`critic/digest.py` の**全 raw-WAL loader** (validated view 型を
    一度発行し、個別 guard を足す形にしない)、`replay.py` の prefix loader、`s6_sort_sweep.py` /
    `s8a_trigger_sweep.py` の certified 判定、`p3_autonomous_workload_trial.py` (**canonical な
    試行台帳 producer。plan が落としていた。レンズ C-1**)、`autonomous_trial_completeness.py`。
13. positive receipt 要求の射程は **新 schema 導入後に生成された成果物**に限る。既存の歴史成果物を
    一括再分類しない (§3-1 へ)。

### 1-D materializer 面の最小閉包

14. `s8b_floor_campaign.py` の official 拒否を wrapper から `_run_campaign_core` 内へ移し、official mode で
    materializer を差し替えられなくする (レンズ A-1 の最小 fix)。`eligible_for_refreeze` を
    receipt chain から導出する再設計は §3-6 へ。
15. **`NON_ADMISSIBLE_MATERIALIZERS` の明示 registry**を置き、`orchestrator/**/*.py` の build 起動箇所が
    「admission を通る」か「registry に載る診断専用」かのいずれかであることを静的テストで閉じる
    (レンズ A-5 の bounded 版)。shell materializer と calibrator の任意 binary path は §3-2 へ。

### 1-E テストと期待値の扱い

16. 既存テストの期待値変更は、次の列挙に限る。各々「なぜ現行期待値が誤りか」を実装子が報告に書く。
    列挙外が赤くなったら回帰として報告し、期待値を触らずに止める。
    - legacy stock cache key の golden (`test_campaign.py` の `_GOLDEN_CK0` 系)
    - 代表 campaign ID の固定値 (`test_campaign.py`)、S8a ID sentinel (`test_p3_s4_loop_trigger_gating.py`)
    - v2 preimage / completion manifest の exact fixture (`test_buildcache_v2.py`)
    - 直接 constructor 前提の admission テスト (`test_campaign.py` の T-316 追加分)
    - `p3_kickoff.py` の dirty no-op を stock/cache hit とみなす分岐に対応するテスト
    - 実 S8a 旧 campaign を render 成功と期待する `test_layer3_report.py`
    **旧値は「T-343 以前の歴史的導出値」として定数を残し、意図的な互換破壊が将来見えるようにする**
    (レンズ B-6)。単なる上書きにしない。
17. tail-repair テストは正規 attempt/receipt を与えて従来契約を維持し、receipt 欠落 committed WAL は
    **tail 破損のない別 fixture**で新規テストにする (レンズ B-8)。1 テストが 2 理由で赤くなる形にしない。
18. cache の「旧 entry 拒否」テストは、旧 entry を**新 key / 新 digest の下へ置いて** validator を
    実際に踏ませる (レンズ B-9)。単なる cache miss を拒否の証拠にしない。
19. overlay のテストは production ledger から期待集合を導出せず、独立な exact tuple
    `(path, campaign id, lock SHA, WAL SHA, build_start count)` と ledger raw SHA をテスト側に固定する
    (レンズ B-5)。membership の独立 sentinel も置く。

### 1-F 落とすもの (nit)

20. `backoff_sweep_report.py` への guard 追加と `autonomous_trial_completeness.py` 深部の二重 guard は、
    上流 validator が必須なら受理集合を変えないため **nit として落とす** (レンズ C-8)。
    予算は producer・schema・全 raw-WAL loader へ振り替える。
21. `variant_id` を変えないことは設計 invariant であり実装項目にしない。

## 2. gate の署名と正例 (`DW-S04`)

新設する禁止を署名で書き、通る正例を 1 つずつ添える。

| 禁止 (署名) | 通る正例 |
|---|---|
| `derive_build_admission(context, source, …)` は、evidence が STOCK 条件を満たさない source に `STOCK_BASELINE` を発行しない | clean tree・宣言 commit = repo pin・`src_token == STOCK` の baseline は token 無しで通る |
| `derive_build_admission(...)` は parser 発行 token 無しに `CODER_AUTHORED` を発行しない | `--allow-coder-derived-build` を付けた 5 driver の invocation は通る |
| `cache_key(...)` / `_v2_identity(...)` は admission receipt digest を欠いた key/preimage を返さない | 同一 class・同一 evidence の再 build は cache hit する |
| `_validate_v2_entry(...)` は admission field を欠く completion manifest を受理しない | 新 schema で publish された entry は hit として受理される |
| `require_admitted_campaign(...)` は overlay 掲載 campaign を admission-aware 選択へ通さない | overlay 非掲載かつ新 schema の receipt を持つ campaign は通る |

## 3. scope 外 — 実装せず裁定パッケージへ返す (real だが本 wave の射程外)

いずれも real と裁定する。**実装したふりをせず、docstring と decisions に「閉じていない」と明記する**
(D127 決定 (4)(5) と同じ扱い)。

1. **全歴史成果物への遡及再分類** (レンズ C-9)。本 wave は 3 campaign を明示 deny し、positive receipt 要求は
   新 schema 以後の成果物に限る。P2 landscape 等を含む全 receiptless artifact と全 consumer の
   inventory は別 wave。
2. **materializer の完全閉包** (レンズ A-5 残余)。shell materializer 3 本 (`certify_calibration.sh`、
   `t141_region_profile.sh`、`t139_positive_control_probe.sh`)、calibrator の任意 executable path、
   S8b content-addressed store の resume 取得。
3. **推移的 provenance** (レンズ A-7)。`s1_known_axes_freeze.py` が編集禁止であるため、旧 campaign 値を
   内包する freeze を経由した laundering は本 wave で閉じられない。
4. **in-process 発行器の信頼境界** (レンズ A-2)。別 process / OS capability / 署名鍵への移設。
5. **T126 control の再測定と新 protocol/pin** (レンズ B-10 / C-10)。本 wave では live member build にだけ
   新 capability を要求し、歴史的 control source は
   `verification_status=historically-certified` + `admission_status=legacy-unclassified` の
   evidence-only として保持する。**series identity への policy 追加も本 wave では行わない**
   (行うと T126 の受理可能 source が 0 件になる)。
6. **S8b `eligible_for_refreeze` の receipt chain 化** (レンズ A-1 残余)。
7. **immutable source snapshot による ABA/混在 snapshot の遮断** (レンズ A-6)。本 wave は evidence と
   build の source root を同一に束縛し記録するに留め、残る窓を既知限界として明記する。

## 4. 実装単位 (段 5)

編集ファイル所有を素集合にする。依存順は `1 → 2 → (3, 4, 5 並列)`。

| 単位 | 所有 (production) | 所有 (test) |
|---|---|---|
| **U1 capability 中核** | `build_admission.py`、`source_digest.py` | `test_build_admission.py` (新規)、`test_source_digest*.py` の該当分 |
| **U2 identity 束縛** | `buildcache.py`、`ident.py`、`pipeline.py`、`loop.py`、`model.py`、`wal.py`、`screening_driver.py` | `test_buildcache_v2.py`、`test_campaign.py` |
| **U3 caller / CLI** | §3.2 の caller のうち S8b・qualification・consumer を除く全て | `test_p3_build_authority_cli.py` (新規)、各 driver 固有 test、`test_p3_exploration_namespace.py` |
| **U4 overlay / consumer** | `artifact_admission.py` (新規)、overlay ledger (新規)、`layer3_report.py`、`layer3_schema.json`、`critic/digest.py`、`replay.py`、`s6_sort_sweep.py`、`s8a_trigger_sweep.py`、`p3_autonomous_workload_trial.py`、`autonomous_trial_completeness.py` | `test_artifact_admission.py` (新規)、`test_layer3_report.py`、`test_critic*.py`、`test_s6*`/`test_s8a*`、`test_autonomous_trial_completeness.py` |
| **U5 S8b 最小 + materializer registry** | `s8b_floor_campaign.py` (official 拒否の core 移設)、`s8b_oracle_driver.py` の admission 配線、materializer registry | `test_s8b_floor_campaign.py`、registry の静的 test |

`test_p3_s4_loop.py` の critic 部分は **U4 所有**とする (レンズ C-7)。qualification (`t126_driver.py` 等) は
constructor 変更に追随する**最小配線のみ** U3 所有とし、series identity には触らない (§3-5)。

## 5. 変異事前登録 (`DW-M01`)

`tools/mutation_harness.py` を使う。各変異は単一理由で赤くなることを実装後に確認し、
手前に同じ入力を拒否する検査がないことを確認する。確認できなければ登録を差し替える。

| ID | 変異位置 | 無効化する不変条件 | 期待 kill node (候補) |
|---|---|---|---|
| M1 | `build_admission.derive_build_admission` の stock 分岐から `tracked_clean` 要求を外す | dirty no-op が stock を名乗れない | `test_build_admission.py::test_dirty_noop_does_not_derive_stock` |
| M2 | 同、stock 分岐から repo pin 照合を外す | caller 選択 checkout の自己整合だけで stock にならない | `test_build_admission.py::test_stock_requires_repo_declared_pin` |
| M3 | CLI authority 検証で plain `True` を受理する | token 以外で coder 権限が出ない | `test_build_admission.py::test_coder_requires_parser_issued_run_token` |
| M4 | `buildcache.cache_key` から admission 成分を外す | legacy key が class を跨がない | `test_buildcache_v2.py::test_legacy_key_binds_admission_for_all_classes` |
| M5 | legacy hit の sidecar exact 検証を skip する | receipt 欠落 legacy entry を hit にしない | `test_buildcache_v2.py::test_legacy_hit_requires_exact_admission_sidecar` |
| M6 | `_v2_identity` の preimage から admission を外す | v2 digest が class を跨がない | `test_buildcache_v2.py::test_v2_preimage_binds_exact_admission` |
| M7 | `_validate_v2_entry` の期待 key 集合から admission を外す | receipt 欠落 manifest を受理しない | `test_buildcache_v2.py::test_completion_manifest_rejects_missing_receipt` |
| M8 | `ident.canonical_preimage` から admission policy を外す | campaign identity が policy を跨がない | `test_campaign.py::test_campaign_id_binds_admission_policy` |
| M9 | loop replay の attempt receipt topology 検証を skip する | receipt 欠落 terminal を skip 再利用しない | `test_campaign.py::test_resume_rejects_committed_attempt_without_receipt` |
| M10 | `artifact_admission.classify_campaign` が overlay 掲載を admitted と返す | 旧 3 campaign が選択材料に入らない | `test_artifact_admission.py::test_three_legacy_campaigns_are_denied` |
| M11 | `layer3_report.build_report` 入口の validator 呼出しを外す | 材料レポートが旧成果物を描画しない | `test_layer3_report.py::test_real_legacy_s8a_campaign_is_rejected` |

**正例 (受理集合の過剰縮小の検出、`DW-M01` 後段)**

- `test_p3_build_authority_cli.py::test_stock_machine_and_opted_in_coder_paths_remain_accepted`
  — clean stock baseline (token 不要)、registered machine sweep、`--allow-coder-derived-build` 付き
  coder driver の 3 経路が通り続けることを固定する。全変異で **SURVIVED (緑のまま)** を期待し、
  ここが赤くなる変異は「承認外の過剰拒否」として扱う。

## 6. 親がやること (実装子はやらない)

- `docs/phase3-s4b-runbook.md` / `phase3-s5-sort-runbook.md` / `phase3-s8a-trigger-runbook.md` の更新
  (レンズ C-6): build / no-build の policy 差、campaign ID が変わること、旧 checkpoint は継続しないこと、
  cache が cold になること、legacy 拒否の確認方法。
- decisions fragment (新 D)、worklog fragment、insights 凍結、commit、記録後検査。
- 計算ノードでの受入全走と変異本走。
- §3 の 7 件を裁定パッケージとしてユーザーへ返す。
