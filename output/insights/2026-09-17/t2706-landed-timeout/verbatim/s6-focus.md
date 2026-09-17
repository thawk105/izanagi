## 所見対応表

判定は提示資料の範囲に限定する。`partial` は未対応または完了証拠不足を含む。

| id | 判定 | 根拠 file:line |
|---|---|---|
| RA1 | partial | [s4-adjudication.md:68][s4m6] に M6 登録と「M5 と同時」の説明が残る。`value-decision.md:1–34` に除外記録なし。 |
| RA2 | closed | [s6-after-fix.diff:44][assert]・`:110`・`:118` に実例外の timeout 値の検証を追加。ただし残余取得の時点差による偽赤可能性は下記 F1。 |
| RA3 | partial | [s4-adjudication.md:47][s4inv] に逆向きの影響と実測義務は記載済み。`value-decision.md:24` は推計のみで、採用値での observations／ref_snapshot timeout 件数はない。 |
| RB1 | closed | [s6-after-fix.diff:145][product] のコメント・45 秒は [value-decision.md:12][value]・`:20`・`:22`・`:32` と一致。176,575 objects は同文書 `:6` に記録済み。 |
| RB2 | partial | RA1 と同じ。[s4-adjudication.md:68][s4m6] の登録除外が未反映。 |
| RB3 | closed | [s4-adjudication.md:22][s4carry]・`:23`・`:24` に B6〜B8、`:13` に OSError の carry、`:44` に DEFAULT_TIMEOUT_SECONDS 等の scope 外を明記。指定どおり段 4 文書で判定。 |
| RB4 | partial | [s6-fix.md:3][fix]・`:9` は未実走を明示しており、全走 PASS の誤認はない。ただし受入全走の時間評価は未確定。 |

## 派生値の再計算

親の script を呼ばず、JSONL 全行と反復点検の `records` から独立集計した。30 run／2,935 command、打切り・error は 0。JSONL の SHA-256 は親の記載と一致する。

| 項目 | 親の値 | 再計算値 | 一致 |
|---|---|---|---|
| (a) 全 command 最大 | 26.87 秒、find-object | **26.870123 秒**、`log --find-object`、OID `f181f703d1d6…` | 一致 |
| (b) path log | n=349／中央値3.84／p95 9.11／最大21.29 | **349／3.836461／9.105933／21.291024**。p95 は昇順332番目 | 一致 |
| (c) cherry 最大 | 13.66 | **13.658294** | 一致 |
| (d) cap 超過本数 | 5→136、10→25、15→11、20→3、30→0 | **136／25／11／3／0** | 一致 |
| (e) 完走／確定 | 予算60→16／4、予算300→30／6 | cap **30・45・60** の各々で **16／4、30／6** | 一致 |
| (f) verdict | landed 2／not-landed 4／indeterminate 24、refs-moved 1 | **2／4／24、うち refs-moved 1** | 一致※ |
| (g) 反復点検 | path log n=69・最大35.94、find-object 20.76、cherry 6.87 | **69・35.939／20.756／6.865** | 一致 |
| (h) 選択規則 | 最大×1.5=40.3→45、35.94≤45 | **40.3051845→45、35.939≤45** | 一致 |

※ (f) は依頼中の値と一致するが、`value-decision.md` 自体には内訳の記載がない。(e) は指定された cherry 続行規則と最後の overhead 加算を適用した推計であり、採用値による再実測ではない。

コメントの **26.9／21.3／35.9／45** は原データと一致する。**11,246／24–92** は `value-decision.md:6` と一致するが、指定原データには commit 総数と本走の load 記録がなく、独立検証できない。反復 JSON の load は約27.46／35.30／39.88で、別の観測である。

製品側は [s6-after-fix.diff:140][producthunk] の **1 ハンク、定数1行置換＋コメント2行追加**だけ。テスト側は2ハンク・114行追加・削除0で、import とテスト追加に限定される。

## 残る所見

- **RA1／RB2 — nit**：M6 登録を除外し、到達不能の理由を記録する必要がある。現状では変異検出能力の表が過大表示になる。
- **RA3 — must-fix（成果物の最終確定時）**：採用値での observations／ref_snapshot timeout 件数を親の実測報告に記録する必要がある。300秒の無中断走では両 phase が30件とも matched だが、60秒予算での逆向きの影響は評価できない。
- **RB4 — nit／親の受入走待ち**：全体所要時間・5分以内という評価は、焦点走や fix 報告では確定できない。
- **F1 — nit**：追加 assert は通常の `min(0.05, remaining)` と整合するが、偽赤は排除できない。wrapper の `remaining()>1` と [Git.run の再取得 :215][remaining] の間で停止され、再取得値が例えば **0.04** になれば、正しい実装でも `TimeoutExpired.timeout==0.04` となり assert が失敗する。0以下なら cause のない例外となり、`.timeout` 取得も失敗する。テスト内で残余取得を制御すれば決定的に検証できる。
- **F2 — nit**：`value-decision.md:25` の未完走14件の分類は集計出力と不一致。指定模擬の最初の中断操作は **path log 12件／find-object 1件／rev-parse 1件**であり、「path log 合計が60秒超の13件」とは説明できない。
- **F3 — nit**：`value-decision.md:4` の入力名は `timing-lifted-2.json.jsonl` と誤記。実ファイルは `timing-lifted-2.jsonl`。ハッシュは一致している。

## GO / NO-GO

**NO-GO（全所見を閉じた最終成果物として）** — 45秒の根拠と製品差分は妥当だが、M6 登録整理と RA3 の必須実測記録が残る。

## 総括

(a)〜(h) の再計算値は、表示精度で一致した。
製品変更は定数1行とコメント2行に限定される。
RB1・RA2 の修正は確認できた。
親の記録・受入走と、残余取得の時点差によるテストの不安定性は残る。
ファイル変更・pytest 実走は行っていない。

[s4m6]: /home/SFC/tanab/.claude/jobs/10430006/tmp/dev-wave-t2706/s4-adjudication.md:68
[assert]: /home/SFC/tanab/.claude/jobs/10430006/tmp/dev-wave-t2706/s6-after-fix.diff:44
[s4inv]: /home/SFC/tanab/.claude/jobs/10430006/tmp/dev-wave-t2706/s4-adjudication.md:47
[product]: /home/SFC/tanab/.claude/jobs/10430006/tmp/dev-wave-t2706/s6-after-fix.diff:145
[value]: /home/SFC/tanab/.claude/jobs/10430006/tmp/dev-wave-t2706/value-decision.md:12
[s4carry]: /home/SFC/tanab/.claude/jobs/10430006/tmp/dev-wave-t2706/s4-adjudication.md:22
[fix]: /home/SFC/tanab/.claude/jobs/10430006/tmp/dev-wave-t2706/s6-fix.md:3
[producthunk]: /home/SFC/tanab/.claude/jobs/10430006/tmp/dev-wave-t2706/s6-after-fix.diff:140
[remaining]: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2706-landed-timeout/tools/check_branch_landed.py:215