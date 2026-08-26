---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-occupancy-repair-20260826
seq: 3
title: 占有判定の再試行を issue 種別から解放し F489 の 4 例目を閉じた (コード + テスト、branch worktree-dev-wave-occupancy-repair-20260826、変異 matrix = baseline PASSED・9/9 一致・KILLED 8・SURVIVED 1 (登録どおり)・MISMATCH 0)
---

## 本文

- **依頼は「既知の赤があれば確認して適切に修理する」だった。既知の赤を 4 系統に棚卸しし、
  未修理の 1 系統を本 wave の scope にした。**
  (1) AI provenance の既知違反台帳 (`tools/known_violations/` 53 件) は
  `python3 tools/check_ai_provenance.py` が rc=0 で 6210 commit を監査し新規違反なし。
  53 件すべてが現に発火しており (checker の stale 検出も緑)、全件が D742 baseline 内の
  改変不能な過去履歴で post-baseline は 0 件。**健全で修理対象なし。**
  (2) `orchestrator/tests/flaky_test_holds.py` の 3 件は並行 job が担当。
  (3) `orchestrator/test_selection_contract.py` の恒久除外表は `SANCTIONED_EXCLUSIONS = ()` で空。
  (4) F489 の 4 例目が未修理で、しかも並行 wave 1 本の land を実際に止めていた。
- **並行 3 session と担当分けを SendMessage で合意した。** 相手は
  `dev-wave flake test correction` (flaky holds 担当) と
  `dev-wave-t1814-shard-time-balance`。後者はこの赤で land できず、
  (a) file 除外 / (b) node hold / (c) 実装修理 の 3 択を相談中だった。
  **ユーザー裁定で「受理集合を変えず、実装修理の land を待つ」と確定し、
  本 wave が (c) を引き取った。** t1814 は `flaky_test_holds.py` にも
  `test_selection_contract.py` にも触らないと通知済み。
- **親の確率見積りが誤っており、並行 wave の指摘で訂正した。** 親は「修理前でも 1 走緑になる
  確率は 9 割近い」と書いたが、これは 1 判定あたりの緑率 (91.7%) であって 1 走の値ではない。
  脆弱 6 node × preflight/recheck の 2 phase = 1 走あたり 12 判定なので、正しくは
  `(1-0.083)^12 = 35%`、尤度比 2.8 対 1。**結論 (1 走緑は修理の証拠として弱い) は変わらないが、
  桁が違うため裁定文と段 3 の prompt へ訂正を反映した。**
- **段 3 の 2 レンズは結論が割れた。** 正しさレンズは「plan の per-pid 再検証も親の代案も採るな、
  まず診断だけ入れて実 issue を測れ」、運用レンズは「per-pid 再検証を実装して 5 走観測せよ」。
  親はどちらとも異なる形へ落とした — **受理する観測の中身 (`valid` 述語) は 1 文字も変えず、
  再試行してよい条件から種別の縛りだけを外す。** 現行コードも既に取り直した scan の clean を
  受理しており、変わるのは試行回数だけである ({{D:occupancy-retry-by-persistence}})。
- **正しさレンズの所見 1 件を既存リスクとして棄却した。** 「cwd `PermissionError` が非 issue で
  ある現行契約により実 occupant を受理しうる」は正しいが、これは D706 の既裁定であり
  (この共有 login node では cwd を読めない他ユーザー process が実測 2,020〜2,213 件あり
  `cwd_permission == 0` は恒久的に到達不能、F490)、**本 wave の変更前後で同一である。**
  受理集合の差分ではない。
- **段 2 の plan は採らなかった。** per-pid 再検証は (a) 初回に正常だった pid の snapshot を
  古いまま保持しつつ scan 窓を約 0.23 秒から約 1.69 秒へ広げる、(b) sleep の注入口が無く
  恒常 issue の既存 node が各約 1 秒増える (duration ledger の現値は 0.001〜0.002 秒)、
  (c) 呼出回数依存の既存 monkeypatch が尽きて `StopIteration` になる、の 3 点で退けた。
- **段 5 の実装子 2 本は計算ノードへの dispatch が全件 rc=16 で 1 件もテストを走らせられず、
  正直に「実装済み・未実走」と報告した。** 原因は codex sandbox からの
  `qstat -Q` が `EACCTAUTH: Unknown user-id` を返すこと。親が実走で補完した。
- **段 6 の敵対レビューが親の裁定文の誤りを 2 件見つけ、どちらも採用した。**
  (1) 登録変異 M2 (再試行述語から `occupants == []` を外す) は**冗長 gate であり equivalent**。
  占有していれば手前の分岐が先に rc=21 で拒否するため観測可能な差が出ない。
  「M1〜M6 全 KILLED」という解除条件は達成不能なので、DW-M03 に従い
  **期待 SURVIVED として理由付きで登録し直した。**
  (2) 「成功時診断の `retry_count` を canary とする」は**読み手が存在しない**。
  親は主張を取り下げ、閉じるのは事後診断だけだと明記した
  ({{D:occupancy-canary-is-postmortem-not-early-warning}})。
- **段 6 の敵対レビューが実装の穴も 2 件見つけた。** (1) 診断整形の fallback だけが
  byte 上限の検査を飛ばしており、制御文字 (JSON で 1 byte が 6 bytes へ膨らむ) を含む入力で
  **JSON が途中で切れ `issues_omitted` が失われる**。件数のみの縮退形へ落とすよう直した。
  (2) 裁定が要求した合成 `/proc` の正例・負例が、実装子 2 本とも**両方の層で依存先を stub**
  しており、実際の走査が変化する `/proc` に対して一過性 issue を解消できるかを
  誰も検査していなかった。fix で実 scanner を連続で呼ぶ形へ置き換えた
  ({{F:stubbed-dependency-hides-the-mechanism}})。
- **親が変異走行中に spool fragment を書いて harness を止めた** (`untracked file を検出`)。
  DW-M05 の「変異中は親の編集と worktree へ書きうる子の起動を止める」に親自身が違反した。
  fragment を commit してから回し直した。
- **変異 matrix は 9 件を事前登録し、本走で 9/9 一致した** (baseline PASSED、KILLED 8、
  SURVIVED 1、MISMATCH 0、TIMEOUT 0)。唯一の SURVIVED は M2 (再試行述語から
  `occupants == []` を外す) で、**敵対レビューが equivalent と予測し親が期待 SURVIVED として
  登録し直したものが、実測でそのとおりになった。** 本 wave の主目的を戻す M1 は
  新設 2 node と既存 1 node に、受理集合を広げる M3 は既存 2 node に殺された。
  段 6 の正しさレンズが「恒真」と名指しした
  `test_main_does_not_retry_occupied_scan` / `test_main_does_not_retry_invalid_target_scan` も、
  再試行の guard を外す M9 が実際に殺したので恒真ではなかった。
- **エージェント工数**: codex 子 8 本 (plan 1 / consult 2 / author 2 / review 2 / fix 1、
  うち author 2 本は dispatch 不能で未実走報告)。親の dispatch した焦点走 5 回、
  変異走 2 回 (probe + 本走、各 baseline 1 + 9 変異)。

## 次の一手差分

### 新規

- {{T:occupancy-issue-scoping}} **P2・新規**: 占有検査の `issues` を「対象 path に関係しうる
  process」へ絞る筋を設計する。本 wave は緩和策 (取り直し) だけを入れ、根の設計は見送った。
  次に踏む人が再調査しないための実測: process 数 2,177〜2,197、1 scan 約 0.23 秒
  (login node 静穏時)、判定あたり赤率 8.3%、clean scan 92%。証明可能な部分集合は
  pid 消滅・zombie・対象外 deleted-cwd・identity 安定下で cwd と cmdline を両方完全に読めて
  対象と一致しない process の 4 つ。ただし現行の `issues == ()` は完全観測フラグではないため、
  絞るなら完全観測フラグを別に作る必要がある。D821 は lease / cgroup / 特権 observer による
  正の証拠を要求しており、受理集合の再設計になるためユーザー裁定を要する。
- {{T:occupancy-retry-rate-canary}} **P3・新規**: 掃除の成功時診断 `retry_count` に
  自動の読み手を作る。本 wave は実 `/proc` を走査する成功 6 node を stub 化したため、
  受入全走は unoccupied 成功経路を再現しない。悪化を land 前に察知する経路が無い。
