---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: worktree-dev-wave-t1434-science-slice
seq: 1
title: [T-1434] T-1222 task-output science sliceを負結果のまま閉じた (code + docs、branch worktree-dev-wave-t1434-science-slice、mutation baseline PASSED・6/6 KILLED)
---

## 本文

- 停止waveの外来未コミットtool/testをrepo外へ同一SHAで保全し、別D95 authorが全文監査して採用した。前authorは利用上限でfinal outputを生成しなかった。
- 段6は敵対review 2本、fix 3巡、focus 2本を実施した。実効所見はreceipt provenance、reader consensus、physical bytes、型厳密性、Git環境、attestation一意性で、最終focusは新規must-fix 0・regressed 0だった。
- receiptに存在しない`prompt_path`を要求する所見は、artifact descriptor path+SHA、pinned receipt raw SHA、receipt `prompt_sha256`の結線を実測してrefutedとした。
- 素材: 2 readerは12/12 cellで一致したが、plan/authorの両stageでdetectedだったlogical findingはO1/O5の2件だけだった。coverageは`2/6 = 1/3`、retrospective task-output acceptanceは`not-accepted`である。
- 素材: integrity validな科学的負結果を保存し、`child-green`、test緑、physical integrityをsemantic acceptedへ昇格しなかった。organizational independenceは`not-established`、section8 completeは`false`である。
- portable/physical CLIはともにrc=0。portableはsemantic `not-evaluated`、physicalはartifact/validator/23 dependency bytesを束縛して`2/6`・`not-accepted`を再計算した。
- 焦点走は専用testとplain-runner meta-testで27 passed。mutationはcommit `7cc5ce907`へ束縛し、baseline 26 passed、SS-M1〜SS-M6 6/6 KILLED、期待node完全集合一致、SURVIVED/MISMATCH/PARSE_ERROR/TIMEOUT 0だった。
- 実装・記録は`892ff9b19..0c48a6cfa`の4 commit、current main取込は`dfb36aaac`。詳細とraw ledgerは`output/insights/2026-08-28_t1434-science-slice/`。
- 中間受入attempt 1はtested main `c384a90a0`、tested tip `dfb36aaac`で`child-green`、18,635 passed / 62 skipped、red/flake 0、effective scheduler `loadgroup`。log SHAは`16991b4c...2e7b`。
- §8全体、外部custodian、routing evidence、served-model attest、model既定化、汎用oracle基盤、別task familyはrepo外handoffの新規T候補へ分離し、同waveへ追加していない。

## 次の一手差分

### 完了

- [T-1434] availability-selectedなT-1222 1 familyのretrospective task-output science sliceを、負結果を保持したまま完了した。
  remaining: none
  base: d5ef325e994be49a2a40f6390654833406b7d55db57a4759e4c744d4a7961aef
