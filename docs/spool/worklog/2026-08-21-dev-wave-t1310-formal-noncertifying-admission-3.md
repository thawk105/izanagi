---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t1310-formal-noncertifying-admission
seq: 3
title: '[T-1310] 正式non-certifying launch admission modeを新設しD510 attempt registryへ統合した (コード+テスト、branch worktree-dev-wave-t1310-formal-noncertifying-admission、変異matrix = baseline PASSED・7/7 KILLED・SURVIVED 0・MISMATCH 0、受入 verdict=child-green)'
---

## 本文

- ユーザー裁定 (2026-08-20): R-01 択(a) を採用。正本 =
  `output/insights/2026-08-18_t1333-t1310-workload-profile/README.md`。
- 段3 敵対相談2レンズ (sol/luna) が独立に、親の (P1) provisional 裁定 (新モードは D510 の
  attempt registry を消費しない) を refuted と判定した。規律面 (reward hacking 懸念、D510
  無断縮小) と技術面 (binding-with-no-slot が既存前提と衝突し実行時クラッシュする) の両方で
  不成立。設計判断は {{D:formal-noncertifying-admission-d510-integration}} を参照。
- 実装規模が当初想定 (逐次2単位) の2〜3倍に膨らむ新事実が判明したため、段4裁定の前に
  ユーザーへ方針確認した。「完全統合で進める」を選択 (実装規模の大きさは承知のうえで、
  親が単位を分割してよいという前提)。
- 段4裁定の追加実測: `create_attempt_registry_genesis()` は manifest 単位で1回だけ生成され
  admission mode とは独立した層にあることが判明し、certifying/non-certifying の slot pool
  分離という重い再設計は不要と分かった。これにより実装規模は「中規模」に収まった。
- 段6 敵対レビュー2本 (real 5件、うち fix 対象2件: CLI 相互排他検査の公開 CLI 経由テスト欠如、
  lifecycle 拒否メッセージの旧 mode 名残留)。焦点再レビュー GO。
- 変異matrix: `tools/mutation_harness.py --runner-mode dispatch` の collection 段階が
  Pegasus dispatch インフラ障害 (`receipt scheduler_logs.stdout.path がない`、rc=16) で
  2回連続 abort した ({{F:mutation-harness-dispatch-collection-infra-failure}})。3回目の
  自動 retry はせず、既存 memory の代替手順 (Edit → `tools/run_tests.py` 実走 →
  `git checkout --` 復元、7変異を手動反復) へ切り替え、baseline PASSED・**7/7 KILLED**・
  SURVIVED 0・MISMATCH 0 を確認した。期待 node は probe 走 (全件 SURVIVED 期待) で確定した
  完全集合と実測が完全一致。
- 受入: 1回目投入は `claim-timeout` (rc=70、投入から約4分、他 wave が lease `held` 中
  [age_seconds≈813] だったが `--max-wait-seconds 7200` を指定したにも関わらず早期に
  timeout した — 原因未特定、再現性は未確認)。2回目投入で `verdict=child-green`、
  `pre_fingerprint`/`post_fingerprint` の `diff_bytes: 0` (走行前後で木は完全不変)。
  受入待機中に spool fragment をworktree内へ誤って作成しかけた near-miss を
  {{F:acceptance-inflight-worktree-write-near-miss}} として記録し、投入直後は repo 外
  staging へ退避して回避した (実害なし)。
- **scope外 (次wave)**: `autonomous_trial_completeness.py` の completeness/report/digest
  consumer は新mode未対応のまま。validator未patchの `run_trial()` は新mode で例外・
  indeterminate lifecycle になる (段6焦点レビューで確認済み、明示された scope 境界)。
  8c 正式測定を report まで完走させるには次wave (下記新規) が必要。
- 工数: Codex 呼び出し8本 (plan×1・consult×2・author×2・fix×1・review×2・focus×1、
  全て model=gpt-5.6-luna・reasoning=max)。段5 author 初回投入は `--reasoning` を誤って
  明示指定し argv error (rc=70) — 段5/6 は docs 権威由来で明示指定不可という制約
  (`DW-O01`) を実演した、再投入で解消。
- 段8 改善候補 (段8裁定へ): (1) 条件dispatch表の能動スキャンをbrief内でチェックリスト化
  する候補 (F50 4回目再発)、(2) 専用handoffの配置先チェックを段1着手直後に明示する候補、
  (3) 受入投入後の repo 内書き込み禁止を `DW-O18`/pegasus-runbook §7.3 へ明記する候補
  ({{F:acceptance-inflight-worktree-write-near-miss}})。

## 次の一手差分

### 完了

- [T-1310] 正式non-certifying launch admission modeを新設し、D510 attempt registryへの
  完全統合・段6敵対レビュー・変異matrix・受入 (verdict=child-green) を完了した。
  completeness/report/digest対応は新規タスクへ分離した。
  remaining: none
  base: 90dbf76b3119a7f6575213db92a044094475d8c3153aab97cc8542edd29e9367

### 新規

- {{T:t1310-completeness-digest-followup}} **P1・次wave**:
  `orchestrator/campaign/autonomous_trial_completeness.py` の completeness/report/digest
  consumer を `registered-formal-non-certifying` mode に対応させ、8c 正式workload
  (H1/H2) の non-certifying 測定を report.json 生成まで完走できるようにする。
  [T-1310] が admission + D510 slot 消費 + arm binding + lifecycle までを実装済み。
  正本 = 本エントリと {{D:formal-noncertifying-admission-d510-integration}}。
