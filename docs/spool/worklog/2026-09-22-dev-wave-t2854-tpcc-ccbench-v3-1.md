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
- **並走:** 同じ T-2854 の単位 4 (verifier 側) を別 wave が同時に進めた (依頼時点で担当分割済み、譲り合いの対象ではないと判断)。v3 frame の形 (C 10 token、R / W / X に表、I 行は出さない) を相互連絡で一致させた。worklog の [T-2854] 項目は、後に land する側が両成果を統合して `更新` に置く取り決め (本 fragment は carry だけ)。単位 4 側の申告: v3 の run は設計 §3.3 の存在履歴の検査が未実装の間 certified にしない。
- 計算投入: 2 本、Elapse 計 208 秒 (約 0.06 node 時間) で、D2212 項 4・D2219 項 1 の確認ライン (2 node 時間) 未満のため確認なしで投入した。1 本目 (18068.nqsv、17 秒) は probe が source を `git archive` で取り出し、CCBench の `.gitattributes` の `oze* export-ignore` で cc/oze が抜けて CMake configure が失敗した。probe を直し (取り出し後に tree と file 集合・blob を完全一致で照合)、2 本目 (18131.nqsv、191 秒、bnode146) で C0〜C6 の全段合格。
- 結果の要点: TPC-C は C 36,156 = commit 数 36,156 (NewOrder 19,751 / Payment 16,405、X = P = 0) で `structure+witness+content pass` (certified ではない)。YCSB は v2 のまま現行 verifier が certified (294,331 取引)。TRACE=0 は 12 source / 21 entry の前処理 (完全展開と include 活性) と tpcc_silo / ycsb_silo の正規化逆アセンブルが pin と一致、TRACE=1 は 21 entry が `-Werror` 付き構文検査に合格。変異 D1 PASS・M1〜M5 KILLED (M2 は D1 の上で C 1,950 > commit 数 1,948)。trace 量の実測は約 1,024 byte / 取引 (設計の試算 1.37 GB / 100 万取引を、この 1 走の条件で約 1.02 GB に置き換える)。
- 素材: trace build の計数修正の境界 (commit 成功直後の quit) は通常の短時間走では踏む保証が無く、commit 直後に自分で quit を立てる診断変種 (D1) と旧順序への変異 (M2) で初めて決定的に示せた。
- D297 の検査器は header の差分を拒否するので、本候補は D297 の合格を名乗らず、pin 前進 (単位 11) の前に header 差分の受理方法を決める必要がある (insight §8)。
- D2219 項 7 (§9 の実行再現): 段 1 で観測できたのは実行時の OrderLine 番号が 0 始まり (19,751 注文すべて) であることだけ。他の所見は段 1 の取引では踏まない、または si を走らせていないので未検証。見送り台帳 [T-156] の発火条件 (TPC-C 級 corpus の採用) は、pipeline の allowlist がまだ YCSB だけなので本 wave では成立していない。
- 段 3 相談 2 本の must-fix 3 件 (trace.hh の追記位置が既存関数の内側、変異免除の誤り、commit 直後の quit 境界の決定的確認) を採用。D297 の既知拒否の実走と既存 patch 17 本の apply 検査は必要性が示せず外した。段 6 レビュー 2 本は C++ への攻撃不成立、probe の must-fix 2 件 → fix 1 → 焦点再レビュー 1 は NO-GO (fix 1 が R 行 0 件の検査まで消した回帰) → fix 2 → 焦点再レビュー 2 で GO。witness parser の二重実装 (nit) は不採用。
- 異常: 着手 (2026-09-22 08:47 JST) の worktree 作成後に session が約 11 時間止まり、19:4x に再開した (開始 gate は再開後 19:50 に local main eef04f5a7 で rc=0)。段 5 の author B は `run_probe.py` の後半を shell の heredoc で追記しようとして hook に拒否され、迂回せず停止した (継続子が編集 tool で完成)。
- 工数: Codex 子 13 本 (plan 1・consult 2・author 3・review 2・fix 3・focus 2、全て gpt-6-astra / medium)、model call 計 188、wall 合計 4,334 秒。計算ノード 2 job (208 秒)。受入全走と land の結果は本 entry に書けない (記録 commit の後に走る)。

## 次の一手差分

### carry

- [T-2854]
