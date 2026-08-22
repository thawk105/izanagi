---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-lease-serialization-ban
seq: 4
title: 受入 lease の待ちループと待ち行列を機構ごと除去した (コード+テスト+docs、branch worktree-dev-wave-lease-serialization-ban、変異matrix = baseline PASSED・MUT-1〜8 8/8 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- ユーザー依頼: 「dev-wave で lease の直列化をやらないよう厳しく制限する。Pegasus 計算ノードが
  混雑しており、lease の直列化で研究が破滅している」。D662 決定 1 は 2026-08-22 に待ち行列廃止を
  裁定済みだったが、実装は opt-in flag に留まり、入口 command は同じ日に
  「lease を取れたときだけ投入せよ」と命じたままだった。設計判断は {{D:lease-wait-unreachable}}。
- **親 brief の実測解釈を段 4 で訂正した。** 段 1 で「lease が free なのに待ち札 4 枚が滞留し、
  新着 wave が `queued` になる状態が現に発生している」と書いたが、段 3 敵対レンズ (sol) が
  待ち札の stale 閾値 300 秒を根拠に反証した。観測した 4 枚は齢 12〜17 分で全て stale であり、
  その瞬間に新着が `queued` になることはなかった。正しい主張は「直前 17 分の間に 4 つの wave が
  即取得できず札を登録した」という混雑の証拠であり、各札の fresh な 300 秒窓の間だけ
  free lease でも新着が `queued` になる。依頼の定性的な結論は worklog entry 831 の実測
  (15 件以上の並行 wave が同時ブロック、最長 63 分超) が独立に支持しており変わらない。
- **段 3 レンズ B の所見 1 件を refuted にした。** 「並行 branch `worktree-dev-wave-lease-cmd-entry-sync`
  が DW-O27 を checker の必須集合から外す」は実 diff と食い違う。同 branch の
  `tools/check_docs.py` 変更は段 6 逐語 3 行だけで、`REQUIRED_REFERENCE_SECTIONS` と条件 18 の
  `DW-O27` は無変更。`orchestrator/tests/test_check_docs.py` はむしろ decoy case を 2 件
  追加して入口検査を強化している。
- **段 3 レンズ A の懸念 1 件は方向が逆だった。** 「既定を unclaimed にすると no-verdict retry が
  通常経路で失われる」— retry gate が lease 所有を要求するのは事実だが、本 wave は `queued` を
  `acquired` へ変えるので ACQUIRED 頻度は上がる。retry 可用性は悪化せず改善する。
- **段 6 レビュー A の must-fix 1 件 (M2) を不採用と裁定した。** 「`held`/`queued` の malformed
  payload を fail-closed で拒否せよ」は、lease directory の破損という一点で全 wave の受入が
  止まる設計であり、D662 が否定した「一つの wave の不具合が全体を止める」形そのものである。
  実害も無い — 未取得経路は claim payload の holder と main SHA を採らず自分で計算した値を使う。
  残る細部 (`holder` が自己 digest なのに `holder_self:false` なら lease を取り逃す) は、
  待ち行列廃止後は誰も止めないので nit として裁定パッケージへ送る。
- **段 6 レビュー B の結論**: 現 tip の受入経路から、lease の `held`/`queued` を理由にした
  待機・poll・再 claim・待ち札登録は到達不能。flag の有無に関係なく 1 回だけ非 blocking claim。
- 段 6 で残った must-fix は 2 巡で全件 closed。Pin C を state × flag の 16 ケースへ展開し、
  race 3 件 (`FileExistsError` retry / stale lease 消失 retry / 所有外 ticket を消さない cleanup) を
  新設し、Pin A の docstring を「未取得経路の投入前 claim は 1 回」へ限定した。
- **codex 実装子 3 本とも pytest を実走できなかった** (`qstat -Q` が sandbox から届かず rc=16、
  child 未起動)。全員が「実装済み・未実走」と正直に申告し、親が計算ノードで実走した。
- **非帰属赤 1 件を実測で確定した。**
  `test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean` が login node で
  再現的に落ちるが、main (83baeefa) の detached probe worktree でも同じく落ち、計算ノードでは
  緑になる。lease と無関係な `IZANAGI_EXPLORATION_OUTPUT_ROOT` の外部 output root 検証であり、
  本 wave に非帰属。
- **手順ミス 1 件**: 変異 probe の走行中に spool fragment を untracked で作り、harness が
  `runner/test 実行前に untracked file を検出` で rc=2 中止した。変異前に止まったので実害なし。
  memory `no-acceptance-run-during-mutation` の「tree へ書かない」に該当する。
  probe attempt 1 は `fresh --attempt-out が既に存在する` でも rc=2 になり、DW-O19 に従って
  `--out`/`--attempt-out`/`--wrapper-attempt` を毎回新しくする runner へ直した。
- 進捗報告の JST 時刻 5 件を実測せず推定で書いた。F1 の再発として記録した。
- 入口 `.claude/commands/dev-wave.md` の段 6 文言は本 wave の scope 外に置いた。
  `worktree-dev-wave-lease-cmd-entry-sync` が同じ行と `tools/check_docs.py` の逐語 pin を
  所有しており、触れば land で競合するためである。両レンズが「最大の穴」と判定した real 所見であり、
  同 branch が着地するまで入口は旧条件を命じ続ける。

## 次の一手差分

### 新規

- {{T:lease-noverdict-retry-unclaimed}} **P2・ユーザー裁定待ち**: 未取得 (`held`) 経路でも
  no-verdict retry を許すか。現行は lease 所有を要求するが、この条件は待ち行列時代の前提に由来する。
  受理集合の変更なので本 wave では実装しなかった。
- {{T:lease-compat-flag-removal}} **P3・ユーザー裁定待ち**: no-op になった `--lease-optional` と
  `--poll-seconds` を将来削除するか。稼働中の並行 wave が rc=2 で死ぬのを避けるため今回は受理を残した。
- {{T:dev-wave-entry-lease-condition-pin}} **P2・新規**: 入口 command 段 6 を、no-op フラグ名でなく
  「lease の取得可否で受入投入を止めない」という条件そのもので pin し直す。
  `worktree-dev-wave-lease-cmd-entry-sync` の着地後に行う。
- {{T:exploration-output-root-login-red}} **P2・新規**: login node でのみ再現的に落ちる
  `test_exploration_external_root_keeps_wave_clean` を調べる。main 単独でも再現し、
  計算ノードでは緑になる環境依存赤である。
- {{T:lease-holder-self-inconsistency}} **P3・新規**: `claim` が `holder` に自己 digest を返しつつ
  `holder_self:false` を返した場合、受入は未取得として進み lease を取り逃す。
  待ち行列廃止後は誰も止めないため実害は lease 残留 (TTL 2400 秒) だけだが、記録として起票する。
- {{T:dev-wave-docs-budget-saturated}} **P2・ユーザー裁定待ち**: dev-wave docs の予算が満杯で、
  実測した作法を 1 行も追記できない。段 8 で「変異走行中に tree へ書かない」(本 wave 実測、
  untracked 1 件で rc=2 中止) を DW-M05 へ足そうとして L1.5 が 9566/9566 bytes と判明し、
  140 bytes の追記で超過した。L2 側も DW-O19 が 998/1000、DW-M07 が 978/1000 で頭が無い。
  自己改善契約は「予算に収まらなければ止めてユーザー裁定へ返す」「予算値を上げる変更は
  独立審査対象」と定めるため実装せず起票する。予算引き上げか L1.5 の縮約審査が要る。
