# silo-function-policy 軸の段階 C — 骨格・型付き検査器・焦点試験・負例・機構変異・生死確認 (2026-09-22、[T-2856] → [T-2857])

- 位置づけ: 軸オンボーディング (`docs/axis-onboarding.md`) の段階 C の記録。設計の正本は `output/insights/2026-09-21/silo-function-synthesis-space/README.md` (以下「設計」)、採用判断は D2214、本段の設計判断は同じ wave の decisions fragment。可変状態の正本 (worklog 末尾・`docs/phase3.md`) にはしない。
- wave: branch `worktree-dev-wave-t2857-silo-policy-stage-c`、起点 local main `8fd2a2f5c` (2026-09-22 08:53 JST に開始 gate rc=0)。submodule pin `e9e477ca` (不変)。wave 中に local main を 3 回取り込んだ (`eef04f5a7` を `7b6114bb7` で、verifier の変更を含む `bc3b23953` を `6d7014707` で、`56ce0f244` を `fa217176d` で)。
- 逐語 (`verbatim/`): 依頼 `request.md`、段 1 brief `brief.md`、段 2 plan `s2-plan.md`、段 3 相談 `s3-consult-{A,B}.md`、段 4 裁定 `s4-ruling.md`、B / C1 の接続 interface `interface-b-c1.md`、段 5 の実装子の報告 `s5-author-{a,b,c1,c2}.md`、段 6 のレビュー `s6-review-{A,B}.md`、段 6 の裁定 `s6-ruling-{1..6}.md`、fix 子の報告 `s6-fix-{1..6,6b}.md`、焦点再レビュー `s6-focus-{1,2}.md`、UBSan harness の結果 `ubsan-1.json`、coverage 3 回目の要約 `coverage-3-summary.txt`、実走に使った verifier の module sha256 `verifier-identity-6d7014707.txt`。行末空白の可逆正規化は `verbatim/NORMALIZATION.md`。段 2・3・6 の prompt と codex の受領証は wave の job dir に置いた (repo 外)。

## 0. 要約

1. **段階 C の出口 (設計 §9 項 6〜9) と生死確認をすべて実測で満たした。**
   - 項 6 (identity): 軸 OFF の inert (src_token = stock)・軸 ON の honest (手書き方策 6 本が相異なる token)・include 一致・diff-of-diffs が計算ノードの compiler で成立 (焦点走 f-a1)。
   - 項 7 (既存 3 負例の軸 ON 積み直し × 2 方策): norw は non-serializable・cycle > 0・exit 1、lockskip は X 理由 2 種、early-unlock は保持欠落のみ。既存 driver と同じ判定式で 6 走とも合格。
   - 項 8 (probe の焦点試験): 3 hook の実呼出し・成功 commit 後の状態継続・retry 後の取得成功・上限 abort・clamp・要因の保存則と照合に到達して合格。
   - 項 9: 契約 fixture 85 本が構文検査・単独 TU とも期待と一致、UBSan harness 1 回が all_pass、検査段ごとの自己試験は変異 matrix で確認 (§3.5)。
   - 生死確認 (smoke): stock と手書き方策 4 本が 4 段検査 → build → legacy / 性能構成 verify (certified) → bench → honest identity をすべて通過。
2. **受理契約 policy-C++ v1 は、仮引数名の省略を許す明確化だけを足した。** 型付き署名と規則は D2214 決定 4 のまま。
3. **段 4 裁定の誤りを 1 つ訂正した。** hook の実呼出しを 1 か所消したとき赤になる照合は 1 種とは限らない (abort 解除 {abort, lock, commit}、lock 解除 {abort, lock}、commit 解除 {commit})。各集合は互いに異なるので、宣言した赤・緑の集合の完全一致で判定する。
4. **機構変異の判定には、変異が壊す経路への到達の証拠を同構成の probe 走で要求した。** 事前登録の `maxwait` では上限出口にほぼ届かず空振りした (F247 の型)。prefix unlock は出口ごとに 1 枚ずつに分けた (焦点再レビューの must-fix)。
5. **計算ノードの実走で、実行時の前提の欠陥が 1 走に 1 件ずつ出た** (F139 の型)。4 巡目で実装子に全 case の外部交点の照合表を作らせてから止まった。
6. 手書き方策の bench throughput は stock の約 2.7〜3.6 倍だったが、同 job の stock 対照つきの 1 走の予備値であり、比較の主張はしない。地形の判断は段階 D が行う。

## 1. 依頼と裁定

- 依頼 (ユーザー直接起動の `/dev-wave`): 手順書 §4 の第 3 列と段階 E の planner 例外を commit し、D2214 の必須条件どおり段階 C を Codex author で実装・実測する。計算は投入前に合計見積りを示してユーザー確認。正しさゲートは不変・規律 2 を緩めない。本題だけ。
- 計算のユーザー確認: 段 4 で用途別に積み上げ直した見積り (約 0.9〜2.4 node 時間) を示し、2026-09-22 19:4x JST に「全体を承認 (合計 2.4 node 時間を上限、超えそうなら止めて再確認)」を得た。質問は 09:5x に出し、回答まで約 10 時間待った。設計時の換算 2.41〜4.12 node 時間との差は、受入の単価を外側の経過時間ではなく job の実測 Elapse で数え直したことによる。
- 段 4 の主な裁定 (`verbatim/s4-ruling.md`):
  - 受理契約の明確化: 全関数定義で仮引数名の省略を許す (`-Wextra -Werror` の unused-parameter は単独 TU と実 build の両方で掛かる)。
  - 焦点試験は実 `TxExecutor` を直接呼ぶ専用 fixture を作らず、YCSB の既存 workload + probe build + 焦点方策で到達を実測する。未到達の check は緑にしない。
  - 生死確認は `pipeline.evaluate` + 認可 + campaign layout を使わず、既存 coverage driver と同じ診断 build 経路で行う。診断 build は NON_ADMISSIBLE で、certified 候補とは称さない。E 段の build admission 写像 (設計 §4) は変えない。
  - 機構変異は相互排他の patch に共通の裸 macro `IZANAGI_BREAK_SILO_POLICY`。
  - lexer は grammar module 内に小さく新設した (既存 `backoff_hole_grammar._tokens()` を流用すると軸間で受理集合が連動する)。

## 2. 実装 (単位と commit)

| 単位 | commit | 内容 |
|---|---|---|
| T-2856 docs | `4c0eb08b9`、`8f87239bd` | 手順書 §4 の第 3 列 (見出しの 3 型化、新 3 行、補足)、段階 E の planner 例外、§4 注記と §7.3 の射程の局所修正 |
| A | `edee44d75` | 骨格 patch `patches/silo-function-policy-variant.patch`、api header の単一正本 `orchestrator/campaign/silo_function_policy_api.hh`、軸定数 `axis_silo_function_policy.py`、手書き方策 6 本、静的 test |
| B | `4970f0396` | 型付き構文検査 `silo_policy_grammar.py`、単独 TU compile と UBSan harness `silo_policy_compile.py`、契約 fixture 85 本と manifest |
| C1 | `2f548f1e3` | probe patch、負例の軸 ON 版 2 枚、機構変異 patch、焦点方策 `focus.cpp`、coverage / smoke driver `silo_policy_coverage.py` |
| C2 | `23acbfa60` | 既存登録簿・閉集合 test の追随 (condition gate の DefineSpec 40→43 など、既存 entry は不変)、smoke 入口の接続試験、hook 変異の赤集合の完全一致判定 |
| 段 6 fix | `da3f51c52`、`5e5506ec9`、`de585bb80`、`eaa39806c`、`53fa5330f`、`0a4b38abe` | §4 |
| 記録 | `c7fc4846c` (smoke)、`62746d625` (coverage) | 計算ノードの結果 JSON |

実装面の全ハンクは Codex author (gpt-6-astra、reasoning medium) が子 worktree で書き、親は所有 path の差分だけを統合した。`patches/README.md` の新しい節と本 insight・台帳 fragment は親が書いた。

## 3. 実測

### 3.1 login の検査 (node 時間に数えない)

- UBSan harness の正式 1 回 (2026-09-22 20:23 JST、g++-12.3.0、結果 = `verbatim/ubsan-1.json`): all_pass。手書き 7 方策 (`abort0`・`focus`・`huge`・`maxwait`・`retry`・`static10`・`static5`) は全 8 要因 × 試行番号 0〜33 × 2 通りの呼出し列でそれぞれ 1,904 呼出し、UBSan 報告 0。UB を含む負例 3 種 (零除算・過大 shift・signed overflow) はどれも UBSan が検出 (rc=1)。
- 構文検査の自己確認 (単位 B の子、`verbatim/s5-author-b.md`): 契約 fixture 85 本が構文検査・単独 TU compile とも期待と一致 (構文検査で受理 21 / 拒否 64、単独 TU で受理 64 / 拒否 21)。自己初期化と switch の fallthrough は g++ の `-Wall -Wextra -Werror -fsyntax-only` を通るので、拒否するのは構文検査だけである (設計 §2.7 の分担どおり)。

### 3.2 焦点走 (計算ノード)

| 走 | 対象 | request | Elapse | 結果 |
|---|---|---|---|---|
| f-a1 | 単位 A の test 1 file (単独走) | 17892.nqsv | 27 秒 | 8 passed |
| f-b1 | 単位 B の test 2 file + メタテスト 2 file | 17950.nqsv | 27 秒 | 29 passed |
| f-c1 | 単位 C1 の test 1 file (単独走) | 17963.nqsv | 10 秒 | 9 passed |
| f2 | 変更 module を参照する test 33 file + メタテスト 2 file | 17975.nqsv | 228 秒 | 8 failed / 4770 passed / 8 skipped (§4 の fix 1) |
| f3 | 同 35 file | 18048.nqsv | 120 秒 | 8 failed / 4773 passed / 8 skipped (§4 の fix 2) |
| f4 | 同 35 file | 18075.nqsv | 118 秒 | 4785 passed / 0 failed / 8 skipped |
| f5 | driver 系 4 file | 18161.nqsv | 91 秒 | 100 passed / 2 skipped |
| f6 | 同 | 18190.nqsv | 91 秒 | 107 passed / 2 skipped |
| f7 | driver の test 1 file (単独走) | 18238.nqsv | 12 秒 | 27 passed |
| f8 | driver の test・`test_p3_s4_loop.py`・`test_ccbench_spawn_sites.py`・メタテスト | 18327.nqsv | 96 秒 | 764 passed / 2 skipped |

### 3.3 coverage (C 段出口 7・8・9 の実走)

最終 = wave commit `0a4b38abe` の木で 1 回 (request 18328.nqsv、1 node、Elapse 1,016 秒、結果 = `output/env/pegasus/calibration/silo_function_policy_coverage.json`、記録 commit `62746d625`)。all_pass = true、33 case・61 check すべて真。verifier は main `bc3b23953` 取り込み後の版 (module sha256 = `verbatim/verifier-identity-6d7014707.txt`)。

| 区分 | case | 結果 |
|---|---|---|
| 既存 3 負例 × 2 方策 | norw / lockskip / early-unlock × `abort0` / `maxwait` | norw は non-serializable (cycle 39,124 / 15,264)・exit 1、lockskip は indeterminate・X 理由 `not-locked-at-entry` と `lock-lost-before-write` の両方、early-unlock は indeterminate・X 理由は `lock-lost-before-write` だけ。break が軸 ON の compile 経路に載っている前処理の証拠と case / patch / source の sha256 つき |
| 焦点 | `focus/focus` | 3 照合の一致 57,003〜61,777・不一致 0、成功 commit 後の比較 57,003 一致・0 不一致、要因の照合 57,003 一致・0 不一致、retry 後の取得成功 29,787 |
| 焦点 | `focus/retry` | retry 後の取得成功 18,537、上限 abort 125,169 (うち prefix 保持下 20,225)、要因 `lock_conflict`、保存則成立 |
| 焦点 | `focus/huge` | clamp 2,939 回 (abort ごとに要求 `4294967295` → 1000 µs に clamp)、certified |
| 焦点 | `focus/abort0` | prefix 保持下の action-abort 出口 24,619 回、上限出口 0 回 |
| 機構変異 | hook 解除 3 件・要因誤記録 | 赤の集合が宣言と完全一致 (abort 解除: abort / lock / commit の不一致 621,750 / 214,017 / 214,044、lock 解除: abort / lock 91,041 / 155,915、commit 解除: commit 53,253、要因誤記録: reason 4,260)、緑の集合は不一致 0 |
| 機構変異 | 再読込削除 | retry 後の取得成功 0 (対照 `focus/retry` 18,537) |
| 機構変異 | clamp 削除 (`huge`)・prefix unlock 2 出口 (`abort0` / `retry`) | 3 走とも trace-timeout、各対照は certified。prefix unlock は同構成の probe 走で prefix 保持下の到達を確認 (上の 2 行) |
| 機構変異 | 上限削除 (`retry`) | certified (非検出対照、検出力の主張に使わない) |
| flag 境界 | 軸 ON + `BACK_OFF=0` / `2`、`NO_WAIT_OF_TICTOC=1`、`NO_WAIT_LOCKING_IN_VALIDATION=0` | 4 種とも骨格の `#error` で停止 |
| TRACE=0 | 通常 build (軸 ON + `abort0`) | compile command に `IZANAGI_` の define なし、前処理に probe・break の断片なし |

- 到達の証拠は同構成の別走の probe であり、変異走そのものの到達ではない (結果 JSON にも明記)。
- 7 要因のうち YCSB (delete・insert・scan なし) で到達しない要因は、写像の静的検査 (単位 A の test) だけで、動的な照合は到達した要因に限る。

### 3.4 smoke (生死確認)

wave commit `6d7014707` の木で 1 回 (request 18208.nqsv、1 node、Elapse 793 秒、結果 = `output/env/pegasus/calibration/silo_function_policy_smoke.json`、記録 commit `c7fc4846c`)。all_pass = true、5 case・30 check すべて真。この後の fix (5・6 巡目) は coverage の case 表と判定と probe だけを変え、smoke の経路は変えていない。

| 方策 | legacy verify | 性能構成 verify (1M / 48 threads / skew 0.9 / 3 秒) | bench 1 走の throughput (txn/s) |
|---|---|---|---|
| stock (軸 OFF、src_token = stock) | serializable | serializable | 1,226,994 |
| abort0 | serializable | serializable | 4,174,467 |
| static5 | serializable | serializable | 4,400,288 |
| static10 | serializable | serializable | 3,918,609 |
| retry | serializable | serializable | 3,281,454 |

- 4 方策とも 4 段検査 (DiffQuarantine → effect gate → 構文検査 → 単独 TU compile) を通った本文だけが build され、source identity は stock と別で互いに異なる (honest identity)。
- throughput は同 job の stock 対照つきの 1 走の予備値で、比較の主張はしない (段 4 裁定 §5)。既知最良 (`p2_2_flag_opt`、元 flags) との比較も、rep・同時刻の複数走もしていない。
- 段 4 裁定 §5 の「生」の条件は、smoke と coverage の両方で満たした。

### 3.5 変異 matrix (dev-wave、段 4・段 6 の事前登録)

- 独立 clone (D1009) の固定 commit `0a4b38abe` で `tools/mutation_worktree.py` を dispatch 本走 (`--runner-mode dispatch --detached`、`--force-dispatch`)。test の集合は 2 group に分けた: 小さい group = `test_silo_policy_grammar.py`・`test_silo_policy_compile.py`・`test_silo_function_policy_template.py`・`test_silo_policy_coverage.py`・`test_silo_policy_smoke_entry.py`、登録簿 group = `test_ccbench_spawn_sites.py`・`test_p3_s4_loop.py`。
- 期待 node は、全件 SURVIVED 期待の probe で観測した失敗 node の完全集合から作り (DW-M08)、final はそれとの完全一致だけを KILLED と数えた。spec・結果 = `verbatim/mutation/`、spec 生成の道具は wave の job dir (`make_mutation_specs.py`、各 anchor が対象 file に 1 回だけ現れることを検査)。
- **final: 15 / 15 KILLED (MISMATCH 0・SURVIVED 0)、基準走は 2 group とも PASSED。**

| ID | 壊したもの | 落ちた node (final、完全一致) |
|---|---|---|
| M-LEX | 代替綴りの字句拒否 | 代替綴りの test + manifest 横断 2 |
| M-TYPE | bool の算術拒否 (bool を U32 扱いに) | bool 算術の test + manifest 横断 2 |
| M-SELFINIT | 初期化子の自己参照拒否 | 自己初期化の test + manifest 横断 2 |
| M-RETURN | 末尾 return 規則 | 末尾 return の test + manifest 横断 2 |
| M-ASSIGN | 部分式の代入拒否 | 部分式代入の test + manifest 横断 2 |
| M-RHSLIT | 除数・shift 量の literal 要求 | literal 除数の test + manifest 横断 2 |
| M-TU-GLOBAL | 単独 TU に大域宣言を 1 行足す | 外部大域の test + compile manifest |
| M-TU-MACRO | 単独 TU の argv に `-DTRACE=1` | 未供給 macro の test + compile manifest |
| M-API-SYNC | api block と header の byte 比較 | 1 byte 改変の負対照つき api 一致 test |
| M-CHK-NORW | norw 判定の `exit_code == 1` | norw 判定の test |
| M-POSTCOMMIT | 成功後比較の到達要件 | 成功後の状態観測の test |
| M-SMOKE-SKIP | smoke 入口の構文検査 (受理扱いにして compile だけ) | smoke 入口の接続試験 + 4 段検査の束縛 test |
| M-PREFIX-REACH | prefix 保持下の到達要件 | 上限出口・action-abort 出口の到達要件の test 2 |
| M-GATE-DOM | gate の呼出しを `if macros:` の内側へ | 交差検査 3 + build sink の行番号 pin 1 |
| M-INGRESS | smoke 入口に `render_hole` の直呼び (到達しない分岐) を足す | materialize 入口の閉集合 test + build sink の行番号 pin 1 |

- M-GATE-DOM と M-INGRESS の行番号 pin の赤は、変異で行数が変わったことの副次の赤で、受理集合の変化ではない (DW-M03)。本来の検出点は交差検査 3 と閉集合 test である。
- **事前登録からの変更 (erratum):** (1) M-CHK-EMPTY は必須集合の一致判定を外しても後段 (`checks == derived`・到達検査) が拒否を保つ過剰決定のため、段 6 裁定 1 巡目で登録から外した (冗長 gate、DW-M03)。(2) M-GATE-DOM の最初の形 (条件式 `X if macros else []`) は probe で SURVIVED した。既存の交差検査が式の中の呼出しを分岐を見ずに数えるためで、文の `if` にした形へ照準し直して probe を取り直した (§5)。(3) M-POSTCOMMIT・M-GATE-DOM・M-INGRESS・M-PREFIX-REACH は段 6 で追加登録した (fix 前)。
- 変異走の runner 時間の合計は 2,207 秒 (probe 3 回と final 2 回、待ち行列を含む上限値)。

## 4. 段 6 の経緯 (所見・赤・fix)

| 巡 | 入力 | 直したもの | 裁定 |
|---|---|---|---|
| 1 | 焦点走 f2 の赤 8 件、レビュー A (NO-GO、must-fix 3)・B (NO-GO、must-fix 2) | 交差検査と gate の支配 (F1)、試験用 CMake fixture の cache 変数 (F2)、materialize 入口を既存 `quarantine` 経由に (F3)、screening の既定値 (F4)、prefix unlock の出口別の走 (F5)、重複対照の共有 (F6)、smoke の timeout 接続試験 (F7)、成功後の状態観測 (F8) | `verbatim/s6-ruling-1.md` |
| 2 | f3 の赤 8 件、修正前 coverage の gate 拒否 | gate を 1 回 1 macro に (G1)、probe / break の companion を外す (G2)、行番号 pin (G3)、compile command の両形 (G4)、拒否理由の保存 (G5) | `s6-ruling-2.md` |
| 3 | coverage-1 の `preprocess-failed` | 最初の gate の前に依存物準備の stock build (H1) | `s6-ruling-3.md` |
| 4 | coverage-2 の owner 行の非一意 | owner 行を ycsb target で選ぶ (I1)、全 case の外部交点の照合と修正 (I2) | `s6-ruling-4.md` |
| 5 | coverage-3 の偽 1 件 (上限出口の変異が certified) | 上限出口の変異を `retry` に、到達の証拠を要求 (J1) | `s6-ruling-5.md` |
| 6 | 焦点再レビュー 1 巡目 (NO-GO、must-fix 1) | prefix unlock を出口ごとの 2 枚に、prefix 保持下の到達計数と `focus/abort0` (K1・K2) | `s6-ruling-6.md` |

- 段 4 裁定 §3 の方策表は prefix unlock 変異に `maxwait` を指定していたが、親が C1 の投げ文で `abort0` と書き違えた (レビュー A / B が捕捉)。
- fix 2 巡目の根拠にした「site 数の不一致」は read-only 調査子の静的な推定で、実機の理由 code (`preprocess-failed`) は fix 2 の後に初めて取れた (裁定 3 巡目 H2 で訂正)。
- 上限出口の変異の `maxwait` が上限出口に届かなかったことは、probe を掛けていない走から直接は確かめておらず、同じ workload の `retry` の probe 走が上限に大量に到達したことからの推定である (焦点再レビュー 1 巡目の指摘)。
- coverage 3 回目は 32 case (共有対照 5 件を含む)・55 check。最終構成は 33 case・61 check (`focus/abort0` と出口別の変異を足した)。
- 焦点再レビュー 2 巡目は GO (must-fix なし)。should 1 件 (`wrong-reason` 変異の複製ループが probe の新しい到達計数に追随していない) は、この変異の判定が同計数を使わず結果の値・合否が変わらないので直していない。

## 5. 観察した stock の既存挙動 (本件では変えない)

- `lockWriteSet()` の absent 出口 (T:185-189) は `unlockWriteSet(itr)` を呼ぶが、`unlockWriteSet(end)` は `[begin, end)` だけを解放する (T:367-379)。したがって absent と判明した現在の tuple の lock は、この出口では解放されない。軸 ON の骨格はこの出口を変えていない (段 4 裁定 A9)。YCSB は delete を行わないので実走では到達しない。CCBench の上流の不具合かは本 wave では判定していない。
- 既存の define / build sink 交差検査 (`orchestrator/tests/test_ccbench_spawn_sites.py`) は、条件式 (`X if c else Y`) の中の gate 呼出しを分岐を見ずに「呼んだ」と数える。変異 M-GATE-DOM の最初の形 (条件式) はこの検査を生き延び、文の `if` にした形で検出された (§3.5)。解析の変更は scope 外。

## 6. 記録前の検査 (DW-S07)

- 三軸語の走査器 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`) は rc=1。holdout hit 3 件はいずれも main に既存の `output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の `journal.jsonl`・`manifest.json`・`result.json` で、本 wave の追加 file の hit は 0 件 (走査 log は wave の job dir の `three-axis-search.log`)。
- 逐語の行末空白は 4 file を可逆に除いた (`verbatim/NORMALIZATION.md`)。stage した記録の `git diff --cached --check` は指摘なし。

## 7. scope 外と残存リスク

- scope 外 (実装していない): 段階 D の IR・偵察、段階 E の driver・coder role・auditor 目録・`.claude/agents/`、p3_s4_loop / pipeline への検査の接続、新しい reject 理由・台帳、候補ごとの sanitizer・TRACE 計数、PIN 前進、push。
- 残存リスク:
  - 構文検査器と単独 TU compile の実装の誤り (自己試験と契約 fixture 85 本・UBSan 1 回で見たが、網羅の証明ではない)。
  - 公平性 (worker 内状態による偏り) の観測点は目視だけ。
  - verify と perf で同じ分岐を踏んだとは言えない (設計 §3.1)。
  - 上限値 (1000 µs / 50 µs / 32 周回) は試走設計値で、最適値ではない。
  - 手書き方策の throughput は 1 走の予備値。
