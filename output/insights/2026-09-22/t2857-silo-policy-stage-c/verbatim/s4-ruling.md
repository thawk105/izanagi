# 段 4 裁定 — [T-2857] silo-function-policy 段階 C (2026-09-22 09:5x JST、親 = Claude manager)

入力: brief.md、codex/s2-plan.md (plan)、codex/s3-consult-A.md (A、正しさ境界)、codex/s3-consult-B.md (B、整合・過剰・見積り)。
裁定 inbox は wave 開始後の更新 0 件、local main は起点 8fd2a2f5c から不動 (09:5x に実測)。
記法: C/ = orchestrator/campaign/、Q/ = orchestrator/tests/、T: = external/ccbench/cc/silo/transaction.cc。

## 1. 所見の裁定 (real / refuted、採否、scope)

| # | 所見 | 判定 | 採否・扱い |
|---|---|---|---|
| A1 | norw 判定に `exit_code == 1` が抜けている (C/s2_verify_calibration.py:411-412) | real | 採用。norw の判定式は `verdict=="non-serializable" and total_cycles>=1 and exit_code==1` の逐語 |
| A2 | 空 checks・ケース欠落で all_pass が真 | real | 採用。必須 run/check 集合を定数で固定し、実結果と完全一致・値は bool・必要な発火数 > 0 を確かめてから集計。空入力・片方策欠落・commit 0 件を test の負例にする |
| A3 / B3 | 最大待機方策・clamp 用・焦点用の方策が未定義、no-limit と上限焦点試験の組合せ | real | 採用。方策集合を §3 で固定。no-limit は上限の焦点試験に掛けず、legacy verify の非検出対照だけにする |
| A4 | hook の呼出しだけを消す変異が計数で見えない | real | 採用。焦点方策が PolicyState 経由で「各 hook が実際に呼ばれた回数」を他 hook の戻り値へ符号化し、probe が戻り値と骨格側の独立計数を照合する (§4) |
| A5 | 4 段検査 → 実 build の接続試験が無い | real | 採用。smoke 入口に 4 段検査を必ず通し、`return true;` (U32 関数) が build 前に止まる負例と合法方策が build へ進む正例を test にする。検査した本文と materialize した本文の digest 一致も |
| A6 | 構文規則の正例・負例の登録不足 (`?:` 型不一致・明示 template 引数・switch fallthrough・入れ子の自己初期化・`ull`・先頭 `::`) | real | 採用。B の fixture に追加 |
| A7 | condition gate の登録は break の意味の証明ではない | real | 採用。登録は条件選択の証明に限ると明記し、各ケースに case/patch/source digest と preprocess 後の対象差分を保存 |
| A8 | 裸 macro だけで「pipeline から定義不能」を一般化できない | real | 採用 (局所)。coverage driver に「通常の TRACE=0 build の compile command と preprocess に probe・break が無い」確認を 1 件入れる。環境一般の新 gate は scope 外 |
| A9 | 軸値 0/1 の閉じ、前提 macro の definedness、absent 出口の stock 挙動 | real | 採用。`SILO_POLICY_VARIANT` は 0/1 以外で `#error`、ON で `NO_WAIT_*` / `BACK_OFF` 未定義も `#error`。absent 出口 (`unlockWriteSet(itr)` は `[begin, itr)` だけ解放、T:185-189 と T:367-379 を親が実測) は変えない。insight に stock の既存挙動として記録 |
| B1 | 見積りの単価が用途違い | real | 採用。§6 で job 種別ごとに積み上げ直す |
| B2 | 生死確認の継続・停止条件が無い | real | 採用。§5 |
| B4 | 無名仮引数の扱いが未決 | real | 採用。**全関数定義で仮引数名の省略を許す** (`-Wextra -Werror` の unused-parameter は単独 TU と実 build の両方で掛かる、`external/ccbench/cmake/CompileOptions.cmake:32`)。型付き署名は不変。設計 §2.7 の「引数名は自由」の明確化として insight と decisions fragment に書く |
| B5 | C が重い | real | 採用。C を C1 (診断 patch + coverage/smoke driver) と C2 (既存登録簿・meta-test 追随 + 接続試験) に分け、C2 は C1 の後 |
| B6 | tokenizer の新設理由 | 一部 real | lexer は grammar module 内に小さく新設する (既存 `_tokens()` は backoff 軸の受理集合に結びついた private 関数で、流用すると軸間で受理集合が連動する。位置情報も欠く)。`backoff_hole_grammar.py` は 1 byte も変えない。汎用 tokenizer framework は作らない |
| B7 | brief のアンカー誤り (lockskip は内側ループの直前)・hook 拒否の断定 | real | brief を訂正扱い (lockskip の挿入点は T:158 の直後・`for (;;)` の前)。login の `cmake --build` の拒否は未実測なので主張しない。build は計画どおり計算ノード |
| B8 | docs の周辺の旧限定 2 か所 | real | 採用。親が docs を局所修正済み (§4 の注記を「trigger-gating 軸についての追補」に限定、§7.3 の diff_digest と mutation-red の射程) |
| plan | 焦点試験のための実 `TxExecutor` 専用 C++ fixture | refuted (過剰) | 不採用。YCSB の高競合 workload + probe build + 焦点方策で到達を実測し、到達しなかった check は緑でなく「未到達」赤とする (DW-G05: 新しい test framework を作らない)。7 要因は静的写像 test + 実走で到達した要因だけ動的照合、未到達要因は未測定と表示 |
| plan | 生死確認に `pipeline.evaluate` + 認可 + GeneratorId + campaign layout | refuted (過剰) | 不採用。C 段の生死確認は既存 coverage driver と同じ診断 build 経路 (condition gate + patchharness + buildcache、診断 build は NON_ADMISSIBLE と記録) で行い、certified 候補とは称さない。E 段の build admission 写像 (設計 §4) は変えない |
| plan | UBSan を独立 module に | 一部 | B の compile module に小さく同居させる (B 提案)。module を増やさない |

## 2. 単位と所有 (素集合)

- **A (先行):** `patches/silo-function-policy-variant.patch`、`C/silo_function_policy_api.hh`、`C/axis_silo_function_policy.py`、`C/silo_function_policy_hand/*.cpp` (§3 の方策本文)、`Q/test_silo_function_policy_template.py`。
- **B (A の後、C1 と並列):** `C/silo_policy_grammar.py`、`C/silo_policy_compile.py` (単独 TU compile と UBSan harness の CLI)、`Q/fixtures/silo_function_policy/contracts/**`、`Q/test_silo_policy_grammar.py`、`Q/test_silo_policy_compile.py`。
- **C1 (A の後、B と並列):** `patches/instr-silo-function-policy-probe.patch`、`patches/broken-silo-policy-norw-validation.patch`、`patches/broken-silo-policy-lockskip-validation.patch`、`patches/broken-silo-policy-<defect>.patch` × 8、`C/silo_policy_coverage.py` (coverage と smoke の 2 sub-command)、`Q/test_silo_policy_coverage.py`。
- **C2 (C1 と B の後):** 既存登録簿と meta-test の追随 (`C/condition_meaning_gate.py`、`Q/test_condition_meaning_gate.py`、`Q/test_ccbench_spawn_sites.py`、`C/materializer_admission.py` と対応 test、`Q/test_p3_s4_loop.py` の patch token 許容集合、`Q/test_campaign.py` の軸 module 組) と、smoke 入口の接続試験 (A5)。
- `patches/README.md` と insight・docs は親が書く (実装子は docs を編集しない)。

## 3. 方策の固定 (A が書く hole 本文、digest は A の test が固定)

| 名前 | abort 後 | lock 競合 | 用途 |
|---|---|---|---|
| `abort0` | 0 | 即 abort | 生死確認、負例の「即 abort」方策、テンプレの既定本文 |
| `maxwait` | 1000 | retry・待機 50 (上限 32 で骨格が abort) | 負例の「最大待機」方策、prefix unlock 変異 |
| `static5` / `static10` | 5 / 10 | 即 abort | 生死確認 |
| `retry` | 0 | retry・待機 0 | 生死確認、reload 変異 (reload 削除で取得成功 0) |
| `huge` | `UINT32_MAX` (`4294967295u`) | 即 abort | clamp の境界正例と clamp 削除変異 |
| `focus` | 状態から導く値 (§4) | 状態から導く応答 | 焦点試験 (3 hook の実呼出し・状態寿命) |

## 4. 焦点試験の観測 (A4 の閉じ方)

- probe (`IZANAGI_SILO_POLICY_PROBE`) は骨格側の独立計数 (abort 出口の到達数、競合 site の到達数、成功 commit 数、retry 後の CAS 成功、上限 abort、clamp 発生、要因別の abort) と、各 hook の**戻り値**を記録する。hook の呼出しの前後に計数 event を置いて「呼ばれた」ことの証拠にしない。
- `focus` 方策は PolicyState に各 hook の実呼出し回数を持ち、戻り値 (待機量の下位 bit など、上限内に収まる形) へ符号化する。probe は戻り値から復号した回数と骨格側の独立計数を worker ごとに照合する。どの hook の実呼出しを 1 か所消しても、この照合だけが赤になる形にする (単一理由)。状態寿命は「成功通知で更新した回数が、同じ worker の次の txn の hook の戻り値に現れる」ことで見る。
- 到達要件: 各 check の対象 event 数 > 0。0 なら check は偽 (未到達) で all_pass に入れない。workload は既存 legacy 構成 (200 records / 4 threads / RMW / 1 秒) を既定とし、到達しない check があれば同じ wave 内で workload を 1 回だけ調整してよい (調整は結果 JSON と insight に記録)。

## 5. 生死確認の継続・停止条件 (B2)

- 「生」= `abort0`・`static5`・`static10`・`retry` の全方策が 4 段検査を通り、build でき、legacy verify と性能構成 verify (1M / 48 threads / skew 0.9 / 3 秒の trace 走) が certified、throughput が出る (bench 1 走)、honest identity (本文ごとに別 digest)、かつ焦点試験で retry 後の取得成功と成功通知後の状態継続が成立。
- 不成立なら修復を試み、許可範囲で直らなければ C 段不合格として後続 (D 段) を止め、ユーザーへ返す。
- 1 走の性能差の大小で軸の生死・優劣を判定しない。throughput は同 job の stock 対照つきの予備値として記録するだけ。地形の判断は D 段、C 合格から E/F へ自動移行しない。

## 6. 変異 (dev-wave 変異 matrix) の事前登録 (DW-M01、位置は実装後に anchor を固定)

| ID | 置換 (実装後に逐語 anchor を固定) | 単一理由 fixture | 期待 KILLED node (案) |
|---|---|---|---|
| M-LEX | 代替綴りの字句拒否を除去 (正規演算子への写像は維持) | 合法な二項 `x bitand y` / `a and b` | grammar の代替綴り test |
| M-TYPE | bool の算術拒否を bool→U32 扱いへ | 他規則に違反しない `(b1 + b2) << 31u` | grammar の bool 算術 test |
| M-SELFINIT | 初期化子の自己参照拒否を除去 | `uint32_t x = x;` と入れ子の自己初期化 | grammar の init.self test |
| M-RETURN | 末尾 return 規則を除去 | 非 void の末尾が if | grammar の return.final test |
| M-ASSIGN | 部分式代入の拒否を除去 | `(a.m = 1u) + (b.m = 2u)` | grammar の assignment test |
| M-RHSLIT | `/= %=` の右辺 literal 要求を除去 | `s.m /= v` | grammar の rhs.literal test |
| M-TU-GLOBAL | TU builder の api 後に大域宣言 1 行を追加 | GlobalEpoch だけを使う compile 単独負例 | compile の外部大域 test |
| M-TU-MACRO | compile argv に `-DTRACE=1` を追加 | `TRACE` を参照する compile 単独負例 | compile の未供給 macro test |
| M-CHK-EMPTY | coverage の必須集合の完全一致を除去 | 空 checks・片方策欠落 | coverage の集計 test |
| M-CHK-NORW | norw 判定から `exit_code==1` を除去 | `exit_code=2` の norw 結果 | coverage の norw 判定 test |
| M-SMOKE-SKIP | smoke 入口の構文検査呼出しを除去 | U32 関数の `return true;` | 接続試験 (C2) |
| M-API-SYNC | api block と header の byte 比較を緩める | 1 byte 改変した api block | template の api 一致 test |

実装後に単一理由性 (前段・後段・内側の別層が同じ入力を拒否しないこと、F820) を確かめ、成立しない変異は登録から外して実効 gate へ再照準する (DW-M01)。期待 node は login self-run か初回 dispatch probe で完全集合に固定する (DW-M08)。

## 7. 計算の見積り (B1 の積み上げ直し、投入前にユーザー確認)

| job | 内容 | 単価の出所 | node 時間 |
|---|---|---|---|
| coverage 1 本 | build 約 20 (負例 3×2・probe 焦点 2・機構変異 8・flag 境界 4・TRACE=0 確認 1・stock 対照) + trace-timeout 期待 2 走の 120 秒待ち | T-2844 の coverage job (6 走で Elapse 132 秒 → 約 22 秒/走) を下側、45 秒/走を上側 + 240 秒 | 0.19〜0.32 |
| smoke 1 本 | stock + 4 方策、各 TRACE build + legacy verify + 性能構成 verify + perf build + bench 1 走 | B-5 の 1 session 217〜510 秒 | 0.30〜0.71 |
| 焦点走 (pytest dispatch) | 3〜4 回 | T-2844 焦点走 Elapse 136 秒、上側 230 秒 | 0.11〜0.26 |
| 変異 matrix (dispatch) | 12 変異 + baseline + probe | T-2844 の 1 run 27〜38 秒 (待ち列を除く) | 0.10〜0.25 |
| 受入全走 | 1〜2 回 | 直近 3 shard の test 実行 668 秒 (下側)、1 回 0.25 h (上側) | 0.19〜0.50 |
| coverage 再走 | fix 後に 1 回 (上側だけ) | 上と同じ | 0〜0.32 |
| **合計** | | | **約 0.9〜2.4 node 時間** |

- 旧単価による換算で、上下限ではない (新骨格の build 所要・verify の trace 量は未測定)。login の構文検査・単独 TU compile・UBSan harness は node 時間に含めない。
- LLM (サブスクの Codex 子): 実装子 4 本 (A・B・C1・C2)、レビュー 2 本、焦点再レビュー 1〜3 本、fix 1〜3 本の見込み。

## 8. scope 外 (実装しない、insight に記録)

E 段の候補生成・p3_s4_loop / pipeline への検査接続・coder / auditor role・`.claude/agents/`、環境経路の診断 macro 一般遮断 gate、stock の absent 出口の lock 解放範囲、7 要因の全経路の動的実証 (YCSB で到達した要因以外)、GeneratorId・campaign layout・新 reject 理由・新台帳。

## 9. 不変条件 (再掲なし、brief のとおり) への追加

- 軸値は 0/1 に閉じる。ON で前提 macro の未定義・別値は `#error`。
- 既存の norw / lockskip / early-unlock patch と driver は 1 byte も変えない (新骨格用の norw / lockskip は新 file、early-unlock は既存 patch を厳密適用で使えなければ停止して親へ報告)。
- `backoff_hole_grammar.py`・`diff_quarantine.py`・`coder_effect_gate.py`・`pipeline.py`・`p3_s4_loop.py` の挙動を変えない (読むだけ・import して使うだけ)。
