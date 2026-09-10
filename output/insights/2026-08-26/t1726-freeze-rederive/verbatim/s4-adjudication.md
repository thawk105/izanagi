# 段 4 裁定 — dev-wave-t1726-freeze-rederive

base: main 33cb632164575ddead33e9af2d9d048dc106d811 (t822-evidence-gaps 着地後へ ff 済み)

## 所見の裁定

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A | `load_legacy_freeze(repository_root)` が編集禁止の `test_trial_registry.py` 正例を `legacy-read` で赤くする | real | 採用 (設計変更) |
| B | `s8b_ratified_freeze` / `s8c_arm_inputs` の eager import が軽量 verifier の依存面を 35 module へ拡大する | real | 採用 (lazy import) |
| C | expected `arm_binding_digest` の比較は既存 gate から恒真で純増ゼロ | real | 採用 (=足さない) |
| D | 投影が legacy entry の `variant_binding` / `unknownness_check` を落とす | real (事実) | 部分採用 |
| E | legacy `derangement` と in-source `DERANGEMENT` が exact 比較されない | 疑い | 採用 |
| F | receipt が名乗る `measurement_head` が独立に束縛されていない | real | 一部採用・残り scope 外 |
| G | `cells=[]` + C02 保持で descriptor 不在のまま受理できる | real | scope 外 |
| H | issuer 層 (`trial_registry`) に同じ authority 断絶が残る | real | scope 外 (編集禁止) |
| I | 親 brief の成果物影響・純増・競合ゼロの記述が過大 | real | 全面採用 (訂正) |
| K | fixture 実 resolver 化で 1.63s→3.5-5s | 疑い | 受容 |

### A — 権威 root を subject repo から分離する
ratified legacy freeze は **verifier 自身の trust root** であり、検証対象 repo が供給するものではない。
`s8b_ratified_freeze.load_legacy_freeze()` を既定 `ROOT` で呼ぶ。subject `repository_root` からは
historical off artifact だけを読む (現行 `resolve_arm_input` の挙動そのまま)。
既存 `p3_autonomous_workload_trial._preflight_workload_profile` が `repository_root=ROOT` を渡す形と同型。
これで `test_trial_registry.py:1615` の正例は赤くならない。

### C — 恒真な assert を足さない
既存 gate が `B_receipt = hash(holdout, arm, C_receipt)` を要求済みのため、
`C_receipt == C_expected` を足せば `B_receipt == hash(holdout, arm, C_expected)` は決定論的に従う。
比較するのは **expected content digest だけ**。省いた理由をコード comment に 1 行残す。

### D — 深刻度は限定的。ただし drift へ fail-closed にする
`s8b_descriptor.project_from_search_config` (85-119 行) が消費するのは
`records` / `threads` / `ycsb.{ycsb_zipf_skew, ycsb_rratio, ycsb_rmw}` の 5 field だけで、
落ちる 2 key は workload 条件に入らない (親が一次資料で確認)。
よって 4-key 投影は T-525 の定義する完全条件と一致する。
ただし legacy holdout entry の **key 集合がちょうど期待 6 key であること**を assert し、
将来の key 増減で黙って通らないようにする。

### F — 一部採用
- **採用**: `launch_admission.binding` の `measurement_head` と receipt の `trial.measurement_head` の
  exact 比較を足す。既存の binding 比較は `arm` / `holdout` / `campaign_id` しか見ていない
  (`s8c_acceptance_receipt.py:764-774`)。
- **scope 外**: ancestor 検査・registry 記録 head との束縛。
  理由: 本 wave の条件再導出は measurement_head に依存しない。on/swapped は commit を使わず、
  off は commit 先の bytes が in-source 期待値 (`_artifact_payloads`) と一致しなければ落ちる。
  別 commit を選んでも**誤条件は通らない**。provenance の穴であり別軸。裁定パッケージへ。

### G / H — scope 外
G は C02 reason 保持の設計と一体で、変えると
`test_partial_receipt_cannot_drop_c02_reason_without_descriptor_proof` の設計意図と衝突する。
H は編集禁止面。どちらも実装したふりにせず裁定パッケージへ返す。

### I — 親 brief の訂正 (正本を上書きする)
- **成果物影響 (DW-G05 再記)**: 現 checkout では全 receipt が構造的に `certifying=false`
  (`s8c_acceptance_receipt.py:393-396`) で、`layer3_report` が `certifying is True` を要求する
  (`layer3_report.py:623-624`)。よって**現在の成果物の値は変わらない**。
  放置して変わるのは標準 verifier の受理集合であり、certifying を有効化する将来世代で
  B-3 の certified 選択が ratified freeze と異なる条件の試行に乗る。
- **純増検出力**: 「標準 verifier 単独で」に限定する。repository-wide では
  `trial_registry` 発行経路が既に expected arm execution を比較している。
- **編集面の競合ゼロ**: テキスト競合に限定。意味的巻き添え (`test_trial_registry.py:1615` の正例) はある。
- **アンカー訂正**: `_formal_profile_source_record` は 854 行 (851 は前 helper)。
  `ycsb_rratio` 一本の証拠は `trial_registry.py:4110-4115`。`layer3_report` の受理は 623-624 行。

### J — [T-1727] の裁定 (本 wave の主要成果の一つ)
**v4 は本 wave では上げない。旧 v2/v3 artifact は固定 V1 authority の legacy として読み続ける。
明示的失効は採らない。** ただし次の 3 条件付きであり、decisions へ記録する。

1. `V1_FREEZE_SHA256` を差し替えない。
2. `HOLDOUTS` / `DERANGEMENT` を改訂しない。
3. 1 または 2 を行う前に、v4 (freeze の path / hash / generation を serialized binding へ載せる)
   を先に入れる。

根拠: 再導出に要る値 (arm / holdout / measurement_head / content digest) は v2/v3 に既にあり、
authority が単一固定である限り v4 の純増は provenance 記録に留まる。
一方 v4 は receipt bytes を変え、`test_reflux_originless_compatibility._PRE_WAVE_ORIGINLESS_BASELINE`
と編集禁止の `test_trial_registry.py` を巻き込む。
authority が複数世代化した瞬間に v4 は受理判定そのものになる — これが上の 3 条件の理由である。

## プラン v2 (段 5 の実装対象)

編集面は `orchestrator/campaign/s8c_acceptance_receipt.py` と
`orchestrator/tests/test_s8c_acceptance_receipt_v2.py` の 2 file **だけ**。

1. module docstring を更新し、「approval authority は推論しないが、記録された arm execution が
   ratified legacy freeze から再導出できることは検証する」と責務を書く。
   `trial_registry` / `layer3_report` 非依存は維持する。
2. helper を 3 本追加する (関数ローカル lazy import)。
   - `_require_ratified_legacy_arm_authority()`
     `s8b_ratified_freeze.load_legacy_freeze()` を **既定 ROOT** で呼ぶ。
     `legacy.document["holdouts"]` の名前集合を `s8b_holdout_freeze.HOLDOUTS` と exact 比較。
     各 legacy entry の key 集合がちょうど
     `{candidate_id, ycsb, records, threads, unknownness_check, variant_binding}` であることを assert。
     4-key 投影 (`candidate_id` / `ycsb` / `records` / `threads`) を canonical bytes で exact 比較。
     `legacy.document["derangement"]` と `s8b_holdout_freeze.DERANGEMENT` を exact 比較。
     失敗は `[receipt-freeze-arm-binding]` の `AcceptanceReceiptError` へ変換する。
   - `_expected_arm_content_digest(root, holdout, arm, commit)`
     `s8c_arm_inputs.resolve_arm_input(...)` を呼び `content_digest_sha256` を返す。
     `ArmInputError` は同じ gate へ変換する。
   - `_assert_rederived_trial_arm_execution(root, trial)`
     expected content digest と `trial.arm_execution.content_digest_sha256` を exact 比較。
     **arm_binding_digest の expected 比較は足さない** (裁定 C、理由を comment に残す)。
3. `_verify_v2_trial_arm_execution` の binding 比較へ `measurement_head` を追加する (裁定 F)。
4. `verify_acceptance_receipt` の v2/v3 経路で、
   ループ前に `_require_ratified_legacy_arm_authority()` を 1 回、
   各 trial の既存検査成功後に `_assert_rederived_trial_arm_execution` を呼ぶ。
   v1 には入れない (裁定どおり v1 は対象外)。
5. `test_s8c_acceptance_receipt_v2.py` の `_fixture` を実 resolver 化する。
   temp repo へ `generate_off_neutral_artifacts` で off artifact を作って commit し、
   その OID を六セル共通の `measurement_head` にする。descriptor と arm execution は
   `resolve_arm_input` の結果から作る。**legacy freeze bytes を temp repo へ複製しない**
   (権威 root は verifier 自身の checkout であり、複製しても検査されない fixture を作らない)。
6. test を追加する (下の変異事前登録と 1 対 1 に対応させる)。

## 変異事前登録 (DW-M01 / B-057)

受理集合を**縮小する** wave のため、過剰拒否を検出する正例も登録する。
各変異は「同じ入力を拒否する層が前後に無いこと」「無効化時の赤理由が一つ」を
実装完了後・harness 起動前に親がコードで確認する。

| ID | 変異位置 | 期待 kill | 単一理由性の根拠 |
|---|---|---|---|
| M1 | `_assert_rederived_trial_arm_execution` の content digest 比較を無効化 | `test_self_consistent_wrong_descriptor_is_rejected_by_freeze_rederivation` | 誤値 mutant は既存 gate を全部通る (段 3 レンズ A の 8 番で file:line 追跡済み)。この比較だけが拒否する |
| M2 | legacy holdout entry の key 集合 assert を無効化 | key 増減 fixture の test | 他に legacy entry の key 数を見る層は無い |
| M3 | `derangement` exact 比較を無効化 | derangement 改竄 fixture の test | resolver は in-source `DERANGEMENT` しか読まないため他層で拒否されない |
| M4 | `binding.measurement_head` 比較を無効化 | binding head 不一致 fixture の test | 既存 binding 比較は arm/holdout/campaign_id のみ |
| M5 | 権威 root を既定 ROOT から `repository_root` へ戻す (過剰拒否の対照) | `test_trial_registry.py::test_p5_six_complete_terminal_reports_pass_acceptance` が赤 | 編集禁止の正例が `legacy-read` で落ちる。承認外の過剰拒否を検出する正例 |

positive control (誤値 receipt が実際に赤になる負の対照) は M1 に対応する test であり、
descriptor の `read_write.read_ratio_percent` を **整数** 80 → 79 に変える
(段 3 レンズ A の指摘どおり文字列ではない)。
receipt / report / run-start の 3 箇所の content digest と、
そこから導く binding digest、report/journal の sha256、receipt bytes をすべて同期し、
既存 gate を全部通過させたうえで新 gate だけで落とす。

## 実装しないと決めたもの (裁定パッケージ候補)

- `measurement_head` の ancestor / registry 記録 head への束縛 (F の残り)。
- `cells=[]` で descriptor 不在のまま受理できる構造 (G)。
- issuer 層 `trial_registry` の legacy freeze 断絶 — producer / issuer / verifier が共有する
  軽量 authority leaf の新設を含む (H)。
- v4 世代交代そのもの (J の条件 3)。
