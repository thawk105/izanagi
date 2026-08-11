# 依頼 — docs-only 差分の敵対レビュー (防御目的)

あなたは izanagi プロジェクトの**防御側**レビュアである。目的は、これから運用規範として
使われる文書が誤った運用 (交絡した計測・偽の成果物同値・過大な機械保証の主張) を招かないことを、
公開前に確認することである。攻撃的な指摘を求めるのは、実害が出る前に自分たちで潰すためである。

## 前提と制約

- 実行環境は read-only sandbox である。**pytest やビルドを走らせる必要はなく、走らせられない。**
  静的検査だけでよい。テスト実測は親が行う。緑を主張しないこと。
- 下記のファイルが読めない場合は、推測で書かず**即座に停止**し、読めなかった path を報告すること。
- **巨大ファイルを全文走査してはならない。** 読む範囲は下で明示する。範囲外の網羅読みをしない。

## 読むもの (この順で、指定範囲だけ)

1. `/work/1/SFC/tanab/dev-wave-jobs/t809-fanout-conditions/wave.diff` — 本 wave の差分全文 (66 行)。
2. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t809-fanout-conditions/output/insights/2026-08-11_t809-fanout-conditions/brief.md`
   — 親 brief (段 1)。scope・裁定・不変条件・provisional 裁定 (P1)(P2) が書いてある。
3. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t809-fanout-conditions/output/insights/2026-08-11_t809-8c-workload-fanout/package.md`
   — 先行評価 wave の裁定パッケージ (208 行、全文可)。§5 が裁定を求めた問い、§6 が明文化すべき条件。
4. `docs/pegasus-runbook.md` の **§7.5 だけ** (904 行目〜1085 行目付近)。それ以外の節を読まない。
5. `docs/phase3-s8c-autonomous-trial-runbook.md` の **§5 だけ** (194 行目以降)。必要なら §3〜§4
   (55〜193 行) を参照してよいが、それ以外は読まない。

repo root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t809-fanout-conditions` である。

## 背景 — 確定済みユーザー裁定 (これは覆せない前提)

RP-1 (a) trial 本体の分割は実装しない / RP-2 (a) build を伴う fan-out は許さない /
RP-3 (c) 正式 6 trial のノード配置は着手時に再評価 (ただし「6 process だから 6 node」の誤読はいま潰す) /
RP-4 (a) 部分成功の意味論は現状維持 / RP-5 (a) 再投入は経路別に明文化 /
RP-6 (c) 運用規範は pegasus-runbook §7.5、trial 固有の条件は 8c runbook。

**裁定そのものへの反対意見は求めていない。**求めているのは「裁定どおりに書けているか」
「書いた文が誤運用を許さないか」である。

## 攻撃してほしい観点

1. **裁定との不一致。** RP-1〜6 のうち、差分が取りこぼした・曲げた・書きすぎた点はあるか。
   とくに (P1)「1 行ずつ」の解釈、(P2) 部分成功を書かない判断は妥当か。
2. **誤読の余地。** 悪意なく急いでいる運用者が、この文だけを読んで
   (i) 6 trial を 6 node へ散らす、(ii) build 付きで fan-out する、(iii) 成功した N-1 本だけで
   集計する、(iv) N 本を 1 trial と同値と呼ぶ、のいずれかへ到達できる読み筋はあるか。
   到達できるなら、その逐語と最小の修文を示せ。
3. **事実誤り。** 差分中のコード由来の主張 (`_check_workload_coverage`、`CrossRoleSessionTracker`、
   `lifecycle-start-once`、`bench_lock` / `competing_bench_pids`、campaign freshness gate、
   `IZANAGI_EXPLORATION_OUTPUT_ROOT` の git 配下拒否、manifest の exact 6 と hash 一致要求) が、
   実コードと食い違っていないか。該当 module を必要な範囲だけ確認してよい
   (`orchestrator/campaign/` 配下)。
4. **恒真な保証・過大主張。** 「人手確認であって機械保証ではない」と書いた箇所が、
   実際には機械強制されている / 逆に機械強制と誤読される書き方になっていないか。
5. **既存記述との矛盾・重複。** §7.5 の他の小節 (とくに「ノード間の性能差は未測定である」
   「並行にしない面」) や 8c runbook §3〜§5 の既存記述と、矛盾または冗長な重複がないか。
   重複は docs 予算の無駄なので、削るべき逐語を示せ。

## 出力形式

Markdown で、各所見に **blocker / should / nit** の重み、対象ファイルと逐語、
「これを直さないと成果物 (certified 選択・レポート・台帳) のどの値・受理集合・参照がどう変わるか」
の 1 行を付けること。書けない指摘は nit とすること。

最後に必ず `## 総括` 節を置き、全体判定 (差分をこのまま採用してよいか) を 1 行で書くこと。
