単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s1-brief.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s1-brief.md` — 親 brief (terminal 証拠の契約の親案を含む)。**これ自身も検査対象である。**
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/artifacts/t1851-unit-c/s2-plan.md` — 段 2 plan。**守らずに攻撃する対象である。**
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/refs/a2beta-decisions-fragment-9.md` — 継承元の裁定 3 件の逐語
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/refs/decisions-verbatim.md` — 確定裁定 11 件の逐語
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/refs/s2-plan-v2.md` と `refs/s4-adjudication-r2.md` — 設計 wave の plan v2 (「単位 C: 起動層」節) と終端裁定
6. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/refs/a1-README.md`、`refs/a2alpha-README.md`、`refs/b2d1-README.md` — 直前 3 実装 wave の規模実測 (2 wave 連続で見積りが下振れした) と閉じていない窓、codex 子が pytest を走らせられない事実

作業 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a`、HEAD `04f06d032`。コードはすべてこの worktree の中を読む。

## レンズ B — 規模・所有・consumer 漏れ・到達可能性・変異の帰属

plan と親 brief を、**実装可能性・所有範囲・既存 test への波及・入力の到達可能性・変異の帰属**の観点で攻撃せよ。plan の推奨を採用するかどうかは問わない。次を必ず検査する。

1. **規模の実測の検算。** plan の依頼 2 の表 (production 行数、test node 数) を現物で数え直せ。特に `record_attempt_terminal` の全呼び手 (production / test / fake registry)、`[s8b-v2-terminal]` / `_reject_unsealed_s8b_v2_terminal` の pin、v2 terminal の event_keys を pin する test、launcher test の `_RecorderRegistry` :158 と `_Token` :168、`test_ccbench_spawn_sites.py:212`。plan が数え落とした consumer を全件列挙せよ。A1' / A2α では見積りが約半分に下振れした — 同じ型の下振れが無いか。(P5) の「1 wave に収まる」を独立に判定せよ。
   plan は (P5) を不採用とし、C1 を C1a (launcher の pre-probe / sink / reservation 入力面、実装子 1 本、v2 terminal は拒否のまま) と C1b (証拠封印 + E1 / E2 + adapter、実装子 2 本) に割った。この分割を独立に判定せよ: (i) C1a 単独で積んだ状態が「production 整合・既存 test 緑・境界固定」を本当に満たすか (reservation の新 field を launcher test 12 node がどう吸収するか)、(ii) 逆に C1a + C1b を unit1 = launcher + `s8b_terminal_evidence.py` + launcher test / unit2 = core + profile + adapter + その test の 2 本で同時に書いたときの結合点 (`SealedTerminalEvidence` の型と seal、sealed API の signature) が plan の記述で十分に固定されているか、不足なら何を足せば 2 本並列で書けるか。fix 巡数の見積りは A2α (fix 5 巡) と B2 / D1 (fix 2 巡) の実績から根拠を付けて出せ。
2. **入力の到達可能性 (DW-O13)。** 契約の各 field について、値が実環境で取りうる値域を現物で示せ: `OpenedFloorAttempt.measurement` の型と attribute (`calibrator/runner.py` の opened measurement)、`launch_failures` の形、`rep_observations` sink の要素 (`capture_measure_point` :803- が sink へ何を書くか、`token.open()` 前後のどちらで書くか)、`use_perf_from_receipt` の入力型、`assess_session` の入力制約 (空列・非有限)。**到達不能な値を要求する述語**が契約や plan に無いか (例: `probe_after` が null なのに throughputs 非空を許すか、`reps_expected` の出所)。
3. **所有と並列分割。** unit1 (launcher) / unit2 (core / profile / adapter) の file 所有で割ったとき、境界の signature (`SealedTerminalEvidence` の exact field と seal、封印 API の引数) を plan が十分に固定しているか。片方が先に終わったとき他方無しで既存 test が緑を保つか。fake registry (`_RecorderRegistry`) を使う launcher test が、実 adapter の封印 API と同じ契約を要求するか (fake と実体の乖離 = 両層 stub で機構を通らない緑、の型)。
4. **fixture 経由の transitive 赤。** `test_s8b_attempt_registry.py` (75 node) と `test_attempt_registry_core_s8b_profile.py` (68 node) の fixture (v2 profile 生成、genesis 生成、`retryable_failure_reasons` の pin) が E2 の 4 語追加でどれだけ赤になるか、node 名で列挙せよ。`test_s8b_holdout_admission.py` (4,215 行) と `test_s8b_floor_campaign.py` (14,020 行) に v2 台帳の terminal 拒否や genesis bytes を pin する node が無いか。
5. **codex 子が pytest を走らせられない前提。** 直前 3 wave で codex 子は 1 度も pytest を走らせられなかった。plan のテスト計画が「親が 1 回の焦点走で赤を全部掴める」形か — 新設 node の fixture が既存 fixture と衝突する型 (前 wave の fix1 の赤: 同じ campaign identity での二重予約) を予見して書き分けているか。
6. **変異の帰属。** plan の依頼 4 の各変異について、KILLED を期待する node が「他の gate に先に遮られる」経路 (冗長 gate) を現物で確かめ、帰属不成立を列挙せよ。特に「self_report のコピーに置き換える」変異は、self_report と再導出が常に一致する正例だけでは SURVIVED になる — 食い違う負例が到達可能な形で用意されているか。
7. **親の実測値とその一般化。** brief の実アンカー表の行番号、test node 数、consumer 件数、DW-O09 節を現物で検算し、誤りを全件列挙せよ。
8. **C1 / C2 の境界の実効性。** (P1) の分割で、C2 が `launch_floor_attempt` を呼ぶときに本 wave の signature を変えずに済むか。本 wave で足す引数 (mode / receipt / protocol 由来値) の受け口が、campaign の現物 (`_run_session` :6213-、`_assert_perf_mode` :448、protocol の `reps` / `session_cv_max`) から供給可能か。

## 出力形式

所見ごとに `所見 N` の見出しを付け、(a) 何が問題か、(b) 現物の file:line、(c) real なら放置時に成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるか 1 行、(d) 修正案、(e) 親 brief の (P) 番号または契約 field との対応、を書け。各主張に [実測] / [推測] を付けろ。**blocker / must-fix / nit** を分けろ。scope 外だが real な所見は「裁定パッケージ候補」として別節にまとめろ。

## 制約

- 読取専用である。pytest の実走は要求しない。静的検査でよい。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 出力の最後に `## 総括` 節を置き、blocker 件数、must-fix 件数、(P5) の独立判定 (規模)、赤になる既存 node 数の検算、(P1)〜(P6) の独立評価を 12 行以内で書け。
