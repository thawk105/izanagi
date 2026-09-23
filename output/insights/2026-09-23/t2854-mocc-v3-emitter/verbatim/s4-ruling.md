# [T-2854] 単位 3 段 4 裁定 (親) — plan v2 と変異の事前登録

入力: 段 1 brief `s1-brief.md` (provisional (P1)〜(P8))。段 2・3 は (P6) により省略 (C2 の形の移植で設計択一が割れない。敵対検証は段 6 のレビュー 2 本が担う)。
裁定 inbox 再走査 (2026-09-23 08:4x JST): 最新 `rulings-inbox/2026-09-23-rulings-full32-verdicts.md` (08:29) の項 1 (T-2858: pin を C 単独で承認、TPC-C の commit は完成時に別途承認) と項 7 (`izanagi-tpcc-v3-trace` は今は push しない、単位 11 で C の上へ載せ直した候補を人間の push 判断へ渡す) は本 wave と食い違わない。
前提の実測: C1' = `6aa7a58fccff9efa218067d1b7ce83026a75357d` を作成済み (`mk-c1p.log`: 親 = C 1 本、C..C1' = header 2 file、blob は C1 と一致、mocc の blob は C のまま)。

## 1. provisional の裁定

| # | 裁定 |
|---|---|
| P1 | 採用。branch `izanagi-tpcc-v3-mocc` = C → C1' → C3。C1' の message は C1 のまま (`cherry-pick -x` の出所行つき)。C3 は `cc/mocc/transaction.cc` の 1 file |
| P2 | 採用 (§2)。 |
| P3 | 採用。比較基点は C。D297 の合格は名乗らない |
| P4 | 採用 |
| P5 | 採用 (§4) |
| P6 | 採用。段 6 は C++ (正しさ境界・規律 1) と probe (過剰・削除レンズ固定) の 2 本 |
| P7 | 採用。確認ライン: probe の計算 job が 2 本目を超える、または実測 Elapse で合計見込みが 2 node 時間以上なら投入前にユーザー確認 |
| P8 | 採用 |

## 2. plan v2 (C++、Codex author A) — 編集は C1' の `cc/mocc/transaction.cc` だけ

C の行番号 (= C1' と同じ) で書く。

1. writePhase の既存 `#if TRACE` ブロック (1159〜1200): `izanagi_txid` (1160) の直後に `const std::uint32_t izanagi_tx_type = izanagi_trace::tpcc_tx_type();`。C 行 (1161〜1164) は `izanagi_tx_type != 0` なら `izanagi_trace::emit_commit_v3(thid_, izanagi_txid, maxtid.epoch, maxtid.tid, read_set_.size(), write_set_.size(), 0, 0, izanagi_tx_type)`、0 なら現行の式をそのまま。R (1166〜1172) は v3 なら `emit_read_v3(thid_, izanagi_txid, get_storage(re.storage_), key_to_hex(re.key_), v.epoch, v.tid)`、0 なら現行の `emit_read(...)`。G2 lineage の 2 行 (1170〜1171) は分岐の外に現行どおり残す。W (1174〜1181) は v3 なら `emit_write_v3(..., get_storage(we.storage_), ..., op, maxtid.epoch, maxtid.tid)`。X not-locked-at-entry (1195〜1197) は v3 なら `emit_lock_violation_v3(thid_, izanagi_txid, get_storage(we.storage_), key_to_hex(we.key_), "not-locked-at-entry")`、0 なら現行の `izanagi_trace::emit_lock_violation(` 呼出しを文字どおり残す。`#line 1158` はそのまま (値の妥当性は §3 C1 と親の行照合で確かめる)。
2. UPDATE の X (1209〜1217): `if (... != W_LOCKED)` に波括弧を付け、中で v3 / v2 を選ぶ。G2 stamp の 2 行は現行どおり。`#line 1169` を保つ。
3. DELETE の X (1236〜1242): 同じ形。`#line 1187` を保つ。
4. publish の X (1251〜1258): 同じ形。`#line 1195` を保つ。
5. E (1267〜1269): E の式は現行のまま、直後に `izanagi_trace::clear_tpcc_tx_type();`。`#endif` の後ろに `#line` を足して、後続の物理行の論理行番号を C と一致させる (値は実装後の実行で決める)。
6. 変えないもの: P 行 (990〜1015)・validation・lock / unlock・abort・G2 watermark の関数群 (24〜120、env gate)・INSERT の X 除外・`#include`。1 取引に C 行はちょうど 1 本。
7. `-Wall -Wextra -Werror` で TRACE=0 / TRACE=1 とも警告 0。
8. 既存の v2 の式・呼出しの bytes を変えない (YCSB の出力 bytes と verifier の証拠面検出 `orchestrator/verifier/model.py` の関数名正規表現を保つ)。

## 3. 内部の受入 = 完了判定 (計算ノード 1 job、probe は Codex author B)

前 wave の probe (`verbatim/run_probe.py`・`v3check.py`・`selftest.py`、前 wave job dir `probe/` の写し) を mocc 向けに改めたもの。前 wave 裁定 §3 の C0〜C7 を次の置換で行う。

- C0: bundle から C (基点)、C1'、C3 を別 checkout に取り出し、C1' の親 = C、C3 の親 = C1'、C..C1' = header 2 file、C1'..C3 = `cc/mocc/transaction.cc` だけ、C..C3 = 3 file を照合。取り出した file 集合と blob を commit の tree と完全一致で照合 (`git archive` の `export-ignore` 欠落、前 wave fix 3 の対策を保つ)。toolchain は `tools/pegasus/mocc_trace_v1_policy.json` の compiler digest と gflags / glog の HEAD で束縛。`/scr` の空きを記録。
- C1: C と C3 の TRACE=0 compile database の 12 source / 21 entry で完全展開 (`-E -P -dD`) と include 活性を比較、全件一致。負例: C3 の tpcc.hh の `#include "trace.hh"` を `#if TRACE` の外へ出した版で TPC-C consumer 9 entry の include 活性が不一致。
- C2: C3 の TRACE=1 compile database の同じ 21 entry を実 flag の `-fsyntax-only` で rc=0。
- C3: C と C3 の `tpcc_mocc.exe` / `ycsb_mocc.exe` を等長の source / build path で build し、nm の `izanagi` 0 件、strings の `izanagi_trace` / `IZANAGI_` 0 件、正規化逆アセンブル一致。binary の sha256 一致・`.text` bytes 一致は主張しない。
- C4: TPC-C (C3、TRACE=1、`tpcc_mocc`、前 wave と同じ flag: 2 thread・extime 1・1 倉庫・Payment 43・他 3 種 0・clocks_per_us 2100) の B0 で v3 構造・witness (C 行数 = `commit_counts_`、E = C、batch 0、rc 0)・X = P = 0・種別 1 と 2 の両方が正・内容照合 (前 wave と同じ定義)。結果名 `structure+witness+content pass` (certified ではない)。G2 watermark の env は設定しない。
- C5: YCSB (C3、TRACE=1、`ycsb_mocc`、前 wave と同じ flag) の C 行が全て 7 token、現行 verifier `orchestrator/verify.py <dir> --expected-commits <stdout 値> --protocol mocc --ccbench-root <C3 の source> --json` が rc=0・certified。
- C6: §4 の変異。
- C7: 構造検査器の自己試験を親が login で走らせ全件期待どおり。
- C8: superproject の受入全走 (差分は insight と fragment だけ) が child-green。
- 生 trace: B0 の TPC-C / YCSB は圧縮して job dir に保持。変異の走は digest だけ。

## 4. 変異の事前登録 (DW-M01、独自 harness = 前 wave 裁定 §4 と同じ同等検査: 出現 1 回の assert・逐次・pristine 復元の sha256 照合・1 件ずつ flush、build 失敗は ERROR)

KILLED = 判定が fail かつ理由が登録どおりのときだけ。anchor の逐語は author A の実装後に親が C3 の実 bytes で確定する。

| ID | 基準 | 変異 | 期待 | 単一理由の根拠 |
|---|---|---|---|---|
| D1 | C3 | tpcc.hh の commit 成功直後 (quit 判定の前) に、成功 commit が 1,000 回目の thread が stderr へ marker を出し quit を立てる (前 wave と同じ置換) | PASS (全検査合格・marker ≥ 1・C 1,000 行以上の file ≥ 1) | mocc の writePhase が 1 commit に C を 1 本出すことを quit 境界で確かめる |
| M1m | C3 | mocc の `izanagi_trace::tpcc_tx_type()` の読みを `0U` に置換 (context を無視) | 先頭理由 `schema` (構造破損に伴う派生理由の併発は許す、前 wave M1 と同じ数え方) | TPC-C の走に v2 の C 行が出る。mocc 側の切替が効いていることの負例 |
| M2 | D1 | tpcc.hh の `#if !TRACE` を `#if 1` (旧計数順序) | 理由集合 = witness だけ・rc 0・E = C・C > commit 数・marker・1,000 行以上の file | mocc の上で計数修正が要ることの負例 |
| M3m | C3 | mocc の v3 W で表 6 を表 5 に写す | 理由集合 = content-table だけ | 構造・witness は不変 |
| M4m | C3 | mocc の v3 C で種別 1 と 2 を入れ替える | 理由集合 = content-txtype だけ | 構造・witness は不変 |
| M5m | C3 (前処理のみ) | mocc の DELETE 側の `#line 1187` を消す | mocc の 4 entry の完全展開が全件不一致・include 活性は全件一致・他 17 entry は一致 | 直後の `default: ERR;` の `__LINE__` だけがずれる。build しない |

SURVIVED は mutated 内容の diff で注入の実在を確かめるまで equivalent としない。初回結果は消さない。

## 5. 所有・順序

- author A: 子 worktree `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-moc-a`、編集面は親が作る使い捨て clone `output/runs/t2854-mocc-v3/ccbench` (C1' を detached checkout、gitignore 下) の `cc/mocc/transaction.cc` だけ。`external/ccbench/` は触らない (F546)。
- author B: 子 worktree `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-moc-b`、`output/runs/t2854-mocc-v3/probe/` に前 wave の probe の写しを置き mocc 向けに改める (run_probe.py・v3check.py・selftest.py・mutation-spec.template.json)。repo の tracked file は編集しない。親が job dir `probe/` へ退避する。
- A・B 並列 → 親が login で probe 自己試験 (C7)・A の差分検査・行照合 → 親が C3 を commit・bundle → spec の anchor 確定 → 段 6 レビュー 2 本 → fix → 計算 job → 記録 → 受入 → land → branch を主 checkout の submodule git dir へ非 force で fetch。
- 見積り: 計算 job 1 本 (前例 Elapse 191 秒、walltime 上限 60 分) ≈ 0.1 node 時間、受入 ≈ 0.25。合計 ≤ 1 node 時間。
