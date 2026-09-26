# [T-2853] 残り (5'') fig1 (P2-5 誘導探索の否定的結果) の生成器を作り、後継図 fig1b を描いて旧図と値が一致することを確かめた

- 作成: 2026-09-26 JST。wave `worktree-t2853-fig1-redraw` (背景 job)、着手時の基準 = local main `6d198ca8a` (開始 gate fresh rc=0、`verbatim/startup-gate.log`)。依頼の逐語は `verbatim/request.md`。
- 正本の前段: 再実行計画 `output/insights/2026-09-23/t2853-figure-rerun-plan/README.md` §2.1・§3.1、前回の 17 図の描き直し `output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/README.md`。
- 位置づけ: 実装記録。可変状態の正本 (worklog 末尾・`docs/phase3.md`) にはしない。新規計測は 0 で、計算は開発の検査 (焦点走・変異・受入) だけ。

## 0. 要約

1. 生成器 `tools/plotting/plot_p2_5_search_cost.py` と test `orchestrator/tests/test_plot_p2_5_search_cost.py` を足した (Codex author、D95)。追跡下の `output/campaigns/p2-5-summary.json` と P2-2 の 3 campaign だけから、旧 fig1 と同じ値を再計算して描く。
2. 後継図 `docs/paper-story/figures/fig1b_phase2_negative.{png,pdf,provenance.json}` を login `pegasus02` (計測機の外) で描いた。旧 `fig1_phase2_negative.png` の bytes は変えていない (sha256 `5a8d414b…` は着手前と同じ)。
3. 旧図と値が一致した。再計算値は summary の記録値と照合 key 全件で一致し (生成器が不一致なら出力しない)、旧図の画素位置から読んだ値と新図の画素位置から読んだ値は全要素で 0.02 以内 (画素 1〜2 個分) だった (§2)。
4. 新事実: P2-2 の 3 campaign は verifier epoch E0 で、既存の `search_baselines.run_workload` (認証読み出し `CERTIFIED_ACCEPTANCE`) は今は拒否する。生成器は fig2b と同じ `HISTORICAL_RAW` で読み、当時の検証記録をそのまま使う (現行 verifier で再検証していない)。

## 1. 何を作ったか

- 生成器 (395 行) は、summary から LLM 誘導の試行コスト・未到達数・試行数 (原試行 WAL は削除済みで summary が唯一の記録) を、P2-2 の 3 WAL から landscape (commit 済みの 8 構成、記録上すべて certified) を読み、
  既存の `search_baselines` / `replay` の関数で貪欲法 500 seed (seed0 = 0)・tied set・random / oracle 期待値・A・厳密 p を再計算する。`orchestrator/` は変えていない。
- 描く値 (k・構成数・tied set・random / oracle 期待値・貪欲の平均と 25/75 分位・誘導の中央値・試行数・A・p) が summary の記録値と一致しなければ 3 成果物を 1 つも出さない (fig13 の再計算一致要求と同じ型)。
- 測定条件は WAL の `run_cmd`・`env_tag` と lock の `ccbench_commit` から取り、read 比以外が 3 campaign で一致することを要求して caption に書く (48 スレッド、1,000,000 レコード、3 秒、clocks_per_us 1800、Zipf 0.9、rmw 0、`numactl --interleave=all`、`perf stat`、各構成 5 反復、CCBench `6656e93`、`linux-baremetal`。read 比は 95 / 50 / 5%)。
- 視覚符号は旧図を継承した (題・軸名・目盛り名・色・記号・注記の文言と桁・panel 順・軸と文字の色 `#2a2a2a`・panel 題の左寄せ)。違いは直接ラベル `random`・`oracle` を軸の内側に置いたこと (旧図は右端の余白へはみ出していた) と、図の寸法・余白・点の横ずらし幅。
- 保存前のレイアウト検査 (テキストの重なり・はみ出しで出力しない)、provenance (入力・出力の sha256、epoch、条件、計算値、照合 key、artist から読み戻した値、caption)、着地 bundle の closure (生成器の現 sha256 は照合しない、規律 7)。
- test (217 行): 実データの値 (write-heavy の貪欲度数 `{1:62,2:66,3:67,4:35,5:31,6:182,7:57}`、A 0.5813 / 0.2304、厳密 p 2.521×10⁻⁴)、照合の負例 4、landscape の負例 2、条件の負例 4、end-to-end (artist と計算値の一致・caption)、
  レイアウト (本物の Figure に重なる文字を足すと拒否)、closure (改変 PNG を拒否、生成器 hash の差は通す)、着地 bundle、自走 harness。

## 2. 旧図との照合

### 2.1 値の出所との一致 (生成器の照合)

3 workload とも照合 key 全件で一致した (provenance の `checked_keys`: read-heavy 11 件、balanced 12 件、write-heavy 13 件)。

| workload | k / tied set | random / oracle | 貪欲 平均・25/75 分位 (500 seed) | 誘導 中央値・未到達 | A | 厳密 p (片側) |
|---|---|---|---|---|---|---|
| read-heavy | 4 / B0-L-W0・B0-L-W1・B0-T-W0・B0-T-W1 | 1.8 / 1.5 | 1.756・1〜2 | 1・0/6 | (k=4 で注記しない) | — |
| balanced | 1 / B0-L-W0 | 4.5 / 1.875 | 4.234・2〜6 | 4・0/12 | 0.58125 (記録 0.5813) | — |
| write-heavy | 1 / B0-L-W0 | 4.5 / 1.875 | 4.362・2〜6 | 8・8/12 | 0.230417 (記録 0.2304) | 2.5211×10⁻⁴ (記録 2.521080185096×10⁻⁴) |

### 2.2 旧図の画素との一致

旧図は生成器も provenance も無いので、描かれた値を画素位置から読んだ。親の使い捨て script (`read_old_fig1.py`、repo 外の job dir) が各 panel の目盛り 1〜8 の行位置で縦軸を 1 次較正し、
色ごとの要素 (破線・点線・横棒・四角・ひげ・点) の行位置を値へ変換する。**同じ script を新図にもかけ、読み取り側の偏りを対照で見た** (1 目盛り = 旧図 60.6 画素・新図 75.7 画素)。

| panel | 要素 | 旧図の読み | 新図の読み | 描いた値 (provenance) | 旧−新 |
|---|---|---|---|---|---|
| read-heavy | oracle 破線 | 1.501 | 1.502 | 1.5 | 0.001 |
| | random 点線 | 1.798 | 1.806 | 1.8 | 0.008 |
| | 誘導 中央値 | 1.006 | 1.000 | 1 | 0.006 |
| | 貪欲 四角 | 1.714 | 1.724 | 1.756 | 0.010 |
| | 貪欲 ひげ 上 / 下 | 1.987 / 0.997 | 1.997 / 0.993 | 2 / 1 | 0.010 / 0.004 |
| balanced | oracle 破線 | 1.880 | 1.872 | 1.875 | 0.008 |
| | random 点線 | 4.504 | 4.500 | 4.5 | 0.004 |
| | 誘導 中央値 | 3.993 | 3.998 | 4 | 0.005 |
| | 貪欲 四角 | 4.207 | 4.209 | 4.234 | 0.002 |
| | 貪欲 ひげ 上 / 下 | 5.998 / 1.987 | 5.999 / 1.997 | 6 / 2 | 0.001 / 0.010 |
| write-heavy | oracle 破線 | 1.880 | 1.872 | 1.875 | 0.008 |
| | random 点線 | 4.504 | 4.500 | 4.5 | 0.004 |
| | 誘導 中央値 | 8.003 | 8.000 | 8 | 0.003 |
| | 貪欲 四角 | 4.310 | 4.330 | 4.362 | 0.020 |
| | 貪欲 ひげ 上 / 下 | 5.998 / 1.987 | 5.999 / 1.997 | 6 / 2 | 0.001 / 0.010 |

- 旧図と新図の差は全 18 要素 (3 panel × 6 要素) で 0.020 以下 (旧図の 1.2 画素)。
- 貪欲の四角は両図とも描いた値より 0.02〜0.05 低く読める。新図の描いた値は provenance で平均 (1.756 / 4.234 / 4.362) と分かっているので、これは読み取り script の偏り (四角の行範囲にひげの行が混ざる) であって旧図の値の違いではない。段 1 brief の時点では旧図だけを読んでいてこの偏りを区別できなかった (§4 の B-S3)。
- 誘導の点: 旧図で棒に隠れずに見える点の高さ (read-heavy 3・3、balanced 1・3・3・5・5 と棒の脇の 4、write-heavy 1・3・4・4 と棒の脇の 8) は summary の試行コスト (read-heavy `[1,1,1,1,3,3]`、balanced `[1,3,3,4×7,5,5]`、write-heavy `[1,3,4,4,8×8]`) と矛盾しない。
  中央値と同じ値の点は旧図・新図とも棒に重なるので、点の個数は画素からは数えられない (値の出所は summary の試行コストで、新図の provenance `artist_series.points` がその全件を持つ)。
- 注記の文字 (目視): 題、軸名、目盛り名、`A=0.58` (balanced、濃灰)、`A=0.23`・`p=2.5×10⁻⁴`・`8/12 mis-converged` (write-heavy、赤)、`random`・`oracle` は旧図と同じ文言・桁。

### 2.3 言わないこと

- 図は判定を作らない。balanced の「有意差なし」、write-heavy の「誘導が貪欲より有害」「8/12 誤収束」は summary の記録 (2026-07-02 再校正・2026-07-03 訂正) の結論で、本 wave は値を描き直しただけである。
- P2-2 の 8 構成の certified は当時の verifier epoch E0 の記録で、現行 verifier で再検証していない (規律 7。再検証は R1 / R2 の話で本 wave の外)。
- 論文ストーリーの凍結版は旧図を参照したまま変えていない。どの版・どの稿で fig1b を使うかは論文側の仕事。

## 3. 段の経過 (実装面は Codex author、D95)

- 段 1 brief (`verbatim/s1-brief.md`): 親の provisional 裁定 P1〜P6。brief の前に login で生死確認 (`verbatim/probe_replay2.log`、親の使い捨て script、1.3 秒) をし、既存関数の認証読み出しが E0 で拒否されること (新事実) と、
  `HISTORICAL_RAW` で組んだ landscape から summary の記録値が全件出ることを確かめた。段 2・3 は軽量版で省いた (DW-C00)。
- 段 4 裁定 (`verbatim/s4-ruling.md`): plan v2、test T1〜T6、変異 M1〜M10 と対照 C0 の事前登録。
- 段 5 実装 (`verbatim/s5-author-a.md`、Codex author 1 本、19:03〜19:13 JST): 生成器 317 行・test 124 行。統合 commit `1533df2c5`。
- 焦点走 1 回目 (新 test と、test file を列挙するメタテスト 4 本・DW-O26 の inventory 4 群、`verbatim/focus-1-summary.txt`): 1,010 passed / 1 failed / 4 skipped。赤は本 wave 起因で、
  `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted` が新 test file の自走 harness 欠如を検出した。
- 段 6 レビュー (`verbatim/s6-review-A.md` 正しさ・値・caption、`verbatim/s6-review-B.md` 過剰・削除): 両方 NO-GO。裁定 1 (`verbatim/s6-ruling-1.md`) で次を採用した —
  p 注記を固定文字列でなく計算値から書式化 (A-M1)、caption に測定条件 (A-M2 = B-M1、FIGURE_CONVENTIONS §6) と記号の意味 (A-S1)、着地 closure で生成器の現 sha256 を比べない (A-M3、規律 7)、
  照合を描く値に絞る (B-S1)、自走 harness (焦点走の赤)、軸・文字の色 `#2a2a2a`・panel 題の左寄せ・点の横ずらし・余白を旧図に揃える (親の試し描きとの比較)。
  不採用: 未到達数の照合 (A-S2、summary が唯一の記録で照合先が無い)、landscape の追加負例 (A-S3、仮想リスク向け)。
- fix 1 (`verbatim/s6-fix-1.md`、19:22〜19:29 JST): commit `e2dd9754c`。焦点走 2 回目 (同じ集合、`verbatim/focus-2-summary.txt`): 1,014 passed / 0 failed / 4 skipped。
- 焦点再レビュー 1 巡目 (`verbatim/s6-focus-1.md`): NO-GO。新規 F-M1 = caption の共通条件を read-heavy の値だけで書いていた。現データでは 3 campaign とも read 比以外同一で図の値は変わらないが、
  caption の主張の根拠なので裁定 2 (`verbatim/s6-ruling-2.md`) で採用した。
- fix 2 (`verbatim/s6-fix-2.md`、19:33〜19:36 JST): commit `3798ba6c8`。生成器 395 行・test 217 行 (上限 450・300 の内)。焦点走 3 回目 (新 test とメタテスト 3 本、`verbatim/focus-3-summary.txt`): 98 passed / 1 skipped。
- 焦点再レビュー 2 巡目 (`verbatim/s6-focus-2.md`): GO、新規所見なし (DW-O16 の 3 巡の内)。
- 親の描画 (19:40 JST、login `pegasus02`、`verbatim/redraw.log`): rc=0、3 成果物。旧図の sha256 は着手前と同じ。

### 3.1 段 1 brief の訂正 (レビュー B-S3)

- brief の「全一致」は summary の記録値との一致を指す。旧図との一致は画素照合で別に確かめた (§2.2)。brief が「旧図の四角が 0.04〜0.05 低く読める」と書いたのは読み取り側の偏りで、新図にも同じ偏りが出た。
- 段 2・3 を省いた理由のうち「受理集合に触れない」は不正確だった。新しい生成器は自分の受理集合 (照合・landscape・条件の検査) を持つ。正しくは「既存の受理集合と正しさ防壁を変えない」。
  段 6 の敵対レビュー 2 本がこの受理集合を攻撃した (B は照合を描く値に絞るよう求め、採用した)。

## 4. 変異 matrix (DW-M01〜M08)

- 対象 commit `3798ba6c8` (fix 2 の後の実装の最終 commit)。同じ commit に固定した detached worktree `t2853-fig1-mut` で `tools/mutation_harness.py --runner-mode dispatch` を走らせた。
  runner は `tools/run_tests.py --force-dispatch orchestrator/tests/test_plot_p2_5_search_cost.py -q -rf` に限った (生成器を import する test はこの file だけ)。
- 事前登録: 段 4 の M1〜M10、段 6 裁定 1 の M11〜M13、裁定 2 の M14 と、docstring だけを変える対照 C0。置換アンカーは生成 script (`mutation/make_specs.py`、sha256 `5aab64af…`、job dir) が対象 file でちょうど 1 回現れることを assert した。
  M6 (貪欲法の seed0 を 1 に) は裁定 1 の B-S2 どおり「照合の `FigureDataError` で実データを読む test が落ちる」として登録した。
- probe (全件 SURVIVED 期待で観測 node を集める、19:40〜19:51 JST、`verbatim/mutation-spec-probe.json`・`verbatim/mutation-probe-summary.txt`): baseline PASSED、14 変異すべてで名指しの test を含む赤、C0 は SURVIVED。
  名指しの外の赤は同じ 1 行の変異から来る同じ理由のもの (M6: 実データを読む 6 test が照合で落ちる、M7: 認証読み出しが E0 で拒否され実データを読む 10 test が落ちる)。
- 本走 (観測 node の完全集合を KILLED 期待に登録、19:52〜20:07 JST、`verbatim/mutation-spec-final.json`・`verbatim/mutation-final-summary.txt`): baseline PASSED、**M1〜M14 の 14 件すべて KILLED (期待 node と完全一致)、C0 は SURVIVED**。変異の木は走行後も clean (dirty 0)。
- 結果 JSON の原本は job dir (`mutation/probe-results.json` sha256 `5c6fbc62…`、`mutation/final-results.json` sha256 `955633d1…`)。

| ID | 変異 | 殺した test |
|---|---|---|
| M1 | 貪欲統計の照合を外す | `test_reconciliation[greedy]` |
| M2 | A の照合を外す | `test_reconciliation[A]` |
| M3 | 厳密 p の照合を外す | `test_reconciliation[p]` |
| M4 | landscape の記録上 certified の検査を外す | `test_landscape` |
| M5 | landscape の 8 構成被覆の検査を外す | `test_landscape` |
| M6 | 貪欲法の seed0 を 0→1 | 実データを読む 6 test (照合で落ちる) |
| M7 | `HISTORICAL_RAW` → `CERTIFIED_ACCEPTANCE` | 実データを読む 10 test (E0 で拒否) |
| M8 | 中央値棒に平均を描く | `test_end_to_end` |
| M9 | closure の出力 sha256 照合を外す | `test_closure` |
| M10 | レイアウト検査を早期 return | `test_layout` |
| M11 | p 注記に A を渡す | `test_end_to_end` |
| M12 | closure に生成器の現 sha256 を戻す | `test_closure_generator_history` |
| M13 | caption からスレッド数を落とす | `test_end_to_end` |
| M14 | 3 campaign の共通条件の一致検査を外す | `test_measurement_conditions_across_campaigns` |

## 5. 計算の費用 (D2212 項 4)

- 図の描画と生死確認・画素照合は login で node 時間 0。新規計測は 0。
- 開発の検査の job Elapse (実測、いずれも 1 node): 焦点走 133 s・130 s・120 s、変異 34 job 計 459 s (各 job の `.e` file の Elapse の和、一覧 `verbatim/mutation-job-elapse.txt`)。合計 842 s ≈ **0.23 node 時間**。
- 受入全走は記録 commit の後に走るので、ここには書かない。

## 6. 残り

- [T-2853] の残りは変わらない: (1'') 今後の論文根拠の実験の job body で保全口の opt-in を有効にする、(4) R2 の入口、(5'') のうち fig15 の repo 外入力の写しと R2 の投入単位の決定・見積り、(6) 公開範囲の確定。
- 論文ストーリーの次の版・稿で fig1 の代わりに fig1b を載せるかは論文側の仕事 (本 wave は版を変えていない)。

## 7. 記録

`verbatim/` に、依頼、開始 gate、段 1 brief、段 4 裁定、段 5 実装子の報告、段 6 レビュー 2 本・裁定 2 本・fix 子の報告 2 本・焦点再レビュー 2 本、焦点走 3 回の要約 (結果行と Elapse)、
生死確認の出力、旧図・新図の画素読み取り、描画の log、変異の spec 2 本と結果の要約 2 本と job ごとの Elapse を置く。
使い捨て script (生死確認 `probe_replay2.py` sha256 `666e9cbf…`、画素読み取り `read_old_fig1.py` sha256 `20e1c82b…`、変異 spec の生成 `mutation/make_specs.py`、Elapse 集計、caption の差し込み) と
焦点走の log 全文は、親が書いた repo 外の物として wave の job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2853-fig1-redraw/`) に置き、repo へは入れない。
Codex 出力の逐語 (`s5-author-a.md`・`s6-*.md` のうち裁定 2 本を除く 6 本) は原文のまま置いた。設計判断の新しい D は無い (E0 の campaign を `HISTORICAL_RAW` で読み当時の記録をそのまま使うのは fig2b の生成器と同じ扱い)。
