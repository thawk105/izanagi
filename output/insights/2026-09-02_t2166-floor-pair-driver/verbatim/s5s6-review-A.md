## 総括

- 静的レビューの結論は差し戻しです。
- 最重要は、production identity が callable の自己申告文字列であり、偽測定から `generated` を作れる点です。
- calibration は rejected 成果物と calibration 外の `records` を受理でき、測定動作点をずらせます。
- contract、build receipt、protocol、site には実体との意味的束縛がありません。
- pytest は実走しておらず、親の実測件数を本レビューの緑とは扱っていません。

## 所見

1. **主張:** production adapter 判定は偽装可能で、RULING の「非 production 測定から candidate floor を出さない」を満たしません。

   - **根拠:** identity は `__module__` と `__qualname__` の連結にすぎません（[floor_pair_driver.py:1266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:1266)）。`run_window` は高位の `measure_fn` を受け取り、その名前と結果内の名前だけを比較し（同 :1572、:1630、:1678）、finalizer も文字列だけを production 名と比較します（同 :1969）。Python 関数の両属性は書換え可能なので、偽関数に production と同じ名前を付け、任意の `MeasurementResult` を返せます。
   - **テストの穴:** mutation 09 の偽関数は自分の素の名前を申告するだけです（[test_floor_pair_driver.py:724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_floor_pair_driver.py:724)、同 :1091）。production 名を偽装する負例がありません。
   - **影響:** 偽関数が candidate 2 セッションへ同じ値を返せば `D=0`、最終 `candidate_floor=0` を生成できます。受理集合が非 production 測定まで広がり、床値を小さくできます。
   - **提案:** 権威ある `run_window` から `measure_fn` seam を除き、常に `_measure_with_runner` を呼んでください。テスト注入は裁定どおり `runner.measure_point` 直下だけに置き、production 名を偽装した高位関数が拒否される負例を追加してください。

2. **主張:** calibration の意味束縛が不完全です。rejected calibration と calibration に一致しない `records` が通ります。

   - **根拠:** `load_verified_calibration` は schema を検証して返しますが、`quality.status == "accepted"` を要求しません（[calibration_verify.py:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/calibration_verify.py:116)）。schema 自体は `rejected` を正規値として許します（[schema_v2.py:472](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/calibrator/schema_v2.py:472)）。driver の照合は env、threads、clocks、workload だけで（[floor_pair_driver.py:979](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:979)）、calibration に存在する `saturation.records` を `perf.records` と比較しません。ところが測定には spec 側の `records` をそのまま渡します（同 :1292）。
   - **テストの穴:** calibration fixture は `quality` と `saturation` 自体を持たず（[test_floor_pair_driver.py:203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_floor_pair_driver.py:203)）、mutation 04 は threads 不一致しか試していません（同 :499）。
   - **影響:** 校正が棄却した動作点、または異なる record 数で測定できます。cache/contention 条件が変わるため `D` と上限が小さくなり得ます。
   - **提案:** required mode では exact `CalibrationV2`、`quality.status == "accepted"`、非 null `saturation` を要求し、全 cell の `perf.records == calibration.saturation["records"]` を検査してください。rejected と records 不一致の単独負例も必要です。

3. **主張:** 複数の凍結 field が実体を見ない宣言に留まり、RULING が採用した artifact の意味的束縛が完了していません。

   - **根拠:** `execution_contract` と `build_receipt` は hash、HEAD bytes の確認後に内容を捨てています（[floor_pair_driver.py:944](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:944)）。`source_commit` は40桁の構文検査だけ（同 :553）、`cell.protocol` も ID として読むだけで runner 引数にも binary receipt 照合にも使いません（同 :688）。`environment.site` も parse されますが、live 検査は env_tag の片側比較だけです（同 :1369）。これは RULING が real・採用とした contract/build receipt の意味束縛（[RULING.md:25](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2166-floor-pair-driver/RULING.md:25)）に届きません。
   - **テストの穴:** fixture の contract と receipts は意味のない一行 JSON でも受理されます。全 field 必須テストは「存在」しか検査せず、値と実体の関係を守りません。
   - **影響:** genuine だが無関係な receipt を、別 binary、別 protocol、別 source の測定へ添付できます。異なる実体の `D` が対象 stratum の値として受理され、成果物の参照も虚偽になります。
   - **提案:** execution contract を live registry の exact contract と照合し、build receipt から binary SHA、source、trace、protocol の導出可能項目を実体と比較してください。`site` は live site と比較し、意味を証明できない field は保証として残さないでください。

4. **主張:** production の env_tag 導出機構はテストされていません。

   - **根拠:** production は `_machine_env_tag_for_site` を呼びます（[floor_pair_driver.py:1336](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:1336)）。一方、共通 helper はこの関数自体を stub し（[test_floor_pair_driver.py:674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_floor_pair_driver.py:674)）、mutation 06 も同じ高位関数を stub しています（同 :864）。
   - **影響:** registry 選択、未知 site 拒否、required/none contract の導出を壊しても対象テストは通り、異なる環境の測定を受理して `D` を変える回帰を守れません。
   - **提案:** `_machine_env_tag_for_site` 自体を通し、その直下の registry/contract だけを fixture 化してください。compute、OTHER、login、suspect、曖昧 registry の正負例が必要です。

## 恒真だと判断した検査

- calibration の env_tag と clocks の再比較（`floor_pair_driver.py:984-989`）は、production verifier が同じ入力との一致を既に要求します。none mode はその前に `calibration is None` で拒否されるため、この2分岐は production 入力では到達不能です。
- session count の Counter exact equality 後にある `any(count != 1 ...)`（同 :1867-1876）は、canonical plan の session ID が一意なので常に false です。exact 1 回性は前段の Counter 比較が既に守っています。成果物影響なしの nit です。
- `environment_mismatch in SESSION_STATUSES` のテスト（`test_floor_pair_driver.py:300-304`）は宣言集合だけを見ています。live mismatch は出力確保前に例外となるため、実装からこの session status の record は一件も生成されません。nit ですが、テスト名が実効機構を過大に見せます。
- callable identity 比較は、production adapter と通常の test fixture の双方が比較相手と同じ名前を自分で記入する自己申告です。実体を呼んだ証明ではありません。
- `NOT_PROVEN` と module docstring の包含検査も宣言同士の整合だけです。列挙された5項目自体は正確ですが、identity の自己申告性と opaque receipt は限界に記載されていません。

## 検査したが問題なしと判断した点

- production adapter の主要テストは実際に `_measure_with_runner` を通し、stub は正しい `runner.measure_point` 境界にあります（`test_floor_pair_driver.py:611-671`、:946-989）。callee 名も本番と一致します。
- 非 complete、欠測、rep 不足、失敗、非有限、非正値は一件でも全体未生成となり、成功分だけを抽出して上限を小さくする経路は見つかりませんでした。
- `extime`、`reps`、`ycsb_max_ope` を含む frozen runner 引数は明示され、`p2_2`、`p3_s4_loop`、`between_run_floor` の定数や dataclass default から入る経路はありません。
- 除算や減算が非有限になれば未生成へ倒れ、`upper >= 1` は保持したまま candidate floor を生成しません。表示用丸めもありません。
- window artifact は live env 検査後、測定前に `O_CREAT|O_EXCL|O_APPEND|O_WRONLY|O_NOFOLLOW` で確保されます。例外時にも削除・改名せず、同一 path の再実行は測定前に止まります。
- HMAC 順序、同一 candidate の2セッション、共通 reference、closed strata の全件最大、raw median からの再計算は実装されています。
- 「証明していないこと」の既定5項目は実装と一致しています。create-only と非 strip binary の symbol 検査について、実際に証明している範囲を過小記載している箇所も見つかりませんでした。