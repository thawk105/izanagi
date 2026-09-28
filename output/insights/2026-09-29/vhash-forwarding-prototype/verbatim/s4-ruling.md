# 段 4 裁定 + plan v2 — md_6 Cicada 選択的 forwarding 試作

- 日時: 2026-09-29 04:1x JST (date で採取した値は handoff 参照)。基準 HEAD 51f896352 (main は 539556aa1 まで進行、本 wave の対象 file の変更なし)。
- 入力: brief v2 (brief-stage1.md)、段 2 = codex/stage2r/out.md、段 3 = codex/stage3a/out.md (正しさ境界)、codex/stage3b/out.md (実効性・過剰)。
- 裁定 inbox 再走査: ba102cf75 (裁定第 39 回) のうち本 wave に効くのは「CCBench の変更は上流 CI (build・clang-format 14) を通る品質」だけ → patch の追加コードも clang-format 14 の CCBench 設定に従う。

## 所見の裁定

| # | 所見 | 判定 | 採否・理由 |
|---|---|---|---|
| S2-1 / A-1 / B-3 | make_define_request が Cicada を拒否するので gate 本体の修正が要る | **refuted** | protocol 引数は mocc の BACKOFF_FIXED 特例専用 (condition_meaning_gate.py:1122-1124)。si の登録 macro は screening_driver.py:139 が protocol 既定のまま呼び、owner TU・target は DEFINE_SPECS から取る。先例 3867e6ec5 も「protocol="si" の明示 request は拒否のまま」で登録だけ行った。gate の判定・受理述語は変えない。Cicada で実際に admitted になるかは smoke の最初の手で実測 (P10)。拒否されたら計測へ進まず段 4 へ戻る |
| A-2 | gate の緑は C/F の動作保証ではない | real | 採用。gate receipt は「compile 条件の証拠」とだけ書く。C/F の発火・F abort・再試行は計数 build の実行証拠 (attempts/success/f_aborts) で別に拘束する |
| A-3 | P2/P3 は B-3 の台帳拘束を外す | 一部 real | P2/P3 は採用 (下の賛否)。一次資料と decisions fragment に md_6 の ledger 要求との差を明記する。専用 manifest の新設は不採用 (DW-G05: 成果物の値・受理集合を変えない新しい検査) |
| A-5 / B-3 後半 | COUNT の companion と build 契約の食い違い | real | 採用。COUNT は ENABLE=1 だけを companion とし、LONGTX に依存しない設計にする (計数は thread id 別に出し、長い/通常の分類は driver が L から行う) |
| A 反例 1・2 | later_ver_ 残存・new_ver_ wts 未書換 | real | 採用 (仕様 v2 に既載)。login pytest では殺せないので変異登録はしない (DW-M01)。段 6 レビューの必須攻撃点にする |
| A 反例 3 | 前進後の INSERT/DELETE/scan | real | 採用。前進済み tx が insert/delete_record/scan を呼んだら status_=aborted (理由 `special_after_forward` を計数)。未前進なら以後その tx を対象外にする |
| B-1 | 発火の生死確認を主計測の前に | real | 採用 (DW-G01)。smoke に短い計数 run (各 workload × C/F、gc=100、K=3、extime 1) を入れ、many_ops で attempts=0 なら主計測へ進まず K=1 → skew 0.99 の順で smoke を足す |
| B-2 | 待機型の「発火しない」を待機前と区別 | real | 採用。待機型は「10 READ + 1 WRITE → 待機 → commit」。待機後に read が無いので待機中の試行は構造上 0、待機前の試行は計数で報告する |
| B-4 | F は長い thread の commit・完了率を併記 | real | 採用 |
| B-5 | gc_inter_us は GC 改善の主張にしない | real | 採用 (一次資料の「確かめていないこと」へ) |
| B-6 / A-4 | 見積りと 100 万件は未較正 | real | 採用。smoke で build 秒・初期化込み run 秒・gate 秒を測り、投入前に再積算。100 万件は Silo 較正の流用と明記 (Cicada の飽和は未確認) |
| B-7 | workload 間は node 交絡 | real | 採用。主張は各 workload 内の stock/C/F paired 比に限定。node を記録 |
| B-8 / A-6 | brief の path 誤り・test_p3_s4_loop 更新は不要 | real | 採用。test_p3_s4_loop.py は変更しない (IZANAGI_ macro を使わない) |
| B 削れる部品 | K sweep を後送、計数 JSON 縮小、独自 build 基盤不要、pytest 縮小、inert は smoke に 1 回 | real | 採用。K sweep は smoke 後に予算内なら many_ops・gc=100 だけ |

## 所有の拡張 (P8) の賛否と結論
- 賛成: patch の新 `#if` は test_ccbench_spawn_sites.py:2917 が IZANAGI_ の有無と無関係に検出し、未登録なら既存テストが赤。build sink の cross product も 2 腕を要求する。登録しないと patch を置けず依頼の実装目的を満たせない。先例 3867e6ec5 (si 2 macro) と同じ足跡。
- 反対: md_6 / common.txt は編集面を「所有」に限る。所有外の gate と期待値の編集は受理集合を広げる。md_2・md_3 と同じ file を触り land で合流が要る。
- 結論 (段 3 の 2 レンズとも賛成): **必要最小の登録を行う。** 自分の 3 macro の entry・exact witness・site 数、それに連動する登録簿テストの集合と件数・docstring の件数文、起動一覧への driver 起動箇所の登録だけ。既存 entry・判定・受理述語は変えない。件数の更新だけを緑の根拠にしない (登録の正しさは inventory テストと smoke の gate 実走で見る)。land 時に他 wave の entry と両立させ件数を数え直す。

## plan v2 (段 5 の契約)

### 仕様 v2 (spec-draft-v1.md への差分。親が spec-v2.md に確定)
1. 発火: read() 経由の read_internal だけ。read-write tx、status_ が aborted でない、scan 中でない、未前進の特殊操作なし。
   物理位置 p (latest_ が 1、pending/aborted/deleted を含む) で T.ts の可視版が p > K のとき。
2. 目標: 先頭 K 版のうち最古の committed 版 v_h (無ければ ineligible_no_hot_committed)。ts' = (clock(v_h) + (thid <= low8(v_h))) << 8 | thid、overflow なら ineligible。
3. 事前確認 (最終保証ではない): read set 全件について ts' で先頭から探索した可視版 (committed/deleted) が r.ver_ と同一か (違えば read_mismatch)。
   探索中に wts < ts' の pending に当たったら待たず conflict、nullptr も conflict。write set: RMW は latest.wts < ts' (でなければ write_constraint、latest が pending なら conflict)、
   UPDATE は ts' の可視版の rts <= ts' かつ deleted でない (でなければ write_constraint)。INSERT/DELETE を含めば ineligible。rts は書かない。
4. 成功時 (全確認後の一箇所で): wts_.ts_ = ts'、localClock_ = max(localClock_, clock(ts') + 1)、write set 全件の new_ver_->wts_ を ts' に store、
   read set と write set の全 later_ver_ を nullptr。ThreadWtsArray/ThreadRtsArray・clockBoost_ は変えない。その後 ts' で先頭から stock と同じ探索をやり直す。
5. 失敗時: 何も変えず元の ts で stock 探索を続ける。
6. F: 発火条件 1 が立ったら status_=aborted にして read から戻る (runner/YCSB が abort() → 同じ procedure を新しい begin() で再試行)。
7. 前進済み tx が insert/delete_record/scan を呼んだら status_=aborted (special_after_forward)。
8. validation 以降は一切変えない。最終保証は stock validation を最終 ts で走らせること。静的論証であり実測の正しさ保証ではない (「未検証の診断値」)。

### 単位 A: patches/cicada-forwarding-variant.patch (Codex author)
- macro 3 つ: `CICADA_FWD_ENABLE` (owner cc/cicada/transaction.cc)、`CICADA_FWD_COUNT` (owner cc/cicada/transaction.cc、ENABLE=1 のときだけ意味を持つ)、
  `CICADA_LONGTX` (owner cc/cicada/ycsb_cicada.cc)。未定義 = 0。新 macro の `#if` は owner TU の .cc にだけ置く (include/*.hh に置かない)。
- 実行時 flag (gflags、該当 macro 有効時だけ DEFINE): ENABLE: `--cicada_fwd_policy=c|f` (既定 c)、`--cicada_fwd_k` (既定 3、0 と 256 超は起動時拒否)。
  LONGTX: `--cicada_long_threads` (既定 0)、`--cicada_long_kind=many_ops|wait_after_reads`、`--cicada_long_ops` (既定 1000)、`--cicada_long_rratio` (既定 90)、
  `--cicada_long_wait_us` (既定 1000)、`--cicada_wait_reads` (既定 10)。
- 計数 (COUNT): transaction.cc の file scope に thread id 添字の cache-line 整列 slot 配列。worker は自 slot に plain 加算。process 正常終了時に file-scope static の destructor で
  `CICADA_FWD_V1 {json}` を 1 行出す。項目: schema, policy, k, threads[]: {thid, triggers, attempts, success, read_mismatch, write_constraint, conflict, ineligible,
  special_after_forward, f_aborts, advance_clock_sum, pos_before_sum, pos_after_sum}。smoke で出力を確認し、出ない場合は driver 側の読み取り方を変えずに patch を直す。
- LONGTX: ycsb_cicada.cc に Cicada 専用 workload 型 (YcsbWorkload の makeDB・表示・通常 procedure に委譲)。末尾 L thread (thid >= thread_num - L、thid 0 は除外) が長い tx。
  many_ops: 1000 ops、90% READ、少なくとも 1 WRITE。wait_after_reads: 10 READ + 1 WRITE の後 wait_us 待って commit (待機後に read しない)。
  process 正常終了時に `CICADA_LONGTX_V1 {json}` を 1 行: threads[]: {thid, long, commits, aborts}。L=0 のとき procedure 生成は YcsbWorkload と同一。
- 既定 (3 macro 未定義) で transaction.cc と ycsb_cicada.cc の前処理結果が pin と同一 (行 marker 除く)。include/ycsb.hh・common/runner.hh・header は不変。
- 追加コードは external/ccbench/.clang-format (clang-format 14) に従う。
- 規模上限: patch の追加行 700 行以内。

### 単位 B (Codex author、単位 A の後)
- orchestrator/campaign/vhash_forwarding_prototype.py: CLI `smoke` / `run --workload normal|many_ops|wait_after_reads [--k-sweep]` / `aggregate`。
  patchharness.checkout/applied、build は 3 種: stock = (ENABLE=0,COUNT=0,LONGTX=1)、fwd = (1,0,1)、count = (1,1,1)、`-DCMAKE_CXX_FLAGS=-D...`、target ycsb_cicada.exe。
  build の前に供給する各 macro について silo_policy_coverage.py:308-360 と同形で gate 2 腕 → require_condition_gate_family、拒否なら build しない。
  smoke: gate → inert 前処理比較 (transaction.cc / ycsb_cicada.cc、pin vs patch 既定) → 3 build → 各 workload × {C,F} の count run (extime 1、gc=100、K=3) → 各 workload × 3 arm の perf run 1 本、全所要を記録。
  run: gc {10,100,1000} × perf 3 rep (順序 stock,C,F → C,F,stock → F,stock,C) + count C/F 1 rep。pgrep -af 'ycsb_.*\.exe' を job 冒頭と各 run 直前、検出・失敗で停止。
  条件: 48 thread、ycsb_tuple_num 1000000、zipf 0.9、rratio 50、max_ope 10、extime 3、clocks_per_us 2100、numactl --interleave=all、長い thread L=4。
  JSON (output/env/pegasus/vhash-forwarding-prototype/): schema_version, git_head, ccbench_pin, patch_sha256, binary_sha256, build_kind, perf_eligible (count は false),
  verification_status "未検証の診断値", workload, gc_inter_us, k, policy, rep, order_index, argv, hostname, started/ended, returncode, stdout/stderr sha256 と本文,
  throughput, fwd_counters, longtx_counters, gate_receipts (compile 条件の証拠), inert_receipt, competing_probe。
- 起動箇所を test_ccbench_spawn_sites.py の起動一覧に登録。gate 登録: condition_meaning_gate.py の DEFINE_SPECS 3 entry (ROUTE_CMAKE_CXX_FLAGS、target ycsb_cicada.exe、
  patch_rel patches/cicada-forwarding-variant.patch、COUNT は companion (("CICADA_FWD_ENABLE","1"),)、inert_values ("0",))、exact witness 行と実 site 数、
  test_condition_meaning_gate.py / test_ccbench_spawn_sites.py の登録簿・件数・docstring 件数文の追随。既存 entry と判定は変えない。
- orchestrator/tests/test_vhash_forwarding_prototype.py (login、build・計測なし): test_order_rotation、test_count_throughput_is_ineligible、test_counter_line_exactly_once、
  test_gate_rejection_stops_build、test_figure_full_shape (FIGURE_CONVENTIONS の保存前検査を実寸 fixture で)。
- output/insights/2026-09-29/vhash-forwarding-prototype/make_figures.py: raw JSON → 図 (C 成功率・失敗理由内訳・stock/C/F throughput 比・長い thread の commit/F abort) + provenance JSON。
- 規模上限: driver 700 行、test 300 行、作図 300 行 (登録簿の追随は除く)。

## 変異の事前登録 (DW-M01)
| id | 位置・内容 | 期待 KILLED node (完全集合は login self-run で確定) |
|---|---|---|
| M1 | driver の rep 順を常に stock,C,F に固定 | test_vhash_forwarding_prototype.py::test_order_rotation |
| M2 | count build の perf_eligible を true | ::test_count_throughput_is_ineligible |
| M3 | CICADA_FWD_V1 行の重複を後勝ちで受理 | ::test_counter_line_exactly_once |
| M4 | gate 拒否後も build 関数を呼ぶ | ::test_gate_rejection_stops_build |
| M5 | DEFINE_SPECS から CICADA_FWD_COUNT entry を削除 | test_ccbench_spawn_sites.py::test_patch_define_inventory_matches_condition_gate_registry ほか (self-run で確定) |
- C++ の論理変異 (later_ver_ 破棄削除、new_ver_ wts 書換削除、pending を読み飛ばし、F の abort 削除) は login pytest で殺せず、単一理由の実効 gate が無いので登録しない。
  代わりに段 6 レビューの必須攻撃点とし、smoke の計数 (F abort > 0、success > 0 で書込み tx を含む) を観測として記録する。検出は md_3 の検査器待ち (限界として一次資料へ)。

## 計算予算
- smoke 1 job (walltime 00:30:00) → 実測で再積算 → 本計測 3 job (workload 別、walltime は実測から、上限 00:40:00)。合計 2 node 時間未満を投入前に確認。超える見込みなら K sweep → gc=1000 の count の順に削る。

## erratum 1 (2026-09-29 08:0x JST、段 6)
- 規模上限の改訂: orchestrator/tests/test_vhash_forwarding_prototype.py の上限を 300 → 350 行にする。
  理由: 段 6 の所見 (A1/A2/A4/B1/B3/B4、焦点再レビュー 2 件) と計算ノードの実機 blocker 4 件 (compile entry 4 件、config.h 未生成、duplicate define、空 job の検査順) の
  回帰テストを足した結果 322 行になった。各テストは実機で起きた不具合か real 所見に 1 対 1 で対応し、削ると回帰を検出できない。driver 700 行の上限は不変 (現 581 行)。

## 段 6 焦点再レビュー 2 (codex/stage6d) の裁定 (2026-09-29 08:2x JST、date 確認前の推定を訂正)
- fix4〜fix9: closed (静的照合 + 計算ノード smoke7 all_pass + 登録関連テスト 401 passed)。
- 新所見「aggregate が workload の欠落を受理する」: real。ただし親が aggregate を完走した run job 3 本 (normal / many_ops / wait_after_reads) の raw を明示して呼び、
  入力 file と sha256 を一次資料に記録する手順で防ぐ。コードは直さない (研究優先・防御的堅牢化は既定で見送り、DW-O16 の fix 巡を重ねない)。
