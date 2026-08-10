判定は **NO-GO**。第2巡は正例を `go` に戻しましたが、同時に「`DENIED` sentinel を出した後で timeout／異常終了した inside」も `go` に通す回帰を作っています。DW-O16/DW-G05 に従い、所見状態と成果物影響を以下に示します。静的検査のみで、親実測の **49 passed** は既知事実として扱いました。

## 所見

### 1. [blocker] F1 は第2巡で regressed — `DENIED` 後の timeout／異常終了が GO

[`_parse_payload_sentinel()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:301) は `executed` と stdout だけを見て、`timed_out` と `rc` を検査しません。[`_paired_command()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:641) はその `denied` をそのまま `inside_blocked=True` にし、[`_paired_verdict()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:80) が `go` にします。

具体例:

```text
outside: REACHED, rc=0
inside:  DENIED|ENETUNREACH, timed_out=True, rc=-9
→ inside_payload_state=denied
→ inside_blocked=True
→ go
```

同様に、sentinel 後の bwrap teardown failureによる非0終了も通ります。第1巡の裁定「timeout は inconclusive」という契約を満たしません。

一方、sentinel の無い単純な bwrap setup failure は `missing` → `inconclusive` であり、これは refuted です。

**DW-G05 成果物影響:** 異常終了した試行を `*_CONTAINED` と記録し、非封じ込め backend を意味 gate の受理材料にできます。

### 2. [blocker] F1/F5 は partial — `denied` 集合が封じ込め原因に限定されていない

[`_CONTAINMENT_ERRNOS`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:55) と [`_WRITE_CONTAINMENT_ERRNOS`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:59) は `ENOENT` を含みます。さらに一般集合は `ECONNREFUSED`、`ETIMEDOUT`、`EAI_AGAIN`、`EAI_NONAME` も受理します。これらは path 誤り、endpoint の一時障害、DNS 障害でも生じ、封じ込め固有ではありません。

S5 system command は errno ですらない一括値 `COMMAND_FAILED` を受理します（[C++ fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1123)、[許可箇所](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1236)）。

- `EEXIST`: 集合外であり refuted
- `ENOSYS`: 集合外であり refuted
- `ENOENT`: 実在する偽 GO 面
- payload 未起動と起動済みは sentinel で区別できる
- ただし「起動して正しく拒否」と「起動後に別理由で失敗」は区別できない

カテゴリ別の狭い errno 契約と、inside の `timed_out=False`、期待 rc、操作後状態の検証が必要です。

**DW-G05 成果物影響:** path・network・tool failure を sandbox 拒否と誤認し、receipt の封じ込め受理集合を拡大します。

### 3. [must-fix] F2 は partial — identity 解決不能時に infinite child を清掃できない

PID verdict 自体は改善されています。pidfile 欠落・不正・identity 不明は `inconclusive`、生存は `no-go`、消滅は `go` です（[`_verdict_descendant()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:159)）。

しかし host PID を解決できなかった場合、[`_cleanup_exact_process()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1019) は何もせず戻ります。outside 正例と inside の双方で、setsid 済み無限子孫を残し得ます。

**DW-G05 成果物影響:** 残存 loop が後続 S6/S7 や同一ノードの測定を攪乱し、receipt の性能・単独性観測を実走条件と食い違わせます。

### 4. [must-fix] F6/R1 は partial — receipt 本体は完全だが `COMPLETED` が非原子的

最終 receipt は temp へ完全書込み・fsync後、hard linkで create-only publishしており、通常経路で「部分 JSON の canonical receipt」が生じるという元所見は refuted です（[`_write_temp()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1833)、[`_link_noreplace()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1809)）。

残る問題は次です。

- `COMPLETED` は最終名を `O_EXCL` で作ってから直接書くため、kill・short write で空／短い marker が残る（[marker publish](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1873)）。
- receipt link 後、marker 完了前に停止すると receipt のみ存在する。
- `PARTIAL.json` は完成後も残り、final receipt に明示的な `state: complete` がない。
- link 成功後に temp unlink と canonical rollback の双方が失敗すると、完全な receipt だけが残る。
- 最終 publish 失敗時は S7 済みの `PARTIAL.json` は残るため、「測定段は終了したが final receipt が無い」は作れる。これは fail-soft 情報としては有用だが、consumer 契約が未固定。

preflight sentinel は通常の失敗経路で `finally` 清掃され、sentinel 残骸所見は refuted です。

**DW-G05 成果物影響:** marker の存在だけを見る consumer が未完成 publish を完成測定として台帳・proof chainへ参照できます。

### 5. [must-fix] F12 は partial — 49 passed のまま observer を壊せる

テストは category literal、verdict 優先順、S4/S6/S7 judge、create-only finalを以前よりよく固定しています。しかし [`observer_runner`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1889) を使う主要結線テストは実 observer を丸ごと迂回し、手書きの `_good_*` を流しています（[テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/orchestrator/tests/test_t316_sandbox_probe.py:213)）。

緑のまま通る具体的変異:

- `_poll_pid_identity()` の deadline 結果を常に `gone` にする。
- `_observe_descendant_control()` / `_observe_binary_descendant()` の inside status を `gone` に固定する。
- `_parse_payload_sentinel()` で `ERROR` や新たな `ENOSYS` を `denied` にする。
- S3/S5 の独自 write observerで inside stateを `denied` に固定する。
- `DENIED` sentinel付き `timed_out=True`／`rc!=0` を受理する現状を維持する。
- `COMPLETED` の `O_EXCL` を `O_TRUNC` に変える。
- temp、marker、directory のいずれかの `fsync` を除去する。
- `persist_partial()` を canonical pathへの直接逐次書込みに変える。
- `discharged_by_this_probe` に未測定項目を追加する。

現在のテストは bwrap setup failureの「sentinel 無し」だけを runner seamで検査し、timeout付き sentinel、実 S3/S5 observer、PID observer、publish crash pointを検査していません。

**DW-G05 成果物影響:** observer または耐久 publish の偽 GO 回帰が受入テストを通過し、誤った receipt を将来の gate 証拠にできます。

### 6. [must-fix] F15 は partial — discharge 済み一覧が verdict と無関係

[`r3_1_coverage`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:2008) は未 discharge の3項目と「overall GOはR3-1完了ではない」を明記しており、この部分は改善されています。

ただし `discharged_by_this_probe` は stage verdict に関係なく固定です。S3が `blocked`、S7が未実施でも、

- `compute-node backend containment observations`
- `single stock ... elapsed-overhead sample`

を discharge 済みと記録します。テストも全stageが良好なケースしか確認していません（[coverage test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/orchestrator/tests/test_t316_sandbox_probe.py:341)）。

**DW-G05 成果物影響:** blocked/inconclusive receiptを「封じ込めとstock overheadを測定済み」と台帳や後続レポートが引用できます。

### 7. [nit] publish preflight失敗後に空の job directory が残る

job directoryを作ってからself-checkするため（[`ReceiptPublisher.__init__()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1826)）、self-check失敗でも空directoryは残ります。sentinel自体は清掃されます。

**DW-G05 成果物影響:** directory存在だけを列挙する運用表示では、測定開始前の失敗を部分測定と誤表示し得ます。

## F1〜F15 対応表

| 所見 | 状態 | 再レビュー結論 |
|---|---|---|
| F1 | **regressed** | sentinel無しは閉じたが、fix2で `DENIED`＋timeout／非0終了をGOへ開いた。 |
| F2 | **partial** | PID identity verdictは改善。identity不明時の無限子孫清掃とobserver testが不足。 |
| F3 | **closed** | 単純timeoutでなく、子孫PID消滅を判定している。 |
| F4 | **closed** | compute host、nodefile、commit/root、dirty、runtime SHAを束縛。 |
| F5 | **partial** | path分離とEEXIST除外は成立。ENOENTを封じ込め拒否として受理。 |
| F6 | **partial** | final JSON本体はatomic create-only。COMPLETEDとpartial/final lifecycleが未完。 |
| F7 | **closed** | warm-up、交互反転6対、median/MAD、単独性、perf/thread検査あり。 |
| F8 | **closed** | runtime/build双方で4脅威を測定。 |
| F9 | **closed** | proxy redactionとcompute-node-local UNIX socketを実装。 |
| F10 | **closed** | outside build正例とsource identity検査あり。 |
| F11 | **closed** | sandbox toolchain契約を検査し、tool欠落をblocked化。 |
| F12 | **partial** | judgeテストは増えたが実observerとcrash-pointの検出力が不足。 |
| F13 | **closed** | DNS対象を名前 `example.com` に分離。 |
| F14 | **closed** | profile値を `declared_configuration_*` と明示。 |
| F15 | **partial** | 未測定項目は明示したが、discharged一覧が実 verdict と非連動。 |

集計: **closed 9 / partial 5 / regressed 1**

## scope と refuted

- production の生成variant受理集合・既存意味gate変更: **refuted**。差分はprobe/policy/testと、新規2実行体を `dispatch-required` とする閉集合fixture追加だけです。
- EEXISTまたはENOSYSがdenied集合に含まれる: **refuted**。
- sentinel無しのbwrap setup failureがGOになる: **refuted**。
- canonical `receipt.json` 本体が逐次書込みで部分JSONになる: **refuted**。
- 既存final receiptを上書きできる: **refuted**。
- pytest: 本レビューでは未実走。親が対象ファイルを **49 passed** と実測済みだが、上記変異の生存可能性は残ります。

## 総括

- blocker: **2件**
- must-fix: **4件**
- nit: **1件**
- refuted: **5件**
- F状態: **closed 9 / partial 5 / regressed 1**
- 投入判定: **NO-GO**

少なくとも `DENIED` を `timed_out=False`・期待終了状態・カテゴリ固有の拒否原因へ束縛し、PID cleanup、原子的 `COMPLETED`、observer実体の変異検査、verdict連動のR3-1 coverageを直すまで、このprobeを計算ノードへ投入してはいけません。