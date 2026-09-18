# 段4裁定・plan v2

## 採否とscope
- D2148項5と裁定inboxを再確認。nodes=5採用を維持する。
- 相談A1/B1はreal。A1/b10-shapeのdefault home consumerと候補headの同node排他喪失は具体的反例を持つ。全launcher変更には広げない。
- 相談A2はreal、mixed path両方向の対照をprobeへ入れる。保持完了通知→挑戦→解放の順序を守り、実bench_lockを呼ぶ。
- 相談A3/B2はreal、候補job bodyのrun-workload子への到達・継承確認を既存harnessの局所拡張で行う。模擬予約/依存/stagingを明記し、compute上の実flockと別証拠とする。
- 相談A4/B4はreal対処済み。policy pinと2 test fileのfixture閉包を同じ単位で変更し、本来の負例理由へ到達させる。
- 相談B3を採用。候補実測は行い、mixed-path反例が成立すれば候補を恒久採用せず既存job bodyを保持する。「共有homeへ戻さない」は実測前に候補採用を義務付ける意味ではない。
- 相談B5採用。既往時短値の比較条件差を添える。今回probeはCC性能測定・正式認証・約8分の再現ではない。
- worker/task固有lockは既存制限で今回の変更起因ではない。追加修復はしない。独立scheduler jobの同居保証も今回probeだけで立証しない。
- 最終成果はpolicy/pin/fixture閉包と実測採否材料。候補が不採用ならjob body/候補専用testを最終diffへ含めず、候補patch/script/結果をjob dirで保全する。

## 実装単位と規模
- author 1単位、所有はpolicy、certification test、job-contract test、共通job body、repo直下の一時probe .py/.pbsのみ。
- production候補はjob bodyに固定scratch_base/bench.lockのexportを一行足す程度。汎用lock/worker/別launcherを変更しない。
- probeは2ノード短時間予約用の1回限り資材。real bench_lock、現物candidate job-body由来path、同node別process/scratch、別node同期、default両方向を確認。新しいframeworkを作らない。
- 親がrun_tests・probe・変異・受入を実行。子の静的確認を緑としない。正しさ/anomaly/proof gateは不変。

## 変異事前登録
- M1: A-2 policy nodes 5→1。literal bytes/nodes pinが検出。実走nodeはpolicy contract testへ絞り別理由maskを避ける。
- M2: _validate_verify_fanout_hostsのcount拒否を無効化。A2/A6の不足/過剰の既存実効負例で検出。anchorと期待nodeの全件は実装後固定する。
- 候補lockを出荷する場合のみM3/M4: export削除、job固有scratchへの置換。run-workload到達済みの継承試験で検出。出荷しない場合は候補probeの比較対照として記録し、本走production変異対象に含めない。
- 受理を縮小する変更ではない。5ノード正例と単一ノードfixtureの既存契約を共存させる。pin testを自己hash比較へ緩めない。
- 実装後、単一理由性を再確認して既存mutation_harnessで固定commit・独立cloneを走る。実装面差分があるのでmatrix免除なし。
