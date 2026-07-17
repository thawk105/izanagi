# s8b v2 前提条件 (裁定非依存 wave) — codex 敵対相談の逐語と親裁定 (2026-07-17)

- **日付:** 2026-07-17
- **記録種別:** 実装前敵対相談の逐語保存 (F20 対応 — 生成セッション内で repo へ凍結) + 親裁定
- **対象:** s8b floor protocol パッケージ「v2 前提条件」のうち裁定非依存サブセットの実装プラン
  (L1 bin_hash full 化基盤 / L2 共有 probe fail-open 是正 / L3 G6' 部分準備 / L4 phase3 (c) docs 同期 /
  L5 buildcache 結線統合テスト)
- **方式:** codex exec, model=gpt-5.6-sol, reasoning=max, sandbox=read-only, cwd=worktree-s8b-v2-prereqs
  (base = main 1b11c87)。並列 4 本 (C-α/C-β/C-γ/C-δ)
- **判定:** 4 本とも「修正後に進めよ」。所見 36 件 (must-fix 26 / should 9 / nit 0 + 判定行)
- **関連:** 裁定待ちパッケージ = `output/insights/2026-07-16_s8b-floor-protocol-package.md` (本 wave では不可触)、
  worklog 2026-07-17 (5) (本 wave のエントリ)

---

## 1. 相談プロンプト逐語

### 1.0 共通コンテキスト (全 4 本の先頭に連結)

# 共通コンテキスト (全相談共通)

あなたは izanagi リポジトリ (cwd、read-only) に対する敵対的レビュアーである。私 (親オーケストレータ) のプランを攻撃し、実装前に設計の穴を潰すのが仕事。遠慮は不要。

## プロジェクト状況

- Phase 3 (CC 合成)。段 8b の floor protocol 凍結案パッケージ (`output/insights/2026-07-16_s8b-floor-protocol-package.md`) が F1〜F7 のユーザー裁定待ち。裁定・push はすべてユーザー待ちのため、今回の wave は「裁定に依存しない v2 前提条件」だけを実装する。
- パッケージ「v2 前提条件として登録 (未実装)」6 件のうち、裁定非依存と判断した 3 件 (oracle 側 binary full-sha256 照合の基盤 / 共有 competing_bench_pids の fail-open 是正 / G6' 共有 materialization モジュール抽出) + 小粒 2 件 (phase3 checkpoint (c) 完了マーク同期 / buildcache 残骸破棄の結線統合テスト) を対象とする。
- 裁定依存の 3 件 (strict v2 verifier 本体 / manifest validator の per-pair floor 形状追随 / oracle bench_max_rounds=1 の run_contract 凍結) は**対象外**。

## 不変条件 (絶対に緩めない — 違反を見つけたら must-fix)

- 発効なし: `s8b_floor_campaign.py` の official mode 一律拒否、oracle driver run 系の gate 拒否は不変
- 規律 2: 正しさゲートを緩める変更を許さない。fail-closed を fail-open 方向に動かさない
- 規律 3: 失敗は構造化して返す (握りつぶさない)
- 凍結ファイル (`output/s8b-freeze/holdout_freeze.json` 等、SHA pin 対象) には触れない
- 本機は計測機ではない。計測を伴う検証はしない
- 裁定待ちパッケージ文書の記載と衝突する変更をしない (パッケージが「要裁定」とした事項を先取りしない)。特に worklog 2026-07-17 (2) 持ち越し (a)「run_campaign() 直呼びの official fail-open」は裁定材料のため今回触らない

## 出力形式

所見を次の形式で列挙せよ (日本語):

- **所見 ID** (レーン記号-連番): 1 行要約
  - severity: must-fix / should / nit
  - 攻撃シナリオ: 具体的にどう壊れるか・どう悪用されるか
  - 根拠: file:line (必ずリポジトリを自分で読んで確認する)
  - 提案: 具体的な修正案

最後に「プラン全体の判定: 進めてよい / 修正後に進めよ / 止めよ」を 1 行で。プランの前提事実 (file:line) が実際のコードと食い違う場合は必ず指摘せよ。

### 1.1 C-α プロンプト

# 相談 C-α: oracle 側 binary full-sha256 照合の「裁定非依存の基盤」実装プラン

所見 ID は A-1, A-2, ... を使え。

## 前提事実 (Explore 調査済み — 検証して食い違いがあれば指摘せよ)

- `BuildResult.bin_hash` = バイナリ全バイトの sha256 hexdigest の先頭 16 文字 (`orchestrator/campaign/buildcache.py:56,63-68`)。full 値は `_bin_hash()` 内で捨てられ、どこにも保持されない
- WAL `STAGE_BUILD_DONE` payload に `trace_bin`/`perf_bin` として 16 文字値が記録される (`orchestrator/campaign/pipeline.py:420-426`)
- floor driver は独自の `_full_sha256()` (`orchestrator/campaign/s8b_floor_campaign.py:129-138`) で full 値を計算し、artifact に `binary_sha256` (full) + `bin_hash_short` (= `result.bin_hash`, 16 文字) の両方を記録 (`:583-584`)。resume 時は full 再照合済み (`:1259-1287`)
- oracle 側 (`s8b_oracle_driver.py`) は binary content hash を binding identity (`_BINDING_KEYS`, `:37-40`) にも WAL 読取り (`_trial_measurements`, `:366-380`) にも一切含めない。`s8b_oracle_manifest.py` の binding schema (`:36-39`) にも無い。ここが v2 前提条件「oracle 側 binary full-sha256 照合」の未実装本体
- 永続化済みの 16 文字値 (過去 campaign WAL の trace_bin/perf_bin、`output/env/linux-baremetal/calibration/s1_verify_extime.json` の binary_hash) を長さ・完全一致で検証する消費点は無い (grep 全数確認済み)
- パッケージの G4 所見: 「恒真 claim 回避のため本パッケージでは『保証』と書かない」— 照合が実装されるまで「保証」と謳ってはいけない

## プラン (攻撃対象)

1. `buildcache._bin_hash()` を full hexdigest を返す `_full_sha256()` 相当に変え、`BuildResult` に **新フィールド `bin_sha256` (full, 64 文字) を追加**。既存 `bin_hash` は `bin_sha256[:16]` として維持 (現行値と bit 単位で同一 — 現行 short は full の接頭辞なので互換)。ファイルは 1 回だけ読む (二重読みしない)
2. WAL `STAGE_BUILD_DONE` payload に **追加キー** `trace_bin_sha256` / `perf_bin_sha256` (full) を追記。既存キー `trace_bin`/`perf_bin` (16 文字) は不変 (過去 WAL との対称性維持)。過去 WAL に新キーが無いことは、現行 consumer が新キーを読まないため無害
3. floor driver の重複実装 `_full_sha256()` を buildcache の公開関数 (例: `buildcache.full_sha256(path)`) の再利用に置換 (アルゴリズム同一なので値不変。二重実装 drift = docs/failures.md:32-34 の解消)。artifact のフィールド (`binary_sha256`/`bin_hash_short`) は形も値も不変
4. 照合ヘルパー純関数 (例: `verify_binary_sha256(expected_full: str, path: str)`) を共有モジュールに追加し unit テスト。**oracle への配線 (floor artifact の hash を oracle が消費する箇所) は freeze v2 再凍結 wave に据え置く** — 配線先の floor 値埋め込み形状が F5 裁定依存のため。今回は「full 値が生産・記録され、照合関数が存在する」まで
5. テスト: full/short の派生関係 (`bin_hash == bin_sha256[:16]`) の固定、WAL 新キーの記録確認、floor 側の値不変 (既存 golden テストが緑のまま)

## 特に攻撃してほしい点

- 新フィールド追加 vs `bin_hash` 自体の full 化、どちらが正しいか。additive 案の隠れコスト (フィールド 2 つの意味混乱、将来の誤用)
- `_BINDING_KEYS` (driver:37-40 / manifest:36-39) に今回触れない判断は正しいか。binding identity への binary hash 追加は F5/F7 裁定依存か、それとも裁定非依存で今やるべきか
- 「oracle への配線は据え置き」で v2 前提条件の意味が骨抜きにならないか。据え置くなら何を文書に残せば恒真 claim (G4) を避けられるか
- 過去 WAL / calibration artifact / layer3 report に埋まった 16 文字値との突合が将来必要になったとき、full 化した新系列と混在して事故らないか (prefix 照合の罠を含む)
- buildcache の cache hit 経路 (`buildcache.py:99-108`) と新規ビルド経路 (`:110-124`) の両方で full 値が正しく計算されるか、hash 計算タイミングの TOCTOU

### 1.2 C-β プロンプト

# 相談 C-β: 共有 competing_bench_pids の fail-open 是正プラン

所見 ID は B-1, B-2, ... を使え。

## 前提事実 (Explore 調査済み — 検証して食い違いがあれば指摘せよ)

- 定義 `orchestrator/calibrator/runner.py:107-144`。fail-open は 1 点: pgrep 起動自体の `OSError`/`subprocess.SubprocessError` を握りつぶして `[]` を返す (`:128-129`) = 「競合なし」と区別不能。さらに **pgrep の rc を検査していない** (rc>1 のエラーでも stdout 空なら「競合なし」扱い)
- PID parse 不能行は競合側に残す fails-closed (`:139-141`) — ここは既に正しい
- fail-open 契約を明示固定するテスト: `orchestrator/tests/test_calibrator.py:479-491` (`test_competing_bench_pids_pgrep_error_returns_empty`、docstring に「既存契約を維持」) — 是正時に書き換え必須
- consumer 全数:
  1. `orchestrator/campaign/p2_2.py:76-90` — `_assert_single_tenant()`: truthy なら RuntimeError。例外は捕捉していない (伝播)
  2. `orchestrator/campaign/between_run_floor.py:45,90,157` — p2_2 の `_assert_single_tenant` を素通し使用 (スタンドアロン CLI、外側捕捉なし)
  3. `orchestrator/campaign/s1_direct_comparison.py:594,621-630` — `try: single_tenant_fn() ... except Exception: budget 記録 + re-raise` = 例外でも安全
  4. `orchestrator/campaign/pipeline.py:248` — bench 直前。`if comp: return abort("bench-competing-tenant", ...)`。try 無し
  5. `orchestrator/campaign/pipeline.py:562` — S2 verify パス。`if comp: _abort("verify-competing-tenant", ...)`。try 無し
- pipeline から例外が漏れた場合の下流: (A) `loop.py:132-136` の broad except → `eval-exception: ...` abort に変換され campaign 継続 (ただし reason が汎用化)。(B) `s8b_oracle_driver.py:649` が例外を捕捉 → `_outcome_for` (`:383-401`) の既知バケツに無い reason → `_UnknownAbortReason` → deviation イベント + schedule row を error_stopped で打ち切り (`:661-671`)
- `s8b_oracle_report.py:28-31` は driver 側 `_outcome_for` と同じ reason 集合を重複定義 (分類漏れリスクを共有)
- floor driver の自前 strict probe (`s8b_floor_campaign.py:458-498`) は rc 検査 + OSError/rc>1/parse不能 → CampaignAbort の fail-closed 済み。B10' 裁定は「floor driver は当面自前 strict probe」なので**今回 floor 側は触らない**

## プラン (攻撃対象)

1. `competing_bench_pids()` を fail-closed 化: (a) pgrep 起動失敗 (`OSError`/`SubprocessError`) → 専用例外 `ProbeError` (新設、`RuntimeError` 派生) を送出。(b) rc を検査し、rc==1 → 空 (競合なし確定)、rc==0 → 現行のパース + 自己子孫除外、rc>1 → `ProbeError`。(c) rc==0 なのに stdout 空という異常も `ProbeError`。PID parse 不能行の「競合側に残す」は現行維持
2. pipeline.py の 2 消費点を `try/except ProbeError` で囲み、専用 abort reason **`bench-probe-error`** (`:248` 側) / **`verify-probe-error`** (`:562` 側) で abort() に変換 — 汎用 eval-exception 化と `_UnknownAbortReason` 打ち切りを防ぎ、reason の構造化を保つ (規律 3)
3. `s8b_oracle_driver._outcome_for` (`:383-401`) と `s8b_oracle_report.VERIFY_INCONCLUSIVE_REASONS` (`:28-31`) に新 reason 2 種を追加 (バケツ分類: probe-error は競合の存在が未確定なので「環境非シグナル」系 — bench-competing-tenant と同じバケツが自然か、それとも別バケツか、attack せよ)
4. p2_2 / between_run_floor / s1_direct_comparison は変更しない (例外伝播 = admission 失敗 = fail-closed として既に正しい挙動。s1 は budget 記録もある)
5. テスト: `test_calibrator.py:479-491` を「ProbeError 送出」に書き換え + rc>1 / rc==0-empty-stdout ケース追加。pipeline 2 消費点の probe-error abort reason テスト追加 (fixture `_mock_pipeline_multipass` の patch 形状変更が必要か確認)。between_run_floor の伝播テスト 1 本

## 特に攻撃してほしい点

- rc==1 を「競合なし確定」と信じてよいか (pgrep の rc 意味論の環境差、busybox pgrep 等)
- `ProbeError` を RuntimeError 派生にする設計 — p2_2._assert_single_tenant の RuntimeError と紛れて呼び手が誤分類しないか
- 新 abort reason 2 種の命名・バケツ分類が s8b oracle 側の既存判定表 (`_outcome_for`) の意味論と矛盾しないか。**oracle 側は現在 gate 拒否で実走しない**が、将来の実走時に false-green / false-red を作らないか
- 消費点の見落とし (私の consumer 列挙が全数か、自分で grep して確認せよ)
- fail-closed 化により「pgrep が無い開発環境でテストが壊れる」類の副作用 (既存テストは pgrep 実在に依存するものがある — test_calibrator.py:535-579 の実プロセステスト)
- この変更が裁定待ちパッケージの記載 (B10' 裁定「共有 helper 是正は v2 前提条件リストへ」) と整合するか — 「今やる」こと自体が裁定の先取りにならないか

### 1.3 C-γ プロンプト

# 相談 C-γ: G6' 共有 materialization モジュール抽出プラン

所見 ID は G-1, G-2, ... を使え。

## 前提事実 (Explore 調査済み — 検証して食い違いがあれば指摘せよ)

- G6' (パッケージ `output/insights/2026-07-16_s8b-floor-protocol-package.md:541-549,569-579`): floor が oracle の私有 helper に結合している状態の解消が v2 前提条件。「variant binding 検証・cell materialization・binding identity・trace-disabled build を公開の小さな共通モジュールへ抽出し、oracle と floor の双方を consumer にする」
- floor→oracle の依存実態 (`s8b_floor_campaign.py`): import は `:71` (モジュール) と `:74-78` (`NUMACTL`/`VerifiedFreeze`/`load_verified_freeze`)。使用は `:568` (`s8b_oracle_driver._prepared_binding` — **唯一の private 結合**)、`:1118` (`prepare_cell` 既定値)、`:1154` (`NUMACTL`)、`:1115` (`VerifiedFreeze` 型検査)、`:1337` (`load_verified_freeze`)
- `prepare_cell` は oracle 固有ではなく `s1_direct_comparison.py:467` の再エクスポート (`s8b_oracle_driver.py:25`)
- 抽出候補の実態 (`s8b_oracle_driver.py`): `_binding_entry` (`:227-238`, freeze から entry を引く純関数) / `_binding_from_prepared` (`:241-251`, identity dict 合成、依存は `pipeline.variant_id` のみ) / `_prepared_binding` (`:254-264`, contextmanager、prepare_fn 呼び出し + identity 合成 — gate/budget/schedule/marker 非依存) / `prepare_binding` (`:267-275`, 公開ラッパー)
- oracle 固有で共通化**できない**もの: `_expected_binding` (`:278-315`, oracle manifest の binding_identity 構造依存) と run_block 内の canonical bytes 比較 (`:609-619`)、cache root 差替え (`:621-626`)、`pipeline.evaluate` 契約 (`:630-648`)
- 「trace-disabled build」は oracle 側に独立関数が存在しない (pipeline.evaluate 内で trace/perf 対ビルドが不可分)。floor 側は `build_cells` (`s8b_floor_campaign.py:554-590`) が `buildcache.build(trace=False)` を直接呼ぶ
- private 名の外部 import は floor の `_prepared_binding` 1 箇所のみ (repo 全数 grep 済み)
- テストの穴: `_binding_from_prepared` が返す identity dict の**中身**を直接 assert するテストが無い (floor/oracle 双方とも間接カバレッジのみ)。抽出でシェイプが変わっても既存テストは緑になり得る

## プラン (攻撃対象)

1. **抽出前に characterization テストを書く**: `_binding_from_prepared` の identity dict のキー集合と各値の導出 (genome_canonical/src_token/variant_id/entry_sha256/binding_sha256) を固定する unit テスト。`_prepared_binding` の contextmanager 分岐 (prepare_fn が contextmanager を返す/返さない両方) も固定。これを先に緑にしてから抽出する
2. 新モジュール `orchestrator/campaign/s8b_binding.py` (仮名) を新設し、`binding_entry` / `binding_from_prepared` / `prepared_binding` / `prepare_binding` を**移動** (公開名化)。`s8b_oracle_driver` は新モジュールから import し、既存の公開名 `prepare_binding` は再エクスポートで温存 (oracle のテスト・consumer を壊さない)。private 名 `_binding_entry` 等の oracle 内 alias は残さない (呼び出し箇所を新名に更新)
3. floor 側 (`s8b_floor_campaign.py:568`) を新モジュールの公開名に置換。`prepare_cell` 既定値 (`:1118`) は `s1_direct_comparison.prepare_cell` の直接 import に置換 (oracle 経由の見せかけ依存を切る)
4. スコープの正直な縮小: G6' の 4 項目のうち「binding 検証」(oracle manifest 依存) と「trace-disabled build」(oracle 側に実体なし) は**今回抽出しない**。抽出するのは cell materialization + binding identity の 2 項目。残 2 項目は v2 再凍結 wave の設計判断として明記 (worklog に記録)
5. `NUMACTL` / `VerifiedFreeze` / `load_verified_freeze` の import は現状維持 (公開名であり G6' の指摘対象は私有 helper 結合。動かすと差分が膨らむ)
6. テスト: 抽出後に characterization テスト + 既存 suite が全部緑 (floor の fresh-run 系テストは実物 `_prepared_binding` を実行するので抽出の動作回帰を検出する)

## 特に攻撃してほしい点

- モジュール名・境界の妥当性 (`s8b_binding.py` は適切か。s1_direct_comparison の `PreparedCell` との関係でもっと自然な置き場があるか)
- 「binding 検証と trace-disabled build は今回抽出しない」の判断 — G6' の意図 (パッケージ原文を読め) を骨抜きにしないか。部分抽出が中途半端な第 3 の状態を作らないか
- `prepare_binding` 再エクスポート温存 vs 完全移行、どちらが drift を生みにくいか
- characterization テストの設計 — 値の固定が「実装詳細への過剰固定」にならない範囲はどこか (binding_sha256 の canonical bytes 計算はどこまで固定すべきか)
- floor は「裁定待ちパッケージが記述した実装」そのもの — 抽出リファクタで floor の挙動・artifact が 1 bit でも変わると裁定材料が陳腐化する。値不変を保証する検証手段は何か
- import cycle のリスク (新モジュールが pipeline を import し、oracle/floor が新モジュールを import する構図で循環しないか、実際の import グラフを確認せよ)

### 1.4 C-δ プロンプト

# 相談 C-δ: wave 全体のスコープ妥当性 + docs 同期 + buildcache 結線統合テスト

所見 ID は D-1, D-2, ... を使え。

## wave 全体像 (攻撃対象)

worklog 末尾 (docs/worklog.md 2026-07-17 (1)〜(4)) の「次の一手」はすべてユーザー待ち (ブランチ push / s8b パッケージ F1〜F7 裁定)。そこで本 wave は裁定非依存の前進として以下を選定した:

- レーン 1: buildcache full sha256 基盤 (oracle 照合の前提。oracle への配線自体は F5 裁定後の v2 wave に据え置き)
- レーン 2: 共有 competing_bench_pids の fail-open 是正 (consumer 受け皿 = pipeline に専用 abort reason 2 種追加)
- レーン 3: G6' のうち cell materialization + binding identity の共通モジュール抽出 (binding 検証と trace-disabled build は v2 wave に据え置き)
- レーン 4: docs 同期 — phase3.md 現行チェックポイント「次:」の (c) (二波監査記録の凍結) に完了マークを付ける
- レーン 5: buildcache 残骸破棄の結線統合テスト 1 本 (見送り台帳からの昇格)

対象外に据え置いた裁定依存 3 件: strict v2 verifier 本体 / manifest validator の per-pair floor 形状追随 / oracle bench_max_rounds=1 の run_contract 凍結。

## 攻撃してほしい問い

1. **裁定先取りの検査**: レーン 1〜3 は本当に F1〜F7 裁定と独立か。裁定のどの択が選ばれても無駄・矛盾にならないか。パッケージ (`output/insights/2026-07-16_s8b-floor-protocol-package.md`) の「v2 前提条件として登録 (未実装)」節と「不採用・縮小した敵対所見」節を読み、「今やる」ことが裁定文書の前提を変えてしまう箇所がないか
2. **裁定材料の陳腐化**: 実装により裁定待ちパッケージの記述 (実装状況節など) が事実と乖離する。パッケージ文書に日付つき追記をすべきか、worklog 記録だけに留めるべきか。ユーザーが裁定するとき混乱しない形は何か
3. **レーン 4 の完了認定の証拠**: phase3.md の checkpoint 次 (c) は「二波監査記録の凍結」。worklog 2026-07-16 (9) (docs/archive/worklog-phase3-0714-0716.md 内) に消化記録 (commit 4bde427、成果物 `output/insights/2026-07-16_s8b-two-wave-audit-reconstruction.md` 等) がある。一方 phase3.md の同じ (c) 文面は将来形のまま。完了マークを付けてよいか — worklog (9) の記録に「(c) のうち未消化の残り」が含まれていないか自分で読んで検証せよ (特に: 第 3 波監査の A3-3/A3-4 は worklog 2026-07-16 (11) で裁定承認、(12) で実装 wave 1 消化とされるが、それが (c) の完了に必要な条件かどうか)
4. **レーン 5 の設計**: 統合テスト案 = `_fake_ccbench_repo()` で repo を作り、`cache_key()` で bdir を算出、bdir に `CMakeCache.txt` (残骸マーカー) を事前設置、`buildcache._run` を fake 化 (configure 時に「マーカーが既に消えていること」を assert する = 順序性の直接検証)、`buildcache.build()` を実呼び出し。この設計で「build() が configure 前に破棄を呼ぶ結線」を将来 refactor から守れるか。fake の仕方に穴はないか (`orchestrator/tests/test_campaign.py:2098-2138` の既存パターン参照)
5. **wave の粒度**: 5 レーンを 1 branch / 1 PR 相当にまとめる予定。分割すべきか。commit 分割の単位はどうあるべきか (レーンごと? 全部 1 commit?)
6. **見落とし**: 裁定非依存で本来今やるべきなのに私が拾っていない開タスクが repo 内にないか (docs/phase3.md の見送り台帳、docs/worklog.md、output/insights の未消化所見から探せ)。逆に「やらない方がよい」レーンはどれか

---

## 2. 相談出力逐語

### 2.1 C-α 出力

- **A-1**: WAL への full hash 追記だけでは、oracle の bench 前拒否関所にならない
  - severity: must-fix
  - 攻撃シナリオ: `pipeline.evaluate()` は build 後に WAL を書くが、そのまま verify・bench まで実行する。oracle driver が新 WAL を読むのは `evaluate_fn()` の復帰後なので、将来 `_trial_measurements()` で照合しても「異なる binary を計測した後の事後検知」にしかならない。
  - 根拠: `orchestrator/campaign/pipeline.py:409-426`, `orchestrator/campaign/pipeline.py:587-595`, `orchestrator/campaign/s8b_oracle_driver.py:631-658`
  - 提案: 今回、期待値の取得元とは独立した post-build/pre-run gate を `pipeline.evaluate()` に設ける。例えば `expected_perf_sha256` または build-gate callback を、build 完了直後かつ trace/bench 起動前に発火させる。mismatch は expected/actual/path を持つ構造化 abort とし、`_run_trace`・`_run_bench` が一度も呼ばれない positive control を置く。floor と照合するのは trace-disabled の `pf` であり、`trace_bin_sha256` は当面 provenance に限定する。

- **A-2**: 「producer + 未配線 helper」を oracle 側 prerequisite 完了として扱うと G4 を再発する
  - severity: must-fix
  - 攻撃シナリオ: full 値と未使用 helper の存在だけでチェック項目を完了にすると、再凍結 wave が「binary 照合済み」と誤認して進む。パッケージ自身はこの項目を「floor hash を消費する側」と定義しており、今回のプランはそこを一切実装しない。
  - 根拠: `output/insights/2026-07-16_s8b-floor-protocol-package.md:532-536`, `output/insights/2026-07-16_s8b-floor-protocol-consultations.md:316-324`, `docs/worklog.md:66-71`
  - 提案: 台帳を「full digest 生産/WAL 記録基盤」と「ratified v2 の期待値取得 + pre-launch perf 照合 + report 再検証」に分割する。前者だけ完了可、後者と総項目は未完了のままにする。文書には `NOT ENFORCED`、`実行 byte の同一性は未保証`、残る acceptance criteria を明記し、「保証」「照合済み」「同一 binary」は使わない。

- **A-3**: additive 方向は正しいが、full/short を独立した可変フィールドにすると矛盾した identity を生成できる
  - severity: must-fix
  - 攻撃シナリオ: refactor や fake が `bin_sha256=A`、`bin_hash=B[:16]` を返しても、WAL と floor artifact は両方をそのまま記録する。現に floor の fake は binary の実 byte ではなく `src_token` を short hash にしており、既存 golden がこの矛盾を許している。artifact 自己検査も `binaries` を検査しない。
  - 根拠: `orchestrator/campaign/buildcache.py:51-60`, `orchestrator/campaign/s8b_floor_campaign.py:577-585`, `orchestrator/tests/test_s8b_floor_campaign.py:171-180`, `orchestrator/campaign/s8b_floor_stats.py:298-310`, `orchestrator/campaign/s8b_floor_stats.py:386-410`
  - 提案: canonical storage は検証済み 64 文字 lowercase の `bin_sha256` 一つにし、`bin_hash` は read-only property または `init=False` の `bin_sha256[:16]` にする。`BuildResult` は frozen、生成は keyword 引数にする。`bin_hash` 自体の full 化は、calibration の `binary_hash` と floor の `bin_hash_short` の既存意味を変えるため不採用が正しい (`orchestrator/campaign/s1_verify_extime_calibration.py:340-408`, `orchestrator/campaign/s8b_floor_campaign.py:583-584`)。

- **A-4**: 「一回だけ読む」と floor 側での再ハッシュが矛盾し、さらに可変 path と実行 byte の TOCTOU が残る
  - severity: must-fix
  - 攻撃シナリオ: プラン 3 のまま floor が公開 helper を再度呼ぶと、buildcache と floor で二回読む。間に binary が差し替われば `binary_sha256` と `bin_hash_short` が別 byte 系列になる。さらに hash 後に差し替えれば、artifact は A を記録しながら session は B を実行できる。resume も全 session 前ではなく開始時に一度照合するだけである。
  - 根拠: `orchestrator/campaign/buildcache.py:99-108`, `orchestrator/campaign/buildcache.py:110-125`, `orchestrator/campaign/s8b_floor_campaign.py:572-589`, `orchestrator/campaign/s8b_floor_campaign.py:734-752`, `orchestrator/campaign/s8b_floor_campaign.py:1180-1189`
  - 提案: fresh artifact は `result.bin_sha256` とその派生 short を使い、再読はしない。公開 helper は resume/pre-launch 再照合に使う。最終的な「実行 byte 保証」には、各起動直前の exact 再照合だけでなく、通常ファイル・非 symlink 検査、hash 前後の `fstat`、cache-key 排他、可能なら digest 名の create-only snapshot または hash 済み fd を実行する設計が必要。一回の path hash は provenance snapshot とだけ記述する。

- **A-5**: 共有 hash/helper の例外契約が未定義で、構造化失敗を破る
  - severity: must-fix
  - 攻撃シナリオ: 現行 `_bin_hash()` は `OSError` を素通しする一方、pipeline の build 隔離は `RuntimeError` と `SubprocessError` しか捕捉しない。floor の CLI も `FloorCampaignError` だけを JSON 化する。単純な共通化では、不在・権限・途中消失が WAL abort や JSON error でなく traceback になる。
  - 根拠: `orchestrator/campaign/buildcache.py:63-68`, `orchestrator/campaign/pipeline.py:409-419`, `orchestrator/campaign/s8b_floor_campaign.py:129-138`, `orchestrator/campaign/s8b_floor_campaign.py:1333-1347`
  - 提案: `BinaryDigestError(RuntimeError)` と `BinaryDigestMismatch` を定義し、path・expected・actual・cause を保持する。floor はこれを `FloorCampaignError` に変換する。`verify_*` が bool を返す曖昧な API ではなく、成功時のみ復帰する `assert_binary_sha256()` とする。不在・読取不能・mismatch の各テストで構造化出力と「build_done/bench なし」を固定する。

- **A-6**: legacy 16 文字系列と full 系列の移行規則がなく、将来の prefix 照合事故を予約している
  - severity: must-fix
  - 攻撃シナリオ: v2 consumer が新キー欠損時に `trace_bin`/`binary_hash` へ fallback し、`actual.startswith(short)` で通すと、64-bit prefix を full identity に昇格してしまう。現在 disk の再ハッシュによる過去 record の backfill も、当時実行した byte の証明にはならない。layer3 report は WAL payload を丸ごと複写するので、新旧系列が同じ schema 内に混在する。
  - 根拠: `orchestrator/campaign/wal.py:27-36`, `output/env/linux-baremetal/calibration/s1_verify_extime.json:58-63`, `orchestrator/campaign/layer3_report.py:185-203`, `orchestrator/campaign/buildcache.py:245-250`
  - 提案: `*_bin` と `binary_hash` は永続的に `sha256-prefix-16/legacy-display-only`、`*_bin_sha256` は exact 64 lowercase と契約化する。v2 は full 欠損を `unknown/unavailable` として拒否し、prefix fallback・現在 disk からの遡及 backfill を禁止する。full/short 関係、15/16/63/65文字、非 hex、正しい prefix だが異なる full hash の負例を置く。

- **A-7**: `_BINDING_KEYS` を今変更しない判断は正しいが、前提調査は report 側の第三 schema を落としている
  - severity: should
  - 攻撃シナリオ: driver と manifest だけへ binary field を足すと report が exact-key 不一致で全拒否する。また現行 `binding_sha256` は build 前の materialization identity から算出されるため、binary hash を混ぜると manifest v1 の意味と digest が変わり、F5/F7 を先取りする。
  - 根拠: `orchestrator/campaign/s8b_oracle_manifest.py:20-39`, `orchestrator/campaign/s8b_oracle_manifest.py:349-390`, `orchestrator/campaign/s8b_oracle_driver.py:241-250`, `orchestrator/campaign/s8b_oracle_report.py:241-276`
  - 提案: 今回は driver・manifest・report の三つの v1 schema を全て不変と明記する。裁定後は、source/materialization binding と expected binary digest を安易に同一 field へ混ぜず、versioned な `binary_expectations` 等の別区画を候補にする。採用形状に応じ manifest/driver/report と `binding_sha256` preimage を同時更新し、schema version を上げる。

- **A-8**: テスト計画が helper 単体と happy-path golden に偏り、結線消失を殺せない
  - severity: should
  - 攻撃シナリオ: full helper が正しくても pipeline が新 WAL キーを書かない、cache-hit だけ旧 short のまま、pre-run gate が呼ばれない、といった回帰が全緑になり得る。「既存 golden が緑」は、現在すでに不整合な floor fake を通しているため証拠にならない。
  - 根拠: `orchestrator/tests/test_campaign.py:2060-2093`, `orchestrator/tests/test_campaign.py:2098-2136`, `orchestrator/tests/test_s8b_floor_campaign.py:171-180`, `docs/failures.md:88-100`
  - 提案: cache-hit/fresh 両経路で 64文字値・派生 short・hasher 呼出し回数を固定する。加えて WAL 四キー、hash 読取失敗、short-only legacy、prefix-only mismatch、floor fake の実 byte 整合、pre-run mismatch 時の trace/bench 未呼出し、旧 WAL/layer3 の legacy 読取りをそれぞれ結線テストにする。

プラン全体の判定: 修正後に進めよ
### 2.2 C-β 出力

- **B-1**: `rc==1` の無条件受理は procps-ng 以外で再び fail-open になる
  - severity: must-fix
  - 攻撃シナリオ: procps-ng では rc=1 が「一致なし」だが、BusyBox の `pgrep` は `-a` をサポートしない。PATH 上の実装が BusyBox 等なら `pgrep -af` の構文エラーが rc=1・空 stdout になり、「競合なし」と誤認され得る。また計画の `rc>1` だけではシグナル終了を表す負の returncode も漏れる。[procps-ng の rc 契約](https://man7.org/linux/man-pages/man1/pgrep.1.html)、[BusyBox の option 一覧](https://busybox.net/downloads/BusyBox.html)、[BusyBox pgrep の option string](https://coral.googlesource.com/busybox/+/refs/tags/1_24_1/procps/pgrep.c)
  - 根拠: `orchestrator/calibrator/runner.py:125-132`、`orchestrator/tests/test_calibrator.py:535-540`、`output/insights/2026-07-16_s8b-floor-protocol-package.md:173-178`
  - 提案: 使用する絶対パスを解決して procps-ng/capability を検証するか、少なくとも「rc=1 かつ stdout/stderr とも空」の場合だけ無競合とする。rc=0 は非空 stdout 必須、それ以外は負値を含め全て専用例外。stderr も取得・記録する。

- **B-2**: 「fail-open は起動失敗と rc 未検査だけ」という前提は、自己子孫除外により成立しない
  - severity: must-fix
  - 攻撃シナリオ: 直前の `ycsb_*.exe` が現在の driver の生きた子プロセスとして残ると、CPU を消費していても子孫集合で除外され、次の計測が開始される。既存テスト自身が「自分の直前 run の残骸」を非競合として固定している。所有者が同じでも計測汚染は同じである。
  - 根拠: `orchestrator/calibrator/runner.py:119-124,133-143`、`orchestrator/tests/test_calibrator.py:429-455,564-576`、`docs/failures.md:36-43`。一方、既存設計素材は子孫除外を明記しており、現状は設計自体と衝突する: `output/insights/2026-07-16_s8b-freeze-v2-design-material.md:422-425`
  - 提案: admission は自 PID だけを除外し、生存する `ycsb` 子孫は競合として残す。あるいは「合法的に生存してよい子 PID」を明示追跡する。この変更は既存設計記載と衝突するため、黙って実装せず先に記載を裁定・整合させる。

- **B-3**: consumer 列挙が全数でなく、probe 障害が回復後も terminal poison になる経路を見落としている
  - severity: must-fix
  - 攻撃シナリオ: 一時的な probe 障害が dedicated abort になると、通常 loop は `identity-error` 以外を terminal として次回も永久 skip、screening driver も terminal を無条件 skip する。S-1 は新 reason を既知集合に持たないため `abandoned` となり、環境非シグナルなのに retry 枠を使わない。
  - 根拠: `orchestrator/campaign/loop.py:66-84`、`orchestrator/campaign/screening_driver.py:133-136`、`orchestrator/campaign/s1_direct_comparison.py:549-559,762-773`。未列挙 consumer には `backoff_overthrottle.py:61`、`backoff_profile.py:134,232`、`backoff_repro.py:89`、`backoff_sweep.py:102,123`、`p3_s4_loop.py:782-784`、`s6_sort_sweep.py:209`、`s8a_trigger_sweep.py:252` 等がある。パッケージが即時是正を見送った理由も consumer 影響である: `output/insights/2026-07-16_s8b-floor-protocol-package.md:566-568`
  - 提案: probe-error 2 種を共有の「環境故障・再評価可能」集合にし、`loop.py`、`screening_driver.py`、S-1 分類へ明示配線する。実競合の既存 reason は従来どおり terminal のままにする。その他の standalone consumer は伝播で安全だが、全参照を監査記録へ載せる。

- **B-4**: S2 probe は verdict 初期化より前にあり、legacy の `serializable` を abort 結果へ持ち越す
  - severity: must-fix
  - 攻撃シナリオ: legacy が pass した後、S2 admission で競合または `ProbeError` が起きると、`_run_one_pass()` が呼ばれないため `res.verdict=""` が実行されない。結果は `aborted=True` なのに `verdict="serializable"` という矛盾した正しさシグナルになる。
  - 根拠: `orchestrator/campaign/pipeline.py:430-437,551-570`、既存の早期 reject 回帰テスト `orchestrator/tests/test_campaign.py:1237-1252`
  - 提案: 各 pass のループ先頭、probe より前で verdict を消去する。`verify-competing-tenant` と `verify-probe-error` の双方で空 verdict、S2 workload tag、S2 trace 未実行を assert する。

- **B-5**: `bench-probe-error` を `VERIFY_INCONCLUSIVE_REASONS` に入れる案は stage 契約を壊す
  - severity: must-fix
  - 攻撃シナリオ: bench 用 reason まで verify allowlist に入れると、legacy pass・S2 missing の壊れた WALを `verify-inconclusive` として受理できる。また現行 report の `bench-failed` 分岐は abort reason を検査しないため、両 verify 後の任意 abort を bench failure と偽装できる。
  - 根拠: `orchestrator/campaign/s8b_oracle_driver.py:383-401`、`orchestrator/campaign/s8b_oracle_report.py:28-31,420-435`、`orchestrator/campaign/s8b_oracle_judge.py:64-70,82-101`
  - 提案: `verify-probe-error → verify-inconclusive`、`bench-probe-error → bench-failed` と stage 別に固定する。verify 集合へ入れるのは前者だけ。report に `BENCH_FAILED_REASONS` を新設して既存3種と後者を閉じた表で検査する。新 outcome は不要で、どちらも judge では `unknown` になることを試験する。

- **B-6**: 専用 abort reason だけでは probe 故障原因が WAL から失われる
  - severity: must-fix
  - 攻撃シナリオ: missing binary、rc=2、シグナル終了、rc=0/空出力がすべて同じ reason だけになると、再起動後に原因を区別できない。`_abort()` の note は WAL payload に入らず、oracle は WAL の abort payload だけを読む。
  - 根拠: `orchestrator/campaign/pipeline.py:395-405,414-419`、`orchestrator/campaign/s8b_oracle_driver.py:366-380`
  - 提案: `CompetingBenchProbeError(RuntimeError)` のように対象を明示した名前とし、`kind`、argv、returncode、errno、stdout/stderr の上限付き抜粋を保持する。RuntimeError 派生自体は互換性上妥当だが、pipeline は専用型だけを捕捉し、WAL の `probe_error` object に構造化して載せる。

- **B-7**: テスト計画は既存 unit fake を即座に壊し、下流分類の回帰も覆わない
  - severity: must-fix
  - 攻撃シナリオ: 現在の fake result には `returncode` がなく、rc 検査追加後は期待した `ProbeError` でなく `AttributeError` になる。また pipeline テストだけでは S-1 の abandoned 化、loop/screening の永久 skip、oracle report の reason-table drift を検知できない。
  - 根拠: `orchestrator/tests/test_calibrator.py:409-413,438-441,464-467`、`orchestrator/tests/test_campaign.py:513,1125`、`orchestrator/tests/test_s8b_oracle_driver.py:448-485`、`orchestrator/tests/test_s8b_oracle_report.py:222-245`
  - 提案: fake を `returncode/stdout/stderr` 完備に更新し、正常 rc=1、rc=1+stderr、rc=0空、rc=2/3、負値、OSError、SubprocessError を網羅する。pipeline 両 fixture に例外注入点を足し、S-1 retry、loop/screening 再実行、driver/report/judge の2 reason を追加する。pgrep 不在環境の実プロセステストは既に `shutil.which()` で回避されるため、unit test を実物依存にしなければ開発環境は壊れない: `test_calibrator.py:535-540,564-568`

プラン全体の判定: 修正後に進めよ
### 2.3 C-γ 出力

- **G-1**: 4 項目中 2 項目への縮小は G6' の実装ではなく要件変更である
  - severity: must-fix
  - 攻撃シナリオ: floor は引き続き `buildcache.build(trace=False)`、oracle は `pipeline.evaluate` 内の別呼出しを使うため、引数・cache root・trace 設定が将来 drift する。「共有 materialization 前提条件を完了」と記録すると、同一 binary の根拠がない第 3 の状態を正式化する。
  - 根拠: `output/insights/2026-07-16_s8b-floor-protocol-package.md:541-549,569-579`、`orchestrator/campaign/s8b_floor_campaign.py:554-590`、`orchestrator/campaign/pipeline.py:407-424`、`orchestrator/campaign/s8b_oracle_driver.py:609-648`
  - 提案: `_expected_binding` の manifest 探索だけは oracle adapter に残してよいが、期待値と実体値の共通検証、cell materialization、identity 生成、trace-disabled build を今回共有化する。実施しないなら変更名を「G6' 部分準備」に落とし、G6' 自体は未完了のまま残す。

- **G-2**: `prepare_cell` の直接 import は cell materialization の抽出になっていない
  - severity: must-fix
  - 攻撃シナリオ: 新モジュールが S-1 driver の `PreparedCell` と `prepare_cell` に依存したままでは、S-1 固有の初期化・cache root・将来変更が oracle/floor を巻き込む。さらに `isinstance` が厳密なので、後から同型 dataclass を新モジュールへ複製すると全 materialization が拒否される。
  - 根拠: `orchestrator/campaign/s1_direct_comparison.py:93-99,467-540`、`orchestrator/campaign/s8b_oracle_driver.py:241-243,267-275`、`orchestrator/campaign/s8b_floor_campaign.py:1115-1119`
  - 提案: `PreparedCell` と実 materializer の所有元を `variant_materialization.py` または `s8b_materialization.py` に移す。S-1 の旧名を残す場合は同一 class/function の再エクスポートにし、`is` で同一性を検査する。4 項目を収容するなら `s8b_binding.py` は狭すぎる。

- **G-3**: 移動対象の依存関係に canonical helper と `OracleDriverError` が脱落しており、素直な移動は循環か例外契約変更になる
  - severity: must-fix
  - 攻撃シナリオ: 新モジュールから oracle の `_canonical_sha256`／`OracleDriverError` を import すれば `oracle → binding → oracle` の循環になる。独自 `BindingError` に変えると、oracle WAL の理由文字列が変わり、floor CLI は `FloorCampaignError` しか捕捉しないため不正 entry や materializer failure が JSON でなく traceback になる。
  - 根拠: `orchestrator/campaign/s8b_oracle_driver.py:43-44,61-72,227-251,685-688`、`orchestrator/campaign/s8b_floor_campaign.py:349-383,1343-1347`
  - 提案: 共通モジュールは oracle を一切 import せず、共通の canonicalization と `MaterializationError` を所有する。oracle/floor の境界でそれぞれ `OracleDriverError`／`FloorCampaignError` へ因果付き変換し、CLI JSON・WAL の構造化失敗を固定する。`binding → s1 → pipeline` 自体は現状 acyclic だが、この逆 import を入れないことを明記する。

- **G-4**: 現行 fresh-run suite は bit-for-bit 不変性を証明せず、プランのテスト前提が事実と違う
  - severity: must-fix
  - 攻撃シナリオ: identity の canonical preimage、Unicode 処理、`binding_sha256` の自己 field 除外を変えても、期待値を本番 helper から計算するテストなら緑になる。既存 floor テストは常に fake materializer/build を注入し、golden も floor 数値しか固定しないため、binding、manifest bytes、`manifest_sha256` の変化を見逃す。
  - 根拠: `orchestrator/tests/test_s8b_floor_campaign.py:152-203,789-825`、`orchestrator/campaign/s8b_floor_campaign.py:578-589,622-632,1172-1173`、`orchestrator/campaign/s8b_oracle_driver.py:244-250`
  - 提案: production helperを使わず、literal canonical bytes と SHA-256 を固定する。少なくとも STOCK/non-STOCK、Unicode・入れ子を含む実 freeze 相当 entry、5 キー集合、`binding_sha256` の4-key preimageを網羅する。固定 path/hash を返す fake で `build_cells` と `manifest.json` bytes/hash の golden も保持し、抽出前後で照合する。計測は不要。

- **G-5**: contextmanager の「二分岐」だけでは一時 worktree の生存期間と cleanup 契約を守れない
  - severity: should
  - 攻撃シナリオ: refactor で manager を consumer の build/evaluate より先に exit しても、現在の fake は永続する文字列 path を返すため緑になり得る。実物では `ExitStack` 終了時に checkout が破棄され、build が消滅済み tree を参照する。
  - 根拠: `orchestrator/campaign/s1_direct_comparison.py:492-540`、`orchestrator/campaign/s8b_floor_campaign.py:568-576`、`orchestrator/campaign/s8b_oracle_driver.py:604-648`、`orchestrator/tests/test_s8b_floor_campaign.py:152-162`
  - 提案: `alive` flag を持つ manager で、consumer 中は alive、終了後は exit 1 回、identity/build例外時にも cleanup、cleanup例外は握りつぶさないことを検査する。`hasattr(__enter__)` という実装詳細は固定せず、raw resource 対応を公開契約にするか削るか決める。

- **G-6**: identity producerだけを移しても schema と verifier の三重実装が残る
  - severity: must-fix
  - 攻撃シナリオ: 共通 producer のキーや canonicalizationだけが変わると、oracle driver、manifest validator、report verifier のいずれかだけが受理・拒否し、凍結済み identity が consumerごとに異なる意味を持つ。これは G6' が防ごうとした drift そのもの。
  - 根拠: `orchestrator/campaign/s8b_oracle_driver.py:37-40,244-250`、`orchestrator/campaign/s8b_oracle_manifest.py:36-56,361-390`、`orchestrator/campaign/s8b_oracle_report.py:241-276`
  - 提案: 共通モジュールを projected binding keys、canonical binding bytes/hash、期待値との厳密比較の正本にする。manifest 固有の holdout/configuration 探索だけを adapter として残して共通 verifierへ渡す。これは per-pair floor schema 裁定とは独立している。

- **G-7**: materializer の source pin が抽出先を覆わず、generator provenance が恒真化する
  - severity: must-fix
  - 攻撃シナリオ: binding/materialization の実装を新ファイルへ移しても manifest が引き続き `s1_direct_comparison.py` だけを `materializer` として pin すれば、新ファイル改変後も generator hash 検査を通る。
  - 根拠: `orchestrator/campaign/s8b_oracle_manifest.py:309-331`、`orchestrator/tests/test_s8b_oracle_manifest.py:100-104`、`orchestrator/tests/test_s8b_oracle_driver.py:154-158`
  - 提案: 実装を単一共通ファイルへ集約して既存 `materializer` record をそのファイルへ向ける。複数ファイルに分けるなら、閉じた source bundle 全体を hash 束縛する。凍結済み freeze は変更しない。

- **G-8**: `prepare_binding` の oracle 再エクスポートは、現状の repo 内需要では不要
  - severity: should
  - 攻撃シナリオ: wrapper再エクスポートにすると既定 materializerや例外変換が共通 API とずれ、テストが旧 oracle 経路だけを通して新モジュールの公開 import 契約を検査しない。
  - 根拠: `orchestrator/campaign/s8b_oracle_driver.py:267-275`、`orchestrator/tests/test_s8b_oracle_driver.py:125-136`。repo全数検索では後者が唯一の consumer。
  - 提案: repo consumerを完全移行して再エクスポートを削除する。外部互換性が明示的に必要なら、単純 alias か例外変換 wrapperかを決め、その差をテストする。動作テストの正本は必ず新モジュールを直接 import する。

- **G-9**: 公開名だけ残す方針では floor→oracle の import-time 密結合は解消しない
  - severity: should
  - 攻撃シナリオ: floor の importだけで oracle 固有の pipeline、budget、marker、manifestまでロードされるため、そのどれかの import失敗や将来の back-edge で floor が main の official拒否に到達する前に落ちる。
  - 根拠: `orchestrator/campaign/s8b_floor_campaign.py:71-78`、`orchestrator/campaign/s8b_oracle_driver.py:23-30`、`output/insights/2026-07-16_s8b-floor-protocol-package.md:569-576`
  - 提案: `VerifiedFreeze/load_verified_freeze` は中立な freeze I/O モジュールへ移し、NUMA値は既に floor が読む `p2_2` の同値契約か小さな共有定数へ寄せる。両順序の cold-import smoke testを追加する。残すなら「private helperだけ解消し、oracle module依存は未解消」と記録する。

プラン全体の判定: 修正後に進めよ
### 2.4 C-δ 出力

- **D-1**: 「裁定非依存 3 件を実装」というスコープ表現は事実と不一致で、レーン 1・3 は部分基盤にすぎない
  - severity: must-fix
  - 攻撃シナリオ: worklog/phase で 3 前提条件を「完了」と記録すると、後続 wave が oracle の full SHA 照合や G6' 境界を実装済みと誤認する。実際にはレーン 1 は hash の生成・記録だけで照合 consumer がなく、レーン 3 も binding 検証・trace-disabled build を残すため、F14 型の恒真保証になる。
  - 根拠: `output/insights/2026-07-16_s8b-floor-protocol-package.md:532-549`、`docs/handoff/2026-07-17-s8b-v2-prereqs.md:49-58`
  - 提案: wave 名と完了記録を「full SHA 基盤」「G6' 部分抽出」と限定する。oracle 照合と G6' 残部は明示的な開タスクのまま残し、「3/6 完了」と数えない。

- **D-2**: 「v2 前提条件は 6 件」というプラン前提は誤りで、G5' env contract が一覧外に脱落している
  - severity: must-fix
  - 攻撃シナリオ: 6 件だけを消化して v2-ready と判断すると、Pegasus 上でも `linux-baremetal`、CLK=1800、48 threads、1M records、固定 NUMA を持ち込む移行 blocker が不可視になる。
  - 根拠: `output/insights/2026-07-16_s8b-floor-protocol-package.md:284-305`、同`:310-311`、同`:561-562`、`orchestrator/campaign/p2_2.py:39-47`、`orchestrator/campaign/s8b_oracle_driver.py:33-36`
  - 提案: G5' を少なくとも第 7 の pending prerequisite として正規台帳へ戻す。ただし F4/env_tag と環境 adapter の形に依存するため、今回実装せず「裁定依存・対象外」と明記する。共有 probe 是正後の floor driver 切替も、同パッケージ`:192-193`どおり残タスクとして保持する。

- **D-3**: 新しい probe error を pipeline の通常 abort にすると、環境故障が variant の permanent skip に化ける
  - severity: must-fix
  - 攻撃シナリオ: ある 1 variant の直前だけ `pgrep` が rc>1/OSError になると、`bench-probe-error` 等が terminal WAL になる。次回再開でもその variant だけ永久に落ち、残りの候補から選択が進む。これは variant 固有欠陥ではなく transient infra failure である。
  - 根拠: `orchestrator/campaign/pipeline.py:395-405`、同`:248-252`、同`:562-570`、`orchestrator/campaign/loop.py:66-80`、`docs/handoff/2026-07-17-s8b-v2-prereqs.md:53-55`
  - 提案: 新 reason を recovery の retryable 集合へ加え、run1=probe failure、run2=復旧後に同一 variant を再評価する番人テストを置く。より強くするなら `ProbeError` は variant abort にせず campaign-scoped failure として伝播させる。

- **D-4**: probe error を oracle の `bench-failed` / `verify-inconclusive` に写像する案は停止意味論を先取りする
  - severity: must-fix
  - 攻撃シナリオ: `pgrep` 実行不能を通常 trial outcome にすると、oracle driver は `trial-result` と budget entry を書き、全行なら campaign を `completed` にできる。裁定案は probe 実行不能・rc>1 を campaign abort としており、retry・課金・resume の意味が変わる。
  - 根拠: `output/insights/2026-07-16_s8b-floor-protocol-package.md:173-178`、同`:503-506`、`docs/handoff/2026-07-17-s8b-v2-prereqs.md:53-55`、`orchestrator/campaign/s8b_oracle_driver.py:383-401`、同`:697-754`
  - 提案: pipeline の構造化 reason 追加まではよいが、oracle `_outcome_for` と report allowlist への追加は裁定後へ据え置く。現時点では未知 reason として driver を `error` 停止させ、reservation を精算しない側が安全。

- **D-5**: shared probe の consumer 棚卸しが「5 箇所」で止まり、`_assert_single_tenant` の広い fan-out を数えていない
  - severity: should
  - 攻撃シナリオ: `ProbeError` の新規送出が歴史 driver 群へ伝播し、ある CLI は構造化拒否、別の CLI は生 traceback という不統一になる。テストも pipeline と数個だけ通って変更影響を過小評価する。
  - 根拠: `docs/handoff/2026-07-17-s8b-v2-prereqs.md:17-23`、`orchestrator/campaign/p2_2.py:71-90`、`orchestrator/campaign/backoff_sweep.py:32,102-123`、`orchestrator/campaign/p3_s4_loop.py:782-784`、`orchestrator/campaign/s8a_trigger_sweep.py:80,252`
  - 提案: fan-out は中央 adapter 利用として明文化し、`ProbeError` に kind/rc/stdout/stderr/error を持たせる。OSError、rc=1、rc=0、rc>1、矛盾した rc=0+空出力を固定し、pipeline WAL payloadにも構造化詳細を残す。

- **D-6**: レーン 3 案は実際の cell materializer を抽出せず、S-1 driver 上の facade を増やすだけ
  - severity: must-fix
  - 攻撃シナリオ: `_prepared_binding` 等だけを移し、`prepare_cell` を直接 import すると、共通 module は依然 `s1_direct_comparison.py` の orchestration 実装に依存する。将来 S-1 側の materializer が変わると oracle/floor の共有境界も一緒に揺れる。さらに `_binding_entry` は `OracleDriverError` を投げるため、そのまま移すと循環 import か例外契約の無断変更になる。
  - 根拠: `docs/handoff/2026-07-17-s8b-v2-prereqs.md:56-58`、`orchestrator/campaign/s1_direct_comparison.py:94`、同`:466-539`、`orchestrator/campaign/s8b_oracle_driver.py:25`、同`:227-264`、`output/insights/2026-07-16_s8b-floor-protocol-package.md:541-549`
  - 提案: `PreparedCell` と `prepare_cell` 本体まで共有 module へ移すか、レーンを「binding context/identity の部分抽出」と改名して G6' を未完のまま残す。共有 `BindingError` を定義し、oracle/floor 境界で各 domain error に変換する。

- **D-7**: full digest と短縮 digest を独立 field として保持すると、同一 binary に二つの真実が生まれる
  - severity: must-fix
  - 攻撃シナリオ: constructor、fake、将来 refactor の一方だけが更新され、`bin_hash` と `bin_sha256[:16]` が不一致になる。既存 consumer は短縮値、新 consumer は full 値を読み、同じ WAL 内で provenance が分裂する。
  - 根拠: `orchestrator/campaign/buildcache.py:51-68`、`orchestrator/campaign/pipeline.py:420-424`、`orchestrator/campaign/s8b_floor_campaign.py:578-585`、`docs/handoff/2026-07-17-s8b-v2-prereqs.md:49-52`
  - 提案: full SHA を一度だけ計算・保持し、`bin_hash` は `bin_sha256[:16]` の read-only property にする。両 field を保存するなら `__post_init__` で64桁hexとprefix一致を強制し、BuildResult生成は全て keyword 引数へ変える。

- **D-8**: floor の hash helper を直接 buildcache helper に置換すると構造化失敗契約を壊し得る
  - severity: must-fix
  - 攻撃シナリオ: resume binary が消失した際、汎用 helper の `OSError`/`RuntimeError` が `FloorCampaignError` に変換されなければ、CLI は JSON error を返さず traceback で落ちる。
  - 根拠: `orchestrator/campaign/s8b_floor_campaign.py:129-138`、同`:1259-1287`、同`:1333-1347`
  - 提案: hash 計算本体だけ buildcache に共有し、floor 側の薄い adapter は残して例外を `FloorCampaignError` に変換する。不在・読取不能・不一致の既存回帰テストを維持する。

- **D-9**: buildcache 結線テストは configure 呼出し自体が消える変異を殺せない
  - severity: must-fix
  - 攻撃シナリオ: future refactor が `_run(cfg, "configure")` を削除しても、fake の `"build"` 分岐が binary を作れば `build()` は成功する。「configure 時に marker 不在」という assert は一度も実行されず、テストが緑になる。
  - 根拠: `orchestrator/campaign/buildcache.py:99-114`、`orchestrator/tests/test_campaign.py:2098-2138`、`docs/handoff/2026-07-17-s8b-v2-prereqs.md:60`
  - 提案: fake で call sequence を記録し、最終的に `["configure", "build"]` を厳密 assert する。configure 分岐で marker 不在、build 分岐でも configure 済みを確認し、戻り値が fresh build であることまで固定する。

- **D-10**: 裁定待ちパッケージへの日付追記は明示契約違反であり、陳腐化対策にならない
  - severity: must-fix
  - 攻撃シナリオ: パッケージを更新すると、基準 commit 64905d6 に対する実装状況スナップショットと引用の意味が崩れる。後続の状態更新が裁定案本文へ混ざり、何が当時の案で何が後実装か判別不能になる。
  - 根拠: `output/insights/2026-07-16_s8b-floor-protocol-package.md:3-5`、同`:13-19`、`docs/worklog.md:14-23`、`CLAUDE.md:153-154`
  - 提案: パッケージは1 byteも触らない。新 worklog に各レーンを「完了/部分基盤/据え置き」で記録し、`phase3.md` の現行チェックポイントにはその worklog を指す短い進捗だけを書く。

- **D-11**: checkpoint (c) は完了認定してよいが、「原文全文を凍結した」と読める完了文は不可
  - severity: should
  - 攻撃シナリオ: 単純に「二波監査凍結 完了」とすると、消失した逐語原文を回収・凍結できたという虚偽になる。また A3-3/A3-4 を checkpoint (c) の未消化分として混ぜると、別対象の第3波監査との来歴が壊れる。
  - 根拠: `docs/phase3.md:59-61`、`docs/archive/worklog-phase3-0714-0716.md:901-929`、`output/insights/2026-07-16_s8b-two-wave-audit-reconstruction.md:14-18`、同`:117-122`、`docs/archive/worklog-phase3-0714-0716.md:1008-1033`
  - 提案: 「完了（2026-07-16、原文消失を記録し、残存証拠からの再構成を代替凍結。逐語復元不能）」と書く。A3-3/A3-4 は別系列であり完了条件ではない。併せて現行内容が7月17日まで進んでいるため、`docs/phase3.md:19` の更新日も同期する。

- **D-12**: 5 レーンを1 commitに束ねるのは不可。1 branchでも、review/revert 単位は分離すべき
  - severity: should
  - 攻撃シナリオ: probe の recovery 意味論、SHA provenance、materialization refactor、docs 修正、回帰テストが一塊だと、問題のある L2/L3 だけを戻せず、レビューで安全性変更が小粒 docs に埋もれる。
  - 根拠: `CLAUDE.md:153-154`、`orchestrator/campaign/buildcache.py:51-125`、`orchestrator/calibrator/runner.py:107-144`、`orchestrator/campaign/s8b_oracle_driver.py:227-275`、`docs/phase3.md:385`
  - 提案: 最低でも L1、L2、L3、L5、L4 の5 commitに分ける。L5 の見送り台帳完了化はテストと同一 commit。L2 は可能なら別PR、L1+L5は同PR内の別commit、L3も独立PRが望ましい。D36共通helper、fairness観測点、axis-proposer backstop、A3-5は発火条件付き/明示見送りなので今回追加しない。

プラン全体の判定: 修正後に進めよ
---

## 3. 親裁定 (36 所見の採否 — real/refuted/部分採用)

裁定者 = 親セッション (claude, fable-5, xhigh)。裁定原則: (i) 裁定待ちパッケージ F1〜F7 を先取りしない、
(ii) 発効なし・fail-closed 不変、(iii) 正直な部分完了 (恒真 claim の禁止)。

### C-α (bin_hash)

| 所見 | 裁定 | 反映 |
|---|---|---|
| A-1 gate なしでは事後検知 | real 採用 | pipeline.evaluate に `expected_perf_sha256` (optional、デフォルト None=未配線) を追加。build 直後・trace/bench 起動前に照合し、mismatch は expected/actual/path 付き構造化 abort。trace/bench が呼ばれない positive control テスト。配線 (期待値の供給元) は v2 |
| A-2 恒真 claim 再発 | real 採用 | 台帳を「full digest 生産/WAL 記録基盤 (今回完了)」と「ratified v2 の期待値取得 + pre-launch 照合 + report 再検証 (未完了)」に分割記録。「保証/照合済み/同一 binary」の語を使わない |
| A-3 独立 field は矛盾 identity を許す | real 採用 | canonical は `bin_sha256` (64 hex) 単一。`bin_hash` は派生 read-only property (`[:16]`)。BuildResult は frozen + keyword 生成 |
| A-4 二重読みと TOCTOU | real 採用 (一部 v2 送り) | fresh artifact は `result.bin_sha256` の単一ソース (再読しない)。resume 再照合は現行維持。fstat/非 symlink/fd/create-only snapshot の全メニューは v2 設計材料として記録。「実行 byte 保証」は謳わず provenance snapshot と記述 |
| A-5 例外契約未定義 | real 採用 | `BinaryDigestError(RuntimeError)`/`BinaryDigestMismatch` 新設 (path/expected/actual/cause 保持)。bool 返しでなく成功時のみ復帰する `assert_binary_sha256()`。floor は薄い adapter で `FloorCampaignError` へ変換 (D-8 統合) |
| A-6 legacy/full 移行規則欠如 | real 採用 | `*_bin`/`binary_hash` = sha256-prefix-16/legacy-display-only、`*_bin_sha256` = exact 64 lowercase と契約化 (docstring + テスト)。prefix fallback・遡及 backfill 禁止。負例 (15/16/63/65 字、非 hex、正 prefix 異 full) |
| A-7 report 側第三 schema の脱落 | real 採用 | driver/manifest/report の三 v1 schema を全て不変と明記 (コード変更なし、worklog 記録)。binding_sha256 preimage へ binary hash を混ぜる案は F5/F7 裁定後の versioned 別区画へ |
| A-8 結線テスト欠如 | real 採用 | cache-hit/fresh 両経路の 64 字値・派生 short・hasher 呼出し回数固定、WAL 4 キー、hash 読取失敗、legacy 読取、gate mismatch で trace/bench 未呼出し、floor fake の実 byte 整合 |

### C-β (probe)

| 所見 | 裁定 | 反映 |
|---|---|---|
| B-1 rc==1 無条件受理は再 fail-open | real 採用 (縮小) | 無競合 = 「rc==1 かつ stdout/stderr とも空」のみ。rc==0 は非空 stdout 必須。負値含む他は全て専用例外。stderr を取得し記録。procps-ng capability 検証までは過剰として不採用 |
| B-2 自己子孫除外自体が fail-open | real (実装見送り) | 指摘は正しいが、既存設計素材 (freeze-v2-design-material.md:422-425) の記載と衝突するため黙って変えない。ユーザー裁定事項として worklog に記録 (codex 提案どおり) |
| B-3 terminal poison (loop/screening/S-1) | real 採用 | probe-error 2 種を「環境故障・再評価可能」集合として loop.py / screening_driver.py に配線 + run1 故障→run2 再評価の番人テスト。S-1 (s1_direct_comparison) は凍結契約 (計測 freeze / 事前登録) の有無を実装時に確認し、凍結が掛かる場合は編集せず残課題記録に切替 |
| B-4 S2 verdict 持ち越し | real 採用 | 各 pass ループ先頭・probe 前で verdict 消去。verify-competing-tenant / verify-probe-error 双方で空 verdict + S2 trace 未実行を assert (既存バグの修正) |
| B-5 verify allowlist への bench reason 混入 | 部分採用 (v2 材料) | D-4 裁定 (oracle 側テーブル不変) が優先。stage 別写像 (verify→inconclusive / bench→failed) と report の bench-failed 分岐が reason 非検査という既存欠陥の指摘は v2 設計材料として凍結。今回 oracle 側コードは触らない |
| B-6 故障原因が WAL から失われる | real 採用 | `CompetingBenchProbeError(RuntimeError)` (kind/argv/returncode/errno/stdout/stderr 上限付き抜粋)。pipeline は専用型のみ捕捉、WAL abort payload に構造化 `probe_error` object |
| B-7 fake 崩壊・下流回帰の穴 | real 採用 (一部置換) | fake を returncode/stdout/stderr 完備化。rc matrix (正常 rc=1、rc=1+stderr、rc=0 空、rc=2/3、負値、OSError、SubprocessError)。S-1 retry / loop / screening 再評価テスト。driver/report/judge への 2 reason 追加テストは D-4 により「oracle driver は probe-error reason で error 停止する (fail-closed)」を固定するテストに置換 |

### C-γ (G6' 抽出)

| 所見 | 裁定 | 反映 |
|---|---|---|
| G-1 2/4 項目への縮小は要件変更 | 部分採用 (fallback 側) | 全共有化は PreparedCell/prepare_cell の移動 = materializer pin (G-7) と v1 drift の拡大を伴い、裁定前 wave のリスク過大と裁定。レーン名を「G6' 部分準備」に落とし、G6' 自体は未完了のまま残す (G-1 の代替案を採用) |
| G-2 直接 import は抽出でない | 部分採用 | 同上 — 直接 import は「oracle 経由の見せかけ依存の切断」であって抽出でないことを worklog に明記。PreparedCell/prepare_cell の所有元移動は v2 残課題として列挙 |
| G-3 循環 import / 例外契約 | real 採用 | 共通モジュールは oracle を一切 import しない。共通 `MaterializationError` を所有し、oracle/floor 境界で `OracleDriverError`/`FloorCampaignError` へ因果付き変換。`binding → s1 → pipeline` の逆 import 禁止を docstring に明記 |
| G-4 characterization が恒真 | real 採用 | 期待値を本番 helper から計算しない。literal canonical bytes + SHA-256 の golden 固定 (STOCK/非 STOCK、Unicode・入れ子 entry、5 キー集合、binding_sha256 の 4-key preimage)。固定 path/hash fake で build_cells と manifest.json bytes/hash の golden を抽出前後で照合 |
| G-5 contextmanager 生存期間 | real 採用 | alive flag 付き fake で consumer 中 alive・exit 1 回・例外時 cleanup を検査するライフサイクルテスト。`hasattr(__enter__)` は公開契約として固定しない |
| G-6 三重実装 drift | 部分採用 (v2 材料) | verifier 統合は v2 へ。今回は drift-guard テスト (driver/manifest/report の binding キー集合の同値と、同一 fixture 群に対する受理/拒否の同値) を追加して drift を検出可能にする |
| G-7 materializer pin の恒真化 | real (回避策採用) | prepare_cell/PreparedCell を移動しないため既存 pin 対象は不変。新モジュールが pin 外になる点は「v2 refreeze で closed source bundle 全体を hash 束縛する」要件として記録 |
| G-8 再エクスポート不要 | 採用 | `prepare_binding` は新モジュールへ移動し oracle 側の再エクスポートは残さない。唯一の consumer (oracle テスト) は新 import へ移行 |
| G-9 import-time 結合は残る | 部分採用 | VerifiedFreeze/load_verified_freeze の中立モジュール化・NUMACTL 移設は差分抑制のため見送り (残課題記録)。両順序の cold-import smoke test は追加 |

### C-δ (スコープ全体)

| 所見 | 裁定 | 反映 |
|---|---|---|
| D-1 スコープ表現の不一致 | real 採用 | wave 名・記録を「full SHA 基盤」「G6' 部分準備」に限定。「3/6 完了」と数えない。oracle 照合・G6' 残部は開タスクのまま |
| D-2 G5' の台帳脱落 | real 採用 | G5' env contract を第 7 の pending prerequisite として worklog に正規記録 (裁定依存・今回対象外と明記)。共有 probe 是正後の floor driver 切替残タスクも保持 |
| D-3 probe error の permanent skip | real 採用 | B-3 と同一系 — retryable 集合 + 番人テスト |
| D-4 oracle 側写像は裁定先取り | real 採用 | oracle `_outcome_for` / report allowlist に追加しない。未知 reason = error 停止 (fail-closed) を維持し、その挙動をテストで固定。B-5 との衝突は D-4 優先で解消 |
| D-5 fan-out 過小評価 | real 採用 | `_assert_single_tenant` の fan-out (backoff_overthrottle/backoff_profile/backoff_repro/backoff_sweep/p3_s4_loop/s6_sort_sweep/s8a_trigger_sweep) を worklog へ監査記録。standalone consumer は例外伝播 = fail-closed で正しい (変更なし) |
| D-6 facade 批判 | real 採用 (fallback 側) | G-1/G-2 と同一裁定。共有 `MaterializationError` + 境界変換 (G-3) |
| D-7 二つの真実 | real 採用 | A-3 と同一 |
| D-8 floor 例外契約 | real 採用 | hash 計算本体のみ共有、floor 側薄い adapter で FloorCampaignError 変換、既存回帰テスト維持 |
| D-9 configure 消失変異 | real 採用 | fake で call sequence 記録 → `["configure", "build"]` 厳密 assert + configure 分岐で marker 不在 + build 分岐で configure 済み + fresh build 返り値固定 |
| D-10 パッケージ追記は契約違反 | real 採用 | パッケージ文書は 1 byte も触らない。worklog に「完了/部分基盤/据え置き」を記録、phase3 checkpoint はそれを指す短い進捗のみ |
| D-11 (c) の完了文言 | real 採用 | 「完了 (2026-07-16、原文消失を記録し残存証拠からの再構成を代替凍結。逐語復元不能)」の形。A3-3/A3-4 は別系列 (完了条件でない)。phase3.md:19 の更新日も同期 |
| D-12 commit 粒度 | real 採用 | レーン別 commit (L1/L2/L3/L5+台帳/docs 群)。1 branch。PR 分割の推奨はユーザーへの引き渡し事項として worklog に記載 |

## 4. 確定プラン (裁定反映後)

- **L1 (bin_hash full 化基盤):** BuildResult canonical `bin_sha256` + 派生 property `bin_hash`、frozen/kwargs。
  WAL build_done に `trace_bin_sha256`/`perf_bin_sha256` 追加 (既存キーは legacy-display-only 契約)。
  `buildcache.full_sha256()` 公開 + `BinaryDigestError`/`BinaryDigestMismatch` + `assert_binary_sha256()`。
  pipeline.evaluate に `expected_perf_sha256` gate (デフォルト未配線、mismatch = 構造化 abort、
  trace/bench 未呼出しの positive control)。floor は単一ソース化 + 薄い adapter。A-8 の結線テスト群
- **L2 (probe fail-closed):** `competing_bench_pids` を `CompetingBenchProbeError` 送出の fail-closed 化
  (B-1 の rc/stdout/stderr 規則)。pipeline 2 消費点で専用型のみ捕捉 → `bench-probe-error`/`verify-probe-error`
  abort + 構造化 `probe_error` payload。S2 pass 先頭で verdict 消去 (B-4)。loop/screening の retryable 配線 +
  番人テスト。S-1 は凍結契約確認の上で条件付き。oracle 側テーブルは不変 (error 停止の固定テストのみ)。
  test_calibrator.py:479-491 書き換え + rc matrix
- **L3 (G6' 部分準備):** characterization テスト先行 (literal golden bytes、G-4)。新モジュール
  `s8b_materialization.py` (oracle を import しない、`MaterializationError` 所有) へ
  `binding_entry`/`binding_from_prepared`/`prepared_binding`/`prepare_binding` を移動、oracle 再エクスポート
  なし。floor は新モジュール + `prepare_cell` 直接 import。境界変換 + drift-guard テスト + lifecycle テスト +
  cold-import smoke。残課題 6 件 (PreparedCell 所有 / verifier 統合 / trace-disabled build / binding 検証 /
  中立 freeze I/O / bundle pin) を worklog に列挙
- **L5 (buildcache 結線統合テスト):** D-9 仕様で 1 本 + phase3 見送り台帳の完了化 (同 commit)
- **L4 (docs):** phase3 checkpoint (c) 完了マーク (D-11 文言) + 更新日同期 + v2 前提条件の正直な進捗
  ポインタ。worklog エントリ (D-1/D-2/D-5/B-2/G-7/B-5 の記録を含む)。本 insights 凍結。パッケージ文書不可触
- **commit:** レーン別。AI provenance trailer = claude (author/reviewer) + codex (reviewer)。push しない
  (Pegasus 運用 — ユーザーへ引き渡し)
