# silo-function-policy 軸 — 既知最良超え 3 点の別 job 再測 (2026-09-26、[T-2865] 付随)

- 位置づけ: `output/insights/2026-09-23/t2865-silo-policy-known-best-compare/README.md` (D2240、以下「元の小比較」) の後継。D2243 項 1「論文 (ComSys 原稿を含む) でこの 3 点を既知最良を超えた点として書く前に、別 job 再測を行う」の実施記録。**報告カテゴリは「偵察 (preliminary)」** で、事前登録のどの構成でもない。可変状態の正本にはしない。
- wave: branch `t2865-known-best-recheck`、起点 local main `265cce13c` (開始 gate rc=0)。
- **§1 の判定規則は計測 job を投げる前に書き、この節だけを先に commit した** (規律 3)。§2 以降は結果を見た後に追記する。
- 逐語 (`verbatim/`): 依頼、段 1 brief、段 3 相談、段 4 裁定 (§2 以降の追記時に置く)。

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
