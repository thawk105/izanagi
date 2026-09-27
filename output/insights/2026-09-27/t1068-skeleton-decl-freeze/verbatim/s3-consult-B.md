### 所見 1 — 案 A では移設した R5・R7 を受理する

**主張:** 本題には案 B が必要です。案 A は提示された位置への挿入を拒否しても、`return;` や局所 shadowing を prologue の直前へ 1 行移すと通します。  
**根拠:** [brief:43–46](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/s1-brief.md:43)、[plan:3–10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/out/s2-plan.md:3)、[骨格適用後の abort()](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/evidence/transaction.cc.skeleton-applied:61)。R4 の reason reset も同様に移せます。  
**影響:** 案 A では mask M と実バイナリの挙動が食い違う source が受理集合に残ります。  
**推奨:** **must-fix** — 案 B の `abort()` 宣言から BEGIN 行頭直前までの隣接一致を採用する。

### 所見 2 — 独立整合テストを fixture の生成源にしない

**主張:** plan の patch・CCBench 原文との独立照合は必要ですが、正例を追加定数からだけ組み立てると、定数と入力が同時に誤る場合を見逃します。既存の block／epilogue テストもこの構造です。  
**根拠:** [plan:24–29](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/out/s2-plan.md:24)、[test_build_admission.py:222–236](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_build_admission.py:222)、[T-1048 の変異結果](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/verbatim/t1048-README.md:134)。独立照合そのものは brief P3 の明示要件です。  
**影響:** 照合テストを欠くと、誤った凍結 bytes を正例も admission も共有し、受理集合のずれが緑になります。  
**推奨:** **must-fix** — patch 由来の prologue／tally と pin 原文由来の head を一つの焦点テストで独立照合する。汎用 patch parser や実行時 file 読み込みは追加しない。

### 所見 3 — tally は必要な第二形だが、misattr 専用形は不要

**主張:** 案 B の受理形は「骨格」と「開き括弧直後に tally」の二つで足ります。misattr は `abort()` 外の `lockWriteSet` を変えるため、第三の prefix 定数や専用分岐は要りません。  
**根拠:** [tally patch:8–33](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/patches/instr-silo-backoff-trigger-gating-tally.patch:8)、[misattr patch:5–23](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/patches/broken-silo-trigger-misattr.patch:5)、[coverage producer:353–367](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/s8a_trigger_coverage.py:353)、[freq producer:155–164](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/s8a_trigger_freq.py:155)。brief は他の producer を骨格＋hole 置換と記録しています（[brief:35–38](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/s1-brief.md:35)）。  
**影響:** tally 形を落とすと現行 S8a の正当な build を拒否し、任意の tally 位置を許すと R5・R7 の受理穴が戻ります。  
**推奨:** **must-fix** — 二形を exact に照合する。misattr 正例は同じ tally prefix を使い、関数外の差分を凍結しないことだけ確認する。

### 所見 4 — compile する合成 fixture の更新は必要だが、stub の一般化は過剰

**主張:** `test_reflux_campaign_issuer.py` は現状 `static void exercise_trigger_gate()` と bool 1 行なので案 B では拒否されます。実 compile する fixture には canonical head を成立させる stub が必要です。一方、再利用可能な偽 CCBench 層まで作る根拠はありません。  
**根拠:** [plan:43–45](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/out/s2-plan.md:43)、[現 fixture:169–199](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_reflux_campaign_issuer.py:169)、[別 fixture の BEGIN 置換](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_buildcache_v2.py:5688)。  
**影響:** fixture を旧形のままにすると、従来の受理期待が prefix 不一致で赤になり、別の拒否理由を検査するテストの意味も変わります。  
**推奨:** **should** — 四箇所の fixture を局所的に canonical 化し、既存の受理・拒否期待を一件も変更しない。compile fixture の stub はその関数が要する最小限に留める。

### 所見 5 — pin 再発行と duration ledger 更新は今回の差分に不要

**主張:** `axis_trigger_gating.py` は凍結 JSON に間接 pin されていますが、記録 SHA は着手前から不一致で、historical 経路に明示的な例外があります。両実装 file は contract-loader 閉包に属し、未 commit 変異の drift は別層の失敗です。`acceptance_duration_ledger.json` は nodeid の所要時間表であり、実装 SHA の pin ではありません。  
**根拠:** [brief の不変条件:23–30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1068-skeleton-decl-freeze/s1-brief.md:23)、[凍結 JSON の記録値](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/output/s1-freeze/known_axes_freeze.json:46)、[_HISTORICAL_CODE_PATHS と照合条件](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/s1_known_axes_freeze.py:864)、[contract-loader 閉包](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/campaign_lock.py:80)、[duration ledger の形式](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/acceptance_duration_ledger.json:1)。  
**影響:** JSON を再 pin すると既存の歴史的参照値が変わります。drift node を新検査の検出力に数えると変異結果の帰属が誤ります。  
**推奨:** **should** — 凍結 JSON と duration ledger は触らず、直接 admission／整合テストと contract-loader-drift の失敗 node を分けて記録する。変更前 SHA は現物確認用とし、新しい固定値にしない。

## 総括

案 B が R4・R5・R7 の提示形と同じ関数内への移設形を閉じます。  
現行 producer の prefix は骨格のみ、または開き括弧直後の tally 付きです。  
block、epilogue、ENOENT／stock／marker ありの三分岐と既存テストの期待は維持します。  
原文 bytes への結合は CCBench pin の `abort()` 冒頭変更でも生じるため、pin 前進時に独立照合で検出します。  
追加の helper、互換層、台帳、一般化した検査は本題の実装に含めません。  
所有が同じ実装 2 file と fixture 4 file なので Codex author 1 本で妥当です。差分の目安は約 250～350 行、compile fixture の stub が主な増分です。  
静的検査のみ行い、テストは実行していません。