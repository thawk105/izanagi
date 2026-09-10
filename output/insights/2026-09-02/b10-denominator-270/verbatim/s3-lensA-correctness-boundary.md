## 所見

1. [plan-out.md:18](/home/SFC/tanab/.claude/jobs/48609c35/tmp/wave-t2201-b10-denominator/artifacts/plan-out.md:18)、[missing-scope README:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-missing-iterations-scope/README.md:67) — 270 と 294 は説明する一方、一次資料にある 360 / 287 / 73 を落としている。270 は 3 workload の論理格子、294 は開始済み 49 attempt、360 は先行 write-heavy を含む 4 campaign の履歴である。270 と 360 の差分がともに 73 なのは、360 側へ完了済み write-heavy 90 枠が分母・分子とも追加されるためで、同じ母集団だからではない。  
   放置時の成果物影響: 正式レポートの値は 270 / 197 / 73 だけになり、追加で実行・完了した 90 verify と 4 campaign の参照履歴が見えなくなる。  
   直し方: 270 を既定の完全性分母としつつ、270 / 197 / 73、294 / 287 / 7、360 / 287 / 73 の三行を条件付きで併記する。

2. [plan-out.md:57](/home/SFC/tanab/.claude/jobs/48609c35/tmp/wave-t2201-b10-denominator/artifacts/plan-out.md:57)、[b10-multinode-formal-run-design.md:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/b10-multinode-formal-run-design.md:297) — 「登録格子」は分母を一意にするが、どの campaign を完了記録の根拠に採るかまでは決めない。計画は `e3de15eb` 採用を固定しているが、設計文書自身は同成果を残すか取り直すか、また protocol hash の置き方によって集約から外れるかを未裁定としている。  
   放置時の成果物影響: 未裁定の `e3de15eb` を集約対象として先取りし、将来のレポートの受理集合と provenance 参照を固定しうる。  
   直し方: 登録枠を `(workload, variant, verify tag, repetition)` の論理キーとして定義し、完了判定・重複 campaign の射影規則は別の裁定済み集約契約に従う、とする。197 は「現行履歴を論理枠へ射影した参考値」と明記し、将来様式へ campaign ID を固定しない。

3. [plan-out.md:89](/home/SFC/tanab/.claude/jobs/48609c35/tmp/wave-t2201-b10-denominator/artifacts/plan-out.md:89)、[trace-truncation README:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:194)、[missing-scope README:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-missing-iterations-scope/README.md:191) — 派生記述を網羅するという計画なのに、「read-heavy の検査対象は write-heavy の約 7 倍」が一覧から落ちている。これは 1690 万 commit そのものとは別の、workload 間比率の主張である。3 飽和点のうち `constant-mu2` は n=3 の未完了 attempt 由来で、15 点格子全体の比でもない。  
   放置時の成果物影響: 派生記述台帳の参照集合が不完全なままになり、この比率だけ母集団条件を追跡できない。certified 選択値自体は変わらない。  
   直し方: 第 5 の派生記述として独立行にする。T-2191 の二語句を一件に束ねること自体は維持してよい。

4. [plan-out.md:92](/home/SFC/tanab/.claude/jobs/48609c35/tmp/wave-t2201-b10-denominator/artifacts/plan-out.md:92)、[decisions.md:46503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/decisions.md:46503)、[trace-truncation README:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:196) — 計画は D1489 の 23 分をそのまま「max」として通しているが、同じ一次資料の観測上端 1465.6 秒は 24.43 分である。10 回なら 3.83 時間ではなく約 4.07 時間、12 時間の倍率は約 3.1 倍ではなく約 2.95 倍になる。  
   放置時の成果物影響: A-6 の walltime 12:00:00 と受理集合は直ちには変わらないが、その根拠レポートの 3.83 時間と安全倍率が誤ったまま参照される。  
   直し方: 本 wave で D1489 を書き換えず、一覧に「D1489 は 23 分を max と再利用したが、保存値の上端は 24.43 分」と記録し、決定文の訂正は別の追記裁定へ送る。

5. [plan-out.md:13](/home/SFC/tanab/.claude/jobs/48609c35/tmp/wave-t2201-b10-denominator/artifacts/plan-out.md:13)、[parent-independent-findings.md:51](/home/SFC/tanab/.claude/jobs/48609c35/tmp/wave-t2201-b10-denominator/parent-independent-findings.md:51) — EOF の H3 は凍結契約内であり parser も壊さないが、450 行の「次の一手」の後なので、1189 の一般読者へ訂正を届けるという目的には弱い。親自身が後から示した H2 直後の blockquote の方が適切である。  
   放置時の成果物影響: archive を入口から読む利用者が旧 294 / 287 / 7 を引用し続け、レポートや台帳の参照値が訂正へ追随しない可能性が残る。  
   直し方: H2 の直後へ見出しを増やさない blockquote の訂正注記を挿入する。既存 bytes は削除・置換しない。EOF 前提の prefix `cmp` は、追加部分だけを除いた旧 bytes との比較へ変更する。

## 親 provisional への評価

(P1-a) **EOF 案には不同意、archive 本体への訂正注記には同意。** 親の後発案どおり H2 直後の blockquote を推す。EOF の H3 も機械的には安全である。[tools/check_docs.py:1019](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/tools/check_docs.py:1019) の full-match は H2 だけを対象とし、[tools/check_docs.py:1023](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/tools/check_docs.py:1023) は次の H3 で「次の一手」を閉じるため、一意性は保たれる。新しい H2 を作れば `_extract_archive_entries` の [line 1395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/tools/check_docs.py:1395) で title full-match に落ち、二つ目の「次の一手」を作れば `_extract_next_action` の [line 1422](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/tools/check_docs.py:1422) で件数 2 として落ちる。提案した blockquote はどちらにも触れない。

(P1-b) **宿り先には同意、提案文面には不同意。** §6 (4) 直後は 135 performance cell と 270 verify 枠を区別できる適切な場所である。ただし未来の報告様式は分母規約だけを固定し、`e3de15eb` の採否や 197 という歴史値を受理規則として固定してはならない。

(P1-c) **網羅性には不同意。** 70.0-87.0 マイクロ秒/commit と 15 認証単位を T-2191 の一件に束ねる判断は妥当である。しかし「約 7 倍」が独立の比率主張として実在するため、完全な意味上の一覧は少なくとも 5 件である。D1489 は「23 分」項の追加出現・判断利用として同じ行に束ねてよい。

## 親の純増 2 件の裏取り

**D1489 の「23 分」: real。** [decisions.md:46501](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/decisions.md:46501) が同じ 23 分を明記し、[decisions.md:46503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/decisions.md:46503) で full-scale 10 回を 3.83 時間へ積み、12:00:00 の根拠に使っている。ただし「max 23 分」は保存された上端 24.43 分と整合しないため、親の発見は実在するが元の一般化は正しくない。

**「約 7 倍」: real。** [missing-scope README:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-missing-iterations-scope/README.md:197) から 3 飽和点の比は 6.83-7.22 倍で、そのうち `constant-mu2` は未完了 attempt の観測 3/5 反復である。ただし欠測値を補完した比ではなく、「観測標本の一部が未完了 attempt に属する」という意味で real であり、15 点格子全体への一般化はできない。

## 総括

270 を既定分母にする裁定自体は、3 workload × 15 変種 × 6 verify の一次資料と整合する。  
ただし 294・360 の条件と 4 campaign 履歴を併記しない計画は、分母の意味と provenance を隠す。  
§5.1 案は 287 反復へ射程を限定し、D295 の非検出限界も残しており、正しさ主張や 45 cell を広げてはいない。  
archive 変更は訂正注記だけで、過去値や当時の certified 判定を遡及変更しない形にできる。  
`docs/paper-story/`、新規 gate・検査・台帳、但し書き本文への scope 漏れは計画上見当たらない。  
静的検査のみであり、pytest や `check_docs.py` の緑は報告しない。