---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: dev-wave-t1167-c12-allocation-binding
seq: 2
---

## 新規

### {{F:frozen-generation-collision}}. 並行 wave が同じ凍結世代番号を先に land し、merge では解けなかった [手順漏れ] [ドリフト]

- 事象: 本 wave と [T-1250] が同時に第 4 世代の条件契約凍結 record を発行した。[T-1250] が先に
  land したため、main を取り込んで自分の record を第 5 世代へ作り直そうとしたところ
  `prepare-revision` が `generation-mutated` で停止した。競合ファイルを main 側の内容へ揃えても
  解けなかった。続けて、文書変更を commit 済みのまま再生成しようとして
  `record-protected-mismatch` でも停止した。
- 根本原因: 2 つある。(1) 凍結 chain の世代 record 不変検査は作業木でなく **HEAD から到達できる
  全 commit** を走査し、同じ世代 path に 2 つ以上の blob oid があれば停止する。競合解消で作業木を
  揃えても、自 branch の履歴 commit に旧 blob が残る限り条件は成立しない。(2) `prepare-revision`
  は文書と証拠契約を**作業木**から読み、履歴は `--commit` で検証する。文書変更を commit 済みに
  すると、その commit の tip record が新しい文書と食い違い必ず落ちる。
- 恒久対応: 検査自体が fails-closed の実体である
  (`orchestrator/campaign/s8c_preregistration.py` の `validate_condition_freeze_at` が
  `generation-mutated` / `record-protected-mismatch` を送出し、`prepare_revision` を止める)。
  手順側は memory `frozen-generation-collision-needs-history-rebuild` — 凍結 artifact を発行する
  wave は、(a) land 前に自 branch 履歴が同一世代の別 blob を含まないことを確かめ、含むなら
  merge でなく main 直上の線形形へ組み直す、(b) 再生成は文書変更を**未 commit**の状態で走らせる。
- 再発検知: 上記 2 つの停止コードが本走前に発火する。どちらも rc=2 で世代を進めないため、
  誤った世代 record が commit へ入る経路は無い。
