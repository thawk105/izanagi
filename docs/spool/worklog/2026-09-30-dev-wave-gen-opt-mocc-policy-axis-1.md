---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-gen-opt-mocc-policy-axis
seq: 1
title: MOCC で LLM が関数単位の方策を書く口 (MOCC 版の関数方策の軸) を設計した — v1 は待ち方だけ (abort 後の待ち・cold read の writer 待ちの待ち時間・commit 通知、方策は abort を新しく生まない)、施錠方式は証拠面が読み側を表さないので重い区分、文法は核 + CC ごとの表、MOCC の変異面 gate は軸ごとの証拠束縛へ一般化が要る (insight のみ、計算なし、branch worktree-dev-wave-gen-opt-mocc-policy-axis)
---

## 本文

- 依頼: 並行 wave の md_10 (`/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_10.txt`、共通指示 `common-3.txt`)。一次資料は `output/insights/2026-09-30/gen-opt-mocc-policy-axis/README.md`。対象の句「MOCC 版の関数方策の軸」を含む item は台帳に無かったので、md_3 の先例と同じく設計の記録はこのエントリとし、実装の item だけを新規に起票した。
- 軽量版で段 2・3 を省き、段 6 の read-only レビュー 1 本を残した (設計 docs の wave のため、common-3 §6)。レビュー (Codex、レンズ A 事実照合・レンズ B 規律 2・3 の攻撃) は NO-GO で must-fix 2・should-fix 3。親は全件 real と裁定して直した: 初版は cold read の待ちの hook に「諦める」を持たせ、諦めたときに読み集合へ積まなければ RLL の組成を方策が変えないと書いたが、`abort()` → `construct_RLL()` が abort の時点の読み集合から次試行の RLL を作るので、abort の時点を選ぶこと自体が RLL を選ぶ (v1 の hook を待ち時間だけにし、abort 付きを施錠方式の側へ移した)。受理集合の差分 test で compile の判定の全 field を比べると一時 path の違いで一致しない (比較の定義を書いた)。ほか trace の断定の範囲、既存負例の到達計数、見積りの仮定の明記。焦点再レビュー 1 巡目は前回の 5 件をすべて closed とし、新しい must-fix 1 件 (差分 test で比べる field の列挙から `PolicyDecision.stage` が抜けていた) を親が実物で確かめて直した。
- 設計の途中で見つけた事実: MOCC の変異面 gate (`orchestrator/tests/test_mocc_template_proof.py`) は MOCC の軸 module が温度述語の 1 本だけであることを固定し、発火時に温度述語の template に束縛された証拠だけを要求する。新しい軸を足すと固定が赤になり、固定だけを外すと新しい軸は自分の証拠なしに gate を通る。
- セッションの異常: model を指定しない Agent 呼び出しが hook `guard_agent.py` に拒否され、sonnet を明示して投げ直した (既知の規則)。`EnterWorktree` の name 形は 1 回で成功した。
- 工数: 調査子 2 本 (sonnet、read-only: Silo 軸の分解、MOCC の hook 候補)、Codex の read-only レビュー 1 本 (11 call・136 秒) と焦点再レビュー 1 本。計算ノードの job なし。

## 次の一手差分

### 新規

- {{T:mocc-policy-axis-onboarding}} **P2・新規、ユーザー承認待ち**: MOCC 版の関数方策の軸の段階 A (軸候補の人間承認) と段階 B (軸定義シートと 3 レンズの敵対レビュー、必須条件を D 番号で凍結)。設計草稿は `output/insights/2026-09-30/gen-opt-mocc-policy-axis/README.md`: v1 の hook は abort 後の待ち (`TxExecutor::abort` の共有 backoff の置き換え)・cold read で他者の writer lock を待つ所の待ち時間 (諦める選択肢は無い)・commit の通知の 3 つで、方策は abort を新しく生まない。`AbortReason` は Silo の 8 値に MOCC 固有の 2 値を足した 10 値、観測は要因・試行番号・乱数だけ。施錠方式 (温度述語・RLL・`lock()`・待ちの途中の abort) は v1 に入れない (同 §4.5 の条件 E1〜E6)。段階 B の攻撃対象: 待ちの hook を待ち時間だけにした判断、上限到達で stock の spin に戻す案、差分 test の入力列と比較の定義、gate の一般化、温度を観測に渡さない判断。D2134 項 9・D2159 項 9 により MOCC の新しい軸の採用は別裁定。
- {{T:policy-grammar-core-tables}} **P2・新規**: 関数方策の検査器 (`silo_policy_grammar.py`・`silo_policy_compile.py`・`silo_policy_ir.py`) を「規則の核 + CC ごとの表」に分け、Silo の表を既定にする (呼び出し側は変えない)。名前空間の直書き 6 か所・hook 署名の辞書・UBSan harness の定数・IR の要因名を表から導く (同 §4.2)。Silo の受理集合を変えないことは、分ける前の 3 module の凍結写しと分けた後の核 + Silo 表に同じ入力列 (契約 fixture 85 件・手書き方策・IR 16 点・字句を変えて作る入力、件数は事前登録) を掛け、判定の一致で見る (文法の判定は全 field、compile の判定は一時 path を置き換えてから比べる。同 §4.3、D387 の限界は残る)。[T-2886] (段 A の軸の受理文法) と同じ部品なので、先に着手する方が核を作り、後の方は表を足すだけにする。Codex author、login のみ。前提: {{T:mocc-policy-axis-onboarding}} の段階 B か [T-2886] の着手のどちらか。
- {{T:mocc-policy-axis-skeleton}} **P2・新規**: MOCC 版の軸の段階 C の実装。API header・coder の接続仕様・軸定数 module・MOCC の表と契約 fixture (MOCC の `CLL_`・`RLL_`・`epotemp_` などの拒否例を含む。MOCC の表には `PolicyAction`・`LockResponse` が無い)・骨格 patch (`cc/mocc/transaction.cc` と `cmake/Options.cmake`、軸 macro OFF で inert、`BACK_OFF` と温度述語の template について `#error`)、MOCC の変異面 gate を軸ごとに自分の証拠へ束縛する形に一般化 (温度述語の軸の要求は変えず、「新しい軸の証拠が無い」「別の軸の証拠を指す」の 2 対照を赤にする)、`condition_meaning_gate.py` への軸 macro の登録。骨格は validation に hunk を持ち、G2 修理の X と同じ区間なので、作る時点の pin に合わせる (同 §5 U2・U3)。Codex author。前提: {{T:mocc-policy-axis-onboarding}} の段階 B の凍結と {{T:policy-grammar-core-tables}}。
- {{T:mocc-policy-axis-proof}} **P2・新規、計算はユーザー確認が要る**: MOCC 版の軸の段階 C の出口の実証と生死確認。既存の負例 `broken-mocc-*` 5 本を軸 ON に積んで 2 方策で走らせ、負例ごとに壊した箇所への到達と期待する X・P・G2 の発火を数えること (到達 0・発火 0 は不合格)、機構の変異 (hook の配線を外す・上限を外す・clamp を外す・要因の取り違え・待ちの後の版の読み直しを外す) が壊す経路に到達して赤になること、手書き方策 3 本の write-heavy の pair。試算は生死確認 0.70〜0.75、骨格の実証に Silo の実績の合計約 1.12 をそのまま当てて合計約 1.8〜1.9 + 負例の増分 (未見積り) node 時間 (1 評価 0.206〜0.220 を当てた。MOCC の pair の単価は未実測) で、2 を超えうるので投入前に確認 (同 §6)。read-heavy の評価は [T-2919] (G2 修理 X を含む pin への前進) の後 (同 §7)。driver の protocol の口と coder role の MOCC 版は段階 D の偵察の後 (同 §5 U5)。前提: {{T:mocc-policy-axis-skeleton}}。
