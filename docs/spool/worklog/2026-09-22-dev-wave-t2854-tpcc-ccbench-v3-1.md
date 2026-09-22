---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-22
wave: dev-wave-t2854-tpcc-ccbench-v3
seq: 1
title: [T-2854] TPC-C 段 1 の CCBench 側 (単位 1・2) を CCBench の local branch izanagi-tpcc-v3-trace に現 pin e9e477ca の子 2 commit (C1 56b5cb70 = trace.hh の v3 helper と tpcc.hh の取引種別 context・trace build 限定の計数、C2 a6f2c741 = silo の v3 emitter) として載せ、計算ノード 1 走で v3 の構造・witness・内容、YCSB v2 の certified、TRACE=0 の前処理と逆アセンブルの一致、変異 6 件を確かめた (insight + docs、push と pin 前進なし、branch worktree-dev-wave-t2854-tpcc-ccbench-v3)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = insight `verbatim/request.md`): 設計 insight §7.1 の単位 1・2 を Codex author で CCBench の izanagi-trace 系統に実装し、現 pin の上で内部の受入まで進める。mocc (単位 3)・superproject 側 (単位 4・5)・pin 前進 (単位 11)・push は対象外、gate・検査・台帳の追加も scope 外。記録 = `output/insights/2026-09-22/t2854-tpcc-ccbench-v3/README.md`。設計判断は {{D:tpcc-v3-producer-silo}}。
- 候補 commit: C1 = `56b5cb709628c9cac98e4e18ff676defc77a9117` (include/trace.hh・include/tpcc.hh)、C2 = `a6f2c7410d58ad140a62b11cc1beab29bfcd191b` (cc/silo/transaction.cc)、親 = pin e9e477ca、branch `izanagi-tpcc-v3-trace` は wave 木の submodule 保管庫にあり、自己完結 bundle を job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/C.bundle` に保全した。gitlink と承認定数は e9e477ca のまま。主 checkout の submodule 保管庫への fetch は land 後に行う (結果は後続の記録)。GitHub への push は人間手番 (D16)。
- **並走:** 同じ T-2854 の単位 4 (verifier 側) を別 wave が同時に進めた (依頼時点で担当分割済み、譲り合いの対象ではないと判断)。v3 frame の形 (C 10 token、R / W / X に表、I 行は出さない) を相互連絡で一致させた。worklog の [T-2854] 項目は、後に land する側が両成果を統合して `更新` に置く取り決めで、単位 4 (entry 1828、D2224) が先に land したので本 fragment が統合した (単位 4 の依頼した残件 2 点を含む)。単位 4 側の申告: v3 の run は設計 §3.3 の存在履歴の検査が未実装の間 certified にしない。
- 計算投入: 2 本、Elapse 計 208 秒 (約 0.06 node 時間) で、D2212 項 4・D2219 項 1 の確認ライン (2 node 時間) 未満のため確認なしで投入した。1 本目 (18068.nqsv、17 秒) は probe が source を `git archive` で取り出し、CCBench の `.gitattributes` の `oze* export-ignore` で cc/oze が抜けて CMake configure が失敗した。probe を直し (取り出し後に tree と file 集合・blob を完全一致で照合)、2 本目 (18131.nqsv、191 秒、bnode146) で C0〜C6 の全段合格。
- 結果の要点: TPC-C は C 36,156 = commit 数 36,156 (NewOrder 19,751 / Payment 16,405、X = P = 0) で `structure+witness+content pass` (certified ではない)。YCSB は v2 のまま現行 verifier が certified (294,331 取引)。TRACE=0 は 12 source / 21 entry の前処理 (完全展開と include 活性) と tpcc_silo / ycsb_silo の正規化逆アセンブルが pin と一致、TRACE=1 は 21 entry が `-Werror` 付き構文検査に合格。変異 D1 PASS・M1〜M5 KILLED (M2 は D1 の上で C 1,950 > commit 数 1,948)。trace 量の実測は約 1,024 byte / 取引 (設計の試算 1.37 GB / 100 万取引を、この 1 走の条件で約 1.02 GB に置き換える)。
- 素材: trace build の計数修正の境界 (commit 成功直後の quit) は通常の短時間走では踏む保証が無く、commit 直後に自分で quit を立てる診断変種 (D1) と旧順序への変異 (M2) で初めて決定的に示せた。
- D297 の検査器は header の差分を拒否するので、本候補は D297 の合格を名乗らず、pin 前進 (単位 11) の前に header 差分の受理方法を決める必要がある (insight §8)。
- D2219 項 7 (§9 の実行再現): 段 1 で観測できたのは実行時の OrderLine 番号が 0 始まり (19,751 注文すべて) であることだけ。他の所見は段 1 の取引では踏まない、または si を走らせていないので未検証。見送り台帳 [T-156] の発火条件 (TPC-C 級 corpus の採用) は、pipeline の allowlist がまだ YCSB だけなので本 wave では成立していない。
- 段 3 相談 2 本の must-fix 3 件 (trace.hh の追記位置が既存関数の内側、変異免除の誤り、commit 直後の quit 境界の決定的確認) を採用。D297 の既知拒否の実走と既存 patch 17 本の apply 検査は必要性が示せず外した。段 6 レビュー 2 本は C++ への攻撃不成立、probe の must-fix 2 件 → fix 1 → 焦点再レビュー 1 は NO-GO (fix 1 が R 行 0 件の検査まで消した回帰) → fix 2 → 焦点再レビュー 2 で GO。witness parser の二重実装 (nit) は不採用。
- 異常: 着手 (2026-09-22 08:47 JST) の worktree 作成後に session が約 11 時間止まり、19:4x に再開した (開始 gate は再開後 19:50 に local main eef04f5a7 で rc=0)。段 5 の author B は `run_probe.py` の後半を shell の heredoc で追記しようとして hook に拒否され、迂回せず停止した (継続子が編集 tool で完成)。
- **受入 attempt 1 (tested main `ec2c1488a`、tip `e5ecf19c2`、21:43〜21:52 JST) は赤 7 件で rc=70、非帰属と判定した。** 赤はすべて `orchestrator/tests/test_dev_wave_cleanup.py` の remove-child 系 7 node で、占有検査が `occupancy result is indeterminate or inconsistent ... {"error":"missing","source":"cwd",...}` で落ちた (走査中に別 process が消える一過性の競合、entry 1803・1809 と同じ機序)。本 wave の superproject 差分は insight と spool fragment だけで、この試験から到達しない。同じ tip で 7 node を単独再走した (18191.nqsv、Elapse 12 秒): 7 passed で再現しない。hold 登録簿へは登録しない。単位 4 の land (main `bc3b23953`) を取り込み (merge `1e75292d0`)、[T-2854] の統合を足した tip で受入を取り直す。
- 工数: Codex 子 13 本 (plan 1・consult 2・author 3・review 2・fix 3・focus 2、全て gpt-6-astra / medium)、model call 計 188、wall 合計 4,334 秒。計算ノード: probe 2 job (208 秒)、受入 1 回、単独再走 1 job (12 秒)。受入の取り直しと land の結果は本 entry に書けない (記録 commit の後に走る)。

## 次の一手差分

### 更新

- [T-2854] **P1・段 1 の一部完了 (D2212 項 2、D2219 項 2) → 残り = 設計 §3.3 の存在履歴、単位 5・3・11**: TPC-C 段 1 (NewOrder / Payment、CCBench 既定比 45% + 43%、
  点読み・点書き・insert のみで `tx.scan` を使わない) の合成候補を直列化可能性で認定できるようにする。設計 = `output/insights/2026-09-21/tpcc-trace-certification-design/README.md`
  (§7.1 の実装単位、§8 の親決定)。実装は Codex author、正しさゲートは不変、trace は compile 時に除去する (規律 1)。
  **済:** 単位 1・2 (CCBench 側、{{D:tpcc-v3-producer-silo}}、`output/insights/2026-09-22/t2854-tpcc-ccbench-v3/README.md`) = CCBench の local branch
  `izanagi-tpcc-v3-trace` に pin e9e477ca の子として C1 `56b5cb709628c9cac98e4e18ff676defc77a9117` (trace.hh の v3 helper・tpcc.hh の取引種別 context と
  trace build 限定の計数) と C2 `a6f2c7410d58ad140a62b11cc1beab29bfcd191b` (silo の v3 emitter)。計算ノード 1 走で v3 の構造・witness・内容、YCSB v2 の certified、
  TRACE=0 の前処理と逆アセンブルの一致、変異 6 件を確認。GitHub への push は人間手番 (D16)。単位 4 (verifier 側、D2224、entry 1828、
  `output/insights/2026-09-22/t2854-tpcc-verifier-v3/README.md`) = v3 を (表, key) で読み cycle に表と取引種別を載せる。v3 の run は存在履歴を検査するまで
  認定しない印 `Integrity.v3_existence_unverified` を立てる。
  **残り:** (1) 設計 §3.3 の存在履歴 (初期キー集合・insert 前の不存在・delete 版の読みの不整合) の verifier 実装と上の印の撤去。v3 を認定に使う前提で、
  §7.1 の単位表に担当が無い (単位 4 の insight §6)。(2) 単位 5: 旧 result_to_dict・CLI・pipeline・受領証 digest への v3 の表・取引種別の配線
  (`core.result_to_dict_v3`)、`orchestrator/campaign/pipeline.py` の allowlist の拡張 (tpcc + v3 + 57:43 の flag)、witness 試験と段 1 の正例・負例。
  単位 1・2 の実 trace は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/evidence/traces-2/` に zstd で保持。(3) 単位 3: mocc の v3 emitter
  (C1 の helper を使い [T-2844] の候補 C の上へ)。(4) 単位 11: pin 前進 ([T-2844] の候補 C の上へ C1 / C2 を載せて 1 回で)。D297 の検査器は header の差分を
  拒否するので、header を含む候補の受理方法を先に決める (単位 1・2 の insight §8)。
  本項で TPC-C の corpus が入るとき (pipeline の allowlist が tpcc を受理した時点) に見送り台帳 [T-156] (selector-8b descriptor への set-size 条件) の発火条件
  「TPC-C 級 workload corpus を採るとき」が成立するので、同項を再評価し、既裁定の「着手前に workload 別の set-size 分布を測る」順序を確認する。
  設計 insight §9 の CCBench 所見 (D2219 項 7): 段 1 で観測できたのは実行時の OrderLine 番号が 0 始まりであることだけ。寿命と範囲読みの所見は [T-2855]、
  si の所見は si を走らせる wave の担当。計算: 検証走・計測・開発の検査を含め 1 タスクの job 合計が 2 node 時間以上になる投入は、見積りを示してユーザー確認後に
  投入する (D2212 項 4、D2219 項 1)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §10、roadmap §3.1。
  base: 12fd984f537ae8432d3995ab1d4f128a1c22be65fa4224cdefc94be1a59e059c
