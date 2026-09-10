単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s1-brief.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s1-brief.md` — 親 brief (terminal 証拠の契約の親案を含む)。**これ自身も検査対象である。**
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/artifacts/t1851-unit-c/s2-plan.md` — 段 2 plan。**守らずに攻撃する対象である。**
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/refs/a2beta-decisions-fragment-9.md` — 継承元の裁定 3 件の逐語 (E1 / E2 は単位 C、証拠の意味規則 3 点、分類 claim / 回復行は囲まない)
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/refs/decisions-verbatim.md` — 確定裁定 11 件の逐語 (特に D1113 / D1114 / D1341 / D1522 / D1530 / D1533)
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/refs/a2alpha-README.md` と `refs/a2alpha-s4-adjudication.md` — v2 terminal の二層拒否 (S5 / S6) を置いた wave。13 節の裁定パッケージと 14 節
6. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/refs/a1-s4-adjudication.md` — A1' が固定した封印 terminal API の signature (本 wave が置き換える対象)
7. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/refs/b2d1-README.md` — 直前 wave。7 節 (閉じていない窓) と 9 節

作業 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a`、HEAD `04f06d032`。コードはすべてこの worktree の中を読む。

## レンズ A — 正しさ境界と裁定整合

plan と親 brief を、**正しさゲートの意味論と確定裁定への整合**の観点で攻撃せよ。plan の推奨を採用するかどうかは問わない。次を必ず検査する。

1. **D1113 (呼び手が status / reason / primary value を選べない)。** plan の封印 API と evidence handle で、campaign (terminal builder) が出した自己申告値が再導出の入力に紛れ込む経路が無いか。`self_report` が「比較にだけ使う」で本当に閉じているか。`mode` / receipt / `session_cv_max` / `reps_expected` のような識別入力を呼び手が偽れば結論が変わるなら、それは D1113 の「値を選べる」に当たるか、当たらないならその根拠 (何が binding で束縛されるか) を現物で示せ。「`excluded_reason → ledger reason` の辞書を権威にしない」を plan が守っているか — 特に (P4) の等値要求 (`require_terminal_reason_equals_classification`) の解決案が辞書を持ち込んでいないか。
2. **再導出 policy の完全性。** 4 語 + `observed` で、生の事実の全組合せが**ちょうど 1 つ**の結論に落ちるか (排他・網羅)。campaign `_run_session` :6312-6323 の precedence と一致するか、一致しない組合せがあれば列挙せよ (例: open 失敗 + probe_after 競合、exec_failures > 0 + CV 超過、throughputs 長不一致 + rep_integrity)。「結論が出せない組合せは fail-closed 拒否」の形になっているか、「不明なら observed」の恒真化が無いか。
3. **証拠の封印と durable 化。** evidence handle の seal が `FloorPostProbeCapability` :96 と同じ強さか (通常構築で偽造できないか、campaign が同型 object を作って渡せないか)。receipts dir への create-only 公開と terminal 行の `terminal_evidence_sha256` の結合で、(a) 行があって file が無い、(b) file があって行が無い、(c) 両方あるが digest 不一致、(d) 同一 digest で内容が再導出と食い違う (改竄)、の 4 状態がすべて replay で拒否されるか。crash 後に権威として読み直す bytes の規則が一意か。
4. **v1 不変と v2 の閉じ方。** v1 台帳 (schema v1) の reader / writer / 全 pin が 1 byte も変わらないか。v2 で旧 `record_attempt_terminal` / `record_classified_failure_terminal` が拒否され続けるか (S5 / S6 の置換が「拒否を外す」だけになっていないか — D1522 の下層直接検査)。E2 の 4 語が v1 の `S8B_RETRYABLE_FAILURE_REASONS` (空) と凍結 4 語に漏れ出さないか。genesis の `retryable_failure_reasons` に 4 語が入ることで既存 v2 世代の bytes / 既存 fixture がどう変わるか。
5. **pre-probe の起動層所有 ((P2))。** 競合時に capture を走らせない分岐が、reservation 済み slot を classify → observation → terminal で正しく閉じるか (row の順序制約、`_assert_observation_row`)。probe を 2 回呼ぶ形が `_external_evidence_sha256` :350 の意味 (classification 時点の外部証拠) を変えないか。
6. **親 brief の (P1)〜(P6) を独立に評価せよ。** 特に (P1) (C を C1 / C2 に割る) が fragment 9 第 1 決定 (E1 は起動層の実際の呼び手を繋ぐ単位 C の中で) と D1530 に整合するか — 「起動層 = launcher を C1 に含める」で十分か、それとも campaign の呼び手が無いと bytes / digest / resume の再読込が定義できない部分が残るか。残るなら**どの field / どの検査**かを名指しせよ。
   plan は親案 14 field に `protocol` / `perf_preflight_receipt` / `open_failure` / `campaign_record` / `finished_at` の 5 field を足して 19 field とした。各追加が D1113 (識別入力の偽装で結論が変わるか) と durable 化 (normalized protocol 全体と session record 全体を証拠へ写す重複が改竄面を増やさないか) の観点で real か、独立に判定せよ。plan の「v2 だけ `require_terminal_reason_equals_classification=False` にし adapter が raw facts から 3 値を再導出して比較する」案 (選択肢 b) が、core の等値 gate を外すことで受理集合を広げる経路 (adapter を迂回して core を直接呼ぶ test / 将来の呼び手) を作らないか、D1522 の下層直接検査で塞げるかを現物で示せ。
7. **親の実測値とその一般化。** brief の実アンカー表の行番号、test node 数 (7 / 75 / 68 / 328)、DW-O09 / O13 節を現物で検算し、誤りを全件列挙せよ。
8. **成果物が実際に効く全層。** 本 wave の gate が production で発火しない (D1114 / D1341) ことを前提に、それでも「効いている」と誤読させる記述が plan / brief に無いか。C2 / D2 の層を実装したふりにしていないか。

## 出力形式

所見ごとに `所見 N` の見出しを付け、(a) 何が問題か、(b) 現物の file:line、(c) real なら放置時に成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるか 1 行、(d) 修正案、(e) 親 brief の (P) 番号または契約 field との対応、を書け。各主張に [実測] / [推測] を付けろ。**blocker / must-fix / nit** を分けろ。scope 外だが real な所見は「裁定パッケージ候補」として別節にまとめろ。

## 制約

- 読取専用である。pytest の実走は要求しない。静的検査でよい。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 出力の最後に `## 総括` 節を置き、blocker 件数、must-fix 件数、契約 field の過不足、(P1)〜(P6) の独立評価 (採用 / 却下 / 条件付き) を 12 行以内で書け。
