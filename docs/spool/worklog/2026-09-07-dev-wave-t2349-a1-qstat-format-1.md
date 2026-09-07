---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2349-a1-qstat-format
seq: 1
title: [T-2349] A-1 driver の qstat 可視性判定を実機 NQSV 書式へ合わせ、終端の消失判定を対象束縛で締める (コード + テスト + docs、branch worktree-dev-wave-t2349-a1-qstat-format、変異 11/11 KILLED + SURVIVED 0)
---

## 本文

- ユーザー指示 (dev-wave 引数): `_observe_qstat_visibility` と `_parse_qstat_terminal` を実機 NQSV 書式へ
  合わせ、`dispatch_compute.py` の実証済み `Current State` parser へ揃える。実機 `qstat -f` の逐語を
  fixture にした正例・負例を同じ commit に足す。`NQSV_QSTAT_STATES` は実書式の語へ写像する形にし、
  未知語の拒否は残す。Codex author 必須。attempt-0002 の再投入は本 wave では行わない。本題の実装だけ。
- 記録は `output/insights/2026-09-07_t2349-a1-qstat-format/`。逐語 (plan / 敵対 2 / 実装 / レビュー 2 /
  fix)、変異 spec と台帳 (最終 + erratum) を収録した。
- **段 4 で「実機で見た形だけを受理する」案を却下した。** 段 3 のレンズ A が A-1 専用の surface profile を
  提案したが、D805 が同じ案を「語彙の二重化」と「過学習 — 本走 2 回目は `Current State = Queued` で
  待機しており、その案なら正常運用で fail-closed していた」として既に却下している。本 wave の親も
  生きた標本を 2 件しか持たない。受理面は共有 leaf のまま使い、絞るのは canonical 側 (`QUE` / `RUN`) だけとした。
- **子の所見 2 件を親の実測で refuted にした。** (a)「共有 leaf が source closure 外なのは provenance の
  欠落」→ closure は 9 path に対し driver の import は 10 件以上が closure 外で、**transitive closure では
  なく意図的な部分集合**。共有 leaf を外しても新種の欠落は生まれない。(b)「job body の allocation-qstat
  parser が PBS-Pro 型」→ 実装は `Execution Hosts(JSVNO):` fallback と `Started Request Time` を持ち
  実機出力に一致する。非代表なのは test fixture だけ。
- 依頼に無かった実機事実を 1 件測った。**不存在 request の `qstat -f` は rc=0 で返る**
  (stdout 51 bytes の 1 行、stderr 0 bytes)。現行 `_observe_scheduler_terminal` は `returncode != 0` を
  失敗としていたので、この前提は実機と合っていなかった。消失枝は現に到達可能で、かつ rc=0 の任意 stdout を
  消失と扱えていた。
- 段 6 の敵対レビュー A が must-fix 1 件 (execution queue 行の全体一意性が裁定より弱い) を出し、親が実測で
  real と確認した。候補識別と書式検証を同じ regex が兼ねていたため、別 server の 2 本目が数えられず素通り
  していた (実機 RUN 全文 + `Queue = other@other (Execution Queue)` が受理された)。fix で候補段と検証段を
  分離し、再実測で両方拒否になった。レビュー B の must-fix は 0 件。
- 変異は初回 `KILLED 7 / MISMATCH 4 / SURVIVED 0`。4 件はいずれも gate の欠陥ではなく親の
  `expected_nodes` の精度で、冗長 gate 1 件を単独証拠から外し、共有 helper の 2 consumer と
  fixture 差し替えの波及を登録へ足して再走したところ `KILLED 11 / MISMATCH 0 / SURVIVED 0` になった。
  初回台帳は erratum として消さずに残した。
- **実装子と fix 子は pytest を実走できていない** (`tools/run_tests.py` が
  `NQSconnect: [API EACCTAUTH] Unknown user-id` で rc=16)。焦点走 794 passed は親の実走である。
- **本 wave は「A-1 が bench へ到達する」と主張しない。** 閉じたのは F852 の投入 blocker と消失判定の
  過剰受理だけで、3 job fan-out・group receipt 待機・barrier・reservation は実機未通過のまま残る。
- 段 3 の初回 2 本は、login node の load が 144 まで上がって launcher の authority snapshot 用 `git` が
  10 秒 timeout し rc=2 (`launcher_error`) になった。子は完走し `validator_rc=0` だったが、記録が
  閉じていないものは採用せず、負荷低下後に投げ直した。段 2 の初回は親の prompt が `## 総括` の
  見出し literal を厳密に指定していなかったため子が別名の見出しを出し、`f43_fragment` で不採用になった。

## 次の一手差分

### 完了

- [T-2349] A-1 driver の qstat 可視性判定を実機 NQSV 書式へ合わせ、終端の消失判定を対象束縛で締めた。
  受理面は共有 leaf のまま使い canonical 側を `QUE` / `RUN` に絞る。実機逐語 4 種を fixture 化。
  変異 11/11 KILLED (SURVIVED 0)、焦点走 794 passed。
  remaining: none
  base: 98e7275736d9376518a2894d73f6c6a2d1e5ccab9b4fb30531dc64ba89142be6

### 新規

- {{T:a1-attempt-0002-resubmit}} **P1・新規**: F852 の fix 着地を前提に、A-1 pilot の attempt-0002 を
  fresh wave で投入する。投入元 checkout は記録を書かない別 worktree にし、3 job の preflight 通過を
  確かめるまで untracked を含めて 1 byte も汚さない。
- {{T:a1-allocation-qstat-fixture}} **P3・新規**: A-1 の allocation-qstat テスト fixture が PBS-Pro 型
  (`exec_host = compute01`) で実機を代表していない。job body の実装は実機 NQSV 対応済みなので機能欠陥では
  ないが、F852 と同じ「テスト代表性」の型である。実機逐語へ差し替える。
- {{T:a1-qstat-receipt-schema}} **P3・新規**: submission / completion receipt へ qstat の raw stdout /
  stderr / rc を保存する schema migration。これが無い限り `stderr == ""` は producer-only invariant に
  留まり consumer が再検査できない。あわせて reader の `NQSV_QSTAT_STATES` 12 語を実在 receipt の
  棚卸しに基づいて縮小するかを判断する。
