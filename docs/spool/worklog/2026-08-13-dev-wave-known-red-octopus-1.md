---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-known-red-octopus
seq: 1
title: main の恒久赤 (4 親 merge) を履歴契約の n 親一般化で直し、受入赤の非帰属を実測で決める checker を足した (コード + docs、branch worktree-dev-wave-known-red-octopus)
---

## 本文

ユーザー依頼「既知のテストの赤を修正してください。また、既知の赤で main land が失敗するのを
失敗しないようにしてください。人間も AI も間違えることはあります。その間違いは一度犯したら
後続の全てが停止するべきではなく、後続のセッションが可能なら直す、難しければ新しい dev-wave で
直すのが適切な営みです」の wave。**この依頼が F269 の「未裁定として残る選択肢」のうち
(b) 履歴契約の n 親拡張を確定させた** ((c) merge 作り直しは rebase / force 禁止で実行不能)。

**赤の正体は偽陽性だった。** `d1de13ad` の 4 親と merge 本体について freeze 状態を決める 3 path の
blob OID を実測すると **5 commit すべて完全一致**で、保護対象は 1 bit も動いていない。
現行実装が拒否していた理由は**親の個数だけ**である。したがって本 wave の A は「正しさゲートを
緩める」変更ではなく偽陽性の除去であり、規律 2 に抵触しない。修正後、`validate_condition_freeze_at`
は main HEAD を含む履歴で緑を返す (修正前 `RED [octopus-merge] d1de13ad` → 修正後
`GREEN generation=1`)。設計判断は {{D:n-parent-history-transition}}。

**台帳の矛盾を 1 件見つけた。** F266 の恒久対応は複数 branch の取り込みに
`git merge --no-ff --no-commit <b1> <b2> <b3>` (親 = main + 各 branch) を命じ、F269 の恒久対応は
「3 親以上の merge を作らない」と命じる。**同じ操作について正反対**であり、`d1de13ad` は
F266 の指示どおりに作られたものだった。本 wave は F266 側を採り契約の方を直した。
記録は {{F:contradictory-remedies-across-ledger}}。

**依頼の後半 (既知の赤で land が止まらない) は、段 3 の敵対レビューで設計を差し替えた。**
段 2 プランは「既知赤の機械可読な登録簿」を提案したが、レンズ B が blocker 6 件を返した。
決定的だったのは **`authority: user` のような field を書くのは AI 自身**であり、
自分が壊した赤を自分で既知赤として登録できてしまう点である (D316 が却下した W1 形式と同型)。
親は登録簿を破棄し、**帰属を宣言でなく再実行で測る** `tools/check_acceptance_reds.py` へ
置き換えた。設計判断は {{D:acceptance-red-attribution-by-rerun}}。

**段 6 のレビューはこの checker に fail-open を 6 件見つけ、全件塞いだ。** 代表は
(i) terminal 集計行より後ろ・header より前の `FAILED` 行を無視して緑にできる、
(ii) probe worktree を全 node で使い回すため、先行 node が残した ignored file や未初期化
submodule で「main でも赤」を捏造でき、自 wave の赤を非帰属に変えられる、の 2 件。
**塞げていない残余は正直に残す** — 任意の過去 log を渡せる点、受入 argv / raw rc が receipt へ
束縛されない点、`dev_wave_land.py` が受入結果を検証しない点 (F101 で既知)、
SIGKILL 経由の probe 残骸。これらは裁定パッケージへ返す。

**fix 子が 1 度正しく停止した。** 親の fix prompt が「既存テストの期待値を変えるな」と書いた一方で、
変更が必要な期待値は**本 wave 自身が作った新規テスト**だった。子は矛盾を検知して着手前状態へ
完全復元し、SHA-256 一致を報告した。親が prompt を訂正して再投入した (tracked な既 land テストと、
同 wave の新規テストを区別して書く必要がある)。

工数は Codex 8 本 (plan 1・consult 2・author 2・review 2・fix 3 のうち 1 本は上記の正当な停止、
`gpt-5.6-sol` / `gpt-5.6-luna`、reasoning=max / high)、変異 harness 走行 4 本
(うち 3 本は argv 契約の誤りで起動前中止: `--wrapper-attempt` は整数、`--attempt-out` と対指定、
`--force-dispatch` 必須)。

## 次の一手差分

### 新規

- {{T:acceptance-log-authenticity-binding}} **P1・新規**: `tools/check_acceptance_reds.py` に
  渡す受入 log が**真正な受入走のものである**ことを機械で束縛できていない。任意の過去 log を
  渡せば、attributable な赤があっても rc=0 に到達しうる。受入 argv・環境・pytest raw rc も
  receipt に束縛されていない。checker が受入走の起動と log の atomic capture を所有する形か、
  別の束縛かを裁定する必要がある。
- {{T:land-verifies-acceptance-receipt}} **P1・新規**: `tools/dev_wave_land.py` は tested main /
  tip の SHA を受け取るだけで**受入結果を一切検証しない** (F101 で既知)。本 wave が足した
  checker も、発火は受入 command の rc に依存し land 層の機械的強制が無い。
  land が acceptance receipt を lock 内で再検証する形をユーザー裁定へ返す。
- {{T:run-tests-login-path-skips-preflight}} **P2・新規**: `tools/run_tests.py` は Pegasus login の
  headroom が足りる経路で bounded test を先に実行して child rc を返すため、
  受入 preflight (未 stage 削除 / RuleOps / submodule) に到達しない場合がある。
  受入健全性に関わるので独立に確認して直す。
- {{T:history-state-ignores-nonhashed-fields}} **P3・新規**: `_HistoryState` は
  `docs/phase3-8c-preregistration.md` の §0 / §5 の値と evidence JSON の表記差を hash 対象に
  含めないため、「状態は同値だが tree は異なる」merge を受理する。**n=2 でも同じ**穴であり
  本 wave が作ったものではない。freeze projection の exact 一致を課すかを裁定する。
- {{T:stale-probe-worktree-reaper}} **P3・新規**: `check_acceptance_reds.py` の probe worktree は
  SIGTERM / SIGHUP / SIGINT では撤去されるが、SIGKILL・host crash では残る。
  残骸は全 wave の land を止めるため、起動時または lease 内の stale reaper を検討する。
