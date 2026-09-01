## 所見

- **所見:** 同一束縛で再投入された別 submission を fresh run と resume に区別できず、既存 WAL・block record を無条件に再利用する経路がある。
- **根拠:** `orchestrator/campaign/b10_backoff_shape_sweep.py:1449-1508` の campaign identity に submission/cohort ID は含まれず、`:1550-1568` は事前登録束縛一致だけを検査し、`:2362-2390` は過去 record の request ID・nonce が自己整合すれば現在 submission との一致を要求せず、`:2925-2964` で既存 cell を測定済みとして skip する。
- **成果物への影響:** fresh run のつもりでも旧測定値が `judge()` とレポートへ入り、`:2609,2630` では現在 submission と過去 submission の records が同居するため、選択結果・レポート・試行台帳の provenance が変わり得る。
- **提案:** 全相で共有する formal-run cohort ID を submit receipt、campaign identity、WAL、block record に束縛し、明示的に一致した cohort だけを resume するよう親 brief と編集許可範囲を拡張する。

- **所見:** 実装子の「consumer tests 6件」は外部 consumer test に限れば正しいが、要求された全参照一覧としては production inventory と変更対象自身の test が欠けている（nit）。
- **根拠:** 追加参照は `orchestrator/campaign/materializer_admission.py:53`、`tools/pegasus/admission_registry.json:22`、直接の production 呼び手 `tools/pegasus/submit_b10_backoff_shape.sh:83-104,193,213-225`、変更対象 test `orchestrator/tests/test_b10_backoff_shape_sweep.py:19,32` である。
- **成果物への影響:** nit — certified な値や受理集合は変わらないが、所有 surface・参照 inventory の報告が不完全になる。
- **提案:** production 参照4面と対象 test を一覧へ追加し、`acceptance_duration_ledger.json:825` 以下は production consumer ではなく test-node inventory として別記する。

相間 path は、提示された同一-worktree前提では成立する。submitter は `tools/pegasus/submit_b10_backoff_shape.sh:225` で repository root から qsub し、job は `tools/pegasus/b10_backoff_shape_campaign.sh:31-38` で同じ `PBS_O_WORKDIR` と git common dir から導出する。実 checkout の導出値も `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output` だった。別 clone・移設後の worktreeなら common dir が変わるが、今回の明示前提外なので real 所見には数えない。

削除された repo 内 claims directory への残存依存はない。verify/perf は外部 claims を `b10_backoff_shape_sweep.py:2800-2811` で用意し、レポートは `:3047-3058` から `_write_reports()` が親 directory を作る。probe は `:2795-2797` の submission directory、build は `:2880-2884` で campaign layout 前に return する。

親の「campaign WAL/lock を書いていない」は正しい。ただし build cache は `:2867,2880-2883` から `_build_binary()` → `:2507-2522` へ書かれるため、「一切の状態がない」ではなく「移設対象の campaign 状態がない」と読む必要がある。

pytest は実行しておらず、以上は静的検査のみ。

## 総括

real と判定した所見は1件：

- 同一束縛の別 submission を fresh run と resume に区別できず、旧 WAL・測定 record を取り込める。