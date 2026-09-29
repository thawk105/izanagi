# 段 6 裁定 — レビュー 2 本と J0c 後の予算判定 (2026-09-29 JST、親)

入力: review-a.md (測定と集計の正しさ)、review-b.md (過剰・削除)、J0c (request 34682.nqsv、bnode005、11:28〜11:34 JST、Elapse 344 秒、rc 0)。

## J0 の結果 (J0c の job-manifest.json と runs.jsonl から)

- 依存準備 11.2 秒、通常 build 14.3 秒 (-j 24)、待機 build は compile 不能 (W5 欠測、判定表 1 行目)。
- perf は literal `perf` の preflight が nonzero-rc で不可 → N は D15 の RSS 下限で W1〜W4 とも 1,000,000 (maxrss 1,114,208〜1,243,768 kB ≥ 4 × 110,100,480 B)。飽和は未判定。
- run 単価 (within-run の median): W1 3.73 秒・W2 3.71・W3 3.71・W4 3.71。静定 load1 2.32 で settled。
- J0 3 attempt の Elapse 合計 = 18 + 32 + 344 = 394 秒 = 6.6 node 分。

## 予算判定 (s4 の式、結果を見る前に固定したとおり)

- 計測の上限 80 node 分 (J0 実 Elapse 6.6 分を含む)。walltime = (依存 11 + 並列 build + Σ run 3.7 秒 + 静定・checkout 約 20 秒) × 1.5。並列 build は J0 の -j 24 で 14 秒、J1 の 7 本並列 (-j 6) は 1 本あたり約 45 秒と保守側に置く。
- 梯子なし: J1 各 126 run → 約 14 分 × 4 = 56、J2 (W1〜W4、上位 3 ∪ control × GC 5 点 × 3) 各 60 run → 約 8 分 × 4 = 32 → 合計 6.6 + 56 + 32 = 94.6 > 80。
- R1 (J2 上位 2): J2 各 45 run → 6 分 × 4 = 24 → 86.6 > 80。
- R2 (J2 の GC 格子から 1 を外す): J2 各 36 run → 5 分 × 4 = 20 → 82.6 > 80。
- R3 (J1 reps 2): J1 各 84 run → 10 分 × 4 = 40 → 6.6 + 40 + 20 = **66.6 ≤ 80**。R4・R5 は不要。
- 適用: **R1 + R2 + R3**。J1 = reps 2、J2 = 上位 2 ∪ control × GC {10,100,1000,10000} × reps 3、W1〜W4 の 4 job。W2 の N は 1M なので共通 1M 条件の追加は不要 (B-B1 は自動的に満たす)。walltime は make-spec 後の analyze の見積りを使い、合計がこの判定を超えたら投入しない。

## レビュー所見の裁定

| ID | 裁定 | 扱い |
|---|---|---|
| A-F1 (合成 counter で find_saturation) | real・今回の結果への影響なし (perf 不可で RSS 経路) | fix: 実測 counter を保持して渡す (安価、次回 perf 可のとき効く) |
| A-F2 / B-B1 / B-B4 (J2 が 5 job、欠測 workload で作図停止) | real | fix: J2 は最大 4 job (W5 がある場合は W2 の job に同居)、作図は測定済み workload だけを描き欠測理由を caption と provenance に残す |
| A-F3 / B-B2 (R4 を make-spec で表せない) | real・成果物影響なし | 実装しない。予算判定で R4 不要が確定したため (DW-G05)。一次資料に「R4 は未実装で、必要になれば停止する」と書く |
| A-F4 / B-B6 (絶対 TPS median が summary に無い、図は mean) | real | fix: J2・J1 の条件別の絶対 TPS median と maxrss median を summary に出し、図も median にする |
| A-F5 (図 (b) に「探索値」) | real | fix: 図 (a) は「J1 探索値」、図 (b) は「J2 確認値」、両方に「正しさ未検証の診断値」 |
| A-F6 (作図が exit_code・計画一致を見ない) | real | fix: 作図は summary を通った入力 (analyze が計画一致を検査済み) に限り、exit_code 0・perf=False の行だけを使う |
| A-F7 (古い負例の赤理由) | real nit | fix: expected_reps を揃え集合だけ判定不能になる理由を直接検査 |
| B-B3 (build 単価の過小) | real | 親の見積りで保守側 45 秒に置いた (上記)。コード変更なし |
| B-B5 (compile command 照合が対象 target に限定されない) | real | fix: `ycsb_cicada.exe` の object (CMakeFiles/ycsb_cicada.exe.dir/) に属する 3 TU だけを照合し、各 1 回ずつ現れることを要求 |
| B-B7 (副軸 RSS が任意 genome) | real | fix: 副軸を削る。maxrss は summary の条件別 median と一次資料の表で示す |
| B-B8 (private helper 依存) | real・受容 | 実装しない。1 関数に局所化済みで、J0c で実際に通った。一次資料の限界に書く |
| B-B9 (設定 API が広い) | nit | 実装しない (梯子の適用に引数が要る)。事前登録外の条件を作らないのは親の運用で担保し、使った argv を記録する |
| A-F9 補足 (N 未決定で J0 全体停止) | real・成果物影響なし | 実装しない (J0 は完了、全 workload で N 確定) |

## 変異 (M1〜M9) の扱い

fix-4 の後に置換位置を再確認し、`tools/mutation_worktree.py` で本走する (DW-M05〜M08)。M2・M3 は B-B5 の fix で照合関数が変わるので、fix-4 の報告で置換位置を更新させる。

## 追補 (J1 実走後、親)

- R6-add1: J1 の j1-1 (34778.nqsv) と j1-3 (34775.nqsv) は Elapse 33 秒で rc=1。build log により、INLINE_VERSION_OPT=1 かつ INLINE_VERSION_PROMOTION=1 の 8 genome はすべて compile 不能 (`cc/cicada/include/transaction.hh:207:13: error: cannot convert 'Storage' to 'int'`、promotion 分岐 200-212 行の `write(s, key, TupleBody(...))` が現行の write と合わない)。他の genome は全て build 成功。stock で測れる空間は 24 点でなく 16 点。CCBench は改変しない (依頼の所有制約) ので、この 8 点は「stock で build 不能 = 欠測」として一次資料に書き、CCBench 還元候補の insight にする (還元判断: ユーザー確認待ち)。
- R6-add2: j1-1・j1-3 の build 可能な genome (各 2) と control を 1 job `cicada-j1-13` (60 run、build 5、rep ごとに j1-1 → j1-3 の順で並べ、control は各 rep・条件 1 回) にまとめて再投入 (34820.nqsv、cbt-m1、walltime 00:09:00)。spec は job dir の specs/j1/cicada-j1-13.json (sha256 e8ce203a…)。analyze には j1-0・j1-2・j1-13 の spec を渡す。投入束は j1 (j1-0・j1-2) と j1b (j1-13) の 2 つになる。
- R6-add3: 予算: j1-0 Elapse 424 秒、j1-1・j1-3 各 33 秒。j1-13 の walltime 9 分を足しても J1 は計 40 分の枠内。
