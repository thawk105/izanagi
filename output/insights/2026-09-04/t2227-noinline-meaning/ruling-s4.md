# 段 4 裁定 — [T-2227] plan v2 と変異事前登録

裁定日: 2026-09-04。入力: brief.md、s2-plan.md、s3-sol.md (8 所見)、s3-luna.md (9 所見)。
裁定 inbox の再走査: worklog carry [T-2227] は entry 1227 の文言から変わらず (1245 まで「(番号)」持ち越し)。

## 所見の裁定 (real / refuted、採否、scope)

| # | 所見 | 性質 | 裁定 |
|---|---|---|---|
| sol-1 / luna-3 | `ConditionalBranchMeaningDeclaration` は registry と同じ値なら factory 外から直接構築できる。D1491 の「factory 以外から発行できない」は object 発行元でなく値の registry 束縛で実装されている | real (観測) | **scope 外・実装しない。** T-2153 が採った既存設計で、evaluator は factory の再導出と等値比較で受理する。直接構築が受理される条件は factory が同じ宣言を出す条件と一致し、受理集合は factory 条件より 1 bit も広がらない。発行元の識別 (capability) は仮想リスク向けの新防壁であり、依頼が scope 外と明示した型。insight に「実装しなかった所見」として残す |
| sol-2 | 登録簿へ `BACKOFF_NOINLINE` を足すと供給の節 `:1758-1766` の `shared_branch_build` が cache route の同 macro (要求 1・既定 0) で `compile-command-unavailable` を出す | real | **採用 (必須)。** 登録の副作用で正当な要求 1 が供給で赤になるのは承認外の過剰拒否。`shared_branch_build` を `request.route == ROUTE_CMAKE_CXX_FLAGS` の場合に限り、cache route の登録 macro は従来の別 build root (`default`) 経路を使う。既存 8 macro (全て CXX_FLAGS) の経路は不変。要求 1 の供給・意味・admission が通る正例を登録する (DW-M01「過剰拒否の正例」) |
| sol-3 / luna-4 | D1492 は promotion 限定でない。t1683 probe は `BACKOFF_NOINLINE` を要求し admission を出力 JSON `condition_gates` に保存する。backoff_sweep / silo_ladder は `BACKOFF_FIXED` 系しか要求せず、screening は admission を捨てる | real | **採用。** 配線先 = A-2、s1、t1683。配線しない driver は「要求しない」(backoff_sweep、backoff_repro、silo_ladder_rung1、a1_paired) と「admission が成果物へ載らない」(screening_driver、backoff_profile) で記録する。brief の (P3) の raw/promotion 境界は撤回する |
| sol-4 / luna-5 | 依存 file (`-MD`) で計装 header の実読を要求する検査と新 reason_code・負例 | sol: refuted (P1 で十分)、luna: real (本題外) | **luna を採る。削る。** 計装 header が読まれなければ marker は 1 つも出ず両観測 (0,0) で既存の `compile-time-branch-selection-not-discriminating` が赤にする。読まれずに (1,1)/(0,1) を作るには CCBench 側の source に marker 出力を書く必要があり、これは既存 8 macro でも防いでいない同じ仮想リスク。依頼が scope 外と明示した「仮想リスク向けの検査」に当たる |
| sol-5 / luna-2 | 既存 8 macro の受理が広がる / 「集合へ追加するだけ」に当たる | refuted | 採用条件を維持: factory の inert 拡張は `BACKOFF_NOINLINE` 限定、既存 8 macro は要求 1・既定 0 固定、`MEANING_SUPPORTED_MACROS` は直接編集しない |
| sol-6 | evidence bytes は plan どおり不変 (15 field、sort_keys) | refuted | 維持: dataclass の field を足さない・既定値を変えない |
| sol-7 | 深い鏡像は dir symlink を追うと循環・root 外走査で hang しうる。走査失敗が `ConditionMeaningGateError` に畳まれないと structured red にならない | real | **採用 (実装条件)。** 深い鏡像は `os.walk(followlinks=False)` 相当で、source 内の dir symlink は symlink のまま置く (中へ降りない)。走査・作成の `OSError` / `RuntimeError` は `compile-time-branch-instrumentation-failed` に畳む。実木は 1438 file / 267 dir (`third_party/shirakami` 込み) で走査は秒未満 |
| sol-8 / luna-7 | toy は実 TU (2 段 include、Masstree `config.h`、`-I` 群、`-ffile-prefix-map`) を含意しない | real | **採用。** 段 6 で親が実 patch 木 (A-2 と同じ `patchharness.checkout` + `applied` + `prepare_masstree_fetchcontent`) で要求 0/既定 0 の意味 arm を計算ノードで実走する (probe は job dir に置き `run_tests.py --force-dispatch <絶対 path>`)。green でなければ段 6 fix |
| luna-1 | (P2) 対照値方式は D1490 の値契約 (要求値で (1,1)・既定値で (0,1)) の書き換えであり、裁定が要る | real | **AI 決定として記録し実装する。** 根拠: (a) D1490 は AI 決定 (ユーザー裁定でない) で、AI が補遺できる層。(b) D1569 (ユーザー裁定) は「D1490 の枝選択 witness を factory から発行し、未確立一覧が実際に縮む driver に配線」を命じ、A-2 の要求は 0/0 なので対照値なしでは D1569 を満たす実装が存在しない。(c) witness の主張範囲「所有 TU でその define の値が枝の選択を決めている」は不変で、観測する値の集合 {0,1} も不変。変わるのは「どちらの値を要求したか」の制約だけ。(d) 受理集合は狭まるだけ (unestablished → green/red)。(e) D1242 が却下したスカラー復号器の流用ではない。**ユーザーが覆す場合の revert 点は factory の 1 条件 (`requested in {"0","1"}` → `requested == "1"`) で、他は不変。** 最終報告で明示する |
| luna-6 | A-2 の admission は供給の節 (D1523、別 wave) が赤の間 False のまま。効果は D1523 取り込み後の fresh run で現れる | real | 採用 (記録)。本 wave の直接効果は「A-2 / s1 / t1683 の `BACKOFF_NOINLINE` meaning record が undeclared から green/red へ置換される」まで |
| luna-8 | configure 回数: condition suite +8〜10 回、+1〜2 秒 | real | 採用。validator の負例は逆順 green の受理と値束縛の最小負例だけに絞る |
| luna-9 | 既受理成果物「空集合」は repo `output/` 内に限定する | real | 採用。記録は「repo `output/` 内は空集合、repo 外の保存先 (A-2 attempt root、s1 output_root、t1683 `--out`) は未走査」と書く。migration 不要も repo 内限定 |
| luna-7 (fixture) | fixture 3 行追加は既存 test を壊さない | refuted | 維持 |

## plan v2 (s2-plan からの差分だけ)

1. **削る:** 依存 file の実読検査、reason_code `compile-time-branch-instrumented-source-unobserved`、その負例・変異項目。
2. **足す:** 供給の節 `shared_branch_build` を CXX_FLAGS route に限る修正と、`BACKOFF_NOINLINE=1` (要求 1・既定 0) の供給 green + 意味 green + admission の正例 test (fixture 木)。
3. **足す:** t1683 probe の配線 (`_condition_requests_by_genome` の `declaration = None` を factory 呼び出しに、`BACKOFF_FIXED` の legacy 宣言はそのまま上書き) と test (`test_pegasus_calibration_workload.py` の `_load_cost_probe()` で module を読み、合成 workload dict で `_condition_requests_by_genome` を呼び、`BACKOFF_NOINLINE` の宣言が `ConditionalBranchMeaningDeclaration` で factory 返値と等しいこと、`BACKOFF_FIXED=-1` は legacy のままであることを assert。compiler 不要)。
4. **実装条件:** 深い鏡像は dir symlink を追わない・`.git` は symlink のまま・走査失敗は `compile-time-branch-instrumentation-failed`。既存 8 macro (`source_rel == request.owner_tu`) は現行 shadow と compile operand 差し替えを逐語維持。
5. **evidence slot:** `requested` = 要求値での観測、`default` = 既定値または対照値での観測 (inert 要求では define_value `"1"`)。docstring に明記。field 追加なし。validator は `BACKOFF_NOINLINE` に限り (要求 0 → selected 0、対照 1 → selected 1) も受理し、既存 8 macro は 1/0 固定のまま。`compiler_identities` の phase 名は不変。
6. **配線しない driver の記録** (insight README): backoff_sweep / backoff_repro / silo_ladder_rung1 / a1_paired = 要求しない、screening_driver = admission を捨てる、backoff_profile = 関門を呼ばない。
7. **記録:** decisions fragment 1 件 (D1490 補遺: inert 要求の対照値観測)、worklog fragment 1 件、insight README (既受理成果物の走査結果、配線表、実装しなかった所見 sol-1 / sol-4)。

## 変異事前登録 (probe で観測 node を集めてから本走で確定)

全て `orchestrator/campaign/condition_meaning_gate.py` または配線 driver への単一置換。category は negative、期待 KILLED。E1 のみ SURVIVED 期待の等価変異。

| id | 位置 (anchor は実装後に逐語で確定) | 期待して殺す test |
|---|---|---|
| M1 | factory: `BACKOFF_NOINLINE` の inert 分岐を外し要求 1 だけ宣言 | inert 正例 (要求 0・既定 0 が green)、factory 範囲 test |
| M2 | 対照値の導出を `"1"` から要求値へ (両観測が同値) | inert 正例 (非識別で red になる) |
| M3 | header 所有時の深い鏡像を旧 shadow (祖先 symlink) へ戻す | inert 正例・要求 1 正例 (marker 0 で red) |
| M4 | compile operand の差し替え先を shadow owner TU から計装 header へ戻す | inert 正例・要求 1 正例 |
| M5 | 供給の節 `shared_branch_build` の route 条件を外す | 要求 1 の供給正例 (`compile-command-unavailable` で red = 過剰拒否) |
| M6 | validator: `BACKOFF_NOINLINE` の逆順 (0/1) 受理を外す | inert 正例の `_validate_arm_record_integrity` |
| M7 | A-2 `declaration` の factory 初期化を `None` へ | A-2 test (factory 呼び出しと undeclared message 不在) |
| M8 | s1 の factory fallback を外す | s1 test |
| M9 | t1683 の factory 呼び出しを外す | t1683 test |
| M10 | factory の inert 拡張を既存 8 macro へ広げる | `test_compile_time_factory_rejects_nonpaired_values` (過剰受理の負例) |
| E1 | 等価変異 (生成 argv 不変の書き換え) | SURVIVED 期待 (harness の正例) |

単一理由性 (DW-M01) は実装後に anchor と赤 node で確認し、複数層で赤になるものは冗長 gate と明記する。
hang_risk の変異は登録しない。

## gate の禁止と正例 (DW-S04)

- 禁止 (署名): `evaluate_define_runtime_meaning(captured, request=<BACKOFF_NOINLINE, requested 0, default 0>, declaration=<factory 返値>)` が、計装 header 経由の観測で 値 0 → (0,1) かつ 値 1 → (1,1) でないとき、`terminal_status="red"` を返す。
- 通る正例: fixture `supplied` (3 行追加後) に対する同 request が `green` / `declared-compile-time-branch-selection-observed`。

## 規模上限

production 3 file (`condition_meaning_gate.py`、`paper_story_a2_certification.py`、`s1_direct_comparison.py`) + probe 1 file (`t1683_rr5_cost_probe.py`) + fixture 1 file + test 4 file。これを超える編集面は差し戻す。
