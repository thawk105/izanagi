### B1 1M・t48 を省く場合の結論が広すぎる

重大度: **must-fix**
根拠: [plan.md](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/plan.md:41)、[plan.md](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/plan.md:51)、[md_11 README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-best-config-verify/output/insights/2026-09-29/vhash-cicada-baseline-tuning/README.md:26)、[request-md_20.txt](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/request-md_20.txt:13)
放置時: 200 tuple・1 秒での陰性を、md_11 が選んだ **1M tuple・48 thread・3 秒**の比較相手の正しさ確認として読めてしまう。
推奨対処: 1M を予算上省く判断は許す。ただし結果表を実走した cell 単位に限定し、主比較条件は「未検査」と明記する。主比較への採用判断は別に残す。

### B2 実行時の workload と GC 値の束縛が計画から抜けている

重大度: **must-fix**
根拠: [plan.md](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/plan.md:25)、[plan.md](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/plan.md:102)、[起動器雛形](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/launch_cicada_run.base-md17.py:851)、[md_11 driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-best-config-verify/tools/vhash_cicada_tuning/driver.py:95)
放置時: JSON の argv と build の `-D` が正しくても、一次資料の `gc_inter_us`・tuple・rratio 等が実際の走行値だったと照合できない。雛形の `run_one()` には stdout の `#FLAGS_*` 照合がない。
推奨対処: `gc_inter_us` を各 cell の明示 argv に入れ、md_11 の `check_flags()` 相当で stdout を argv と照合する。JSON に照合結果と stdout の hash を残す。

### B3 inline 件数だけでは trace の正しさを確認できない

重大度: **must-fix**
根拠: [plan.md](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/plan.md:3)、[plan.md](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/plan.md:11)、[instr patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-best-config-verify/patches/instr-cicada-trace.patch:20)、[CCBench transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-best-config-verify/external/ccbench/cc/cicada/transaction.cc:102)
放置時: `R_INLINE>0` と `W_INLINE>0` でも、選択した版の wts と R 行の wts が一致した証拠にはならない。plan 自身が認める選択から登録までの窓が、一次資料の「trace 網羅確認」に残る。
推奨対処: 診断 patch の件数は到達確認として扱う。版値の一致を直接確かめる観測を実装できないなら、その範囲を未確認と明記する。この穴を埋めるために既存 instr patch の bytes を変更する案は、D2294 と並走 patch への影響を含む裁定候補にする。

### B4 正例は BEST100 の条件に届かない

重大度: **should**
根拠: [plan.md](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/plan.md:47)、[plan.md](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/plan.md:49)、[plan.md](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/plan.md:61)
放置時: W2・BEST の壊しが検出されても、W4・BEST100 (`REUSE_VERSION=0`、100 操作) の同条件で検出力が働いたとは言えない。
推奨対処: BEST100 の主張にも正例の裏付けを求めるなら同条件の壊しを追加し、発火・commit・巡回・帰属を確認する。予算で省くなら正例の射程を BEST の W2 cell に限る。

### B5 49 run と 2 node 時間の見積りがまだ成立していない

重大度: **should**
根拠: [plan.md](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/plan.md:43)、[plan.md](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/plan.md:51)、[plan.md](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/plan.md:53)、[md_3 README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-best-config-verify/output/insights/2026-09-29/vhash-cicada-verifier/README.md:162)、[md_17 README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-best-config-verify/output/insights/2026-09-29/vhash-cicada-verifier-ext/README.md:143)
放置時: J2 だけ投入前に見積もっても、J1 の verifier、W4 の長い trace、build、追加の切り分けで総 Elapse が 7,200 秒を越えうる。md_3/md_17 の job 時間は別 workload の複数 run と build を含み、49 run の単価にはならない。
推奨対処: L0 の実測から **残りの J1・J2・正例・予備**を合算して投入判断する。W4 は 200 tuple・48 thread の commit 数と trace 行数を先に見て、第二尺度や走行延長の必要性を決める。

### B6 追加実装を結果が出る前に抱え込みすぎている

重大度: **should**
根拠: [plan.md](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/plan.md:69)、[plan.md](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/plan.md:85)、[plan.md](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/plan.md:104)、[request-md_20.txt](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/request-md_20.txt:12)
放置時: TRACE=0 同一性二組、診断 patch、FOCUS mode と保存済み JSON からの自動展開が、必要な実走より先に起動器の変更量と検証量を増やす。TRACE=0 同一性は既存 patch の性能非干渉には有用だが、この wave の巡回判定条件ではない。
推奨対処: 最初は build 束縛・flag 照合・trace 判定・raw 保存・同条件の正例に絞る。巡回が出てから一軸切り分けを実装する。TRACE=0 再確認と inline 件数診断は、主判定の証拠として何を追加するかを定めてから採否を決める。

### B7 正例の帰属条件は壊し run 自身の整合性も要る

重大度: **should**
根拠: [plan.md](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/plan.md:61)、[md_3 README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-best-config-verify/output/insights/2026-09-29/vhash-cicada-verifier/README.md:96)、[md_3 README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-best-config-verify/output/insights/2026-09-29/vhash-cicada-verifier/README.md:100)
放置時: 巡回と rw 辺が見つかっても、壊し run に framing・orphan・commit 数の異常があれば、md_3 と同じ強さの「期待した経路で検出」とは言えない。
推奨対処: 正例にも integrity 数値項目 0、C 行＝commit 数、異常終了なしを明示的に要求し、事象ログは代表 witness が属する終盤まで打ち切らず保存する。

## 総括

現状の plan は**そのまま採用しない**。特に実行時 flags の照合を足し、inline trace の確認範囲を狭く正確に記す必要がある。1M・t48 を省くなら、md_11 の比較条件を検査済みとは扱えない。L0 後に全 job の node 秒を見積もり、2 node 時間未満の投入範囲を決めるのがよい。起動器は md_17 の雛形を使えるが、先行実装は判定に必要な部分へ絞れる。repo 外の診断 patch を使う場合も、既存 instr patch、forwarding・GC patch、gitlink には触れず、判定に効く変更が必要になった時点で所有範囲の裁定を求める。静的検査のみであり、patch 適用・build・実走の成立は確認していない。