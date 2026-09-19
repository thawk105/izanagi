単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-tail-cohort2

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/78abb492/tmp/wave/stage1-brief.md — 親の段 1 brief (攻撃対象に含む)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/78abb492/tmp/wave/prereg-append.diff — 親が事前登録へ加えた追記の diff (42 行追加・削除 0)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-tail-cohort2/docs/b10-backoff-static-tail-preregistration.md — 追記込みの事前登録全文。§0、§1、§4.5、§4.9、§7、§8、末尾の「2026-09-10 追補」と「2026-09-19 追記」を読む。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/78abb492/tmp/wave/D2050-verbatim.md — 2 本目 cohort の地位を先に決めるよう求めた裁定 D2050 の逐語。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-tail-cohort2/output/insights/2026-09-16/b10-tail-formal-submit/README.md — cohort 1 の再導出と、2 本目を投入しなかった理由・レンズ A の 4 条件 (§5〜§7)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-tail-cohort2/docs/b10-backoff-static-tail-submission.md — 投入手順書。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-tail-cohort2/orchestrator/campaign/b10_backoff_static_tail_formal.py — `load_preregistration` (作業ツリー bytes == 束縛 commit の blob を要求) と spec の parse。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-tail-cohort2/orchestrator/tests/test_b10_backoff_grid_submit.py と /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-tail-cohort2/orchestrator/tests/test_b10_backoff_static_tail_formal.py — 事前登録文書の本文・hash を pin する test。読めなければ即停止。

## 役割

あなたは read-only の敵対相談子である。書込可能な tmp は無いので pytest の実走は要求しない。静的検査でよい。
テストの実測は親が行う。予算が尽きそうなら、途中までの結論を下の出力形式どおりに書いて終われ (無出力が最悪)。

## 状況

ユーザー決定 (2026-09-19、逐語): 「第 2 cohort は独立再現とする。cohort 1 (group b10-backoff-grid-20260915T061814Z-545445、verdict not-observed-in-any-workload) の verdict を主として保持し、cohort 2 の verdict は再現欄に併記する。合成はしない」。この地位の明記を結果を見る前に事前登録の追記 (commit cad6f46d8 の bytes は不変、日付付き append-only 追記) として commit してから投入する。

親はこの決定を事前登録への追記 (diff 参照) として書いた。**この追記は commit 後に cohort 2 の束縛 commit になり、結果が出た後は事前登録として訂正できない。** だから commit 前にあなたに攻撃させる。

## 攻撃レンズ (この 1 本で全部やる)

1. **後付け選択の抜け穴 (絶対規律 3)。** 追記の文言に、結果を見た後で「どちらの verdict を採るか」「報告するか」「どう言うか」を選べる余地が残っていないか。文の曖昧さ・未定義語 (「再現欄」「主として保持」「合成」) が抜け穴にならないか。
2. **既存本文との矛盾。** 追記が §0・§1・§4.5・§4.9・§7・§8.2・2026-09-10 追補のどれかと矛盾・二重定義していないか。「§4〜§9 の 1 行も変えない」と書きながら実質的に規則を変えていないか。
3. **束縛の論理。** driver は作業ツリー bytes == `--preregistration-commit` の blob を要求する。追記 commit を束縛 commit にする親の計画は正しいか。cohort 2 が cohort 1 と別の blob に束縛されることを、事前登録の §7-12・§4.9 (3 job の同一性: 本書の commit・blob・spec) は許すか。追記が「本書自身の hash を書かない」規則 (§0) を守っているか。
4. **ユーザーの「append-only」との整合。** 親は末尾追記に加えて §0 の箇条書きへ 1 項目を挿入した (brief の P1-a)。これはユーザー決定の「日付付き append-only 追記」に反するか。反するなら、§0 の更新契約 (変更理由と時点を本節へ明記) との両立案を出せ。
5. **test・consumer への影響。** `test_b10_backoff_grid_submit.py` は本文を `"### 8.2 "` と `"## 9."` で split する。`test_b10_backoff_static_tail_formal.py` は HEAD blob と作業ツリーの一致と spec SHA を pin する。追記が (commit 後に) これらを壊すか。他に本文を読む consumer を思いつくなら挙げよ (実在確認は親が行う。推測は推測と書け)。
6. **過剰・削除。** 追記の 7 項目のうち、ユーザー決定に無い事を親が足していないか (例: 項 4 の「3 本目」、項 6 の「探索走 campaign」)。足しているなら、それが必要か・削るべきか・ユーザー裁定に返すべきかを分けて言え。
7. **brief の実測値とその一般化。** brief の「実測した前提」と (P1-a)〜(P1-d) を疑え。特に P1-c の集団報告出力先、P1-d の「file 名の slug は後付け判断にならない」という主張。

## 出力形式 (この順・この見出しで)

### 所見
番号付き。各所見に「real 候補 / refuted 候補」の自己判定、根拠 (file と節名または行)、放置時に成果物 (cohort 2 の稿・fig8 再現欄・事前登録の効力) がどう変わるかを 1 行。

### 追記の修正案
所見が real なら、追記の該当行に対する具体的な置換文 (diff 形式でなくてよい。前後がわかる引用で)。修正が要らなければ「修正不要」と書く。

### 親 brief への所見
(P1-a)〜(P1-d) それぞれに対して 採る / 採らない / 条件付き と理由 1 行。

## 総括
3〜6 行。commit してよいか (yes / yes-with-fixes / no) を最初の行に書く。
