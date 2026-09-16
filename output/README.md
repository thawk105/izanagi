# output — 全成果物

探索の全成果物をここに置く。**二軸構成 (D13)**: 成果物は「入力 (workload spec) に依存するか」で置き場を分ける。

```
output/
├── campaigns/<campaign-id>/      入力ごとの探索 (= 入力依存。campaign スコープ)
│   ├── campaign.lock             同一性の正準 pre-image
│   ├── spec/                     凍結した入力 spec
│   ├── runs/wal.jsonl            評価の WAL (env tag・測定値・gate結果 = forensic binding)
│   ├── variants/                 variant source/patch と build identity
│   ├── reports/                  report・plot・provenance の決定論的射影先
│   └── insights/                 campaign 固有 insight / whiteboard
├── env/<env-tag>/                環境ごと・入力非依存 (= 測定の物差し。env スコープ)
│   ├── binaries/                 測定に使う binary bytes の content-addressed store (`<binary_sha256>`)。**追跡外** (`.gitignore`)。B-4 凍結 spec の `artifacts[].binary_relpath` はここを指し、s8b floor campaign も同じ規則で置く ([T-2697])。**凍結するのは path・期待 sha256・receipt であって bytes の可用性ではない** — 全複製を失えば消費側は正しく拒否するが、bit 同一の復旧は保証しない。調達済み record からの配置は `python3 -m orchestrator.campaign.b4_binary_record place`
│   ├── calibration/              レコード数飽和点 + noise floor (within-run / between-run, A2)
│   ├── characterization/         正しさ検査の歯の実証 (correctness-only、fitness 非計測。例: t152 write-intent。必須 env は各 driver docstring が正本)
│   └── profile/                  perf 機序プロファイル (spin 分離・有用 IPC 等, P2-4)
├── insights/                     CCBench 還元すべき発見 / calibrator・探索の妥当性文書
├── runs/silo-sample/             任意・追跡外 (.gitignore) の**大規模**実 Silo trace。置いた機体でだけ追加検証される。**規律2 の常時検査はこれではなく**追跡 fixture 3 つ (orchestrator/tests/fixtures/ の g5_silo_real_prefix/ g6_silo_serial_1thread/ r8_silo_broken_norw/) が担う (契約は orchestrator/tests/README.md、独立性の射程は同 fixtures/README.md)
├── s1-freeze/                    S-1 の known-axes / measurement freeze (両者とも生成済み)
├── s1-budget/                    S-1 計測の時間台帳 (time_ledger.json)
├── s6-rounds/                    S-2/S-3 提案ラウンドの匿名化・採点・集計 provenance
├── s8b-freeze/                   段 8b holdout freeze (holdout_freeze.json)
├── s8c-preregistration/          段 8c 事前登録の**条件契約** hash 世代台帳 (condition-freeze.v1.g<N>.json)。側置きの immutable generation で、前世代の bytes hash・変更理由・裁定参照を持つ。**発効の宣言物ではない** — 発効は判定器が commit ごとに導出する (docs/phase3-8c-preregistration.md §6)。承認 record・active pointer・失効 record は置かない
├── exploration/                  探索 (非公式) 成果物の隔離 namespace (D65。official が型と marker で拒否)
│   ├── namespace.json            namespace marker (exact bytes)。official report が exploration root を拒否する唯一の根拠であり、hooks が改変・削除を拒否する
│   ├── campaigns/<campaign-id>/  s4 driver 族 (p3_s4_loop / _sort / _trigger_gating / p3_s4_red / p3_kickoff / 8c build) の**新規** campaign。構造は campaigns/ と同一で、WAL と campaign.lock は同じく hooks の保護対象
│   └── autonomous-trials/<trial-id>/ 段 8c bounded supervisor の試行 journal (D106)。attempt journal・role payload/envelope・proposal・terminal report。**探索の運用記録であって正式 proof chain ではない** — 実 build 時の WAL / campaign report の正本は exploration/campaigns/<campaign-id>/ 側
├── t189-routing-preregistration/ T-189 model 経路事前登録の**素材** (docs/phase3-t189-model-routing-preregistration.md が正本)。事前選別の候補台帳 task-catalog-v1.json、その task type 分類 task-type-classification-v1.json (基準は docs/phase3-t189-task-catalog-classification.md)、price-snapshot-v1.json と byte 同一抜粋 price-standard-table-excerpt.html、task-specific 束縛を実データで発火させる限定 task-oracle-wiring-slice-v1.json。**採用した held-out task の集合でも§8 ledger本体でもない** (同書 §§8.3, 13)
├── t080-migration/               一回限りの移行契約 receipt (D78。hooks 保護外・4 状態機械と履歴検証が正 — 発効は人間 R commit のみ)
├── task-runs/                    AI 開発作業の統計記録 (開発プロセス観測。証拠ではない — D66、詳細 task-runs/README.md)
├── dev-wave-supervisor/          bounded dev-wave supervisor の運用契約 (README.md) と private runtime (runtime/ は gitignored、control WAL・raw child 出力。[T-076]、D74)
└── reports/                      campaign 横断の材料レポート (s_prime_final_report.md, s1_direct_comparison/)
```

`<campaign-id>` = `<spec-slug>-<search-tag>-<cfg-hash8>` (内容ハッシュ、D13)。`<env-tag>` = `linux-baremetal` 等。

`s1-freeze/`・`s1-budget/`・`s6-rounds/`・`s8b-freeze/`・`s8c-preregistration/`・`reports/` は campaign を
またぐ登録済み主実験の補助成果物である。`s1-freeze/` には `known_axes_freeze.json` と `measurement_freeze.json` (freeze v2、
18 セル・比較対・schedule・実装 hash) が生成済みで、後者は S-1 計測開始 gate を閉じる時点で凍結した。
`s6-rounds/` は独立セッションの提案・匿名化・採点を結ぶ記録であり、通常の campaign 出力ではない。

## なぜ二軸か (D13)

- **campaign スコープ (入力依存)**: fitness・材料レポートは入力 workload ごとに変わる。campaign-id は spec の**中身** + ccbench-commit + 探索 config のハッシュなので、入力が変われば別 campaign になる (honest-by-construction)。
- **env スコープ (入力非依存)**: calibration (レコード数・noise floor) と profile は「測定の物差し」であって variant の fitness ではない。(env, thread数, 代表 workload) ごとに決まり入力非依存なので campaign と分ける。
- **二軸の外 (D66)**: `task-runs/` は実験証拠の二軸に属さない開発運用 namespace (開発プロセスの観測)。
  proof chain・fitness・benchmark の証拠として参照してはならず、`exploration/` と同様に official 側は
  型・path 検査で拒否する。

## proof chain の扱い

- `campaign.lock` と `campaigns/*/runs/` は proof chain の保護対象である。COMMIT/fitness を記録する唯一の
  経路は `pipeline.evaluate()` であり、直接編集・削除・移動しない。**official / exploration の双方の
  campaign tree に同じ保護が掛かる** (D123) — namespace の移動で防壁の強さを変えない。
  `exploration/namespace.json` も改変・削除を拒否する (marker が消えると official report が
  exploration root を official として受理しうるため)。
- **hooks の保護対象は repo 内の campaign tree だけ**である。exploration campaign は
  `IZANAGI_EXPLORATION_OUTPUT_ROOT` で repo 外 (job 専用領域) へ実行先を出せる ([T-422] / F98) が、
  外部 root は hooks 防護外の使い捨て領域であり、certified 材料・proof chain 素材を置かない。
  proof chain へ入る材料は従来どおり repo 内の official 経路だけが正本である。
- `exploration/autonomous-trials/` の journal は正式 proof chain ではないため、この保護の対象外である。
- `reports/` と `insights/` は生成物・散文を置く射影先で、機械防護の対象外である。ただし WAL や source
  identity と矛盾する根拠を後から書き換えてよい意味ではない。report は入力証拠を参照可能に保つ。
- throwaway な生 trace・一時バイナリ・ローカルの実行残骸は追跡しない。必要な再現根拠は WAL、lock、凍結
  spec、report/provenance、または insight に構造化して残す。

## insights の使い方

探索中に CCBench 自体の問題を見つけたら、ここに構造化レポートを吐く。例:

```
output/insights/YYYY-MM-DD/<topic>.md
  - 発見: 何が
  - 再現条件: thread/records/workload/seed
  - 該当コード: ccbench の file:line
  - 仮説: なぜそうなるか
  - CCBench論文/insight との関係
  - 還元判断: ユーザー確認待ち
```

新規の資料は日付ディレクトリにまとめる。複数ファイルなら
`output/insights/YYYY-MM-DD/<topic>/` とし、子名に日付を重ねない。
入口は `output/insights/README.md`。旧配置の資料は日付別の移動対応表から探せる。
既存の凍結資料・固定パスを使う実験の継続出力は旧位置を維持し、一括置換しない。

**CCBench のバグ等を還元する判断には必ず「還元判断: ユーザー確認待ち」を付ける。** AI は発見を構造化するところまで。上流 CCBench へ PR を出すかは人間 (ユーザー) が判断する。誤検出 (verifier のバグを CCBench のバグと誤認) を防ぐ関所。

insights には CCBench 還元候補だけでなく、**探索の妥当性文書**も置く (calibrator のレコード数決定根拠、ケーススタディの機序分析・敵対的検証、measurement 汚染インシデント等)。「なぜそのレコード数/floor/結論か」を査読に先回りで答える材料。加えて、**プロセス監査・ユーザー裁定用の凍結スナップショット** (相談・監査の逐語凍結、裁定パッケージ) も置いてよい — その場合は冒頭に `authority: none` / `default_effect: no-state-change` を明示し、可変状態の正本 (worklog 末尾・現行 phase doc) にはしない。

文献検索の実行記録は、凍結物本体を `docs/related-work/claim-survey/` に置き、頁ごと・record ごとの
機械可読な取得証拠を `output/insights/<日付>/<topic>/` の sidecar として置いてよい。sidecar は
`manifest.json` と `MANIFEST.sha256` で digest を束縛し、凍結物側が `manifest.json` の SHA-256 を
参照する。**HTTP 応答本文の全文は保存しない** — 保存するのは契約が要求する構造化台帳だけである。

`output/insights/` の寿命管理は `docs/ruleops.md` を正本とする。`authority: none` は可変状態の正本で
ないことを示すだけで、削除可能という意味ではない。RuleOps v1 は HEAD inventory と候補 package を
人間裁定へ運ぶが、自動削除、正式 report / proof chain の退役、既存 insight の一括分類は行わない。
