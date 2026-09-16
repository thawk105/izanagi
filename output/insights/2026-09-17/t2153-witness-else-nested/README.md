# [T-2153] 意味 witness を (a) 型 (`#else` + 入れ子) の 2 macro へ広げ、S2 検証較正へ配線した

- 日付: 2026-09-17
- branch: `worktree-dev-wave-t2153-witness-else-nested` (base = local main `1042a1bc9`)
- 実装 commit: `fa353d8cbc9fd55ce8b03b95980d6d449ae9fa6b` (Codex `role=author` 1 本 + fix 1 本、統合は親)
- 対象: `orchestrator/campaign/condition_meaning_gate.py` の compile-time 枝選択 witness (D1490) 登録簿、
  `orchestrator/campaign/s2_verify_calibration.py` の condition gate 配線
- 前 wave: `output/insights/2026-09-02/t2153-meaning-witness/README.md` (entry 1195)

## 何が変わったか

枝選択 witness の登録簿へ、`#else` を持ち内側に `#if ADD_ANALYSIS` の入れ子がある positive control 2 macro を足した。
機構 (probe の挿入形、一意性・非識別・完了 marker の検査、factory の要求 1 / 既定 0 条件、`DEFINE_SPECS`、
旧 `MeaningWitnessDeclaration` / CLI の `--meaning-case` 経路) は 1 行も変えていない。

- `IZANAGI_BREAK_NOREAD_VALIDATION` (`patches/broken-silo-norw-validation.patch`、所有 TU `cc/silo/transaction.cc`)
- `IZANAGI_BREAK_HIGHKEY_VALIDATION` (`patches/broken-silo-highkey-validation.patch`、同)

配線先は両 macro を要求する唯一の専用 driver `s2_verify_calibration._require_condition_gate` (D1492)。
CLI (`condition_meaning_gate` の `--macro` は供給 domain 全体、cases 未指定なら factory 自動) は既配線で追随する。
`screening_driver` は裸 `-D` 不在の route 不一致 (`screening-build-route-mismatch`) で admission 前に拒否され、不変。

件数: 意味 witness 対応集合 **13 → 15** (枝選択 12 → 14 + `BACKOFF_FIXED`)、供給 domain 38 のうち未対応 **25 → 23**。
entry 1195 が「動かせなかった 13 件」と記した集合のうち、現在未対応は 12 件 (`BACKOFF_NOINLINE` は D1569 / D1613 で確立済み)
→ 本 wave 後 **10 件**。

## なぜ (a) 型だけか — (b)(c) は既存機構で届かない (toy 実測 + 実 patch の静的対応付け)

依頼は「既存機構で届く (a)(b)(c) から取る」。段 1 で機構の制約を現物で確かめ、repo 外の使い捨て script
(実 compiler、実 patch の前処理構造を模した toy TU) で裏を取った。

| 型 | macro | 既存機構での結果 | 根拠 |
|---|---|---|---|
| (a) `#else` + 入れ子 | NOREAD、HIGHKEY | **green** (要求 1 → (1,1)、既定 0 → (0,1)) | probe は宣言指令の直前に自己完結の `#if M / SELECTED / #endif / COMPLETED` 塊を挿入するので、元の枝の `#else` と入れ子は marker の選択条件に入らない (所有 TU の前処理が成功する場合) |
| (b) 別条件の内側 | `IZANAGI_BREAK_TRIGGER_MISATTR` | **red** `not-discriminating` | `#ifdef` は対照 `-D=0` でも定義済み。toy 実測: 最上位で (1,1)/(1,1)、`#if BACKOFF_TRIGGER_GATING` の内側 (既定 0) で (0,0)/(0,0)。実 patch では更に外側に `#if NO_WAIT_LOCKING_IN_VALIDATION` がある |
| (c) 複数箇所 | `IZANAGI_SILO_LADDER_RUNG1` ×2、`BACKOFF_REQUESTED_US` ×2 (header 側の 2 回は別 file)、`BACKOFF_TRIGGER_GATING` ×12 | **red** `start-not-unique` | 所有 TU 内の完全一致 (改行だけを除く) の件数。toy で同一逐語 ×2 の red を実測 |

(b)(c) の「red」は toy 実測と実 patch の静的対応付けであり、4 件の実 patch を実 compiler に通した結果ではない。
機構変更 (`#ifdef` の定義 / 未定義観測、複数箇所の代表選択) は本 wave の scope 外で、提案もしていない。

生死実験の script と出力 (親が書いた使い捨て、repo には入れない):
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-else-nested/liveness_a_type.py` (sha256 `1235ba9f7eb80509…`、5556 bytes)、
  同 `.out` (sha256 `ba52063e39d24ca9…`)
- `probe_m11_s2.py` (sha256 `17efead551ea4719…`、2970 bytes)、`.with.out` (`af6392d6d0f2eb28…`) / `.without.out` (`dac15f3d068ca1fd…`)

## 主張の境界 (正直に書く)

- witness が確立するのは D1490 のまま: 「所有 TU において、その define の値が宣言した枝の選択を決めている」。
  **所有 TU の前処理が成功する場合**に限る。動的到達性、positive control が期待する異常の実行時発火、枝本文の内容は主張しない。
- 単体 test の正例は **実 patch の前処理構造を模した toy TU** (`ADD_ANALYSIS` 未定義の fixture) + 実 compiler で、
  実 supply + 実 meaning + 実 family を通し `admitted is True` かつ `unestablished_meaning_macros == ()` を確認した。
  **実 patch 適用後の CCBench TU (masstree `config.h` 依存) と実機 S2 走行は未検証。**
- S2 が現行 condition gate 下で実機で走った記録は無い (最終走行 2026-07-06、`condition_gates` を持たない JSON)。
  S2 は依存供給先 (`FETCHCONTENT_BASE_DIR` 等) を gate へ渡さないので、実機では supply / meaning とも masstree
  `config.h` 欠落で前処理 red になりうる (D2059 と同型)。縮小を観測できる場所は
  `output/env/linux-baremetal/calibration/s2_verify_<…>.json → condition_gates[i].admission.unestablished_meaning_macros`。
  supply が同じ configure 引数で通っても、meaning は別の一時 build root で前処理するため、header 可用性は自動には保証されない。
- 受理集合: meaning arm 単独では狭まる向きだけ (unestablished(admit) → green(admit) か red(reject))。
  family 全体では、registry 会員になったことで supply 側の実行形が共有 build root 分岐 (既存 8+3 の CXX_FLAGS macro と同形) へ移る。
  S2 の supply 呼出しと configure 引数は不変。共有 root の cache 残留で supply の観測が変わる入力は本 wave では確認していない。
- S2 の `_broken_build_and_verify` 内の再検査 (S2:309) でも meaning arm が走るようになった (preflight と合わせ configure は
  patch あたり 4 → 8 回)。実機の所要増分は未計測。

## 段ごとの所見 (要点)

- **段 2 plan が brief の漏れ 2 点を補正した。** 既存 test `test_compile_time_factory_keeps_unregistered_macro_unestablished`
  が NOREAD を「未登録 macro」として使っていた (TRIGGER_MISATTR へ差し替え)。registry 追加が supply の共有 root 分岐に効く。
- **段 3 の 2 レンズ**: 一意性 (stock 0 件 + S2 の個別 `applied` + `assert_pinned_clean`) と生死実験の形は refuted で閉じた。
  `source_rel` 変異は test helper の assert が factory より先に赤を出すため登録から外し (DW-M01)、S2 配線変異の主 killer を
  新 consumer test (実 factory を spy で包み、evaluator へ渡る request / declaration の `is` 同一性まで検査) に置いた。
  CLI の自動追随と screening の拒否理由 (route 不一致) を brief に訂正した。
- **段 6 の 2 レビューは must-fix 0 だったが、親の consumer 回帰 (9 file、688 passed) が real 赤を 1 件出した**:
  `test_build_site_gate.py::test_m11_coverage_configure_gates_are_independent` — S2 の `_broken_build_and_verify` は site gate より前に
  condition gate を呼ぶため、配線後は meaning arm の configure (一時 dir prefix `izanagi_compile_time_branch_`) が test の
  `subprocess.run` 代役に落ち `AttributeError` になった。fix は代役の素通し集合に prefix を足す 1 行 (production は不変)。
  repo 外 probe で fix 無し = 再現、fix 有り = 期待の `BuildError` + 非素通し call 0 件を実測してから fix 子へ渡した。
  レビュー 2 本が取り逃したのは consumer 回帰の完了前に投入したためで、回帰 log を段 6 の射影に含める順序が正しい。
- 焦点走 (計算ノード): f1 = TG 124 + T5 12 = 136 passed、f2 = consumer 9 file 688 passed / 1 failed (上記)、
  f3 (fix 後) = TG + T5 + build_site_gate = 159 passed。

## 変異による裏取り

`mutation-spec-final.json` / `mutation-final-report.json` が正本 (container worktree、統合 commit `fa353d8cb`、runner =
`run_tests.py test_condition_meaning_gate.py test_s5_permutation_coverage.py --force-dispatch`)。
**baseline PASSED、負例 7/7 KILLED (期待 node と観測 node が完全一致)、等価変異 M0 SURVIVED、MISMATCH 0。**

| 変異 | 対象 | 結果 | 検出 node 数 | 被覆の由来 |
|---|---|---|---|---|
| M0 | registry 直前に comment 1 行 (等価) | SURVIVED | 0 | 対照 |
| M1 | NOREAD entry の指令逐語 | KILLED | 5 (registry 束縛、accepts_each、新正例、S2 consumer ×2) | 既存 test の対象拡張 + 新規 |
| M2 | HIGHKEY entry の指令逐語 | KILLED | 5 (同型) | 同上 |
| M3 | S2 配線を `declaration=None` へ戻す | KILLED | 5 (S2 consumer ×4、source 検査) | 本 wave の新規 |
| M4 | `MEANING_SUPPORTED_MACROS` から 2 新 macro を除外 | KILLED | 5 (domain 境界、accepts_each ×2、新正例 ×2 — green record の `admission-contract-invalid`) | 新規 + 既存 |
| M5 | 一意性 `!= 1` → `< 1` | KILLED | 1 (`rejects_duplicate_start_directive`) | 既存被覆 |
| M6 | factory `requested != "1"` → `not in {"0","1"}` | KILLED | 1 (`factory_rejects_nonpaired_values[0-0]`) | 既存被覆 |
| M7 | 非識別検査の除去 | KILLED | 5 (`rejects_non_discriminating_observation`、非指令本文 ×2、`owner_prefix_undef`、`line_spliced_comment_endif`) | 既存被覆。reason 契約の検出であり誤受理防止の独立層ではない (1195 insight を継承) |

probe 段 (`mutation-spec-probe.json` / `mutation-probe-report.json`) は全件 SURVIVED 期待で登録し、観測 node を集めてから
本走を登録した。`source_rel` 変異は test helper (`_compile_time_source_root` の `assert macro == "BACKOFF_NOINLINE"`) が
factory より先に赤を出し単一理由性が無いため登録していない。M1 / M2 の新正例での検出は前処理前の逐語 assert
(`declaration.start_directive == f"#if {macro}"`) によるもので、compiler による検出は `accepts_each_registry_macro` 側。

## 段ごとの一次資料

`verbatim/` に段 1 の brief、段 2 の plan、段 3 の 2 レンズ、段 4 (+ 段 6) の親裁定、段 5 の実装子報告、段 6 の 2 レビューと
fix の報告を逐語で置く。prompt・焦点走 log・生死実験・probe・変異の attempt 台帳は job dir
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-else-nested/` に保全した。
