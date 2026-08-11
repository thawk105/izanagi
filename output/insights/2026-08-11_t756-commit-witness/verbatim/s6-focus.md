fix 後の production 経路に新たな fail-open は見つかりませんでした。R1 系と R2-1/R2-2 は閉じています。一方、mutation 事前登録に関する R2-3/R2-4 は commit `c3d24655` では閉じていません。

## 所見ごとの対応表

| 所見 ID | 判定 | 根拠 file:line | 備考 |
|---|---|---|---|
| R1-1 | closed | `orchestrator/campaign/s2_verify_calibration.py:57-58,122-132`、`orchestrator/campaign/pipeline.py:230-253` | S2 は pipeline の一意・非負整数 parser を共有し、main/batch の欠落・不正と batch 非0を verifier 前に拒否する。 |
| R1-2 | closed | `orchestrator/campaign/pipeline.py:277-281,323-333,951-965` | 不在・非directory・`listdir` の `OSError` が `_TraceDirUnavailable` となり、構造化 `trace-no-commit-witness` abortへ帰属する。 |
| R1-3 | closed | `orchestrator/tests/test_campaign.py:6170-6181,6293-6318` | 残骸時の subprocess 0回を spy で固定し、WAL の reason/files/workload も検査する。M11 の赤理由が一意になった。 |
| R1-4 | closed | `orchestrator/tests/test_verifier.py:609-639` | 元 nodeid の no-witness `certified=True` characterization を復元し、witness 付き indeterminate テストを別 nodeとして維持。 |
| R1-5 | closed | `orchestrator/tests/test_verifier.py:759-798` | no-witness 出力を実行時生成した期待値ではなく、独立 literal JSON bytes と完全一致させている。 |
| R1-6 | closed | `orchestrator/campaign/pipeline.py:262-268,931-934,979-984` | 検算したが破れなかった。`_TraceRunResult` は属性で消費され、fix は型や production consumer を変更していない。 |
| R1-7 | closed | `orchestrator/verifier/core.py:26-40` | 検算したが破れなかった。`replace` 後の同一 `Integrity` に witness note と既存 integrity 情報が載る順序を維持している。 |
| R1-8 | closed | `orchestrator/verifier/report.py:42-75` | 検算したが破れなかった。fix の変更ファイルに `report.py` と ladder はなく、凍結 JSON の serializer/外側照合は不変。 |
| R2-1 | closed | `orchestrator/tests/test_verifier.py:827-844`、`orchestrator/verifier/cli.py:66-69,99-104` | 不一致 witness=3 に対して `certified=False`、`indeterminate`、literal note、rc=3を固定。CLI 結線削除は生存しない。レビュー記載のrc=1ではなく、現行契約上 indeterminate はrc=3が正しい。 |
| R2-2 | closed | `orchestrator/tests/test_verifier.py:759-798` | self-fulfilling 比較とは独立した literal byte pinを追加済み。 |
| R2-3 | partial | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-trace-v2/s4-adjudication.md:112`、`orchestrator/verifier/core.py:35-39` | delta の実装は依然 `core.py` だが、事前登録 M05 は `report.py` を指したまま。新CLIテストも符号反転を検出するため検出力は増えたが、注入参照は未修正。 |
| R2-4 | partial | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-trace-v2/s4-adjudication.md:106-121`、`orchestrator/tests/test_verifier.py:693-740,827-844` | fix は検出 node を追加・強化した一方、M01〜M05 の完全な `expected_nodes` 集合は更新していない。複数 node 帰属は残り、むしろ新CLI nodeも集合へ含める必要がある。 |

`regressed` と判定する所見はありません。

## 新規欠陥の検査

新規 blocker は見つかりませんでした。

- production fail-open: 検算したが破れませんでした。`Integrity.clean()` の witness 一致連言は `model.py:146-161`、`certified` の integrity 必須条件は `model.py:211-214` に残っています。pipeline も witness 欠落拒否 `pipeline.py:1008-1015`、batch 非0拒否 `:1016-1022`、witness を verifier に渡した後の非certified拒否 `:1023-1027,1051-1061`を維持しています。
- 既存テストの緩和: 検算したが破れませんでした。skip/xfail・テスト削除・期待値緩和はありません。残骸テストの書換えは同じ拒否期待に subprocess 0回を加えた強化であり、R1-4 は旧characterizationの復元です。
- `report.py`: commit の変更対象5ファイルに含まれず、`git diff c3d24655^ c3d24655 -- orchestrator/verifier/report.py` は空でした。現行 serializer は `report.py:42-75` のままです。
- S2 import: 検算したが破れませんでした。S2 は fix 前から `pipeline` の `CorrectnessWorkload`、`S2_FLAGS`、`_parse_abort_counts` を importしており、今回は同じ依存辺へ `_parse_commit_witness` を足しただけです（`s2_verify_calibration.py:57-58`）。`pipeline.py:26-57` から S2 への逆 import はなく、循環も依存方向の新規逆転もありません。
- `trace_dir` 正常経路: 検算したが破れませんでした。`evaluate` は `tempfile.mkdtemp()` で存在するdirectoryを作って直後に渡します（`pipeline.py:927-934`）。新検査 `:323-335` はその空directoryを通し、消失・非directory・走査不能だけを拒否します。

## 残所見

### F-1 / M05 の注入参照が旧位置のまま

- 判定: **real**
- 根拠: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-trace-v2/s4-adjudication.md:112`、`orchestrator/verifier/core.py:35-39`
- 具体的な失敗経路: 登録どおり `report.py` の delta 式を置換しようとしても anchor が存在せず、mutation harness は注入不能として停止する。`core.py:39`へ再照準すれば複数テストが符号反転を検出する。
- 深刻度: **must-fix（mutation 本走前）**。production soundness の blocker ではない。
- 成果物影響: mutation ledger の M05 が `KILLED` ではなく anchor mismatchとなり、14件の受入根拠を成立させられない。
- 処方: M05 の対象を `orchestrator/verifier/core.py:39` に変更し、符号反転で落ちる全 nodeを登録する。

### F-2 / M01〜M05 の期待失敗 node 集合が未確定

- 判定: **real**
- 根拠: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-trace-v2/s4-adjudication.md:106-121`、`orchestrator/tests/test_verifier.py:693-740,827-844`
- 具体的な失敗経路: witness gateやdelta/schemaを壊す一変異が direct verifier、serializer、CLI、pipelineの複数 nodeを落とす。単一 nodeだけを `expected_nodes` にすると、検出できていても集合完全一致に失敗する。
- 深刻度: **must-fix（mutation 本走前）**。production の受理集合には影響しない。
- 成果物影響: M01〜M05 が `KILLED` ではなく `MISMATCH` となり、mutation acceptance artifactの値と参照 node集合が不正になる。
- 処方: fix後 collectionを基準に各変異の完全な失敗 node集合を登録する。特に新設したCLI mismatch nodeを該当変異へ追加する。

## 総括

production fix は **GO** です。S2 の偽緑経路、trace directory診断、M11検出力、旧characterization、CLI結線、byte pinはいずれもコードで閉じており、新たな fail-open・凍結 evidence破壊・import循環・正常経路の過剰拒否は見つかりませんでした。

ただし wave 全体の mutation acceptance はまだ **NO-GO** です。R2-3/R2-4として、M05の注入位置とM01〜M05の完全な期待 node集合を、本走前に修正する必要があります。