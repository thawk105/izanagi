# 2026-07-20 wave 2 (裁定パッケージ実装) — ハイブリッド標準ループの逐語凍結

branch approved-waves、基点 58934ae → 最終 code commit a89e2b8。プラン起草を codex に委譲する
ハイブリッド形式の初回試行 (親 = brief + 裁定 + scope 監査 + 統合 + 変異ゲート)。
変異台帳 (machine-readable) = 2026-07-20_wave2-mutation-ledger.json。

## brief (親→planner、逐語)

```
あなたは実装プランの起草者です。以下の brief と repo の実コードを読み、緻密な実装プランを書いてください。あなたのプランは後段で独立した敵対的レビュー 2 本の攻撃対象になります。曖昧さを残すほど攻撃されるので、file:line 粒度で具体化してください。

# 背景 (ユーザー裁定、確定済み — この scope を超える実装を計画しないこと)

s8b campaign (orchestrator/campaign/s8b_*.py) の oracle 後処理に関する裁定済み 5 件を実装する。公式実験は extime=5/reps=5 (leaf: s8b_experiment_numbers.py に pin 済み)。探索 (試行錯誤) は 3 秒 3 回目安で検証器の対象外。

実装順の裁定: P-A1(b) → P-B5+P-B6 (+P-A2) → P-A5。P-A1(a) は本 wave では実装せず段階導入の設計判断の記録まで。

1. **P-A1(b)**: 探索成果物を公式成果物と別の namespace/書式に隔離し、official 側 (report/judge/combined verdict) が型で拒否する。現状: report は独自の軽量 manifest 検査のみで verify_manifest を呼ばず (s8b_oracle_report.py:69-102)、run_contract 欠落 manifest を legacy として receipt 検査なしで受理し (同 :524-544 _receipt_expectations)、CLI は raw JSON を直接使う (同 :758-767)。judge は manifest_sha256 の非空 str しか見ず (s8b_oracle_judge.py:130-133)、combined verdict は転記のみ (s8b_verdict.py:597,716,735)。layout.py:204 に探索/公式の型区別なし。**(a) の検査必須化・legacy 受理廃止は今回やらない** — その段階導入方針を設計判断として文書化する所まで
2. **P-A2**: 裁定 =「reps=5 は成功した測定値 5 個。足りなければ不合格」。report が len(tps)==run_contract.reps を検査する (s8b_oracle_report.py:409-421 の bench 集計)。calibrator/runner.py の require_all_reps 既定は触らない (探索経路は対象外)
3. **P-B5**: outcome ごとの段階 truth-table (例: build-failed は build_done==0 ∧ verify 両 missing ∧ bench 無し / timeout は build_done==1 ∧ bench 無し 等) を abort reason 閉表 (s8b_abort_reason_contract.py) と同じ stdlib-only leaf 思想で閉表化し、_assess_window (s8b_oracle_report.py:327-515) で検査する。binary-mismatch 分岐 (:469-482) が唯一の full truth-table 形の手本。既知 false-accept 2 例 (build-failed 宣言 + verify_done(pass) 付き WAL / timeout 宣言 + bench_done 付き WAL) は負例テスト化必須
4. **P-B6**: 全 PIPELINE_STAGES record の payload について Mapping 検査を row-level protocol_violation 化する。_binding_schema_issues (s8b_oracle_report.py:273-278) の様式が手本。現状の穴: :384-393 (build.payload)、:414 (benches[0].payload)。CLI の例外捕捉 (:748-767) に AttributeError が無く report 全体が落ちる
5. **P-A5**: standalone gate-check (s8b_oracle_driver.py:165-286、CLI :1220-1270) は launch_validate を呼ばず、load_ratified_freeze (s8b_ratified_freeze.py:1286-1327) は floor protocol の数値検証をしない。v2 gate-check で launch_validate または floor protocol full validation (s8b_floor_contract.py:104-229 validate_protocol) を必須化し、floor extime=3 + oracle manifest 5/5 の負例 fixture で allowed=False を固定する

# 不変条件 (破るプランは不採用)

- 正しさ検査を緩める・迂回可能にする方向の変更は不可。すべて fail-closed
- 裁定 scope を超える実装を計画しない。scope 外の発見は「実装せず報告」として別節に列挙
- 新しい閉表/truth-table は stdlib-only leaf (s8b_abort_reason_contract.py と同思想)
- 新テストが実 repo ROOT を読む場合は conftest.py REAL_REPO_SERIAL_NODES と test_real_repo_serialization.py の golden の両側に列挙 (二重台帳)
- 既存テスト・fixture への影響 (探索 namespace 導入の後方互換) を明示する

# プランに必ず含める成果物

(i) 実装ステップ (file:line 粒度、変更ごとに理由 1 行)
(ii) 並列実行のための作業分割案 (2 単位目安。ファイル競合面と依存を明示。競合するなら直列化を指示)
(iii) 変異テスト事前登録リスト (実装予定の各検査に対し「この 1 行をこう壊したらどのテストが赤くなるか」の対応表。8〜15 本)
(iv) 追加する正例/負例テストの一覧 (テストファイル・テスト名・何を固定するか)
(v) docs 記録方針 (phase3.md 見送り台帳の裁定・完了記録様式、decisions.md への設計判断)
(vi) P-A1(a) 段階導入の設計判断ドラフト (実装しない。方針文書のみ)

# 出力形式

番号付き節。根拠の file:line は実際に repo を読んで確認したものだけを書く。推測は「未確認」と明記。日本語で。
```

## プラン v1 (codex planner gpt-5.6-sol max、逐語)

```
以下を実装プランとします。行番号は現行コードを基準にしており、新規ファイルは「現行行なし」と明記します。実装・テスト実行はまだ行っていません。

## 1. 設計の要点と実装順

実装順は裁定どおり、次の barrier を置きます。

1. P-A1(b): 探索 artifact の namespace・schema・実行時型を分離
2. P-B5 + P-B6 + P-A2: report の証拠検査を同一 wave で強化
3. P-A5: standalone v2 gate-check に full launch validation を追加
4. P-A1(a): `decisions.md` に段階導入方針だけ記録し、コードは変更しない

P-A1(b) の「型」は `TypedDict` のような静的型ではなく、JSON 互換の専用 `dict` subclass と role-specific loader で実装します。これにより既存の添字アクセス・`json.dump`・等値比較を保ちつつ、report / judge / combined verdict は raw `dict` や探索型を受理しなくなります。

ただし、この型は検証済み provenance の証明ではありません。official schema を偽装して official loader を呼ぶ攻撃まで閉じるのは P-A1(a) であり、本 wave では明示的な残存リスクとします。

## 2. 実装ステップ

### 2.1 P-A1(b): 探索 namespace・書式・型の分離

1. `orchestrator/campaign/s8b_oracle_artifacts.py` を新設します（現行行なし）。

   追加する契約は以下で固定します。

   - official runtime 型:
     - `OfficialManifest`
     - `OfficialObservations`
     - `OfficialVerdict`
   - exploration runtime 型:
     - `ExplorationArtifact`
   - official schema 定数:
     - `8b-oracle-manifest/v1`
     - `8b-oracle-observations/v1`
     - `8b-oracle-verdict/v1`
   - exploration schema:
     - `8b-oracle-exploration-artifact/v1`
   - exploration exact top-level keys:
     - `schema_version`
     - `artifact_role`
     - `campaign_id`
     - `measurement_hint`
     - `payload`
   - `artifact_role` の閉集合:
     - `manifest`
     - `observations`
     - `verdict`
   - `measurement_hint` の exact keys:
     - `extime_s`
     - `reps`
   - `extime_s` / `reps` は非 bool の正整数のみ。3/3 は受理するが、5/5 を要求する official validator は呼ばない。
   - `Official*` / `ExplorationArtifact` は相互に継承させず、consumer は `type(value) is Official...` で exact type を要求する。
   - `OracleArtifactTypeError` を定義し、official loader・consumer の共通拒否型にする。
   - `load_official_manifest()` は分類器に限定する。`verify_manifest()` や `_validate_run_contract()` は呼ばない。
     - `schema_version == official v1` は `OfficialManifest` にする。
     - `schema_version` 欠落も staged legacy として `OfficialManifest` にする。
     - exploration schema または未知の明示 schema は拒否する。
   - observations / verdict の official loader は各 official schema の完全一致を必須とする。
   - docstring に「型マーカーであって provenance 検証ではない」と明記する。

   理由: 現在は各 module が schema literal と raw `Mapping` を別々に扱い、JSON round-trip 後の役割境界が存在しないため。

2. [layout.py:164-212](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/layout.py:164) を変更します。

   - 現行 `CampaignLayout` の path property と `ensure()` を私有共通 base に抽出する。
   - `CampaignLayout` は従来どおり official 用 public 型として残す。
   - sibling 型 `ExplorationCampaignLayout` を追加する。`CampaignLayout` の subclass にはしない。
   - `campaign_id` 検査 [204-210](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/layout.py:204) を私有 helper に一元化する。
   - 現行 `campaign_layout()` の出力は変更しない:
     - `<output_root>/campaigns/<campaign_id>`
   - `exploration_campaign_layout()` を追加する:
     - `<output_root>/exploration/campaigns/<campaign_id>`

   理由: 既存 official artifact の場所を移動せず、探索 WAL・report を official report が探索しない別 root に閉じるため。

3. `orchestrator/campaign/s8b_oracle_exploration.py` を新設します（現行行なし）。

   - `package_exploration_artifact()` は `ExplorationCampaignLayout` exact type のみ受理する。
   - 出力先はユーザー指定不可とし、次へ create-only で書く:
     - `reports/<artifact_role>.exploration.json`
   - CLI を追加する場合も `--out` は設けず、`--output-root`、`--campaign-id`、`--role`、`--extime-s`、`--reps`、`--input` のみにする。
   - 入力 payload は top-level `Mapping` を要求する。
   - この module は探索を実行・判定せず、generic pipeline の成果を隔離形式へ包装するだけにする。

   理由: official validator に `mode=exploration` bypass を作らず、3/3 の探索成果を置く実在の入口を用意するため。

4. [s8b_oracle_manifest.py:23-41](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:23)、[642-718](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:642)、[751-845](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:751) を変更します。

   - `SCHEMA_VERSION` を artifact module の official manifest schema の再輸出にする。
   - `build_manifest()` は `OfficialManifest` を返す。
   - `write_manifest()` は `OfficialManifest` exact type のみ受理する。
   - `verify_manifest()` は全検査後、`VerifiedManifest.document` に `OfficialManifest` を格納する。
   - 既存 `VerifiedManifest` の意味と full verification は変更しない。

   理由: official producer が最初から official 型を発行し、探索型を official writer へ渡せないようにするため。

5. [s8b_oracle_report.py:69-102](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:69)、[701-739](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:701)、[758-767](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:758) を変更します。

   - `build_observations()` の先頭で `OfficialManifest` exact type を要求する。
   - `_validate_manifest()` の既存軽量検査は残す。`verify_manifest()` は呼ばない。
   - 戻り値を `OfficialObservations` にする。
   - CLI は `json.loads()` の戻り値を直接渡さず、`load_official_manifest()` を通す。
   - exploration schema、raw `dict` の直接 API 呼出し、未知 schema は official observations を一切生成せず拒否する。
   - staged legacy として `run_contract` 欠落 manifest は引き続き受理する。

   理由: P-A1(a) を先取りせず、探索型だけを official report 境界で確実に止めるため。

6. [s8b_oracle_judge.py:118-262](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_judge.py:118)、[280-288](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_judge.py:280) を変更します。

   - `judge_oracle()` は `OfficialObservations` exact type のみ受理する。
   - raw / exploration 入力を従来の「official indeterminate verdict」へ変換せず、例外で拒否する。
   - typed だが内部構造が壊れた official observations に対する既存 indeterminate 判定は残す。
   - 戻り値を `OfficialVerdict` にする。
   - CLI は `load_official_observations()` を使い、型不一致時は rc=2、出力ファイルなしとする。

   理由: 探索 observations を official indeterminate verdict へ昇格させる経路も閉じる必要があるため。

7. [s8b_verdict.py:550-599](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_verdict.py:550)、[725-740](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_verdict.py:725)、[827-853](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_verdict.py:827) を変更します。

   - `VerifiedPrediction` 検査 [565-567](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_verdict.py:565) の直後に、`oracle` が `OfficialVerdict` exact typeか検査する。
   - raw / exploration oracle は `_oracle_holdouts()` へ進めず `VerdictError` にする。
   - CLI は `_load_json_object()` の raw 戻り値ではなく `load_official_verdict()` を使う。
   - `oracle_manifest_sha256` の転記 [597-599](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_verdict.py:597)、[716](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_verdict.py:716)、[735](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_verdict.py:735) は変更しない。

   理由: combined verdict まで探索型を通さず、manifest hash 再束縛は P-A1(a) に残すため。

### 2.2 P-B5: outcome 段階 truth-table

1. `orchestrator/campaign/s8b_outcome_stage_contract.py` を新設します（現行行なし）。

   `s8b_abort_reason_contract.py` が stdlib-only leaf であることは [1-8](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_abort_reason_contract.py:1) に明記されています。同じ規律で、他の campaign module を一切 import しません。

   追加するもの:

   - `PIPELINE_STAGES`
   - `OUTCOMES`
   - immutable `StageEvidence`
   - `OUTCOME_STAGE_TRUTH_TABLE`
   - `matches(outcome, evidence)`

   exact truth-table は次で固定します。

   | outcome | build_start | build_done | legacy | s2 | bench_done | abort | commit | abort workload tag |
   |---|---:|---:|---|---|---:|---:|---:|---|
   | committed | 1 | 1 | pass | pass | 1 | 0 | 1 | `None` |
   | correctness-red | 1 | 1 | red | missing | 0 | 1 | 0 | `legacy` |
   | correctness-red | 1 | 1 | pass | red | 0 | 1 | 0 | `s2` |
   | build-failed | 1 | 0 | missing | missing | 0 | 1 | 0 | `None` |
   | timeout | 1 | 1 | missing | missing | 0 | 1 | 0 | `legacy` |
   | timeout | 1 | 1 | pass | missing | 0 | 1 | 0 | `s2` |
   | bench-failed | 1 | 1 | pass | pass | 0 | 1 | 0 | `None` |
   | verify-inconclusive | 1 | 1 | missing | missing | 0 | 1 | 0 | `legacy` |
   | verify-inconclusive | 1 | 1 | pass | missing | 0 | 1 | 0 | `s2` |
   | binary-mismatch | 1 | 1 | missing | missing | 0 | 1 | 0 | `None` |

   abort reason 自体は既存 `s8b_abort_reason_contract.py:11-30` を唯一の正本として残し、新 leaf へ複製しません。

   理由: 現行の outcome 分岐 [434-495](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:434) は条件の粒度が不揃いで、binary-mismatch [469-482](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:469) だけが完全形だからです。

2. [s8b_oracle_report.py:327-515](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:327) を変更します。

   - counts、legacy/s2 state、bench count、abort workload tag から `StageEvidence` を一度だけ構築する。
   - `_outcome_stage_contract.matches()` を module-qualified で呼ぶ。
   - 現行 [434-495](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:434) の重複した段階条件を削除し、次だけを outcome 固有検査として残す:
     - build-failed reason membership
     - timeout reason membership
     - bench-failed reason membership
     - verify-inconclusive reason membership
     - binary-mismatch 固定 reason
   - 物理順序検査 [430-432](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:430) は独立防壁として残す。
   - mismatch 時の理由には outcome と actual `StageEvidence` を含める。

   理由: 段階証拠の authority を一か所にし、分岐ごとの条件落ちを再発させないため。

### 2.3 P-B6: 全 pipeline payload の row-level Mapping guard

1. [s8b_oracle_report.py:363-421](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:363) に `_pipeline_payload_issues()` と安全な payload 射影 helper を追加します。

   - `pipeline_records` に含まれる全 record を走査する。
   - `payload` が `Mapping` でなければ、
     - `pipeline[ordinal] <stage>.payload が object でない`
     を `issues` に追加する。
   - 不正 record を counts や truth-table から除外しない。存在証拠は残したまま、その row を不合格にする。
   - build binding の `.get()` [388-389](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:388) と bench `.get()` [414](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:414) は、Mapping でなければ `{}` を見る安全な経路へ統一する。
   - abort reason / workload tag 抽出も同じ helper を使う。
   - 最終的には既存 [512-514](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:512) により row-level `protocol_violation` になる。

   理由: `AttributeError` を CLI 全体の例外へ変換するだけでは観測行を失うため、データ異常を row に帰属させる必要があるため。

2. CLI の例外列 [764](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:764) には `AttributeError` を追加しません。

   理由: 全 PIPELINE_STAGES のデータ由来 `.get()` は上記 guard で除去し、未知の `AttributeError` はプログラム不具合として隠さないため。CLI テストで「rc=0かつ該当 row が protocol_violation」を固定します。

### 2.4 P-A2: reps は成功測定値の exact 件数

1. [s8b_oracle_report.py:69-102](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:69) で `expected_reps` を抽出します。

   - `run_contract` が存在する場合:
     - `Mapping` であること
     - `reps` が非 bool の正整数であること
     を検査する。
   - `run_contract` が欠落する staged legacy manifest では `expected_reps=None` とする。
   - `_validate_manifest()` の戻り値へ `expected_reps` を追加し、`build_observations()` → `_assess_campaign()` → `_assess_window()` に明示引数で渡す。変更 anchor は [701-720](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:701)、[573-574](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:573)、[670-672](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:670)。

   理由: hardcoded 5 ではなく manifest が宣言した reps と観測証拠を直接束縛し、full pin 検査は P-A1(a) に残すため。

2. [s8b_oracle_report.py:409-421](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:409) を変更します。

   - tps の型・有限値検査後、`expected_reps is not None` なら `len(raw_values) == expected_reps` を要求する。
   - 4件だけでなく6件も拒否する。
   - 不一致時は `bench_values=[]` のままとし、理由に actual / expected 件数を含める。

   理由: protocol violation の row から部分標本が後段へ漏れない all-or-nothing 射影にするため。

3. [calibrator/runner.py:390-399](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/runner.py:390)、[425-446](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/runner.py:425) は変更しません。

   理由: `require_all_reps=False` は探索・汎用経路の契約であり、裁定は official report の証拠件数検査だからです。

### 2.5 P-A5: standalone v2 gate-check の full validation

1. [s8b_oracle_driver.py:225-245](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:225) を変更します。

   v2 branch を次の順序に固定します。

   1. `launch_validated` が渡されていれば同一 object を再利用し、再検証しない。
   2. `ratified_error` があれば即 `freeze-ratify` refusal。
   3. `ratified` が渡されていれば候補にする。
   4. 候補がなければ `load_ratified_freeze(root)` で active static freeze を読む。
   5. static `RatifiedFreeze` に必ず `launch_validate(candidate, root)` を一度だけ実行する。
   6. `RatifiedFreezeError` は
      - `v2-execution: launch-validate: [reason] ...`
      に変換する。
   7. その他の例外も同 prefix で refusal にする。
   8. freeze SHA は `LaunchValidatedFreeze.ratified.sha256` と比較する。

   理由: static loader は floor protocol を parse するだけで、数値検証を deferred と明記しているためです。[s8b_ratified_freeze.py:901-915](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:901)

2. run-block の既存経路 [782-853](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:782) は変更しません。

   ここでは既に `load_ratified_freeze()` → `launch_validate()` → 同一 `LaunchValidatedFreeze` を `gate_check()` へ渡しています。

   理由: standalone だけを補い、run-block の一度だけ検証という TOCTOU 境界を崩さないため。

3. full validation の正本は [s8b_ratified_freeze.py:2588-2598](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:2588) が呼ぶ [s8b_floor_contract.py:104-226](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_contract.py:104) とします。

   特に reps pin は [167-172](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_contract.py:167)、extime pin は [188-190](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_contract.py:188) です。

   理由: gate-check 内へ第二の部分 validator を追加しないため。

4. A5 fixture は [test_s8b_ratified_freeze.py:458-639](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:458) の production emitter を再利用します。

   - `_build_v2_repo()` [test_s8b_oracle_driver.py:1804-1817](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:1804) に `floor_extime_s` を追加する。
   - `mutate(state)` seam [test_s8b_ratified_freeze.py:512-523](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:512) で、正式生成後の protocol `extime_s` だけを3へ変える。
   - emitter が protocol byte hash と generation record を再構築するため、static `load_ratified_freeze()` は通る。
   - oracle manifest は `_emitter_manifest()` [1820-1830](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:1820) から従来どおり5/5で発行する。
   - standalone gate-check を次の3ケースで固定する:
     - floor=5、active self-load: `allowed=True`
     - floor=3、active self-load: `allowed=False`
     - floor=3、static `ratified` 注入: `allowed=False`

   理由: self-load 経路だけ直して injected `RatifiedFreeze` が bypass になる実装を防ぐため。

5. この fixture は実 repo の v1 freeze 等を読む [test_s8b_ratified_freeze.py:420-435](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:420) ため、次の同一 node を二重台帳へ追加します。

   - [conftest.py:47-88](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/conftest.py:47)
   - [test_real_repo_serialization.py:28-62](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_real_repo_serialization.py:28)

   追加 node:

   `test_s8b_oracle_driver.py::test_v2_standalone_gate_check_requires_full_floor_validation`

   parameter suffix は台帳へ含めません。

## 3. 並列実行の作業分割

裁定順を維持するため、P-A1(b) と P-A5 は直列 barrier にします。並列化するのは B wave 内だけです。

1. 直列 prerequisite: P-A1(b)

   所有ファイル:

   - `layout.py`
   - `s8b_oracle_artifacts.py`
   - `s8b_oracle_exploration.py`
   - `s8b_oracle_manifest.py`
   - `s8b_oracle_report.py`
   - `s8b_oracle_judge.py`
   - `s8b_verdict.py`
   - A1 関連テスト

   `s8b_oracle_report.py` を後続 unit も触るため、A1 commit が完成するまで B wave を開始しません。

2. 並列 unit A: truth-table leaf

   所有ファイル:

   - `s8b_outcome_stage_contract.py`
   - `test_s8b_outcome_stage_contract.py`

   凍結する API:

   - `StageEvidence`
   - `OUTCOMES`
   - `PIPELINE_STAGES`
   - `matches()`

3. 並列 unit B: report consumer

   所有ファイル:

   - `s8b_oracle_report.py`
   - `test_s8b_oracle_report.py`

   作業:

   - P-B5 の leaf 配線
   - P-B6
   - P-A2

   unit A の上記 API を事前合意し、別 worktree で実装します。merge 順は A → B とします。

4. 直列 post-barrier: P-A5 と文書

   所有ファイル:

   - `s8b_oracle_driver.py`
   - `test_s8b_oracle_driver.py`
   - real-repo 二重台帳
   - `phase3.md`
   - `decisions.md`
   - `worklog.md`

   理由: A5 は production file 競合こそありませんが、裁定上 B wave の受入後に統合する必要があるためです。

文書と mutation 実測結果は統合担当だけが編集し、並列 branch 間の競合と未実測 KILL 数の先書きを避けます。

## 4. 変異テスト事前登録

| ID | 予定する1行変異 | 赤くなるテスト |
|---|---|---|
| M1 | exploration path の `os.path.join(root, "exploration", "campaigns", cid)` から `"exploration"` を削除 | `test_exploration_package_uses_disjoint_namespace_schema_and_accepts_three_by_three_hint` |
| M2 | exploration builder の schema を official manifest schema に置換 | 同上、および `test_official_loaders_reject_exploration_schema_for_all_roles` |
| M3 | `write_manifest()` の `OfficialManifest` exact type guard を `Mapping` に緩和 | `test_write_manifest_rejects_exploration_artifact_type` |
| M4 | report の `type(manifest) is OfficialManifest` を `isinstance(manifest, Mapping)` に緩和 | `test_report_rejects_raw_and_exploration_manifest_types` |
| M5 | judge の `OfficialObservations` type guard を削除 | `test_judge_rejects_raw_and_exploration_observation_types` |
| M6 | combined verdict の `OfficialVerdict` type guard を削除 | `test_judge_combined_rejects_raw_and_exploration_oracle_types` |
| M7 | build-failed table の `legacy_verify="missing"` を `"pass"` に変更 | `test_impossible_declared_outcome_histories_are_protocol_violations[build-failed-with-verify]` |
| M8 | timeout table の `bench_done=0` を `1` に変更 | `test_impossible_declared_outcome_histories_are_protocol_violations[timeout-with-bench]` |
| M9 | s2 frontier の abort tag を `s2` から wildcard/`None` に緩和 | `test_abort_workload_tag_must_match_verify_frontier` |
| M10 | report の `_outcome_stage_contract.matches(...)` を `True` に置換 | `test_report_reads_outcome_stage_contract_leaf` |
| M11 | 全-record payload guard から1 stageを除外、または bench の安全射影を直接 `.get()` に戻す | `test_non_mapping_pipeline_payload_is_row_level_protocol_violation` と `test_cli_non_mapping_pipeline_payload_emits_observation` |
| M12 | `len(raw_values) != expected_reps` 検査を削除 | `test_committed_bench_requires_exact_manifest_reps[4]` |
| M13 | `!=` を `<` に変更して過剰件数を許す | `test_committed_bench_requires_exact_manifest_reps[6]` |
| M14 | `expected_reps = run_contract["reps"]` を literal `5` に置換 | `test_rep_count_reads_manifest_run_contract_not_literal` |
| M15 | gate-check の `launch_validate(candidate, root)` を `candidate` の直接利用に置換 | `test_v2_standalone_gate_check_requires_full_floor_validation` の floor=3 二ケース |

完了条件は15/15 KILLEDです。survivor があれば完了記録を書かず、テストまたは設計を修正します。

## 5. 追加・更新するテスト

| テストファイル | テスト名 | 正負 | 固定する契約 |
|---|---|---:|---|
| 新規 `test_s8b_oracle_artifacts.py` | `test_exploration_package_uses_disjoint_namespace_schema_and_accepts_three_by_three_hint` | 正 | 3/3探索、exact schema、official と disjoint な path |
| 同上 | `test_exploration_package_rejects_invalid_slug_hint_and_role` | 負 | traversal、bool/0、未知 role を fail-closed |
| 同上 | `test_official_loaders_reject_exploration_schema_for_all_roles` | 負 | manifest/observations/verdict loader の交差受理禁止 |
| 同上 | `test_artifact_contract_import_loads_no_other_campaign_module` | 正 | artifact 契約の leaf 性 |
| `test_s8b_oracle_manifest.py` | 既存 `test_write_is_create_only_and_valid_manifest_verifies` を拡張 | 正 | build と verified document が official type |
| 同上 | `test_write_manifest_rejects_exploration_artifact_type` | 負 | exploration を official writer で封印不可 |
| `test_s8b_oracle_report.py` | `test_report_rejects_raw_and_exploration_manifest_types` | 負 | direct API の exact type gate |
| 同上 | `test_report_cli_rejects_exploration_manifest_without_output` | 負 | rc=2、official output 不生成 |
| 同上 | `test_staged_legacy_v1_without_run_contract_remains_accepted` | 正 | P-A1(a) を先取りしない legacy 互換 |
| 新規 `test_s8b_outcome_stage_contract.py` | `test_outcome_stage_truth_table_matches_independent_golden` | 正 | 上記 truth-table の完全一致 |
| 同上 | `test_leaf_import_loads_no_other_campaign_module` | 正 | stdlib-only leaf |
| `test_s8b_oracle_report.py` | `test_report_reads_outcome_stage_contract_leaf` | 負 | literal 複製でなく module-qualified 配線 |
| 同上 | `test_impossible_declared_outcome_histories_are_protocol_violations` | 負 | 必須2例。WAL物理順は正しくして truth-table だけを攻撃 |
| 同上 | `test_abort_workload_tag_must_match_verify_frontier` | 負 | legacy/s2 frontier と abort tag の一致 |
| 同上 | `test_non_mapping_pipeline_payload_is_row_level_protocol_violation` | 負 | 全6 stageを parametrize、truthy list payload を使用 |
| 同上 | `test_cli_non_mapping_pipeline_payload_emits_observation` | 負 | CLI全落ちでなく row-level protocol_violation |
| 同上 | `test_committed_bench_requires_exact_manifest_reps` | 負 | tps 4件・6件を拒否し `bench_values=[]` |
| 同上 | `test_rep_count_reads_manifest_run_contract_not_literal` | 負 | manifest reps=4 / tps=5 が不一致になる |
| `test_s8b_oracle_judge.py` | `test_judge_rejects_raw_and_exploration_observation_types` | 負 | raw/exploration から official verdict を作らない |
| 同上 | `test_judge_cli_rejects_exploration_input_without_output` | 負 | rc=2、出力なし |
| `test_s8b_verdict.py` | `test_judge_combined_rejects_raw_and_exploration_oracle_types` | 負 | combined verdict の型境界 |
| 同上 | `test_cli_rejects_exploration_oracle_without_output` | 負 | rc=2、combined output なし |
| `test_s8b_oracle_driver.py` | `test_v2_standalone_gate_check_requires_full_floor_validation` | 正負 | floor=5 正例、floor=3 self-load/injected 負例 |

既存 fixture への変更は次のとおりです。

- report の `_trial()` 既定 tps [test_s8b_oracle_report.py:152-213](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_report.py:152) を5値へ変更する。
- 既存の committed 正例 [260-276](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_report.py:260)、[646-665](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_report.py:646)、[790-896](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_report.py:790) の明示2値と期待配列も5値へ更新する。
- judge の `_observations()` と非対称 helper は `OfficialObservations` を返し、正常 bench 配列も5値にする。
- verdict の `make_oracle()` は `OfficialVerdict` を返す。
- 内部構造を壊す既存テストは official 型を維持したまま nested field を変更する。型拒否を試すテストだけ `dict(...)` で raw 化する。
- JSON CLI テストは既存 JSON bytes を維持し、role-specific loader が runtime 型を復元することを検査する。
- official path `output/campaigns/...` と既存 schema version は変更しないため、既存保存 fixture の移動は不要。

なお `wal.log()` は falsy payload を `{}` に変える [wal.py:63-69](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/wal.py:63) ため、B6 負例には `[]` ではなく `["not-a-mapping"]` のような truthy 非 Mapping を使います。

## 6. 文書記録方針

1. [docs/phase3.md:455-479](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:455) の「裁定・完了記録」に次の形式で1項追加します。

   ```text
   - **(完了 YYYY-MM-DD) oracle 後処理裁定パッケージ
     P-A1(b)/P-B5/P-B6/P-A2/P-A5**
     (D64 残余、worklog 2026-07-20 (2)(3)、D65) —
     namespace/schema/type 境界、段階 truth-table、全 stage payload guard、
     exact reps 証拠、standalone launch validation の実装要旨。
     受入 = 対象テスト + 全走 + 変異 15/15 KILLED。
     P-A1(a) は未実装で D65 の段階導入条件へ残す。
   ```

   既に裁定済みの D64 残余なので、新しい見送り B-ID は発行しません。

2. [docs/decisions.md:2409-2441](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/decisions.md:2409) の D64 は履歴として変更せず、現行 EOF [2442](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/decisions.md:2442) に D65 を追加します。

   D65 に記録する内容:

   - artifact 型は JSON 互換 marker であり provenance 証明ではない
   - official namespace は不変、探索は `output/exploration/campaigns/...`
   - exploration exact schema と3/3が validator 対象外であること
   - official consumer の exact type gate
   - truth-table を reason closure とは別 leaf にした理由
   - A2 を runner でなく report 証拠検査に置いた理由
   - A5 は部分 validator でなく `launch_validate` を再利用すること
   - P-A1(a) の段階導入と残存リスク
   - 研究結果・実測値への影響なし

3. [docs/worklog.md:945-979](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/worklog.md:945) の裁定を参照する完了 entry を追加します。

   - 実装 commit
   - 対象/全走結果
   - mutation 15本の実測
   - real-repo 二重台帳追加
   - 「計測なし・公式 artifact 発効なし」
   - P-A1(a) が次段であること

4. 現在の active handoff は完了時に worklog / decisions / phase3 へ吸収し、repo の handoff 運用規則に従って終了処理します。

## 7. P-A1(a) 段階導入の設計判断ドラフト

D65 には次を、未実装の将来方針として記録します。

> **P-A1(a) の段階導入:** 本 wave は Stage 0 とし、探索 artifact を別 namespace・別 schema・別 runtime 型に隔離する。official manifest v1 と `run_contract` 欠落 legacy の軽量受理は維持するため、この段階は provenance 検証を保証しない。
>
> **Stage 1 — verified manifest cut-in:** 別途ユーザー承認後、report の official API は `OfficialManifest` でなく `VerifiedManifest` のみ受理する。CLI は active ratified freeze を解決して `launch_validate` を通し、その同一 freeze document/sha256 を `verify_manifest` へ渡す。raw Mapping・単なる official schema 分類器から report へ入る経路は廃止する。
>
> **Stage 2 — upstream identity の連鎖:** observations は verified manifest SHA-256 と active generation/freeze SHA-256 を同一 verified object から記録する。judge は caller-supplied verified upstream identity と一致する observations だけを `VerifiedObservations` へ昇格し、`VerifiedVerdict` を発行する。combined verdict は `VerifiedVerdict` と caller が保持する `VerifiedManifest` / active generation identity の完全一致を要求し、非空文字列の転記だけでは受理しない。
>
> **Stage 3 — legacy cutover:** 保存済み v1 artifact の棚卸しと移行手順を承認後、report の `_receipt_expectations()` にある `run_contract` 欠落時の `None` 分岐を削除し、official CLI の v1/raw loader を廃止する。旧 artifact は official judge へ流せる `--allow-legacy` や `mode=exploration` を設けず、非公式の inspection/migration 経路からのみ閲覧可能にする。
>
> **cutover acceptance:** `run_contract` 欠落、raw dict、exploration schema、別 manifest hash への差替え、別 active generation の verdict、旧 v1 artifact がすべて official chain の各入口で拒否されることを負例で固定する。
>
> **Stage 0 の残存リスク:** 呼出側が探索 payload を取り出し、official schema に再包装して official factory を明示的に呼べば型マーカーを偽装できる。この wave が閉じるのは誤混入と正規探索 producer からの交差受理であり、検証済み provenance の保証は Stage 1〜3 の責務である。

## 8. 受入・完了検査

実装後は次の順で実行します。

1. 新規・変更対象テスト

   ```bash
   python3 -m pytest -q \
     orchestrator/tests/test_s8b_oracle_artifacts.py \
     orchestrator/tests/test_s8b_oracle_manifest.py \
     orchestrator/tests/test_s8b_outcome_stage_contract.py \
     orchestrator/tests/test_s8b_oracle_report.py \
     orchestrator/tests/test_s8b_oracle_judge.py \
     orchestrator/tests/test_s8b_verdict.py \
     orchestrator/tests/test_s8b_oracle_driver.py \
     orchestrator/tests/test_real_repo_serialization.py
   ```

2. 変異15本を実測し、15/15 KILLED を確認

3. repo 全走

   ```bash
   python3 tools/run_tests.py
   ```

4. 必須静的検査

   ```bash
   python3 tools/check_codex_agents.py
   python3 tools/check_docs.py
   ```

5. 実装・phase 完了記録・二重台帳を同一 commit に含める

6. commit 後

   ```bash
   python3 tools/check_ai_provenance.py
   ```

テスト・mutation・文書検査のいずれかが未完なら、phase3 の完了項は追加しません。

## 9. Scope 外として実装せず報告する事項

- P-A1(a) の `verify_manifest()` 必須化、manifest hash 再束縛、legacy 廃止は本 wave では実装しません。現行 legacy branch は [s8b_oracle_report.py:524-544](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:524) です。
- judge が manifest SHA の真正性を検証する変更はしません。現行検査は非空文字列のみです。[s8b_oracle_judge.py:130-135](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_judge.py:130)
- `calibrator/runner.py` の `require_all_reps` 既定は変更しません。
- official validator / driver へ `mode=exploration` や 3/3 bypass を追加しません。
- generic pipeline 全体の探索 runner、既存探索 artifact の移動・migration は実装しません。追加するのは隔離 package 境界までです。
- WAL producer 全体へ payload Mapping 強制を追加しません。P-B6 は official report consumer の row-level 防壁です。
- standalone `verify_floor_artifact()` の protocol 射影には extime が含まれていません。[s8b_floor_contract.py:56-64](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_contract.py:56)、[s8b_floor_stats.py:403-411](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_stats.py:403) ただし本 scope は gate-check で `launch_validate` を必須化するため、この低位 API の schema 拡張は行いません。
- artifact marker の深い不変化、forge-proof 化、署名・暗号学的 attestation は実装しません。
- 公式計測、freeze 再発行、artifact 発効、push は行いません。
tokens used
```

## 敵対相談 C-A (正しさ境界) 出力 (逐語。プロンプト = brief 同梱プラン + レンズ、job 記録)

```
基準 HEAD `58934ae` を read-only で確認しました。結論は「このまま実装開始すべきでない」です。high 4件、medium 6件あります。

## 1. high — schema 欠落 legacy 分岐が型隔離を実質的に洗浄する

壊れ方: schema なしの探索 payload を `load_official_manifest()` に渡すだけで `OfficialManifest` へ昇格します。report の軽量検査は `campaign_ids` / `schedule` / `allowed_excluded_reasons` 等しか要求せず、`run_contract` が欠ければ receipt 検査も消えます。そのため、対応 WAL を用意すれば CLI/direct API の双方で `OfficialObservations → OfficialVerdict → combined verdict` まで到達できます。official schema への再包装すら不要です。

さらに、昇格後は `write_manifest()` の exact-type guard も通ります。現行 writer は構造再検証をせず、その点はプランでも変わりません。

根拠:

- report の manifest 検査は部分的: [s8b_oracle_report.py:69](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:69)
- legacy は receipt 検査なし: [s8b_oracle_report.py:524](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:524)
- writer は Mapping 確認だけ: [s8b_oracle_manifest.py:751](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:751)
- judge の manifest identity 検査は非空文字列だけ: [s8b_oracle_judge.py:130](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_judge.py:130)
- repo の既存調査でも 3×3・schema/run_contract 欠落から determinate verdict まで再現済み: [consultations:110](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-20_b004-experiment-numbers-consultations.md:110)

最小修正案: schema 欠落値を `OfficialManifest` にしないで `LegacyManifest` として分離し、少なくとも official writer では拒否すること。ただし legacy から `OfficialObservations` を発行し続ける限り、未検証探索 payload と真正 legacy は識別不能です。P-A1(a) を実装しないなら、Stage 0 の保証は「完全な exploration envelope の誤投入を拒否するだけ」と明記し、型隔離完了とは記録できません。

## 2. high — namespace は `--output-root` の付け替えだけで一致する

壊れ方: planned exploration path が

`<base>/exploration/campaigns/<id>`

なら、official report に `--output-root <base>/exploration` を渡すと、現行 `campaign_layout()` はまったく同じ path を読みます。symlink すら不要です。探索 WAL に独自 schema/marker もないため、artifact の dict 型分離では WAL 読取りを防げません。

direct API でも、公開 dataclass の `ExplorationCampaignLayout(root=<official root>)` を直接構築できるため、exact layout type は path capability になりません。

根拠:

- official path は渡された root への単純 join: [layout.py:204](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/layout.py:204)
- report はその root から WAL を読む: [s8b_oracle_report.py:573](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:573)
- `--output-root` は任意指定可能: [s8b_oracle_report.py:751](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:751)
- WAL 自体に namespace identity 検査はない: [wal.py:75](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/wal.py:75)

最小修正案: output root に official/exploration の role marker または capability を持たせ、report が role を検査すること。加えて exploration WAL/session に distinct schema marker を記録する。`output_root=<base>/exploration` と symlink alias の負例が必要です。

## 3. high — P-A2 が「5個」ではなく「自己申告 reps 個」に変質している

壊れ方:

- `run_contract.reps=3` + tps 3個が合格
- `reps=4` + tps 4個が合格
- schema-less legacy は `expected_reps=None` となり、1個でも合格
- 巨大な正整数を宣言し、同数の値を与えれば公式扱い

これは裁定済みの「reps=5 は成功測定値5個」と一致しません。プランの M14 は「reps=4 / tps=5」を検査するだけで、「reps=4 / tps=4」の偽緑を殺しません。

根拠:

- official authority は明示的に5: [s8b_experiment_numbers.py:14](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_experiment_numbers.py:14)
- official manifest validator は既に authority と完全一致を要求: [s8b_oracle_manifest.py:364](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:364)
- D64 も両 validator の単一 authority を決定済み: [decisions.md:2419](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/decisions.md:2419)

最小修正案: report の `expected_reps` は常に `_experiment_numbers.APPROVED_REPS` とする。`run_contract` が存在する場合は、その `reps` 自体も authority と一致させる。legacy 欠落時も件数5は免除しない。負例に `3/3`、`4/4`、legacy 4個を追加してください。

## 4. medium — tps 5個でも「成功した実行5回」は証明しない

壊れ方: `run_once()` は既定で subprocess の非ゼロ終了を拒否しません。非ゼロ終了でも parse 可能な metrics を出せば throughput が追加されます。これを5回繰り返すと、report の `len(tps)==5` は通ります。

根拠:

- `strict_returncode=False` が既定: [runner.py:346](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/runner.py:346)
- 非ゼロ拒否は strict 時だけ: [runner.py:371](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/runner.py:371)
- pipeline は `require_all_reps` を渡さない: [pipeline.py:231](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:231)
- tps があればそのまま成功列へ追加: [runner.py:462](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/runner.py:462)

最小修正案: generic 既定は変えず、official oracle driver だけ `require_all_reps=True` を明示する seam を追加するか、rep ごとの return code を WAL に残して report が5件すべて rc=0 を検査すること。「成功」を単に「TPS が parse できた」と定義するなら、その意味を裁定記録へ明記する必要があります。

## 5. medium — truth-table が verify の順序を表現できない

壊れ方: 次の producer 不可能な履歴が、planned `StageEvidence` では committed 正規行と同値です。

`build_start → build_done → s2(pass) → legacy(pass) → bench_done → commit`

現行 report への read-only in-memory 入力でも、tpsを5個にしたまま `status=completed` を確認しました。保存予定の物理順序検査も、両 verify を同じ順位2に置くため検出しません。

根拠:

- producer は passes を legacy から構築: [pipeline.py:380](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:380)
- 実行もその順で直列: [pipeline.py:617](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:617)
- report の両 verify は同順位: [s8b_oracle_report.py:518](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:518)

最小修正案: `StageEvidence` に状態2個ではなく、順序付き `verify_sequence` を持たせること。例: committed は `(("legacy","pass"),("s2","pass"))`、s2-red は `(("legacy","pass"),("s2","red"))`。

## 6. medium — correctness-red の reason 連鎖と workload schema が未検査

壊れ方:

- `verify_done(legacy, certified=False, verdict=non-serializable)`
- `abort(reason=build-error, workload.tag=legacy)`
- `trial-result.outcome=correctness-red`

が通ります。現行 report への in-memory 入力で `status=completed` を確認しました。planned table も red 状態と tag しか見ず、残す outcome 固有検査一覧に correctness-red がありません。

また `build-failed` の abort payload を `{"reason":"build-error","workload":["malformed"]}` としても、top-level は Mapping、抽出 tag は `None` になり、表の `None` と一致します。B6 は nested workload を検査しません。

根拠:

- producer は verify verdict を WAL に記録: [pipeline.py:540](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:540)
- 同じ verdict を abort reason にする: [pipeline.py:555](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:555)
- workload は producer が exact object として追加: [pipeline.py:417](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:417)
- 現行 correctness-red 検査は red/terminal 数だけ: [s8b_oracle_report.py:439](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:439)

最小修正案: correctness-red では sole red `verify_done.verdict == abort.reason == abort.verify.verdict` を要求する。abort workload は `ABSENT / INVALID / legacy / s2` の4状態にし、`None` へ畳まない。

## 7. medium — 正当な prepare retry が report で protocol_violation になる

壊れ方: attempt 1 の transient prepare failure は producer が

`trial-start(1) → retry(attempt=2) → trial-start(2) → ... → trial-result(2)`

を発行します。report は最初の window に trial-result がないため protocol_violation とし、その後 attempt 2 が成功しても「過去 attempt が invalid」として最終行を protocol_violation にします。P-B5 の terminal outcome tableを追加しても直りません。

根拠:

- producer の正規 retry: [s8b_oracle_driver.py:1012](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:1012)、[s8b_oracle_driver.py:1106](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:1106)
- 既存テストもこの順序を正規形として固定: [test_s8b_oracle_driver.py:1129](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:1129)
- report は trial-start ごとに window 化: [s8b_oracle_report.py:221](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:221)
- 過去 invalid attempt が後続成功を汚染: [s8b_oracle_report.py:687](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:687)

最小修正案: outcome table の前に attempt lifecycle を閉表化し、「pipeline/trial-result なし、retry 1件、次 attempt と番号一致」の window を正当な retried attempt として扱うテストを追加する。

## 8. high — `launch_validated` 注入が P-A5 を完全に迂回する

壊れ方: プランは `launch_validated` が渡されれば無条件再利用します。しかし `LaunchValidatedFreeze` は公開 dataclass で、repo のテスト自身が直接 constructor を使用しています。floor=3 の static `RatifiedFreeze` を手で `LaunchValidatedFreeze` に包み、standalone `gate_check()` へ渡すと `launch_validate()` は呼ばれません。

CLI にはこの注入引数がないため CLI は安全ですが、direct API の「full validation 必須」は成立しません。exact type guard を足しても公開 constructor なので解決しません。

根拠:

- 現行 gate も注入時は即再利用: [s8b_oracle_driver.py:199](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:199)
- active としても同じ injected object を使用: [s8b_oracle_driver.py:228](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:228)
- public dataclass: [s8b_ratified_freeze.py:752](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:752)
- 実際に直接構築できる既存 helper: [test_s8b_oracle_driver.py:267](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:267)

最小修正案: public standalone `gate_check()` から `launch_validated` 引数を外し、必ず自己 load/static ratified validation を行わせる。run-block 専用に private `_gate_check_validated()` を分け、production caller が run-block だけであることを静的テストで固定する。

## 9. medium — floor=3 負例 fixture が extime pin を単独で検査していない

壊れ方: 提案どおり `mutate(state)` で protocol の `extime_s` だけを3にすると、新 protocol bytes と generation record hash は更新されますが、既に発行済みの cert / manifest / journal / result の `protocol_sha256` や extime mirror は旧値のままです。

したがって extime pin を削除しても、後続の protocol hash chain/mirror 検査で `allowed=False` のままです。A5 テストと M15 は「launch_validate が呼ばれた」ことは検査しますが、「full validator の extime pin が効いた」ことを保証しません。

根拠:

- mutate は実測後に実行: [test_s8b_ratified_freeze.py:512](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:512)
- protocol だけ再直列化: [test_s8b_ratified_freeze.py:523](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:523)
- generation は新 protocol hash を束縛: [test_s8b_ratified_freeze.py:580](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:580)
- 後段にも独立な protocol hash-chain 検査がある: [s8b_ratified_freeze.py:2709](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:2709)

最小修正案: 少なくとも refusal が `floor protocol full validation` の `extime_s` pin 由来であることを assert する。さらに extime pin 行を削除する mutation を事前登録するのが確実です。

## 10. medium — role loader の手前で duplicate key が last-wins に潰れる

壊れ方: report CLI は plain `json.loads()` 後に loader を呼ぶ計画です。例えば同じ object 内に exploration schema と official schema の `schema_version` を重複させると、Python は後勝ちで1個に畳み、official loader は曖昧な入力を Official 型へ昇格します。

repo には既に重複キー・NaN を拒否する strict manifest loader があるのに、この境界では使われません。

根拠:

- report CLI は plain `json.loads`: [s8b_oracle_report.py:758](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:758)
- judge CLI も同様: [s8b_oracle_judge.py:280](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_judge.py:280)
- 正しい strict parser は既に存在: [s8b_oracle_manifest.py:105](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:105)

最小修正案: role-specific loader が Mapping ではなく path/bytes を受け取り、duplicate key・非有限定数拒否を含む strict parse まで所有する。全3 role に duplicate `schema_version` の負例を追加する。

## 穴を確認しなかった点

- truth-table の10個の正規 stage 状態自体は official producer と一致します。correctness-red の `bench_done=0` も、oracle driver が `screening=None` を固定しているため正しいです。[s8b_oracle_driver.py:1068](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:1068)
- timeout と verify-inconclusive が同じ stage 形になること自体は妥当です。reason 集合は分離され、全 verify 途中 abort に workload tag が実際に付与されます。[s8b_abort_reason_contract.py:11](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_abort_reason_contract.py:11)
- P-B6 は、提案どおり build/bench/abort の全 `.get()` を安全射影へ統一すれば、top-level 非 Mapping に関する追加クラッシュ経路は見つかりませんでした。`_verify_state()` は既に Mapping guard を持ちます。[s8b_oracle_report.py:306](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:306)
- `launch_validated` 注入を除けば、self-load と injected static `RatifiedFreeze` は提案順序で `launch_validate()` を一度通り、例外も refusal へ倒れます。run-block 本線も現状一度だけです。[s8b_oracle_driver.py:782](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:782)
- reps の bool/0 拒否、4件だけでなく6件も拒否する all-or-nothing 射影は妥当です。問題は比較対象を自己申告値にした点と、process 成功性を数えられない点です。
tokens used
277,038
基準 HEAD `58934ae` を read-only で確認しました。結論は「このまま実装開始すべきでない」です。high 4件、medium 6件あります。

## 1. high — schema 欠落 legacy 分岐が型隔離を実質的に洗浄する

壊れ方: schema なしの探索 payload を `load_official_manifest()` に渡すだけで `OfficialManifest` へ昇格します。report の軽量検査は `campaign_ids` / `schedule` / `allowed_excluded_reasons` 等しか要求せず、`run_contract` が欠ければ receipt 検査も消えます。そのため、対応 WAL を用意すれば CLI/direct API の双方で `OfficialObservations → OfficialVerdict → combined verdict` まで到達できます。official schema への再包装すら不要です。

さらに、昇格後は `write_manifest()` の exact-type guard も通ります。現行 writer は構造再検証をせず、その点はプランでも変わりません。

根拠:

- report の manifest 検査は部分的: [s8b_oracle_report.py:69](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:69)
- legacy は receipt 検査なし: [s8b_oracle_report.py:524](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:524)
- writer は Mapping 確認だけ: [s8b_oracle_manifest.py:751](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:751)
- judge の manifest identity 検査は非空文字列だけ: [s8b_oracle_judge.py:130](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_judge.py:130)
- repo の既存調査でも 3×3・schema/run_contract 欠落から determinate verdict まで再現済み: [consultations:110](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-20_b004-experiment-numbers-consultations.md:110)

最小修正案: schema 欠落値を `OfficialManifest` にしないで `LegacyManifest` として分離し、少なくとも official writer では拒否すること。ただし legacy から `OfficialObservations` を発行し続ける限り、未検証探索 payload と真正 legacy は識別不能です。P-A1(a) を実装しないなら、Stage 0 の保証は「完全な exploration envelope の誤投入を拒否するだけ」と明記し、型隔離完了とは記録できません。

## 2. high — namespace は `--output-root` の付け替えだけで一致する

壊れ方: planned exploration path が

`<base>/exploration/campaigns/<id>`

なら、official report に `--output-root <base>/exploration` を渡すと、現行 `campaign_layout()` はまったく同じ path を読みます。symlink すら不要です。探索 WAL に独自 schema/marker もないため、artifact の dict 型分離では WAL 読取りを防げません。

direct API でも、公開 dataclass の `ExplorationCampaignLayout(root=<official root>)` を直接構築できるため、exact layout type は path capability になりません。

根拠:

- official path は渡された root への単純 join: [layout.py:204](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/layout.py:204)
- report はその root から WAL を読む: [s8b_oracle_report.py:573](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:573)
- `--output-root` は任意指定可能: [s8b_oracle_report.py:751](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:751)
- WAL 自体に namespace identity 検査はない: [wal.py:75](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/wal.py:75)

最小修正案: output root に official/exploration の role marker または capability を持たせ、report が role を検査すること。加えて exploration WAL/session に distinct schema marker を記録する。`output_root=<base>/exploration` と symlink alias の負例が必要です。

## 3. high — P-A2 が「5個」ではなく「自己申告 reps 個」に変質している

壊れ方:

- `run_contract.reps=3` + tps 3個が合格
- `reps=4` + tps 4個が合格
- schema-less legacy は `expected_reps=None` となり、1個でも合格
- 巨大な正整数を宣言し、同数の値を与えれば公式扱い

これは裁定済みの「reps=5 は成功測定値5個」と一致しません。プランの M14 は「reps=4 / tps=5」を検査するだけで、「reps=4 / tps=4」の偽緑を殺しません。

根拠:

- official authority は明示的に5: [s8b_experiment_numbers.py:14](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_experiment_numbers.py:14)
- official manifest validator は既に authority と完全一致を要求: [s8b_oracle_manifest.py:364](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:364)
- D64 も両 validator の単一 authority を決定済み: [decisions.md:2419](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/decisions.md:2419)

最小修正案: report の `expected_reps` は常に `_experiment_numbers.APPROVED_REPS` とする。`run_contract` が存在する場合は、その `reps` 自体も authority と一致させる。legacy 欠落時も件数5は免除しない。負例に `3/3`、`4/4`、legacy 4個を追加してください。

## 4. medium — tps 5個でも「成功した実行5回」は証明しない

壊れ方: `run_once()` は既定で subprocess の非ゼロ終了を拒否しません。非ゼロ終了でも parse 可能な metrics を出せば throughput が追加されます。これを5回繰り返すと、report の `len(tps)==5` は通ります。

根拠:

- `strict_returncode=False` が既定: [runner.py:346](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/runner.py:346)
- 非ゼロ拒否は strict 時だけ: [runner.py:371](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/runner.py:371)
- pipeline は `require_all_reps` を渡さない: [pipeline.py:231](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:231)
- tps があればそのまま成功列へ追加: [runner.py:462](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/runner.py:462)

最小修正案: generic 既定は変えず、official oracle driver だけ `require_all_reps=True` を明示する seam を追加するか、rep ごとの return code を WAL に残して report が5件すべて rc=0 を検査すること。「成功」を単に「TPS が parse できた」と定義するなら、その意味を裁定記録へ明記する必要があります。

## 5. medium — truth-table が verify の順序を表現できない

壊れ方: 次の producer 不可能な履歴が、planned `StageEvidence` では committed 正規行と同値です。

`build_start → build_done → s2(pass) → legacy(pass) → bench_done → commit`

現行 report への read-only in-memory 入力でも、tpsを5個にしたまま `status=completed` を確認しました。保存予定の物理順序検査も、両 verify を同じ順位2に置くため検出しません。

根拠:

- producer は passes を legacy から構築: [pipeline.py:380](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:380)
- 実行もその順で直列: [pipeline.py:617](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:617)
- report の両 verify は同順位: [s8b_oracle_report.py:518](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:518)

最小修正案: `StageEvidence` に状態2個ではなく、順序付き `verify_sequence` を持たせること。例: committed は `(("legacy","pass"),("s2","pass"))`、s2-red は `(("legacy","pass"),("s2","red"))`。

## 6. medium — correctness-red の reason 連鎖と workload schema が未検査

壊れ方:

- `verify_done(legacy, certified=False, verdict=non-serializable)`
- `abort(reason=build-error, workload.tag=legacy)`
- `trial-result.outcome=correctness-red`

が通ります。現行 report への in-memory 入力で `status=completed` を確認しました。planned table も red 状態と tag しか見ず、残す outcome 固有検査一覧に correctness-red がありません。

また `build-failed` の abort payload を `{"reason":"build-error","workload":["malformed"]}` としても、top-level は Mapping、抽出 tag は `None` になり、表の `None` と一致します。B6 は nested workload を検査しません。

根拠:

- producer は verify verdict を WAL に記録: [pipeline.py:540](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:540)
- 同じ verdict を abort reason にする: [pipeline.py:555](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:555)
- workload は producer が exact object として追加: [pipeline.py:417](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:417)
- 現行 correctness-red 検査は red/terminal 数だけ: [s8b_oracle_report.py:439](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:439)

最小修正案: correctness-red では sole red `verify_done.verdict == abort.reason == abort.verify.verdict` を要求する。abort workload は `ABSENT / INVALID / legacy / s2` の4状態にし、`None` へ畳まない。

## 7. medium — 正当な prepare retry が report で protocol_violation になる

壊れ方: attempt 1 の transient prepare failure は producer が

`trial-start(1) → retry(attempt=2) → trial-start(2) → ... → trial-result(2)`

を発行します。report は最初の window に trial-result がないため protocol_violation とし、その後 attempt 2 が成功しても「過去 attempt が invalid」として最終行を protocol_violation にします。P-B5 の terminal outcome tableを追加しても直りません。

根拠:

- producer の正規 retry: [s8b_oracle_driver.py:1012](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:1012)、[s8b_oracle_driver.py:1106](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:1106)
- 既存テストもこの順序を正規形として固定: [test_s8b_oracle_driver.py:1129](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:1129)
- report は trial-start ごとに window 化: [s8b_oracle_report.py:221](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:221)
- 過去 invalid attempt が後続成功を汚染: [s8b_oracle_report.py:687](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:687)

最小修正案: outcome table の前に attempt lifecycle を閉表化し、「pipeline/trial-result なし、retry 1件、次 attempt と番号一致」の window を正当な retried attempt として扱うテストを追加する。

## 8. high — `launch_validated` 注入が P-A5 を完全に迂回する

壊れ方: プランは `launch_validated` が渡されれば無条件再利用します。しかし `LaunchValidatedFreeze` は公開 dataclass で、repo のテスト自身が直接 constructor を使用しています。floor=3 の static `RatifiedFreeze` を手で `LaunchValidatedFreeze` に包み、standalone `gate_check()` へ渡すと `launch_validate()` は呼ばれません。

CLI にはこの注入引数がないため CLI は安全ですが、direct API の「full validation 必須」は成立しません。exact type guard を足しても公開 constructor なので解決しません。

根拠:

- 現行 gate も注入時は即再利用: [s8b_oracle_driver.py:199](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:199)
- active としても同じ injected object を使用: [s8b_oracle_driver.py:228](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:228)
- public dataclass: [s8b_ratified_freeze.py:752](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:752)
- 実際に直接構築できる既存 helper: [test_s8b_oracle_driver.py:267](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:267)

最小修正案: public standalone `gate_check()` から `launch_validated` 引数を外し、必ず自己 load/static ratified validation を行わせる。run-block 専用に private `_gate_check_validated()` を分け、production caller が run-block だけであることを静的テストで固定する。

## 9. medium — floor=3 負例 fixture が extime pin を単独で検査していない

壊れ方: 提案どおり `mutate(state)` で protocol の `extime_s` だけを3にすると、新 protocol bytes と generation record hash は更新されますが、既に発行済みの cert / manifest / journal / result の `protocol_sha256` や extime mirror は旧値のままです。

したがって extime pin を削除しても、後続の protocol hash chain/mirror 検査で `allowed=False` のままです。A5 テストと M15 は「launch_validate が呼ばれた」ことは検査しますが、「full validator の extime pin が効いた」ことを保証しません。

根拠:

- mutate は実測後に実行: [test_s8b_ratified_freeze.py:512](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:512)
- protocol だけ再直列化: [test_s8b_ratified_freeze.py:523](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:523)
- generation は新 protocol hash を束縛: [test_s8b_ratified_freeze.py:580](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:580)
- 後段にも独立な protocol hash-chain 検査がある: [s8b_ratified_freeze.py:2709](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:2709)

最小修正案: 少なくとも refusal が `floor protocol full validation` の `extime_s` pin 由来であることを assert する。さらに extime pin 行を削除する mutation を事前登録するのが確実です。

## 10. medium — role loader の手前で duplicate key が last-wins に潰れる

壊れ方: report CLI は plain `json.loads()` 後に loader を呼ぶ計画です。例えば同じ object 内に exploration schema と official schema の `schema_version` を重複させると、Python は後勝ちで1個に畳み、official loader は曖昧な入力を Official 型へ昇格します。

repo には既に重複キー・NaN を拒否する strict manifest loader があるのに、この境界では使われません。

根拠:

- report CLI は plain `json.loads`: [s8b_oracle_report.py:758](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:758)
- judge CLI も同様: [s8b_oracle_judge.py:280](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_judge.py:280)
- 正しい strict parser は既に存在: [s8b_oracle_manifest.py:105](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:105)

最小修正案: role-specific loader が Mapping ではなく path/bytes を受け取り、duplicate key・非有限定数拒否を含む strict parse まで所有する。全3 role に duplicate `schema_version` の負例を追加する。

## 穴を確認しなかった点

- truth-table の10個の正規 stage 状態自体は official producer と一致します。correctness-red の `bench_done=0` も、oracle driver が `screening=None` を固定しているため正しいです。[s8b_oracle_driver.py:1068](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:1068)
- timeout と verify-inconclusive が同じ stage 形になること自体は妥当です。reason 集合は分離され、全 verify 途中 abort に workload tag が実際に付与されます。[s8b_abort_reason_contract.py:11](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_abort_reason_contract.py:11)
- P-B6 は、提案どおり build/bench/abort の全 `.get()` を安全射影へ統一すれば、top-level 非 Mapping に関する追加クラッシュ経路は見つかりませんでした。`_verify_state()` は既に Mapping guard を持ちます。[s8b_oracle_report.py:306](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:306)
- `launch_validated` 注入を除けば、self-load と injected static `RatifiedFreeze` は提案順序で `launch_validate()` を一度通り、例外も refusal へ倒れます。run-block 本線も現状一度だけです。[s8b_oracle_driver.py:782](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:782)
- reps の bool/0 拒否、4件だけでなく6件も拒否する all-or-nothing 射影は妥当です。問題は比較対象を自己申告値にした点と、process 成功性を数えられない点です。
```

## 敵対相談 C-B (整合・実効性) 出力 (逐語)

```
## 結論

基準 commit `58934ae8ad099205d76420c6e608269cb39d1dee` を実読した結果、このプランは現状 **NO-GO** です。特に P-A2、P-A1(b)、P-B6、P-B5 に裁定未達の high 所見があります。

## 所見

1. **high — P-A2 の件数 authority が未検証 manifest に逆戻りしている**

壊れ方: `load_official_manifest()` は schema 分類器に留まるため、`run_contract.reps=3` の v1 JSONも `OfficialManifest` になります。WAL の `tps` が3件なら、プランどおり `len==manifest.reps` で通り、3/3探索値を公式 row にできます。また `run_contract` 欠落 legacy は `expected_reps=None` なので、2件でも無検査です。judge は現在、非空有限配列なら件数を問わず eligible にします。

根拠: approved authority は [s8b_experiment_numbers.py:14](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_experiment_numbers.py:14)、full manifest validator はそれを参照して5を要求します [s8b_oracle_manifest.py:364](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:364)。一方、report の軽量検査は現在 run contract を見ません [s8b_oracle_report.py:69](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:69)。legacy 分岐は欠落を許します [s8b_oracle_report.py:524](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:524)。judge は非空性だけです [s8b_oracle_judge.py:98](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_judge.py:98)。

最小修正: report は `run_contract.reps == s8b_experiment_numbers.APPROVED_REPS` と `len(tps)==APPROVED_REPS` の両方を要求する。legacy も受理自体は維持しつつ、件数期待値は5にする。3/3、legacy 4件、v1 reps=4/tps=4 の負例を追加する。M14 は後述のとおり逆向きなので差し替える。

2. **high — 提案された探索 namespace は `--output-root` の rebasing で公式 namespace と同一になる**

壊れ方:

```text
exploration_campaign_layout(base, cid)
  = base/exploration/campaigns/cid

campaign_layout(output_root=base/exploration, cid)
  = base/exploration/campaigns/cid
```

公式 report の CLI に `--output-root output/exploration` を渡すだけで、探索 WAL と同じ場所を公式 report が読みます。M1 の「同じ base で path が異なる」検査では検出できません。

根拠: `campaign_layout()` は渡された root に無条件で `campaigns/<id>` を足します [layout.py:204](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/layout.py:204)、[layout.py:212](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/layout.py:212)。report は任意の `output_root` から layout を再構築します [s8b_oracle_report.py:573](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:573)、CLI も任意 path を受けます [s8b_oracle_report.py:752](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:752)。

最小修正: namespace root に official/exploration の role marker または capability を持たせ、公式 consumer が exploration marker の root を拒否する。少なくとも `official output_root=base/exploration` の負例を追加する。単なる文字列 path の違いだけでは分離契約になりません。

3. **high — P-B6 guard は campaign-level early return の後なので「全 PIPELINE_STAGES record」にならない**

壊れ方: `trial-start → build_start(payload=list)` の後に campaign-terminal が欠落した WALでは、report は payload を検査せず全 row を `campaign-incomplete` にして返します。campaign-start の異常など `global_issues` がある場合も `_assess_window()` 自体が呼ばれません。

根拠: payload を扱う `_assess_window()` は [s8b_oracle_report.py:327](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:327)。しかし terminal 異常はその前に return します [s8b_oracle_report.py:592](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:592)。global issue 時も window assessment を skip します [s8b_oracle_report.py:655](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:655)。

最小修正: WAL 読取直後に全 pipeline record を一度走査し、window へ帰属できる issue と orphan/global issue に分ける。payload 違反は `campaign-incomplete` より優先して row-level `protocol_violation` にする。terminal 欠落・aborted terminal・global deviation と非 Mapping payload の組合せを追加する。

4. **high — P-B5 の集約 truth-table は verify の物理順を閉じない**

壊れ方: `build_start → build_done → verify_done[s2 pass] → verify_done[legacy pass] → bench → commit` は、表上 `legacy=pass/s2=pass` で committed に一致します。既存の物理順検査でも両 `verify_done` は同じ rank なので通ります。

根拠: producer は legacy を先頭に置き、その後に extra correctness を並べます [pipeline.py:380](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:380)、実行もその順です [pipeline.py:617](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:617)。report の `PIPELINE_ORDER` は全 verify を同じ `2` に潰します [s8b_oracle_report.py:518](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:518)。

最小修正: `StageEvidence` に verify frontier の順序証拠を含めるか、物理順検査で `legacy < s2` を明示する。逆順 committed、逆順 s2-red、s2 の後に legacy が現れる timeout を負例にする。

5. **medium — abort workload tag の `None` が「不存在」と「壊れた値」を同一視する**

壊れ方: build-failed の abort payload が `{"reason":"build-error","workload":[]}` でも、安全射影が tag を `None` にすると表の期待 `None` に一致します。top-level payload は Mapping なのでB6にも引っかからず、reason も閉表内です。

根拠: 正規 producer は tag を付ける場合、必ず `{"workload":{"tag":...}}` を発行します [pipeline.py:417](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:417)。現在の report も nested workload の不正を一部では `None` に潰しています [s8b_oracle_report.py:402](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:402)。

最小修正: `ABSENT` と `INVALID` の sentinel を分けるか、不正 nested workload を独立 issue にする。tagなしを期待する build-failed/bench-failed/binary-mismatch 全てで、list、`{"tag":None}`、余分 key を拒否する。

6. **medium — exploration layout/package は既存 producer に一度も配線されない**

壊れ方: 新 packager は「generic 成果を後から包装」するだけで、元 WAL/report の生成場所を変更しません。現行の公式 driver と generic pipeline caller は引き続き `campaign_layout()` を使います。したがって「探索 WAL・report を別 root に閉じた」という完了主張は、packager 単体テストだけでは成立しません。

根拠: driver は常に公式 layout を作ります [s8b_oracle_driver.py:879](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:879)。pipeline は caller から layout を受けるだけです [pipeline.py:324](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:324)。通常 loop も公式 factory を使います [loop.py:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/loop.py:47)。

最小修正: generic runner 全体を実装範囲に広げなくても、3/3入力から exploration package までの実在する入口を一本配線し、元入力を含め official root に何も生成されない E2E を置く。そこまで行わないなら、完了記録を「包装 utility の追加」に弱める。

7. **medium — 新 leaf が schema/stage の単一 authority になっていない**

壊れ方: プランは manifest の `SCHEMA_VERSION` だけ再輸出すると明記していますが、report、judge、combined verdict の schema literal は残す設計です。producer と loader の値が将来ずれれば、JSON round-trip 後だけ壊れます。同様に、新 leaf に `OUTCOMES/PIPELINE_STAGES` を置いても、report のローカル集合を削除・再輸出する手順がありません。ローカル filter が先に record/outcome を落とせば `matches()` は呼ばれません。

根拠: 現在の重複 literal は [s8b_oracle_report.py:25](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:25)、[s8b_oracle_judge.py:16](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_judge.py:16)、[s8b_verdict.py:112](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_verdict.py:112)。stage/outcome 集合も report 内にあります [s8b_oracle_report.py:27](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:27)。

最小修正: 全 schema 定数を artifact leaf の再輸出にし、stage/outcome は module-qualified 参照へ統一する。D64 と同じく、leaf 参照をローカル literal に戻す変異を追加する。

8. **medium — 既存 positive fixture 6件が新 truth-table と矛盾する**

壊れ方: `_trial()` の通常 timeout/verify-inconclusive は s2 tag を付けますが、`test_terminal_outcomes_accept_closed_abort_reason` は `abort_payload={"reason": reason}` で payload 全体を置換し、tag を消します。新表では timeout 1件と verify-inconclusive 5件が protocol violation になります。プランのfixture更新一覧にはありません。

根拠: override は merge でなく全置換です [test_s8b_oracle_report.py:157](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_report.py:157)。通常形は s2 tag 付きです [test_s8b_oracle_report.py:188](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_report.py:188)。positive test は reason だけを渡します [test_s8b_oracle_report.py:386](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_report.py:386)、[test_s8b_oracle_report.py:418](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_report.py:418)。

最小修正: reason だけを default payload に merge するか、frontier tag も明示する。timeout/verify-inconclusive は legacy frontier と s2 frontier の双方を positive にする。

9. **medium — driver の公式 fixture が reps=5 manifest と2値 WALを生成し続ける**

壊れ方: `_fake_evaluate_factory()` は多数の driver 正例で公式 manifest/WALを生成しますが、bench値は2個です。新 report に渡せば全て protocol violation です。既存 driver テストは report を呼ばないため、全走してもこの producer→consumer 不整合を検出しません。

根拠: manifest は reps=5です [test_s8b_oracle_driver.py:165](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:165)。fake producer は2値です [test_s8b_oracle_driver.py:185](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:185)、[test_s8b_oracle_driver.py:207](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:207)。

最小修正: fake を中央値不変の5値へ変更し、driverが完了した1 campaignをそのまま report に読ませる統合テストを1本追加する。

10. **medium — A5 fixture の floor=5 正例が unrelated known-axes refusal で落ちる**

壊れ方: production-emitter の tmp repo は standalone gate の known-axes source provenance を満たしません。既存 `_run_v2()` はそのため明示的に `s1_known_axes_freeze.verify` をpatchしています。新 standalone testには同じ隔離が記載されていないため、floor=5 の `allowed=True` が成立せず、floor=3も launch validation 以外の refusal で偽赤になります。

根拠: 既存 helper が理由とpatchを明記しています [test_s8b_oracle_driver.py:1849](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:1849)。gate は必ず known-axes verify を呼びます [s8b_oracle_driver.py:247](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:247)。fixture は実 repo の v1/known-axes bytesを読みます [test_s8b_ratified_freeze.py:420](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:420)。

最小修正: standalone testでも既存と同じ orthogonal patch を使い、floor=3 の refusal が1件だけで `v2-execution: launch-validate:` prefixを持つことを assertする。`launch_validate` の呼出し回数と引数 object identity も固定する。

11. **medium — 15 mutation は現状「15個の確定変異」になっていない**

各IDの実効性は次のとおりです。

| ID | 判定 | 条件・問題 |
|---|---|---|
| M1 | 有効だが不足 | exact path assert なら殺せる。ただし finding 2 の rebase alias は検出不能 |
| M2 | 有効 | exact exploration schema assert で殺せる |
| M3 | 有効 | exploration object の write 成功を許すため例外期待が落ちる |
| M4 | 条件付き | explorationだけでは軽量manifest検査に落ちてマスクされる。有効な `dict(official_manifest)` が必須 |
| M5 | 条件付き | 有効な raw observations を使うこと。壊れた explorationだけでは別検査でマスクされる |
| M6 | 条件付き | 有効な raw verdict を使うこと |
| M7 | 条件付き有効 | verify付き build-failed が他issueなしで mutant時だけ completedになる必要あり |
| M8 | 条件付き有効 | benchは5値、abort tag/reason/物理順を全て正しくしないと別検査でマスク |
| M9 | 無効な事前登録 | 「wildcard/None」は別変異。wrong=`legacy` だけでは `s2→None` mutantが生存する |
| M10 | 設計可能 | 正常rowで `matches` をmonkeypatchしてFalseにし、呼出し回数とprotocol violationをassertすれば殺せる。テスト名やsource grepだけでは不足 |
| M11 | 無効な事前登録 | 「1 stage除外」と「benchを直接.get」は別変異。statusだけでは既存reason検査にマスクされる |
| M12 | 有効 | 他条件を満たす4値負例なら殺せる |
| M13 | 有効 | 他条件を満たす6値負例なら殺せる |
| M14 | 機械的には有効だが契約が逆 | 正しい approved authority 実装を殺し、未検証manifestのrepsを信頼する実装を要求している |
| M15 | 不十分 | `LaunchValidatedFreeze` を `RatifiedFreeze` に置換すると型/属性エラーで死ぬだけになり得る。さらに finding 10 のrefusalでマスクされる |

根拠として、非 Mapping payload は既存 reason 検査でも赤くなり得ます [s8b_oracle_report.py:398](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:398)、[s8b_oracle_report.py:446](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:446)。したがって M11 は専用issue文字列までassertしないと恒真化します。

最小修正: M9/M11を個別diffへ分割し、M14を「approved authority参照をmanifest宣言へ置換」に変更する。M15は `LaunchValidatedFreeze` 風 wrapper を返す機能的 bypass mutant にする。実測記録には各 mutant の exact diff を残す。

12. **medium — exact runtime 型が二重 import namespace で分裂する**

壊れ方: repo は `campaign.*` と `orchestrator.campaign.*` の両方を使います。同じソースでもクラスobjectは別なので、片方で作った `OfficialManifest` をもう片方の report が `type(...) is` で拒否します。実際、現行 `VerifiedPrediction` で両 namespace をimportするとクラス identity は不一致でした。

また `s8b_verdict.py` は direct-execution branch を持ちますが [s8b_verdict.py:64](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_verdict.py:64)、基準commitでは `python3 orchestrator/campaign/s8b_verdict.py --help` が、manifest の absolute `campaign` import [s8b_oracle_manifest.py:16](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:16) により `ModuleNotFoundError` になります。予定された `main()` 単体テストでは検出できません。

最小修正: artifact class を常に一つの canonical module名からimportする。direct CLIも同じ namespaceに寄せ、実 subprocess テストを追加する。`OracleArtifactTypeError` は必ず `TypeError` subclassと明記するか、各CLIのexcept列に明示追加する。現在のCLIは TypeError しか捕捉しません [s8b_oracle_report.py:758](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:758)、[s8b_oracle_judge.py:280](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_judge.py:280)。

13. **medium — `CampaignLayout` 全体のbase抽出は裁定外の広いrefactor**

壊れ方: constructor、dataclass継承、`ensure()` の戻り型・reprなどが変わると、s8b以外の campaign/test へ波及します。探索 sibling を足すために現行 public class を作り替える必要はありません。

根拠: public class本体は [layout.py:164](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/layout.py:164)。pipelineもこの型を公開引数にします [pipeline.py:324](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:324)。非s8bにも直接構築があります [guided.py:55](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/guided.py:55)。

最小修正: `CampaignLayout` はbyte-levelに近い形で維持し、slug helperだけ抽出して siblingを追加する。refactorするなら対象テストに `test_campaign.py`、guided/backoff/direct-comparison系も含める。

14. **low — 新しい意味論 leaf が generator pin の外に出る**

壊れ方: manifest が記録する generator source は materializer/report/judge の3ファイルだけです。新 truth-table/artifact leafのbytesだけを変更しても、report/judgeの記録hashは変わらず、同じ generator pinで意味論が変化します。

根拠: generator key集合は [s8b_oracle_manifest.py:42](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:42)、検査は各単一file hashです [s8b_oracle_manifest.py:377](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:377)、manifestへの格納は [s8b_oracle_manifest.py:715](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:715)。

最小修正: schema/bundle pin拡張がscope外なら、このwaveで無理に実装せずD65の残存リスクに明記する。将来のP-A1(a)で transitive source bundle identityを対象にする。

15. **low — 並列DAGは安全だが過直列化されている**

壊れ方: correctness上の破綻はありませんが、unit Aの新規 truth-table leaf/testはA1の所有fileと交差しません。A5もproduction/test fileが別です。

最小修正: `A1` と `unit A` は並列開始可能。unit Bだけが `A1 report変更 + unit A API` の両方を待つ。A5は実装・fixture作成を並列に進め、裁定順どおり最後にmerge/受入すればよい。現行案の「A→B merge順」は正しいです。

## producer / fixture 追跡で穴がなかった点

以下はrepo-wide検索で確認でき、プランどおりです。

- repo-owned production codeから `build_manifest()` を呼ぶ箇所はなく、現状はtest/library producerのみです。driverはfileを受け、`verify_manifest()` の戻りobjectを使います [s8b_oracle_driver.py:837](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:837)。
- driverはreport/judge/combined verdictを直接呼びません。JSON chainは report CLI [s8b_oracle_report.py:761](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:761)、judge CLI [s8b_oracle_judge.py:283](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_judge.py:283)、verdict CLI [s8b_verdict.py:838](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_verdict.py:838) の3境界です。各境界でrole loaderを通す方針自体は正しいです。
- `s8b_materialization.py` はbinding producer、`s8b_floor_campaign.py` は別schemaのfloor manifestであり、oracle型ゲートの直接波及はありません。
- test_s8b系以外から `build_observations/judge_oracle/judge_combined` を呼ぶ統合テストは見つかりませんでした。保存済みoracle JSON fixtureもありません。非s8b波及の主因は finding 13 のlayout refactorだけです。

## 文書・検収契約で一致していた点

- 基準commitではD64がEOFで、D65は未使用です [decisions.md:2409](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/decisions.md:2409)。
- `tools/check_docs.py` は現状 `違反なし`。D見出し重複とliving docの不存在D参照を検査します [check_docs.py:113](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/check_docs.py:113)、[check_docs.py:156](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/check_docs.py:156)。D65とphase3参照を同一commitに入れる方針は正しいです。
- worklogは85,326 bytesで、rotation閾値100,000 bytes未満です [check_docs.py:71](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/check_docs.py:71)。
- real-repo台帳のnodeはparameter suffixなしが正契約です [conftest.py:44](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/conftest.py:44)。hookも `originalname` でparameter instanceを正規化します [conftest.py:99](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/conftest.py:99)。独立golden側への同一node追加も正しいです [test_real_repo_serialization.py:28](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_real_repo_serialization.py:28)。
- phase3の完了記録形式は既存様式と整合します [phase3.md:455](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:455)。

文書上の最小注意点は二つです。終了時に削除するhandoffは、他の中断handoffではなく `2026-07-20-adjudicated-wave-a1b-b5b6a2-a5.md` と明記してください。運用規則は「自分のfile以外に書かない」「正常終了時に自分のfileを削除」です [handoff/README.md:8](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/README.md:8)、[handoff/README.md:15](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/README.md:15)。またStage 3の「v1 loader廃止」は、現行の正式schema自体がv1 [s8b_oracle_manifest.py:23](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:23) なので、「schema-less/run_contract-less legacyの廃止」なのか「manifest v2へのbump」なのかを分けて記述すべきです。
```

## E1 実行報告 (逐語、diff 部除く)

```
実装完了しました。E1 担当範囲外のファイル、git commit、branch 操作は行っていません。

## 1. 変更ファイル

新規:

- [s8b_oracle_artifacts.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-e1/orchestrator/campaign/s8b_oracle_artifacts.py)
- [s8b_oracle_exploration.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-e1/orchestrator/campaign/s8b_oracle_exploration.py)
- [test_s8b_oracle_artifacts.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-e1/orchestrator/tests/test_s8b_oracle_artifacts.py)

変更:

- [layout.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-e1/orchestrator/campaign/layout.py)
- [s8b_oracle_manifest.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-e1/orchestrator/campaign/s8b_oracle_manifest.py)
- [s8b_oracle_report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-e1/orchestrator/campaign/s8b_oracle_report.py)
- [s8b_oracle_judge.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-e1/orchestrator/campaign/s8b_oracle_judge.py)
- [s8b_verdict.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-e1/orchestrator/campaign/s8b_verdict.py)
- [test_s8b_oracle_manifest.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-e1/orchestrator/tests/test_s8b_oracle_manifest.py)
- [test_s8b_oracle_report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-e1/orchestrator/tests/test_s8b_oracle_report.py)
- [test_s8b_oracle_judge.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-e1/orchestrator/tests/test_s8b_oracle_judge.py)
- [test_s8b_verdict.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-e1/orchestrator/tests/test_s8b_verdict.py)

## 2. 実装結果

- V1: `LegacyManifest` を分離。official writer は `OfficialManifest` exact type のみ受理し、observations に `manifest_kind` を追加。
- V2: exploration root に exact `namespace.json` marker を生成。official report は直接指定と symlink alias の双方を拒否。
- V3: 既存 manifest 数値 pin を維持。E3 所有の report reps 検査には未着手。
- V9: manifest・observations・verdict loader を duplicate key／非有限値拒否のstrict parserへ統一。
- V10: 3秒×3回を包装できる exploration CLI を追加。official campaign rootには生成しない。
- V11: oracle chainとcombined verdictのschema定数をartifact leafから再輸出。
- V13: canonical importを `campaign.s8b_oracle_artifacts` に固定。`OracleArtifactTypeError` は `TypeError` subclass。実 subprocess テストを追加。
- V14: `CampaignLayout` 本体を維持し、slug helperと非継承の `ExplorationCampaignLayout` を追加。
- report／judge／combined verdict に exact runtime type gateを実装。raw dictやexploration型はfail-closed拒否。

## 3. テスト結果

- 指定テスト:
  `python3 -m pytest -q ...test_s8b_oracle_artifacts.py ...test_s8b_verdict.py`
  → **199 passed / 0 failed**
- 関連互換テスト:
  `test_campaign.py`, `test_s8b_materialization.py`, `test_s8b_binding_driftguards.py`, `test_s8b_experiment_numbers.py`, `test_s8b_oracle_driver.py`
  → **211 passed / 0 failed / 11 skipped**
- E1変異 M1〜M6・M17:
  → **7/7 KILLED**
- `python3 -m py_compile ...`
  → passed
- `python3 tools/check_codex_agents.py`
  → passed
- `python3 tools/check_docs.py`
  → passed
- `git diff --check`
  → passed

## 4. 逸脱・未了・発見事項

- scope逸脱なし。E2/E3、driver、truth-table、docs、二重台帳は未編集です。
- 全19変異のうちE1所有7本のみ実測済み。残り12本と全repo走は統合担当の受入事項です。
- `docs/*` 編集禁止に従い、通常のclass 3 handoff/worklog更新は実施していません。
- commit禁止のため `check_ai_provenance.py` は未実行です。
- 指定されたscope外事項（rep rc=0成功性、prepare retry、既存direct-exec問題、generator pin拡張、P-A1(a) provenance強化）は未実装です。
```

## E2 実行報告 (逐語、diff 部除く)

```
実行報告

1. 変更ファイル

新規:

- [s8b_outcome_stage_contract.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-e2/orchestrator/campaign/s8b_outcome_stage_contract.py)
- [test_s8b_outcome_stage_contract.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-e2/orchestrator/tests/test_s8b_outcome_stage_contract.py)

変更:

- [s8b_oracle_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-e2/orchestrator/campaign/s8b_oracle_driver.py)
- [test_s8b_oracle_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-e2/orchestrator/tests/test_s8b_oracle_driver.py)
- [conftest.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-e2/orchestrator/tests/conftest.py)
- [test_real_repo_serialization.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-e2/orchestrator/tests/test_real_repo_serialization.py)

2. 実装結果

- V4/V5: 順序付き `verify_sequence` と4状態の `abort_workload` を持つ immutable `StageEvidence`、完全 truth-table、`matches()` を stdlib-only leaf として実装。
- V7: public `gate_check()` から `launch_validated` を除去。run-block 専用 `_gate_check_validated()` を分離し、production caller が `run_block` のみであることを静的テストで固定。
- V8: standalone v2 gate が self-load／injected `RatifiedFreeze` の双方を `launch_validate()` へ厳密1回渡すよう変更。extime=3 は単一の `v2-execution: launch-validate:` refusal で拒否。
- V12: fake bench を5値化し、driver completed WALをreport CLIが5測定値として受理する統合テストを追加。
- real-repo nodeを二重台帳へ同一内容で追加。
- M7/M8/M9a/M9b/M15/M16を実測し、6/6 KILLED。

3. テスト結果

- 指定合同コマンド:
  `python3 -m pytest -q orchestrator/tests/test_s8b_outcome_stage_contract.py orchestrator/tests/test_s8b_oracle_driver.py orchestrator/tests/test_s8b_ratified_freeze.py orchestrator/tests/test_real_repo_serialization.py`
  - 107 passed / 0 failed / 1 skipped
- 追加回帰:
  `python3 -m pytest -q orchestrator/tests/test_s8b_binding_driftguards.py`
  - 9 passed / 0 failed
- 静的検査:
  - `python3 tools/check_codex_agents.py` — passed
  - `python3 tools/check_docs.py` — passed
  - `git diff --check` — passed

4. 逸脱・未了・発見事項

- 担当外ファイル、`docs/*`、git commit／branchは変更していません。
- M16は担当外 production fileを編集せず、隔離プロセス内で関数本文のextime pin行だけを置換してKILLを確認しました。
- E1/E3、全19 mutation、repo全走、文書完了記録は統合担当の範囲です。
- 指定済みscope外事項（repのrc=0成功性、prepare retry偽陽性、verdict直接実行問題、generator pin拡張）は未実装です。
```

## E3 実行報告 (逐語、diff 部除く)

```
実装完了しました。commit / branch 操作は行っていません。

1. 変更ファイル

- 変更: [s8b_oracle_report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-e3/orchestrator/campaign/s8b_oracle_report.py:87)
- 変更: [test_s8b_oracle_report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-e3/orchestrator/tests/test_s8b_oracle_report.py:340)

2. 実装結果

- V3: `APPROVED_REPS` を唯一の件数 authority とし、3/4/6件および legacy 4件を拒否。宣言 reps 不一致も protocol issue 化。
- V4/V5: 順序付き `verify_sequence` と4状態 abort workload を `StageEvidence` へ射影。truth-table を一度だけ呼び、reason 閉表・correctness-red の reason 連鎖を独立検査。
- V6: 全6 pipeline stage の payload を WAL 読取直後に検査。terminal 欠落時にも該当行の `protocol_violation` を優先。
- V11: `OUTCOMES` / `PIPELINE_STAGES` を leaf から再輸出し、consumer は module-qualified 参照。
- V12: abort fixture override を workload tag 保持型へ修正。timeout / verify-inconclusive の legacy・s2 両 frontier 正例を追加。
- M7〜M14/M18 に対応する killer テストを追加。

3. テスト結果

- `python3 -m pytest -q orchestrator/tests/test_s8b_oracle_report.py`
  - 99 passed / 0 failed
- 指定3スイート:
  - `python3 -m pytest -q orchestrator/tests/test_s8b_oracle_report.py orchestrator/tests/test_s8b_outcome_stage_contract.py orchestrator/tests/test_s8b_oracle_driver.py`
  - 160 passed / 0 failed / 1 skipped
- `python3 tools/check_codex_agents.py`: passed
- `python3 tools/check_docs.py`: passed
- `git diff --check`: passed

4. 逸脱・未了・発見事項

- 担当外ファイルの編集、commit、branch 操作なし。
- 19本の実 mutation 実測と repo 全走は統合担当向けの未了事項。E3 の killer テスト実装まで完了。
- scope 外の rep rc=0 成功性、prepare retry、`s8b_verdict` 直接実行問題、generator pin 拡張には未着手です。
```

## レビュー R1 (正しさ・敵対) 出力 (逐語)

```
結論は **NO-GO** です。型境界・truth-table・reps・A5 の本体は概ね裁定どおりですが、namespace 防壁に実際の迂回経路があり、受入証拠もまだ独立監査可能な形で残っていません。

1. severity: high — campaign 子ディレクトリの symlink で exploration WAL を official report に読ませられる

壊れ方:

- `<base>/exploration/campaigns/C` に、official manifest の hash・schedule・binding と整合する探索 WAL を置く。
- marker のない `<base>/official` を作り、`<base>/official/campaigns/C` を上記探索 campaign への symlink にする。
- `output_root=<base>/official` で report を実行する。
- marker 検査は `output_root/namespace.json` しか見ないため通過し、`is_dir()` と `wal.read_records()` は campaign symlink を追う。
- 5 個の有限 tps と正しい stage history があれば `OfficialObservations` → `OfficialVerdict` → combined verdict まで到達できる。

同様に、`output_root` symlink を marker 検査後・campaign path 構築前に差し替える TOCTOU も残ります。`resolve()` した値を捨て、後段で元の path を再利用しているためです。

根拠:

- marker は直下のみ検査: [s8b_oracle_report.py:57](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:57)
- 後段は未解決の `output_root` から layout を再構築: [s8b_oracle_report.py:666](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:666)
- campaign path は単純な join: [layout.py:214](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/layout.py:214)
- WAL open は symlink を追う: [wal.py:75](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/wal.py:75)
- 現テストは `output_root` 自身の symlink alias だけ: [test_s8b_oracle_report.py:458](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_report.py:458)

最小修正案:

- marker 検査から resolved root を返し、その同一 path だけを後段で使う。
- campaign root を `resolve(strict=True)` し、`resolved_output_root / "campaigns"` 配下から外れる場合、または途中 component が symlink の場合は拒否する。
- 強い敵対境界にするなら、最終的には `openat`/dirfd + `O_NOFOLLOW` で検査から WAL open まで固定する。
- `campaigns/C` symlink と検査後の root 差替えを負例に追加する。

2. severity: medium — 巨大 JSON 整数で report と judge がデータ由来 `OverflowError` を漏らす

`10**400` のような JSON 整数は strict parser を通りますが、`float(value)` で `OverflowError` になります。

実行確認:

- `_assess_window(..., tps=[10**400])` → `OverflowError: int too large to convert to float`
- `judge_oracle(OfficialObservations(... bench_values=[10**400]))` → 同じ `OverflowError`

これにより report は row-level `protocol_violation` を生成せず、judge は「typed だが内部構造が壊れた observations を indeterminate にする」という維持対象契約を破ります。

根拠:

- report の変換: [s8b_oracle_report.py:501](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:501)
- report CLI は `OverflowError` を処理しない: [s8b_oracle_report.py:912](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:912)
- judge の同型変換: [s8b_oracle_judge.py:103](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_judge.py:103)

最小修正案:

- 数値を一度だけ安全に float 射影し、`OverflowError`/`ValueError` または非有限なら不正値として扱う helper を report/judge で使う。
- CLI の except に足すだけでは row を失うため不可。
- report は `protocol_violation + bench_values=[]`、judge は `indeterminate` になる巨大整数負例を追加する。

3. severity: medium — 「20/20 KILLED」は現 branch から独立監査不能

20 という数え方自体は、M9a/M9b と M11a/M11b を別 mutant と数えれば整合します。しかし exact diff、killer command、baseline/mutant rc、restore hash は tracked artifact にありません。記録は job tmp の `mutspec.json` と `mutation_gate_wave2.py` を指すだけです。

根拠:

- 20/20 主張と証拠の所在: [handoff:8](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-20-adjudicated-wave-a1b-b5b6a2-a5.md:8)
- harness は一時ファイルで、後で凍結する予定: [handoff:24](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-20-adjudicated-wave-a1b-b5b6a2-a5.md:24)

壊れ方:

- mutant が意図した行でなく setup/import error で赤くなっていても、branch だけでは識別できない。
- exact diff の一意性や復元確認も第三者が再検算できない。
- プランの「各 mutant の exact diff を実測記録に残す」という完了条件をまだ満たさない。

最小修正案:

- per-mutant の exact patch、baseline rc、mutant rc、赤くなった test、失敗要旨、前後 hash を machine-readable artifact として凍結する。
- 特に M15 は「呼出回数 0 による kill」であることをログにも残す。

4. severity: low — 未知 schema を拒否する loader 契約に、生存しうる未登録変異がある

現コードは正しく未知 schema を拒否します。しかし observations/verdict loader のテストは exploration schema と duplicate key だけで、未知 schema の拒否を固定していません。未知 schema の負例は manifest loader にしかありません。

生存しうる具体的変異:

```diff
- if document.get("schema_version") != OFFICIAL_OBSERVATIONS_SCHEMA:
+ if document.get("schema_version") == EXPLORATION_ARTIFACT_SCHEMA:
```

同型を verdict loader に適用しても、現行 loader テストは exploration を拒否するため緑のままです。未知 schema は loader を通り、judge/combined が official marker を付けた indeterminate 出力を生成します。

根拠:

- loader: [s8b_oracle_artifacts.py:121](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_artifacts.py:121)
- exploration と duplicate のみ: [test_s8b_oracle_artifacts.py:86](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_artifacts.py:86)
- unknown/null は manifest 限定: [test_s8b_oracle_artifacts.py:134](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_artifacts.py:134)

最小修正案:

- observations/verdict loader にも `None`、`unknown/v1`、他 role の official schema を拒否する負例を追加する。
- CLI についても rc=2・出力なしを固定する。

5. severity: low — V15/D65 と完了記録は commit range に未実装

`58934ae..HEAD` には docs 差分がなく、`decisions.md` は D64 で終わっています。したがって Stage 0 の限定保証、rep 成功定義、generator pin 外、legacy 廃止と v2 bump の分離はまだ正本化されていません。

根拠:

- 現行末尾は D64: [decisions.md:2409](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/decisions.md:2409)
- worklog は「実装は次セッション」のまま: [worklog.md:968](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/worklog.md:968)
- handoff 自身も `作業中`: [handoff:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-20-adjudicated-wave-a1b-b5b6a2-a5.md:3)

最小修正案:

- 上記 high/medium 修正と再受入後に D65・phase3・worklog・mutation 実測を同一 completion commit に含める。現時点で完了表記は追加しない。

所見ゼロだった主要観点:

- Official/Legacy/Exploration の runtime class は非継承で、report・judge・combined の exact type gate も実在します。
- duplicate key/non-finite strict parse は共通 leaf にあります。
- truth-table は `verify_sequence` の順序、4 状態 abort tag、全 count を完全一致で検査し、report も module-qualified `matches()` を実際に呼んでいます。
- reps は `APPROVED_REPS` を直接参照し、3/4/6 個と legacy 4 個の killer が実分岐を踏んでいます。
- public `gate_check()` から `launch_validated` は除去され、v2 は `launch_validate()` を通り、private validated gate の production caller は `run_block` のみです。

検証上の制約として、対象 pytest は起動を試みましたが、このセッションでは `/tmp` を含め writable temporary directory がなく、pytest 初期化時に停止しました。テスト失敗ではありませんが、全走結果を独立再実行済みとは扱っていません。純 read-only の import・入力プローブと `git diff --check` は実行でき、巨大整数の2件は上記のとおり再現しました。
```

## レビュー R2 (整合・完全性) 出力 (逐語)

```
## 判定

**NO-GO**。所見は high 1件、medium 2件、low 1件です。実装の主要経路は概ね整合していますが、V9違反と検収記録欠落のため、この4 commitを完了 wave として認定できません。

## 所見

1. **high — 完了条件・D65・変異証拠が commit range に存在しない**

   壊れ方: このまま merge すると、コードだけ発効して Stage 0 の保証範囲、P-A1(a) の段階導入、既知の scope 外4件が正本に残りません。後続担当は D64 の残余と worklog の「次セッションで実装」を見続け、20変異の exact diffも再監査できません。

   根拠:

   - `58934ae..HEAD` の docs / insights 差分はゼロ。
   - decisions はD64で終了し、D65がありません。[decisions.md:2409](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/decisions.md:2409)
   - phase3の完了記録にも本waveがありません。[phase3.md:455](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:455)
   - worklogの正本はまだ「次セッションで実装」です。[worklog.md:968](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/worklog.md:968)
   - 証拠は未追跡 handoff にしかなく、状態も「作業中」です。[handoff:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-20-adjudicated-wave-a1b-b5b6a2-a5.md:3)
   - mutation の exact diff と harness は `job tmp` にのみ置かれています。[handoff:8](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-20-adjudicated-wave-a1b-b5b6a2-a5.md:8)
   - 同じ handoff 内で「20/20」と「19本・19/19」が矛盾します。[handoff:69](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-20-adjudicated-wave-a1b-b5b6a2-a5.md:69)

   最小修正案: 下記コード所見を直した後、D65、phase3完了項、worklog、exact mutant diffを含む追跡済みinsightを同一commitへ追加する。M9/M11を分割 mutant と数えるなら、正しい総数は20として全正本を統一する。handoffは吸収・削除する。

2. **medium — V9の「非有限値拒否」が指数overflowで迂回できる**

   壊れ方: `1e999` はJSON構文上numberですが、Pythonでは `inf` になります。現loaderはこれを3 roleすべてでofficial型に昇格します。実際、有効observationsに未使用の `1e999` fieldを足すと、`OfficialObservations → determinate OfficialVerdict` まで洗浄できました。

   根拠: `parse_constant` は `NaN` / `Infinity` literalだけを捕捉し、`parse_float`または再帰的finite検査がありません。[s8b_oracle_artifacts.py:59](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_artifacts.py:59) [s8b_oracle_artifacts.py:91](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_artifacts.py:91)

   実測:

   ```text
   manifest OfficialManifest inf False
   observations OfficialObservations inf False
   verdict OfficialVerdict inf False
   OfficialObservations inf OfficialVerdict determinate
   ```

   最小修正案: `parse_float`で変換後に `math.isfinite()` を要求するか、parse後に全階層のfloatを再帰検査する。3 role loaderすべてについて `1e999` と nested `1e999` の負例を追加する。

3. **medium — judge fixtureの5-rep波及が未完**

   壊れ方: official reportは常に5値を要求する一方、judgeの正常fixtureは2値、非対称fixtureは3値のままです。テスト内で到達不能なofficial observationsを量産しており、5-rep入力だけで発生する退行をjudge suiteが見逃します。プランv1の「正常bench配列も5値へ」の未実装です。

   根拠:

   - 通常fixtureは2値。[test_s8b_oracle_judge.py:45](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_judge.py:45)
   - tie正例も2値へ上書き。[test_s8b_oracle_judge.py:82](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_judge.py:82)
   - 非対称fixtureは3値。[test_s8b_oracle_judge.py:245](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_judge.py:245)

   最小修正案: 正常・tieを5値化する。非対称fixtureは、medianとmeanで勝者が反転する5値配置（例 `c-low=[10,10,10,10,60]`, `c-high=[15,15,15,15,15]`）へ変更し、数値assertを更新する。意図的破損ケースの1値配列はそのままでよい。

4. **low — 明示的scope外だった `s8b_verdict.py` 直接実行を実質修正している**

   壊れ方: 安全性退行ではありませんが、「既存ModuleNotFoundErrorは実装しない」というscope監査結果と差分が一致しません。新しいsys.path bootstrapにより、実測で `python3 orchestrator/campaign/s8b_verdict.py --help` がrc=0になりました。

   根拠: 直接実行より前にorchestrator pathを注入しています。[s8b_verdict.py:63](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_verdict.py:63)。一方、scope外宣言は [handoff:67](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-20-adjudicated-wave-a1b-b5b6a2-a5.md:67) です。

   最小修正案: 有益な副作用なので戻すより、ユーザー承認の上でscope訂正し、直接実行smoke testを追加して意図した変更として固定する。

## V1〜V15突合

| V | 状況 | 判定根拠 |
|---|---|---|
| V1 | **部分** | Legacy型分離・writer拒否・`manifest_kind`は実装済み。D65のStage 0限定保証が未実装 |
| V2 | 完了 | marker生成とrealpath後のofficial拒否、symlink alias負例あり |
| V3 | 完了 | `APPROVED_REPS`常時参照、宣言不一致、legacy 5値強制あり |
| V4 | 完了 | 順序付き`verify_sequence`と逆順3負例あり |
| V5 | 完了 | abort workload 4状態、exact nested schema、red reason連鎖あり |
| V6 | 完了 | WAL読取直後に全stage走査し、terminal欠落よりpayload issueを優先 |
| V7 | 完了 | public引数除去、private gate分離、production caller静的固定 |
| V8 | 完了 | extime=3単独理由、1 refusal、呼出回数・identity検査あり |
| V9 | **部分** | duplicate keyは拒否するが、`1e999 → inf`を受理。所見2 |
| V10 | 完了 | 3/3 subprocess E2Eとofficial `campaigns/`非生成assertあり |
| V11 | 完了 | schema定数とstage/outcome authorityをleafへ集約 |
| V12 | **部分** | abort merge、両frontier、driver 5値、driver→report統合は実装。judge fixture波及漏れは所見3 |
| V13 | 完了・scope逸脱 | canonical import、TypeError subclass、CLI subprocessあり。所見4 |
| V14 | 完了 | official layout維持、slug helperのみ抽出、非継承sibling |
| V15 | **未実装** | D65自体が存在しない。generator pin外・rep成功定義・Stage 3分離が未記録 |

## 所見なしとした観点

- consumer取り残し: repo-wide call-site検索では、production chainは `build_manifest/verify_manifest → report loader → judge loader → verdict loader` に収束しています。型付きproducerとCLI復元も接続済みです。
- truth-table配線: leafのexact table、module-qualified `matches()`、独立reason closure、物理順序防壁はすべて実在します。[s8b_outcome_stage_contract.py:66](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_outcome_stage_contract.py:66) [s8b_oracle_report.py:527](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:527)
- B6 row-level化: 全6 stageを走査し、非Mapping recordをcountsから除外していません。[s8b_oracle_report.py:368](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:368)
- exploration非汚染: 出力はexploration配下の固定名create-onlyで、E2Eはofficial `campaigns/`非生成を検査しています。[s8b_oracle_exploration.py:48](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_exploration.py:48) [test_s8b_oracle_artifacts.py:193](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_artifacts.py:193)
- real-repo二重台帳: 両側に同一nodeが追加済みです。[conftest.py:86](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/conftest.py:86) [test_real_repo_serialization.py:60](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_real_repo_serialization.py:60)
- plain-runner: 新規2ファイルに実行する`__main__` harnessがあります。
- AI provenance: 4 commitすべて形式適合。`check_ai_provenance --range 58934ae..HEAD`も成功しました。

実行確認は、AST parse 18ファイル、純粋検査14経路、`check_codex_agents.py`、`check_docs.py`、provenance検査が成功しました。sandboxに利用可能な一時directoryがないため、tmp fixtureを使うpytest全走は独立再実行できていません。未追跡handoff記載の2093 passed / 20 mutation KILLは、追跡済み証拠がないためレビュー上は未認証です。
```

## fix 報告 (逐語)

```
実装完了しました。正しさ検査はすべて fail-closed のままです。

変更ファイル:

- 実装:
  - [s8b_oracle_artifacts.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-fix/orchestrator/campaign/s8b_oracle_artifacts.py)
  - [s8b_oracle_report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-fix/orchestrator/campaign/s8b_oracle_report.py)
  - [s8b_oracle_judge.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/wave2-fix/orchestrator/campaign/s8b_oracle_judge.py)
- テスト:
  - `test_s8b_oracle_artifacts.py`
  - `test_s8b_oracle_report.py`
  - `test_s8b_oracle_judge.py`
  - `test_s8b_verdict.py`
- 作業記録:
  - `docs/phase3.md`
  - `docs/worklog.md`

各 fix:

- F1: resolve 済み output root を後段まで再利用。campaign root の containment と symlink component を検査し、探索 campaign symlink を `ReportError` で拒否。root 差し替え負例も追加。
- F2: strict JSON loader で `1e999` と nested overflow を拒否。共通の有限 float 射影で巨大整数を捕捉し、report は row-level `protocol_violation`＋空 bench、judge は `indeterminate`。
- F3: 正常・tie・median/mean 反転 fixture をすべて 5-rep 化。
- F4: observations/verdict loader の `null`、未知 schema、他 role official schema を API/CLI 双方で拒否。CLI は rc=2・出力なし。

テスト結果:

- 指定 pytest: `265 passed, 1 skipped`
- `git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 成功

逸脱:

- commit は未作成です。sandbox が `.git/worktrees/wave2-fix/index.lock` を read-only として拒否しました。index への部分反映はなく、差分は未 staged のままです。
- 担当外の実装変更・push はありません。
```

## 親裁定サマリ

- プラン v1 への敵対相談: C-A 10 件 (real 10 / refuted 0)、C-B 15 件 (real 15 / refuted 0)。
  採用修正 V1〜V15 + 実行分割 V16 (正本 = 本 wave worklog エントリ、当時の作業台帳 = handoff、吸収済み)
- レビュー: R1 5 件 + R2 4 件 + V 突合。real = コード 4 件 (fix a89e2b8 で閉鎖)、記録 2 件 (本
  insights + 変異台帳 + D65 で閉鎖)、scope 訂正 1 件 (下記)、期待どおりの未了指摘 2 件 (記録段前の
  D65/phase3 不在)
- scope 訂正 (R2-4): E1 が s8b_verdict.py に sys.path bootstrap を追加し直接実行の既存
  ModuleNotFoundError が偶発的に直った。scope 外宣言と差分の不一致をレビューが検出。親裁定 =
  V13 (CLI 実 subprocess テスト) の enabler として維持し、ここに記録して訂正 (正しさゲートへの影響なし)
- fix unit の scope 逸脱 1 件: 担当外の worklog/phase3 を編集 (wave 未完了時点の完了表明) → 親が
  差し戻し、記録は本記録段で一括作成。exec 子への docs 編集禁止の明示は次回プロンプトから恒久化

## 裁定パッケージ (§5-(ix) 形式、ユーザー裁定待ち — 本 wave では実装せず)

1. **P-C1 (medium): rep の「成功」が rc=0 を含意しない。** run_once は strict でない限り非ゼロ終了でも
   parse 可能な tps を採用し、5 回繰り返せば report の件数検査 (5/5) を通る (C-A4。runner.py:346,371,462、
   pipeline.py:231)。**選択肢**: (a) official driver だけ require_all_reps=True の seam、(b) rep ごとの rc を
   WAL に記録し report が 5 件 rc=0 を検査、(c) 「成功 = 有限 tps が parse された rep」を意味論として追認
   (D65 に暫定明記済み)。**推奨 = (b)** (report が証拠と突き合わせる現行様式に整合)
2. **P-C2 (medium): 正当な prepare retry が report で protocol_violation になる既存偽陽性。** driver の
   transient prepare 失敗は trial-start(1)→retry→trial-start(2) を発行するが、report は window 1 を
   trial-result 0 件で invalid とし、成功した attempt 2 も「過去 attempt が invalid」で上書きする (C-A7、
   親が実読で裏取り。driver:1106-1112 vs report の window 化 + 過去 attempt 汚染)。安全側の偽陽性だが
   「report が証拠 truth table を検証する」契約の穴。**推奨**: attempt lifecycle の閉表化 (「trial-result
   なし + retry 1 件 + 次 attempt 番号一致」window を正当 retried として扱う) + 正例テスト
3. **P-C3 (low): 意味論 leaf が oracle manifest の generator pin の外。** generator source hash は
   materializer/report/judge の 3 ファイルのみで、s8b_outcome_stage_contract.py / s8b_oracle_artifacts.py の
   変更は pin に映らない (C-B14。s8b_oracle_manifest.py:42,377,715)。**推奨**: P-A1(a) 段階導入時に
   transitive source bundle identity へ拡張 (D65 残存リスクに明記済み)

## ループ工数 (ハイブリッド初回試行の観測値)

- codex: planner 1 (max) + 相談 2 (max) + 実行 3 (high) + 変異仕様 1 (medium) + レビュー 2 (high) +
  fix 1 (high) = 9 本。親 = fable (brief、裁定、scope 監査、統合、変異ゲート実測、記録)
- 敵対段の初回検出力: 相談 25 所見 (プラン v1 NO-GO)、レビュー 9 所見 (実装 NO-GO→fix で閉鎖)。
  従来形式 (B-004: 相談 14 所見) との比較はサンプル 1 のため結論保留 — 品質面の劣化兆候はなし
