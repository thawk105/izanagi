# [T-2854] 単位 11 段 4 裁定 (親) — plan v2、変異の事前登録、受理方式案の骨格

入力: brief `s1-brief.md` (P1〜P7)、段 2 plan `out/s2-plan.md`、段 3 相談 A (正しさ境界・受理方式、sol) `out/s3-consult-A.md`、B (実効性と過剰・削除、luna) `out/s3-consult-B.md`。全て `check_codex_output.py` rc=0。
裁定 inbox 再走査 (14:2x JST): 最新は `rulings-inbox/2026-09-23-rulings-full34-verdicts.md` (D2237) のまま、T-2854 の新裁定なし。local main は `74e6d2f23` のまま (wave 開始時と同じ)。

## 1. 所見の裁定

| 所見 | 判定 | 採否 |
|---|---|---|
| A1 16 context は「silo 8 genome × `GLOBAL_VALUE_DEFINE` 有無」で、実 TPC-C build の 16 構成ではない。`tpcc_mocc.cc` は登録対象外で mocc の実 define を自動では選べない | real (`source_digest.py:344-351`・`:2116-2128`、`genome.py:106-116`、C2' `tpcc_silo.cc:1-16`・`tpcc_mocc.cc:1-13` を親が照合予定、§5) | 採用。insight の不足保証の書き方を改める |
| A2 D297 の「`-E -P` は #define を残さない」は現行 `_cpp_normalize` の `-dD` で部分的に解消。残る本質は consumer TU の文脈と列挙 | real | 採用 |
| A3 header 無変更の別候補は D297 を通りうるが、D2225 決定 2・3・5 と D2230 の再裁定、TRACE=1 だけで取引 loop を複製する経路のずれの確認が要る | real | 採用。第 4 の択として並記 |
| A4 (a) で D2225 決定 6 の改訂は必須とは限らない (過去の名乗りは維持)。D2207 は `<set>` include の射程で、無条件の改訂対象と書かない | real | 採用 |
| A5 (a) の「1〜2 wave」は未設計で上限でない。設計審査と実装の委任を 1 択に束ねない | real | 採用 |
| A6 brief の実測値は正しい。拒否は「受理集合外」を示すだけで TRACE=0 同一性の偽を示さない | real (nit) | 採用 (文言) |
| B1 C6 は単位 1〜3 の再演が多い。H-set を主に残し、protocol 側は代表例に絞る | real | 採用 (§3) |
| B2 非影響側 PASS を kill 条件にすると別 target なので結合の証拠にならず不安定 | real | 採用。非影響側の再 build・再走行はしない |
| B3 結合の命題は「同一 source tree の別 binary」。1 binary に 2 protocol が入る構成は無い | real | 採用 (結果文の限定) |
| B4 再投入時は累積 node 時間を合算して確認 | real | 採用 (§4) |
| B5 C1 の include 負例は前例の再演 | 一部 real | 不採用: 改修した probe 自身の C1 比較が検出することの陽性対照として残す (前処理だけで数十秒) |
| B6〜B8 anchor 実在・前例 fix の保持・brief の実測 | 攻撃不成立 | — |

## 2. plan v2 (probe、Codex author B) — 段 2 plan 第 1 部を次の限定で採用

- 起点: 子木 `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-u11-b` の `output/runs/t2854-u11/probe/` (単位 3 の probe の写し、sha256 は `setup-children.log`)。
- C0: bundle (`C.bundle`、ref `refs/heads/izanagi-tpcc-v3-silo-mocc`) から C と C2' を取り出し、C→C1'→C3→C2' の親を逐一照合。raw diff は C..C1' = header 2 file、C1'..C3 = `cc/mocc/transaction.cc`、C3..C2' = `cc/silo/transaction.cc`、C..C2' = 4 file (全て `M 100644`)。取り出した file 集合と blob を tree と完全一致で照合 (export-ignore 対策を保持)。toolchain の束縛は前例どおり。
- build: C TRACE=0、C2' TRACE=0、C2' TRACE=1 の 3 木で `tpcc_silo`・`ycsb_silo`・`tpcc_mocc`・`ycsb_mocc` の 4 target。変異用の別 build 木は影響 target だけを再 build。
- C1: C と C2' の TRACE=0 compile database で 12 source / 21 entry (期待集合との厳密照合を両木で再確認) の完全展開 (`-E -P -dD`) と include 活性。21 / 21 一致を要求。負例 (tpcc.hh の `#include "trace.hh"` を `#if TRACE` の外へ) は TPC-C 9 entry の include 活性不一致を要求 (probe の陽性対照)。
- C2: C2' TRACE=1 の同じ 21 entry を実 flag の `-fsyntax-only`、21 / 21 rc=0。
- C3: 4 binary で nm の `izanagi` 0 件、strings の `izanagi_trace` / `IZANAGI_` 0 件、正規化逆アセンブル一致 (C と C2')。binary 本体の sha256・`.text` bytes 一致は主張しない。
- C4: C2' TRACE=1 の `tpcc_silo` と `tpcc_mocc` の B0 (前例と同じ flag) で `structure+witness+content pass`、X = P = 0、種別 1・2 とも正。
- C5: C2' TRACE=1 の `ycsb_silo` と `ycsb_mocc` の B0 (前例と同じ flag) の C 行が全て 7 token、現行 verifier `orchestrator/verify.py <dir> --expected-commits <stdout 値> --protocol silo|mocc --ccbench-root <C2' の source> --json` が rc 0・certified。protocol を引数化する (`run_probe.py` の mocc 固定を外す)。
- C6: §3 の 4 変異だけ。削った変異 (H-count-D/M、S-line、M-line) の実装・selftest 負例は作らない。
- C7: `v3check.py` の自己試験 (親が login)。selftest は §3 の判定に合わせて最小に改める。
- 生 trace: B0 の 4 走行を zstd で保持し、raw の byte 数・sha256 と圧縮 file の sha256 を記録。変異走行は digest と判定だけ。
- 結果文の命題: 「C2' の単一 source tree から作る各 protocol の binary が、共有 header と各 emitter を正しく使う」。2 protocol が 1 binary に入る構成は無い。D297 の合格・TPC-C の certified は名乗らない。

## 3. 変異の事前登録 (DW-M01、独自 harness は前例と同等: 出現 1 回の assert・逐次・pristine 復元の sha256 照合・1 件ずつ flush、build / 走行の失敗は ERROR で kill に数えない)

基準は全て C2'。KILLED = 判定が fail かつ理由が登録どおりのときだけ。anchor の逐語は author B の実装後に親が C2' の実 bytes で出現 1 回を照合して確定する。

| ID | 変異 (C2' の行は段 2 plan の静的読み) | 走らせるもの | 期待 (KILLED の条件) | 単一理由の根拠 |
|---|---|---|---|---|
| H-set | `include/tpcc.hh:61` の `izanagi_trace::set_tpcc_tx_type(get_tx_type(query.type));` を消す (呼ばない形) | `tpcc_silo` と `tpcc_mocc` を再 build し各 B0 | **両 protocol とも**先頭理由 `schema` (構造破損に伴う派生理由の併発は許す、前例 M1 と同じ数え方)。片側だけの赤は KILLED と呼ばない | 共有 header の 1 箇所が 2 protocol の v3 切替を同時に担うこと (結合固有)。context 0 で両 emitter が v2 の C 行を出す |
| H-line | `include/tpcc.hh:63` の `#line 56` を消す (build しない) | C1 の 21 entry の前処理だけ | TPC-C 9 entry の完全展開が全件不一致、他 12 entry は一致、include 活性は 21 / 21 一致 | 後続の `ERR` の `__LINE__` だけがずれる。規律 1 の証拠層 (C1) が結合 tree の共有 header の論理行ずれを検出すること |
| S-table | `cc/silo/transaction.cc:628-632` の `emit_write_v3` の表引数で、表 6 を 5 へ写す | `tpcc_silo` だけ再 build し B0 | silo の理由集合 = `{content-table}` だけ | 構造・witness は不変。mocc は再 build・再走しない (B2) |
| M-type | `cc/mocc/transaction.cc:1162-1165` の `emit_commit_v3` の最終引数で種別 1 と 2 を入れ替える | `tpcc_mocc` だけ再 build し B0 | mocc の理由集合 = `{content-txtype}` だけ | 構造・witness は不変。silo は再 build・再走しない (B2) |

- 対照: 無変異の C4 (両 protocol の B0 が pass) が各変異の陰性対照を兼ねる。
- SURVIVED は mutated 内容の diff で注入の実在を確かめるまで equivalent としない。初回結果は消さない。
- superproject の実装面差分はゼロなので pytest の変異 matrix は免除 (DW-S04)。受入全走は行う。

## 4. 計算の見積りと確認線

- probe 1 job (walltime 上限 60 分)。段 2 の推測 8〜15 分 ≈ 0.13〜0.25 node 時間 (変異を 4 件に絞ったので下側寄り)。受入 1 回 ≈ 0.25。合計 ≈ 0.4〜0.5 node 時間で D2212 項 4 の線 (2 node 時間) の下。確認不要。
- 失敗して再投入が要るときは、消費済み Elapse と次 job の walltime 上限・受入を合算し、2 node 時間以上の見込みなら投入前にユーザーへ確認する。

## 5. 受理方式案の骨格 (insight §に書く。検査器は編集しない)

- 事実: 現行 D297 検査器は C→C2' を `_validate_diff` の header 一律拒否で止める (rc=1、前処理に入らない)。これは「受理集合外」を示すだけで、TRACE=0 同一性の偽を示さない。
- 択 (いずれも pin C を維持したまま次に何を検討するかの問い。本 wave では C2' を pin に入れない):
  1. **D297 の header 受理規則の設計審査** (変更 header を読む consumer TU の列挙と、TU ごとの protocol・実 define の対応、TRACE=0 完全展開と include 活性の比較、複数 compiler)。審査の承認と実装の委任は別。D297 の受理規則の改訂が要る。D2207 は `<set>` の射程で整合を説明、D2225 決定 6 の過去の名乗りは維持、D780 項 2 の別防壁は単独設計しない。
  2. **C2' に限る代替証拠での受理** (本 wave の 21 entry・4 binary の証拠、必要なら pin 前進 wave で 16 context × GCC 2 版へ広げた consumer TU 比較を足す)。D297 合格とは呼ばない限定例外の新裁定が要る。
  3. **header 無変更の別候補** (取引 loop を `tpcc_<protocol>.cc` の `#if TRACE` へ複製)。D297 は現行のまま通る可能性があるが未実証。D2225 決定 2・3・5 と D2230 の再裁定、両 workload 経路の対応確認、C++ と結合証拠の作り直しが要る。
  4. **当面は何もしない** (C2' は branch 証拠のまま、TPC-C 段 1 の campaign 認定は保留)。既裁定の変更なし。
- 推奨 (親): 1 の設計審査。理由 = 段 2 (設計 §5.3・§7.1 の単位 6・7) も `include/tpcc.hh`・`tpcc_initializer.hh` 等の header を変えるので、C2' 限りの例外 (2) は段 2 で同じ諮問を繰り返す。2 は速いが、例外を重ねるほど D297 の保証名が実態から離れる。3 は検証済みの C1〜C3 を捨て、取引 loop の二重管理を作る。
- 不足する保証 (2 の場合): silo の他 7 genome と `GLOBAL_VALUE_DEFINE` 無の文脈、第 2 compiler (GCC 12.3) での比較、repo の独立した検査器としての試験と変異。列挙した 21 entry の外の TU。ただし 16 context は実 TPC-C build の 16 構成ではない (A1)。
