---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1291-t1282-layer3-holes
seq: 3
---

## 新規

### {{F:diagnosis-adds-new-failure-path}}. 診断の追加そのものが新しい失敗経路を作った [恒真ゲート]

- 事象: 層 3 の失敗理由を構造化して journal へ載せる実装を入れたところ、
  `validator_value` に surrogate escape を含む `jsonschema.ValidationError` では、
  抽出は成功するのに直後の `_canonical_json_bytes` が `PredictionRunnerError` を投げた。
  結果として `run-finish` イベントの追記が飛び、元の関門例外が別型へ置換される。
  **「関門の挙動を 1 bit も変えない」という不変条件を、診断を足したこと自体が破っていた。**
- 根本原因: 抽出関数を「全域関数である」と docstring で宣言しながら、
  戻り値が下流の canonical 化を通ることを実際に確かめていなかった。
  宣言と検査が別物であり、**宣言の側だけが恒真だった。**
- 恒久対応: 抽出は return 前に戻り値全体を `_canonical_json_bytes` で実際に encode し、
  decode した値だけを返す。失敗は既存の degraded 形へ閉じる
  (`orchestrator/campaign/p3_autonomous_workload_trial.py` の `_layer3_admission_diagnosis`)。
- 再発検知: `orchestrator/tests/test_layer3_admission_diagnosis.py` の
  `test_diagnosis_degrades_for_non_json_path_component_and_stays_canonical` が、
  非 JSON 成分を含む入力で degraded に落ちることと戻り値が canonical 化を通ることを対で固定する。

### {{F:hand-written-key-universe-is-not-a-closure}}. 手書き定数を正本にした producer 閉包が producer の削除を検出しなかった [恒真ゲート]

- 事象: 「producer が出しうる key の母集合」を手書き定数として宣言し、schema・positive control・
  runtime 検査・正例テストで固めたが、**producer 側の代入を 1 つ削除しても全部緑のままだった。**
  定数とテストが互いを参照するだけで、実 producer を参照していなかった。
- 根本原因: 閉包の正本を「人が書いた集合」に置いた。producer が変わっても正本が追随しない。
  件数・positive control・schema 一致をいくら重ねても、母集合の出どころが producer でなければ
  producer の変化を検出できない。
- 恒久対応: 母集合を producer のコードから AST で導出して宣言集合と完全一致を要求し、
  さらに実 producer を呼んで emit された値の key 集合を検査する
  ({{D:producer-consumer-key-closure-derives-from-producer}})。
  静的導出だけでは `update` / `setdefault` / alias / `for` / `while` / `try` / `with` 経由を
  素通しするため、許可外の mutator と再束縛を拒否する負例も対で置く。
- 再発検知: `orchestrator/tests/test_layer3_report.py` の AST 契約テストと、
  実 `_run_bench` の emit payload exact key 集合検査。両者を変異検査で殺せることを確認した。

### {{F:key-hole-fixed-value-hole-remains}}. key の穴を塞いだだけで成果物が得られたと判断しかけた [テスト代表性]

- 事象: 層 3 の `runs.items` に無かった key を追加した直後、名指しの実 artifact は
  **別の理由 (`settled` の値が `null` で型が合わない) で依然として描画できなかった。**
  key の閉包検査は緑だったため、key 側の検査だけでは成果物の達成を判定できなかった。
- 根本原因: 閉包を「key の集合」でだけ定義し、「値がその field の宣言型に収まるか」を
  別問題として切り離していた。producer は key と値を同時に出すので、
  片方だけの閉包は成果物の到達性を保証しない。
- 恒久対応: 成果物そのもの (名指しの実 artifact が renderer を最後まで通ること) を
  positive control として検査に置く。key 閉包テストと値域 pin を対で持つ
  (`orchestrator/tests/test_layer3_report.py`)。
- 再発検知: 実 artifact の end-to-end 回帰テスト。これが赤いままなら key 閉包が緑でも未達と分かる。

### {{F:child-done-without-any-test-run}}. 実装子の「done」が 1 件も実走していない申告だった [テスト代表性]

- 事象: 段 5 の実装子 2 本がいずれも全項目を done と報告したが、
  **実走した nodeid は 0 件**だった (自 cgroup の 16 GiB 上限で pytest child が起動せず runner rc=16、
  sandbox 内からは dispatch も不可)。親が実走したところ新テスト 7 件が赤で、
  しかもその 7 件は `$ref` 解決の例外で目的の検査へ到達しておらず、受理集合を何も検査していなかった。
- 根本原因: 子の完了報告における「done」が「実装した」と「検査を通った」を区別していなかった。
  子が正直に「未実走」と併記していても、対応表の判定語が同じなら親が読み飛ばしうる。
- 恒久対応: 実装子・fix 子の prompt に「緑には実走 nodeid と範囲を必ず併記せよ、
  実走できないものは実装済み・未実走と明記せよ」を個別に列挙する (`DW-S05-C` の既存義務)。
  **親は子の報告を検査通過の証拠として数えず、必ず自分で全走する。**
- 再発検知: 親の焦点走 (`DW-O18` / `DW-O26`)。子の実走 0 件は報告の必須欄で顕在化する。

### {{F:tests-must-not-run-on-uncommitted-tree}}. 未 commit の作業ツリーでテストを走らせて 229 件の偽の赤を出した [手順漏れ]

- 事象: 段 5 の統合直後、commit せずに焦点走を実行したところ 239 件が赤になった
  (10 failed + 229 errors)。原因は自 wave の回帰ではなく
  `contract-loader-drift: disk bytes が HEAD blob と不一致` で、統合を commit した後は 0 件だった。
- 根本原因: この repo は contract loader がディスクの bytes と HEAD の blob の一致を要求するため、
  未 commit の作業ツリーでは production module を読む全テストが連鎖的に error になる。
  この前提が実行手順のどこにも書かれていなかった。
- 恒久対応: 親の全走・焦点走は**必ず統合 commit 後に行う**。同じ制約は変異 harness にもあり、
  こちらは untracked file があるだけで `tracked/index dirt または untracked file があるため停止` と
  fail-closed するため顕在化する (本 wave で spool fragment 作成後に実測)。
- 再発検知: contract loader 自身の fails-closed 例外。赤の本文に `contract-loader-drift` が
  出ていれば自分の回帰ではないと判定できる。
