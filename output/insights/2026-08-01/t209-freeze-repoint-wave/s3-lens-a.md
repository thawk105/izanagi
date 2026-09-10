# 判定: NO-GO

静的確認のみ実施した。編集・pytest・実行検査は行っていない。

## 所見

### 1. BLOCKER — P1 は T-193 の完了条件を無断で緩めている

(74) #1 は「取り込んだうえで削除する」と明記している（[裁定原文](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t209-freeze-repoint/docs/archive/worklog-phase3-0731-74.md:9)）。その後の正本も、branch の 50 path は廃棄する一方、`Group Name` exact 束縛は「移植する」と明記する（[T-193 決着正本](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t209-freeze-repoint/output/insights/2026-07-30_dev-wave-improve-wave/s9-t193-ruling.md:55)）。

M4 の限定命題「main に三ファイルがない」は真だが、「削除面は no-op」は偽である。削除対象は branch 側実装であり、現時点でも `codex/dev-wave-improve@77db32c` に三ファイルが tracked で残る。さらに main の `_accounting_present` は現在も Request ID・Started・Ended・Elapse しか検査しない（[dispatch_compute.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t209-freeze-repoint/tools/pegasus/dispatch_compute.py:731)）。

M5 の「T-222 へ分離済み」も状態記述にすぎない。[T-222] は (80) で AI が起票した「P1・新規」であり、責務分離をユーザーが裁定した記録ではない（[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t209-freeze-repoint/docs/worklog.md:700)）。同じ (80) は T-221 だけを完了とし、T-193 は「変わらず」とした（[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t209-freeze-repoint/docs/worklog.md:696)）。

厳密解釈では T-222 完了まで閉鎖不能となり、freeze が再発効しない。だが、その実害は閉鎖条件を親が勝手に緩める根拠にはならない。「(80) が移植要件を supersede し、T-222 を独立残務とする」とユーザーが再裁定するか、T-222 を実装してから閉じる必要がある。

成果物影響: T-193/T-209 を terminal にするか、freeze を発効させるかが変わり、同時に `Group Name` 無束縛の accounting evidence を受理する集合と台帳参照が残る。

### 2. HIGH — M1〜M6 の一般化は混在しており、M3〜M6 を閉鎖根拠に使えない

- M1 は支持できる。phase3 の付替えは commit `27b2813` で既着地している（[phase3.md](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t209-freeze-repoint/docs/phase3.md:134)）。
- M2 は「live な規範箇所は phase3 の一段落だけ」と限定すれば支持できる。「repo 内の記述が一箇所」は archive に同条件が複数残るため過大表現。ただし archive は凍結済みなので書換え対象ではない。
- M3 は「正本選択が決着」まで真で、「T-193 閉鎖」までは導けない。(80)〜(83) の全てで T-193 は「変わらず」である（現行末尾は [worklog (83)](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t209-freeze-repoint/docs/worklog.md:1374)）。
- M4 は main 上の不在という事実だけ真で、裁定履行の no-op 化は偽。
- M5 はタスク起票の事実だけ真で、ユーザー承認済み責務分離という一般化は偽。
- M6 は親自身が反証済みであり、現在の landed 最大値は T-234。さらに稼働中の T-207 worktree は T-235〜T-239 を使用し（[別 worktree の worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/docs/worklog.md:1360)）、network-split brief も T-235 を使用している（[brief](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-network-split/output/insights/2026-08-01_network-split-wave/s1-brief.md:1)）。

D70 上、未 land の番号は予約ではない。したがって現在の T-235/T-236 は候補ですらなく単なる placeholder と扱い、latest main 取込み後の統合直前に全出現を再採番しなければならない。「全 worktree の docs」走査では `output/insights` の in-flight brief も捕捉できない。

成果物影響: 衝突した ID を確定すると phase と worklog が別タスクを指し、`check_docs.py` が未検出の内容再利用によって台帳の受理集合・参照が破損する。

### 3. HIGH — P2 は「(80) で閉鎖」と「閉鎖が見えなかった」を都合よく併用している

phase3 は発火条件を「T-193 の閉鎖」とし、対象 ID と進捗の正本を worklog 末尾に置く（[phase3.md](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t209-freeze-repoint/docs/phase3.md:134)）。その worklog が (80) 以後も T-193 を open のまま運んだ以上、状態機械としての閉鎖は (80) に起きていない。

従って整合する択は二つだけである。

- 今回の terminal エントリを閉鎖・発効境界にする。この場合、(81)〜(83) は発効前であり遡及違反ではない。
- (80) で意味上閉鎖したとする。この場合、(81)〜(83) は既存規則の発効後であり、「可視化されなかった」だけでは非違反にならない。受容するなら一回限りの明示的なユーザー免責が要る。

段 2 プランが選んだ「今回の閉鎖エントリから発効」は整合的だが、親 brief の P2 は refuted と明記して捨てる必要がある。

成果物影響: (81)〜(83) を受理済み wave と数えるか違反・免責対象と数えるか、および次 wave で許される作業種別が変わる。

### 4. HIGH — P4 の「本 wave は対象外」に原文上の根拠がない

2026-07-22 改訂はプロセス系を freeze し、2026-07-26 改訂は解除対象を「本番コードに触らないプロセス系」と定義している（[phase3.md](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t209-freeze-repoint/docs/phase3.md:84)）。本 wave は docs-only の freeze 管理・台帳・routing であり、この分類に正面から該当する。「メタ作業」は列挙された例外ではない。

今回の terminal 記録を発効点にすれば、本 wave は発効前なので例外自体が不要になる。逆に (80) 発効を維持するなら P4 は未裁定の自己免除であり採用不可。

成果物影響: 本 wave を受理集合へ入れられるか、閉鎖直後に要求された研究 wave より前へプロセス wave を一件追加できるかが変わる。

### 5. BLOCKER — P3 は既存研究タスクと既知の陰性結果を再起票している

「データ構造水準の変異軸」は既に [T-140] が所有し、実 set-size 分布から「地形は存在しない」と実測して択 (c) を発火、軸を廃止している（[T-140 一次資料](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t209-freeze-repoint/output/insights/2026-07-28_t140-setsize-distribution.md:71)）。再評価条件は `max_ope` の大きい workload 採用時だけであり、今回その条件は示されていない。

「既知解までの距離」は [T-139] の劣化版 Silo 梯子として rung 1・certified evidence まで完了済み（[archive](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t209-freeze-repoint/docs/archive/worklog-phase3-0729-59-0730-67.md:164)）。Shirakami-LTX との中間は既存 [T-144] が所有する（[archive](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t209-freeze-repoint/docs/archive/worklog-phase3-0728-33-37.md:102)）。

従って「新規二件」は、二件で足りるか以前に原子の同定が誤っている。[T-140] は発火条件なしに再開せず、次 wave は既存 [T-144] の優先度変更、または [T-139] 成果物から未完部分だけを切り出した具体的な継続原子として再設計すべきである。

成果物影響: terminal な陰性結果を新規研究として再実行し、完了済み rung を二重計上して、材料レポートの新規性・試行台帳・次 wave の受理集合を誤らせる。

### 6. HIGH — phase3 追記草案は現状では「状態追記」ではなく未裁定の意味変更である

草案の「T-222 が独立所有し、T-193 の残件ではない」は P1 の未裁定解釈そのもの（[段 2 プラン](/home/SFC/tanab/.claude/jobs/eff60885/tmp/t209-jobs/s2-plan/output.md:50)）。また発効境界・遡及非違反も P2 の裁定である。これらを既成事実として phase に書くと、2026-07-31 改訂の「T-193 閉鎖」の意味を後から狭める。

一方、ユーザー再裁定後に「(80) は正本選択のみ、今回の entry が terminal 閉鎖」「以後 freeze」「次 wave は研究」と追記するなら、2026-07-26/31 改訂とは整合し、roadmap 本体・絶対規律にも直接触れない。恒久一般則にせず一回限りの裁定として書く限り、新 D は不要である。

成果物影響: 未裁定草案を入れると phase 正本が T-193 の完了条件と freeze 発効条件を改変し、将来 manager の着手許可集合と台帳参照が変わる。

### 7. MEDIUM — worklog は追記だけで整合可能だが、現プランの座標と容量判断は失効している

過去エントリは凍結されている（[worklog 規約](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t209-freeze-repoint/docs/worklog.md:12)）。従って (80) を書き換えず、新エントリで「(80) は main 選択の決着、terminal 閉鎖は本エントリ」と区別すれば headline と「変わらず」を整合できる。ただし P1 の再裁定前に T-193/T-209 を閉鎖・完了とは書けない。

静的確認時点の HEAD/main は `4a4e7ed`、worklog は 93,960 bytes である。段 2 プランの約 6,843-byte エントリを足せば 100,000-byte 上限を超えるため、「通常はローテーション不要」は既に失効し、プラン自身の `(77)` ローテーション分岐が必須になる。

成果物影響: 古い座標・非ローテーション案のまま進めると docs 検査が赤になり、entry 番号・archive 索引・T 番号参照を含む記録成果物を受理できない。

## 総括

**NO-GO。**
最重要 BLOCKER は、未実装の `Group Name` 移植を AI 起票の T-222 へ移しただけで T-193 を閉鎖しようとしている点。
発効境界は今回の terminal 記録に置くか、(80) 発効 + 明示免責のどちらかに統一し、P4 の自己免除は捨てること。
研究 routing は既存 T-139/T-140/T-144 と陰性結果を再裁定し、最終 ID は land 直前まで固定しないこと。