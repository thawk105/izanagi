# 段 6 裁定 1 — [T-2853] (5'') fig1 生成器

入力: レビュー A (`codex/s6-review-A.md`、NO-GO)、レビュー B (`codex/s6-review-B.md`、NO-GO)、焦点走 1 回目 (`focus-1.log`、request 29766.nqsv、Elapse 133 s: 1,010 passed / 1 failed / 4 skipped)、
親の試し描き (`preview/fig1b_phase2_negative.png`) と旧図の比較。

## 所見の裁定

| ID | 裁定 | 採否 | 理由 |
|---|---|---|---|
| A-M1 (p 注記が固定文字列) | real | 採用 | 描く値が計算値から来ない。`d['p']` を有効 2 桁の `p=2.5×10⁻⁴` 形に書式化する関数から作る |
| A-M2 = B-M1 (caption に測定条件なし) | real | 採用 | FIGURE_CONVENTIONS §6。条件は WAL の `run_cmd`・`env_tag` と lock の `ccbench_commit` から取る (実在を実測: 3 campaign とも `run_cmd` 8 件が exe path 以外同一、`env_tag` 40 件 `linux-baremetal`、lock `ccbench_commit` `6656e93`)。1 campaign 内で flag が割れる・取れないなら `FigureDataError` |
| A-M3 (着地 closure が生成器の現 sha256 を比べる) | real | 採用 | 図 README「生成器の sha256 は生成時点の記録で現行 source を縛る pin ではない」(規律 7)。closure の照合対象から生成器を外し、provenance には記録として残す。着地 test の `prov['caption'] == fig1.caption()` も現行生成器を縛るので外し、README 包含だけにする |
| A-S1 (記号の意味が caption に無い) | real | 採用 | 平均と中央値・分位を取り違えうる。点・横棒・四角・ひげ・点線・破線を 1 文ずつ定義 |
| A-S2 (未到達数が照合外) | real (事実) | 不採用 | summary が唯一の記録で照合先が無い。caption・provenance に「summary の凍結値」と明記済みの範囲で足りる (G05: 検査を足しても図の値は変わらない) |
| A-S3 (landscape の負例不足) | real (事実) | 不採用 | 規則は `replay.load_landscape` の写しで、追加負例は仮想リスク向け (依頼の scope 外、G05 で成果物影響を示せない) |
| B-S1 (描かない値まで照合) | real | 採用 | 裁定 (P3) は「描く値に限る」。照合を `k`・`n`・`tied_set`・`random_E`・`oracle_E`・greedy の `n`/`mean`/`iqr_lo`/`iqr_hi`・guided の `median`・`guided_n`・A・p に絞る (`greedy_p_lt`・greedy の min/max/median・guided の mean/min/max/iqr を外す) |
| B-S2 (M6 の帰属) | real | 採用 (変異表の修正のみ) | M6 は照合の `FigureDataError` で落ちる。期待 kill を「実データを読む test (照合で落ちる)」に改め、probe で node を集める |
| B-S3 (brief の言い過ぎ) | real | 採用 (記録の訂正のみ) | 「全一致」は summary 記録値との一致を指し、旧図との一致は画素照合で別に確かめる。段 2・3 省略の理由のうち「受理集合に触れない」は、新しい生成器が自分の受理集合 (照合・landscape 検査) を持つので不正確 — 正しくは「既存の受理集合・正しさ防壁を変えない」。insight に訂正として書く |
| P-M1 (焦点走の赤: `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`) | real、本 wave 起因 | 採用 | 新 test file に自走 harness が無い。`orchestrator/tests/test_plot_mocc_witlight_four_arm.py` 末尾と同じ形の `_run()` と `if __name__ == "__main__": sys.exit(_run())` を足す (allowlist へは逃がさない) |
| P-S1 (軸・文字の色) | real | 採用 | 旧図は軸線・文字が `#2a2a2a` (画素実測 (42,42,42))、新図は黒。旧図に揃える |
| P-S2 (panel 題の位置) | real | 採用 | 旧図は左寄せ (`loc='left'`) |
| P-S3 (点の横ずらし) | real | 採用 | 新図は 0.012 刻みで点が重なって見える。旧図程度に広げる (刻み 0.03 前後、中央値棒 ±0.25 の内) |
| P-N1 (題下の余白) | real | 採用 | `top=.78` の余白が大きい。重なり検査を通す範囲で詰める |

## 変異の再登録 (fix 前、DW-M01)

- M1 は照合を絞った後も「greedy 統計 (mean) の照合を外す」とし、T2 greedy で kill。
- M6 の期待 kill を「`load_data` を呼ぶ実データ test が照合の `FigureDataError` で落ちる」に改める (node は probe で確定)。
- 追加: M11 = p 注記の書式化に `d['A']` を渡す → end-to-end の注記照合で kill。M12 = closure に生成器を戻す → 新 test (provenance の生成器 sha256 を変えても closure が通る) で kill。
  M13 = caption の条件文からスレッド数を落とす → caption に WAL 由来の条件値が入ることを見る test で kill。

## fix の範囲

所有 2 file のまま。上限は生成器 450 行・test 300 行 (段 4 と同じ)。既存テストの期待値を変えない (新 test file 内の期待は本裁定に沿って直してよい)。
