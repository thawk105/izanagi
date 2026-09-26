## 所見

**B1 — must-fix｜完了判定 (a) は production 経路では成立しない。**
根拠: [brief:7–19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/s1-brief.md:7)、[buildcache.py:2707](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/buildcache.py:2707)、[buildcache.py:3456](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/buildcache.py:3456)、[pipeline.py:2162](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:2162)。両 build 経路は YCSB binary を選ぶ。allowlist 拡張で可能になるのは、別途用意した TPC-C binary を `_run_trace` に渡す経路と、その後の verifier 結合検査までである。**修正案:** 単位 5 の完了判定をこの範囲と親の実 trace probe に限定し、production `evaluate` が TPC-C を build・選択して認定する主張は後続の workload/build 配線へ送る。依頼と設計 §7.1 は buildcache を単位 5 に含めていない。
放置すると: 台帳が production の TPC-C 認定経路を完成済みと記録する一方、実際の候補は YCSB を実行する。

**B2 — must-fix｜完了判定 (c) の「受領証 digest に表・取引種別が載る」は、certified 正例では検査不能。**
根拠: [brief:11–13](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/s1-brief.md:11)、[core.py:194–218](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/core.py:194)、[core.py:284–292](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/core.py:284)。表と取引種別は anomaly の射影であり、正常な認定結果には anomaly がない。存在詳細も正常時は空リストになる。**修正案:** digest 試験は v3 の異常結果を用いて表・取引種別・存在詳細の束縛を検査し、certified 正例では「存在違反 0 を含む v3 射影の digest」と正確に記す。正常取引の表・種別を載せる新 field は本依頼からは導けない。
放置すると: 受領証が正常 TPC-C の取引種別と表を記録した、という誤った成果主張になる。

**B3 — must-fix｜pipeline 正例の試験案は allowlist を通らない。**
根拠: [plan:59–63](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/codex/s2-plan.md:59)、[pipeline.py:504–524](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:504)、[pipeline.py:434–440](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:434)。`trace_runner` を注入すると `_run_trace` 内の allowlist を迂回する。したがって同じ seam で flag 違いの事前拒否を期待する計画も成立しない。**修正案:** executor と実 verifier の結合試験はそのまま使い、flag 受理・拒否だけは実 `_run_trace` を使う小さい試験で分けて確認する。
放置すると: allowlist を消しても「TPC-C 正例」が緑のままになり、受理集合の変更を検証したことにならない。

**B4 — should｜§6.1 の witness 試験と変異の帰属が混ざっている。**
根拠: [plan:41](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/codex/s2-plan.md:41)、[plan:84](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/codex/s2-plan.md:84)、[test_campaign.py:7382–7414](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7382)。既存 tail-loss 試験は E 行も欠け、framing 違反だけでも赤になるため、「witness 引渡しを消す」変異の単独 kill にはならない。(c) と (d) も削除する txid の配置次第で別の integrity 違反が併発する。**修正案:** witness の変異 control は、完全な末尾 frame を取り除き、残存 trace の frame・txid が正常である一例を主にする。(b)〜(d) は欠落形態の確認として扱い、赤の理由を witness だけと断定しない。
放置すると: witness 配線が壊れても他の検査による赤を kill と誤認し、認定ゲートの検出力を過大記録する。

**B5 — should｜§6.1 の不足分は plan の見積りより少ない。実 CC 走は本単位から外すのが妥当。**
根拠: [plan:47–55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/codex/s2-plan.md:47)、[test_verifier.py:3475–3492](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:3475)、[test_verifier.py:3517–3542](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:3517)、[test_verifier.py:3903–3927](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:3903)、[patches/README.md:47–80](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/patches/README.md:47)。表識別、手書き G2、`read-unborn-genesis` と一行修正の対照は既存試験に対応づければよい。v3 lost update とその直列対照を合成 fixture で足すことを推奨する。実 CC 案は v3 source への patch 適用、計算ノード build、異常 schedule の発生と帰属確認が必要で、既存 patch の実証は YCSB に対するもの。**修正案:** 本単位では合成 fixture を採用し、実 CC の再現を完了条件に数えない。
放置すると: 試験が重複し、実 CC の schedule が出ないことを pipeline 配線の未完了と誤判定する。

**B6 — should｜新しい制約と abort reason の必要性を絞るべき。**
根拠: [plan:14–29](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/codex/s2-plan.md:14)、[plan:33–35](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/codex/s2-plan.md:33)、[brief:44–46](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/s1-brief.md:44)。`.exe` 接尾辞、`"043"`・`"00"` 排除の個別検査、`trace-schema-mismatch` という新 reason、不正な手作り `AnomalyV3` の CLI 例外試験は、依頼の四つの配線先を完成させる必須条件ではない。特に `.exe` は v3 emitter や計数修正の証拠にならない。**修正案:** 既定値の影響がある四つの flag と v3 拒否を検査の中心に置く。新 reason を採るなら v2 TPC-C 拒否の既存 reason では意味を表せないことだけを根拠にし、付随試験を増やさない。
放置すると: TPC-C の受理集合と WAL の reason 語彙が、必要性の示されない条件で変わる。

**B7 — should｜受領証 digest の変更範囲は plan が認める以上に明示が要る。**
根拠: [plan:5–7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/codex/s2-plan.md:5)、[core.py:284–292](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/core.py:284)、[test_verifier.py:3742–3749](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:3742)、[test_t1286_commit_receipt.py:345–416](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_t1286_commit_receipt.py:345)。既発行の v3 capability はあり得る。同じ v1 domain でも新射影によって v3 digest は変わり得る一方、v2 の dict は同じで、既存の framing・permutation 詳細除外も維持できる。**修正案:** 変更前後の v2 digest と CLI 実 JSON bytes を固定して比較し、v3 digest の新旧互換を主張しない。凍結された `report.py` と `verifier/__init__.py` は編集せず、既存試験の期待値も書き換えない。
放置すると: 古い v3 digest を新射影で再計算できると誤解し、受領証照合や台帳の説明が食い違う。

**B8 — nit｜呼び手の整理と行番号を直す。**
根拠: [cli.py:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/cli.py:90)、[pipeline.py:656](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:656)、[core.py:284](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/core.py:284)、[pipeline.py:146–151](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:146)、[plan:29](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/codex/s2-plan.md:29)。変更が必要な呼び手は CLI JSON、pipeline の拒否診断、capability の digest 射影の三箇所で、四つ目の「pipeline」は `_run_trace` と verifier 後の v3 判定である。plan の `pipeline.py:146–151` は flag の型保証ではなく、YCSB の既定値を定める箇所。旧射影を使う [silo_ladder_rung1.py:3056](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/silo_ladder_rung1.py:3056) と [reflux_result_evidence.py:738](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/reflux_result_evidence.py:738) は本 brief では YCSB 専用として除外され、切替対象に数えない。**修正案:** plan の根拠行と呼び手一覧をこの区分に直す。
放置すると: 配線漏れの判断と変更範囲の台帳が不正確になる。

**B9 — should｜二本の author 分割は path 上は素集合だが、この規模では一本が簡潔。**
根拠: [plan:86–90](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/codex/s2-plan.md:86)。A と B の所有 file は重ならない。ただし B の診断試験は A の射影を前提にし、B の正例試験は allowlist を迂回する案の修正も要る。約 260–440 行の見積りには削れる重複試験が含まれる。**修正案:** 一人の author が三つの production 呼び手と最小試験を一続きで実装する。二本を維持する場合も A の射影契約確定後に B を結合する。
放置すると: 結合前の片側だけでは診断と digest の成果を検証しにくく、試験重複が増える。

## 総括

単位 5 は、外部で用意した TPC-C v3 trace を pipeline の正しさゲートへ通す配線として実施できる。
現行 buildcache を含む production `evaluate` の TPC-C 認定は、この wave の差分だけでは到達しない。
完了判定 (a) と (c) は、実際に検査できる成果へ書き直す必要がある。
§6.1 は既存の表識別・G2・genesis 試験を再利用し、v3 lost update の合成例を足す方針を推奨する。
witness の変異 control は framing や txid 欠落による赤を排除して帰属させる。
凍結ファイルと v2 の期待 bytes は維持する。以上は静的検査であり、テスト実測は行っていない。