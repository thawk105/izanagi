## 所見

1. **must-fix — 正例 test の接続が曖昧。** plan は「小さい Git source」で写しを検査する一方、builder が読む元は固定の `ROOT` です。写しメソッドだけの試験では、「写しを作るが builder は `ROOT` から複製する」変異を殺せません。[plan](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/codex/s2-plan-out.md>)、[builder](</work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1458>)。**最小是正:** 小 Git 正例で写しの集合・bytes・一回生成を検査し、既存の実 builder 検査に「`copytree` の複製元が完成した局所写し」という assert を一つ足す。二本の新規 test は必須ではない。既存の全件性検査二か所と、写し経由の正例は残す。

2. **should — lock・marker・残骸処理は重複して見えるが、別 key の同時 builder には同期が必要。** 既存 `get()` の lock と `complete.json` は **key ごと**なので、七つの key に共通する写しを一回だけ作る保証にはなりません。[共有 base](</work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:920>)。専用 flock、完成 marker、失敗後の残骸削除は残す。ただし `get()` と同型の短い処理に収め、独立した汎用 cache 基盤や新しい残骸管理 test は足さない。marker を `output` 外へ置く判断も、複製集合を汚さないため妥当。

3. **should — 変異五本をすべて別検査で支える必要はない。** 直接複製への逆戻り、写しを作るだけで使わない経路、可視 file の脱落は正しさ・効果に直結するので kill を残す。marker 欠落は二回目の生成回数で、`shutil.copy` への変更は mtime で、同じ正例から検出できる。mode だけでは `shutil.copy` 変異を殺せません。[plan の変異表](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/codex/s2-plan-out.md>)。五本の変異を口実に新たな test・台帳を増やさず、既存 test への接続 assert と一つの正例で足りるかを先に確認する。

4. **should — `get()` に写しを「一つの base key」として載せる案は、そのままでは等価でない。** `get()` は五項目 key から実 builder を呼び、repo root と document を返す契約です。写しは `output/` だけで、七 key の builder に先立って共有されます。載せるには汎用 builder 引数、返り値、再入時の lock 順序まで変更する必要があり、この一ファイルの局所修正より広がります。[`get()`](</work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:945>)。builder に「複製元」を引数で渡す案は成立しうるものの、全呼出しの変更が要る。現案の小さな写しメソッド＋builder の一箇所分岐を優先する。

5. **must-fix — brief の完了判定は測定前 land を許す文面。** 原依頼は「隣接対の実受入で効果を測ってから land」です。[依頼](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/verbatim/T-2273-origin.md>)。brief の「land し、対差を記録」は順序と効果不成立時の扱いを欠きます。[brief](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/s1-brief.md>)。**最小是正:** 下記の land 条件を系列投入前に固定する。五分未達でも明確な改善なら「五分目標は未達、段階的改善として land」と記録できる。変化なし・退行・判定不能なら性能改善として land しない。

6. **should — brief の数値は出所を限定すれば整合する。** 310.7〜344.9 秒は T-2825 の **B 条件三走**の shard-0 W₀（310.663、334.439、344.931 秒）で、常時の範囲ではありません。[前回走表](</work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/output/insights/2026-09-21/t2825-ledger-refresh-ab/README.md>)。−123.9 秒／−27.3% は 454.6→330.7 秒の一対から正しく丸められていますが、X は事前 staging 済みで、今回の遅延生成費用を含みません。診断の 29,885 は除外前の**可視 path 集合**で、実複製 file 数として書けません。90.1〜111.5 秒は診断走の値であり、今回の実装効果の予測値ではありません。[第4回診断](</work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/output/insights/2026-09-23/t2273-shard0-bottleneck-4/README.md>)。

7. **should — 2 node 時間未満の見積りには余白が小さい。** 0.25 node 時間×六走＋最終受入一走で **1.75 node 時間**。残り 0.25 に両 tree の温め、変異、無効対の再走は入る保証がありません。前回は有効三対に七走を投入しました。[前回測定手順](</work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/output/insights/2026-09-21/t2825-ledger-refresh-ab/README.md>)。**最小是正:** 0.25 を概算単価と明記し、投入済み node 時間と残る必須走を毎対後に見積もる。2 時間以上が見込まれた時点で親がユーザー確認を取る。外側の投入→完了時間には queue 待ちが混ざるため、それを node 時間へ代入しない。

## 事前登録の提案

- **比較対象・順序:** 測定時 local main の clean な A と、A＋実装差分の clean な B を SHA 固定する。`A,B / B,A / A,B` の隣接三対を逐次投入し、測定中は自分の他 job を走らせない。固定二 tree は時刻の近い対照を作るが、同一 node・同一 allocation ではない。この限界を結果に明記する。[D357](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/verbatim/D357.md>)、[前回の測定形](</work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/output/insights/2026-09-21/t2825-ledger-refresh-ab/README.md>)。
- **投入・有効性:** 前回と同じ他受入 leader ≤1、load1 ≤60 の門番、各 tree の HEAD・clean、同じ環境・collection・選択 node・skip 集合、三 shard の JUnit/report と緑を確認する。infra 赤は理由を分類し、その走を含む**対全体**を同順序で取り直す。実装由来の赤は無効走として捨てず、修正して測定を最初からやり直す。
- **判定量:** 各対の `Δᵢ=W₀(Aᵢ)−W₀(Bᵢ)` と `rᵢ=Δᵢ/W₀(Aᵢ)`、それぞれの中央値を別々に報告する。条件別中央値の差とも混同しない。保守的な land 条件は、三対すべて `Δᵢ>0`、かつ対率中央値 `≥10%`。10% は前回の運用閾値であり、D357 から導かれた統計的有意差ではない。[前回集計器](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/probe/t2825_ab_analyze.py:230>)。
- **補助量・五分目標:** 各走の Wmax とその最遅 shard、shard-0 の Omax・L・`Omax−L`、可能なら builder 待ちを併記する。五分達成は B の Wmax 三走中央値 `≤300秒` として別判定にする。land 条件を満たし五分未達なら、未達を明記して段階的改善として land。方向不一致、対率中央値 10% 未満、又は判定不能なら land しない。
- **probe の最小改作:** job dir・slug・差分対象を今 wave に替え、台帳固有の hash／予測負荷／shard 移動／旧 L 判定を集計器から外す。`warm_errors()` は前回の `warm-A/B.json` を要求するため、同じ両 tree collect-only 温めを行うか、その前提だけ外す。投入順・門番・対全体の再走・W₀/Omax/L の抽出は再利用できる。[run-series.sh](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/probe/run-series.sh>)、[run-measure.sh](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/probe/run-measure.sh>)、[集計器](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/probe/t2825_ab_analyze.py:344>)。

## 総括

**修正後 GO。** 写しの専用同期は必要だが、新規 test 二本や汎用 cache 化は不要。実 builder の複製元まで正例で押さえることが最優先。測定は三つの隣接対で成立するが、同一 node の比較とは呼べない。land は測定後の事前登録判定に従い、五分達成と改善の有無を分けて記録する。