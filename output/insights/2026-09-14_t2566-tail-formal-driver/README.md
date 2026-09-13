# [T-2566] 静的 backoff 右 tail の本走 driver — 投入前条件 5 件を実装し実測で確かめた

`docs/b10-backoff-static-tail-preregistration.md` §8.1 が挙げた投入前条件 5 件を実装し、
production の経路を通して実測で確かめた。**本走の投入は行っていない。**

**成果物** = `orchestrator/campaign/b10_backoff_static_tail_formal.py` (新規)、
`orchestrator/tests/test_b10_backoff_static_tail_formal.py` (新規)、
共有の測定経路 (`orchestrator/calibrator/benchparse.py` / `runner.py`、
`orchestrator/campaign/pipeline.py` / `loop.py`) への opt-in 拡張、
exact 閉包の登録簿 4 file と受入の所要台帳への登録。

## 0. 依頼と、実際に起きたこと

依頼は「投入前条件 5 件を満たす本走 driver を実装する。§8.2 の要求に従い、格子・動作点・判定値を
コード定数で置換しない。既存 3 系列の受理集合・成果物・report schema は変更しない。
本走の投入はこの wave では行わない」だった。

実際に起きたことは、**「正常な走行が必ず無効になる」型の欠陥が、今度は実装側に出た**ことである。
先行 wave (T-2500) は事前登録の本文で同じ型を作り込み、焦点レビューの 2 巡目で見つけていた。
本 wave では 2 箇所で再発し、どちらも段 6 の敵対レビューが見つけた。

## 1. 5 件の投入前条件と、それぞれの充足のしかた

| # | 条件 | 満たし方 | 実測の経路 |
|---|---|---|---|
| 1 | 本書の spec を parse する consumer と、その発火 | 新 module が marker 対の内側から fence 2 行を除いた bytes を取り、§5 の全 section を exact に閉じて parse する。格子・動作点・判定値は spec から引数として渡す | 現物の文書 bytes を入力に、binding → 設定生成 → 測定の引数生成まで通す。spec の `execution.records` を変えると CCBench の `-ycsb_tuple_num` が変わることを示す |
| 2 | 性能測定の rep ごとの整数カウンタの WAL 保存と、abort 率の再計算 | 共有の測定経路に opt-in を足し、rep ごとの `abort_counts_` / `commit_counts_` を exact な十進整数のまま記録の conditional key `reps` へ載せる。解析は `aborts/(aborts+commits)` で全精度に再計算する | 保存済みの実 CCBench 標準出力 (`output/env/pegasus/t139-r4-env-probe/0:896504.nqsv/run-R01.log` 系列) を実 `measure_point` の subprocess 置換として注入し、production の writer を通して記録へ載せ、読み戻して再計算する |
| 3 | observation ごとの出所 field を WAL の容器から導出 | loader が admission 済み snapshot と同じ施錠/記録全体 hash を確かめた bytes を読み、物理行を再 parse して記録と順序付きで対応づける。行 digest は保存された行 bytes の SHA-256 | production writer が発行した試験 campaign を admission → replay → 行対応づけ → observation まで通す。探索 campaign は formal loader の入口で拒否されることも実測 |
| 4 | 1 cell あたり 5 本の正しさ記録の発行 | 既存の correctness workload の逐次反復機構へ `loop.run_campaign` から転送する配線を足した。**新しい反復機構は作っていない** | 実 verifier に trace fixture を通して campaign 入口から走らせ、1 cell に 5 本の `verify_done` が並ぶことを確認 |
| 5 | 正しさ検査の mode 座標の記録と比較 | `verify_done.payload.workload.tag` を記録し、探索走の実 WAL から読んだ値と一致することを要求する | 探索の実 WAL から `legacy` を解決し、本走側の 5 本すべてが同じ値を持つことを確認。異なる mode は拒否 |

**正しさの権威は `payload.certified is True`** であり、`verdict` の文字列ではない
(探索の実値は `"serializable"` であって `"certified"` ではない)。report の point 側の
`certified` も正しさの判定に使っていない。

## 2. 「正常な走行が必ず無効になる」欠陥が 2 箇所で再発した

### (a) 集団の同一性に、測定順の先頭の格子点に依存する値を使っていた

初版は、3 本の走行を 1 つの集団として扱うときの同一性検査に、
**測定順の先頭の genome から作った source token** を使っていた。3 本は設計上それぞれ別の
workload を測るので測定順の先頭が違う (物理 2500 / 1250 / 3535)。`BACKOFF_FIXED` は
正規化 bytes に効くので、**同じ checkout・同じ toolchain で測った正常な 3 本が必ず
`invalid` になる**。

直し方は、**追跡された checkout の bytes から、workload にも格子点にも依存しない digest を作る**
ことである。正例の fixture が固定値を渡してこの生成経路を迂回していた点も直し、
実 driver が作る identity で 3 本が一致することを検査に入れた。

### (b) 拒否したときに、失敗理由と観測値を伴う報告が出なかった

事前登録 §7 は、失敗条件に当たった集団を `invalid` として**報告する**ことを求めている。
初版は loader が例外を投げ、報告を書く前に終わっていた。1 点の欠測・整数カウンタの欠損・
時間切れのいずれでも、残りの正常な観測まで報告から消える。

**直したのは「拒否のしかた」であって「拒否するかどうか」ではない。**
失敗した集団は受理されないままで、`invalid` の報告が値を伴って出るようにした。
受理されないことと報告が出ることの両方を検査に入れた。

## 3. 環境の形式と実装の前提が食い違っていた

初版の scheduler 問い合わせは、別方式 (OpenPBS) の JSON 出力と `Jobs[id].stime` を前提にしていた。
**親が実機で叩いたところ、この計算機の scheduler ではその指定は JSON を返さず、
項目一覧の説明を出して rc=0 で終わる。** 放置すると本走は 1 cell も測らずに
`run_workload` の冒頭で止まる。既存の投入 script が同じ問い合わせを text で解析しているので、
その解析を正本として合わせ、保存された実物を入力にした検査を入れた。

## 4. 数値 — 実装が正しく、テストの期待値の側が誤っていた

自由度が非整数のときの Student t 分位点で、テストと実装が食い違った。

- 実装の返す値 `2.94309932340672` → 累積確率 `0.9900000000000` (目標 0.99)
- テストの期待 literal `2.943099940173` → 累積確率 `0.9900000091101`
- 親が独立に高精度の数値積分と二分法で求めた真値 `2.9430993234069955`

**期待値の側を直した。** 自由度が整数の 3 件は累積確率が目標と一致しており、触っていない。

## 5. 変異 — 12 件のうち 2 件が生存し、再照準した

事前登録した 12 件を実機で走らせたところ、10 件は期待どおりテストを落としたが 2 件が生存した。
どちらも**現在のテストに対して等価**だった。

- **spec の fence 行の検査を消しても落ちない。** 既存の否定例は開始 fence を短い語へ替えるので、
  検査が無くても切り出し位置がずれて JSON の parse が同じ例外を出す。
  **同じ byte 数の別の語**へ替える否定例を足して、この検査だけが拒否する形にした。
- **整数カウンタの字句検査を緩めても落ちない。** 既存の否定例は浮動小数の値そのものを入れており、
  **文字列としての小数**が parser に届く経路を突いていなかった。緩めても後段の整数変換が
  同じ例外を出す。小数点・符号・空白・指数表記の文字列を渡す否定例を足した。

**字句検査の緩和だけでは受理集合が変わらないことも実測でわかった** — 検出は診断文字列の違いに
よるもので、規律上これは kill に数えられない。したがって本走の変異は、
**字句検査の緩和と浮動小数経由の変換を同時に入れる**形へ再照準した。この形なら受理集合が動く。

初回の生存結果は消さずにこの節へ残す (再照準の経緯そのものが証拠である)。

## 6. scope 外として返したもの — 残る blocker は投入経路の配線 1 件

**新しい走行種別は、既存の投入 script と job script の境界で拒否される。**
`tools/pegasus/submit_b10_backoff_grid.sh` と `tools/pegasus/b10_backoff_grid.sh` は
旧 3 系列だけを受理し、job script が起動するのも旧 driver である。3 本の成果物を
1 つの集団として集める投入側の入口も無い。

依頼が「本走の投入はこの wave では行わない」と明示しており、投入経路の配線は投入の一部である。
既存 3 系列が現に使っている shell の受理集合を、投入しない wave で実測なしに変えるのは
発火条件を書けない機能追加に当たる。したがって**実装せず、裁定パッケージとして返す。**

**「§8.1 の 5 件が外れ、残る blocker は投入経路の配線 1 件になった」**が正しい言い方である。
「本走投入の唯一の blocker が外れた」とは書かない。

## 7. 既存 3 系列を変えていないことの根拠

- `record_rep_integer_counters` は既定 `False`。False の経路では追加 key も新しい拒否条件も
  適用されない。記録の payload は required 13 key のまま、conditional に `reps` が 1 つ増えただけ。
  caller 所有の extra 経路 (`screening_disabled` の exact 集合) は変更していない。
- 既定 False で記録の key 集合が従来と完全に同一であることを、負例として検査に入れた。
- `EXTENDED_SWEEP_US` とその上端を pin しているテストは触っていない。
- 親の焦点走: `test_layer3_report.py` 217 件、
  `test_calibrator.py` / `test_calibrator_deferred_output.py` / `test_screening_opt_in.py` /
  `test_backoff_extended_sweep.py` / `test_backoff_extended_sweep_report.py` 計 134 件、
  新規 file + 登録簿 3 file 計 128 件 (登録簿更新前)、最終の新規 file 単独 68 件が緑。

## 8. balanced schedule との併用は配線せず拒否した

共有 API が受理した整数記録の指定が、balanced schedule の経路では黙って消えていた。
**呼び手が要求した保存が黙って消えてはならない**ので、併用を測定前に明示的に拒否する形にした。
本走 driver はこの組合せを使わないため、既定経路の回帰ではない。

## 9. エージェント工数

Codex 子 10 本 — plan 1 / consult 2 / author 3 / review 2 / fix 4 のうち、
review 2 本は `--reasoning` が段別に禁止されている argv 誤りで 1 度 rc=2 即死し、同じ prompt を
新しい出力 path で投げ直した。すべて `gpt-6-astra`。model call と wall-clock は
job artifact 側の receipt にある。

**段 5 の実装子 2 名は、テストを 1 件も走らせずに終わった。** どちらも `tools/run_tests.py` を
叩き、子の sandbox には scheduler の実行 file が PATH に無いため投入 preflight が rc=1 になり
`rc=16` で止まった。親が同じ木で自走 harness を叩くと普通に走る。
以後の fix 子の prompt には自走 harness の叩き方を書き、実走できた。
