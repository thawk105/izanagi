## 所見

- **F1｜must-fix｜[analysis.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/analysis.py:29)**：実測した LLC カウンタを捨て、miss rate を固定の 100 万 loads に丸め直して `find_saturation` に渡している。Δ=0.01 の境界付近では判定が変わり得る。**放置すると採用 N が変わり、以後の最良設定・集合・図の測定条件も変わる。** 実測カウンタを保持して渡すか、丸めによる判定不変を境界例で証明する。

- **F2｜must-fix｜[driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:139)、[plot_vhash_cicada_tuning.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/plotting/plot_vhash_cicada_tuning.py:136)**：既定の J2 は W1〜W5 を各 1 job、計 5 job に分け、裁定の最大 4 job を超える。さらに W5 を J0 判定で除外した正当な部分結果でも、作図器は W5 を必須として停止する。R4 で W4 を J1 から外した場合も図 (a) が停止する。**放置すると裁定どおり縮小・欠測を記録した実測から図を生成できず、予算計算の job 数も変わる。** J2 の割付けを最大 4 job にし、図は実測済み workload だけを描き、欠測理由を provenance に残す。

- **F3｜must-fix｜[driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:139)**：R4 の「W4 は J1 から外し、J2 では control と W3 上位 2」は `make-spec` の引数と選抜規則で表せない。W4 は `selected["W4"]` を要求する。**放置すると予算超過時に事前登録した縮小梯子を実行できず、後付けの候補選択か測定中止になる。** R4 を明示引数にし、W3 選抜結果から W4 の J2 条件を生成する。

- **F4｜should｜[driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:635)、[analysis.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/analysis.py:128)**：J2 の summary は score と best を出すが、裁定で併記する候補別の絶対 throughput *median* を出さない。図の集約も mean である。推奨は J2 の各候補について絶対値の rep median を summary に追加し、本文・図で使う統計量を明示すること。

- **F5｜should｜[plot_vhash_cicada_tuning.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/plotting/plot_vhash_cicada_tuning.py:25)**：共通注記の「探索値」が J2 の図 (b) にも入る。図 (b) は裁定上「確認値」。推奨は図ごとに「J1 探索値」「J2 確認値」を分け、両方に「正しさ未検証の診断値」を残すこと。

- **F6｜should｜[plot_vhash_cicada_tuning.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/plotting/plot_vhash_cicada_tuning.py:67)**：作図器は `perf=False` だけで入力を選び、`exit_code` と事前登録 spec との一致を確認しない。`analyze` を通さず生 JSONL と schema だけで図を作れる。推奨は作図前に完走・予定 run 一致を検証し、無効行を図から排除すること。

- **F7｜nit｜[test_vhash_cicada_tuning.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/orchestrator/tests/test_vhash_cicada_tuning.py:166)**：CV 欠測・session 2 の古い負例は `expected_reps=3` のまま 1 rep しか与えず、候補欠測で赤になる。R-add4 自体には別の正例がある。推奨は古い負例も `expected_reps=1` とし、集合だけ判定不能になる理由を直接検査すること。

## 裁定・事前登録との照合

| s4-ruling の項目 | 判定 |
|---|---|
| A-F1／B-B2：rr50 全24点×GC 3点、他 workload の主張範囲 | 測定格子は**実装どおり**。主張名は一次資料未作成のため**未実装**。 |
| A-F2／B-B7、R-add1：compile command と SHA256 による binding | **実装どおり**。J0b の通常 build manifest では Cicada の対象 TU と期待 define を照合済み。 |
| A-F3：J1 探索、J2 確認 | 集計分離は**実装どおり**。J2 の最大4 job は**ずれ**。 |
| A-F4／B-B5、R-add4：CV 幅内集合、session不足時は集合のみ不能 | **実装どおり**。best・score は残る。絶対 throughput median の併記は**未実装**。 |
| A-F5：公式 floor・compare・採否に接続しない | **実装どおり**。summary は公式 floor 未取得と記す。 |
| A-F6／B-B4、B-B9：W5 の定義・生死判定・欠測 | driver は**実装どおり**。J0b で待機 build が `thid` と `clock_delay` の未宣言により compile 不能だった事実と整合する。欠測時の図は**ずれ**。 |
| A-F7：perf 付き値の隔離 | `analysis._valid` と作図の stage/perf 選別は**実装どおり**。作図の完走検証には所見 F6。 |
| A-F8：rep ごとの固定 seed、control、時刻・load・直前 run | **実装どおり**。 |
| A-F9／plan P4：飽和候補、RSS 下限、8M 未決定停止 | 区分と停止は**実装どおり**。合成 counter の精度は**ずれ**。 |
| A-F10：正しさ未検証の診断値 | driver・図の注記は**実装どおり**。最良設定の trace 検査は裁定上 scope 外。 |
| B-B1：rr50 の共通 1M 条件 | J2 条件追加は**実装どおり**。 |
| B-B3：事前 build、単価、×1.5 見積り | **実装どおり**。J2 job 数と R4 縮小は**ずれ**。 |
| B-B8／plan P8：private helper の利用を一箇所へ | **実装どおり**。 |
| R-add2：build 並列度、180秒静定、perf parser | **実装どおり**。 |
| R-add3：J0 walltime 30分 | 投入ログでは**実装どおり**。driver 自身の walltime 設定ではない。 |
| 変異 M1〜M9 | M1〜M6、M8、M9 は対象処理を名指す検査がある。M7 は helper を直接検査する。変異そのものの実走証拠はなく、F7 の古い負例は赤理由が絞れていない。 |

## 正しいと確認した点

`runtime_argv` は実効の `-ycsb_*` flag を使い、holdout 比率を拒否する。`check_flags` の数値比較は実測 J0c のタブ区切り表示を受理できる。compile define の綴りは CMake と一致し、`-DWORKER1_INSERT_DELAY_RPHASE_US=1000` は待機 build の `CMAKE_CXX_FLAGS` に入っている。J0c の指定ログ時点では走行中で、取得済みの行は通常 build・perf なしの較正値だった。J0c の完了や較正結果は確認していない。

## 総括

binding と主要な J1/J2 集計規則は概ね裁定に沿う。先に F1〜F3 を直す必要がある。現時点の J0 は待機型の compile 不能と J0c の途中記録までが確認できた事実であり、最良設定・集合・図の実測成果物はまだ確定していない。