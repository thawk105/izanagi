[1] 両 shell の実効 rratio 受理集合は exact に一致する / 投入側は既定 `50` と最終代入値を `5,20,50,80,95` に逐語比較し、job body も必須 env を同じ 5 文字列へ逐語比較する (`tools/pegasus/submit_certify.sh:18,27-44`; `tools/pegasus/certify_calibration.sh:154-164`) / quoted の `05`、`+5`、前後空白、全角 `５`、literal 改行付きは拒否、`--rratio=95` は unknown argument、引数順序は任意。呼出元の unquoted 分割や command substitution が事前に `5` へ変換した場合だけ canonical `5` として通る / 成果物影響 1 行: sanctioned 経路が記録・計測する値は `{5,20,50,80,95}` のみで、両側の食い違いはない / 自己判定: refuted / nit

[2] 複数 `--rratio` は last-wins なので、shadow された不正値を含む argv 自体は通る / validation は全引数処理後に一度だけ行われる (`tools/pegasus/submit_certify.sh:27-44`) / `--rratio 51 --rratio 5` は通り、逆順は `05` で拒否される / 成果物影響 1 行: pre-submit、receipt、qsub env、job-result は最終値 `5` のみを記録し、certified 選択・report・台帳値は変わらない。先行した `51` は参照に残らない / 自己判定: real / nit。重複拒否 gate の新設は本題に不要なので求めない

[3] accepted と呼ぶ条件の緩和はない / 差分の file header は test と 2 shell だけで、`report.py`、`schema_v2.py`、`cli.py` は無変更 (`artifacts/s5-diff.patch:1,214,235`)。job は従来どおり `--certify`、receipt、binary hash を渡す (`tools/pegasus/certify_calibration.sh:844-869`) / env・argv・既定値から quality/schema/publish 判定を迂回する変更を想定したが、追加値は workload へ伝播するだけ。CLI 直接起動の任意 rratio は既存かつ scope 外 (`ruling.md:87-96`) / 成果物影響 1 行: rr5/rr95 も既存の accepted 条件を満たした JSON だけが publish 対象となる / 自己判定: refuted / nit

[4] 既存の受理・拒否挙動に退行は見つからない / rr50 既定 (`submit_certify.sh:18`)、protocol gate (`submit_certify.sh:45-50`; `certify_calibration.sh:165-172`)、legacy tolerance 拒否 (`submit_certify.sh:22-25`; `certify_calibration.sh:173-176`)、clean 判定 (`submit_certify.sh:89-98`; `certify_calibration.sh:191-197`)、create-only staging (`submit_certify.sh:110-118`; `certify_calibration.sh:37-45`)、preflight 4 capture (`submit_certify.sh:129-142`)、receipt fields (`submit_certify.sh:144-183,233-263`) は差分外で、再代入・順序・quoting も不変 / rr20・rr50・rr80、protocol 不正、dirty tree、既存 staging、preflight failure を再検討したが変更 hunk に到達しない / 成果物影響 1 行: 既存 3 workload の receipt field、拒否時点、publish 参照は従来どおり / 自己判定: refuted / nit

[5] job body の exact-set テストは、論理または直前正規化を壊しても全 assertions が成立する / `_rratio_gate_values` は比較 literal だけを抽出し operator と直前代入を見ず、job 実起動負例は `+5` だけである (`orchestrator/tests/test_pegasus_calibration_workload.py:36-43,78-154`)。正例 5 件は submitter dry-run までで job body を実行しない (`test_pegasus_calibration_workload.py:677-700`) / 具体的変異 A: `certify_calibration.sh:156` の最初の `&&` を `||` にすると全 5 値を拒否するが、literal 集合、bash parse、`+5` の error は不変。具体的変異 B: gate 直前へ `IZANAGI_CALIBRATION_RRATIO=${IZANAGI_CALIBRATION_RRATIO#0}` を挿すと job 側だけ `05` を受理するが、静的集合と `+5` 負例は不変 / 成果物影響 1 行: A では rr5/rr95 を含む accepted JSON が一件も得られず、B では非 canonical `05` 由来の run が rr5 として receipt・登録成果物へ進み得る / 自己判定: real / must-fix。job body の正例と複数の非 canonical 負例を test-only で固定することは、本題の accepted calibration 取得に必要であり、新しい production gate ではない

[6] 「error 文字列だけ更新して比較を壊す」変異は捕捉される / 両 gate の literal 集合を exact 比較し、submitter の全 5 正例を dry-run し、双方の error 文字列も検査する (`test_pegasus_calibration_workload.py:80-88,144-154,501-526,677-700`) / 旧 3 値比較のまま message だけ 5 値化すれば static 集合と rr5/rr95 正例が失敗し、message だけ旧値へ戻せば runtime 負例が失敗する / 成果物影響 1 行: error 編集だけで rr5/rr95 の拒否を隠し、誤った certified 選択を作ることはできない / 自己判定: refuted / nit

[7] 親裁定への実装違反はない / job gate は `write_failure` 準備後の元位置で value/message だけ更新 (`artifacts/s5-diff.patch:218-234`; `ruling.md:31-33`)。旧 `95` 拒否期待だけが指定どおり未登録値負例へ置換され、skip・xfail・削除・緩和はない。scheduler path test の既存 assertions は維持され、rr50 の no-option qsub pin も残る (`test_pegasus_calibration_workload.py:649-674`)。差分は裁定された 3 file のみ (`ruling.md:135-145`; `artifacts/s5-diff.patch:1,214,235`) / gate 移動、所有外編集、新台帳、production 一般化を探したが該当なし。README は親所有の事前更新である / 成果物影響 1 行: failure provenance、既存期待値、所有境界、成果物参照はいずれも裁定どおり / 自己判定: refuted / nit

pytest は実走していない。上記は指定資料の静的レビューと shell 条件式の局所確認による。

## 総括

must-fix は 1 件。  
[5] job body の exact-set テストが operator 破壊と `05` 正規化変異を見逃す。  
現行実装の受理集合自体は両側とも exact `{5,20,50,80,95}` である。