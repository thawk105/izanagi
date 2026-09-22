# [T-2854] TPC-C 段 1 の CCBench 側 (単位 1・2) — trace v3 の helper・取引種別 context・trace build 限定の計数修正と silo の v3 emitter を、現 pin e9e477ca の子 2 commit として local branch に載せ、計算ノード 1 走で構造・witness・内容・TRACE=0 同一性・変異 6 件を確かめた

authority: none
default_effect: no-state-change

- 日付: 2026-09-22
- wave: `dev-wave-t2854-tpcc-ccbench-v3` (branch `worktree-dev-wave-t2854-tpcc-ccbench-v3`)。着手時 local main `eef04f5a7fae95153e6253d362ce872555e65d4e` (開始 gate rc=0、19:50:04 JST、job dir `startup-gate.log`)
- 依頼の逐語 = `verbatim/request.md`。入力 = 設計 `output/insights/2026-09-21/tpcc-trace-certification-design/README.md` の §3.1・§3.5・§7.1・§8
- 既裁定: D16、D14、D95、D295、D296、D297、D2207、D2212 項 2・4、D2219 項 2・7、F546。本 wave の設計判断は decisions の fragment (`{{D:tpcc-v3-producer-silo}}` として land 時に採番)
- job dir (親の script・生 log・codex receipt・bundle・probe・生 trace の圧縮): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/`
- 並走: 同じ T-2854 の単位 4 (verifier 側) は別 wave が担当。v3 frame の形は相互連絡で一致させた (§3)

## 0. 結論

1. **候補 commit:** CCBench の local branch `izanagi-tpcc-v3-trace` に、C1 = `56b5cb709628c9cac98e4e18ff676defc77a9117` (include/trace.hh・include/tpcc.hh) と C2 = `a6f2c7410d58ad140a62b11cc1beab29bfcd191b` (cc/silo/transaction.cc) を、現 pin `e9e477ca` の子として作った。push・gitlink・承認定数の更新はしていない (D16、依頼どおり)。
2. **計算ノードの確認 1 走 (request 18131.nqsv、bnode146、Elapse 191 秒) は C0〜C6 の全段合格。** TPC-C (NewOrder / Payment、2 thread、1 秒) の trace は v3 frame の構造検査・witness (C 行 36,156 = stdout の `commit_counts_` 36,156)・内容照合 (取引種別と操作群、NewOrder 表と Order 表の INSERT key の対応) に合格、YCSB の trace は v2 のまま現行 verifier が serializable / certified (294,331 取引)、TRACE=0 は 12 source / 21 compile entry の前処理 (完全展開と include 活性) と tpcc_silo / ycsb_silo の正規化逆アセンブルが pin と一致、TRACE=1 は同じ 21 entry が `-Werror` 付きの構文検査に合格。
3. **変異 (事前登録の 6 件) は全件期待どおり:** 診断変種 D1 (commit 成功直後に quit を立てる) は計数一致で PASS、計数を旧順序へ戻した M2 は D1 の上で C 1,950 > commit 数 1,948 の不一致だけで KILLED、取引種別の setter を消した M1・表 6 を 5 へ写した M3・種別 1 と 2 を入れ替えた M4・`#line 56` を消した M5 も登録した理由で KILLED (§5)。
4. **TPC-C の trace は certified ではない。** 本 wave の TPC-C の結果名は `structure+witness+content pass` であり、直列化可能性の認定ではない。現行 verifier は v3 を受理せず、並走の verifier 側 wave は v3 の run を「存在履歴 (設計 §3.3) の検査が未実装」の印で certified にしない設計と申告している (§7)。
5. **D297 の合格は名乗らない。** D297 の検査器は header の差分を保証範囲外として拒否する (`tools/check_trace0_preprocess_identity.py:195`)。本候補は header を変えるので、pin 前進 (単位 11) の前に header 差分の受理方法を決める必要がある (§8)。
6. 計算投入は合計 2 本、Elapse 17 秒 + 191 秒 = 208 秒 (約 0.06 node 時間)。1 本目は probe の source 取り出しの欠陥で C0 の configure が失敗した (§6)。

## 1. 依頼の完了条件と状態

| 完了条件 (段 4 裁定 `verbatim/s4-ruling.md` §3、kill 条件は段 6 裁定 `verbatim/s6-ruling.md` §3 で置換) | 状態 |
|---|---|
| 単位 1・2 を Codex author で実装し、CCBench の izanagi-trace 系統 (現 pin の子) に commit | **済** — §2 |
| C0 source と toolchain の束縛、C1 / C2 の分割 | **済** — pin・C2 とも 404 / 404 file の集合と blob が commit の tree と一致 (除外は gitlink `third_party/shirakami` だけ、symlink 0)。pin→C1 = header 2 file、C1→C2 = silo 1 file。compiler は policy の digest と一致した `x86_64-linux-gnu-g++-11` |
| C1 TRACE=0 前処理 (21 entry、完全展開 + include 活性) | **済** — 21 / 21 一致。負例 (`#include "trace.hh"` を `#if TRACE` の外へ出した版) は 9 / 9 で include 活性が不一致 (§4) |
| C2 TRACE=1 構文検査 (21 entry、実 flag) | **済** — 21 / 21 rc=0 |
| C3 TRACE=0 binary | **済** — tpcc_silo / ycsb_silo とも nm の `izanagi` 0 件、strings の `izanagi_trace` / `IZANAGI_` 0 件、正規化逆アセンブル一致 (binary 本体の sha256 は異なる、§4) |
| C4 TPC-C の v3 構造・witness・内容 | **済** — §3 |
| C5 YCSB の v2 と現行 verifier の certified | **済** — §3 |
| C6 D1 と変異 M1〜M5 | **済** — §5 |
| C7 構造検査器の自己試験 (親が login で実走) | **済** — 最終 193 / 193 (`evidence/parent-selftest-summary.txt`) |
| C8 superproject の受入全走 | 本 insight の記録 commit の後に走る。結果は land の受領証と worklog の後続記録が持つ (本 insight には書けない) |
| push・gitlink / 承認定数の更新・mocc (単位 3)・verifier / pipeline (単位 4・5) | 行っていない (scope 外) |

## 2. 候補 commit (CCBench の local branch `izanagi-tpcc-v3-trace`)

| 項目 | C1 | C2 |
|---|---|---|
| OID | `56b5cb709628c9cac98e4e18ff676defc77a9117` | `a6f2c7410d58ad140a62b11cc1beab29bfcd191b` |
| 親 | `e9e477ca1b55348ab4530de0b1cf663ce4555290` (現 pin) | C1 |
| tree | `0e98cdedb3cd72af7ba5ca177845861ff7a27311` | `30ab7f53774decad96d9ff96c98e38c194a71358` |
| 変更 | `include/trace.hh` +49、`include/tpcc.hh` +12 | `cc/silo/transaction.cc` +65 / −19 |
| 変更後の blob | trace.hh `1ff95bcec49e49d02669321b09414ab114c20df2`、tpcc.hh `24e7d13288cf7df1e86a87aac0bd44ab9112eb9c` | transaction.cc `4434447d2fa3fe31c21f014f30d2c4695e0b3422` |

- pin→C2 の raw diff は 3 file の M だけ (mode 100644 不変)。逐語 = `verbatim/mk-commits.log`。
- **作り方:** Codex author A が使い捨て clone (子 worktree の `output/runs/t2854-ccbench-v3/ccbench`、gitignore 下、F546) の 3 file を編集 → 親が clone から単位別 patch を取り出し、wave 木の submodule に job dir 配下の一時 worktree を pin で切って `git apply --check` → 適用 → 適用後の blob を author の最終 file と照合 → `commit -F` (committer は `git -c user.*`、T-2844 の mk-C-commit.sh 型)。superproject の作業ツリーの `external/ccbench` は 1 byte も書いていない (submodule の HEAD と作業ツリーは pin のまま、porcelain 0)。
- commit message の逐語 = `verbatim/C1-commit-message.txt`・`verbatim/C2-commit-message.txt`。trailer は Codex `role=author` (author A)、Codex `role=reviewer` (段 3 相談・段 6 レビュー、gpt-6-astra / medium)、Claude `role=manager`。
- 自己完結 bundle = job dir `C.bundle` (3,219,103 byte、sha256 `307ac02df46b0f7667cd546cbc97ad84a3a8e636041b5514e4edbe7e331d92a5`、complete history、`git bundle verify` 済み)。
- 差分の逐語は本 insight に写さない (`.patch` は実装面と判定されるため)。`git show 56b5cb70 a6f2c741` か bundle から読む。
- T-2844 の mocc 計装候補 C (`68106660`) が変えるのは `cc/mocc/transaction.cc` だけで、本 wave の 3 file と path が重ならない。C の上へ C1 / C2 を載せる際の path 上の衝突は無い (内容の結合確認は単位 11 の仕事)。

### 2.1 実装の要点 (詳細は decisions の fragment と `verbatim/s4-ruling.md` §2)

- **v3 frame:** `C txid thid epoch tid nR nW nS nQ tx_type` / `R txid table key_hex ver_epoch ver_tid` / `W txid table key_hex op epoch tid` / `X txid table key_hex reason`。table は `Storage` の整数 (`get_storage`)、tx_type は `TxType` の値、段 1 は nS = nQ = 0。P / E は v2 と同形。I 行は出さない。
- **切替:** `tpcc.hh` が `tx.begin()` 直後に trace build 限定の thread-local context へ取引種別を置き (`#if TRACE`)、silo の writePhase が 1 回読んで非 0 なら v3 helper、0 なら既存の v2 の式と既存の `emit_lock_violation` 呼出しを使う。E の直後に 0 へ戻す。1 取引に C 行は 1 本。
- **計数:** `tpcc.hh` の commit 成功後の quit 判定を `#if !TRACE` で囲み、trace build は成功 commit を必ず数える。TRACE=0 の判定と計数順序は不変。
- **`#line`:** tpcc.hh に 4 本 (27・56・110・111)、silo に 4 本 (635・658・679・700)。trace.hh は TRACE=0 で中身が空で `__LINE__` の利用も無いので置かない。親の独立検算 (`evidence/parent-trace0-lines-*.txt`) で、tpcc.hh と transaction.cc は TRACE=0 で有効な行の (論理行番号, 本文) が pin と完全一致 (MATCH)。trace.hh は file 末尾の改行後の空要素の番号だけが異なり (MISMATCH と出る)、実在の行と include 元の行番号には影響しない。

## 3. TPC-C と YCSB の走行 (C4・C5、計算 2 本目)

実行: `python3 tools/pegasus/dispatch_compute.py --task generic --walltime 01:00:00 -- /usr/bin/python3 <job dir>/probe/run_probe.py …` を wave worktree (clean、HEAD `eef04f5a7`) から。YCSB の検証に使った verifier はこの HEAD の版 (単位 4 の v3 対応 D2224 の着地前)。request 18131.nqsv、gen_S 1 node (bnode146)、21:22:58〜21:26:04 JST、Elapse 191 秒、child rc=0 (`evidence/compute-2-dispatch.log`)。段ごとの合否と所要 = `evidence/compute-2/compute-summary.json`。

| 走 | 条件 | 結果 |
|---|---|---|
| TPC-C B0 (C2、TRACE=1) | `-thread_num=2 -extime=1 -tpcc_num_wh=1 -tpcc_perc_payment=43 -tpcc_perc_order_status=0 -tpcc_perc_delivery=0 -tpcc_perc_stock_level=0 -clocks_per_us=2100` | `structure+witness+content pass`。C 36,156 = E 36,156 = `commit_counts_` 36,156、`batch_commit_counts_` 0、rc 0。R 499,538・W 535,872・X 0・P 0。取引種別は 1 (NewOrder) 19,751・2 (Payment) 16,405 |
| YCSB B0 (C2、TRACE=1) | `-thread_num=2 -extime=1 -ycsb_tuple_num=200 -ycsb_rratio=50 -ycsb_rmw=true -ycsb_max_ope=5 -ycsb_zipf_skew=0 -clocks_per_us=2100` | C 行はすべて v2 の 7 token。C 294,331 = `commit_counts_`。現行 verifier (`orchestrator/verify.py … --expected-commits 294331 --protocol silo --ccbench-root <C2 の source> --json`) は rc 0、runs 1、certified_serializable 1、verdict serializable (reads 1,457,064、writes 731,572、keys 200、edges 2,149,748) |

- 内容照合の定義 (段 6 裁定 F1): 各 frame の W から署名を作る (表 4 への INSERT = Payment、表 5〜8 への INSERT = NewOrder)。署名と宣言種別の一致を `content-txtype`、署名に対する表構成 (NewOrder は表 5・6・7・8 へ INSERT し表 5 と表 6 の key が同じ 8 byte で 1 対 1、Payment は表 4 へ INSERT 1 本と表 0・1・2 への UPDATE) を `content-table` で見る。frame の見本 = `evidence/compute-2/B0-tpcc-run.json` の `frame_samples`。
- **trace 量 (実測):** TPC-C 37,014,250 byte / 36,156 取引 = 約 1,024 byte / 取引 (100 万取引あたり約 1.02 GB)。設計 §7.3 の試算 (段 1 で約 1.37 GB) を置き換える実測値だが、条件は上の 1 走 (1 倉庫・2 thread・1 秒、NewOrder 54.6 %) に限る。YCSB は 83,058,277 byte / 294,331 取引 = 約 282 byte / 取引 (max_ope 5)。
- **生 trace の保持:** B0 の TPC-C / YCSB の生 trace を zstd で job dir `evidence/traces-2/` に保持 (TPC-C 3,028,777 + 2,964,134 byte、YCSB 6,482,431 + 7,397,516 byte。sha256 = `evidence/kept-traces-sha256.txt`)。単位 4・5 の結合確認に使える。repo には入れない。
- throughput は trace build の値なので性能の主張に使わない。

## 4. TRACE=0 / TRACE=1 の compile 面 (C1〜C3)

- **consumer:** `include/tpcc.hh` を include する 9 source (cicada・ermia・mocc・mvto・oze・si・silo・ss2pl・tictoc の `tpcc_*.cc`) と `include/trace.hh` を include する 3 source (silo・si・mocc の `transaction.cc`、各 4 workload) = 12 source / 21 compile entry。CMake の宣言から導いた期待集合と compile database が一致 (`evidence/compute-2/b0-cnd-consumers.json`)。
- **C1:** pin と C2 の TRACE=0 compile database の各 entry を、出力と依存 file の option だけを除いた実 argv で `-E -P -dD` (完全展開) と `-E` (line marker の入退場の file 列) にかけ、source / build root の文字列だけを置き換えて比較した。21 / 21 とも両方一致 (`evidence/compute-2/C1-preprocess.json`)。include 活性の比較では行番号を比べない (候補の `#line` 自体が line marker を増やすため。行番号と `__LINE__` の一致は完全展開の比較が担う、継続子への裁定)。
- **include 活性の負例:** C2 の tpcc.hh の `#include "trace.hh"` を `#if TRACE` の外へ出した scratch 版で、9 / 9 の TPC-C consumer の include 活性が不一致 (`evidence/compute-2/C1-include-negative-preprocess.json`)。**ただし同じ負例は完全展開の比較でも空白行 1 つ分ずれており、include 活性の比較だけが検出したわけではない。**
- **C2:** C2 の TRACE=1 compile database の同じ 21 entry を実 flag (`-Wall -Wextra -Werror` を含む) の `-fsyntax-only` にかけ 21 / 21 rc=0 (`evidence/compute-2/syntax.json`)。silo 以外の protocol の TRACE=1 compile 互換を含む。link と実行は silo だけ。
- **C3:** pin と C2 を等長の source / build path で build (比較用の追加 compile flag なし) し、`tpcc_silo.exe` (756,016 byte) と `ycsb_silo.exe` (701,720 byte) の両方で nm の `izanagi` 0 件、strings の `izanagi_trace` / `IZANAGI_` 0 件、正規化逆アセンブル (行頭アドレスを除いた `objdump -d --no-show-raw-insn`) の digest が一致 (`evidence/compute-2/binary-digests.json`)。**binary 本体の sha256 は pin と C2 で異なる** (埋め込まれる source path の文字差などが残る)。`.text` の bytes 一致は測っておらず主張しない。
- 比較は選んだ構成 (Release・stock の protocol option・GCC 11.4) に限る。全 compiler・全 macro 構成の同一性や D297 の保証とは同じでない。

## 5. 変異 (C6、事前登録 = 段 4 裁定 §4、kill 条件は段 6 裁定 §3)

harness は probe の一部 (Codex author B)。C2 の source の別 copy と別 build 木にだけ当て、正確な文字列置換 1 箇所 (出現数 1 を assert)・置換 diff の記録・影響 target だけの再 build・走行と判定・書き換えた file だけを pristine bytes へ戻して sha256 照合・1 件ずつ JSON へ flush、を逐次に行った。spec = job dir `spec/mutation-spec.json` (anchor は C2 の blob と同一の file で出現 1 回を親が照合、`verbatim/check-anchors-fix1.log`)。結果 = `evidence/compute-2/mutation-results.json`。

| ID | 変異 | 条件 | 結果 |
|---|---|---|---|
| D1 | tpcc.hh の commit 成功直後 (quit 判定の前) に、成功 commit が 1,000 回目の thread が stderr へ marker を出し quit を立てる | PASS = 全検査合格・marker ≥ 1・C 1,000 行以上の file ≥ 1 | **PASS** (marker 1、C = commit 数 = 1,849) |
| M1 | setter の呼出しを消す | 先頭理由 `schema` (構造破損に伴う派生理由の併発は許す) | **KILLED** (理由 = schema・frame・witness・content-txtype・content-table、先頭 schema) |
| M2 | D1 の上で `#if !TRACE` を `#if 1` にする (旧計数順序) | 理由集合 = witness だけ・rc 0・E = C・C > commit 数・marker・1,000 行以上の file | **KILLED** (C 1,950 > commit 数 1,948、E 1,950、marker 1) |
| M3 | silo の v3 W で表 6 を表 5 に写す | 理由集合 = content-table だけ | **KILLED** |
| M4 | silo の v3 C で種別 1 と 2 を入れ替える | 理由集合 = content-txtype だけ | **KILLED** |
| M5 | tpcc.hh の `#line 56` を消す (build しない) | 9 TPC-C consumer の完全展開が全件不一致・include 活性は全件一致 | **KILLED** |

- M1 は単一理由の変異ではなく、先頭理由の一致として数える (構造が壊れた trace は後段の検査も連鎖して落ちる)。
- D1 / M2 は、本候補の計数修正が「commit 成功直後に quit が立つ」境界で C 行数と commit 数を一致させること、旧順序ではこの境界で必ずずれることを決定的に示す。通常の 1 秒走 (B0) はこの境界を踏む保証が無い。
- 変異は計算 job 内で走らせた独自 harness で、repo の `tools/mutation_harness.py` (pytest 用) ではない。superproject の実装面差分はゼロ。

## 6. 経過 (段 1〜6)

- **段 1〜4:** brief (`verbatim/s1-brief.md`) → Codex plan 1 本 (`verbatim/s2-plan.md`) → 敵対相談 2 本 (正しさ境界 `verbatim/s3-consult-A.md`、実効性と過剰・削除 `verbatim/s3-consult-B.md`) → 裁定 (`verbatim/s4-ruling.md`)。相談の must-fix 3 件 (trace.hh の追記位置が既存関数の内側を指していた、変異免除は誤り、commit 直後の quit 境界の決定的確認が無い) を採用。D297 の既知拒否の実走と既存 patch 17 本の apply 検査は必要性が示せないので外した。
- **段 5:** Codex author A (C++、7 分) は逸脱なし。author B (probe) は 1 巡目で `run_probe.py` の後半を shell の heredoc で追記しようとして hook に拒否され正しく停止し、継続子 B2 が編集 tool で完成させた。
- **段 6:** 敵対レビュー 2 本はどちらも C++ への攻撃不成立、probe に must-fix 2 件 (M2 の発火確認、M4 の単一理由)。fix 1 → 焦点再レビュー 1 (NO-GO: fix 1 が R 行 0 件の検査まで消した回帰) → fix 2 → 焦点再レビュー 2 (GO)。段 6 の裁定 = `verbatim/s6-ruling.md`。
- **計算 1 本目の失敗:** request 18068.nqsv (bnode049、Elapse 17 秒) は C0 の CCBench configure が `add_subdirectory given source "cc/oze" which is not an existing directory` で rc=1 (`evidence/compute-1-summary.json`・`evidence/compute-1-configure-0023.stderr.txt`)。原因は CCBench の `.gitattributes` の `oze* export-ignore` で、probe が source を `git archive` で取り出したため `cc/oze` が抜けた。fix 3 で probe の scratch 保管庫の `info/attributes` に `* -export-ignore` を置き、取り出した file 集合と blob を commit の tree と完全一致で照合するようにした (2 本目で 404 / 404 一致)。fix 3 は実機の失敗への対応で、焦点再レビューは行わず 2 本目の走行そのもので確かめた。
- Codex 子は計 13 本 (plan 1・consult 2・author 3・review 2・fix 3・focus 2)、model call 計 188、wall 合計 4,334 秒 (`verbatim/codex-usage.tsv`)。全子 gpt-6-astra / medium。

## 7. 並走の単位 4 (verifier 側) との関係

- v3 frame の形は着手時に相互連絡で一致させた (C 10 token・tx_type 1..5・R / W / X に table 0..10・I 行は出さない・P / E は v2 と同形)。
- 単位 4 側の申告 (本 wave では検証していない): v3 の parse は同じ形、1 run 内の v2 / v3 混在は拒否、v3 の run は「設計 §3.3 の存在履歴 (挿入前の genesis 読み・削除版の読み) の検査が未実装」の印を立てて certified にしない。§3.3 の実装とこの印の撤去が、v3 を認定に使う前提として単位 5 以降に残る。
- 本 wave の生 trace (§3) は単位 4 の wave では使わない (実 emitter との結合は単位 5 の仕事) とのこと。

## 8. 単位 11 (pin 前進) へ渡す材料 — 本 wave では決めていない

- **D297 と header 差分:** D297 の検査器は `.hh` の差分を例外なく拒否する (`tools/check_trace0_preprocess_identity.py:195`)。本候補は `include/trace.hh`・`include/tpcc.hh` を変えるので、pin を C2 (か C の上へ載せた版) へ進めるときに検査器は fail-closed で落ちる。D2207 は検査器を緩めない向きの決定。§4 の consumer TU 比較は本 wave の内部の証拠であって D297 の代替承認ではない。単位 11 で受理方法 (検査器の拡張、別の保証名、裁定) を決める必要がある。
- **既存 patch:** `patches/` の 36 本のうち `cc/silo/transaction.cc` に hunk を持つものが 17 本 (header 2 file に hunk を持つものは 0 本)。本候補に当たるかは検査していない (段 3 の相談 B で必要性が示せず外した)。
- **mocc:** 単位 3 (mocc の v3 emitter) は C1 の helper を使える。T-2844 の候補 C とは path が重ならない。

## 9. §9 の CCBench 所見の実行再現 (D2219 項 7) について

- 段 1 の取引で観測できたのは「実行時の OrderLine の番号は 0 始まり」だけ: TPC-C B0 の 19,751 注文すべてで行番号の最小値が 0 (`orderline_zero_min_fraction` 1.0、見本は `evidence/compute-2/B0-tpcc-run.json`)。初期ロードが 1 始まりであることは静的根拠 (`include/tpcc/tpcc_initializer.hh:279`) のままで、本 wave は実測していない。隣の注文を scan で読む現象は段 1 の取引に無く再現していない。
- 挿入 tuple の公開後・write set 登録前の return、abort による挿入 tuple の即時解放、OrderStatus / Delivery の所見は段 1 の取引 (scan なし) では踏まない。si の所見は si を走らせていないので対象外・未検証。いずれも T-2855 (段 2) と si の担当で、本 wave は再現を主張しない。

## 10. 主張しないこと

- TPC-C の直列化可能性の認定 (v3 は現行 verifier が受理せず、単位 4 も当面 certified にしない)。
- D297 の合格、`.text` の bytes 一致、全 compiler・全 macro 構成での TRACE=0 同一性。
- 内容照合は W の特徴 (署名と表構成) の検査で、R の表番号の取り違えを範囲内で検出する保証は無い。
- 57 : 43 は生成比率の設定で、commit 件数の比は 1 走で NewOrder 54.6 % だった。
- throughput (trace build の値)。

## 11. 再現資料

- job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/`: `C.bundle`・`C1.oid`・`C2.oid`、`probe/` (run_probe.py・v3check.py・selftest.py・mutation-spec.template.json、Codex author B が作成、sha256 = `evidence/probe-and-parent-scripts-sha256.txt`)、`spec/mutation-spec.json`、`run-compute.sh`、`evidence/compute-1/`・`evidence/compute-2/` (compute.json 本体と 1.2 GB の log、sha256 = `evidence/compute-json-sha256.txt`)、`evidence/traces-2/` (圧縮した生 trace)、`mk-commits.sh`・`verify_trace0_lines.py`・`check_anchors.py` (親の検算)。
- repo には probe の `.py` と差分の `.patch` を入れていない (実装面の判定のため)。
