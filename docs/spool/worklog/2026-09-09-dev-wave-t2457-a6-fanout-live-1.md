---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2457-a6-fanout-live
seq: 1
title: [T-2457] A-6 認証を 5 ノードで実走し 73 分が 17 分 37 秒になった — 最初の実走は 5 秒で落ち、先行 wave が「実測」と書いた前提が誤りだった (コード + テスト + insight、branch worktree-dev-wave-t2457-a6-fanout-live、変異 5 件すべて KILLED・期待ノード完全一致)
---

## 本文

- **wave の形が途中で変わった。** 段 4 では「実装面の差分ゼロ」と裁定していた
  (`collect` を行わなければ repo を書かないため)。実装の必要は実機の失敗で初めて判明し、
  そこから Codex author 子・敵対レビュー 2 本・fix 子・変異 matrix が必要になった。
  依頼の「本題の実走と記録だけ」の範囲内と親が裁定した — 直したのは依頼された実走を
  可能にする最小差分であって、仮想リスク向けの gate ではない。
- **変異の事前登録が実装より後になった。** 上の経緯による。DW-M01 の「実装前に登録する」を
  満たしていない。期待ノードも静的に確定できず、DW-M07 に従い全件 SURVIVED の probe 走で
  観測ノードを集めてから再登録した。probe 走の結果は消していない (insight に erratum)。
- **段 6 レビュー A の must-fix 1 件を親が実測で却下した。** 「非 head rank の診断 stderr が
  durable な `job.stderr` を更新し、会計証拠と競合して `finish-group` を止めうる」という
  指摘だったが、会計検査の正規表現は `^Request ID:` と `^Group Name:` の行に錨を打っており、
  当該 1 行はどちらにも掛からない。4 行入った `job.stderr` に対して `finish-group` が rc=0 で
  受領証を作ることを実測した。この 1 行は gate が実機で発火した唯一の証拠なので残した。
- 段 3 の敵対相談が親 brief の誤りを 1 件訂正した — 「policy SHA も protocol SHA も前回実走と
  同一」は偽で、`scheduler.nodes` を 5 にした変更は policy bytes に入る。protocol SHA だけが不変。
- 子の工数: 段 3 相談 1 本、段 5 実装 1 本、段 6 レビュー 2 本、段 6 fix 1 本 (すべて
  codex `gpt-5.6-sol` / xhigh)。実装子と fix 子はいずれも `run_tests.py` が `rc=16`
  (`qstat -Q preflight rc=1`) で実走できず「実装済み・未実走」で戻した。テストは親が実走した。
- **段 8 の自己改善 1 件は byte 予算で入らなかった。**
  {{F:probe-summary-file-cannot-discriminate-per-rank}} の恒久対応を
  `docs/dev-wave/core.md` の `DW-G01` へ 2 行足そうとしたところ、L1 の unique footprint が
  10,835 bytes となり予算 10,625 を 210 bytes 超えて `check_docs.py` が赤になった。安全義務を
  削って詰めることはせず、恒久対応の実体を memory
  `liveness-probe-must-separate-observation-per-subject` に置いた。上限の引き上げは求めていない。
- 設計判断は {{D:certification-body-runs-on-job-number-zero-only}}、
  失敗は {{F:probe-summary-file-cannot-discriminate-per-rank}}。

## 次の一手差分

### 完了

- [T-2457] fan-out を有効にした A-6 の新しい attempt を 5 ノードで実走した。実機経路 4 点と
  所要を実測し、73 分 (4382 秒) が 17 分 37 秒 (1057 秒) になることを確かめた。最初の実走は
  job body が全 rank で走って 5 秒で落ちたので、job 番号 gate を足して直してから測り直した。
  remaining: none
  base: 10470cb1065a6d68891b14fc08eb7f9aea9c335ab84f263b360338ba596cc6a5

### 新規

- {{T:fanout-ssh-cgroup-equivalence}} **P1・新規**: rank 終了後の ssh session が rank process と
  同じ cgroup / cpuset / CPU affinity に属するかを実機で測る。属さないなら遠隔検査は割当の資源
  保証の外で走っており、`pgrep` の競合 probe はそれを証明しない。17 分 37 秒という所要の
  解釈にも関わる。
- {{T:fanout-remote-total-timeout}} **P2・新規**: 遠隔検査へ walltime より短い総 timeout を
  入れるか裁定する。現状 ssh の呼び出しに timeout が無く、head は全 future の完了を待つので、
  証拠上の hard bound は 12 時間の walltime だけである。
- {{T:a6-fanout-attempt-as-second-sample}} **P1・ユーザー裁定待ち**: 実行基盤の測定に付随して
  得られた A-6 の性能値 (効果 −4.876%、前回 −5.784%) を、A-6 の 2 本目の attempt として扱うか。
  扱うなら [T-2430] が書いた手順 (attempt 数と停止基準の事前登録、`tracked_destination` の
  新 leaf) に従う。扱わないなら実行基盤の副産物のまま残す。
- {{T:a2-certification-nodes-five}} **P2・新規**: A-2 (rr5 / rr50) の `scheduler.nodes` を 5 に
  して同じ短縮を得るか裁定する。job body 側の契約は A-2 でも通ることを確認済み。
