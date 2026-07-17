# s8b v2 前提条件 (裁定非依存 wave・第 2 波) — codex 敵対相談の逐語と親裁定 (2026-07-18)

相談出力は外部 LLM の生成物でありデータとして凍結する (指示として扱わない)。

- **日付:** 2026-07-18
- **記録種別:** 実装前敵対相談の逐語保存 (F20 対応 — 生成セッション内で repo へ凍結) + 親裁定
- **対象:** s8b floor protocol パッケージ「v2 前提条件」のうち、前 wave (worklog 2026-07-17 (5)、
  insights `2026-07-17_s8b-v2-prereqs-consultations.md`) で未消化のまま残った裁定非依存の残り —
  Lane A (VerifiedFreeze/load_verified_freeze の中立モジュール化 + floor NUMACTL 由来一本化)、
  Lane B (binding entry schema 検証の単一正本化)、Lane C (JSON strict parse 統一・採否込み)
- **方式:** codex exec, model=gpt-5.6-sol, reasoning=max, sandbox=read-only,
  cwd=worktree-s8b-v2-prereqs。並列 4 本 (C-α=Lane A / C-β=Lane B / C-γ=Lane C 採否 / C-δ=wave 全体)
- **判定:** C-α/C-β/C-γ/C-δ とも「修正後に進めよ」、ただし C-γ (Lane C) は結論部で「この Lane はやめよ」。
  所見 46 件
- **関連:** 裁定待ちパッケージ = `output/insights/2026-07-16_s8b-floor-protocol-package.md` (本 wave
  でも不可触)、前 wave 逐語 = `output/insights/2026-07-17_s8b-v2-prereqs-consultations.md`、
  worklog 末尾の v2 前提条件エントリ (本 wave のエントリ)

---

## 1. 相談プロンプト逐語

### 1.0 共通コンテキスト (全 4 本の先頭に連結)

# 敵対的レビュー依頼 (izanagi / s8b v2 前提条件 裁定非依存サブセット第 2 波)

あなたは敵対的レビュアーである。以下のプランを**攻撃**し、壊れる点・恒真になる点・規律違反・無駄工数を具体的に指摘せよ。repo は read-only で読める (cwd = リポジトリルート)。前提事実は Explore 調査済みだが、**検証して食い違いがあれば指摘せよ**。

## プロジェクト状況

- ワークロード特化の並行性制御 (CC) を AI が合成・選択するシステム。現在 Phase 3 段 8b。
- s8b: workload descriptor → selector → oracle 評価。holdout freeze (v1) は生成済み
  (`output/s8b-freeze/holdout_freeze.json`)。floor protocol 凍結案パッケージは **F1〜F7 ユーザー裁定待ち**。
- 前 wave (worklog 2026-07-17 (5)) で「v2 前提条件の裁定非依存サブセット」第 1 波を実装済み:
  L1 = bin_hash full-sha256 生産基盤 (消費配線なし)、L2 = probe fail-closed、L3 = G6' 部分準備
  (`orchestrator/campaign/s8b_materialization.py` へ binding_entry / binding_from_prepared /
  prepared_binding / prepare_binding を抽出)、L5 = buildcache 結線テスト。
- 本 wave はその続き: **裁定非依存で残っている部分だけ**を消化する。

## 不変条件 (絶対に緩めない — 違反を見つけたら must-fix)

1. 正しさゲートを緩める変更は禁止。fail-closed の弱体化は禁止。
2. **裁定先取りの禁止**: F1〜F7 (floor protocol / freeze v2 schema / 承認束縛 / v2 検証意味論) の
   択を先に実装しない。oracle `_outcome_for` / report allowlist に追加しない (D-4)。
   manifest `_validate_execution_snapshot` の per-pair 形状追随はしない (F5 依存)。
3. 裁定待ちパッケージ文書 (`output/insights/2026-07-16_s8b-floor-protocol-package.md` /
   `2026-07-16_s8b-freeze-v2-design-material.md`) は 1 byte も変更しない (D-10)。
4. PreparedCell / prepare_cell の定義は `s1_direct_comparison.py` から動かさない
   (G-1 裁定: materializer pin + v1 drift 拡大のリスク過大。本 wave でも維持)。
5. `s8b_selector_freeze.py` の完全孤立 (campaign 内 import ゼロ) は構造遮断設計であり不変。
6. 挙動同値の原則: リファクタは受理/拒否の絶対挙動を変えない。既存 drift-guard 8 fixtures
   (`orchestrator/tests/test_s8b_materialization.py:328-405`) の絶対 pin は不変で通ること。

## 確定済みの前提事実 (Explore 調査済み、file:line 付き)

- materializer pin = oracle manifest の `generator_versions` が s1_direct_comparison.py (materializer) /
  s8b_oracle_report.py (report) / s8b_oracle_judge.py (judge) の**ファイル全 bytes** の sha256 を束縛
  (`s8b_oracle_manifest.py:309-332,544,651`)。**本番 manifest は未生成** (`output/` に generator_versions
  を含む artifact ゼロ、`build_manifest()` の本番呼出しゼロ) — pin 値はまだどこにも記録されていない。
- v1 holdout freeze の `verify_document` は worktree bytes 照合で、design_source/generator の drift に
  より**現在すでに不合格** (実測記録 = floor-protocol-package.md:447-450。v2 で git blob 照合へ移行予定)。
- floor→oracle_driver の残 import は `NUMACTL` / `VerifiedFreeze` / `load_verified_freeze` の 3 シンボル
  のみ (`s8b_floor_campaign.py:81-85`)。使用箇所: NUMACTL=:1184、VerifiedFreeze=:1145、
  load_verified_freeze=:1367 (CLI)。
- `VerifiedFreeze` dataclass = `s8b_oracle_driver.py:94-102`、`load_verified_freeze` = :105-132
  (bytes 一度読み + sha256 pin + NaN/Infinity 拒否 strict parse。duplicate key 拒否なし)。
- binding entry schema 検証の三重実装:
  - manifest: `_validate_binding_identity` (`s8b_oracle_manifest.py:349-399`、7 キー集合・SHA-256 形式・
    4-key preimage 再計算・schedule cell 完全一致、違反 = ManifestError raise)
  - report: `_binding_schema_issues` (`s8b_oracle_report.py:247-277`、同型ロジックの並行実装、
    issue list 返却)。report は `s8b_oracle_manifest` を import 済み (:18) だが再利用していない
  - driver: `_expected_binding` (`s8b_oracle_driver.py:248-285`、射影 5 キー集合検査のみ) +
    run_block :579-589 の canonical bytes 実値比較
  - `_BINDING_KEYS` 定数が driver (5 キー、:41-44) / manifest (7 キー、:36-39) / report (7 キー、
    :241-244) に三重定義。キー集合同値は `test_s8b_materialization.py:294-312` が機械固定済み
  - manifest/report の受理拒否同値は 8 fixtures で固定済み (`test_s8b_materialization.py:328-405`)。
    **driver 経路はこの行列の対象外** (盲点)
- `_canonical_bytes`/`_canonical_sha256` が `s8b_materialization.py:35-46` と
  `s8b_oracle_driver.py:65-76` に重複定義。
- JSON parse strictness の 4 実装差 (所見 D8'): `s8b_holdout_freeze._load_json` (:137-144、素の
  json.loads) / `s8b_oracle_driver.load_verified_freeze` (NaN 拒否のみ) / `s8b_oracle_manifest`
  (素の loads、:79-86) / `s8b_selector_freeze._load_json_object` (:685-704、dup-key + NaN 拒否)。
  v2 設計材料では「単一 `load_ratified_freeze()` を全 consumer の唯一入口にする」(F6/F7 裁定依存)。
- マシン固有値: `p2_2.py:39-41` に `ENV_TAG="linux-baremetal"` / `CLK=1800`。floor は :75 で import
  済み。`NUMACTL=["numactl","--interleave=all"]` は `s8b_oracle_driver.py:40`、`p2_2.py:41` に
  `NUMA` (同値)、他多数の campaign ファイルに同値の独立定義。G5' env contract 本体は裁定依存 (D-2) で対象外。
- import グラフ: `s8b_oracle_manifest.py` / `s8b_holdout_freeze.py` は stdlib のみの leaf。
  `s8b_materialization.py` は pipeline + s1_direct_comparison に依存 (oracle/floor/manifest/report を
  import しない契約、テスト固定済み)。
- テスト基線: 996 passed / 23 skipped / 0 failed (tools/run_tests.py、5.25s)。

## 出力形式

番号付き所見のリスト。各所見に: 深刻度 (must-fix / should / nit / question)、主張 (1-2 文)、
根拠 (file:line または論理)、提案 (あれば)。最後に総合判定を 1 行で:
「このまま進めよ」「修正後に進めよ (must-fix 列挙)」「この Lane はやめよ (理由)」のいずれか。

### 1.1 C-α プロンプト (Lane A)

## あなたの担当: Lane A — VerifiedFreeze/load_verified_freeze の中立モジュール化 + floor の NUMACTL 由来一本化 (G-9 残課題の消化)

### プラン (攻撃対象)

1. 新 leaf モジュール `orchestrator/campaign/s8b_freeze_io.py` (stdlib のみ、campaign 内 import ゼロ) を
   新設し、`VerifiedFreeze` dataclass・`load_verified_freeze`・`_reject_json_constant` を
   `s8b_oracle_driver.py` から**移動** (コピーでなく)。
2. 再エクスポートは残さない (前 wave の G-8 裁定と同じ方針)。全 consumer を新 import へ移行:
   - `s8b_oracle_driver.py` (自己使用: gate_check / run_block)
   - `s8b_floor_campaign.py:83-84` → `from campaign.s8b_freeze_io import VerifiedFreeze, load_verified_freeze`
   - `orchestrator/tests/test_s8b_oracle_driver.py:722-749` / `test_s8b_floor_campaign.py:39,116-117,419`
3. 例外契約: `load_verified_freeze` は現在 `OracleDriverError` を投げる。移動後は中立の例外
   (新設 `FreezeIOError` など) を投げ、oracle driver / floor campaign の境界で各自の例外へ変換する
   (s8b_materialization の MaterializationError → OracleDriverError/FloorCampaignError 変換と同型)。
   ただし: WAL/ログの reason 文字列・既存テストの例外型 assert との互換を確認し、必要なら境界 wrapper で
   メッセージを現行と一致させる。
4. NUMACTL: floor は `s8b_floor_campaign.py:81-82` の `from campaign.s8b_oracle_driver import NUMACTL` を
   やめ、`p2_2` から import する (ENV_TAG/CLK と同じ由来元へ揃える。p2_2.py:41 に同値の `NUMA` が既存)。
   oracle driver 側の `NUMACTL` 定義 (:40) は現状維持 (oracle 自己使用のみ)。他 campaign ファイルの
   重複定義には触れない (差分抑制)。
5. これにより floor→oracle_driver の import edge が完全消滅。cold-import orders テスト
   (`test_s8b_materialization.py:539-551`) は 4 順序のまま通ることを確認し、
   「floor が oracle を import しない」ことを機械固定する negative import テストを追加
   (materialization の逆 import 禁止テストと同型、対象 = s8b_floor_campaign.py のソース走査)。

### 特に攻撃してほしい点

- **A-1**: 新モジュール名 `s8b_freeze_io.py` と「freeze I/O」という責務切りは適切か。v2 の
  `load_ratified_freeze` (F6/F7 裁定後に実装) の自然な着地点になるか、それとも v2 で捨てられる
  死荷重になるか。`s8b_holdout_freeze.py` (leaf、ただし v1 freeze の generator source record として
  hash 束縛されており bytes 変更は drift を拡大する) へ置く代替案との比較。
- **A-2**: 例外型の変更 (OracleDriverError → 新 FreezeIOError) は floor CLI (:1367) や既存テストの
  except 節・assert を壊さないか。全 catch 箇所を列挙して裏取りせよ。互換のため
  「OracleDriverError を維持したまま定義だけ移す」案 (新モジュールが OracleDriverError を所有するのは
  倒錯) との比較。
- **A-3**: floor の NUMACTL を p2_2.NUMA へ切り替えると、将来 G5' env contract (裁定依存) の設計と
  衝突しないか。p2_2 という「旧 campaign ファイル」をマシン固有値の事実上の由来元として追認することの
  是非。oracle driver と floor で NUMACTL の由来が分かれる (driver=自前 :40、floor=p2_2) のは
  「単一正本化」の名に反しないか — 反するなら honest な記録の書き方。
- **A-4**: 移動により s8b_oracle_driver.py の import time 依存が変わる。gate_check / run_block の
  TOCTOU 遮断 (VerifiedFreeze 単一 object 再利用、A3-6) の意味論が 1 bit も変わらないことの確認方法。
- **A-5**: この Lane が裁定 (F1〜F7) のどれかを先取りしていないか。特に F6/F7 (承認束縛・v2 検証意味論)
  との関係で「中立モジュール新設」自体が択を狭めるか。
- **A-6**: テスト戦略の穴。移行漏れ (grep 残り)、cold-import、例外境界、既存 996 passed の維持。

### 1.2 C-β プロンプト (Lane B)

## あなたの担当: Lane B — binding entry schema 検証の単一正本化 + canonical hash 重複解消 (G-6 の裁定非依存部分)

### プラン (攻撃対象)

1. `s8b_oracle_manifest.py` (stdlib のみの leaf、driver/report が既に import 済み) を binding entry
   schema 検証の**単一正本**にする:
   - 公開関数 `binding_entry_issues(entry) -> list[str]` を新設 (検査内容 = 7 キー集合一致・非空文字列・
     entry_sha256/binding_sha256 の SHA-256 形式・4-key preimage からの binding_sha256 再計算一致)。
     現行 `_validate_binding_identity` (:349-399) の entry 単位部分を切り出し、同関数は
     `binding_entry_issues` を呼んで違反時 ManifestError raise + list/重複/schedule 完全一致の
     コレクション級検査を維持。
   - 公開定数 `BINDING_KEYS` (7 キー) と `PRODUCER_BINDING_KEYS` (5 キー = 7 − cell 2 キー) を公開し、
     driver `_BINDING_KEYS` (s8b_oracle_driver.py:41-44) と report `_BINDING_KEYS` (:241-244) を
     import 置換 (ローカル再定義を削除)。
   - report `_binding_schema_issues` (s8b_oracle_report.py:247-277) は
     `s8b_oracle_manifest.binding_entry_issues` への委譲に置換 (report は :18 で import 済み、
     新 edge 不要)。issue 文字列の文言が変わる場合、report 側の既存テストの assert を確認。
2. driver の `_canonical_bytes`/`_canonical_sha256` (s8b_oracle_driver.py:65-76) を削除し
   `s8b_materialization` から import (重複解消。materialization は driver が既に import 済み)。
3. drift-guard の強化: 8 fixtures 行列 (`test_s8b_materialization.py:328-405`) に driver 経路
   (`_expected_binding` の受理/拒否) を第 3 列として追加し、三者同値を機械固定する。
   driver は射影 5 キーの schema 検査のみなので、fixture の cell 2 キーを除去した射影版で判定。
   絶対挙動 pin (assert manifest_verdict is expected) は不変。
4. **触らないもの**: report の緩い `_validate_manifest` (:62-95) と `_binding_entry` 多形探索
   (:220-238) は意図された疎結合として維持 / manifest `_validate_execution_snapshot` (:402-434) は
   F5 per-pair 裁定依存のため不可触 / `_validate_generators` も不変。

### 特に攻撃してほしい点

- **B-1**: 「manifest を正本にする」判断。代替 = s8b_materialization に置く (producer と verifier が
  同居する概念的一貫性はあるが、manifest が materialization を import すると leaf でなくなり
  pipeline/s1_direct_comparison が manifest の import chain に入る) / 新 leaf モジュール。
  import グラフ・将来の v2 strict verifier との整合で最善はどれか。
- **B-2**: s8b_oracle_report.py は generator pin (report) の対象ファイルである。本番 manifest 未生成で
  pin 実害なしという判断は正しいか。見落としている pin 消費者・凍結物はないか (grep で裏取りせよ)。
- **B-3**: 受理/拒否の絶対挙動が 1 bit も変わらないことの保証方法。特に report の issue 文字列文言
  変更が「issue の有無」判定以外に漏れる消費者 (レポート出力 JSON に issue 文字列が載る等) が
  いないか。issue 文字列が artifact に載るなら文言互換も必要では。
- **B-4**: driver `_expected_binding` を fixture 行列に足す際の罠。driver は schema 検査のみで
  hash 再計算をしない (実値比較は run_block :579-589 の canonical bytes)。fixture の
  「hash 不一致」ケースは driver では受理される (設計どおり) — 三者「同値」を謳うと嘘になる。
  正直な行列の書き方 (driver 列は期待値が異なることの明示) を設計せよ。
- **B-5**: `_canonical_bytes` の重複解消で、driver 側と materialization 側の実装に微妙な差
  (sort_keys / separators / ensure_ascii 等) がないか。bytes 単位で同一であることを確認せよ。
  差があれば run_block の実値比較の挙動が変わる — must-fix。
- **B-6**: この統合が F5 (freeze v2 schema) / manifest per-pair 追随の裁定を先取りしないか。
  strict v2 verifier が binding 検証をどう吸収するか未記載 (設計材料に記述なし) の状態で
  統合することの将来リスク。
- **B-7**: テスト戦略の穴と、既存テスト (test_s8b_oracle_manifest / test_s8b_oracle_report /
  test_s8b_oracle_driver) の assert が文言変更で壊れる箇所の列挙。

### 1.3 C-γ プロンプト (Lane C 採否)

## あなたの担当: Lane C — JSON strict parse の統一 (所見 D8' の裁定非依存部分)。**この Lane は採否自体を攻撃対象とする — 「やめよ」の判定を遠慮なく出せ**

### プラン (攻撃対象)

1. 共有 helper `load_strict_json_bytes(data: bytes) -> dict` (duplicate key 拒否 + NaN/Infinity 拒否 +
   top-level object 強制) を新設し (置き場所は Lane A の `s8b_freeze_io.py` を想定、Lane A が
   不成立なら独立 leaf)、以下 3 実装をこれに置換:
   - `s8b_holdout_freeze._load_json` (:137-144、現状素の json.loads)
   - `s8b_oracle_driver.load_verified_freeze` (:105-132、現状 NaN 拒否のみ → dup-key 拒否を追加)
   - `s8b_oracle_manifest` の manifest 読込 (:79-86、現状素の loads)
2. `s8b_selector_freeze._load_json_object` (:685-704) は触らない (完全孤立は構造遮断設計)。
   strictness の仕様は selector_freeze 実装に揃える (dup-key + NaN 拒否が既に最強)。
3. 既存 v1 artifact (`output/s8b-freeze/holdout_freeze.json`、`output/s1-freeze/*.json`) が strict
   parse を通ることを実物で確認する characterization テストを追加 (artifact が repo 内に実在する場合)。
4. 拒否時の例外は各モジュールの既存例外型 (FreezeError / OracleDriverError / ManifestError) を維持
   (helper は ValueError を投げ、呼び出し側で変換)。

### 特に攻撃してほしい点

- **C-1 (採否)**: v2 設計材料は「単一 `load_ratified_freeze()` を全 consumer の唯一入口にし、
  parser 差を解消する」(F6/F7 裁定依存) を予定している。本 Lane はその一部を先行実装することになる —
  これは (a) 裁定先取り (F6/F7 の択を狭める) か、(b) 択に依存しない fail-closed 強化として独立に
  正当か、(c) v2 で丸ごと置換されるので無駄工数か。三択で判定し理由を述べよ。
- **C-2**: strict 化は「今まで受理していた入力を拒否する」方向の挙動変更である。fail-closed 強化とは
  いえ、既存の正当な artifact・テスト fixture が dup-key / NaN を含んでいて壊れないか。テスト
  fixture 全数を grep で裏取りせよ (json.dumps 生成の fixture は dup-key を含み得ないが、手書き
  JSON 文字列リテラルは要確認)。
- **C-3**: v1 holdout freeze の verify は既に drift 不合格 (worktree bytes 照合)。gate も
  freeze-v2-verifier-not-implemented で拒否中。この状態で loader だけ強化することに意味があるか —
  「動かない経路の防御強化」は無駄工数ではないかを判定せよ。逆に、strict 化しないと v2 実装時に
  「v1 時代に受理された緩い artifact」が resume 等で混入する経路があるかも調べよ。
- **C-4**: `s8b_holdout_freeze.py` は v1 freeze の generator source record として bytes 束縛されており
  既に drift 不合格。ここへの追加編集は drift を拡大する (v2 で git blob 照合に変わるまで不合格の
  まま)。この編集は「既に不合格だから無害」か「不合格の理由を増やして v2 移行時の照合を複雑化する」か。
- **C-5**: dup-key 拒否の実装 (object_pairs_hook) が selector_freeze の実装と意味的に完全一致するか。
  微妙な差 (ネスト内 dup、非 str key 等) があれば列挙せよ。

### 1.4 C-δ プロンプト (wave 全体)

## あなたの担当: C-δ — wave 全体のスコープ・戦略・docs プランの敵対検証

### wave 全体像 (攻撃対象)

背景: F1〜F7 (floor protocol / freeze v2) はユーザー裁定待ちで、主経路 (floor 実測 → oracle 実走) は
進められない。前 wave (worklog 2026-07-17 (5)) で裁定非依存サブセット第 1 波を実装済み。本 wave は
その残りから裁定非依存の 3 Lane + docs を選んだ:

- **Lane A**: VerifiedFreeze/load_verified_freeze を新 leaf `s8b_freeze_io.py` へ移動 (G-9 残課題。
  前回見送り理由は「差分抑制」のみ)。floor の NUMACTL 由来を p2_2 へ一本化。
  floor→oracle_driver import edge の完全消滅。
- **Lane B**: binding entry schema 検証の単一正本化 (manifest を正本に、report/driver は委譲/import
  置換)。`_canonical_bytes`/`_canonical_sha256` の重複解消。drift fixture 行列へ driver 経路を追加。
- **Lane C** (採否込み): JSON strict parse (dup-key + NaN 拒否) の 3 loader 統一。selector_freeze 不変。
- **Lane D (docs)**: docs/failures.md の F15 タグ `[テスト代表性]` が冒頭タグ台帳 (8 種、:17-18) に
  未登録という自己矛盾の解消 (台帳へ追記) / worklog 新エントリ / phase3 checkpoint の進捗ポインタを
  worklog (5) → 新エントリへ更新 / handoff 削除。
- commit はレーン別 (A/B/C/D 各 1 本以上)。push しない (ユーザー引き渡し)。
- **明示的に見送るもの (正直な残として記録)**: PreparedCell/prepare_cell 所有移動 (G-1 裁定維持) /
  trace-disabled build 共有 (oracle 側は pipeline.evaluate が所有、floor 側だけの抽出は consumer 1 の
  「共有」で価値薄 + 計測 driver への接触リスク) / G5' env contract (D-2 裁定依存) / strict v2
  verifier・manifest per-pair・bench_max_rounds=1 凍結・oracle 消費配線・bundle pin (すべて裁定依存) /
  floor の共有 probe 切替 (B-2 自己子孫除外の裁定待ちと絡む)。

### 攻撃してほしい問い

- **D-1**: この wave はそもそもやる価値があるか。裁定待ち中の「正しい待ち方」として、(a) この 3 Lane、
  (b) 何もせず裁定を待つ (リファクタは v2 実装と同時にやる方が手戻りがない)、(c) 別の作業
  (見送り台帳の計測系、層3 v3 準備等) — のどれが最善か。特に「v2 実装時にどうせ触るファイル群を
  今リファクタする」ことの手戻りリスク vs 「v2 wave の diff を小さくして裁定後の実装を速くする」
  利益のトレードオフを検討せよ。
- **D-2**: Lane 分割と依存関係は正しいか。Lane C は Lane A の新モジュールに helper を置く想定 —
  この結合は commit 順序・部分不成立時のフォールバックを複雑にしないか。
- **D-3**: 見送りリストに「本当は今できるのに見送っているもの」「逆に、見送るべきなのに Lane に
  入っているもの」がないか。特に trace-disabled build 共有の見送り理由の妥当性。
- **D-4**: docs プランの穴。worklog / phase3 checkpoint の更新で「完了と数えない」規律 (D-1 前 wave
  裁定) に反する表現が入りやすい点、phase3 の「裁定非依存の 3 件は部分基盤のみ実装済み」文言との
  整合。failures F15 タグの直し方 (台帳に追記 vs F15 を既存タグに再分類) はどちらが正しいか —
  docs/failures.md を実際に読んで判定せよ。
- **D-5**: 本 wave が絶対規律 (観測者効果分離 / 正しさゲート / 信頼境界)・裁定先取り禁止・D-10
  (パッケージ文書不可触) のどれかに触れる隠れ経路がないか。
- **D-6**: テスト・検算計画の穴。基線 996 passed / 23 skipped / 0 failed の維持だけで十分か、
  Lane 別に追加すべき負テスト・結線テストはないか。

---

## 2. 相談出力逐語

### 2.1 C-α 出力

1. **[must-fix] 「再エクスポートなし」と自己使用 import が両立する形を明記していない。** driver が `from campaign.s8b_freeze_io import VerifiedFreeze, load_verified_freeze` とすると、Python 上は旧 `driver.VerifiedFreeze` / `driver.load_verified_freeze` がそのまま残る。  
   根拠: 現在のテストは `driver.load_verified_freeze` を使用している (`test_s8b_oracle_driver.py:728-743`)。  
   提案: driver/floor とも `from campaign import s8b_freeze_io as _freeze_io` のような private module alias で参照し、`hasattr(driver, "load_verified_freeze") is False` を固定する。

2. **[must-fix] 例外変換点は三つあり、一つでも漏れると終了契約が変わる。** 全 production call/catch は、`gate_check` の広域 catch (`s8b_oracle_driver.py:157-160`)、`run_block` の `OracleDriverError` catch (`:454-461`)、floor `main` の `FloorCampaignError` catch (`s8b_floor_campaign.py:1363-1377`) である。oracle `main` の広域 catch (`s8b_oracle_driver.py:797-817`) は変換漏れを `refused/rc2` でなく `error/rc1` にしてしまう。  
   根拠: floor CLI は現在 loader の `OracleDriverError` を捕捉できず、pilot 経路で例外が外へ漏れる。直接 loader を捕捉するテストは `test_s8b_oracle_driver.py:735-743` だけで、floor 境界テストはない。  
   提案: 各 consumer に private adapter を置き、`FreezeIOError` だけを `raise ConsumerError(str(exc)) from exc` で変換する。driver の refusal class名・message・rc、floor pilot の rc1 JSON と cause を個別に固定する。floor 側は既存不具合修正であり、純粋な無挙動変更とは記録しない。

3. **[must-fix] 現行 TOCTOU テストは「単一 read」を実証していない。** `test_load_verified_freeze_single_read...` は read 回数を数えず (`test_s8b_oracle_driver.py:722-744`)、V6 は helper が `gate_check` を常時 allowed に mock するため (`:235-243,790-791`)、gate への `verified` 渡し忘れや二重 load を検出できない。  
   提案: `Path.read_bytes` が厳密に1回である positive control と、`run_block` が同一 object を `gate_check(verified=...)` に渡し、raw loader を一度しか呼ばない identity test を追加する。既存の manifest 後差替えテストも残す。

4. **[must-fix] 4順序 cold-import test は import edge 消滅の証明として恒真である。** 現在 floor が oracle を直接 import している状態でも `test_cold_import_orders` (`test_s8b_materialization.py:539-551`) は通る。提案されたソース走査も transitive/dynamic import を見逃す。  
   根拠: clean process で現行 floor を単独 import すると `campaign.s8b_oracle_driver in sys.modules` は `True` だった。これは `docs/failures.md:88-94` の F9 型そのもの。  
   提案: fresh subprocess で floor だけを import し、`*.s8b_oracle_driver` が `sys.modules` に存在しないことを assert する。現行コードで赤になる positive control を確認し、AST の direct-import 検査は補助に留める。

5. **[must-fix] NUMACTL の本番 wiring は既存テストで一度も実行されない。** floor テスト helper は常に `measure_fn` を注入する (`test_s8b_floor_campaign.py:196-206`) ため、`measure_fn is None` の closure (`s8b_floor_campaign.py:1177-1185`) に `NUMACTL` の NameErrorや誤配線があっても全テストと cold import が通る。  
   提案: `NUMA as NUMACTL` として既存 module 属性・値を保ち、`measure_fn=None` かつ `measure_point` を fake にした wiring test で `numactl is p2_2.NUMA` を検査する。

6. **[should] 「NUMACTL の単一正本化」は過大主張になる。** floor 内の `ENV_TAG/CLK/NUMACTL` は p2_2 に揃うが、oracle は独立 `NUMACTL` のままなので、将来 `p2_2.NUMA` だけが変われば同じ env_tag の二経路が漂流する (`p2_2.py:39-41`, `s8b_oracle_driver.py:40`)。  
   提案: 「floor-local の由来統一、oracle との重複は G5' まで意図的残置」と記録する。G5' 完了や全 campaign の単一正本化とは数えない。

7. **[should] `VerifiedFreeze` を将来の ratified 型と見なすと F6/F7 を先取りし、しかも保証が弱い。** 現型は任意の `dict/hash` で直接構築でき、現 loader が保証するのは byte hash と NaN拒否までである (`s8b_oracle_driver.py:94-132`)。F6 は candidate を渡せない `load_ratified_freeze` 型分離 (`floor-protocol-package.md:405-411`)、F7 は duplicate/未知key/schema/approval/active 検証まで要求する (`:458-468`)。  
   提案: `s8b_freeze_io.py` は「現行 raw bytes loader の中立置場」と明記し、将来は別 `RatifiedFreeze` と `load_ratified_freeze` を追加して production consumer から raw loader を外す。現 wave では duplicate-key 拒否等を足さない。

8. **[should] 新 leaf は妥当だが責務名が広すぎる。** `s8b_freeze_io` は selector freeze 等まで扱うように読める一方、今回扱うのは実行用 holdout freeze bytes だけである。  
   根拠: `s8b_holdout_freeze.py` は生成・未知性検証を所有し (`:2-7`)、その bytes は v1 generator record に束縛済みで現在も drift 中なので、同ファイルへ置く代案はさらに悪い。  
   提案: module docstring で対象を限定する。新 leaf を採用し、`s8b_holdout_freeze.py` は変更しない。

9. **[should] loader の受理拒否 drift guard が不足する。** 現テストは成功・hash不一致・NaNだけで、read不能、invalid UTF-8、malformed JSON、top-level非objectを固定していない (`test_s8b_oracle_driver.py:722-744`)。  
   提案: 新 leaf に直接テスト行列を置く。移行漏れ grep は `s1_direct_comparison.py:115` の同名だが別物の loader を誤検出しないよう、import origin／qualified reference で検査する。

10. **[must-fix] 完了検査が repo 規律を満たしていない。** 現プランには cold-import と既存 suite しか明記されず、必須の `check_codex_agents.py`、`check_docs.py`、commit後の provenance 監査がない。  
    根拠: `AGENTS.md:26-28`。  
    提案: targeted tests、`tools/run_tests.py`、両 checker、凍結文書の byte不変確認、commit後の `check_ai_provenance.py` を統合チェックリストへ入れる。

11. **[question] テスト基線の記録が一致していない。** `docs/worklog.md:191` は `996 passed / 22 skipped / 1 failed`、現 handoff `:19` と依頼は `996 / 23 / 0`。現 tree の collect は合計1019件だったが、read-only sandboxでは一時領域を作れず full run は再実測できなかった。  
    提案: 実装開始時に writable な通常環境で同一コマンドを再実行し、どちらを基線とするか固定する。Lane A 関連のその他の提示事実には食い違いを認めなかった。

修正後に進めよ (must-fix: 実再エクスポート排除、全例外境界とCLI契約の固定、非恒真なTOCTOU/import-edge/NUMACTLテスト、必須完了検査の追加)

### 2.2 C-β 出力

1. **must-fix [B-3/B-6]**

   主張: `binding_entry_issues` の単一化は現状のままでは挙動同値にならない。非有限値を含む `genome_canonical` に対し、manifest は受理、report/driver は拒否している。

   根拠: manifest の canonicalizer は `allow_nan=False` がない (`s8b_oracle_manifest.py:46-56`) 一方、report・driver・materialization は明示的に拒否する (`s8b_oracle_report.py:56-59`, `s8b_oracle_driver.py:65-76`, `s8b_materialization.py:35-46`)。実行確認でも `{"x": NaN}` と整合する hash を持つ entry は manifest が受理し、report は `ValueError`、driver は `OracleDriverError` になった。manifest loader/write も NaN を許すため到達可能である (`s8b_oracle_manifest.py:79-86,558-560`)。

   提案: NaN/Infinity fixture を追加し、manifest の permissive canonicalizer を report に流用しない。manifest を strict 化する解決は受理域変更かつ F7 の strict parse 裁定先取りになるため、共有化するなら「共通構造検査 + report 固有 strict precheck」に縮小するか、F7 後へ送る。

2. **must-fix [B-3]**

   主張: 新関数の `binding_entry_issues(entry)` には期待 cell が渡らないため、report の cell identity 検査が消える。

   根拠: report は composite/nested mapping のキーから entry を取り出せる (`s8b_oracle_report.py:220-238`) が、entry 内の `holdout_id/configuration_id` が検索対象と一致するかは `_binding_schema_issues` だけが検査する (`:247-255`)。実確認でもキー `H1:stock` の中身が `H2/other` の entry を検索は返し、現行検査は拒否した。単なる schema 委譲では非空の異なる ID を受理し得る。

   提案: report wrapper に期待 cell 照合を残すか、共有 API に明示的な `expected_holdout/configuration` を渡す。list・nested・`H:C`・`H/C` の各探索形に mismatch positive control を置く。

3. **must-fix [B-3]**

   主張: issue 文言は内部診断ではなく observations artifact の一部であり、「文言が変わるならテスト更新」で済ませられない。また複合故障時の検査順も現行挙動である。

   根拠: `binding_reasons` は row の `reason` に連結され (`s8b_oracle_report.py:350-370,437-455`)、CLI が create-only JSON に書く (`:624-647`)。同じ欠落キーでも manifest は「`binding_identity entry schema が不一致`」、report は「`manifest.binding_identity の必須 identity field が完全でない`」と異なる。さらに「重複 cell + 不正 hash」では現行 manifest は重複を先に報告する (`s8b_oracle_manifest.py:369-390`)。

   提案: 共有層は文字列でなく安定した issue code を返し、manifest/report が現行文言と順序へ個別に render する。単独故障だけでなく複合故障の precedence も golden 化する。

4. **must-fix [B-4]**

   主張: driver を第3の「同値 verdict」にしてはいけない。`_expected_binding` は5キー集合と JSON 化可能性しか検査せず、8 fixtures のうち4件で manifest/report と意図的に異なる。

   根拠: `s8b_oracle_driver.py:248-285`; 現行実測は以下。

   | fixture | schema verdict | `_expected_binding` returns |
   |---|---:|---:|
   | valid | true | true |
   | missing binding hash | false | false |
   | missing variant | false | false |
   | extra key | false | false |
   | variant non-string | false | true |
   | entry hash non-hex | false | true |
   | binding hash wrong | false | true |
   | genome empty | false | true |

   実値検査は別途 `run_block` の canonical bytes 比較で行われる (`s8b_oracle_driver.py:579-589`)。また cell 2キーを手で除いた composite mapping は、`verify_manifest` 後の本番経路では到達しない形である (`s8b_oracle_manifest.py:648-650`)。

   提案: manifest/report の schema 行列と driver の projection 行列を別テストにする。driver 側は別の期待列を持ち、full 7-key list を渡して内部で射影させる。実値不一致は既存 end-to-end binding-refused テストを拡張して固定する。

5. **must-fix [B-5]**

   主張: driver/materialization の canonical bytes は byte 単位で同一だが、直接 import 置換すると例外契約が変わる。

   根拠: `sort_keys=True`, `separators=(",", ":")`, `ensure_ascii=False`, `allow_nan=False` は完全一致する。差は driver が `OracleDriverError`、materialization が `MaterializationError` を送出する点 (`s8b_oracle_driver.py:65-76`, `s8b_materialization.py:35-46`)。`run_block` は例外型名を WAL reason に埋め込むため (`s8b_oracle_driver.py:642-658`)、直接 import は artifact を `prepare OracleDriverError` から `prepare MaterializationError` へ変える。

   提案: 中立な canonical helper を置いて consumer 境界で例外変換するか、driver に薄い変換 wrapper を残す。NaN・非 JSON 値について例外型、cause、WAL reason を固定する。

6. **must-fix [B-2]**

   主張: 「report は指定ファイルに機械的に pin される」という前提は正確でない。既存本番 artifact がない点は確認できたが、role と正規 path の束縛も、report 実行時の自己検査もない。

   根拠: repo-wide grep では `build_manifest()` 呼出しはテストだけで、`output/` に `generator_versions`/oracle manifest/observations はゼロだった。一方 `_validate_generators` は root 内実在 path と自己申告 hash しか検査せず (`s8b_oracle_manifest.py:309-332`)、実確認では `materializer/report/judge` の全ラベルに `CLAUDE.md` を指定して受理した。report の `_validate_manifest` は `verify_manifest` を呼ばず (`s8b_oracle_report.py:62-95`)、共有意味論を manifest や新 leaf へ移すと、その bytes は `generator_versions.report` に含まれない。

   提案: pin を provenance 記録に過ぎないのか実行ゲートなのか明記する。後者なら role→正規 path を固定し、共有 validator/materialization を含む source closure を束縛し、report 実行時にも検査する。少なくともこの不完全な pin を変更安全性の根拠に使わない。

7. **should [B-1/B-6]**

   主張: 長期的な配置は stdlib-only の versioned leaf が最善で、materialization は最悪、manifest は最小差分だが暫定案である。

   根拠: materialization は `pipeline` と `s1_direct_comparison` を引く (`s8b_materialization.py:27-28`)。manifest は leaf なので import graph は壊さないが、oracle manifest v1 の7-key identity と freeze の `variant_binding.entries` は別 schema である (`s8b_holdout_freeze.py:412-437`, `s8b_selector_freeze.py:348-365`)。Mapping を受ける validator は duplicate JSON key も検出できず、F7 loader の代替にはならない。

   提案: `s8b_oracle_binding_identity.py` のような stdlib-only leaf に、`ORACLE_BINDING_IDENTITY_V1_*` と versioned issue code を置く。ただし所見1・6の strictness/pin を先に解決し、`s8b_selector_freeze.py` からは import しない。`_validate_execution_snapshot` を触らない限り、直接の F5 先取りではない。

8. **should [B-1]**

   主張: 公開キー集合を通常の `set` にすると、単一正本が共有可変状態になり、任意 consumer の `.add()` が全 verifier の受理域を変えられる。

   根拠: 現行3定義はいずれも mutable set (`s8b_oracle_manifest.py:36-39`, `s8b_oracle_report.py:241-244`, `s8b_oracle_driver.py:41-44`)。公開・共有後は影響範囲が拡大する。

   提案: 公開値は `frozenset`、診断順用には別の固定 tuple を使う。テストは本番定数から期待集合を導出せず、現行どおり literal を独立 oracle として維持する。

9. **must-fix [B-7]**

   主張: 現行テスト群はこの変更の互換性を証明できず、複数の破壊が緑のまま通る。

   根拠:

   - `test_s8b_materialization.py:328-405` は非有限値、cell 文脈、driver の狭い役割を含まない。
   - `test_s8b_oracle_manifest.py:273-294` は「`binding_identity entry schema`」を期待するため文言変更で壊れる一方、複合故障順序は未検査。
   - `test_s8b_oracle_report.py:274-296` は reason に `"binding"` があることしか見ず、文言 drift を捕捉しない。
   - `test_s8b_oracle_driver.py:345-359` は event 順だけで、canonical 例外型・reason・各 field の実値不一致を固定しない。
   - `test_s8b_materialization.py:294-319` の private 定数参照は公開名へ更新が必要だが、literal 集合は残す必要がある。
   - generator role の wrong-path、委譲先 drift、report self-pin のテストがない。

   提案: NaN/Infinity、composite cell mismatch、正直な driver 別期待列、exact issue strings、mixed-fault precedence、canonical exception/WAL reason、wrong generator path を必須 fixture に追加する。

修正後に進めよ (must-fix: 1 非有限値/F7、2 cell 文脈、3 診断互換、4 driver 行列、5 例外契約、6 pin 実効性、9 テスト補強)。

### 2.3 C-γ 出力

1. **must-fix — C-1 の三択判定は Lane 全体では (c)**

   主張: duplicate key / NaN 拒否という字句規則自体は (b) の裁定非依存な fail-closed 強化であり、v2 設計素材も strict parse を「実装既定」としているため (a) ではない。しかし本 Lane の中心である現行 3 adapter への配線は、F7 の単一 `load_ratified_freeze` 導入時に置換される捨て実装である。

   根拠: `2026-07-16_s8b-freeze-v2-design-material.md:211-213`、`2026-07-16_s8b-floor-protocol-package.md:405-411,466-468`。現行 oracle 本番 manifest・実走経路も未成立で、現在価値は ratification 不可の pilot にほぼ限られる。

   提案: strict parser は F7 後の `load_ratified_freeze` 内で初めて配線する。pilot だけ緊急強化するなら driver loader の局所修正に限定し、D8' 解消とは数えない。

2. **must-fix — 共有 helper 化すると v1 の generator pin が空洞化する**

   主張: `s8b_holdout_freeze.py` が新しい `s8b_freeze_io.py` を import すると、freeze が記録する `generator.sha256` は wrapper 1 ファイルしか束縛せず、実際の生成・検証意味論を担う helper bytes が pin 外になる。

   根拠: `_load_json` は生成時の known-axes 読込にも使われる (`s8b_holdout_freeze.py:464`) 一方、source record は同ファイルだけ (`:492-494`)、検証もその path の bytes だけ (`:573-594`)。実 artifact も `holdout_freeze.json:13-15` で同じ単一-file pin。これは既に G-7 で指摘された source-bundle 問題と同型 (`2026-07-17_s8b-v2-prereqs-consultations.md:320-324`)。

   提案: closed source bundle を v2 schema で束縛できるまで共有 import を入れない。v1 schema のままこれを安全に直す方法は、共有化を諦める以外にない。

3. **must-fix — 「統一」は恒偽で、緩い consumer が複数残る**

   主張: 3 実装を置換しても oracle driver の別 parser、oracle report、floor resume が last-wins のままなので、JSON strict parse の統一とは呼べない。

   根拠: `s8b_oracle_driver.py:79-86,217`、`s8b_oracle_report.py:640-646`、`s8b_floor_campaign.py:440-460,1266-1286`。特に report は `verify_manifest()` を呼ばず、duplicate manifest を直接部分検証する。selector を触らないことは不変条件上正しいが、`s8b_selector_freeze.py:685-705,724-729` が独立 parser のままなので D8' 自体も未解消である。

   提案: 今回は「3 loader の部分 hardening」と正直に限定するか、F7 後に全 consumer を単一入口へ移す。

4. **must-fix — C-5: selector と「意味的に完全一致」は仕様不足**

   主張: 同じ `object_pairs_hook` なら nested duplicate、`"a"` と `"\u0061"` の重複、nested NaN/Infinity は同様に拒否する。非 string key は JSON 文法上存在しない。

   根拠: `s8b_selector_freeze.py:685-705`。ただし `parse_constant` は `1e999` を捕捉せず `float("inf")` として受理する。また helper が `json.loads(data: bytes)` を直接使うと UTF-16/32・UTF-8 BOM を受理し、`read_text(encoding="utf-8")` の selector より受理域が広がる。NFC/NFD の異なる key は双方とも別 key として受理する。

   提案: bytes は明示的に UTF-8 decode する。全非有限値を拒否するなら `parse_float` または再帰的 `math.isfinite` 検査を追加し、selector と同じ欠陥をコピーしない。

5. **must-fix — strict reader が自身の writer 出力を拒否し得る**

   主張: reader だけ strict 化すると、現行 writer が生成できる NaN/Infinity を後で自分で読めない非対称契約になる。

   根拠: `s8b_holdout_freeze.py:535` と `s8b_oracle_manifest.py:559` は `allow_nan=False` がなく、manifest canonicalization も `:46-52` で同様。さらに run contract は必須 key の包含しか要求しない (`:293-306`) ため、余剰 field に非有限値を持ち込める。

   提案: parser と同時に全該当 writer/canonicalizer を `allow_nan=False` にし、round-trip の拒否対称性をテストする。

6. **must-fix — floor pilot の例外契約が壊れたまま**

   主張: `load_verified_freeze()` の dup-key 拒否は `OracleDriverError` になるが、floor CLI は `FloorCampaignError` しか捕捉しないため、pilot が構造化 JSON でなく traceback で落ちる。

   根拠: loader は `s8b_oracle_driver.py:105-132`、floor import は `s8b_floor_campaign.py:81-85`、pilot 呼出しは `:1363-1371`、catch は `:1373`。これは NaN/hash mismatch でも既に存在する境界欠陥で、プラン手順 4 は floor を列挙していない。

   提案: floor 境界で `OracleDriverError` を因果付き `FloorCampaignError` に変換し、CLI subprocess テストを置く。

7. **must-fix — 共有 import は direct CLI を壊し得る**

   主張: `s8b_holdout_freeze.py` は直接実行を公開契約にしているが、現在 package bootstrap を持たない。素朴な relative import も `from campaign...` も direct invocation では失敗し得る。

   根拠: 使用法は `s8b_holdout_freeze.py:4-7`、現行 import 部は stdlib のみ (`:9-20`)。

   提案: 実施するなら package/direct の二経路 import を明示し、`python3 orchestrator/campaign/s8b_holdout_freeze.py verify ...` の subprocess 回帰を必須にする。

8. **nit — C-2 の「既存正当 artifact が壊れる」懸念は裏取り上 refuted**

   主張: 実 artifact 3 件はいずれも UTF-8 top-level object、duplicate key なし、NaN/Infinity・overflow 非有限値なしで、提案 strict parse を通る。

   根拠: `output/s8b-freeze/holdout_freeze.json`、`output/s1-freeze/known_axes_freeze.json`、`measurement_freeze.json` を全 object-pairs と再帰的 finite 検査で走査済み。全 `test_s8b_*.py` の手書き JSON も、正当入力には該当なし。例外は既存の拒否用 `{"floor": NaN}` (`test_s8b_oracle_driver.py:741`)、別 parser の duplicate negative (`test_s8b_floor_campaign.py:368`)、truncated WAL (`test_s8b_oracle_driver.py:957`) だけだった。

   提案: compatibility migration は不要。

9. **must-fix — 提案の characterization テストは配線を証明しない**

   主張: helper に実 artifact を直接食わせるだけでは、各 consumer が helper を使わなくても常に通るため mutation-killing にならない。特に `measurement_freeze.json` は提案 3 loader の実経路に接続していない。

   根拠: S1 の実 loader は別実装のまま (`s1_direct_comparison.py:105-119`、`s1_known_axes_freeze.py:120`、`s1_measurement_freeze.py:92`)。既存 materialization 8 fixtures (`test_s8b_materialization.py:328-405`) も binding schema 用で parser 配線を検査しない。

   提案: 各公開 adapter に top/nested duplicate、3 constant、`1e999`、非 UTF-8/BOM、非-object を直接投入し、domain 例外まで固定する。tracked artifact の存在は conditional skip にせず欠落を失敗にする。

10. **should — C-3 の「gate は v2-verifier-not-implemented で拒否中」は実 artifact について不正確**

   主張: checked-in v1 freeze は `floor`/`budget` がともに null なので、v2 refusal 分岐ではなく v1 `verify()` 分岐へ入り、source drift と null gate で落ちる。

   根拠: artifact `holdout_freeze.json:622-623`、分岐は `s8b_oracle_driver.py:165-182`。本番 `build_manifest()` 呼出しと `generator_versions` artifact は検索上ゼロ。一方 floor pilot は loader を現用するが、artifact は `eligible_for_refreeze: false` (`s8b_floor_campaign.py:1020`)。

   提案: oracle 防御としての即時価値を主張しない。active resume を守るなら、むしろ lax な floor manifest/journal parser を対象にすべきである。

11. **should — 「v1 時代の緩い artifact が v2 resume に混入」は経路未成立**

   主張: floor resume は protocol が pin した同一 freeze byte hash を再読し、resume manifest も同じ hash を要求するため、別の legacy freeze が黙って混入する経路はない。将来の `load_ratified_freeze` が改めて strict parse すれば、duplicate を含む旧 bytes はそこで拒否できる。

   根拠: `s8b_floor_campaign.py:1266-1282,1363-1367`。oracle は resume を全面拒否する (`s8b_oracle_driver.py:374-418`)。

   提案: 将来混入防止を本 Lane の便益に数えない。

12. **should — C-4 の追加 drift は移行照合を複雑化しないが、裁定資料を再現不能にする**

   主張: 現在の recorded→actual は generator `1910fff…→2356fd5…`、design `1829af7…→bce6eff…` で、追加編集後も v1 は単に不合格のまま。F7 の git blob 検証は `frozen_at_head` の旧 bytes を見るため、worktree の追加 drift 自体は旧世代照合を複雑化しない。

   根拠: `s8b_holdout_freeze.py:641-644` は design を先に拒否し、F7 案は `floor-protocol-package.md:447-468`。ただし同文書が実測値として固定した現行 `2356fd…` は編集直後から再現不能になり、D-10 により文書側を追随できない。

   提案: pending 裁定資料の実測状態を保つためにも、このファイルの追加編集は F7 裁定後へ送る。

13. **must-fix — 挙動同値 refactor として扱えない**

   主張: duplicate key strict 化は、従来 last-wins で受理した入力を拒否する明示的な意味変更であり、共有 helper 抽出と一括して「リファクタ」と認定すると不変条件 6 に違反する。

   根拠: 現行の素の `json.loads` は `s8b_holdout_freeze.py:137-144`、`s8b_oracle_manifest.py:79-86`。提案後は受理集合が真に縮む。

   提案: 実施時は extraction と hardening を分離し、後者を明示的な fail-closed 変更として独立レビューする。

この Lane はやめよ (strict parser は F7 後の `load_ratified_freeze` に統合すべきで、現行案は v1 generator pin を空洞化し、部分統一の捨て配線を増やす)

### 2.4 C-δ 出力

1. **深刻度: must-fix** — **主張:** 3 Lane 全部を今進める戦略は過剰である。最善は Lane A と docs 衛生だけに縮め、Lane B/C は裁定後へ送ることだ。
   **根拠:** 現行主経路は F1〜F7 裁定→floor 実測→v2 再凍結で止まっている（`docs/phase3.md:54-59`）。A は既知の import edge を安定的に除去できる一方、B は bundle pin、C は F7 意味論に依存する。層3 v3・別計測へ逸れる根拠も現 checkpoint にはない。
   **提案:** wave を「G-9 中立 freeze I/O 抽出 + docs 衛生」に縮小する。裁定が直近なら、何もせず待つ案も A と僅差だが、現行の B/C より安全である。

2. **深刻度: must-fix** — **主張:** Lane C は F7 の明白な裁定先取りであり、撤回すべきである。fail-closed 強化でも、未裁定の検証意味論を先に選んでよいことにはならない。
   **根拠:** F7 推奨案はまさに「単一 loader + duplicate key・NaN・未知 key 拒否」である（`output/insights/2026-07-16_s8b-floor-protocol-package.md:443-468`）。現行 holdout/manifest は素の `json.loads`（`s8b_holdout_freeze.py:137-144`, `s8b_oracle_manifest.py:79-86`）なので、C は受理集合も変更する。
   **提案:** F7 裁定後に `load_ratified_freeze()` として全 consumer を一括移行する。今は parser 差の在庫記録以上をしない。

3. **深刻度: must-fix** — **主張:** Lane B の manifest 委譲は report pin を実質的に弱める。これは未裁定の bundle pin を実装せず、load-bearing な検証コードだけ pin 外へ移す変更である。
   **根拠:** `generator_versions.report` は report ファイル全 bytes だけを束縛し、manifest は対象外である（`s8b_oracle_manifest.py:35,309-332,544,651`）。現行 binding validator は report 内部（`s8b_oracle_report.py:241-277`）だが、委譲後は report hash が同じまま manifest 側の変更で受理挙動を変えられる。bundle pin は明示的残課題である（`docs/worklog.md:179-183`）。
   **提案:** bundle pin の形が決まるまで validator 統合を延期し、現行 drift guard を維持する。本番 manifest が未生成という事実は「移行不要」を意味するだけで、将来 pin の完全性は保証しない。

4. **深刻度: must-fix** — **主張:** manifest/report の validator は8 fixture外では同値でなく、B を「挙動同値リファクタ」として実装できない。どちらへ寄せても現行挙動が変わる。
   **根拠:** manifest canonicalizer は `allow_nan=False` を指定せず（`s8b_oracle_manifest.py:46-52`）、report は拒否する（`s8b_oracle_report.py:56-59`）。実際に `genome_canonical={"x": NaN}` と整合 hash を与えると、manifest は受理し report は `ValueError` になった。既存行列も cell identity・件数・重複を意図的に除外している（`test_s8b_materialization.py:328-405`）。
   **提案:** 将来 B を行うなら、NaN・非JSON値・重複/余剰 cell・複数同時違反まで先に characterization し、manifest 側を厳格拒否へ変えるなら「正しさ hardening」として別裁定・別 commit にする。report を permissive 側へ寄せてはならない。

5. **深刻度: should** — **主張:** driver を8 fixture行列へ直接追加しても、本番経路の盲点は埋まらず恒真化しやすい。
   **根拠:** `run_block()` は `_expected_binding()` より先に `verify_manifest()` を通し（`s8b_oracle_driver.py:463-481,579-582`）、そこで同じ entry は全件検証済みである。private helper 単体へ壊れた fixture を通すのは本番順序を再現しない。
   **提案:** 壊した実 manifestを `run_block()` に渡し、`status=refused`、campaign/budget書込みゼロ、prepare/evaluateゼロを固定する統合負テストに置き換える。

6. **深刻度: should** — **主張:** canonical helper の重複前提は不完全で、driver/materialization の一組だけを統合するのは恣意的である。
   **根拠:** 同系実装は driver、materialization、manifest、report、floor に存在する（例: `s8b_oracle_driver.py:65-76`, `s8b_materialization.py:35-46`, `s8b_floor_campaign.py:122-133`）。また driver helper は binding 比較だけでなく marker preimage・manifest hash にも使われる（`s8b_oracle_driver.py:385,483,582`）。materialization helperへ寄せると非materialization処理が `MaterializationError` 契約へ漏れる。
   **提案:** 今回は generic canonical helper を触らない。将来行うなら、標準ライブラリだけの中立 primitiveと consumer別例外 adapterを別スコープで設計する。

7. **深刻度: must-fix** — **主張:** Lane A は単純移動ではない。新 leaf の例外型を決めずに動かすと driver の拒否応答か floor CLI の失敗形が変わる。
   **根拠:** 現 loader は `OracleDriverError` を送出し、`run_block()` はそれだけを捕捉する（`s8b_oracle_driver.py:105-132,454-461`）。floor `main()` は `FloorCampaignError` しか捕捉しない（`s8b_floor_campaign.py:1363-1377`）。既存テストも driver API の例外型を固定している（`test_s8b_oracle_driver.py:722-744`）。
   **提案:** leaf は `FreezeIOError` を所有し、driver/floor が各 domain errorへ因果付き変換する。`VerifiedFreeze` は単一 class identity、driver の公開名は互換 wrapper/re-exportで保持する。floor の現行 traceback をJSON errorへ直すなら、リファクタではなく明示的 hardening として扱う。

8. **深刻度: should** — **主張:** NUMACTL を `p2_2.NUMA` 由来にするのは「一本化」ではなく、歴史的 campaign driverへの所有権追加である。G5' env contract 完了とは絶対に数えられない。
   **根拠:** `p2_2.py:36-41` は歴史的 pin を持つ campaignで、oracleや他 campaignには同値定数が残る。既存 cold-import testは import成功しか見ず、floor→oracle edge不存在を証明しない（`test_s8b_materialization.py:535-551`）。
   **提案:** 裁定前は floor ローカル定数でもよい。`p2_2.NUMA` を使うなら挙動同値だけを主張し、AST/import負テスト、`sys.modules` 不在、既定 measure経路へ渡る argv の完全一致を追加する。

9. **深刻度: should** — **主張:** trace-disabled build共有の見送り結論は正しいが、「consumer 1なので価値薄」という理由は不正確である。実際には既に共通 primitiveを使っている。
   **根拠:** oracle は `pipeline.evaluate()` 内で `buildcache.build(..., trace=False)` を呼び（`pipeline.py:423-429`）、floor も同じAPIと `s8b-build-cache` を使う（`s8b_floor_campaign.py:581-606`, `s8b_oracle_driver.py:591-596`）。
   **提案:** pipelineへ新wrapperを挿入せず、同一引数契約の結線テストで足りるかを G6' の残課題として再評価する。観測者効果に近い経路へ抽象層を足す利益は薄い。

10. **深刻度: must-fix** — **主張:** phase の pointerだけを `(5)` から新エントリへ替えると、現在の「裁定非依存の3件」という文言が新 wave の完了数に読めて腐る。
    **根拠:** 現文は「3件は部分基盤のみ、完了と数えない」と固定している（`docs/phase3.md:54-57`）。worklog は commit内容の再説明を禁じ、未裁定・持ち越し中心の短い索引を要求する（`docs/worklog.md:12-23`）。
    **提案:** 「裁定非依存の先行基盤は複数 wave で部分実装したが、v2 前提条件の完了には数えない。正本=新 worklog」と一般化する。F1〜F7、G6'、bundle pin、G5' は未完了のまま明記し、phase checkboxは動かさない。

11. **深刻度: should** — **主張:** F15 は既存タグへ再分類せず、`[テスト代表性]` を型タグ台帳へ追加するのが正しい。
    **根拠:** F15 の根因は「仕様形だけのモックと実出力分布の乖離」であり、単なる手順漏れではない（`docs/failures.md:141-152`）。後続監査でも独立した F15 型レンズとして再利用されている（`output/insights/2026-07-16_s8b-third-wave-audit.md:29`）。
    **提案:** `docs/failures.md:17-18` に第9タグとして追加する。未知タグ lint は有用だが、この小 wave の blocker にする必要はない。

12. **深刻度: must-fix** — **主張:** 全体基線が緑だけでは不十分で、さらに新テスト追加後も「996 passed維持」と書くと未収集を見逃す。pass数は追加分だけ増えるべきである。
    **根拠:** Lane Aには single-read、hash mismatch、invalid UTF-8/top-level、consumer別例外、class identity、floor既定NUMA、import-edge不存在が必要である。完了時には関連テストに加え `check_codex_agents.py`、`check_docs.py`、commit後の provenance監査が必須（`AGENTS.md:26-28`）。
    **提案:** targeted負テスト→collect件数差分→`tools/run_tests.py`→2 checker→各commit後 provenance の順で検算する。記録上の現基線 996/23/0 は `docs/worklog.md:233-280` と一致したが、このread-only環境では writable temp directory不在のため fresh suite完走は確認できなかった。

13. **深刻度: should** — **主張:** D-10等の不可触面は「触らない予定」だけでなく差分防壁を置くべきである。
    **根拠:** A/Bは driver周辺を、docs Laneは近接する insight/docsを触るため、広い stagingやformatterで凍結文書を巻き込める。Codexには project hookが自動適用されない（`AGENTS.md:17-20`）。
    **提案:** 開始時/終了時の2文書SHA-256比較、明示path staging、凍結2文書・`_outcome_for`・report allowlist・`_validate_execution_snapshot`・PreparedCell定義・selector import面の forbidden-diff確認を追加する。phase完了を付ける場合だけは実装と同じcommitに置く。

総合判定: **修正後に進めよ (must-fix: Lane C撤回、Lane Bをbundle pin後へ延期、Lane Aの例外/API契約固定、docsの未完了表現修正、targeted負テストと必須検算追加)**

---

## 3. 親裁定 (2026-07-18) — codex 敵対相談 4 本 (C-α/C-β/C-γ/C-δ、計 46 所見) の採否

裁定者 = 親セッション (claude fable-5)。裁定原則は前 wave と同一: (i) F1〜F7 を先取りしない、
(ii) 発効なし・fail-closed 不変 (強化はユーザー裁定材料へ)、(iii) 正直な部分完了 (恒真 claim 禁止)、
(iv) 裁定待ちパッケージ文書は 1 byte 不変 (D-10)。

## C-α (Lane A: freeze I/O 中立化) — 11 所見

| 所見 | 裁定 | 反映 |
|---|---|---|
| A-1 実再エクスポート | real 採用 | module alias 参照 + `hasattr(driver, "load_verified_freeze") is False` 負テスト。全 consumer 移行 (再エクスポートなし = 前 wave G-8 と同方針。C-δ #7 の互換 re-export 案は棄却) |
| A-2 例外境界 3 点 | real 採用 | leaf が `FreezeIOError` を所有。driver / floor の境界 adapter で因果付き変換、refusal class 名・message・rc を固定。floor CLI が loader 例外を捕捉できない現行欠陥の是正は「境界欠陥の是正」として正直に記録 (純リファクタと呼ばない) |
| A-3 TOCTOU 恒真 | real 採用 | `Path.read_bytes` 厳密 1 回の positive control + `gate_check(verified=...)` への同一 object 受け渡し identity テスト |
| A-4 cold-import 恒真 | real 採用 | fresh subprocess で floor 単独 import 後 `campaign.s8b_oracle_driver not in sys.modules` を assert。**実装前に現行コードで赤になることを確認** (F9 型対策)。AST 走査は補助 |
| A-5 NUMACTL 配線未実行 | real 採用 | `from campaign.p2_2 import NUMA as NUMACTL` (module 属性・値を維持) + `measure_fn=None`・fake `measure_point` の配線テスト (`numactl is p2_2.NUMA`) |
| A-6 単一正本化の過大主張 | 採用 | worklog は「floor-local の由来統一。oracle との重複は G5' まで意図的残置」と記録 |
| A-7 ratified 先取り回避 | 採用 | docstring に「現行 raw bytes loader の中立置場。ratified 型/strictness 追加は F6/F7 後」と明記。dup-key 拒否等は追加しない |
| A-8 責務名 | 採用 | docstring で対象を「実行用 holdout freeze bytes の読込」に限定。s8b_holdout_freeze.py は不可触 (C-γ #12 と併せ確定) |
| A-9 loader 行列不足 | 採用 | 新 leaf テストに受理拒否行列 (read 不能 / invalid UTF-8 / malformed JSON / top-level 非 object / hash 不一致 / NaN)。strictness は現状同値 (characterization) |
| A-10 完了検査 | real 採用 | targeted → collect 件数差分 → tools/run_tests.py → check_docs + check_codex_agents → commit 後 provenance 監査 |
| A-11 基線不一致 | 解決 | worklog (5) の 996/22/1 はエントリ (7) の D60 降格以前の値。現基線 = 996 passed / 23 skipped / 0 failed (親が writable 環境で実測) |

## C-β (Lane B: binding 検証統合) — 9 所見

統合本体は C-δ #3 (pin 外への load-bearing 検証移動 = report pin の実質弱体化) と B-1 非同値により
**v2 (closed source bundle pin 裁定後) へ延期** — 前 wave G-6 裁定「統合は v2 へ」を再確認する形。
Lane B は **Lane B′ (テストのみ、production 0 byte 不変)** に縮小。

| 所見 | 裁定 | 反映 |
|---|---|---|
| B-1 manifest NaN 受理の非同値 | real 採用 (縮小) | 統合しないため挙動変更なし。乖離を known-drift characterization テストで機械固定 (v2 材料コメント付き)。manifest canonicalizer / writer の `allow_nan=False` 化は fail-closed 強化として**ユーザー裁定材料に記録** (C-δ #4 の「別裁定」指示に従う) |
| B-2 cell identity 検査消失 | real 採用 (縮小) | 統合しないため非発生。report の cell mismatch positive control (list / nested / composite `H:C`・`H/C` 形) を追加 |
| B-3 issue 文言 = artifact 出力 | real 採用 (記録) | v2 統合時の設計要件として記録: 共有層は安定 issue code、文言・複合故障 precedence は consumer 側 render + golden |
| B-4 driver 非同値 (4/8 fixture) | real 採用 (置換) | C-δ #5 を優先し driver fixture 列は作らない。代わりに run_block 統合負テスト (壊れた manifest → status=refused、prepare/evaluate 不発火、campaign/budget 書き込みゼロ) |
| B-5 WAL reason 契約 | real 採用 (中止) | canonical helper 統合自体を中止 (C-δ #6: marker preimage / manifest hash へ MaterializationError 契約が漏れる)。v2 設計要件として記録 |
| B-6 pin は provenance 記録に過ぎない | real 採用 (記録) | role→正規 path 束縛なし (materializer に CLAUDE.md を指定しても受理、実証済み)。v2 bundle pin 設計要件に「role→path 束縛 + source closure + report 実行時自己検査」を記録。pin を変更安全性の根拠に使わない |
| B-7 配置は versioned leaf | 採用 (記録) | v2 統合時の設計要件として記録 (`ORACLE_BINDING_IDENTITY_V1_*` 等) |
| B-8 frozenset | 採用 (記録) | v2 設計要件として記録。テストの literal 集合は独立 oracle として維持 |
| B-9 テスト補強 | real 採用 (縮小) | Lane B′ のテスト 3 群に反映 |

## C-γ (Lane C: JSON strict parse 統一) — 13 所見

**Lane C 撤回** (総合判定「やめよ」を採用。C-δ #2 と一致)。根拠: strict parser は F7 後の
`load_ratified_freeze` で配線すべき捨て実装 / s8b_holdout_freeze.py への共有 import は v1 generator
pin を空洞化 (G-7 同型) / 3 loader 置換でも緩い consumer が残り「統一」は恒偽 / dup-key 拒否は
受理集合縮小でありリファクタではない。

副産物として記録するもの: (1) 実 artifact 3 件 (holdout_freeze / known_axes / measurement) は
strict parse をすべて通る (C-γ 実測。v2 移行時の互換確認済み事実)。(2) strict reader 化には writer /
canonicalizer の `allow_nan=False` 対称化が必要 (round-trip 対称性、C-γ #5)。(3) `1e999` は
parse_constant で捕捉されず inf 受理 — selector 実装にも同欠陥 (C-γ #4)。(4) s8b_holdout_freeze.py
への追加編集は裁定資料が固定した実測 drift hash (2356fd…) を再現不能にするため **F7 裁定まで同
ファイルは一切編集しない** (C-γ #12。Lane A でも遵守)。(5) floor CLI 境界欠陥 (C-γ #6) は Lane A で是正。

## C-δ (wave 全体) — 13 所見

| 所見 | 裁定 | 反映 |
|---|---|---|
| D-1 スコープ縮小 | 部分採用 | Lane C 撤回・Lane B 統合延期は採用。Lane B′ (テストのみ) は「盲点の機械固定」として維持 — 前 wave G-6 裁定 (drift-guard 追加) と同型で統合ではない |
| D-2 Lane C = F7 先取り | real 採用 | 撤回 |
| D-3 Lane B = pin 弱体化 | real 採用 | 統合延期。bundle pin 設計要件へ B-6 と併せ記録 |
| D-4 非同値 (NaN) | real 採用 | characterization + ユーザー裁定材料 (B-1 と同一) |
| D-5 driver 行列より統合負テスト | 採用 | run_block 統合負テストに置換 (B-4) |
| D-6 canonical helper 統合中止 | real 採用 | 中止 (B-5) |
| D-7 Lane A 例外契約 | real 採用 | A-2 と同一。re-export のみ C-α 側 (再エクスポートなし) を採用 |
| D-8 NUMACTL 正直記録 | 採用 | A-5/A-6 と同一 |
| D-9 trace-disabled build 見送り理由の訂正 | real 採用 | worklog の見送り理由を訂正: 「consumer 1 で価値薄」ではなく「oracle/floor は既に buildcache.build(trace=False) primitive を共有。残るのは同一引数契約の結線テストで足りるかの再評価 (G6' 残課題)」 |
| D-10 phase3 文言腐敗 | real 採用 | 「裁定非依存の先行基盤は複数 wave で部分実装 (完了と数えない)。正本 = worklog 最新の v2 前提条件エントリ」へ一般化。checkbox 不変 |
| D-11 F15 タグ | 採用 | `[テスト代表性]` を docs/failures.md 冒頭台帳の第 9 タグとして追加 (再分類しない) |
| D-12 検算順序 | real 採用 | A-10 と同一 + collect 件数差分 (passed 数は追加分だけ増えるべき) |
| D-13 forbidden-diff 防壁 | 採用 | 凍結 2 文書 (floor-protocol-package / freeze-v2-design-material) の SHA-256 前後比較 + 明示 path staging。`_outcome_for` / report allowlist / `_validate_execution_snapshot` / PreparedCell 定義 / selector import 面 / s8b_holdout_freeze.py の diff ゼロ確認 |

## 4. 確定プラン (縮小後)

- **Lane A**: `orchestrator/campaign/s8b_freeze_io.py` 新設 (stdlib のみ leaf。`FreezeIOError` /
  `VerifiedFreeze` / `load_verified_freeze`。strictness は現行同値 = NaN/Infinity 拒否のみ、dup-key
  拒否は追加しない)。s8b_oracle_driver / s8b_floor_campaign / テストを新 import へ移行 (再エクスポート
  なし)。境界 adapter で例外変換 + message/rc 固定。floor CLI の loader 例外構造化は境界欠陥是正として
  記録。NUMACTL は `from campaign.p2_2 import NUMA as NUMACTL`。新テスト = test_s8b_freeze_io.py
  (受理拒否行列 / 単一 read / identity / import-edge subprocess 負テスト / hasattr 負テスト /
  NUMACTL 配線)。s8b_holdout_freeze.py と test_s8b_materialization.py は不可触。
- **Lane B′**: テストのみ。新ファイル `orchestrator/tests/test_s8b_binding_driftguards.py` に
  (1) NaN 乖離 characterization、(2) report cell mismatch positive control、(3) run_block 統合負テスト。
  production コード 0 byte 不変。既存 test_s8b_materialization.py は変更しない (衝突回避のため必要時
  のみ追記可)。
- **Lane C**: 撤回 (worklog に理由と副産物を記録)。
- **Lane D**: insights 逐語凍結 (プロンプト 5 + 出力 4 + 本裁定 + 確定プラン) / failures.md 第 9 タグ /
  phase3 checkpoint 文言一般化 / worklog 新エントリ (親が執筆) / handoff 削除 / SHA 前後比較。
- commit はレーン別、AI provenance trailer 付き、push しない (ユーザー引き渡し)。
