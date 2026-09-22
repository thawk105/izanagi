# [T-2854] 段 4 裁定 (親) — plan v2 と変異の事前登録

入力: 段 2 plan `out/s2-plan.md` (codex gpt-6-astra/medium, read-only)、段 3 相談 A `out/s3-consult-A.md` (正しさ境界・整合)、相談 B `out/s3-consult-B.md` (実効性と過剰・削除)。
裁定 inbox 再走査 (2026-09-22 20:1x JST): 最新 `rulings-inbox/2026-09-22-rulings-full31-verdicts.md` (08:4x 受領、= D2219) は本 wave と食い違わない。T-2854 の持ち越し文 (entry 1819) は §9 の寿命・範囲読みの所見 (OrderLine 番号の食い違いを含む) を T-2855 (段 2) に割り当てている。

## 1. 所見の裁定

| 所見 | 判定 | 採否・処置 |
|---|---|---|
| A1 plan の trace.hh 追記位置 (元 120 行の直前) は `emit_lock_violation` の本体内 | real (must-fix) | 採用。新 helper は元 121 行 (空行) と 122 行 (namespace 終端) の間に置く。trace.hh 全体が `#if TRACE` 内で TRACE=0 の出力は空、trace.hh 内に `__LINE__` の利用も無いので trace.hh には `#line` を置かない |
| A2 共有 header の TRACE=1 互換性を silo の 2 target だけでは見ない | real (should) | 採用。計算 job で候補の TRACE=1 compile database から、変更 header を読む 12 source / 21 entry を実 flag (`-Werror` を含む) の `-fsyntax-only` で通す |
| A3 / B3 範囲内の表・取引種別の取り違えを構造検査は通す | real (should) | 採用。実 trace の内容照合を足す (§3 の C4)。変異 M3・M4 を負例にする |
| A4 / B2 commit 成功直後の quit 経路を通常走は踏む保証が無い | real (B は must-fix) | 採用。scratch の診断変種 D1 (commit 成功直後に自 thread が quit を立てる) で候補は一致、計数を旧順序へ戻した M2 は不一致を確かめる。診断の変更は候補 commit に入れない |
| A5 生 trace を消すと後日の再検証ができない | real (should) | 採用。正常走 B0 の TPC-C / YCSB の生 trace を圧縮して job dir `evidence/traces/` に保持 (単位 4 への受け渡しまで)。repo へは入れない (sha256・bytes だけ insight へ) |
| A6 / B15 P1 の理由の一般化 | real (nit) | 採用。理由を「現行 CMake は workload 別 define を供給しない。TRACE=1 target 限定の define も可能だが CMake 変更と取引種別の二重管理が増える」に限定する |
| A7 P7 の正当化を「別 worktree だから」に置かない | real (nit) | 採用。根拠は依頼の明示 (単位 1 = trace.hh / tpcc.hh)・D16・設計 §5.3・F546。拒否されたらその地点で停止 |
| B1 変異 matrix の免除は誤り (CCBench の C++ と probe も実装面) | real (must-fix) | 採用。§4 の producer 変異 5 件を事前登録し、probe 内の独自 harness で走らせる (DW-M05 の同等検査を §4 で登録) |
| B5 21 entry の重複実行 | nit | 不採用 (全 21 entry を比べる。費用は小さい) |
| B6 D297 検査器の既知拒否の実走 | real (nit) | 採用。実走しない。検査器が `.hh` 差分を拒否する根拠 (`tools/check_trace0_preprocess_identity.py:195`) を記録し、単位 11 の未解決条件として残す。D297 pass と称さない |
| B7 既存 patch 17 本の apply 検査 | real (nit) | 採用。本 wave では行わない (pin を進めず、変異にも既存 patch を使わない)。17 本の列挙だけを単位 11 の材料として記録 |
| B8 P5 の書き方 (「段 1 では到達しない」は誤り) | real (should) | 採用。OrderLine 挿入 key の復号は内容照合 (C4) の材料として使い、「実行時の番号は 0 始まり」の観測だけを記録する。初期ロードの 1 始まりは静的根拠。§9 の再現は T-2855 と si の担当で、本 wave は再現を主張しない。si の所見は「対象外・未検証」と書く |
| B9 2 commit は必須でない | nit | 不採用。2 commit を維持 (単位 3 が C1 だけを T-2844 の候補 C の上へ載せられる) |
| B11 `/scr` 全体の容量 | real (should) | 採用。probe 起動時と trace 開始前に空き容量を記録し、不足ならその場で停止 |
| B13 既存 driver 関数の再利用 | nit | 採用 (author B の裁量)。`_run_checked`・`_resolve_toolchain`・`_prepare_dependencies`・`_normalize_objdump` 等を read-only import してよい。`_load_policy` / `_common_configure_args` / `_verify` / `_run_trace` は mocc 固定・witness なしなので使わない |
| B14 見積りの上限保証 | should | 採用。§5 |
| B4・B10・B12・B16 と A の攻撃不成立項目 | refuted / 不成立 | 記録のみ |

## 2. plan v2 (C++、Codex author A)

正本は plan `out/s2-plan.md` の §1〜§3 に、次の差分を当てたもの。

1. **include/trace.hh:** plan §1 の API (`tpcc_tx_type_context` / `set_tpcc_tx_type` / `tpcc_tx_type` / `clear_tpcc_tx_type` と `emit_commit_v3` / `emit_read_v3` / `emit_write_v3` / `emit_lock_violation_v3`、出力形は plan §1 の text 枠) を、元 121 行と 122 行の間に置く。既存 helper と既存行は 1 byte も変えない。`#line` は置かない。新しい include は足さない。
2. **include/tpcc.hh:** 変更は 3 箇所だけ (plan §2 の表から clear 3 行を削る。silo が E 直後に clear し、次の取引は必ず begin 直後の setter を通るので持越しは起きない。共有 header の変更面と `#line` を減らす)。
   (a) 元 26 行の include の後に `#if TRACE` / `#include "trace.hh"` / `#endif` / `#line 27`。
   (b) 元 55 行 `tx.begin();` の直後に `#if TRACE` / `izanagi_trace::set_tpcc_tx_type(get_tx_type(query.type));` / `#endif` / `#line 56`。
   (c) 元 110 行の quit 判定を plan §2 の形 (`#if !TRACE` / `#line 110` / 元の行 / `#endif` / `#line 111`) にする。
3. **cc/silo/transaction.cc:** plan §3 のとおり。writePhase の既存 `#if TRACE` 内で `izanagi_txid` の直後に `const std::uint32_t izanagi_tx_type = izanagi_trace::tpcc_tx_type();` を取り、C / R / W と X 3 箇所を `izanagi_tx_type != 0` で v3 helper、それ以外は現行の式・現行の `izanagi_trace::emit_lock_violation(` 呼出しをそのまま残す (verifier の証拠面検出 `model.py:45` の正規表現が関数名を探すため)。表は `get_storage(<elem>.storage_)`。E は現行式のまま、E の直後に `izanagi_trace::clear_tpcc_tx_type();`。`#line 635`・`#line 658`・`#line 679`・`#line 700` で復元。P 行・validation・begin / abort は変えない。
4. v3 frame は並走の単位 4 と一致させた形 (brief 不変条件 4) を変えない。
5. 変更は e9e477ca 上の 3 file だけ。C1 = include/trace.hh + include/tpcc.hh、C2 = cc/silo/transaction.cc。branch `izanagi-tpcc-v3-trace`。

## 3. 内部の受入 = 完了判定 (計算ノード 1 job、probe は Codex author B)

C0. 前提: `/scr` の空き容量と build 類の使用量を記録。toolchain は `tools/pegasus/mocc_trace_v1_policy.json` の compiler digest と gflags / glog の HEAD で束縛 (policy は読むだけ、mocc 固有 key は使わない)。CCBench の source は bundle から pin と C2 を別 checkout に取り出し、C1 の親 = pin、C2 の親 = C1、差分 = 3 file を照合。
C1. TRACE=0 前処理: pin と C2 の TRACE=0 compile database から 12 source / 21 entry の各々を `-E -P -dD` (完全展開) と include 活性 (`-E -dI` か line marker の入退場) で比べ、全件一致。比較 0 件・欠落・失敗は赤。自己試験の負例: 候補の tpcc.hh の `#include "trace.hh"` を `#if TRACE` の外へ出した版は include 活性の不一致で赤。
C2. TRACE=1 compile: C2 の TRACE=1 compile database の同じ 21 entry を実 flag の `-fsyntax-only` で rc=0。
C3. TRACE=0 binary: pin と C2 の tpcc_silo.exe / ycsb_silo.exe を**等長の source / build path** で build (比較のための追加 compile flag は付けない、先例 T-2844 と同じ)、nm の `izanagi` 0 件・strings の `izanagi_trace` / `IZANAGI_` 0 件、正規化逆アセンブル (行頭アドレス除去の `objdump -d --no-show-raw-insn`) 一致。
C4. TPC-C (C2、TRACE=1、2 thread、extime 1、1 倉庫、Payment 43・OrderStatus / Delivery / StockLevel 0、clocks_per_us 2100) の正常走 B0: plan §5 (a) の v3 構造検査、(b) witness (全 C 行数 = `commit_counts_`、E 数 = C 数、batch 0、rc 0)、X = P = 0、tx_type 1 と 2 の両方が正の件数。**内容照合** (根拠 `include/tpcc/tpcc_tx_neworder.hh:104`・`:114`・`:143`・`:279`、`tpcc_tx_payment.hh:39`・`:76`・`:188`・`:224`): 各 tx_type=1 frame は表 5・6・7・8 への W op=I を持ち、表 5 と表 6 の INSERT key が同じ 8 byte で 1 対 1 に対応し、表 4 への W を持たない。各 tx_type=2 frame は表 4 への W op=I をちょうど 1 本と表 0・1・2 への W op=U を持ち、表 5・6・7・8 への W を持たない。OrderLine (表 8) の INSERT key を復号し実行時の番号の最小値 (0 を期待) と見本を記録する。結果名は `structure+witness+content pass` (TPC-C の certified とは呼ばない)。
C5. YCSB (C2、TRACE=1): C 行が全て 7 token (v2) で、現行 verifier CLI `python3 <W>/orchestrator/verify.py <dir> --expected-commits <stdout 値> --protocol silo --ccbench-root <C2 の source checkout> --json` が rc=0・certified。
C6. D1 と変異 (§4): D1 が witness 一致、M1〜M5 がすべて KILLED。
C7. 構造検査器の自己試験 (plan §5 (f) の負例表 + C4 の内容照合の負例) は親が login で `--selftest` として先に走らせ、全件期待どおり。
C8. superproject の受入全走 (本 wave の superproject 差分は insight と spool fragment だけ) が child-green。
生 trace: B0 の TPC-C / YCSB は圧縮して job dir に保持。D1・変異の走は検査後に削除し digest だけ残す。

## 4. 変異の事前登録 (DW-M01、独自 harness の同等検査 = DW-M05)

harness は probe の一部 (author B)。scratch の C2 checkout の複製にだけ適用し、候補 commit・repo・wave 木は変えない。各変異は (i) 正確な文字列置換 1 箇所 (置換前の出現数 = 1 を assert、置換後の差分を記録)、(ii) 影響 target だけ incremental rebuild (M5 は build せず前処理だけ)、(iii) 走行と判定、(iv) pristine bytes へ戻して sha256 を照合、(v) 結果を 1 件ずつ JSON へ flush、を逐次に行う。build 失敗は ERROR (kill と数えない)。**KILLED = 判定が fail かつ最初に落ちた検査の理由コードが登録した期待コードと一致したときだけ。** anchor の逐語は author A の実装後に親が C2 の実 bytes で確定し (一意性を login で確認)、spec JSON で probe に渡す。

| ID | 基準 | 変異 (意図) | 期待理由コード | 単一理由の根拠 |
|---|---|---|---|---|
| D1 | C2 | tpcc.hh の commit 成功直後 (quit 判定より前) に、成功 commit 数が k (例 1000) に達した thread が自分で quit を立てる診断 | (pass が期待: witness 一致) | 診断変種そのもの。候補の計数が境界経路で正しいことの決定的確認 |
| M1 | C2 | tpcc.hh の setter 呼出しを消す (context が 0 のまま) | `schema` (TPC-C の走に v2 の C 行) | 構造検査の最初の C 行で落ちる。witness・内容は後段 |
| M2 | D1 | tpcc.hh の `#if !TRACE` を常に真の条件にする (旧計数順序) | `witness` (C 行数 > commit_counts_) | 構造・内容は不変。D1 で quit を立てた thread は必ず計数を飛ばす |
| M3 | C2 | silo の v3 W で表 6 を表 5 に写す | `content-table` | 構造・witness は不変。表 5・6 の INSERT 対応で落ちる |
| M4 | C2 | silo の v3 C で tx_type 1 と 2 を入れ替える | `content-txtype` | 構造・witness は不変。取引種別と操作群の対応で落ちる |
| M5 | C2 (前処理のみ) | tpcc.hh の `#line 56` を消す | `trace0-preprocess` (ERR の `__LINE__` がずれ 9 TU で不一致) | build しない。TRACE=0 前処理比較だけが見る |

SURVIVED は mutated 内容の diff で注入の実在を確かめるまで equivalent としない (DW-M04)。初回結果は消さない。

## 5. 計算量と確認ライン

1 job (walltime 上限 60 分) の見積り 0.4〜0.7 node 時間 (出所: 試算。依存準備、3 build 木、前処理 21×2 と構文 21、TPC-C 走 6 本 + YCSB 1 本、incremental rebuild 5 回、検査)。再投入 1 回を含め ≤ 1.4、受入 1〜2 回 ≈ 0.25 ずつ → 合計 ≤ 1.9 node 時間。**計算ノードへ 3 本目の probe job が要る場合、または Elapse の実測で合計見込みが 2 node 時間以上になる場合は、投入前にユーザーへ見積りを示して確認を取る。**

## 6. 所有・順序

- author A: 子 worktree `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-ccb-a`。編集面は親が事前に作る使い捨て clone `output/runs/t2854-ccbench-v3/ccbench` (e9e477ca) の 3 file だけ。`external/ccbench/` は触らない (F546)。
- author B: 子 worktree `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-ccb-b`。`output/runs/t2854-ccbench-v3/probe/` 配下に probe・自己試験・変異 harness・spec 雛形を書く。repo の tracked file は編集しない。親が job dir `probe/` へ退避する。
- A と B は並列。接点 (v3 frame、context API 名、stdout の `commit_counts_:` / `batch_commit_counts_:`、理由コード) は本裁定で固定。
- 順序: A・B 並列 → 親が login で probe 自己試験 (C7) と A の差分検査 → 親が 2 commit・bundle → 変異 spec の anchor 確定 → 段 6 レビュー 2 本 (C++ と probe) → fix → 計算 job → 記録 → 受入 → land。計算 job を段 6 fix の後に置くのは、fix で C2 が変わると証拠を取り直すため。
