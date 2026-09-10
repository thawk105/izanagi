### pin 閉包は 2 ファイルの 7 更新値で閉じる

種別: real

根拠:

- 凍結 snapshot: `orchestrator/tests/reflux_origin_fixture_baseline.json:15-17,23-25` が ordered projection の長さ/hash と result record の hash を固定する。
- 独立 golden: `orchestrator/tests/test_reflux_result_evidence.py:24-27` の 4 定数が `:154-181` で別々の hash 層を固定し、`_LEDGER_EVIDENCE_DIGEST_GOLDEN` は `:298-300` でも使われる。
- 不変の長さ pin: 同 file `:150` と baseline `:24` の `1848` は変更不要。
- live copy: builder は source WAL の hash/長さを `reflux_origin_fixture_builder.py:388-398`、projection hash を `:463-469`、repository 各 record の参照を `:608-618,649-655` で実データから再計算するため、手更新対象ではない。
- 静的な canonical-byte 再計算結果はプランと一致した。source WAL は 715 bytes、projection は `975 / 271323c60ad2af8b4034872096d5c1c5066f26c6c85689252dd5ce762ddd3bc6`、result record は `1848 / 631a5fa04f9cc1a5442c5660410bb27b1ad03ef76f5da3fe3d4603ac5577c82c`。派生 2 値もプラン記載どおり。
- `tools/`、`docs/`、`output/` に現行 hash 値の追加 pin はなかった。`docs/failures.md:1778-1785` と `output/insights/2026-09-05_t2257-formal-consumer-wal-shape/verbatim/s4-ruling.md:42-43` は過去の経緯であり、歴史記録に分類される。

影響: pin を更新しないと fixture baseline と result-evidence tests が赤になり、変更を受理できない。本番 certified 選択や台帳値を直接変える pin ではない。

分類: must-fix

### 64 hex・長さ・caller・repo 外の 4 探索でも第三の operative pin は見つからない

種別: refuted

根拠: 現行 projection/result hash の値検索は上記 2 test file の 6 出現だけだった。`test_reflux_formal_consumer.py:42-56,682-684` の 64 hex は trigger producer の独立 golden、`test_trial_registry.py:693-706` の値は arm content digest であり、terminal fixture からの dataflow がない。`reflux_origin_fixture_builder.py:385-469` の全 hash caller は自己計算か上記 golden に収束する。

影響: pin 更新対象をさらに増やしても成果物の参照整合性は強くならず、無関係な frozen 値を動かすだけになる。

分類: nit

### 10-file test 閉包は間接利用者を 1 ファイル漏らしている

種別: real

根拠: `orchestrator/tests/test_reflux_originless_compatibility.py:13` が `test_p3_autonomous_workload_trial` を helper として importし、`:134` で `_origin_public_inputs()` を呼ぶ。その helper は `test_p3_autonomous_workload_trial.py:10502` で変更対象の `build_fixture_repository()` を呼び、`:10624-10630` で生成 result bytes と evidence root を formal consumer へ渡す。さらに compatibility test は `test_reflux_originless_compatibility.py:136-144,1168-1172` で origin-enabled の完全経路を実行する。段 2 の一覧 `s2-plan.md:230-243` にはこの file がない。

影響: 漏らすと、fixture terminal 変更が origin-enabled report と originless compatibility guardを同時に壊す回帰を検出できない。

分類: must-fix

### 10-file 集合は保守的 import closure としては妥当だが、最小挙動閉包では 2 file が過剰

種別: real

根拠:

- `test_reflux_origin_topology.py:12-14,30` が使うのは `build_recovery_envelope_inputs()` だけで、同 builder は `reflux_origin_fixture_builder.py:497-539` にあり `_wal_records()` を呼ばない。
- `test_trial_registry.py:43,844-854` が builder から使うのは `build_launch_admission_inputs()` だけで、formal consumer も `:895-914` で型と reason enum を合成するだけで `_validate_wal_outcomes()` を呼ばない。
- ただし module import smoke を目的にするなら両 file を残す理由はある。保守的集合は 10 ではなく、上記間接 file を加えた 11 file。

影響: 過剰 2 file は受理集合や成果物値を変えず、実行時間だけを増やす。

分類: nit

### 元の 3-file scope なら 5 test が確実に赤になるが、5-file plan はそれを閉じている

種別: real

根拠: pin 更新を省いた場合に落ちる assertion は次のとおり。

- `test_reflux_origin_fixture_builder.py:112-114`: baseline 全 entry と再計算値の等価比較。
- `test_reflux_result_evidence.py:157`: raw record hash と旧 `_RECORD_RAW_GOLDEN`。
- 同 `:163`: ledger digest と旧 `_LEDGER_EVIDENCE_DIGEST_GOLDEN`。
- 同 `:181`: 新 raw bytes から作る wrong-domain hash と旧 golden。
- 同 `:298-300`: 新 record digest と旧 ledger golden の member mapping 比較。

`test_hash_layer_3...` の `:167-173` は、両方の旧定数を残すだけなら自己整合して赤にならないが、意味的には stale になる。プランは ledger golden と outer commitment を同時に更新しており正しい。

影響: 3-file 実装では焦点走を通せない。5-file 実装なら、これらの既知 assertion mismatch は静的に解消される。

分類: must-fix

### 完全 plan と 11-file 集合の実走結果は判定不能

種別: 判定不能

根拠: 本段では pytest を実行していない。特に `test_reflux_originless_compatibility.py:136-144` は temporary repository、formal consumer、report 書き込みを通る動的統合 test で、静的検査だけから実際の終了状態までは断定できない。

影響: 未実走を緑と扱うと、report projection または lifecycle 台帳の動的回帰を見逃す。

分類: nit

### pin 2 file が増えても実装子 1 本で十分である

種別: refuted

根拠: 編集は consumer の 2 判定、fixture の同一 terminal、対応 test、そしてその出力を固定する 2 pin file に閉じる。`reflux_origin_fixture_builder.py:385-469` が projection から result hash まで直列に伝播させるため、core と pin を別所有にすると中間状態だけが不整合になる。静的再計算値も既に確定している。

影響: 1 本なら consumer、fixture、golden を同時に整合させられ、certified/report/ledger の意味を分割所有で変える危険はない。

分類: nit

### accepted 側が FC07 を通るという狭い DW-G05 主張は正しい

種別: refuted

根拠: 判定順は次のとおり。

1. 全 verify 成功後、`pipeline.py:1627-1669` が verify tag を確定して certified にする。
2. `pipeline.py:1762-1786` が `verify_configs` と `build_attempt_id` を payload に入れ、`:1790-1800` が `STAGE_COMMIT` で `wal.log()` する。
3. `wal.py:1585-1592` が `WalRecord` を作り、`:424-428` が `{variant, stage, env_tag, ts, payload}` を書く。`model.py:28` の commit 定数と一致する。
4. `reflux_result_evidence.py:594-598` は attempt を payload から読み、`:629-669` が projection と source WAL bytes の一致を検査する。
5. `reflux_formal_consumer.py:1030-1041` の順で FC05C、FC06、verifier policy、FC07 に到達する。計画どおり `:861` を `terminal["stage"] == STAGE_COMMIT` に直せば stage が通り、`:864` は payload の `verify_configs` を読む。
6. 全判定通過後は `:1056-1082` で `P6Unavailable` と receipt が発行される。

影響: valid accepted projection の report reason は FC07 から P6Unavailableへ変わり、`formal_receipt_sha256` と `evidence_root_sha256` は null から実 digest になる。

分類: nit

### ただし certified 選択や完全な本番 projection producer が復活するわけではない

種別: real

根拠: production API は `p3_autonomous_workload_trial.py:428-437` の `OriginProducerInputs` として result bytes/evidence root を外部から受け、`:1664-1665` で consumer へ渡す。repo 内の `OriginProducerInputs(...)` 構築は `test_p3_autonomous_workload_trial.py:10622` だけである。また `reflux_result_evidence.py:431-442` の writer に production caller はなく、repo 内 caller は test のみ。さらに成功後も consumer は `reflux_formal_consumer.py:1070-1082` で P6Unavailable、client は `reflux_origin_client.py:259-276` で `OriginSealed(aborted=True)` を台帳へ書く。

影響: この修理で変わるのは FC07 後の report/projection 参照であり、certified 選択集合と台帳の aborted terminal は変わらない。

分類: scope 外（裁定パッケージ候補）

### rejected 側の production abort は修理後も FC07 で止まる

種別: real

根拠: production abort payload は `pipeline.py:1071-1075` と `:1204-1215` の `{reason, error?, build_attempt_id, ...}` である。`candidate_attributable` と `witness_class_sha256s` の production producer はなく、`reflux_source_closure.py:86` も別名 `wal.abort.payload.witnesses` を記す。stage 修正後は `reflux_formal_consumer.py:867` を通るが、`:868-877` の attribution、truncated、witness 一致で FC07 になる。

影響: rejected report は FC07、receipt/evidence-root 参照は null のままで、certified 選択には入らない。

分類: scope 外（裁定パッケージ候補）

### plan に gate・互換層・reason code の scope 超過はない

種別: refuted

根拠: `s2-plan.md:42` は `_validate_wal_outcomes()` の他判定と `_wal_field()` を不変とし、`:172` は terminal exact-key/type gate、helper、reason code を追加しない。旧 root `kind` の両受けもなく、production 定数 import、2 stage 比較、fixture/test/pin 同期だけである。

影響: FC07 の terminal kind 判定以外の受理集合、reason code、台帳 schema は変わらない。

分類: nit

### fixture terminal の exact production 外枠を直接読む semantic assertion は欠けている

種別: real

根拠: `test_reflux_origin_fixture_builder.py:321-335` は trigger record の outer/payload key 集合を exact に検査するが、terminal record は検査しない。段 2 の正例 `s2-plan.md:141-170` は手組み commit、負例 `:121-139` は手組み legacy record であり、fixture 自身から root `kind` と root payload fields が消えたことを意味で固定しない。baseline hash は exact bytes を固定するが内容の意味は表さない。

影響: 現 plan の値は正しいが、将来 golden を機械更新した際に hybrid fixture を許しても report/台帳 test が理由を示さず通る可能性が残る。

分類: nit

## 総括

must-fix:

- `reflux_origin_fixture_baseline.json` と `test_reflux_result_evidence.py` の 7 literal 更新を core 修理と同じ変更単位に含める。
- 親の実行対象へ `orchestrator/tests/test_reflux_originless_compatibility.py` を追加し、保守的閉包を 10 から 11 file にする。

親が段 4 で裁定すべき択一:

- pin 更新を scope に含めるか、既知の 5 test red を受け入れるか。推奨は含める。
- test 集合を保守的 11 file にするか、挙動最小の 9 file に削るか。推奨は間接統合を含む 11 file。
- 実装子を 1 本のままにするか、core/pin に分けるか。推奨は 1 本。
- DW-G05 を「accepted terminal が FC07 を通って P6Unavailableへ進む」と限定するか、「certified 選択が復活する」と書くか。前者だけが現物に合う。
- rejected witness producer と完全な production result-evidence producerを本 wave に広げるか。確定 scope に従い、今回は scope 外の限界として記録するのが妥当。

pytest は実行しておらず、緑とは判定していない。