単独段 dispatch: stage=consult; lane=luna; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root (read-only): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2`
- **親の段 1 brief (攻撃対象)**: `/home/SFC/tanab/.claude/jobs/c311da24/tmp/dev-wave-t1851-unit-c3b/s1-brief.md`
- **段 2 の plan (攻撃対象)**: `/home/SFC/tanab/.claude/jobs/c311da24/tmp/dev-wave-t1851-unit-c3b/out-s2-plan.md`
- 直前単位 C3a の記録: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-09_t1851-unit-c3a-wiring/README.md`
- C3a の裁定パッケージ: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-09_t1851-unit-c3a-wiring/ruling-package.md`
- 床値実走の runbook: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/phase3-8b-restart-runbook.md`
- 投入手順の正本: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/README.md`
- 機体固有情報の正本: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/pegasus-runbook.md`
- pilot 走行の一次資料: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-08-25_t1431-floor-pilot-values/README.md`
- 裁定台帳: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/decisions.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/CLAUDE.md`

# 段 3 レンズ B — 実効性と運用の穴から攻撃する

作業 root は read-only である。**書込み可能な tmp は無い。** pytest 緑を要求しない。
静的読解と grep による実測だけで結論を出す。**走らせていないものを緑と書かないこと。**

**file を 1 つも作れない。** 成果物は**最終メッセージの本文へ全文を書く**こと。

予算が尽きそうなら、**途中結論を下の出力形式どおりに書いて終わること** (無出力が最悪)。

この段では commit を作らない。git の状態を変えない。plan を守る義務は無い — **壊しに行くこと。**

## 攻撃対象

親 brief と段 2 plan の**両方**が対象である。レンズ A は正しさ境界と proof chain を見る。
**このレンズは「走らせて記録する」という運用が実際に成立するか**を見る。重複を恐れず、
しかし自分の観点を優先せよ。

親の provisional 裁定 4 件のうち、このレンズの主たる的は次である。

- **(P1-2)** receipt は `output/insights/` の `.md` 1 本とし、抽出 producer を新設しない。
- **(P1-4)** 1 job・1 ノード直列でよい。

## このレンズで必ず見ること

1. **「実装面の差分 0」は本当に成立するか。** 親は受入全走・変異 matrix を免除できると
   踏んでいる (`DW-S04` は「実装面の差分ゼロの wave だけ変異 matrix を免除する。受入全走は免除しない」)。
   - 走行の結果を receipt にするだけで、repo の tracked file が 1 つも変わらないか。
   - 台帳 fragment (`docs/spool/`)、insight directory、worklog は docs であって実装面ではない。
     しかし **`orchestrator/` 配下の非 `.md` は計測データでも実装面**である
     (path で決まる)。走行成果物をそこへ置く計画が紛れていないか。
   - 受入所要台帳など、新規 file を足すと必ず競合する台帳に触れないか。
2. **成果物の退避が参照を保つか。** runbook W-2 の最終段落は
   「run directory / content-addressed の binary store (`output/env/<env>/binaries/<sha>`) /
   submission receipt / job staging」の 4 点を 1 つの bundle にまとめ、構成 manifest と各 hash を
   残せと命じる。**run directory だけを残すと参照が dangling になる。**
   親の計画がこれを満たすか。使い捨て submit-tree を消した後に何が失われるかを列挙せよ。
3. **holdout clean-scan との衝突。** 走行が repo の `output/` 配下へ書いた成果物を残したまま
   次の official 床値 job を起動すると、その起動証明 (`clean_scan_digest` の hit 0 件要求) が
   止まる。除外は `output/s8b-freeze/` だけである。**本 wave が使う submit-tree は
   `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1851-unit-c3b/submit-tree` で、
   wave の worktree とは別 directory だが同一 repository の worktree である。**
   共有 admission root (git common dir 配下) を経由した相互作用が起きないかを追え。
4. **停止条件の実効性。** 次の既知の穴に対し、親の計画が実際に検出できるかを検査せよ。
   - `driver_rc=0` かつ `status: completed` でも床値が全 null になりうる。
   - `job-result.json` の書込みに失敗しても driver 成功なら wrapper は rc=0 で終わる。
   - `failure.json` は best-effort で、存在も内容も保証しない。最初の失敗 1 件だけ記録する。
   - job 開始直後に journal を見て最初の数 session が全滅していないかを確かめる必要がある。
5. **1 run で足りるか。** `DW-O13` は「時間予算は実測分布の max への倍率で決め、母集合と
   『観測 regime が適用対象と同じか』を併記する」と要求する。1 run の観測で
   **どの述語について何が言えるようになり、何が言えないままか**を表で示せ。
   親は「1 run の min/max を母集合へ一般化できない」を限界文言で処理する方針である。
   これで `DW-O13` の要求を満たしたと言えるか、言えないなら何が最小の追加か。
   **ただし「本数を増やせ」という提案は費用対効果で却下されうる** — 増やす本数と、
   それで初めて言えるようになることを対にして書くこと。
6. **投入から完走までの待ち設計。** pilot 実績は job Elapse 約 48 分。queue 待ちは別である。
   親は待ち手を 1 本だけ張る方針。**job 名は `qstat` の列で 8 文字に切れる**という既知の罠がある。
   生存判定と完了判定をどう書くべきかを具体的な command で示せ。

## 出力形式

次の H2 だけを使い、この順で書く。所見は 1 件ずつ `B-<番号>` で採番し、
**real か refuted か自分の判定を書き**、根拠を file:line か逐語で示す。

## 総括
## 所見
## 退避 bundle の構成案
## 1 run で言えること・言えないこと
## 待ち設計の具体案
## 未解決の問い

結合文字 U+0300〜U+036F を出力に使わないこと。
