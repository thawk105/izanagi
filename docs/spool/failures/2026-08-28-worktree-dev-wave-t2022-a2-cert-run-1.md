---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-28
wave: worktree-dev-wave-t2022-a2-cert-run
seq: 1
---

## 新規

### {{F:a2-protocol-case}}. build targetの表記をsource directoryの表記に使い、A-2全cellがidentity前に止まった [ドリフト] [テスト代表性]

- 事象: policy `ccbench_protocol="SILO"`から`cc/SILO/CMakeLists.txt`を構成したが、実submoduleは`cc/silo/CMakeLists.txt`で、4 cellすべてidentity-errorになった。
- 根本原因: synthetic fixtureも`cc/SILO/ycsb_SILO.exe`を作り、production policyと同じ誤ったcaseを再演していた。実submodule layoutを通す正例が無かった。
- 恒久対応: `paper_story_a2_certification.v2.json`とloaderをexact lowercase`silo`へ固定し、production policy→Genome→実CMake path→target/binaryを通すtestとM7を追加した。
- 再発検知: protocol文字列をsource pathとbuild targetへ使うdriverは、実submoduleのCMakeListsと生成targetの双方をproduction helperで照合する。

### {{F:a2-generator-capability-missing}}. GeneratorIdだけを作ってcapability resolverを接続せず、A-2 adopted全点がadmission前に止まった [恒真ゲート] [テスト代表性]

- 事象: A-2は`GeneratorId.BACKOFF_REPRO`のBuildRunContextを作ったが`attest_generator_output`を渡さず、adoptedだけでなくfull pin不一致に隠れたstockも含め全cellがadmission-errorになった。
- 根本原因: unit positiveが`run_campaign`を丸ごとmockし、source evidence→resolver→derive admissionのproduction forwardingを通していなかった。
- 恒久対応: A-2 run_workloadへpolicy/workload/genome-boundなBACKOFF_REPRO resolverを接続し、actual loopと既存deriveを通すPC4、M9を追加した。
- 再発検知: BuildRunContextのgenerator IDを持つdriverは、stock/adoptedをactual loop経由でstock-baseline/machine-generatedへ分類する正例を持つ。

### {{F:mutation-plan-only-dispatch-evidence}}. plan-onlyが存在しないdispatch evidenceを要求し、preflight失敗containerをresumeでも閉じられなかった [手順不整合]

- 事象: `mutation_worktree.py --plan-only`が変異0件の後に`退避 dispatch evidence が通常 directory でない`でrc=125。spec hash転記誤りで保全されたcontainerへ正しいhashでresumeしても同じ終端になった。
- 根本原因: plan-only/preflight失敗と実dispatch後で、wrapper teardownが同じdispatch evidence directory必須条件を使う。前者にはdirectoryが構造上存在しない。
- 恒久対応: 本waveでは実装せず、`tools/mutation_worktree.py`のplan-only/preflight-failure分岐と`docs/dev-wave/mutation.md`の回復契約を同時に直す候補として専用handoffへ記録した。
- 再発検知: fresh scratchでplan-only、およびspec hash不一致後の正しいresumeを実行し、job未投入・container teardown・rcの意味が一致することを検査する。

## 再発

### F251

- **再発: 2026-08-28** — pre-existing A-2 attempt `t2022-20260827`はcompute preflight通過後に束縛先worktreeが消え、2 workloadともsource path不在でidentity-error。新waveはworktreeをlockし、finish/collect完了まで保持した。

### F580

- **再発: 2026-08-28** — 有効なA-2 4-cell acquisitionのtracked publishがLustre上の`RENAME_NOREPLACE` EINVALで停止。A-1既存先例と同じEINVAL限定exclusive-claim fallbackをA-2へ実装し、同じacquisitionの再提示でpublishした。

### F601

- **再発: 2026-08-28** — A-2 submitterがfull 40桁HEADをreceiptへ渡し、build admissionのshort `pin.CURRENT_PIN`完全一致でstock/adopted全cellが拒否された。submit/compute/Pythonをcanonical short + resolved full HEAD + literal prefixへ統一した。
