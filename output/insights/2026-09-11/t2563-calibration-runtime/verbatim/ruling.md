# T-2563 段4裁定・plan v2

- 段3 a/bともrc0、出力検査rc0。親brief/planを独立に攻撃した。
- real: gflags自動target選択バグ。親の未使用target仮説を撤回。ライブラリ意味を変える修理はscope外、実装しない。
- real: 各120sの3copyは独立。全終了・全成功→既存pristine検証→build→単独測定の順序を維持できる。
- refuted: 予約上限が枠を超えることを、実時間短縮の実験禁止へ一般化する結論。
- 採用候補は3copyだけの並行化。新しいcache・scheduler・計測基盤・検査gateを作らない。
- 同条件mocc rr50 t48、既存submit、before1回/after1回を上限とする。新しいprotocol/workloadを追加しない。旧989271は同条件比較の代替にしない。
- 各jobでgflags/glog/CCBench fresh build各1、3copy、pristine検証1、較正標本・各probeを維持。成功判定と単独性は既存契約。全体Elapseと処理回数を比較し効果が示せなければ実装を残さない。
- 測定中にsource/docsを変更しない。beforeはwave起点固定、afterはauthor候補commit固定。要求7200s・全timeout・標本数固定。
- 時間式は未解決。現最大枠の部分和7330は実時間の下限ではない。CLI4990+wrapper reserve600を別途要求するconsumerも維持する。
- 効果が確認できても、時間式・既存consumerの整合を閉じず採用/landしない。実測済みprefixで代替する等の予算契約変更を暗黙に行わない。
- 実装所有はtools/pegasus/certify_calibration.sh、既存orchestrator/tests/test_pegasus_calibration_workload.pyだけ。test_pegasus_tools.pyはconsumerとして検査。最大production追加40行/既存test追加100行。超過時は報告。
- 正例: 3依存が全成功なら既存pristine検証が1回、同じ3sourceを消費し同じbuild/較正を行う。
- 拒否: 1copyでも失敗すれば全起動copyを回収し、検証・build・較正へ進まない。新しい受理/拒否条件は加えない。
- 変異事前登録: M1=copy終了waitの削除→実際の重畳/完了barrier検査でkill。M2=非0copyを無視→後段実行禁止検査でkill。具体的置換anchorと期待node集合はauthor後・変異前に一意性確認する。
- 段4直前inbox/現spoolを再照合、T-2563の追加裁定なし。T-2518はdocs-onlyでcode所有重複なし。
