結論: R1 は reject。must-fix 8 件、nit 2 件です。pytest は実行していません。

### R1-1 — 自己ハッシュしただけの偽 ledger で旧 campaign を admitted にできる

- file:line: [trigger_gate_reinspection.py:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/trigger_gate_reinspection.py:100)、[artifact_admission.py:459](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/artifact_admission.py:459)
- 攻撃シナリオ: 旧 WAL の build_start hash を計算し、全 entry を `"passed"` にした dict を作り、公開仕様どおり outer SHA を再計算する。`require_admitted_campaign(..., reinspection_ledger=dict)` に渡せば、source/provenance checkerを一度も通らず全 verdict が PASS になる。`create-only` writerを完全に迂回できる。
- 成果物影響 (DW-G05): `legacy-unclassified` が `admitted-reinspected`、classification が `historical-trigger-reinspected` に反転し、旧 WAL 全体が `AdmittedCampaign` の受理集合へ入る。
- 提案: **must-fix**。raw Mapping入力を廃止し、consumer-side再検査または外部 trust root に束縛された発行証拠を要求する。自己ハッシュは真正性を与えない。

### R1-2 — 1 個の無関係な現行 source が全 historical record を合格させる

- file:line: [trigger_gate_reinspection.py:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/trigger_gate_reinspection.py:73)、[trigger_gate_reinspection.py:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/trigger_gate_reinspection.py:143)、[test_artifact_admission.py:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/tests/test_artifact_admission.py:166)
- 攻撃シナリオ: 対象旧 campaign には異なる `src_token` を持つ build_start が2件ある。それでも一時 directory に `izanagi_gate_pass = true;` を1個置き、全 records と同じ `source_root` を渡すと、実装は両方を PASS にする。既存テストがこの fail-open を正例として固定している。
- 成果物影響 (DW-G05): record別 source/provenance が失われていても全 record hash が PASS になり、旧 campaign の受理集合と reinspection ledger参照が捏造される。
- 提案: **must-fix**。`old-record-hash -> record固有のsource snapshotまたは逐語provenance` を束縛する。対応証拠がない record は必ず `SOURCE_UNAVAILABLE`。単一 campaign-wide `source_root` は廃止する。

### R1-3 — extractor は「compiler が選ぶ枝」を検査していない

- file:line: [source_digest.py:249](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/source_digest.py:249)、[source_digest.py:257](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/source_digest.py:257)
- 攻撃シナリオ:

```cpp
// EVOLVE-BLOCK-BEGIN silo-backoff-trigger-gating
#if BACKOFF_TRIGGER_GATING && 0
  izanagi_gate_pass = true;
#else
  Backoff::backoff(FLAGS_clocks_per_us);
#endif
// EVOLVE-BLOCK-END silo-backoff-trigger-gating
```

  marker は部分一致、directive は単に最初の `if/else/endif` として認識される。checker は隠れた then-branch を合格させるが、flag=1 の compiler は else-branch を実行する。buildcache の再検査も同じ extractor なので通過する。
- 成果物影響 (DW-G05): receipt は `true` の digestを参照する一方、binary・性能値・certified選択は別挙動を実行する。
- 提案: **must-fix**。binary-modeのまま marker行、`#if BACKOFF_TRIGGER_GATING`、同一nestingの `#else/#endif`、immutable frameを完全一致で検査する。

### R1-4 — S8A直接 materializer は receipt を通行証にしている

- file:line: [s8a_trigger_coverage.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8a_trigger_coverage.py:132)、[s8a_trigger_coverage.py:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8a_trigger_coverage.py:158)、[s8a_trigger_coverage.py:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8a_trigger_coverage.py:163)
- 攻撃シナリオ: admission検証後、configure前に hole を `izanagi_gate_pass = false;` へ交換する。以後は直接 `subprocess.run` で buildし、pre/post-buildの actual-source再認識がない。`s8a_trigger_freq.py` も同じ `_build` を再利用する。
- 成果物影響 (DW-G05): `build_admissions` は交換前sourceを参照する一方、coverage/frequency JSON の counts、checks、effective reasons は交換後binary由来になる。
- 提案: **must-fix**。buildcacheの権威経路へ統合するか、configure直前とbuild直後に全 `SourceEvidence` を exact再計算する。

### R1-5 — receipt発行時に全 SourceEvidence を再検査していない

- file:line: [build_admission.py:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/build_admission.py:425)、[build_admission.py:434](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/build_admission.py:434)
- 攻撃シナリオ: `resolve_evidence()` 後、holeは維持したまま `cmake/Options.cmake` または `include/backoff.hh` を変更する。発行処理は hole digestだけ比較するため、古い tracked diff/source digestを含む receiptを発行する。
- 成果物影響 (DW-G05): pipelineでは receipt付き standard build_start の後に `build-error` となり、本来の receiptless pre-admission rejectとWAL topology/reasonが変わる。R1-4経路ではそのまま別binaryのS8A reportになる。
- 提案: **must-fix**。発行APIへ Genome/compiler contextを渡し、fresh `resolve_evidence()` と入力 `SourceEvidence` の完全等値を発行条件にする。

### R1-6 — artifact consumer が trigger grammar lock を常に未指定で検証する

- file:line: [artifact_admission.py:648](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/artifact_admission.py:648)、[wal.py:633](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/wal.py:633)、[wal.py:676](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/wal.py:676)
- 攻撃シナリオ: 正当な grammar-bound campaign lock と本物の admission-v2 build_startを artifact consumerへ渡す。呼出しが `trigger_grammar_locked` を省略するため default=Falseとなり、必ず「grammar-bound lockがない」で拒否される。
- 成果物影響 (DW-G05): 正当な新規 trigger campaign が admitted view、S8A consumer、Layer3 reportの受理集合から全除外される。
- 提案: **must-fix**。`wal.replay()` と同じ lock判定を渡し、本物のv2 campaign E2E正例を追加する。

### R1-7 — WAL は attempt未束縛abortと任意reasonを受理する

- file:line: [wal.py:762](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/wal.py:762)
- 攻撃シナリオ: post-policy WALへ `{"stage":"abort","payload":{"reason":"verifier-red"}}` を単独で置く。`build_attempt_id` がなくactive attemptもなければ検査はそのままcontinueする。またreceiptless startに任意文字列reasonのabortを結んでも閉enum検査がない。
- 成果物影響 (DW-G05): 不正abortがadmitted WALのterminal状態となり、variantを永久skipさせてcertified候補集合を縮められる。
- 提案: **must-fix**。admission-aware WALではabortを常に matching active attemptへ束縛し、receiptless abort reasonを閉集合へ限定する。

### R1-8 — reject経路が入力tokenをWAL・critic・logへ出す

- file:line: [p3_s4_loop_trigger_gating.py:128](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/p3_s4_loop_trigger_gating.py:128)、[p3_s4_loop_trigger_gating.py:372](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/p3_s4_loop_trigger_gating.py:372)、[p3_s4_loop.py:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/p3_s4_loop.py:264)
- 攻撃シナリオ: `izanagi_gate_pass = true; thid_ SECRET_CANARY` を投入する。grammar reject後もlegacy blacklistを走らせ、`thid_` をreason、evidence、logへ逐語出力し、そのdigestをWALへ保存する。既存テストも [test_p3_s4_loop_trigger_gating.py:1129](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1129) でtoken露出を要求している。
- 成果物影響 (DW-G05): WAL `diff_quarantine` payload、critic digest、ログの値が入力tokenを含む形へ変わる。
- 提案: **must-fix**。matched namesを永続化せず、閉じた `legacy-forbidden` subtype/booleanだけを出す。

### R1-9 — prebuild notes canary は入力を経路へ渡していない

- file:line: [test_campaign.py:1897](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/tests/test_campaign.py:1897)
- 攻撃シナリオ: `secret_source` はローカル変数内で自己確認されるだけで、fake resolverは最初から安全化済み `TriggerGateSourceError` を投げる。actual bytes→exception→notes/log/WAL の合成経路を踏んでいない。
- 成果物影響 (DW-G05): 現行実装への追加攻撃はこのテストだけからは構成できない。
- 提案: **nit**。fake resolver内部で実 binary inspectorを対象sourceへ呼び、その例外をpipelineへ流す。

### R1-10 — P1–P9正例は全層KILL nodeになっていない

- file:line: [test_trigger_gate_language.py:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/tests/test_trigger_gate_language.py:301)
- 攻撃シナリオ: 9式はpublic checkerへ渡すだけで、rendered-hole抽出、receipt、build境界を通らない。下流だけが特定の正例を過剰拒否する変異でもこのnodeは緑のままになる。
- 成果物影響 (DW-G05): 現行diffで実際に過剰拒否する入力は構成できなかった。
- 提案: **nit**。段6でP1–P9をraw/indent付き双方についてquarantine→render→receipt→build境界まで通す。

## 変異 KILL node 静的監査

- M1–M9、M10–M13、M15–M17の直接nodeは存在し、裁定上の入力へ到達する。
- M14の「ledgerなしをadmit」変異nodeも存在するが、R1-1/R1-2の偽・非束縛ledgerを殺さない。
- M18は静的checker baselineが成功した。旧adapter SHA変異の実KILLは親実測が必要。
- M12 cache-hit testは初期検査後にsource交換し、M13は公開quarantineを直接叩くため、静的には相互maskなし。M12+M13同時変異は未実測。
- mutation harnessは実行していないため、KILLED件数は主張しない。

## 攻撃したが構成できなかった面

- recognizerの判定順、A2-5、512/513、64/65、kUnset semantic、手書きtruth tableから受理拡大は構成できなかった。
- buildcache本経路はbinary抽出、cache-hit/fresh後の全SourceEvidence再検査、旧entry promote 3負例を備え、text-mode権威化やreceipt fallbackは見つからなかった。
- non-trigger cache key/preimageへtrigger fieldが混入する分岐は見つからなかった。
- 永続`issued` field、reinspectionから標準attemptへの昇格、receiptless build_done/commit受理は見つからなかった。
- S8Bの5-key/7-key exact shapeとLayer3 claim-boundary削除について、追加の受理拡大は構成できなかった。

## 総括

- must-fix: **8件**、nit: **2件**。
- 最重要はR1-1/R1-2。reinspection ledgerはsource証明ではなく、自己申告PASSとして旧campaignをadmitできる。
- 次点はR1-3。権威extractorがcompiler選択枝を検証せず、receiptと実binaryを分離できる。
- 親はR1-1〜R1-8の負例、正当v2 artifact、4面canaryを計算ノードで実測すべき。
- M1–M18、P1–P9、M12+M13同時変異をmutation harnessで実走し、単一理由性を確認すべき。
- C++一回限りdifferentialも裁定どおり親が実測・記録すべき。
- 本レビューではpytest未実行。静的`check_codex_agents.py`と`git diff --check`は成功、ファイル変更なし。