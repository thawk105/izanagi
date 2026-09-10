静的検査のみ（pytest 未実施）。現状は **NO-GO** です。主な理由は、独立した source 集合の同期防止、拡張後のテスト代表性、dirty tree による偽の赤です。

### D-01 / certified source 集合が独立しており、片側だけの拡張を検出できない / real

- **根拠**: `orchestrator/campaign/campaign_lock.py:27-30` は T-721 対象の 2 path（拡張後 8）。`orchestrator/qualification/contract.py:38-81` は別の code 37 path と script 3 path。`orchestrator/qualification/identity.py:130-144`、`t126_driver.py:346-365` が後者を利用する。`silo_ladder_rung1.py:254-294` はさらに別の runtime module 集合を持ち、現在は固定 path、activation JSON、4 calibrator module、`patchharness.py`、`run_probe.py`、`verifier/*.py`（現行 8 ファイル）からなる 22 path。C++ 側は `silo_ladder_rung1_contract.py:19-22` の 2 path。`source_digest.py:73-82` の 3 path は別目的の候補 source allowlist で、同一集合ではない。
- `test_t419_probe_causality.py:25-42` は env-contract path が qualification 集合の部分集合であることしか検査しない。`test_t126_pegasus_tools.py:1450-1465` は qualification 集合自身の完全性だけを検査する。campaign 集合との cross-check はない。親 brief の「両集合の等値 assert はない」は確認できた。
- **成果物影響**: campaign lock が 8 path を記録しても qualification identity は別集合のままとなり、certified 選択・qualification 台帳・報告の source identity が一致しないまま通る。
- **最小の修正案**: T-721 内で campaign の期待 8 path を独立検査し、qualification との意図した差分を明示する監査テストを追加（scope 内）。qualification 集合そのものを 8 path に統合するのは brief の選択肢 c で scope 外。

### T-01 / 動的 fixture と index 依存が閉包の誤りを吸収する / real

- **根拠**: `campaign_lock_test_support.py:18-31` は production の閉包を走査して fixture を自動生成する。`test_artifact_admission.py:346-360` も同じ経路。`test_layer3_report.py:53-80` は別の動的 helper を持つ。共有 helper の利用先は 15 ファイルあり、これとは別に `test_layer3_report.py` が 1 ファイルある。
- `test_campaign_lock_codec.py:39-44` は閉包を走査するため、path を 1 本落としても fixture 自体は成立する。`test_artifact_admission.py:1217-1224` の alias 検査も production constant と同じ object を見るだけで、期待集合を検査しない。
- `test_artifact_admission.py:981,1159,1181,1194` は `[0]`、`test_artifact_admission.py:1137` は `[-1]` に依存する。閉包が 2→8 になると `[-1]` は旧 activation path から `artifact_admission.py` に移るが、全 path の検証にはならない。
- `test_t671_source_binding.py:20-23,116,156` の旧 2-path golden は拡張時に赤くなるが、「どの path が欠落したか」を検出する検査ではない。更新後に dynamic fixture だけを残すと、6 path 中 1 本を落とす変異を既存テストは安定して検出できない。さらに `_authority` の `str(index) * 64`（`test_campaign_lock_codec.py:39-44`）は 8 path 化後に index 10/11 が 128 文字となり、意図しない hash shape エラーを起こす。
- **成果物影響**: certified lock の source hash map が 7 path でも、選択・レポート・台帳生成テストが通り、欠落した module の変更が受理判定から消える。
- **最小の修正案**: 独立した期待 8 path の exact sentinel、8 path 全てを parameterize した live/committed 検査、各 key 欠落の codec 検査を追加（scope 内）。fixture の自動追随だけに依存しない。

### O-01 / enforcement 6 module の dirty tree が通常のテスト・driver を偽の赤にする / real

- **根拠**: `contract_loader_binding.py:320-355` は live 検証時に閉包各 path の disk bytes と記録済み commit blob を比較する。`ident.py:449-479` が新規・既存 certified 実行の停止点である。
- certified identity を経由する driver は `loop.py:146-150`、`screening_driver.py:99-113,157-167`、`guided.py:172-175,199-202`、`s1_direct_comparison.py:248-254`、`s8a_trigger_sweep.py:380-383`、`s6_sort_sweep.py:278-281`、`p3_s4_loop.py:880-884,1002-1004`、`p3_s4_loop_sort.py:239-242,326-328`、`p3_s4_loop_trigger_gating.py:570-572,770-772`。
- v2 fixture は `campaign_lock_test_support.py:18-20` と `test_layer3_report.py:63-77` で現在の source を直接 capture するため、6 module の編集中に fixture 作成段階で `contract-loader-drift` になる。
- 一方、既存の submit script は全 tree dirty を既に拒否する（`tools/pegasus/submit_certify.sh:72-78`、`submit_floor.sh:194-204`、`submit_t126_qualification.sh:76-94`）。また artifact admission は committed blob のみを検証し、working tree を読まない（`artifact_admission.py:549-564`、`contract_loader_binding.py:358-373`）。
- **成果物影響**: dirty な certified 実行では選択・WAL・receipt が生成されず、開発中の直接 driver と dynamic fixture だけが偽の赤になる。既存 artifact admission の受理値は必ずしも赤にならない。
- **最小の修正案**: fixture を clean な一時 commit／明示的な frozen binding から作るようにし、dirty-tree 拒否は専用テストで検証する（scope 内）。production の fail-closed は維持。

### N-01 / `contract_loader_*` という名称が 8 path の enforcement gate を loader 2 module と誤認させる / real

- **根拠**: 定数は `campaign_lock.py:27-30`、wire key と dataclass field は `campaign_lock.py:40-59,153-188`、`contract_loader_binding.py:47-82`。実際の 6 path には `loop.py`、`pipeline.py`、`wal.py`、`ident.py`、`artifact_admission.py` が含まれる。`docs/decisions.md:11910-11945` は現状を「contract loader 2 module」と説明しており、T-721 後は旧説明と衝突する。
- 改名対象の直接参照は次の 9 ファイル：`campaign_lock.py`、`contract_loader_binding.py`、`ident.py`、`artifact_admission.py`、`tests/campaign_lock_test_support.py`、`tests/test_campaign_lock_codec.py`、`tests/test_artifact_admission.py`、`tests/test_layer3_report.py`、`tests/test_t671_source_binding.py`。過去の `output/insights/2026-08-09_t671-impl/mutation-ledger.json` と `mutation-spec.json` は履歴なので書き換えない。
- 「v2 lock が 0 本なので今しか改名できない」は、ローカル `output` に v2 lock がないという意味では正しいが、外部・未取得 artifact まで 0 と証明するものではない。また後続 v3 migration という窓は残る。従って「唯一の窓」ではなく「最小コストの窓」。
- **成果物影響**: 将来の監査者が loader 2 module だけを hash すべきだと誤読し、certified 選択・レポート・台帳の enforcement source identity を縮小する危険がある。
- **最小の修正案**: `ENFORCEMENT_SOURCE_RELATIVE_PATHS`、`enforcement_source_commit`、`enforcement_source_blob_sha256s` へ全 9 ファイルで改名し、新しい decision で旧 D259 を明示的に supersede（scope 内、P1 を変更する場合）。互換 alias は追加しない。API/class 名まで全面改名する場合は scope 外。

### A-01 / 「受理集合は縮むだけ」という親 brief の一般化が誤り / real（親の主張は refuted）

- **根拠**: brief `brief.md:54-55` は受理集合が縮むと一般化しているが、`campaign_lock.py:153-172` は v2 authority key を閉包との exact set で比較する。stage2 plan `stage2-plan.md:115-130` 自身が、旧 2-key v2 は reject、exact 8-key v2 は従来の extra-key reject から accept になると認めている。
- **成果物影響**: ローカル実 artifact は v1 が 32 件、v2 が 0 件なので既存 artifact の受理値は変わらないが、wire-level v2 受理集合は単純な部分集合ではなく置換になる。
- **最小の修正案**: brief と decision の表現を「既存 artifact は不変、v2 wire contract は旧 exact 2-key から新 exact 8-key へ置換」と修正し、旧 2-key／新 8-key の acceptance matrix を追加（scope 内）。

### M-01 / 親の実測 1–7 は狭義には概ね正しいが、5–7 の射程が広すぎる / partially refuted（nit）

- **根拠**:
  - 1–3（6 module の存在、`output` の 32 v1 / 0 v2、`FROZEN_MANIFEST` が output/insights のみ）は再確認できた。manifest は `orchestrator/tests/test_frozen_artifacts.py:38-85,139-153` でも管理される。
  - 4 の「9 ファイル」は旧定数・wire key の直接参照としては正しいが、dynamic helper の間接利用先を含まない。
  - 5 の「4 production call site」は production 限定なら正しいが、テスト側にも `campaign_lock_test_support.py:19` と `test_layer3_report.py:64` の capture 経路がある。
  - 6 の「15 test files」は共有 helper の importers としては正しいが、独立 helper の `test_layer3_report.py:53-80` を加えると dynamic v2 fixture の影響先は 16 ファイル。
  - 7 の「cross-set equality がない」は正しい。ただし「機械検査が全くない」と読むなら誤りで、qualification 自己検査と `test_t419` の一方向 subset 検査は存在する。
- **成果物影響**: 影響範囲の過小評価により、テスト更新・dirty-tree 対策・監査対象ファイルが漏れる。
- **最小の修正案**: 実測表に「production direct」「shared fixture」「duplicate fixture」「one-way qualification check」を分けて記載（scope 外の文書修正）。

## 総括

NO-GO。must-fix 5 件、nit 1 件。  
必須なのは独立した 8-path 検査、per-path テスト、dirty fixture 対策、名称の是正、受理集合の表現修正。  
qualification 集合の統合自体は scope 外だが、非同一性を監査可能にする必要がある。