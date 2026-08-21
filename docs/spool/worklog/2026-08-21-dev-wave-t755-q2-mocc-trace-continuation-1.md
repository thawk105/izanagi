---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t755-q2-mocc-trace-continuation
seq: 1
title: '[T-755] Q2継続: Mocc trace pilot用のsanctioned adapterを実装・段6敵対レビュー2巡+焦点再レビューで検証したが、admission registryのmain固定によりTRACE=1実機実行は次waveへ持ち越す (コード+テスト、branch worktree-dev-wave-t755-q2-mocc-trace-continuation)'
---

## 本文

- ユーザーが Pegasus login node 上で `mocc-trace-v2.patch` を実 identity (thawk105) で
  `external/ccbench` へ commit した (new OID `ef9328a35d49b1b9b610f244bee22ad7f10b8b66`)。
  AI はこの wave で identity を一切設定していない。ユーザー自身の申し送りは
  `dev-wave-jobs/dev-wave-t755-q2-mocc-trace/continuation-handoff-2026-08-21.md`。
- 上記 commit は `mocc-trace-v2.patch` (前 wave 保全) をそのまま適用したもので、
  trace.hh include 行の末尾コメントが前 wave の段6 fix 前の版のまま残っていたと判明した
  (実行で確認、`tools/check_trace0_preprocess_identity.py` が正しく reject する)。
  TRACE=0 の性能実測はこの一点が解消するまで実施不可。TRACE=1 の正しさ検証はこの defect の
  影響を受けない。
- Mocc 用 sanctioned submitter/job script (`tools/pegasus/submit_mocc_trace.sh`,
  `tools/pegasus/mocc_trace_pilot.sh`) を Codex `role=author` で新設した。段6 で敵対レビュー
  2レンズ (`stage6-reviewA.md`/`stage6-reviewB.md`) を実施し、real 所見6件 (verifier CLI 呼び出し
  の致命的誤り、`pegasusinfo` の綴り誤り [親が独立発見]、signal 時の worktree 撤去漏れ、
  walltime 予算逼迫、nonce/cache path の入力境界、`ycsb_max_ope` の provenance 欠落) を fix
  2段 (`stage6-fix.md`/`stage6-fix2.md`) で修正し、統合後の焦点再レビュー
  (`stage6-focus.md`) で4点の解消を確認した。残る real 所見 (root binding の narrow gap、
  worktree 撤去の best-effort、workload 型検証欠如) は `certify_calibration.sh` の既存踏襲
  または pilot scope として許容し次課題とした。
- **wave 自身が land するまで新設 submitter を実機投入できないことが判明した。**
  `hooks/guard_bash.py` は自身の `__file__` から repo root を解決し (worktree 非依存)、
  `tools/pegasus/admission_registry.json` を常に primary checkout (main) 側から読む。
  本 wave が同ファイルへ追加した2 entry は wave branch 上の commit にしか存在せず、
  main へ land するまで guard から見えない。設計判断は {{D:pegasus-admission-main-anchored}}
  を参照。
- read-only 一次資料調査 (T-816 実測手順) を fork へ委任したところ、継承した `/dev-wave`
  manager 役定義を自分の役目と誤認する事故が再発した (約49分・32万token・成果物ゼロ・
  agent-message での越権中間報告)。F425 への再発として記録した。

## 次の一手差分

### 更新

- [T-755] **P1・Q1(a)/Q3(a)は完了 (既存記述のまま)。Q2(a)=mocc trace pilot 用 adapter を実装・
  段6敵対レビュー2巡+fix2段+焦点再レビューまで完了、受入緑を確認後 land 予定。ただし
  admission registry が main固定のため、本 wave 自身では TRACE=1/TRACE=0 の実機実行が
  できない (submitter が guard に未登録のまま、land まで待つしかない構造的制約)。
  次の一手 (次 wave): land 後、`bash tools/pegasus/submit_mocc_trace.sh --trace-mode 1`
  で実際に qsub し、C/R/W/E trace を回収して `python3 -m orchestrator.verifier` で検証する。
  TRACE=0 は `tools/check_trace0_preprocess_identity.py` が現行 commit を reject し続ける限り
  実施できない (別途 mocc-trace-v2.patch の trace.hh include 行修正 commit が要る、
  人間手番)。**
  base: 8946502f3fc4b78fef19917fa0385a64938718939e14547ab62ee9d11e544ac6
