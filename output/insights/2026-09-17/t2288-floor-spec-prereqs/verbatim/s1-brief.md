# 段 1 brief — [T-2288] 床値 spec 凍結の前提 A-3 / A-4 / C 群を閉じ、[T-2465] §11.3 を追記訂正する (docs のみ)

wave `dev-wave-t2288-floor-spec-prereqs`、branch `worktree-dev-wave-t2288-floor-spec-prereqs`、起点 local main `20a92f6a6`。
2026-09-17 00:58 JST。

## 研究前進 (1 行)
論文 B-4 (規律 3 の還流 on/off ablation) の事前登録 §5 floor 欄は、workload 別 3 spec (`floor-pair-spec/v3`) の凍結を待って空のままであり、材料レポートの分析 verdict は 1 種類 (protocol violation) に固定されている。凍結を塞ぐ前提 A-1〜A-5・B・C のうち **較正と独立な A-3・A-4・C を本 wave で閉じ**、残る前提を A-5 (窓の日時・seed・出力名 = 無裁定の AI 起草値を禁じる §11.1) だけにする。完了判定 = A-3/A-4/C の 3 件が decisions に記録され、§11.3 の 4 点が追記反映され、残前提が A-5 のみと insight に書けること。
成果物影響 (DW-G05): 放置すると §5 floor 欄が記入不能のまま → §7.1 の 4 分類は実効化せず B-4 の certified 選択・レポートは 1 分類しか出せない。

## scope
- A-3: `perf_config` の `extime` / `reps` / `ycsb_max_ope` を calibrator の測定構成から導き、D1641 決定 3 の委任の下で AI が承認し D として記録する。
- A-4: 「3 workload × §5 に列挙する contention セル」の具体列を起こし D として記録する。
- C 群: 同条件の accepted 較正記録が複数あるときの適格条件と採用順序を、値に依存しない形で **結果を見る前に** 定め D として記録する (D2044 項 11)。
- T-2465: 事前登録 §11.3 の 4 点 (担当者指名・対象集合・統計関数・採用証拠の受理) を D1641 決定 1〜3 / D1695 (n=62) / D1887 / D1936 末尾の反映として追記訂正する。§11.1 の D1812 (c) 追記が「食い違いはユーザー裁定へ返してある」と書く箇所へ決着の追記を足す。
- A-5: 記入しない。何が要るかを裁定パッケージで返す。
- scope 外: spec JSON の作成・凍結、binary record / 配置規則 / official 床値の再取得、較正の再取得、gate・検査・台帳・一般化の追加、§5 の値セルの変更、validator 拡張 (D1696)。実装面差分 0。

## 確定済みユーザー裁定 (再裁定しない)
D15 (較正は env/thread/代表 workload で key)、D1311 (床値選択は最早の適格 run、最新採用は却下)、D1537 (自己不整合な較正は健全世代発効まで使わない)、D1538 (genome 不在 record の silo 仮定は既存分に閉じる)、D1641 決定 1〜3、D1695 (n=62)、D1696 (validator 拡張せず人手責任)、D1887、D1936 項 7 と末尾、D1974、D2044 項 11。

## 不変条件
1. `docs/phase3-b4-reflux-ablation-preregistration.md` は check_docs で living、全文 sha256 pin は歴史記録 1 件のみ (DW-O09 閉包済み)。§5 の値セルには触れず、§11.1/§11.3 への**追記だけ**を行う (既存文は書き換えない、規律 7)。§5 表を読む consumer 4 本の焦点走で無影響を実測する。
2. 凍結成果物 (較正 JSON・freeze・spec) の bytes は 1 byte も変えない。
3. 規律 2 を緩めない。C 群の規則は spec を書く人手 (D1696) の選択規則であり、loader/binder の受理集合を変えない (gate 新設なし)。
4. A-5 の値 (日時・campaign 識別子・seed・出力名) を AI が起草して書かない。
5. 台帳は spool fragment のみ (D 番号は fold が採番)。事前登録本文には未採番 D を引かず、insight path と D1641 等の既存 D だけを引く。

## 親の provisional 裁定 (攻撃対象)
- **(P1) A-3 の値:** `extime=3`、`ycsb_max_ope=10`、`reps=5`。根拠: accepted 較正 4 件 (silo) はすべて calibrator CLI 既定 `--extime 3` で測られ (`orchestrator/calibrator/cli.py:150`、4 job の `calibrate-argv.json` に上書きなし)、runner は `-ycsb_max_ope` を渡さないので CCBench 既定 10 (`external/ccbench/include/ycsb.hh:22`) で測られている。この 2 値を変えると較正した動作点 (LLC miss 率・working set) と別物になる。`reps` は動作点を変えず推定量の分散だけを決める量で、較正 JSON に key が無く calibrator は sweep 3 / noise floor 10 の 2 値を使う (どちらも「1 測定」の反復数ではない)。`PerfConfig` の既定 5 (`orchestrator/campaign/pipeline.py:184`)、§11.2 の名目 (1 測定 = 5 反復 × 3 秒)、D1640 の参照測定 (5 反復)、qualification shape (reps 5) と揃え、`median/v1` が実 rep を返す奇数を採る。**reps=5 は calibrator 出力から導けないことを明記して承認する。**
- **(P2) A-4 の具体列:** 3 workload = rr95 (read-heavy) / rr50 (balanced) / rr5 (write-heavy)、contention セル = 較正が実在する 1 セル (threads 48・`ycsb_zipf_skew=0.9`・`ycsb_rmw=0`) のみ → **spec ごとに cell 1 個、合計 3 cell**。records は各 workload の採用較正の `saturation.records` (rr95 1,000,000 / rr50 1,000,000 / rr5 2,000,000)。根拠: binder は較正 `workload` と cell `workload` の exact 一致・`records` 一致を要求し、accepted 較正は skew 0.9 / rmw 0 / t48 にしか無い。skew の追加は新較正 (D15 の関門) を要し、本 wave では起こさない。
- **(P3) C 群の適格条件 (値非依存) と採用順序:** 適格 = (c1) `output/env/pegasus/calibration/registered/` 配下の tracked record、(c2) `quality.status=accepted` かつ floor driver と同じ入口 (`calibration_verify.load_verified_calibration`、mode=required、spec の env_tag / clocks_per_us) を通る、(c3) protocol が対象 driver の protocol (silo) と一致 (`genome` があればそれ、無ければ job-staging の `calibrate-argv.json` の `--binary`)、(c4) `workload`・`threads` が cell と exact 一致、(c5) effective-clock の `method` が現行 policy と一致し、D1537 の消費側除外集合 (`layer3_report.SELF_INCONSISTENT_WITHIN_RUN_CALIBRATIONS`) に載っていない。採用順序 = 適格集合が 2 件以上なら `acquisition_receipt.qsub.submit_epoch` 最小 (最早の適格、D1311 の型。最新採用は「望む結果が出るまで測り足す」を許すので却下)、同 epoch は sha256 昇順。**適用結果 (rr50): g1 `753f535a` は (c5) で不適格、g2 `94a4b79f` を採る。** rr95 は `5c836a22`、rr5 は `2b7ba072` (各 1 件、規則は形式的に適用)。
- **(P4) T-2465 の追記形:** §11.3 第 1 bullet の末尾に追記 1 段落 (4 点 + n=62 + driver 変更単位の決着と D 番号)、§11.1 の D1812 (c) 追記末尾に決着の追記 1 文。既存文は残す。
- **(P5) 記録先:** A-3/A-4/C は decisions fragment (3 D)。事前登録 §11.2 へは値を再掲しない (D1812 (c) の「12 項目の値の正本は D1641 決定 3 の列挙であり本書はそれを再掲しない」に従う)。

## 段 1 で判明した、既存記録を覆す新事実 (段 4 で再裁定)
- registered 較正は 8 件 (2026-09-15 insight の内訳から増加)。silo は rr5×1 / rr50×2 / rr95×1 で、C 群が実際に発火するのは rr50 だけ。rr95 の複数化は非 silo (mocc/tictoc) であり binder は protocol を照合しないので、(c3) が無いと mocc 較正で silo cell を束縛できてしまう。
- rr50 の 2 件は環境契約の世代 g1/g2 そのもので、g1 は D1537 の自己不整合較正である。前 wave の insight はこの関係に触れていない。
- 較正 JSON (calibration/v2) に extime / reps / max_ope の key は無い (前 wave の指摘を再確認)。導出は argv・runner・CCBench 既定から行うしかない。

## 模擬 / 実の差
tracked 較正 8 件の admission probe は実の `load_verified_calibration` を呼んだ (8/8 ADMITTED)。loader `load_frozen_spec`・driver・issuer は spec が存在しないため未実行。較正・床値の測定はしない。

## 成果物の形
- `output/insights/2026-09-17/t2288-floor-spec-prereqs/README.md` + `verbatim/` (brief・plan・consult・裁定・review・probe 出力)
- `docs/spool/decisions/2026-09-17-dev-wave-t2288-floor-spec-prereqs-1.md` (D 3 件)、`docs/spool/worklog/…-2.md` (T-2288 更新・T-2465 完了)
- `docs/phase3-b4-reflux-ablation-preregistration.md` §11.1 / §11.3 の追記

## 変更面 (実アンカー)
| file | anchor | 操作 |
|---|---|---|
| docs/phase3-b4-reflux-ablation-preregistration.md | §11.1 追記 (2026-09-08、[T-2140]、D1812 (c)) の段落末「両者の食い違いはユーザー裁定へ返してある。」の直後 | 追記 1 文 |
| docs/phase3-b4-reflux-ablation-preregistration.md | §11.3 第 1 bullet「**追記 (2026-09-07)。** … ユーザー手番である。」の直後 | 追記 1 段落 |
| output/insights/2026-09-17/t2288-floor-spec-prereqs/ | 新規 | README + verbatim |
| docs/spool/decisions/, docs/spool/worklog/ | 新規 fragment | seq 1, 2 |

## 並列分割・受入
docs-only なので実装子・fix 子はゼロ、親が直接編集。段 2 plan 1 本 (codex read-only)、段 3 consult 2 本 (レンズ A = 事前登録・HARKing 境界・値依存性・授権範囲、レンズ B = 較正/binder/receipt/CCBench 既定の実物照合と閉包)、段 6 review 2 本 (diff の敵対レビュー)。受入 = login node で `python3 tools/check_docs.py`、`spool_fold.py --dry-run`、prereg consumer 4 本の焦点走、受入全走 (`tools/dev_wave_wait.py acceptance`)。変異 matrix は実装面差分 0 で免除 (DW-S04)。
