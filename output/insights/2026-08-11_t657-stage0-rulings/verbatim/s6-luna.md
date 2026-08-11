## 静的変異追跡

- state pin 無効化: 4 件の `resolved→unresolved` と `CFAB-S-SEAL→S1` は既存 schema・enum・applicability を通るため、対応する 5 node が赤になる。単一理由性は成立する。
- module hash pin 無効化: hash 再計算済み並べ替えは semantic `frozenset` を通り、`test_required_gate_reorder_with_refreshed_manifest_hash_is_rejected` だけが実効 kill になる。
- selection 列照合無効化: `test_design_selection_column_matches_selection_enums` が実効 kill になる。
- 段集合照合無効化: `test_design_stage_scope_matches_fixture_assignment_gate_id` が実効 kill になる。
- 抽出 0 件は selection 側の ID exact 照合、段集合側の `len(matches) != 1` により fail-closed。単純な vacuous pass はない。
- required-gate entries は LF なし 612 bytes、SHA-256 は `93cfe2b3…11e41` で三者一致。record 全体だけが canonical JSON + LF であり、末尾 LF の分離は正しい。

## LUNA-01 / blocker

- **破れる具体構成:** 実際の `mutation-spec.json` をそのまま走らせる。段 4 の M3（`FREEZE-U-A1` enum を旧 2 値へ戻す SURVIVED 変異）は存在せず、段 4 の M4/M5/M6 が M3/M4/M5 に改番され、M6 は「全 12 ID resolved」から `CFAB-S-SEAL` 1 件の期待値変更へ置換されている。spec は 5 変異で終了する。
- **根拠の file:line:** `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-rulings/s4-ruling.md:100-106`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-rulings/mutation-spec.json:6-92`。別の discovery spec にだけ旧 enum 変異相当が M6 として残る (`mutation-spec-discovery.json:24-36`)。
- **成果物影響:** 変異台帳の母数が事前登録の 6 から 5 へ変わり、wave 前 enum 形を一度も検査せず「全登録変異を処理済み」と受理できる。

## LUNA-02 / blocker

- **破れる具体構成:** 段 4 M3 どおり `_SELECTION_ENUMS["FREEZE-U-A1"]` を `{"activation-window","post-activation-lease"}` へ戻す。profile の `post-activation-lease` は enum を通るが、最初に docs selection exact 照合が拒否する。そこも同時に無効化すると state pin が拒否する。さらに負例 helper は拒否理由を `"selection is outside its allowed enum"` に固定しているため、別層の拒否でも node 自体は赤になる。
- **根拠の file:line:** enum と docs 照合は `orchestrator/tests/calibration_freeze_authority_contract.py:83-95,527-532`、state pin は同 `:589-596`。理由文字列を oracle にする helper は `orchestrator/tests/test_calibration_freeze_authority_contract.py:124-132`、対象 node は同 `:490-505`。SURVIVED 主張は `s4-ruling.md:103`。
- **成果物影響:** certified selection の受理集合は masking により不変なのに、変異台帳は acceptance-equivalent な M3 を KILLED または MISMATCH と記録し、enum に独立検出力があるという誤った値を持つ。

## LUNA-03 / blocker

- **破れる具体構成:** §8.1 の現 Markdown 表を HTML comment 内へ移し、可視部分を HTML table にして U-A1 へ `post-activation-lease` を追加する。抽出器は comment 内の旧行をそのまま読むため緑になる。同様に §10 の現宣言行を comment 内へ移し、可視行を「段 1〜4 および段 5〜8」と書き換えると、旧 gate ID を導出して緑になる。いずれも静的に再現できた。
- **根拠の file:line:** regex は raw text を直接検索し comment を除去しない (`orchestrator/tests/calibration_freeze_authority_contract.py:53-61,315-354`)。設計が可視表・宣言を正本とする箇所は `docs/calibration-freeze-authority-bundle-design.md:502-520,638-647`。新テストは通常行の直接置換しか扱わない (`orchestrator/tests/test_calibration_freeze_authority_contract.py:645-677`)。
- **成果物影響:** 可視設計では lease または段 5 を許容しながら、contract・gate・profile は隠した旧値を検証できるため、certified 選択とレポートの説明、および台帳 gate ID の受理集合が分離する。

## LUNA-04 / must-fix

- **破れる具体構成:** required-gate module pin 比較だけを無効化し、通常 fixture のまま `test_required_gate_entries_have_independent_module_sha_pin` を走らせる。この node は production の比較を検査せず、現在の entries・manifest hash・production module 定数が一致することだけを再確認するため緑のままである。赤になるのは並べ替え負例だけである。
- **根拠の file:line:** production 比較は `orchestrator/tests/calibration_freeze_authority_contract.py:491-503`。陽性 node は `orchestrator/tests/test_calibration_freeze_authority_contract.py:227-234`、実効負例は同 `:592-610`。段 4 は両 node が kill すると登録している (`s4-ruling.md:102`) が、実 spec は並べ替え node だけへ変更済み (`mutation-spec.json:28-40`)。
- **成果物影響:** required-gate の受理集合自体は並べ替え負例が守るが、変異台帳の事前登録 expected-node 集合は成立せず、M2 を「登録どおり完全一致 KILLED」として受理できない。

## LUNA-05 / nit

- **破れる具体構成:** state pin または required-gate validator を削除し、checked-in fixture は変更しない。`test_adjudicated_ruling_and_gate_projection_is_exact` は引き続き緑である。これは validator の拒否能力ではなく、現在の fixture 内容の snapshot assertion だからである。
- **根拠の file:line:** node は `load_ruling_profile()` / `load_manifest()` の返値を固定 tuple と比較するだけ (`orchestrator/tests/test_calibration_freeze_authority_contract.py:186-224`)。拒否入力は別の陰性 node が担う。
- **成果物影響:** 現行の受理集合は陰性 node が守るため変わらないが、この node を production gate の mutation sensitivity と説明すると検査報告だけが過大になる。

## 総括

NO-GO。  
最大の破れは、段 4 で固定した M1〜M6 と実際の mutation spec が別物で、旧 enum 変異が脱落していること。  
さらに M3 は復元しても docs 照合と state pin に二重 masking され、SURVIVED にはならない。  
新設した docs binding は抽出 0 件には fail-closed だが、HTML comment に旧表・旧宣言を隠す構成では緑のまま破れる。