---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2234-budget-vacuity
seq: 1
title: [T-2234] 8c 予算 consumer の恒真な保証を発火する形へ直した — 規範の「対称」「一致」は厳密一致で実装し、変異 12 件を全件 KILLED した (コード + テスト + insight、branch worktree-dev-wave-t2234-budget-vacuity)
---

## 本文

- **親の段 1 brief の誤りを段 3 レンズ A が反証した。** brief は「予算停止を一度も発火させられない」
  と書いたが、現行の 3 層 (総上限・arm・holdout) は超過を実際に検出しており、既存テストも
  3 層それぞれの witness を持っていた。恒真だったのは「予約が実在することを要求する述語が無い」
  ことと、規範が要求する arm 上限の対称性・holdout 上限の和の一致を誰も検査していないことである。
  brief はまた `symmetric_indeterminate` が理由コードを返すと書いたが、同関数は cell ID 集合だけを
  返し `budget-insufficient` は supervisor が付ける。どちらも insight §2 で訂正した。
- **段 3 の 2 レンズが独立に同じ blocker を出し、片方がもう 1 件を追加した。**
  (a) 変更面が 2 file では閉じず `test_p3_autonomous_workload_trial.py` の supervisor fixture も
  規範適合値へ直す必要がある。(b) 段 2 プランが採った許容差 1e-9 では、総予算 0 のまま
  新しい 3 検査を全部通る入力が作れる。(b) を受けて厳密一致へ切り替えた ({{D:budget-normative-limits-exact}})。
- **実装しない裁定を 2 件出した。** 極小正値 regime の閉塞と `ReservationCell` の field 正規化は
  どちらも real な所見だが、前者は規範に無い「最低予約量」を実装が決めることになり、後者は
  本 wave の scope 指示 (仮想リスク向けの検査を足さない) の外である。{{T:budget-minimum-reservation-authority}}
  と {{T:reservation-cell-field-normalization}} として次の一手へ回した。
- **変異の期待 node は 2 段構えで確定した。** 全 12 件を `expected_status=SURVIVED` で登録した probe を
  先に走らせ、観測した完全集合を本走 spec の `expected_nodes` にした。単一 node と決め打ちしていたら
  M1・M3 (3 node) と M6・M8 (2 node) で MISMATCH になっていた。この probe→本走の 2 段構えは
  `docs/dev-wave/mutation.md` の `DW-M07` に「node 空の spec は起動前に中止」としか書かれておらず、
  probe spec を全件 SURVIVED で登録する作り方は明文が無い。
- **段 6 の敵対レビュー 2 本は blocker・must-fix ともに 0 件だった。** `DW-M02` に従い、所見ゼロを
  変異なしで緑と数えず、親が変異 matrix を走らせて 12 件全件 KILLED を得た
  (`registered=12`・`matching=12`・`MISMATCH=0`・`SURVIVED=0`、baseline `PASSED`)。
- **段 8 の候補 2 件はどちらも本文編集に至らなかった。** (a) 変異 probe を全件 SURVIVED で登録して
  期待 node を集める作法は `DW-M07` に既に明文があり、追記不要だった (handoff の「明文が無い」は
  親の誤り)。(b)「`git worktree add` も前景 timeout で SIGTERM され branch だけ残る」を `DW-C01` へ
  統合しようとしたが、同節は exact 契約 pin 付きで単節予算 1000 bytes に対し現行が満杯であり、
  最小の追記でも 1094 bytes になって `check_docs` が赤になった。予算引き上げには至らず、
  独立 2 例にも達しないので D782 の手順で閉じた。
- **エージェント工数。** codex 子 6 本 (plan 1・consult 2・author 1・review 2、いずれも
  `gpt-5.6-sol` / `xhigh`)。変異走行は probe と本走で計 26 run。
- 逐語と実測は `output/insights/2026-09-08_t2234-budget-vacuity/`。

## 次の一手差分

### 完了

- [T-2234] 全 cell の予約値 0 が `held` として受理される恒真化を直した。予約の実在・arm 上限の
  対称性・holdout 上限の和の一致を consumer へ入れ、負例 10 件と変異 12 件 (全件 KILLED) で
  発火することを実測した。C05 の結線・事前登録の予算欄の解除・C06 の充足は主張しない。
  remaining: none
  base: fa617c0e8e7c39fba20169ee1b3df59f637f1739e66e68a1f190288dc92f40fd

### 新規

- {{T:budget-minimum-reservation-authority}} **P2・新規・ユーザー裁定待ち**: 8c 予算 consumer の
  極小正値 regime を閉じるかを決める。総上限 1e-9・arm 上限 各 1e-9・holdout 上限 各 5e-10・
  予約 各 5e-324 は現行の全検査を通って `held` になる。閉じるには「最低予約量」か「正式 workload の
  事前コスト計画との結合」が要るが、どちらも事前登録の規範に無く、実装が決めると
  {{D:budget-normative-limits-exact}} が避けた「権威のない仕様」になる。
- {{T:reservation-cell-field-normalization}} **P3・新規**: `ReservationCell.__post_init__` が
  `_finite_nonnegative` の戻り値を field へ保存しないため、比較を上書きした `float` subclass が
  受理済みオブジェクトに残る。1 行で直せるが、同型の穴が他の dataclass にも無いかを先に数える。
  公開経路では JSON 読み戻しで `BudgetError` になるので、不整合な台帳が黙って通ることはない。
