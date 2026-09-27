### 所見 1 — 既存 buildcache テストの fixture 置換が停止する

**主張:** `test_qualification_stock_build_case_dependency_options` は全 7 パラメータで、検査対象へ進む前に `ValueError` になる見込みです。  
**根拠:** [test_buildcache_v2.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_buildcache_v2.py:5699) は `void TxExecutor::abort() {\n` を検索しますが、同テストの checkout を作る [test_s1_direct_comparison.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_s1_direct_comparison.py:429) の原文は `class Transaction` 内の `void abort()` です。さらに検索箇所だけ直しても、後続の `raw[end:]` は旧 fixture の関数末尾を残すため、置換後の C++ の構造を確認する必要があります。  
**影響:** 既存テストが失敗し、正当な build の受理回帰を検証できません。  
**推奨:** **must-fix。** checkout 全体を、宣言・関数末尾まで整合する canonical な合成 source に更新してください。

### 所見 2 — 受理境界は限定主張どおりで、関数前の前処理は残る

**主張:** 提示された R4 二形・R5・R7 と abort() 内の移設形は、新照合で拒否されます。一方、宣言行より前の `#if` やマクロ、行継続で凍結 bytes の解釈を変える形は引き続き受理され得ます。これは同じ関数内の挿入経路ではなく、裁定済みの**別経路**です。  
**根拠:** [build_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/build_admission.py:216) の `endswith` は凍結 prefix 内の変更を拒否しますが、その前の bytes は比較しません。[test_build_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_build_admission.py:789) も宣言前の変更を正例にしています。CRLF が凍結領域内に入れば byte 不一致、BOM・`#line` が領域前にあれば受理、BEGIN が関数外に見える形や宣言の重複は byte 照合だけでは C++ の意味を判定しません。  
**影響:** 前処理などを介した source では、受理された mask と実際の gate 動作が食い違う余地が残ります。  
**推奨:** **scope 外。** 現行 docstring の限定を維持し、今回の R4/R5/R7 閉鎖の証拠に含めないでください。

## 総括

**NO-GO** — 既存 buildcache テストの fixture 回帰を修正する必要があります。  
凍結 head・tally・prologue は、提示された pin 原文、patch の 24 行・7 行、骨格適用後 source と静的に整合します。  
独立照合 3 本は定数とは別の出所を読み、pin object 欠落は skip せず失敗する構成です。  
骨格のみ、骨格＋tally、tally＋misattr の受理形に、静的検査で byte 不一致は見つかりませんでした。  
M1～M3・M5～M7 は狙ったテストで殺される見込みですが、baseline の赤を直してから node 集合を実測すべきです。  
M4 は `endswith(b"\n" + prefix)` への強化、M5 は宣言直後から `// remove inserted records` 前までを任意 bytes とする照合への弱化で具体化できます。