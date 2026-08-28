---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: worktree-dev-wave-t2000-legacy-build-probe
seq: 1
title: [T-2000] legacy buildの3-arm probeをfail-closed実装し、production admission不成立で裁定不能と確定した
---

## 本文

- production `build()` / `build_v2()`、admission、site、trace gateを変更せず、通常suite外のT-2000専用probeをCodex D95 authorで実装した。所有pathは `orchestrator/manual_probes/test_t2000_legacy_build_probe.py` 1本だけで、T-1941の `build_admission.py` 編集面との重複は0。
- 最終pathのpure 14 node + hook inventory meta 1 nodeはPegasus request `956909.nqsv`で15 passed、通常suite境界meta-testは `956574.nqsv`で76 passed。B-057最終matrixはbaseline PASSED、6/6 KILLED、SURVIVED/TIMEOUT/PARSE_ERROR/MISMATCH 0。
- 敵対review 2本と焦点review 3本で、Git transportの未観測0、legacy失敗の循環分類、dependency終端identity、configure値束縛、deadline、precondition artifact、process identity、explicit node gate、publisher namespaceを修正した。
- real投入でtests dispatcherのabsolute selector表現とTMPDIR非供給を実測し、D95 fixとpure負例へ固定した。最終request `956856.nqsv` はproduction admission preconditionでfail-closedし、3 armはすべて `not-run`、classification=`indeterminate`。結論とcreate-only raw/digestは `output/insights/2026-08-28_t2000-legacy-build-probe/RESULT.md` から引く。
- 単発wall、pytest緑、precondition失敗を因果証明・正式性能値・移行候補へ昇格せず、規律2とproduction admissionを緩めなかった。
- 再開段のCodex subprocessはauthor 1本、review/focus 5本、fix 5本。親は重複検査、real/refuted裁定、pure/meta/real実走、変異、記録、統合を担当した。

## 次の一手差分

### 更新

- [T-2000] **P2・裁定済み → production admission blocker調査待ち**: build経路は移行せず現状維持。別waveで3 armより前のproduction admission不成立のexact原因を特定する。admission/site/trace/correctness gateの緩和、production module変更、汎用probe API化はしない。
  base: 6eaf5e61376518457f98d65229599c3a27b9cc36ff6588a2876c8d009b0bb71d
