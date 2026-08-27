Layer3 のエラー優先順位を修正しました。

| 契約 | 判定 | 現在の挙動 |
|---|---|---|
| receipt 不整合の専用診断 | closed | marker 付き certifying report では schema より先に同値条件を検査 |
| historical admission の専用診断 | closed | receipt 条件を満たした後、`admission_status=admitted` を先に検査 |
| certifying report の marker 禁止 | closed | receipt・admission が正しければ schema 検証へ進み、marker を拒否 |

受理の含意: marker のない certifying report は、receipt 非 null・admission admitted・その他の schema 条件を満たせば従来どおり受理されます。

拒否の含意: marker 付き certifying report は、前提不足なら専用診断、前提充足後なら `layer3 schema 検証に失敗` で拒否されます。

差分は [layer3_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-author/orchestrator/campaign/layer3_report.py:236) のみです。既存診断を helper 化し、marker 付き certifying 入力だけ schema 前にも検査しています。schema conditional、旧v3互換、reason enum、受理・拒否集合は変更していません。テスト、docs、tracked output、凍結 bytesにも差分はありません。

通る正例は、marker のない certified report と、`certifying_input=false` の historical marker reportです。`git diff --check` は rc=0。fix3 だけが unstaged で、既存統合差分は staged のままです。stage/commit 操作はしていません。

実走要求した node:

- `test_reader_rejects_certifying_input_without_acceptance_receipt`
- `test_reader_rejects_certifying_historical_admission`
- `test_reader_rejects_historical_marker_on_certifying_input`

`python3 tools/run_tests.py` は wrapper rc=16、`child_started=false`、`child_rc=null` でした。`qstat -Q` preflight の infrastructure failure のため3 nodeとも未実走であり、緑とは報告しません。波及は上記の限定的な診断順位変更だけです。

## 総括

実装上の3契約は closed です。検証実走だけは dispatch infrastructure failure により partial のままです。
