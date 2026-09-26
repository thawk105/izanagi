# silo-function-policy 軸 — 既知最良超え 3 点の別 job 再測 (2026-09-26、[T-2865] 付随)

- 位置づけ: `output/insights/2026-09-23/t2865-silo-policy-known-best-compare/README.md` (D2240、以下「元の小比較」) の後継。D2243 項 1「論文 (ComSys 原稿を含む) でこの 3 点を既知最良を超えた点として書く前に、別 job 再測を行う」の実施記録。**報告カテゴリは「偵察 (preliminary)」** で、事前登録のどの構成でもない。可変状態の正本にはしない。
- wave: branch `t2865-known-best-recheck`、起点 local main `265cce13c` (開始 gate rc=0)。
- **§1 の判定規則は計測 job を投げる前に書き、この節だけを先に commit した** (commit `4175771006`、2026-09-26 20:15:46 JST。計測 job の投入は同 20:16 JST ごろ、規律 3)。§0 と §2 以降は結果を見た後に追記した。§1 の本文は追記時に変えていない。
- 逐語 (`verbatim/`): 依頼 (`request.md`)、段 1 brief (`brief.md`)、段 3 相談 (`s3-consult-A.md`)、段 4 裁定 (`s4-ruling.md`)、段 5 実装子の報告 (`s5-author-agg.md`)、段 6 レビュー・裁定・焦点再レビュー (`s6-review-A.md`・`s6-ruling-1.md`・`s6-focus-1.md`)、集計スクリプト (`recheck-aggregate-script.md`)、各方策の生値の抜粋 (`raw-cases.txt`、jq の出力そのまま)。

## 0. 要約

1. **3 点とも §1.3 の判定で「再現」だった。** 別 job での最良参照比 r' は 1111 = 1.051、1110 = 1.065、1001 = 1.073 (元の小比較では 1.068、1.069、1.062)。3 job とも最良参照は fixed10 (静的 10 µs) で、r' は fixed10 比と同じ値。
2. 18 方策 (3 job × 6) すべてが legacy・性能構成の両 verify で serializable、trace0 clean、status complete。投げ直しは 0 本 (採用試行 = 各 job 番号の 1 本目)。
3. 補助指標 (判定に使わない): 3 点とも、5 rep の最小が同 job の fixed10 の 5 rep 最大を上回った。同じ job に入った相方の IR 点 (0000・0001・0110) は 0.973〜0.989 で、元の小比較 (0.983〜0.994) と同じく fixed10 を下回った。
4. **これで論文に書けること:** 「固定 16 点のテンプレート部分空間で、同 job の既知最良 (現 pin で再評価した静的 10 µs) を 3% 超えて上回った 3 点は、別 job・別ノードの再測でもそれぞれ 3% 超 (5〜7%) を保った」。限定 (§3) を同じ段落に置く。
5. 計算: 計測 3 job の Elapse 合計 2,318 秒 (0.64 node 時間)。受入を含む見積りは確認線 (2 node 時間) の下。

## 1. 判定規則 (結果を見る前に固定)

### 1.1 対象と計測

- 対象は元の小比較で同 job の最良参照比が 3% 線を越えた 3 点に固定する: `1111` (job 0)、`1110` (job 1)、`1001` (job 6)。
- 機構は既存の偵察 driver を**コード変更なし**で使う: `python3 -m orchestrator.campaign.silo_policy_recon run --phase compare --job <0|1|6>` を `tools/pegasus/dispatch_compute.py --task generic` (walltime 30 分、待ち上限 3600 秒) で 1 job 1 ノード、3 本。job の中身は元の compare job と同じで、対象点 + 同 job の相方 IR 1 点 + abort0・stock・`B0-L-W0`・fixed10 の 6 方策、実行順も元と同じ (`_cases` の job mod 6 巡回)。相方 IR 点は判定に使わず、記述だけする。
- 結果は `output/env/pegasus/calibration/silo_function_policy_recon/compare-recheck/compare-<job>.json`。元の `compare/` 配下と段階 D の file は書き換えない。

### 1.2 投げ直しと採用試行 (値を見ずに決める)

- 各 job 番号について compare job を 1 本採用する。採用試行は結果の throughput・abort 率・比を読む前に固定する。
- 起動前失敗 (dispatch が driver を起動しなかった)、または対象点の行を一つも生成せずに終了した場合だけ、同じ job 番号を最大 1 回投げ直す。
- Pre-running のまま停滞して重複投入した場合は、先に完了した試行を採用し、他方も記録する。
- 完了後の参照不適格や対象点の値を理由に投げ直さない。部分的な JSON でも対象点の行があればそれを採用し、下の規則を当てる。

### 1.3 判定 (この順に当てる)

1. **束縛:** 採用 job の phase = compare、job 番号、`case_order` と各行の role・順序が driver の `_cases("compare", job)` と一致すること。対象点の IR 本文 sha256 と因子が列挙 (`silo_policy_ir.enumerate_recon`) および元の compare JSON の値と一致すること。abort0 の本文、stock・`B0-L-W0`・fixed10 の genome flags、fixed10 の trace1 / trace0 の実効 define (`-DBACKOFF_FIXED=10` と `-DBACK_OFF=1` がちょうど 1 個ずつ)、固定 workload、source evidence が元の小比較の集計 (`_compare_detail`) と同じ照合を通ること。(hostname, started_at) が元の 8 job のどれとも異なること。**対象点を判定できない束縛不成立、または対象点の行の欠損は「判定不能」。**
2. 束縛が成立した後、対象点の status が `verify-not-certified` または `trace0-not-clean` なら **「失格」** (規律 2)。
3. それ以外で、対象点・同 job の abort0・参照 3 本 (stock・`B0-L-W0`・fixed10) のいずれかが D2240 項 2 の適格条件 (両 verify certified・trace0 clean・5 rep 有効・前後の source evidence が非空で一致) を満たさない、または対象点が high-abort (abort 率の中央値が同 job の abort0 の 2 倍超) なら **「判定不能」**。相方 IR 点の適格性は条件に含めない。
4. 残る対象点について、5 rep throughput 中央値を、同じ job の stock・`B0-L-W0`・fixed10 の各中央値の最大値で割った r' を出す。**r' > 1.03 は「再現」、r' ≤ 1.03 (ちょうど 1.03 を含む) は「非再現」。** fixed10 が最良参照でなくても最大値を分母に使う。

### 1.4 記述の範囲

- 論文で「別 job 再測でも、同 job の既知参照の最良を 3% 超えた」と書けるのは「再現」の点だけ。「3 点とも」は 3 点すべてが再現のときだけ使う。
- 元と新の比を平均して判定しない。元の値を新しい独立証拠として数えない (元の値は 16 点から 3% 超を選んだ選択に使った値である)。
- 補助指標 (fixed10 比、対象点の 5 rep 最小が同 job の fixed10 の 5 rep 最大を上回るか、元の比との差、相方 IR 点の値) は記述だけで、判定に使わない。
- 限定: 3% 線は Pegasus で未較正の暫定値。統計的優位、多重選択を補正した有意性、別 workload への転移は主張しない。対象点の job 内の位置は元と同じなので、この再測は job・ノード・時刻が別の再測であって、実行位置や job 内の交絡から独立した再現ではない。
- pin: 元の計測は CCBench `e9e477ca`、本再測は `68106660`。確認した差分 (`git diff --stat e9e477ca 68106660`) は `cc/mocc/transaction.cc` の 64 行追加だけ。pin 差は記録し、同一 binary の証明とは扱わない。pin 差だけを理由に再測を無効にも有効にもしない (規律 7)。
- firewall (手順書 §3-D): 本 insight・結果 JSON・集計 JSON には点 ID と比が載る。段階 E / F の coder・planner の入力へ流さない。`projection.json` は書き換えない。本 insight を読んだ事実は段階 E / F の campaign provenance に情報源として記録する義務を残す。
- 診断 build は NON_ADMISSIBLE で、certified 候補とは称さない (D2226 項 5)。

### 1.5 計算の見積り (投入前、job Elapse の実測単価)

- 計測: 元の compare job の Elapse 768〜779 秒 × 3 = 約 2,340 秒 (0.65 node 時間)。投げ直しが全 job で起きる最悪時は 6 job 約 4,670 秒 (1.30)。
- 受入全走: 2026-09-26 の受入 3 shard の Elapse 合計 約 1,070 秒 (0.30) × 最大 2 回 = 0.59。
- 焦点走・変異は repo の実装面の差分ゼロで不要 (集計は repo 外)。
- 検査込み合計: 通常 約 0.95、最悪 約 1.89 node 時間 < 2 → D2212 項 4 のユーザー確認は不要。

## 2. 実測

### 2.1 構成と採用試行

- 計測木 3 本 (`.claude/worktrees/t2865-recheck-recon-{0,1,6}`、detached `265cce13c`、CCBench `68106660`、作成時 clean) から、§1.1 の argv を同時に 3 本投げた。driver・build 経路・workload・bench 構成 (1M records / 48 threads / skew 0.9 / rratio 5 / rmw false / max_ope 10 / 3 秒 / 5 rep、numactl interleave) は元の小比較と同じ設定。`silo_policy_recon.py`・`silo_policy_coverage.py`・`silo_policy_ir.py` は元の計測 commit `9cd4099d7` から無変更 (`git log` で確認)。これらが import する `orchestrator/campaign/pipeline.py`・`pin.py` 等は元の計測後に他 wave の変更を受けている (`git diff --stat 9cd4099d7 265cce13c -- orchestrator/campaign/`)。
- 3 本とも dispatch rc=0 で完了し、driver の error は無い。§1.2 の投げ直し条件に当たる job は無く、**採用試行は各 job 番号の 1 本目** (結果 JSON を開く前に確定)。

| job | 対象点 | request | node | 開始 (JST) | Elapse |
|---|---|---|---|---|---|
| 0 | 1111 | 29950.nqsv | bnode105 | 20:23:58 | 770 秒 |
| 1 | 1110 | 29951.nqsv | bnode107 | 20:16:19 | 774 秒 |
| 6 | 1001 | 29952.nqsv | bnode108 | 20:16:19 | 774 秒 |

- 結果 = `output/env/pegasus/calibration/silo_function_policy_recon/compare-recheck/compare-{0,1,6}.json`、判定 = 同 dir の `recheck-aggregate.json` (集計スクリプトの出力そのまま、login で実行)。元の `compare/` 配下・段階 D の file・`projection.json` は書き換えていない。

### 2.2 集計スクリプトの検収 (新 job に当てる前)

- 集計は既存 `compare-aggregate` (8 job 揃い・現行 PIN 一致を要求) が使えないため、Codex author が driver の関数を import して per-job の照合と比の計算を再利用する repo 外スクリプトを書いた (`verbatim/recheck-aggregate-script.md`、sha256 `829da2ea…`)。
- 親が wave の木で実走: (a) 元の 8 job に当てると 16 点の {case_id, job, ratio_vs, best_ref_ratio, reason, exceeds} が既存 `compare-aggregate.json` と完全一致 (float の丸めなし)、(b) 負例 3 本 (対象点の `source_evidence_after` 欠落 → 判定不能、fixed10 の trace0 define 不成立 → 束縛不成立で判定不能、対象点の verify 不成立 → 失格) がすべて期待どおり。
- スクリプトは §1.3 より強い照合を 2 つ持つ: 相方 IR 点の本文 sha256・因子も照合する (driver の `_compare_detail` と同じく job の全 IR 行を照合するため)、新 3 job の toolchain の一致も要求する。今回のデータではどちらも成立しており、判定の根拠は §1.3 の条件だけである。

### 2.3 参照 (同 job の 5 rep 中央値、千 txn/s と abort 率)

| job | abort0 | stock | B0-L-W0 | fixed10 | (元の fixed10) |
|---|---|---|---|---|---|
| 0 | 2,356 (0.785) | 1,367 (0.125) | 2,348 (0.791) | 3,949 (0.385) | 3,973 |
| 1 | 2,332 (0.787) | 1,360 (0.122) | 2,311 (0.794) | 3,910 (0.388) | 3,944 |
| 6 | 2,514 (0.775) | 1,372 (0.123) | 2,554 (0.780) | 4,007 (0.382) | 3,983 |

- 3 job とも参照 3 本の最良は fixed10。fixed10 の trace1・trace0 の実効 define は 3 job とも照合を通った (§1.3 の 1)。

### 2.4 対象 3 点と判定

| 点 | job | throughput (千 txn/s) | abort 率 | r' (= ÷ fixed10) | ÷ B0-L-W0 | ÷ stock | 判定 | 元の r' | 元の throughput |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|
| 1111 | 0 | 4,152 | 0.292 | **1.051** | 1.768 | 3.037 | **再現** | 1.068 | 4,243 |
| 1110 | 1 | 4,165 | 0.344 | **1.065** | 1.802 | 3.063 | **再現** | 1.069 | 4,216 |
| 1001 | 6 | 4,301 | 0.341 | **1.073** | 1.684 | 3.135 | **再現** | 1.062 | 4,230 |

- 千 txn/s の値は、新旧とも生 JSON の 5 rep 中央値を最近接の千に丸めた。元の記録 (2026-09-23 の README) は 3 値を切り捨てで表示している (job 0 の fixed10 3,972、1110 は 4,215、1001 は 4,229)。比と判定には影響しない。

- 3 点とも束縛が成立し (IR 本文 sha256 は列挙・元の compare JSON と一致、(hostname, started_at) は元の 8 job と重複なし)、失格・判定不能の条件に当たらず、r' > 1.03。
- 補助 (判定に使わない): 5 rep の最小 > 同 job の fixed10 の 5 rep 最大 — 1111: 4,120 > 3,970、1110: 4,067 > 4,003、1001: 4,274 > 4,048。abort 率は元の小比較 (0.290・0.342・0.346) とほぼ同じ。
- 相方 IR 点 (記述だけ): 0000 (job 0) 0.973、0001 (job 1) 0.983、0110 (job 6) 0.989 (元 0.983・0.984・0.994)。

## 3. 解釈と限定

- **言えること:** 元の小比較で 16 点から選ばれた 3 点について、選択に使っていない別 job の値でも、同 job の既知最良 (静的 10 µs) に対する比がそれぞれ 3% 線を越えた (1.051〜1.073)。新しい r' は元の選択 (16 点から 3% 超を選んだ) に使っていない値である。ただし再測したのは選ばれた 3 点だけで、job 内位置の交絡も残るので、選択全体の補正や統計的優位は示さない。3 点の中では、1111 は元より 1.7 ポイント低く、1001 は 1.1 ポイント高い。
- **言えないこと:** 統計的な優位 (各点 1 回の再測、3% 線は Pegasus で未較正、分散の推定なし)、16 点の選択全体を補正した有意性、全 IR・LLM×C++ の空間、別 workload (balanced・read-heavy・TPC-C) への転移、fixed10 以外の静的値 (5 µs・20 µs など、現 pin で掃いていない) より良いか。対象点の job 内の位置は元と同じ (同じ `_cases` 巡回) なので、この再測は job・ノード・時刻が別の再測であって、実行位置や job 内の交絡から独立した再現ではない。
- pin: 元は CCBench `e9e477ca`、本再測は `68106660`。確認した差分は `cc/mocc/transaction.cc` の 64 行追加だけで、pin 差は記録にとどめる (同一 binary の証明とは扱わない)。
- 論文へ書くときは、§0 の 4 の文と上の限定を同じ段落に置く。「既知最良」は「同 job で測った静的 10 µs (write-heavy の既存最良値、現 pin で再評価)」と定義を添える。
- firewall (手順書 §3-D): 本 insight・結果 JSON・`recheck-aggregate.json` の点 ID・比は段階 E / F の coder・planner の入力へ流さない。`projection.json` は書き換えていない。並走中の段階 E wave へも点 ID・比を送っていない。
- 診断 build は NON_ADMISSIBLE で、certified 候補とは称さない (D2226 項 5)。verify の serializable は各有限履歴についての判定。

## 4. 計算ノードの使用 (job Elapse)

| 用途 | request | Elapse |
|---|---|---|
| 計測 job 0・1・6 | 29950〜29952.nqsv | 770・774・774 秒 (計 2,318 秒 = 0.64 node 時間) |

- 投げ直し 0 本、焦点走・変異 0 本 (repo の実装面の差分ゼロ)。受入全走は本記録の commit の後に行い、結果は land の受領証に残る。
