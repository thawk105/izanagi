## 閉じた所見と実装

実装は完了しています。ただし pytest が未実走のため、最終的な `closed` 判定は申告しません。

- F0: probe の Python/PBS を `dispatch-required` として [admission_registry.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2228-fix1/tools/pegasus/admission_registry.json:190) に登録。
- O1/O2: record と admission を production の `require_condition_gate_family()` で再検証。arm、macro、status、request digest、issuer、canonical ID/digest、record IDs を結合。
- 現行 pin 対照: clean な現行 pin、要求 pinとの差、production `assert_pinned_clean` の traceback、関門発行物 0 件を機械判定し、repro の `ok` 条件へ追加。
- 中止系例外: `KeyboardInterrupt`、`SystemExit` などを捕捉せず伝播。
- fixture: M2/M3/M5 を observer 経由の production 発行物へ変更。M5 は `_run_sweep()` 本体を通過。
- run binding: 全 payload に共通 run UUID、PBS job ID、process IDを追加。publish 失敗時は次 driver を走らせず rc=4。
- PBS: stdout/stderr の実 FD path が repo 外の regular file か検査。
- Git: 指定された全 `GIT_*` 変数を最初の Git 操作前に unset。

## 閉じなかった所見と理由

コード上の未実装所見はありません。

ただし計算ノード child が起動できなかったため、F0およびレビュー所見を検査実走で閉じることはできませんでした。PBS の実環境での FD path 検査も未確認です。

## 変異登録の再確認

- M1、M4、M6、M7: 照準を維持。
- M2: production 再検証を外す変異へ再照準。status 検査だけを外す変異は、production が導出する admission 判定と重複するため単独赤理由にできません。
- M3: admission と exact record IDs の結合を外す変異へ再照準。無関係な production admission だけを混ぜる fixture としました。
- M5: completed、gate、committed を成立させ、`aborted` だけを赤理由として `_run_sweep()` で検査。
- 全 fixture は production 発行物を observer で取得します。M2 の負例は発行後の record digest 1項目だけを改変します。

## 走らせた検査 (nodeid と rc)

- `orchestrator/tests/test_t2228_driver_gate_liveness_probe.py` 全体: rc=16。`qstat -Q` preflight failure、child未起動。テスト結果ではありません。
- `orchestrator/tests/test_hooks.py::test_bash_pegasus_execution_inventory_is_synchronized`: rc=16。同じく child未起動。
- production 発行物の捕捉・再検証・中止系例外伝播 smoke: rc=0。
- `_run_sweep()` の green/aborted 分岐 smoke: rc=0。
- run binding と publish 即時停止 smoke: rc=0。
- `git diff --check`、Python module import、registry JSON parse: 各 rc=0。

## 未実走・未確認

- 上記2つの pytest 範囲。
- PBS job body の計算ノード実走。
- s1、repro、sweep の3 driver実走。
- `bash -n` は admission guard に拒否されたため未実走です。

## 波及可能性の静的列挙

- probe を直接起動する所有外 caller は新しい必須引数 `--pbs-job-id` が必要です。所有 PBS caller は更新済みです。
- qsub の stdout/stderr が pipe、削除済み file、repo 内 fileの場合、jobは fail-closedになります。
- JSON consumerには `run_binding` と `pin_mismatch_before_gate` が追加され、`used_for_ok` は真になりました。既存 `failed_before_gate` は互換のため残し、意味を期待 pin mismatch に強化しています。
- admission registry consumerは2 artifactを計算ノード専用として扱います。
- shared fixtureへの変更はありません。
- production codeは変更していません。

## 総括

所有された4 pathだけを変更しました。commit、push、docs編集、production変更はありません。実装と軽量 smoke は完了していますが、正式 pytest と計算ノード実走ができていないため、最終 `closed` ではなく「実装済み・未実走」です。