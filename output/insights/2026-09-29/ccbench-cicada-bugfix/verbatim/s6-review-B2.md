## 所見

- **must-fix — 計装 patch の適用失敗。** [instr-cicada-trace.patch:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/patches/instr-cicada-trace.patch:52) の `transaction.hh` hunk `@@ -198,6 +212,11 @@` は、旧引数名 `later_ver` を文脈に含みます。G 側では無名引数になっているため、G への `git apply` でこの hunk は一致しません。放置すると R6 の計装小走行を開始できず、G の正しさ検証結果を記録できません。repo の patch は変えず、R6 の作業用コピーの文脈を G の引数表記に合わせてください。

- **nit — 計上コメントの範囲が広すぎます。** [transaction.cc:131](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/review/files/cc/cicada/transaction.cc:131) の「`read() already accounts`」は `read()` については [同:187](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/review/files/cc/cicada/transaction.cc:187) のとおりですが、`scan()` も `read_internal()` を直接呼びます（[同:448](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/review/files/cc/cicada/transaction.cc:448)）。放置すると G の ADD_ANALYSIS 計上の説明が scan 経路まで含むように読めます。「`read()` accounts for its own latency; no start timer exists here.」など、削除理由に限定してください。

## 判定 (NO-GO)

**R6 の計装 patch をそのまま使う検証計画には NO-GO** です。実装の R1〜R3 に不要な置換や欠落は見つかりませんでした。`later_ver` の無名化は重複追加の削除に伴う最小変更で、README の flag 説明も段 4 裁定では一致とされています。ただし README 本文は今回の射影資料に含まれず、独立には照合できません。

親の[構文検査](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/probe_syntax.log:8)は `transaction.cc` の既定・promotion・ADD_ANALYSIS・W5 の各文脈で rc=0 です。共通 header の変更箇所に、他 TU 固有の新たな構文エラーは静的には見当たりません。一方、24 genome の全 build、他 TU の compile、W5 の実待機まで通るとは、この 1 TU の結果からは断定できません。

## 総括

6 行の修正自体は段 4 裁定に沿っています。物理行数が同じでも、patch の**文脈文字列**は変わるため、「offset 0 なら適用できる」という予測には上記 `transaction.hh` hunk が反例です。[trace patch の `transaction.cc` `@@ -907`・`@@ -932`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/patches/instr-cicada-trace.patch:107) と [version-lifetime patch の commit 冒頭](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/patches/instr-cicada-version-lifetime.patch:828) の文脈には、変更された 924–925 行は含まれません。これらの hunk について、この 6 行を原因とする適用失敗は見当たりません。