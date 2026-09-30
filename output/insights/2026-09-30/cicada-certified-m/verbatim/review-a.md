### A1 API 壊しの正例を起動器が不合格にする

**重大度:** must-fix
**根拠:** [API 壊し patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/broken-cicada-m-skip-read-register.patch:17) は登録を飛ばす。[M patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:419) は `API_EXTERNAL` を出し、同 patch の [終了照合](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:119) は不足した read-set 件数にも `API_EXTRA_REGISTER` を出す。一方、[起動器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:374) は期待 kind 以外の違反を全て拒否する。元の登録点は `external/ccbench/cc/cicada/transaction.cc:126`。
**失敗例:** 外部 read 1 件の登録を飛ばす → `API_EXTERNAL` と `API_EXTRA_REGISTER` が出る → 壊し API が `fail`。
**成果物への影響:** 発火した正例を偽の赤にし、SMOKE とそれに依存する変異確認が進まない。
**推奨対処:** 登録不足を `API_EXTRA_REGISTER` として報告しないよう照合を分けるか、この壊しに限って二つの違反を事前登録し、双方の帰属を検査する。

### A2 MV-B の kill 判定が到達診断を読めない

**重大度:** must-fix
**根拠:** [起動器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:369) は `CICADA_BREAK_FIRED` の `rts_raised > 0` を必須とする。[B 壊し patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/broken-cicada-m-early-reclaim.patch:12) の集計行にはその field がなく、`rts_raised` は [個別 EVENT](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/broken-cicada-m-early-reclaim.patch:34) にだけある。挿入先は `external/ccbench/cc/cicada/transaction.cc:934` の read-only 経路。
**失敗例:** RTS が上がり MV-B で B 違反が消える → `fired.get("rts_raised", "0")` は常に 0 → `survived`。
**成果物への影響:** MV-B の kill が構造上成立せず、B 照合の変異証拠を得られない。
**推奨対処:** 集計行に `rts_raised` を追加し、実際に上げた件数を出す。起動器は EVENT 件数との整合も確認する。

### A3 母集団の等式が独立した検査になっていない

**重大度:** must-fix
**根拠:** [M patch の `traceEnd`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:107) が `tx_end_reads_nonempty` と `b_end_checked_*` を同じ分岐で増やす。[`read()` 入口](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:350) も `read_calls` と `api_checked` を隣接して増やす。[起動器の等式](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:282) はそれらだけを比較する。元の別 clear 経路は `external/ccbench/cc/cicada/transaction.cc:971–975`。
**失敗例:** read set が終了照合前に別経路で clear される → B の対象読取が消えるが、比較する両カウンタは同じように減る → 等式は緑。
**成果物への影響:** 「照合済み＝母集団」という一次資料の主張に根拠がなく、照合漏れを偽の緑にできる。
**推奨対処:** begin 時点と読取登録時点で独立に対象数を記録し、commit・abort・clear の全経路で保存数と照合する。`reconnoiter_end` は対象外なら、呼ばれないことを実行時に検査する。

### A4 U 壊しは裁定で要求した設置集合との差を発火させない

**重大度:** should
**根拠:** [U 壊し patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/broken-cicada-m-drop-published-write.patch:19) は `cpv()` 後に write set だけから要素を外す。`trace_installed_` と `trace_published_` は残るため、[三者照合](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:123) では `U_MISSING_W` のみ発火する。元の公開 site は `external/ccbench/cc/cicada/transaction.cc:687–721`。[裁定](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/s4-ruling.md) は同じ版の `U_MISSING_W` と設置集合との差の違反を要求するが、[起動器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:29) は前者だけを期待する。
**失敗例:** 公開後に W 要素を除去 → 設置＝公開、公開≠W → 起動器は合格し得るが、裁定の二つ目の発火条件は満たさない。
**成果物への影響:** U の正例が仕様より狭い検査のまま緑になり、設置・公開照合を発火確認したという主張はできない。
**推奨対処:** この壊しの期待を公開対 W の検査に限定すると裁定で明記するか、設置対公開を別の一 site 壊しで発火確認する。

## 総括

**NO-GO。** 静的レビューのみで、build・patch 適用・実走は行っていない。
A1 は API 正例、A2 は MV-B kill を構造上妨げる。A3 は母集団の偽の緑を許す。
must-fix の三件を直し、計算ノードで stock・壊し・変異の実走を通せば、再レビューで GO を判断できる。
その際、A4 の U 証拠の範囲も裁定と揃える必要がある。