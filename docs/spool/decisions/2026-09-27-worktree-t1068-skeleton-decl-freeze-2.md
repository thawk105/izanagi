---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-27
wave: worktree-t1068-skeleton-decl-freeze
seq: 2
---

## {{D:trigger-abort-prefix-freeze}}. trigger 骨格の凍結を abort() 宣言行から BEGIN 行頭直前まで広げ、受理形は骨格のみと骨格 + S8a 計装 tally の 2 つに限る

**決定:** build admission の trigger 軸検査に、marker のある source の BEGIN 行頭直前の bytes が
`void TxExecutor::abort() {` から始まる凍結 2 形 (骨格のみ / 宣言行直後に S8a 計装 tally を挿入した形) のどちらかで終わることを論理積で足す。
2026-08-16 /rulings 全件 第 3 回 項 22 (「trigger 骨格 = 凍結する (R4 / R5 / R7)」) の実装である。
凍結 bytes は CCBench 原文 (pin の abort() 冒頭 20 行)・骨格 patch の prologue 7 行・tally patch の 24 行の 3 定数に分け、それぞれを出所と照合する独立テストで固定する。
実行時には patch も CCBench も読まない。宣言行より前の bytes、block・epilogue の照合、source 不在と stock の受理は変えない。受理集合は狭くなるだけである。
閉じたと主張するのは「abort() 宣言行から BEGIN 行頭直前までの領域内」の R4・R5・R7 の提示形と移設形に限る。
file scope の宣言、前処理器、他 file による名前解決、R1・R3・R6、source 不在の受理は残る限界として docstring と insight に書く。
凍結 JSON (known_axes / measurement / holdout) は再 pin しない (`axis_trigger_gating.py` は wave 前から記録値と不一致で、`_HISTORICAL_CODE_PATHS` が許容している)。

**理由:**
- BEGIN 直前の骨格 prologue だけを凍結すると、`return;`・局所 shadowing・reason reset を prologue の 1 行上 (同じ関数本体) へ移すだけで通る。
  裁定理由の「文字は同じだが意味は死んでいる」状態が残る。変異 M2 (照合を prologue だけへ弱める) が移設版 4 件を受理側へ落とすことで、この差を実測した。
- S8a の特性評価 (coverage / freq) は admitted 経路で、計装 tally を関数の開き括弧の直後に挿入する。これを拒否すると正当な build が止まるので第 2 形が要る。
  misattr は `lockWriteSet` だけを変えるので専用形は不要。
- 定数から正例の入力を作るテストは定数と同時に動くので、出所との独立照合がないと誤った凍結 bytes が緑になる (T-1048 の MUT-3 と同型)。変異 M6・M7 で独立照合だけが落ちることを確認した。
- CCBench 原文 bytes への結合は、pin 前進で abort() 冒頭が変われば HEAD ↔ pin 原文の独立テストが赤になって検出する。候補 C2' の silo 差分は `writePhase` だけである。

**却下した選択肢:**
- BEGIN 直前の prologue 7 行だけを凍結する — 移設で通る (上記)。
- C++ の字句解析・制御流解析で意味を判定する — T-897 の段 6 が自前字句解析の偽受理と過剰拒否を両方向で実証済み。
- misattr 専用の第 3 形・tally の位置を問わない受理 — 前者は不要、後者は tally 位置への `return;` を通す (変異 M5 で実測)。
- 凍結 JSON の再 pin — 保留中の凍結チェーン検証の条件 (凍結 bytes を書き換えない) に反する。
