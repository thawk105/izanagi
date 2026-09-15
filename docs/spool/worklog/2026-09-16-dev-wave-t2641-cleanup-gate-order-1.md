---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2641-cleanup-gate-order
seq: 1
title: "[T-2641] 掃除の棚卸しを安い gate 先行へ直し、実測で 2 つの欠陥を閉じた (コード + docs、branch worktree-dev-wave-t2641-cleanup-gate-order、変異 matrix = baseline PASSED・5/5 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致)"
---

## 本文

- **T-2642 と編集面が完全衝突し、先後を実測して本 wave が続行した。** job dir 作成 04:29:13 対
  04:29:39、worktree 作成 04:34:11 対 04:34:38、`.git/worktrees/` 登録 04:34:10 対 04:34:38 で、
  本 wave が約 27 秒先発。05:50 に T-2642 の session から「後発なので実装を降りる」と連絡があり
  実測と一致した。T-2642 は調査成果を insight として残し、本 wave の land 後に別 wave で当てる。
  **着手前の worktree 一覧 (04:31) では T-2642 がまだ存在せず** (04:34:38 作成)、`ps` の
  `dev_wave_codex.py --repo-root` で初めて検出した。1 回の ls では直後に立ち上がる wave を捕まえられない。
- **親が実測して段 3 / 段 6 の争点を決着させた。** (a) 裸の `git status --short` は worktree の
  index を書き換える (tracked file の mtime 変更直後に md5 が
  `622f9487ca7db6e31d7cab9adedbf62e` → `107713b4710d1cdbf74ffd6734743ec0`。
  `GIT_OPTIONAL_LOCKS=0` では不変 = 負の対照)。{{F:cleanup-status-writes-index}} へ。
  (b) 占有 checker は対象 path を argv に含む process を占有と数える。
  {{F:occupancy-checker-sees-reader-argv}} へ。(c) `discard_changes: true` は 21 bytes で、
  敵対レビューの「20」は誤り (refuted)。
- **敵対レビューの是正案を 1 件だけ却下した。** 予算レンズは「§3 手順 3 を F26 へ退避すれば
  本文 5810 bytes で増枠不要」と bytes つきで示した。bytes の点では成立するが、§3 手順 3 は
  破壊操作の gate であり、常に読まれる入口から pointer の先へ移すと pointer を辿らなかったときに
  gate が効かない。{{D:cleanup-command-budget-raise}} で採らないと裁定し、上限を
  5_900 → 6_204 (確定本文 6203 + 1) の最小増分で上げた。**D782 が親へ委任した手順の最終段であり、
  ユーザーへ報告する事項である。**
- **効果の出所を誤って記録しない。** 全 worktree の `git status` は省略しない (§4 の事後検査が
  surviving worktree 全体の事前 status を要求する)。短縮は (i) その取得の並列化と
  (ii) 占有検査・削除直前の再確認を安い条件の通過対象だけに絞ること、の 2 つから来る。
  「安い gate で落ちた分だけ status が消える」という評価は成立しない。
- **親の実測と、そこから断定できないこと。** 2026-09-16 に本 worktree で測った値は
  `git status --short` が 1 worktree あたり real 37.654 s (cold) / 22.021 s (warm)、
  `git rev-list --count --left-right` 0.099 s、`git cherry` 0.080 s、
  `git for-each-ref refs/heads` (83 本) 0.183 s、`git worktree list` 1.752 s。
  CPU 時間は実時間の 11〜15 % で、残りの内訳は測っていない。
  「2026-09-15 の branch 判定 10 分は 1 対象 1 tool call の呼び出し費用」は**仮説**であり、
  1 本の測定からは断定できない。他の 67 worktree への外挿根拠も無い。
  並列化による実際の高速化率は未測定である。
- **変異を段 6 で全件再照準した。** 段 4 で登録した M1〜M7 は、対象 file が whole-file SHA pin 下に
  あるため本文を変異させると必ず SHA pin にも当たり、単一理由にならない。焦点再レビューの指摘を
  受けて F28 に従い N1〜N5 へ再照準した。**段 4 の変異事前登録では「対象 file が whole-file
  SHA pin 下にあるか」を先に確認すべきだった。**
- **子の argv 制約を記憶に書いてあったのに読まずに 2 回踏んだ。** `--lane` は consult 専用、
  `--reasoning` は plan/consult 専用で、他段は rc=2。変異 harness の runner argv には `-rf` が必須。
- **fix 子の成果物は launcher が `evidence_status=invalid` で未受理にした** (子自身は exit 0、
  16 model call、wall 353 s)。契約どおり「未完了」と記し、親が作業ツリーを直接監査したうえで
  焦点再レビュー子に裏取りさせて GO を得た。

## 次の一手差分

### 完了

- [T-2641] `/cleanup-branches` §1 / §2 を安い gate 先行へ直し、§3 手順 3 に directory 撤去の
  並列化条件を置いた。削除が成立する述語の連言と閾値は 1 つも変えていない。
  remaining: none
  base: 2e96b7a4901d0f561040dbaf257a3db717b21b1567dec5dcab0cea2035e19ffa

### 新規

- {{T:cleanup-removal-process-lifetime}} **P3・新規**: 撤去を並列化したとき、親が kill された場合の
  子 process の寿命と取消契約が `/cleanup-branches` §3 に無い。本 wave は「1 件 1 process・各々長い
  timeout・path 相互非包含なら並列可・prune は全撤去 process の終了と成功を確認した後」までを
  入口へ置いたが、親 kill 時に子が残るか道連れかは launcher の構成次第で未定義のままである。
  process group の扱いと、不明・中断を完了扱いしない判定手順を決める。入口の byte 予算の
  外に置けるかも同時に判断する。
- {{T:cleanup-prune-necessity-wording}} **P4・新規**: `/cleanup-branches` §3 手順 3 の
  「全候補＝今回所有確認済み対象なら `git worktree prune`」は、後続の「余分・不明候補時は
  real prune せず引渡し」と §0 の許可集合を併せて読めば必要条件を保つが、手順 3 単独では
  候補不足 (preview が所有確認済み集合の真部分集合) の拒否が明示されない。焦点再レビューの
  minor 所見で、受理集合は変わらないため本 wave では直していない。条件を足さずに局所的な
  明示へ戻す (+15 bytes 程度)。
- {{T:dev-wave-l1-budget-blocks-two-improvements}} **P4・新規**: 段 8 の自己改善候補 2 件が
  `docs/dev-wave/**` の L1 予算に阻まれた。実測で L1 unique footprint の余裕は **1 byte**
  (上限 10625)。候補は (a) `DW-M01` へ「登録前に対象 file が whole-file hash pin 下かを見る。
  下なら本文変異は必ず pin にも当たり単一理由にならない」(+221 bytes)、(b) `DW-S01` へ
  「編集面が他 wave と重なりうるなら worktree 一覧だけで判定しない。作成前の wave は一覧に
  出ないので子の argv も走査する」(+238 bytes)。どちらも本 wave で実測済みだが、
  D730 の「実測 3 例以上だけを例外とする」に届かないため実施しない側へ落とした。
  同型の実測が積み上がったときに、L1 の縮約または増枠と合わせて再検討する。
